"use strict";
/*jslint todo: true, regexp: true, nomen: true, browser: true */
var test = require('tape');

var concordance_utils = require('../lib/concordance_utils.js');

// Turn a space-separated list of words into a KwicTerms lookup
function kwic_terms(words) {
    var out = {};
    words.split(' ').map(function (w) {
        out[w] = 1;
    });
    return out;
}

test('renderTokenArray', function (t) {
    var data, short_data;

    data = ['and', ' ', 'the', ' ', 'hammerhead', '-', 'sh<a>rk', ' ', 'said', ',', ' ', '"', [0, 2, 4, 6, 8]];
    data.matches = [];
    data.kwicSpan = {};

    short_data = ['Flash', '!', [0]];
    short_data.matches = [];
    short_data.kwicSpan = {};

    // Words are marks, space is span, HTML is quoted
    t.equal(concordance_utils.renderTokenArray(data, 'display'),
            '<div class="l">' +
            '<mark>and</mark>' +
            '<span> </span>' +
            '<mark>the</mark>' +
            '<span> </span>' +
            '<mark>hammerhead</mark>' +
            '<span>-</span>' +
            '<mark>sh&lt;a&gt;rk</mark>' +
            '<span> </span>' +
            '<mark>said</mark>' +
            '<span>,</span>' +
            '<span> </span>' +
            '<span>&quot;</span>' +
            '</div>');

    // Reverse mode just changes the div class
    data.kwicSpan = { reverse: true };
    t.equal(concordance_utils.renderTokenArray(data, 'display'),
            '<div class="r">' +
            '<mark>and</mark>' +
            '<span> </span>' +
            '<mark>the</mark>' +
            '<span> </span>' +
            '<mark>hammerhead</mark>' +
            '<span>-</span>' +
            '<mark>sh&lt;a&gt;rk</mark>' +
            '<span> </span>' +
            '<mark>said</mark>' +
            '<span>,</span>' +
            '<span> </span>' +
            '<span>&quot;</span>' +
            '</div>');

    // Matches get added to class
    data.matches = [1, 3];
    t.equal(concordance_utils.renderTokenArray(data, 'display').replace(/>.*/, ">"), '<div class="r m1 m3">');
    data.kwicSpan = {};
    t.equal(concordance_utils.renderTokenArray(data, 'display').replace(/>.*/, ">"), '<div class="l m1 m3">');

    // Sort mode, get first/last three words, ignore whitespace
    t.equal(concordance_utils.renderTokenArray(data, 'sort'),
            'and:the:hammerhead:');
    data.kwicSpan = { reverse: true };
    t.equal(concordance_utils.renderTokenArray(data, 'sort'),
            'said:sh<a>rk:hammerhead:');
    data.kwicSpan = {};

    // Sort mode, short data isn't a problem
    t.equal(concordance_utils.renderTokenArray(short_data, 'sort'),
            'Flash:');
    short_data.kwicSpan = { reverse: true };
    t.equal(concordance_utils.renderTokenArray(short_data, 'sort'),
            'Flash:');

    // Filter and export mode just return string
    t.equal(concordance_utils.renderTokenArray(data, 'filter'),
            'and the hammerhead-sh<a>rk said, "');
    t.equal(concordance_utils.renderTokenArray(data, 'export'),
            'and the hammerhead-sh<a>rk said, "');

    t.end();
});

test('generateKwicRow', function (t) {
    function gkr(kwic_search, node) {
        var row = [[[]], node, [[]]],
            allWords = {};

        concordance_utils.generateKwicRow(
            kwic_terms(kwic_search),
            [{ignore: true, reverse: true}, {start: 0, stop: 10}, {ignore: true}],
            row,
            allWords
        );
        return {
            kwic: row.kwic,
            matches: row[1].matches,
            allWords: Object.keys(allWords).sort(),
        };
    }

    // Terms are normalised as part of the match, so apostrophes/case don't have to match
    // and returned terms in allWords have had apostrophe's normalised
    t.deepEqual(gkr("aren't", ['“', ' ', 'Aren’t', ' ', 'you', ' ', 'capable', [2, 4, 6]]), {
        kwic: 1,
        matches: [1],
        allWords: ['aren\'t', 'capable', 'you'],
    });

    t.end();
});

test('merge_tags', function (t) {
    function mt(old_tc, old_tc_order, new_tc, new_tc_order) {
        return concordance_utils.merge_tags({
            tag_columns: old_tc,
            tag_column_order: old_tc_order,
        }, {
            tag_columns: new_tc,
            tag_column_order: new_tc_order,
        });
    }

    t.deepEqual(mt({}, [], {}, []), {
        tag_columns: {},
        tag_column_order: [],
    }, "Both states empty");

    t.deepEqual(mt({a: {x: 1}}, ['a'], {}, []), {
        tag_columns: {a: {x: 1}},
        tag_column_order: ['a'],
    }, "Empty new_state");

    t.deepEqual(mt({}, [], {a: {x: 1}}, ['a']), {
        tag_columns: {a: {x: 1}},
        tag_column_order: ['a'],
    }, "Empty old_state");

    t.deepEqual(mt({a: {x: 1}}, ['a'], {b: {y: 1}, c: {z: 1}}, ['b', 'c']), {
        tag_columns: {a: {x: 1}, b: {y: 1}, c: {z: 1}},
        tag_column_order: ['a', 'b', 'c'],
    }, "Merge old and new state");

    t.deepEqual(mt({e: {x: 1}}, ['e'], {b: {y: 1}, c: {z: 1}}, ['b', 'c']), {
        tag_columns: {e: {x: 1}, b: {y: 1}, c: {z: 1}},
        tag_column_order: ['e', 'b', 'c'],
    }, "Merge old and new state, ordering preserved");

    t.deepEqual(mt({e: {x: 1}}, ['e'], {b: {y: 1}, c: {z: 1}, e: {x: 2}}, ['b', 'c', 'e']), {
        tag_columns: {e: {x: 1}, b: {y: 1}, c: {z: 1}, "e-1": {x: 2}},
        tag_column_order: ['e', 'b', 'c', 'e-1'],
    }, "Merge old and new state, ordering preserved, non-unique columns renumbered");

    t.end();
});
