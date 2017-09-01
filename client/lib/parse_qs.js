"use strict";
/*jslint todo: true, regexp: true */

/**
  * Querystring-parsing utility
  * @module
  */

/**
  * Parse querystring into an object, separating positional and key/value arguments
  * @param location Generally document.location
  * @return Object representing URL
  * @example
    // page location: /parp/document.html?peep&parp=2=3&poop#!moo=daisy&soup
    parse_qs(document.location)
    // => { doc: '/document.html', args: ['peep', 'poop', 'soup'], parp: ['2=3'], moo: ['daisy']
  */
module.exports.parse_qs = function (location) {
    var out = { "args": [], "doc": location.pathname.replace(/^.*\//, '/') };

    [].concat(
        location.search.replace(/^\?/, '').split(/;|&/),
        location.hash.replace(/^\#!?/, '').split(/;|&/)
    ).filter(function (str) {
        // Remove empty entries from an empty search/hash
        return str.length > 0;
    }).map(function (str) {
        var m = /(.*?)\=(.*)/.exec(str);

        if (m) {
            if (!out[m[1]]) {
                out[m[1]] = [];
            }
            out[m[1]].push(decodeURIComponent(m[2]));
        } else {
            out.args.push(str);
        }
    });
    return out;
};
