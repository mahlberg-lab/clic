"use strict";
var Analytics = require('./analytics.js');
var PagePromise = require('./page_promise.js');

var page_classes = {
    '/concordance': require('./page_concordance.js'),
    '/clusters': require('./page_cluster.js'),
    '/subsets': require('./page_subset.js'),
    '/flexiconc': require('./page_flexiconc.js'),
    '/keywords': require('./page_keyword.js'),
    '/text': require('./page_text.js'),
    '/corpus': require('./page_corpus.js'),
    '/count': require('./page_count.js'),
    '/': require('./page_contents.js'),
    '': function () {
        this.page_title = function () {
            return "Page not found";
        };
        this.reload = function (page_state) {
            throw new Error("Unknown page: " + page_state.doc());
        };
    },
};

var controlbar_classes = {
    '/flexiconc': require('./controlbar_flexiconc.js'),
    '/corpus': require('./controlbar_corpus.js'),
    '': require('./controlbar.js'),
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

    'fc-select-type': "",
    'fc-select': "[]",
    'fc-path': "1",
    'fc-all-paths': {},

    'book': '',
    'chapter_num': 0,
    'chapter_id': -1,
    'word-highlight': [],
    'scroll-pos': -1,
    'chap-highlight': [],

    'corpus-editoractive': 'no',
    'corpus-content': '',
    'corpus-regions': [],
    'corpus-filename': 'clic-book.txt',
};

var page, cb, analytics, current_page = null;

function select_components(page_state) {
    var PageConstructor, ControlBarConstructor, deconstructors = [];

    if (!page || page_state.doc() !== current_page) {
        if (page && page.shutdown) {
            deconstructors.push({ reload: page.shutdown.bind(page) });
        }
        PageConstructor = page_classes[page_state.doc()] || page_classes[''];
        page = new PageConstructor(document.getElementById('content'));
    }

    if (!cb || page_state.doc() !== current_page) {
        if (cb && cb.shutdown) {
            deconstructors.push({ reload: cb.shutdown.bind(cb) });
        }
        ControlBarConstructor = controlbar_classes[page_state.doc()] || controlbar_classes[''];
        cb = new ControlBarConstructor(document.getElementById('control-bar'));
    }

    if (!analytics) {
        analytics = new Analytics();
    }

    current_page = page_state.doc();
    window.document.title = page.page_title(page_state);
    return deconstructors.concat([cb, page, analytics]);
}

var pp = new PagePromise(select_components, state_defaults);

if (window) {
    pp.wire_events();
}
