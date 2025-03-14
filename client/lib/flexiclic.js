"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true, nomen: true */
/*global crypto, Promise, Proxy, Worker */
var DisplayError = require('./alerts.js').prototype.DisplayError;

// Create flexiclic, which proxies any method calls through to python
module.exports.flexiclic = new Proxy({}, { get: function (target, propName) {
    if (propName === "shutdown") {
        return function () {
            if (window.flexiclic_worker) {
                window.flexiclic_worker.terminate();
                window.flexiclic_worker = undefined;
            }
            return Promise.resolve();
        };
    }

    // Assume any get is fetching a method, construct closure in response
    return function (kwargs) {
        return new Promise(function (resolve, reject) {
            var transactionId, worker;

            if (window.parent && window.parent.flexiclic_worker) {
                worker = window.parent.flexiclic_worker;
            } else if (window.flexiclic_worker) {
                worker = window.flexiclic_worker;
            } else {
                // If not present, start webworker & listen to transactions
                window.flexiclic_worker = new Worker("/flexiclic/flexiclicWorker.js");
                window.flexiclic_worker._fc_transactions = {};
                worker = window.flexiclic_worker;
                worker.addEventListener("message", function (e) {
                    var err;
                    if (!e.data.tx) {
                        throw new Error("Message has no transaction ID " + e.data);
                    }
                    if (!worker._fc_transactions[e.data.tx]) {
                        throw new Error("No promise for transaction ID " + e.data.tx);
                    }
                    if (e.data.error) {
                        err = new DisplayError(e.data.error);
                        err.level = e.data.level || "error";
                        worker._fc_transactions[e.data.tx].reject(err);
                        delete worker._fc_transactions[e.data.tx];
                    } else if (e.data.done === false) {
                        // Generator, collate parts into an array
                        worker._fc_transactions[e.data.tx].rv = worker._fc_transactions[e.data.tx].rv || [];
                        worker._fc_transactions[e.data.tx].rv.push(e.data.rv);
                    } else if (worker._fc_transactions[e.data.tx].rv) {
                        // Return results of generator
                        worker._fc_transactions[e.data.tx].resolve(worker._fc_transactions[e.data.tx].rv);
                        delete worker._fc_transactions[e.data.tx];
                    } else {
                        // Call relevant resolve, throw away
                        worker._fc_transactions[e.data.tx].resolve(e.data.rv);
                        delete worker._fc_transactions[e.data.tx];
                    }
                });
            }

            // Send method call as request
            transactionId = crypto.randomUUID();
            worker._fc_transactions[transactionId] = {resolve: resolve, reject: reject};
            worker.postMessage({
                tx: transactionId,
                method: propName.toString(),
                kwargs: kwargs || {},
            });
        });
    };
} });
