"use strict";

/** Shallow clone of obj */
function shallow_clone(obj) {
    var out = obj.constructor(),
        attr;

    for (attr in obj) {
        if (obj.hasOwnProperty(attr)) {
            out[attr] = obj[attr];
        }
    }

    return out;
}

module.exports.shallow_clone = shallow_clone;
