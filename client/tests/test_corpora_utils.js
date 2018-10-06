"use strict";
/*jslint todo: true, regexp: true, nomen: true, browser: true */
var test = require('tape');

var corpora_utils = require('../lib/corpora_utils.js');

test('regions_to_html', function (t) {
    var out;

    out = corpora_utils.regions_to_html("I don't know. Have you tried swimming?", [
        ['chapter.sentence', 0, 13],
        ['aardvark', 2, 7],
        ['chapter.sentence', 13, 38],
    ]).split('</span>');
    t.deepEqual(out, [
        '<span>',
        '<span class="boundary-sentence">',
        '<span class="chapter-sentence">I ',
        '<span class="chapter-sentence aardvark">don\'t',
        '<span class="chapter-sentence"> know.',
        '<span class="boundary-sentence">',
        '<span class="boundary-sentence">',
        '<span class="chapter-sentence"> Have you tried swimming?',
        '<span class="boundary-sentence">',
        '',
    ], "Can nest regions, chapter.sentence gets boundaries as a special case");

    out = corpora_utils.regions_to_html("I don't know. Have you tried swimming?", [
        ['chapter.sentence', 0, 13],
        ['aardvark', 2, 18],
        ['chapter.sentence', 13, 38],
    ]).split('</span>');
    t.deepEqual(out, [
        '<span>',
        '<span class="boundary-sentence">',
        '<span class="chapter-sentence">I ',
        '<span class="chapter-sentence aardvark">don\'t know.',
        '<span class="boundary-sentence">',
        '<span class="boundary-sentence">',
        '<span class="aardvark chapter-sentence"> Have',
        '<span class="chapter-sentence"> you tried swimming?',
        '<span class="boundary-sentence">',
        '',
    ], "Can overlap regions, apply all relevant tags");

    t.end();
});

test('chapter_headings', function (t) {
    var out;

    out = corpora_utils.chapter_headings("heading 1, heading 2 and heading three", [
        ['chapter.title', 0, 9, 1],
        ['chapter.title', 11, 20, 2],
        ['chapter.title', 25, 39, 3],
    ]);
    t.deepEqual(out, [
        { id: 1, title: 'heading 1' },
        { id: 2, title: 'heading 2' },
        { id: 3, title: 'heading three' },
    ], "Can nest regions, chapter.sentence gets boundaries as a special case");

    t.end();
});
