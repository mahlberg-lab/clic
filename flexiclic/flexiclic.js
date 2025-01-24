// TODO: https://github.com/GoogleChromeLabs/comlink ?

// Create flexiclic, which proxies any method calls through to python
window.flexiclic = new Proxy({}, { get: function (target, propName) {
  // Assume any get is fetching a method, construct closure in response
  return function (kwargs) {
    return new Promise((resolve) => {
      // If not present, start webworker & listen to transactions
      if (!target._worker) {
        target._transactions = {};
        target._worker = new Worker("/flexiclic/flexiclicWorker.js");
        target._worker.addEventListener("message", (e) => {
            if (e.data.error) {
                throw new Error(`FlexiClic error: ${e.data.error}`);
            }
            if (!e.data.tx) {
                throw new Error(`Message has no transaction ID ${e.data}`);
            }
            if (!target._transactions[e.data.tx]) {
                throw new Error(`No promise for transaction ID ${e.data.tx}`);
            }
            if (e.data.done === false) {
                // Generator, collate parts into an array
                target._transactions[e.data.tx].rv ||= [];
                target._transactions[e.data.tx].rv.push(e.data.rv);
            } else if (target._transactions[e.data.tx].rv) {
                // Return results of generator
                target._transactions[e.data.tx](target._transactions[e.data.tx].rv);
                delete target._transactions[e.data.tx];
            } else {
                // Call relevant resolve, throw away
                target._transactions[e.data.tx](e.data.rv);
                delete target._transactions[e.data.tx];
            }
        });
      }

      // Send method call as request
      const transactionId = crypto.randomUUID();
      target._transactions[transactionId] = resolve;
      target._worker.postMessage({
        tx: transactionId,
        method: propName.toString(),
        kwargs: kwargs,
      });
    });
  };
} });
