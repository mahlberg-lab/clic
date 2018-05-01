"use strict";
/*jslint plusplus: true, nomen: true */
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
        arg: function (x) {
            return input[x];
        },
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

test('post_process', function (t) {
    var content_el = { children: [] },
        pt = new PageConcordance(content_el);

    return Promise.resolve(true).then(function () {
        // Ignore all columns
        var data = pt.post_process(
            mock_state({tag_columns: {}, tag_column_order: []}),
            kwic_terms('tongue'),
            [{ignore: true, reverse: true}, {ignore: true}, {ignore: true}],
            {data: [
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'us', [0, 2, 4]],
                    ["into", '.', [0]],
                    ['parp', 0, 100, 103], // Book / chapter / offset start / offset end
                    [0, 0], // para-in-chap, sent-in-chap
                ],
            ], chapter_start: {
                parp: {0: 100},
            }, version: 33}
        );
        t.deepEqual(data.data[0].DT_RowId, 'parp:0:100', 'Formed row ID from book/word');
        t.deepEqual(data.data[0].DT_RowClass, '', 'No matches, RowClass (explicitly) empty');
        t.deepEqual(data.data[0].kwic, 0, 'No matches, kwic 0');
        t.deepEqual(data.allWords, {}, 'Ignoring all rows, so no words found');
        t.deepEqual(pt.extra_info, ['from 1 book'], "Extra info updated");

    }).then(function () {
        // Match one
        var data = pt.post_process(
            mock_state({tag_columns: {}, tag_column_order: []}),
            kwic_terms('gotten'),
            [{ignore: true, reverse: true}, {start: 0, stop: 10}, {start: 0, stop: 10}],
            {data: [
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'us', [0, 2, 4]],
                    ["into", '.', [0]],
                    ['parp', 0, 120, 123], // Book / chapter / offset start / offset end
                    [0, 0], // para-in-chap, sent-in-chap
                ],
            ], chapter_start: {
                parp: {0: 100},
            }, version: 33}
        );
        t.deepEqual(data.data[0].DT_RowId, 'parp:0:120', 'Formed row ID from book/word');
        t.deepEqual(data.data[0].DT_RowClass, 'kwic-highlight-2', "Colour classes start at 2");
        t.deepEqual(data.data[0].kwic, 1, 'Overall 1 match');
        t.deepEqual(data.allWords, {'you\'ve': true, gotten: true, us: true, into: true}, 'Found words in middle, right');
        t.deepEqual(pt.extra_info, [
            'from 1 book',
            '1 line / 1 book with 1 KWIC match',
        ], "Extra info updated");

    }).then(function () {
        // Group by books for distribution plot
        var data = pt.post_process(
            mock_state({tag_columns: {}, tag_column_order: [], 'table-type': 'dist_plot'}),
            kwic_terms('gotten us'),
            [{ignore: true, reverse: true}, {start: 0, stop: 10}, {start: 0, stop: 10}],
            {data: [
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'us', [0, 2, 4]],
                    ["into", '.', [0]],
                    ['parp', 99, 100, 103], // Book / chapter / offset start / offset end
                    [0, 0], // para-in-chap, sent-in-chap
                ],
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'out', [0, 2, 4]],
                    ["of", '.', [0]],
                    ['slarp', 99, 100, 103], // Book / chapter / offset start / offset end
                    [0, 0], // para-in-chap, sent-in-chap
                ],
                [
                    ['a', ' ', 'fine', ' ', 'mess', [0, 2, 4]],
                    ["you've", ' ', 'gotten', ' ', 'away', [0, 2, 4]],
                    ["from", '.', [0]],
                    ['parp', 99, 100, 103], // Book / chapter / offset start / offset end
                    [0, 0], // para-in-chap, sent-in-chap
                ],
            ], chapter_start: {
                parp: {0: 100, _end: 5555},
                slarp: {0: 100, _end: 2222},
            }, version: 33}
        );

        t.deepEqual(data.version, 33, "Data version preserved");
        t.deepEqual(data.data[0][0], "parp", "First row for parp");
        t.deepEqual(data.data[0].DT_RowId, "parp", "First row for parp");
        t.deepEqual(data.data[0][1].length, 2, "2 parp sub-rows");
        t.deepEqual(data.data[0][1][0].kwic, 2, '2 matches in first sub-row');
        t.deepEqual(data.data[0][1][1].kwic, 1, '1 match in second sub-row');
        t.deepEqual(data.data[0][1].max_kwic, 2, 'Maximum 2 matches in row');
        t.deepEqual(data.data[0][1].kwic_count, 2, '2 KIWC matches in row');
        t.deepEqual(data.data[0].rel_freq, '360.04', 'Relative frequency');

        t.deepEqual(data.data[1][0], "slarp", "Second row for slarp");
        t.deepEqual(data.data[1].DT_RowId, "slarp", "Second row for slarp");
        t.deepEqual(data.data[1][1].length, 1, "1 slarp sub-row");
        t.deepEqual(data.data[1][1][0].kwic, 1, '1 match in first sub-row');
        t.deepEqual(data.data[1][1].max_kwic, 1, 'Maximum 1 match in row');
        t.deepEqual(data.data[1][1].kwic_count, 1, '1 KIWC match in row');
        t.deepEqual(data.data[1].rel_freq, '450.05', 'Relative frequency');

    }).then(function () {
        t.end();
    }).catch(function (err) {
        setTimeout(function () { throw err; }, 0);
        t.end();
    });
});

test('post_process:extra_info', function (t) {
    function ei(data, chapter_start, table_type) {
        var content_el = { children: [] },
            pt = new PageConcordance(content_el);

        pt.post_process(
            mock_state({tag_columns: {}, tag_column_order: [], 'table-type': table_type || 'basic'}),
            kwic_terms('ape gorilla chimp'),
            [{ignore: true, reverse: true}, {start: 0, stop: 10}, {ignore: true}],
            {
                data: data,
                chapter_start: chapter_start,
                version: 33,
            }
        );
        return pt.extra_info;
    }

    t.deepEqual(ei([
    ], {
    }), [
        "from 0 books",
    ], "Books / matches allowed to be empty");

    t.deepEqual(ei([
        string_to_line("", "No monkeying about", ""),
    ], { "AgnesG": {0: 0, _end: 5555} }), [
        "from 1 book",
    ], "We just count books");

    t.deepEqual(ei([
    ], { "AgnesG": {0: 0, _end: 5555}, "AgnesH": {0: 0, _end: 5555} }), [
        "from 2 books",
    ], "We just count books");

    t.deepEqual(ei([
        string_to_line("", "An ape", "", ['AgnesG', 99, 100, 103]),
        string_to_line("", "ape a gorilla", "", ['AgnesG', 99, 100, 103]),
        string_to_line("", "ape a gorilla", "", ['AgnesH', 99, 100, 103]),
        string_to_line("", "chimp ape gorilla", "", ['AgnesH', 99, 100, 103]),
        string_to_line("", "chimp ape gorilla", "", ['AgnesH', 99, 100, 103]),
        string_to_line("", "chimp ape gorilla", "", ['AgnesH', 99, 100, 103]),
        string_to_line("", "No monkeying about", "", ['AgnesG', 99, 100, 103]),
    ], { "AgnesG": {0: 100, _end: 5555}, "AgnesH": {0: 100, _end: 5555} }), [
        "from 2 books",
        '3 lines / 1 book with 3 KWIC matches',
        '2 lines / 2 books with 2 KWIC matches',
        '1 line / 1 book with 1 KWIC match'
    ], "We show each group of KWIC matches in reverse order");

    t.end();
});
