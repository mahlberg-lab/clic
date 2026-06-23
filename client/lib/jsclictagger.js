/**
 * jsclictagger: JavaScript client for the jsclictagger web worker.
 *
 * The default export is a Proxy that turns any property access into a method
 * call dispatched to the worker.  Each call resolves with the worker's return
 * value, so this:
 *
 *     import clictagger from "./jsclictagger.js";
 *     const regions = await clictagger.regionsFromContent({ file, highlight });
 *
 * ... is roughly equivalent to running, in Python:
 *
 *     TaggedText.from_file(file).table(highlight=highlight)
 */
"use strict";
var DisplayError = require('./alerts.js').prototype.DisplayError;

// Create jsclictagger, which proxies any method calls through to python
module.exports = new Proxy({}, { get: function (target, propName) {
    if (propName === "shutdown") {
        return function () {
            if (window.jsclictagger_worker) {
                window.jsclictagger_worker.terminate();
                window.jsclictagger_worker = undefined;
            }
            return Promise.resolve();
        };
    }

    // Assume any get is fetching a method, construct closure in response
    return function (kwargs) {
        return new Promise(function (resolve, reject) {
            var transactionId, worker;

            if (window.parent && window.parent.jsclictagger_worker) {
                worker = window.parent.jsclictagger_worker;
            } else if (window.jsclictagger_worker) {
                worker = window.jsclictagger_worker;
            } else {
                // If not present, start webworker & listen to transactions
                window.jsclictagger_worker = new Worker("/jsclictagger/jsclictaggerWorker.js");
                window.jsclictagger_worker._jct_transactions = {};
                worker = window.jsclictagger_worker;
                worker.addEventListener("message", function (e) {
                    var err;
                    if (!e.data.tx) {
                        throw new Error("Message has no transaction ID " + e.data);
                    }
                    if (!worker._jct_transactions[e.data.tx]) {
                        throw new Error("No promise for transaction ID " + e.data.tx);
                    }
                    if (e.data.error) {
                        err = new DisplayError(e.data.error);
                        err.level = e.data.level || "error";
                        worker._jct_transactions[e.data.tx].reject(err);
                        delete worker._jct_transactions[e.data.tx];
                    } else if (e.data.done === false) {
                        // Generator, collate parts into an array
                        worker._jct_transactions[e.data.tx].rv = worker._jct_transactions[e.data.tx].rv || [];
                        worker._jct_transactions[e.data.tx].rv.push(e.data.rv);
                    } else if (worker._jct_transactions[e.data.tx].rv) {
                        // Return results of generator
                        worker._jct_transactions[e.data.tx].resolve(worker._jct_transactions[e.data.tx].rv);
                        delete worker._jct_transactions[e.data.tx];
                    } else {
                        // Call relevant resolve, throw away
                        worker._jct_transactions[e.data.tx].resolve(e.data.rv);
                        delete worker._jct_transactions[e.data.tx];
                    }
                });
            }

            // Send method call as request
            transactionId = crypto.randomUUID();
            worker._jct_transactions[transactionId] = {resolve: resolve, reject: reject};
            worker.postMessage({
                tx: transactionId,
                method: propName.toString(),
                kwargs: kwargs || {},
            });
        });
    };
} });
