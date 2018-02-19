"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
require('./polyfill.js');
var State = require('./state.js');
var ControlBar = require('./controlbar.js');
var Alerts = require('./alerts.js');

var page_classes = {
    '/concordance': require('./page_concordance.js'),
    '/clusters': require('./page_cluster.js'),
    '/subsets': require('./page_subset.js'),
    '/keywords': require('./page_keyword.js'),
    '/': require('./page_contents.js'),
    '': function (content_div) {
        this.reload = function (page_state) {
            throw new Error("Unknown page: " + page_state.doc());
        };
    },
};

var state_defaults = {
    'corpora': [],
    'conc-subset': 'all',
    'conc-q': '',
    'conc-type': 'whole',
    'subset-subset': '',
    'kwic-span': '-5:5',
    'kwic-dir': 'start',
    'kwic-int-start': '3',
    'kwic-int-end': '3',
    'kwic-terms': [],
    'refcorpora': [],
    'subset': '',
    'refsubset': '',
    'clusterlength': 1,
    'pvalue': '0.0001',

    'tag_columns': {},
    'tag_column_order': [],
    'tag_column_selected': '',

    'table-metadata': 'show',
    'table-filter': '',
    'selected_rows': [],
};

var page, cb, alerts, current_page = null;

function page_load(e) {
    var page_state = new State(window, state_defaults),
        alerts = new Alerts(document.getElementById('alerts')),
        PageConstructor = page_classes[page_state.doc()] || page_classes[''];

    return Promise.resolve(page_state).then(function (page_state) {
        alerts.clear();
        document.body.classList.toggle('loading', true);

        if (window.ga) {
            window.ga('set', 'location', window.location.href);
            window.ga('send', 'pageview');
        }

        if (!page || page_state.doc() !== current_page) {
            page = new PageConstructor(document.getElementById('content'));
            current_page = page_state.doc();
        }
        if (!cb) {
            cb = new ControlBar(document.getElementById('control-bar'));
        }

        return Promise.all([page, cb].map(function (x) {
            return x.reload(page_state).catch(function (err) {
                // Turn any error output back into a level: { message: ... } object
                var rv = { a: alerts.err_to_alert(err) };

                rv[rv.a[1]] = rv.a[0];
                return rv;
            });
        }));
    }).then(function (rvs) {
        rvs.forEach(function (rv) {
            if (rv && rv.info) { alerts.show(rv.info, 'info'); }
            if (rv && rv.warn) { alerts.show(rv.warn, 'warn'); }
            if (rv && rv.error) { alerts.show(rv.error, 'error'); }
        });

        if (rvs[0]) {
            cb.new_data(rvs[0]);
        }
        document.body.classList.toggle('loading', false);
    }).catch(function (err) {
        alerts.error(err);
        document.body.classList.toggle('loading', false);
        throw err;
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
