"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true, nomen: true */
/*global crypto, Promise, Proxy, Worker */
var DisplayError = require('./alerts.js').prototype.DisplayError;

// Create flexiclic, which proxies any method calls through to python
module.exports.flexiclic = new Proxy({}, { get: function (target, propName) {
    if (propName === "shutdown") {
        return function () {
            if (target._worker) {
                target._worker.terminate();
                target._worker = undefined;
            }
            return Promise.resolve();
        };
    }

    // Assume any get is fetching a method, construct closure in response
    return function (kwargs) {
        return new Promise(function (resolve, reject) {
            var transactionId;

            // If not present, start webworker & listen to transactions
            if (!target._worker) {
                target._transactions = {};
                target._worker = new Worker("/flexiclic/flexiclicWorker.js");
                target._worker.addEventListener("message", function (e) {
                    var err;
                    if (!e.data.tx) {
                        throw new Error("Message has no transaction ID " + e.data);
                    }
                    if (!target._transactions[e.data.tx]) {
                        throw new Error("No promise for transaction ID " + e.data.tx);
                    }
                    if (e.data.error) {
                        err = new DisplayError(e.data.error);
                        err.level = e.data.level || "error";
                        target._transactions[e.data.tx].reject(err);
                        delete target._transactions[e.data.tx];
                    } else if (e.data.done === false) {
                        // Generator, collate parts into an array
                        target._transactions[e.data.tx].rv = target._transactions[e.data.tx].rv || [];
                        target._transactions[e.data.tx].rv.push(e.data.rv);
                    } else if (target._transactions[e.data.tx].rv) {
                        // Return results of generator
                        target._transactions[e.data.tx].resolve(target._transactions[e.data.tx].rv);
                        delete target._transactions[e.data.tx];
                    } else {
                        // Call relevant resolve, throw away
                        target._transactions[e.data.tx].resolve(e.data.rv);
                        delete target._transactions[e.data.tx];
                    }
                });
            }

            // Send method call as request
            transactionId = crypto.randomUUID();
            target._transactions[transactionId] = {resolve: resolve, reject: reject};
            target._worker.postMessage({
                tx: transactionId,
                method: propName.toString(),
                kwargs: kwargs || {},
            });
        });
    };
} });
