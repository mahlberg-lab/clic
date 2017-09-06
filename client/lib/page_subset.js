"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var PageTable = require('./page_table.js');
var dt_utils = require('./dt_utils.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

function isWord(s) {
    return (/\w/).test(s);
}

// PageSubset inherits PageTable
function PageSubset() {
    return PageTable.apply(this, arguments);
}
PageSubset.prototype = Object.create(PageTable.prototype);

PageSubset.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.non_tag_columns = [
        { data: "kwic", visible: false, sortable: false, searchable: false },
        { title: "", defaultContent: "", sortable: false, searchable: false },
        { title: "Left", data: "0", render: dt_utils.renderReverseTokenArray, class: "contextLeft text-right" }, // Left
        { title: "Node", data: "1", render: dt_utils.renderForwardTokenArray, class: "contextNode hilight" }, // Node
        { title: "Right", data: "2", render: dt_utils.renderForwardTokenArray, class: "contextRight" }, // Right
        { title: "Book", data: "3.0", class: "metadataColumn", searchable: false }, // Book
        { title: "Ch.", data: "3.1", class: "metadataColumn", searchable: false }, // Chapter
        { title: "Par.", data: "3.2", class: "metadataColumn", searchable: false }, // Paragraph
        { title: "Sent.", data: "3.3", class: "metadataColumn", searchable: false }, // Sentence
        { title: "In&nbsp;bk.", data: "4", render: dt_utils.renderPosition, searchable: false, orderData: [5, 9] }, // Book graph
    ];
    this.table_opts.orderFixed = { pre: [['0', 'desc']] };
    this.table_opts.order = [[9, 'asc']];
    this.table_opts.language = {
        search: "Filter subset:",
    };
};

PageSubset.prototype.reload = function reload(page_state) {
    var tag_list = Object.keys(page_state.state('tag_columns', {}));

    function renderBoolean(data, type, full, meta) {
        return data ? "✓" : " ";
    }

    // Generate column list based on tag_columns
    this.table_opts.columns = this.table_opts.non_tag_columns.concat(tag_list.map(function (t) {
        return { title: t, data: t, render: renderBoolean, class: "tagColumn" };
    }));

    return PageTable.prototype.reload.apply(this, arguments);
};

PageSubset.prototype.reload_data = function reload(page_state) {
    var api_opts = {};

    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora', []);
    api_opts.subset = page_state.arg('subset-subset', 'shortsus');

    if (!api_opts.corpora || api_opts.corpora.length === 0) {
        throw new DisplayError("Please select a corpora to search in", "warn");
    }

    return api.get('subset', api_opts).then(function (data) {
        var i, j, allWords = {}, totalMatches = 0,
            tag_state = page_state.state('tag_columns', {}),
            tag_list = Object.keys(tag_state);

        data = data.results;

        for (i = 0; i < data.length; i++) {
            // TODO: Assume book+word_id is unique for now. Server-generate this
            data[i].DT_RowId = data[i][3][0] + data[i][4][0];

            data[i].kwic = 0; //TODO:

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
PageSubset.prototype.generateKwicRow = function (d, allWords) {
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

module.exports = PageSubset;
