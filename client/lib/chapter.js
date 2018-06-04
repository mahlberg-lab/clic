"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var ControlBar = require('./controlbar.js');
var Analytics = require('./analytics.js');
var PagePromise = require('./page_promise.js');
var Chapter = require('./page_chapter.js');

var state_defaults = {
    'start': 0,
    'end': 0,
    'book': '',
    'chapter_num': 1,
    'chapter_id': -1,
    'chap-highlight': [],
};

var page, cb, ga;

function select_components(page_state) {
    if (!page) {
        page = new Chapter(document.getElementById('content'));
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
