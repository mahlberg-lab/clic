"use strict";
/*jslint plusplus: true */
/*global Promise */
var test = require('tape');
var proxyquire =  require('proxyquire');

var req_count = 0;

global.window = { setTimeout: setTimeout };
var PageConcordance = proxyquire('../lib/page_concordance.js', {
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
function mock_state(input) {
    return {
        state: function (x) {
            return input[x];
        },
    };
}

// Turn a space-separated list of words into a KwicTerms lookup
function kwic_terms(words) {
    var out = {};
    words.split(' ').map(function (w) {
        out[w] = 1;
    });
    return out;
}

test('post_process', function (t) {
    var content_el = { children: [] },
        pt = new PageConcordance(content_el);

    return Promise.resolve(true).then(function () {
        // Ignore all columns
        return pt.post_process(
            mock_state({tag_columns: {}, tag_column_order: []}),
            kwic_terms('tongue'),
            [{ignore: true, reverse: true}, {ignore: true}, {ignore: true}],
            {data: [
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'us', [0, 2, 4]],
                    ["into", '.', [0]],
                    [['parp']], // Book ID
                    [[1234]], // Word ID
                ],
            ]}
        );
    }).then(function (data) {
        t.deepEqual(data.data[0].DT_RowId, 'parp1234', 'Formed row ID from book/word');
        t.deepEqual(data.data[0].DT_RowClass, '', 'No matches, RowClass (explicitly) empty');
        t.deepEqual(data.data[0].kwic, 0, 'No matches, kwic 0');
        t.deepEqual(data.allWords, {}, 'Ignoring all rows, so no words found');

    }).then(function () {
        // Match one
        return pt.post_process(
            mock_state({tag_columns: {}, tag_column_order: []}),
            kwic_terms('gotten'),
            [{ignore: true, reverse: true}, {start: 0, stop: 10}, {start: 0, stop: 10}],
            {data: [
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'us', [0, 2, 4]],
                    ["into", '.', [0]],
                    [['parp']], // Book ID
                    [[1238]], // Word ID
                ],
            ]}
        );
    }).then(function (data) {
        t.deepEqual(data.data[0].DT_RowId, 'parp1238', 'Formed row ID from book/word');
        t.deepEqual(data.data[0].DT_RowClass, 'kwic-highlight-2', "Colour classes start at 2");
        t.deepEqual(data.data[0].kwic, 1, 'Overall 1 match');
        t.deepEqual(data.allWords, {'you\'ve': true, gotten: true, us: true, into: true}, 'Found words in middle, right');

    }).then(function () {
        t.end();
    }).catch(function (err) {
        setTimeout(function () { throw err; }, 0);
        t.end();
    });
});

