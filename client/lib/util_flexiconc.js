"use strict";
/*jslint todo: true, regexp: true, unparam: true, nomen: true */

var flatten = require('./flatten.js');

/** convert arg structure into nested object */
module.exports.renest_args = function (args) {
    var out = {};

    flatten.set_values(out, Object.keys(args).map(function (k) {
        if (k.endsWith("[]") || args[k].length > 1) {
            // Explicitly an array, or multiple values, keep array-ness
            return {key: k, value: args[k]};
        }
        if (args[k].length === 1) {
            // Return single value
            return {key: k, value: args[k][0]};
        }
        // Empty list
        return {key: k, value: null};
    }.bind(this)));

    return out;
};

module.exports.renest_all = function (paths) {
    var out = {};

    Object.keys(paths).forEach(function (path_k) {
        if (path_k === "0") {
            // Ignore analysis-tree "path"
            return;
        }

        out[path_k] = module.exports.renest_args(paths[path_k]);
        out[path_k] = out[path_k].algo;
    });
    return out;
};

module.exports.remove_path = function (fcAllPaths, pathToRemove) {
    return Object.fromEntries(Object.entries(fcAllPaths).filter(function (entry) {
        // Remove unrequired path
        return entry[0] !== pathToRemove;
    }).map(function (entry, i) {
        // Re-number remaining paths
        return [i.toString(), entry[1]];
    }));
};
