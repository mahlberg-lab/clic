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
    var cq = this;

    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.columns = [
        { data: "5", render: dt_utils.renderKwicMatch, visible: false, sortable: false, searchable: false },
        { title: "", data: null, render: function () { return ""; }, sortable: false, searchable: false },
        { title: "Left", data: "0", render: dt_utils.renderReverseTokenArray, class: "contextLeft text-right" }, // Left
        { title: "Node", data: "1", render: dt_utils.renderForwardTokenArray, class: "contextNode hilight" }, // Node
        { title: "Right", data: "2", render: dt_utils.renderForwardTokenArray, class: "contextRight" }, // Right
        { title: "Book", data: "3.1", searchable: false }, // Book
        { title: "Ch.", data: "3.2", searchable: false }, // Chapter
        { title: "Par.", data: "3.3", searchable: false }, // Paragraph
        { title: "Sent.", data: "3.4", searchable: false }, // Sentence
        { title: "In&nbsp;bk.", data: "4", render: dt_utils.renderPosition, searchable: false, orderData: [5, 9] }, // Book graph
    ];
    this.table_opts.orderFixed = { pre: [['0', 'desc']] };
    this.table_opts.order = [[9, 'asc']];
    this.table_opts.language = {
        search: "Filter concordance:",
    };
    this.table_opts.createdRow = function (row, data, index) {
        if (row) {
            row.className = cq.getRowClass(data);
        }
    };
};

PageConcordance.prototype.reload_data = function reload(page_opts) {
    var self = this,
        api_opts = {
            testCollection: 'dickens',
            terms: 'hands',
            selectWords: 'whole',
            testIdxMod: 'chapter',
        }; //TODO:

    this.kwicTerms = {};
    this.kwicSpan = [{ignore: true}, {ignore: true}];

    // Values has 2 values, a min and max, which we treat to be
    // min and max span inclusive, viz.
    //      [0]<------------------------->[1]
    // -5 : -4 : -3 : -2 : -1 |  1 :  2 :  3 :  4 :  5
    // L5 : L4 : L3 : L2 : L1 | R1 : R2 : R3 : R4 : R5
    if (this.page_opts['kwic-span-l'] < 0) {
        this.kwicSpan[0] = {
            start: -Math.min(this.page_opts['kwic-span-r'], -1),
            stop: -this.page_opts['kwic-span-l'],
            reverse: true,
            prefix: 'l',
        };
    }
    if (this.page_opts['kwic-span-r'] >= 0) {
        this.kwicSpan[1] = {
            start: Math.max(this.page_opts['kwic-span-l'], 1),
            stop: this.page_opts['kwic-span-r'],
            prefix: 'r',
        };
    }

    (this.page_opts['kwic-terms'].split(/\s+/) || []).map(function (t, i) {
        self.kwicTerms[t.toLowerCase()] = i + 1;
    });

    return api.get('concordance', api_opts).then(function (data) {
        var i, allWords = {}, totalMatches = 0;

        data = data.concordances;
        data.shift();

        // Add KWICGrouper match column
        for (i = 0; i < data.length; i++) {
            data[i].push(self.generateKwicRow(data[i], allWords));

            if (data[i][5] > 1) {
                totalMatches++;
            }
        }

        //TODO: Send allWords, totalMatches back to controlbar
        console.log(["allWords, totalMatches", allWords, totalMatches]);
        return { data: data };
    });
};

/*
 *
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
    kwic_row = [
        0,
        testList(d[0], this.kwicSpan[0], this.kwicTerms),
        testList(d[2], this.kwicSpan[1], this.kwicTerms),
    ];
    kwic_row[0] = Object.keys(matchingTypes).length;

    return kwic_row;
};

PageConcordance.prototype.updateKwicGroup = function () {
    var cq = this,
        allWords = {},
        totalMatches = 0;

    this.concordanceTable.rows().every(function () {
        var d = this.data(),
            new_result = cq.generateKwicRow(d, allWords);

        if (new_result.length > 1) {
            totalMatches++;
        }

        if (d[5].length !== new_result.length || d[5].join(':') !== new_result.join(':')) {
            // Concordance membership has changed, update table
            d[5] = new_result;
            this.node().className = cq.getRowClass(d);
            this.invalidate();
        }
    });

    //TODO: Send allWords, totalMatches back to controlbar
    console.log([allWords, totalMatches]);
    this.concordanceTable.draw();
};

PageConcordance.prototype.getRowClass = function (data) {
    var i, out = '';

    if (data[5].length <= 1) {
        return '';
    }

    out += ' kwic-highlight-' + (data[5][0] % 4 + 1);
    for (i = 1; i < data[5].length; i++) {
        out += ' match-' + data[5][i];
    }

    return out;
};

PageConcordance.prototype.updateKwicGroup = function () {
    var cq = this,
        allWords = {},
        totalMatches = 0;

    this.concordanceTable.rows().every(function () {
        var d = this.data(),
            new_result = cq.generateKwicRow(d, allWords);

        if (new_result.length > 1) {
            totalMatches++;
        }

        if (d[5].length !== new_result.length || d[5].join(':') !== new_result.join(':')) {
            // Concordance membership has changed, update table
            d[5] = new_result;
            this.node().className = cq.getRowClass(d);
            this.invalidate();
        }
    });

    //TODO: Send allWords, totalMatches back to controlbar
    console.log([allWords, totalMatches]);
    this.concordanceTable.draw();
};

module.exports = PageConcordance;
