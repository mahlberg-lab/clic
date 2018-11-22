"use strict";
/*jslint plusplus: true, nomen: true */
/*global Promise */
var test = require('tape');
var proxyquire =  require('proxyquire');

var PageState = require('lib/state.js');

var req_count = 0;

global.window = { setTimeout: setTimeout };
var PageSubset = proxyquire('../lib/page_subset.js', {
    './api.js': {
        get: function (endpoint, qs) {
            return Promise.resolve({
                count: req_count++,
                endpoint: endpoint,
                qs: qs,
            });
        },
    },
});

// Return a fake PageState wrapping the input
// Make a PageState object with given args
function page_state(pathname, search) {
    return new PageState({
        location: {
            pathname: (pathname || '/'),
            search: '?' + (search || ''),
        },
        history: { state: {} },
    }, {
        'corpora': [],
        'tag_columns': {},
        'tag_column_order': [],
        'table-type': 'basic',
        'subset-subset': 'all',
    });
}

// Turn a space-separated list of words into a KwicTerms lookup
function kwic_terms(words) {
    var out = {};
    words.split(' ').map(function (w) {
        out[w] = 1;
    });
    return out;
}

// Turn string(s) into a concordance line
function string_to_line(str_left, str_node, str_right, metadata) {
    function conv(str) {
        var i, words = [], tokens = str ? str.split(/(\s+)/) : [];

        for (i = 0; i < tokens.length; i++) {
            if (tokens[i].search(/\w/) > -1) {
                words.push(i);
            }
        }
        tokens.push(words);

        return tokens;
    }

    return [
        conv(str_left),
        conv(str_node),
        conv(str_right),
        metadata || ['slarp', 99, 100, 103], // Book / chapter / offset start / offset end
        [0, 0], // para-in-chap, sent-in-chap
    ];
}

test('post_process:extra_info', function (t) {
    function ei(data, chapter_start, table_type) {
        var content_el = { children: [] },
            input = { data: data, chapter_start: chapter_start, version: 33 },
            query_string = 'table-type=' + [table_type || 'basic'] + '&subset-subset=longsus',
            pt = new PageSubset(content_el);

        input.word_count_all = {};
        Object.keys(chapter_start).forEach(function (k) {
            input.word_count_all[k] = chapter_start[k]._end;
        });
        pt.post_process(
            page_state('/c', query_string),
            kwic_terms('ape gorilla chimp'),
            [{ignore: true, reverse: true}, {start: 0, stop: 10}, {ignore: true}],
            input
        );
        return pt.extra_info;
    }

    t.deepEqual(ei([
        string_to_line("", "No monkeying about", ""),
    ], { "AgnesG": {0: 0, _end: 5555} }, undefined), [
        '<abbr title="percentage of total words that are in longsus subsets">%age</abbr> 0.05 pm', // (3 / 5555) * 100
        "from 1 book",
    ], "Subsets use %ages, not rel.freq");


    t.end();
});
