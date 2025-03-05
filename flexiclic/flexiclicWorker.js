importScripts("manifest.js");
importScripts(PYODIDE_REQUIREMENTS["_pyodide"]);
// https://pyodide.org/en/stable/usage/type-conversions.html#explicit-conversion-of-proxies
// https://pyodide.org/en/0.21.3/usage/api/js-api.html#PyProxy.callKwargs

// Fetch pyIodide / flexiclic & instantiate
async function setupFlexiClic(apiRoot) {
  const pyodide = await loadPyodide({
    env: { ICU_DATA: "/lib/python3.12/site-packages/icudata" },
    packages: PYODIDE_REQUIREMENTS["_preload"],
  });
  await pyodide.loadPackage("micropip");
  const micropip = pyodide.pyimport("micropip");

  // Use pyodide-http to fake requests
  await micropip.install('pyodide-http');
  await pyodide.runPythonAsync("import pyodide_http ; pyodide_http.patch_all()")
  await pyodide.loadPackage("requests");

  self._pyodide = pyodide;
  const flexiclic = pyodide.pyimport("flexiclic");
  return flexiclic.FlexiClic(api_root=apiRoot, install_package_fn=async function (pkg) {
      if (!self._installed_packages) self._installed_packages = {};
      if (self._installed_packages[pkg]) return;

      // Install requirements from manifest (read: direct wheel locations) or package itself
      await micropip.install((PYODIDE_REQUIREMENTS[pkg] || [pkg]).map(function (x) {
          // micropip takes prebuilt/thing.whl to mean file://, not a relative URL
          return x.endsWith(".whl") ? "https://" + self.location.host + "/flexiclic/" + x : x;
      }));

      self._installed_packages[pkg] = true;
  });
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
    return flexiclic[event.data.method].callKwargs(event.data.kwargs);
  }).then(function (rv) {
    if (rv instanceof self._pyodide.ffi.PyAsyncGenerator) {
        // Async generator, promise-chain calls to next()
        return rv.next().then(function handle (x) {
            if (x.done === true) {
                post(event.data.tx, undefined, true);
                return;
            }
            post(event.data.tx, x.value, false);
            return rv.next().then(handle);
        });
    }

    if (rv instanceof self._pyodide.ffi.PyGenerator) {
        // For generators, send values to main thread one by one
        while (true) {
            const x = rv.next();
            if (x.done === true) break;
            post(event.data.tx, x.value, false);
        }
        post(event.data.tx, undefined, true);
        return;
    }

    // Post single values
    post(event.data.tx, rv, true);
  }).catch((error) => {
    var message = error.message, level = "error";
    console.warn(error);
    if (error.name === "PythonError" && error.message && error.type) {
        // Bin the traceback, just return the summary
        // NB: error.type won't be fully-qualified, so guess preamble
        if (error.type === "UserError") {
            message = error.message.replace(new RegExp(".*\\n(?:[a-z0-9A-Z\\.]*)" + error.type + ": ", "s"), "");
            level = "warn";
        } else {
            message = error.message.replace(new RegExp(".*\\n(?:[a-z0-9A-Z\\.]*)" + error.type + ": ", "s"), error.type + ": ");
        }
    }
    self.postMessage({ tx: event.data.tx, error: message, level: level });
  });
};
