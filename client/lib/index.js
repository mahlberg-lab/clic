"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
require('./polyfill.js');
var parse_qs = require('./parse_qs.js').parse_qs;
var ControlBar = require('./controlbar.js');
var Alerts = require('./alerts.js');

var page_classes = {
    '/concordance': require('./page_concordance.js'),
    '/subsets': require('./page_subset.js'),
    '': function (content_div) {
        this.reload = function (page_opts) {
            throw new Error("Unknown page: " + page_opts.doc);
        };
    },
};

var page, cb, alerts, current_page = null;

function page_load(e) {
    var page_opts = parse_qs(document.location),
        alerts = new Alerts(document.getElementById('alerts')),
        PageConstructor = page_classes[page_opts.doc] || page_classes[''];

    return Promise.resolve(page_opts).then(function (page_opts) {
        alerts.clear();

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
            if (rv && rv.message) {
                alerts.show(rv.message);
            }
        });

        if (rvs[0]) {
            return cb.new_data(rvs[0]);
        }
        return;
    }).catch(function (err) {
        alerts.error(err);
        if (!err.level) {
            throw err;
        }
    });
}

function table_selection(e) {
    cb.new_selection(e.detail);
}

if (window) {
    document.addEventListener('DOMContentLoaded', page_load);
    window.addEventListener('popstate', page_load);
    window.addEventListener('replacestate', page_load);
    window.addEventListener('tableselection', table_selection);
}
