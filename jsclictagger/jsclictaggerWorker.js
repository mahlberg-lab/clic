/**
 * jsclictagger web worker: load pyodide, import jsclictagger & proxy requests.
 *
 * To call into it from the page, import jsclictagger.js.
 * To define the set of wheels to load, see jsclictagger/Makefile.
 */
importScripts("manifest.js");
importScripts(PYODIDE_REQUIREMENTS["_pyodide"]);
// https://pyodide.org/en/stable/usage/type-conversions.html#explicit-conversion-of-proxies
// https://pyodide.org/en/stable/usage/api/js-api.html#PyProxy.callKwargs

async function setupClicTagger() {
  const pyodide = await loadPyodide({
    packages: PYODIDE_REQUIREMENTS["_preload_pyodide"],
  });
  const micropip = pyodide.pyimport("micropip");

  // Install the rest from local wheels (relative to this worker's URL)
  await micropip.install(PYODIDE_REQUIREMENTS["_preload_wheels"].map(function (x) {
    return x.endsWith(".whl") ? new URL(x, self.location.href).toString() : x;
  }));

  self._pyodide = pyodide;
  const jsclictagger = pyodide.pyimport("jsclictagger.jsclictagger");
  return jsclictagger;
}
self.clictagger_ready = setupClicTagger();

function post(tx, rv, done) {
  // https://pyodide.org/en/stable/usage/type-conversions.html#type-translations-pyproxy-to-js
  const pyproxies = [];
  try {
    if (rv instanceof self._pyodide.ffi.PyProxy) {
      rv = rv.toJs({ pyproxies, dict_converter: Object.fromEntries });
    }
    self.postMessage({ tx, done, rv });
  } finally {
    for (const px of pyproxies) px.destroy();
  }
}

onmessage = function (event) {
  return self.clictagger_ready.then((clictagger) => {
    if (!clictagger[event.data.method]) {
      throw new Error(`Unknown clictagger method ${event.data.method}`);
    }
    return clictagger[event.data.method].callKwargs(event.data.kwargs);
  }).then(function (rv) {
    if (rv instanceof self._pyodide.ffi.PyAsyncGenerator) {
      return rv.next().then(function handle(x) {
        if (x.done === true) {
          post(event.data.tx, undefined, true);
          return;
        }
        post(event.data.tx, x.value, false);
        return rv.next().then(handle);
      });
    }
    if (rv instanceof self._pyodide.ffi.PyGenerator) {
      while (true) {
        const x = rv.next();
        if (x.done === true) break;
        post(event.data.tx, x.value, false);
      }
      post(event.data.tx, undefined, true);
      return;
    }
    post(event.data.tx, rv, true);
  }).catch((error) => {
    let message = error.message, level = "error";
    console.warn(error);
    if (error.name === "PythonError" && error.message && error.type) {
      message = error.message.replace(
        new RegExp(".*\\n(?:[a-z0-9A-Z\\.]*)" + error.type + ": ", "s"),
        error.type + ": "
      );
    }
    self.postMessage({ tx: event.data.tx, error: message, level: level });
  });
};
