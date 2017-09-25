"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var PageTable = require('./page_table.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

function escapeHtml(tag, s) {
    // https://bugs.jquery.com/ticket/11773
    return '<' + tag + '>' + (String(s)
        .replace(/&(?!\w+;)/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')) + '</' + tag + '>';
}

function isWord(s) {
    return (/\w/).test(s);
}

// Column is an array of tokens, mark these up as words, only sort on word content
function renderTokenArray(data, type, full, meta) {
    var i, t, count = 0, out = "";

    if (type === 'display') {
        for (i = 0; i < data.length; i++) {
            out += escapeHtml(isWord(data[i]) ? 'mark' : 'span', data[i]);
        }

        return '<div class="' +
            'm' + (data.matches[0] || '0') +
            (data.kwicSpan.reverse ? ' r' : ' l') +
            '">' + out + '</div>';
    }

    if (type === 'export') {
        return data.join("");
    }

    for (i = 0; i < data.length; i++) {
        t = data[data.kwicSpan.reverse ? data.length - i - 1 : i];
        if (isWord(t)) {
            count++;
            out += t + ":";
            if (count >= 3) {
                return out;
            }
        }
    }
    return out;
}

/* Column represents a fractional position in book */
function renderPosition(data, type, full, meta) {
    var xVal;

    if (type === 'display') {
        xVal = (data[0] / data[1]) * 50; // word in book / total word count
        return '<a class="bookLink" title="Click to display concordance in book" target="_blank"' +
               ' href="/chapter?chapter_id=' + data[2] + '&start=' + data[3] + '&end=' + data[4] + '" >' +
               '<svg width="50px" height="15px" xmlns="http://www.w3.org/2000/svg">' +
               '<rect x="0" y="4" width="50" height="7" fill="#ccc"/>' +
               '<line x1="' + xVal + '" x2="' + xVal + '" y1="0" y2="15" stroke="black" stroke-width="2px"/>' +
               '</svg></a>';
    }

    if (type === 'export') {
        return data[0] + '/' + data[1];
    }

    return data[0];
}

// PageConcordance inherits PageTable
function PageConcordance() {
    return PageTable.apply(this, arguments);
}
PageConcordance.prototype = Object.create(PageTable.prototype);

PageConcordance.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.autoWidth = false;
    this.table_opts.non_tag_columns = [
        { data: "kwic", visible: false, sortable: false, searchable: false },
        { title: "", defaultContent: "", width: "3rem", sortable: false, searchable: false },
        { title: "Left", data: "0", render: renderTokenArray, class: "context left" }, // Left
        { title: "Node", data: "1", render: renderTokenArray, class: "context node" }, // Node
        { title: "Right", data: "2", render: renderTokenArray, class: "context right" }, // Right
        { title: "Book", data: "3.0", class: "metadataColumn", searchable: false }, // Book
        { title: "Ch.", data: "3.1", class: "metadataColumn", searchable: false }, // Chapter
        { title: "Par.", data: "3.2", class: "metadataColumn", searchable: false }, // Paragraph
        { title: "Sent.", data: "3.3", class: "metadataColumn", searchable: false }, // Sentence
        { title: "In&nbsp;bk.", data: "4", width: "52px", render: renderPosition, searchable: false, orderData: [5, 9] }, // Book graph
    ];
    this.table_count_column = 1;
    this.table_opts.orderFixed = { pre: [['0', 'desc']] };
    this.table_opts.order = [[9, 'asc']];
};

PageConcordance.prototype.reload = function reload(page_state) {
    var tag_column_order = page_state.state('tag_column_order', []);

    function renderBoolean(data, type, full, meta) {
        return data ? "✓" : " ";
    }

    // Generate column list based on tag_columns
    this.table_opts.columns = this.table_opts.non_tag_columns.concat(tag_column_order.map(function (t) {
        return { title: "<div>" + t + "</div>", data: t, width: "2rem", render: renderBoolean, class: "tagColumn" };
    }));
    this.table_el.classList.toggle('hasTagColumns', tag_column_order.length > 0);

    return PageTable.prototype.reload.apply(this, arguments);
};

PageConcordance.prototype.reload_data = function reload(page_state) {
    var self = this,
        kwicTerms = {},
        kwicSpan = [],
        api_opts = {};

    // Values has 2 values, "(min):(max)", which we treat to be
    // min and max span inclusive, viz.
    //      [0]<------------------------->[1]
    // -5 : -4 : -3 : -2 : -1 |  1 :  2 :  3 :  4 :  5
    // L5 : L4 : L3 : L2 : L1 | R1 : R2 : R3 : R4 : R5
    // Output a configuration suitable for testList
    function parseKwicSpan(values) {
        var out = [{ignore: true}, {ignore: true}, {ignore: true}],
            ks = values.split(':');

        if (ks[0] < 0) {
            out[0] = {
                start: -Math.min(ks[1], -1),
                stop: -ks[0],
                reverse: true,
            };
        }

        if (ks[1] >= 0) {
            out[2] = {
                start: Math.max(ks[0], 1),
                stop: ks[1],
            };
        }

        return out;
    }
    kwicSpan = parseKwicSpan(page_state.arg('kwic-span', '-5:5'));

    (page_state.arg('kwic-terms', [])).map(function (t, i) {
        if (t) {
            kwicTerms[t.toLowerCase()] = i + 1;
        }
    });

    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora', []);
    api_opts.subset = page_state.arg('conc-subset', 'all');
    api_opts.q = page_state.arg('conc-q', '');

    if (api_opts.corpora.length === 0) {
        throw new DisplayError("Please select a corpus to search in", "warn");
    }
    if (!api_opts.q) {
        throw new DisplayError("Please provide some terms to search for", "warn");
    }

    if (page_state.arg('conc-type', 'whole') === 'any') {
        api_opts.q = api_opts.q.split(/(\s+)/).filter(function (t) {
            return (/\w/).test(t);
        });
    }

    return api.get('concordance', api_opts).then(function (data) {
        var i, j, r, allWords = {}, totalMatches = 0,
            tag_state = page_state.state('tag_columns', {}),
            tag_column_order = page_state.state('tag_column_order', []);

        data = data.data;

        for (i = 0; i < data.length; i++) {
            // TODO: Assume book+word_id is unique for now. Server-generate this
            data[i].DT_RowId = data[i][3][0] + data[i][4][0];

            // Add KWICGrouper match column
            r = self.generateKwicRow(kwicTerms, kwicSpan, data[i], allWords);
            if (r > 0) {
                totalMatches++;

                // Add classes for row highlighting
                data[i].DT_RowClass = 'kwic-highlight-' + (r % 4 + 1);
            }

            // Add tag columns
            for (j = 0; j < tag_column_order.length; j++) {
                data[i][tag_column_order[j]] = !!tag_state[tag_column_order[j]][data[i].DT_RowId];
            }
        }

        return {
            allWords: allWords,
            totalMatches: totalMatches,
            data: data,
        };
    });
};

/*
 * Annotate rows with KWICGrouper information, specifically:
 * For each column...
 * - matches: Array of KWIC match positions
 * - kwicSpan: The kwicSpan settings used
 * For the entire row...
 * - kwic: Overall match count
 * Return Overall match count
 */
PageConcordance.prototype.generateKwicRow = function (kwicTerms, kwicSpan, d, allWords) {
    var matchingTypes = {};

    // Check if list (tokens) contains any of the (kwicTerms) between (span.start) and (span.stop) inclusive
    // considering (tokens) in reverse if (span.reverse) is true
    function testList(tokens, span) {
        var i, t, wordCount = 0, out = [];

        if (span.start === undefined) {
            // Ignoring this row
            return out;
        }

        for (i = 0; i < tokens.length; i++) {
            t = tokens[span.reverse ? tokens.length - i - 1 : i];

            if (isWord(t)) {
                t = t.toLowerCase();
                wordCount++;
                allWords[t] = true;
                if (wordCount >= span.start && kwicTerms.hasOwnProperty(t)) {
                    // Matching has started and matches a terms, return which match it is
                    matchingTypes[t] = true;
                    out.push(wordCount);
                }
                if (span.stop !== undefined && wordCount >= span.stop) {
                    // Finished matching now, give up.
                    break;
                }
            }
        }

        return out;
    }

    // Annotate left/node/right with matches, and the span information used
    d[0].matches = testList(d[0], kwicSpan[0]);
    d[1].matches = testList(d[1], kwicSpan[1]);
    d[2].matches = testList(d[2], kwicSpan[2]);
    d[0].kwicSpan = kwicSpan[0];
    d[1].kwicSpan = kwicSpan[1];
    d[2].kwicSpan = kwicSpan[2];
    d.kwic = Object.keys(matchingTypes).length;
    return d.kwic;
};

module.exports = PageConcordance;
