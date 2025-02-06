importScripts("manifest.js");
importScripts(PYODIDE_URL);
// https://pyodide.org/en/stable/usage/type-conversions.html#explicit-conversion-of-proxies
// https://pyodide.org/en/0.21.3/usage/api/js-api.html#PyProxy.callKwargs

// Fetch pyIodide / flexiclic & instantiate
async function setupFlexiClic(apiRoot) {
  const pyodide = await loadPyodide({
    env: {ICU_DATA: "/icudata"},
    packages: PRELOAD_WHEELS,
  });
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");

  // Use pyodide-http to fake requests
  await micropip.install('pyodide-http');
  await pyodide.runPythonAsync("import pyodide_http ; pyodide_http.patch_all()")
  await pyodide.loadPackage("requests");

  self._pyodide = pyodide;
  const flexiclic = pyodide.pyimport("flexiclic");
  return flexiclic.FlexiClic(api_root=apiRoot);
}
// Create promise to working FlexiClic object, callees either wait for setup or get previously instantiated object
self.flexiclic_ready = setupFlexiClic(location.origin);

// Wrap postMessage, sanitising PyProxy objects to plain JS
function post(tx, rv, done) {
  // https://pyodide.org/en/stable/usage/type-conversions.html#type-translations-pyproxy-to-js
  let pyproxies = [];
  try {
    if (rv instanceof self._pyodide.ffi.PyProxy) {
      // Convert rv to (plain) JS object
      rv = rv.toJs({pyproxies, dict_converter: Object.fromEntries});
    }
    self.postMessage({ tx, done, rv });
  } finally {
    for (const px of pyproxies) px.destroy();
  }
}

onmessage = function (event) {
  return self.flexiclic_ready.then((flexiclic) => {
    // Proxy message through to flexiclic
    // TODO: https://pyodide.org/en/stable/usage/keyboard-interrupts.html
    if (!flexiclic[event.data.method]) throw new Error(`Unknown flexiclic method ${event.data.method}`);
    let rv = flexiclic[event.data.method].callKwargs(event.data.kwargs);
    if (rv instanceof self._pyodide.ffi.PyGenerator) {
        // For generators, send values to main thread one by one
        while (true) {
            const x = rv.next();
            if (x.done === true) break;
            post(event.data.tx, x.value, false);
        }
        post(event.data.tx, undefined, true);
    } else {
        post(event.data.tx, rv, true);
    }
  }).catch((error) => {
    console.error(error);
    self.postMessage({ tx: event.data, error: error.message });
  });
};
