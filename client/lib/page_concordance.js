"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var PageTable = require('./page_table.js');
var dt_utils = require('./dt_utils.js');

function isWord(s) {
    return (/\w/).test(s);
}

// PageConcordance inherits PageTable
function PageConcordance() {
    return PageTable.apply(this, arguments);
}
PageConcordance.prototype = Object.create(PageTable.prototype);

PageConcordance.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.non_tag_columns = [
        { data: "kwic", visible: false, sortable: false, searchable: false },
        { title: "", defaultContent: "", sortable: false, searchable: false },
        { title: "Left", data: "0", render: dt_utils.renderReverseTokenArray, class: "contextLeft text-right" }, // Left
        { title: "Node", data: "1", render: dt_utils.renderForwardTokenArray, class: "contextNode hilight" }, // Node
        { title: "Right", data: "2", render: dt_utils.renderForwardTokenArray, class: "contextRight" }, // Right
        { title: "Book", data: "3.1", class: "metadataColumn", searchable: false }, // Book
        { title: "Ch.", data: "3.2", class: "metadataColumn", searchable: false }, // Chapter
        { title: "Par.", data: "3.3", class: "metadataColumn", searchable: false }, // Paragraph
        { title: "Sent.", data: "3.4", class: "metadataColumn", searchable: false }, // Sentence
        { title: "In&nbsp;bk.", data: "4", render: dt_utils.renderPosition, searchable: false, orderData: [5, 9] }, // Book graph
    ];
    this.table_opts.orderFixed = { pre: [['0', 'desc']] };
    this.table_opts.order = [[9, 'asc']];
    this.table_opts.language = {
        search: "Filter concordance:",
    };
};

PageConcordance.prototype.reload = function reload(page_opts) {
    var page_state = window.history.state || {},
        tag_list = Object.keys(page_state.tag_columns || {});

    function renderBoolean(data, type, full, meta) {
        return data ? "✓" : " ";
    }

    // Generate column list based on tag_columns
    this.table_opts.columns = this.table_opts.non_tag_columns.concat(tag_list.map(function (t) {
        return { title: t, data: t, render: renderBoolean, class: "tagColumn" };
    }));

    return PageTable.prototype.reload.apply(this, arguments);
};

PageConcordance.prototype.reload_data = function reload(page_opts) {
    var self = this,
        api_opts = {};

    // Values has 2 values, "(min):(max)", which we treat to be
    // min and max span inclusive, viz.
    //      [0]<------------------------->[1]
    // -5 : -4 : -3 : -2 : -1 |  1 :  2 :  3 :  4 :  5
    // L5 : L4 : L3 : L2 : L1 | R1 : R2 : R3 : R4 : R5
    // Output a configuration suitable for testList
    function parseKwicSpan(values) {
        var out = [{ignore: true}, {ignore: true}],
            ks = values.split(':');

        if (ks[0] < 0) {
            out[0] = {
                start: -Math.min(ks[1], -1),
                stop: -ks[0],
                reverse: true,
                prefix: 'l',
            };
        }

        if (ks[1] >= 0) {
            out[1] = {
                start: Math.max(ks[0], 1),
                stop: ks[1],
                prefix: 'r',
            };
        }

        return out;
    }

    this.kwicTerms = {};
    this.kwicSpan = parseKwicSpan(this.page_opts['kwic-span'] || '-5:5');

    (this.page_opts['kwic-terms'] || "").split(/\s+/).map(function (t, i) {
        if (t) {
            self.kwicTerms[t.toLowerCase()] = i + 1;
        }
    });

    // Mangle page_opts into the API's required parameters
    api_opts.corpora = ['dickens']; //TODO:
    api_opts.subset = this.page_opts['conc-subset'] || 'all';
    api_opts.q = this.page_opts['conc-q'];
    api_opts.type = this.page_opts['conc-type'] || 'whole';

    if (!api_opts.q) {
        throw new Error("Please provide some terms to search for");
    }

    return api.get('concordance', api_opts).then(function (data) {
        var i, j, r, allWords = {}, totalMatches = 0,
            tag_state = window.history.state.tag_columns,
            tag_list = Object.keys(tag_state);

        data = data.concordances;

        for (i = 0; i < data.length; i++) {
            // TODO: Assume book+chap+word_id is unique for now. Server-generate this
            data[i].DT_RowId = data[i][3][0] + data[i][3][2] + ':' + data[i][3][5];

            // Add KWICGrouper match column
            r = self.generateKwicRow(data[i], allWords);
            data[i].kwic = r[0];
            if (r[0] > 0) {
                totalMatches++;

                // Add classes for row highlighting
                data[i].DT_RowClass = 'kwic-highlight-' + (r[0] % 4 + 1);
                for (j = 1; j < r.length; j++) {
                    data[i].DT_RowClass += ' match-' + r[j];
                }
            }

            // Add tag columns
            for (j = 0; j < tag_list.length; j++) {
                data[i][tag_list[j]] = !!tag_state[tag_list[j]][data[i].DT_RowId];
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
 * Return value: [(# of unique types matched), (match position, e.g. "r1"), (match position, e.g. "r2"), ... ]
 */
PageConcordance.prototype.generateKwicRow = function (d, allWords) {
    var matchingTypes = {}, kwic_row;

    // Check if list (tokens) contains any of the (terms) between (span.start) and (span.stop) inclusive
    // considering (tokens) in reverse if (span.reverse) is true
    function testList(tokens, span, terms) {
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
                if (wordCount >= span.start && terms.hasOwnProperty(t)) {
                    // Matching has started and matches a terms, return which match it is
                    matchingTypes[t] = true;
                    out.push(span.prefix + wordCount);
                }
                if (span.stop !== undefined && wordCount >= span.stop) {
                    // Finished matching now, give up.
                    break;
                }
            }
        }

        return out;
    }

    // Find the kwic matches in both left and right, as well as total matches
    kwic_row = [0].concat(
        testList(d[0], this.kwicSpan[0], this.kwicTerms),
        testList(d[2], this.kwicSpan[1], this.kwicTerms)
    );
    kwic_row[0] = Object.keys(matchingTypes).length;

    return kwic_row;
};

module.exports = PageConcordance;
