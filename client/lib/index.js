"use strict";
/*jslint todo: true, regexp: true, browser: true */
/*global Promise */
var ControlBar = require('./controlbar.js');
var Analytics = require('./analytics.js');
var PagePromise = require('./page_promise.js');

var page_classes = {
    '/concordance': require('./page_concordance.js'),
    '/clusters': require('./page_cluster.js'),
    '/subsets': require('./page_subset.js'),
    '/keywords': require('./page_keyword.js'),
    '/chapter': require('./page_chapter.js'),
    '/count': require('./page_count.js'),
    '/': require('./page_contents.js'),
    '/carousel': function () {
        this.page_title = function () {
            // NB: This should be only needed until we're done with the carousel test
            return "Carousel example test";
        };
        this.reload = function () {
            return Promise.resolve({});
        };
    },
    '': function () {
        this.page_title = function () {
            return "Page not found";
        };
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

    'table-type': 'basic',
    'table-filter': '',
    'selected_rows': [],

    'book': '',
    'chapter_num': 1,
    'chapter_id': -1,
    'word-highlight': '0:0',
    'chap-highlight': [],
};

var page, cb, ga, current_page = null;

function select_components(page_state) {
    var PageConstructor;

    if (!page || page_state.doc() !== current_page) {
        PageConstructor = page_classes[page_state.doc()] || page_classes[''];
        page = new PageConstructor(document.getElementById('content'));
        current_page = page_state.doc();
    }

    if (!cb) {
        cb = new ControlBar(document.getElementById('control-bar'));
    }

    if (!ga) {
        ga = new Analytics();
    }

    window.document.title = page.page_title(page_state);
    return [page, cb, ga];
}

var pp = new PagePromise(select_components, state_defaults);

if (window) {
    pp.wire_events();
}
