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
