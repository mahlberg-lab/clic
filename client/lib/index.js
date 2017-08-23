"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
require('./polyfill.js');
var parse_qs = require('./parse_qs.js').parse_qs;
var ControlBar = require('./controlbar.js');

var page_classes = {
    '/concordance': require('./page_concordance.js'),
    '': require('./page_static.js'),
};

var page, cb, current_page = null;

function page_load(e) {
    var page_opts = parse_qs(document.location),
        PageConstructor = page_classes[page_opts.doc] || page_classes[''];

    return Promise.resolve(page_opts).then(function (page_opts) {
        if (!page || page_opts.doc !== current_page) {
            page = new PageConstructor(document.getElementById('content'));
        }
        if (!cb) {
            cb = new ControlBar(document.getElementById('control-bar'));
        }

        return Promise.all([
            page.reload(page_opts),
            cb.reload(page_opts),
        ]);
    }).then(function (rvs) {
        rvs.forEach(function (rv) {
            // TODO: Display messages, etc.
            if (rv && rv.message) {
                console.log(rv);
            }
        });
    }).catch(function (err) {
        console.log("TODO: " + err);
        throw err;
    });
}

if (window) {
    document.addEventListener('DOMContentLoaded', page_load);
    window.addEventListener('popstate', page_load);
}
