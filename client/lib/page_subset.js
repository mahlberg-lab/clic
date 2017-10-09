"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var PageConcordance = require('./page_concordance.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;
var concordance_utils = require('./concordance_utils.js');

// PageSubset inherits PageConcordance
function PageSubset() {
    return PageConcordance.apply(this, arguments);
}
PageSubset.prototype = Object.create(PageConcordance.prototype);

PageSubset.prototype.reload_data = function reload(page_state) {
    var self = this,
        kwicTerms = {},
        kwicSpan = [{reverse: true, ignore: true}, {}, {ignore: true}],
        api_opts = {};

    // We only parse the KWIC node
    kwicSpan[1] = {
        start: 0,
        stop: parseInt(page_state.arg(
            page_state.arg('kwic-dir') === 'start' ? 'kwic-int-start' : 'kwic-int-end'
        ), 10),
        reverse: (page_state.arg('kwic-dir') !== 'start'),
    };

    // Lower-case all terms, put them in object
    (page_state.arg('kwic-terms')).map(function (t, i) {
        if (t) {
            kwicTerms[t.toLowerCase()] = i + 1;
        }
    });


    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora');
    api_opts.subset = page_state.arg('subset-subset');
    api_opts.contextsize = 5;

    if (!api_opts.corpora || api_opts.corpora.length === 0) {
        throw new DisplayError("Please select a corpus to search in", "warn");
    }
    if (!api_opts.subset) {
        throw new DisplayError("Please select a subset", "warn");
    }

    return api.get('subset', api_opts).then(function (data) {
        var i, j, r,
            allBooks = {}, allWords = {}, allMatches = {},
            tag_state = page_state.state('tag_columns'),
            tag_column_order = page_state.state('tag_column_order');

        data = data.data;

        for (i = 0; i < data.length; i++) {
            data[i].DT_RowId = data[i][3][0] + data[i][4][0];

            // Add KWICGrouper match column
            r = concordance_utils.generateKwicRow(kwicTerms, kwicSpan, data[i], allWords);
            if (r > 0) {
                allMatches[r] = (allMatches[r] || 0) + 1;

                // Add classes for row highlighting
                data[i].DT_RowClass = 'kwic-highlight-' + (r % 4 + 1);
            }

            // Add tag columns
            for (j = 0; j < tag_column_order.length; j++) {
                data[i][tag_column_order[j]] = !!tag_state[tag_column_order[j]][data[i].DT_RowId];
            }

            // Count books used
            allBooks[data[i][3][0]] = (allBooks[data[3][0]] || 0) + 1;
        }

        // Update info line
        self.extra_info = concordance_utils.extra_info(allBooks, allMatches);

        return {
            allWords: allWords,
            data: data,
        };
    });
};

module.exports = PageSubset;
