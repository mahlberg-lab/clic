"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var PageConcordance = require('./page_concordance.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

// PageSubset inherits PageConcordance
function PageSubset() {
    return PageConcordance.apply(this, arguments);
}
PageSubset.prototype = Object.create(PageConcordance.prototype);

PageSubset.prototype.reload_data = function reload(page_state) {
    var self = this,
        kwicTerms = {},
        kwicSpan = [{ignore: true}, {}, {ignore: true}],
        api_opts = {};

    // We only parse the KWIC node
    kwicSpan[1] = {
        start: 0,
        stop: parseInt(page_state.arg(
            page_state.arg('kwic-dir', 'start') === 'start' ? 'kwic-int-start' : 'kwic-int-end',
            3
        ), 10),
        reverse: (page_state.arg('kwic-dir', 'start') !== 'start'),
    };

    // Lower-case all terms, put them in object
    (page_state.arg('kwic-terms', [])).map(function (t, i) {
        if (t) {
            kwicTerms[t.toLowerCase()] = i + 1;
        }
    });


    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora', []);
    api_opts.subset = page_state.arg('subset-subset', 'shortsus');

    if (!api_opts.corpora || api_opts.corpora.length === 0) {
        throw new DisplayError("Please select a corpora to search in", "warn");
    }

    return api.get('subset', api_opts).then(function (data) {
        var i, j, r, allWords = {}, totalMatches = 0,
            tag_state = page_state.state('tag_columns', {}),
            tag_list = Object.keys(tag_state);

        data = data.results;

        for (i = 0; i < data.length; i++) {
            // TODO: Assume book+word_id is unique for now. Server-generate this
            data[i].DT_RowId = data[i][3][0] + data[i][4][0];

            // Add KWICGrouper match column
            r = self.generateKwicRow(kwicTerms, kwicSpan, data[i], allWords);
            data[i].kwic = r[0];
            if (r[0] > 0) {
                totalMatches++;

                // Add classes for row highlighting
                r[0] = 'kwic-highlight-' + (r[0] % 4 + 1);
                data[i].DT_RowClass = r.join(' ');
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

module.exports = PageSubset;
