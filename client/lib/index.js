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
            window.ga('set', 'page', window.location.href);
            window.ga('send', 'pageview');
        }

        if (!page || page_state.doc() !== current_page) {
            page = new PageConstructor(document.getElementById('content'));
            current_page = page_state.doc();
        }
        if (!cb) {
            cb = new ControlBar(document.getElementById('control-bar'));
        }

        return Promise.all([
            page.reload(page_state).catch(function (err) { alerts.error(err); console.log(err); }),
            cb.reload(page_state).catch(function (err) { alerts.error(err); console.log(err); }),
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
    }).then(function () {
        document.body.classList.toggle('loading', false);
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
