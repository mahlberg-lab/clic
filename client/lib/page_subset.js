"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var PageConcordance = require('./page_concordance.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;
var concordance_utils = require('./concordance_utils.js');

// PageSubset inherits PageConcordance
function PageSubset() {
    return PageConcordance.apply(this, arguments);
}
PageSubset.prototype = Object.create(PageConcordance.prototype);

PageSubset.prototype.page_title = function (page_state) {
    return "CLiC subsets search";
};

PageSubset.prototype.reload_data = function reload(page_state) {
    var kwicTerms = {},
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
    api_opts.metadata = ['book_titles', 'chapter_start', 'word_count_all'];

    if (!api_opts.corpora || api_opts.corpora.length === 0) {
        throw new DisplayError("Please select the corpora to search in", "warn");
    }
    if (!api_opts.subset) {
        throw new DisplayError("Please select a subset", "warn");
    }

    return this.cached_get('subset', api_opts).then(this.post_process.bind(this, page_state, kwicTerms, kwicSpan));
};


PageSubset.prototype.relative_frequency_title = function (page_state) {
    return '<abbr title="percentage of total words that are in ' + page_state.arg('subset-subset') + ' subsets">%age</abbr>';
};

PageSubset.prototype.relative_frequency_unit = function () {
    return '';
};

PageSubset.prototype.relative_frequency = function (lines, total_words) {
    var words_in_subset = lines.reduce(function (total, l) {
        return total + l[1][l[1].length - 1].length;
    }, 0);

    return ((words_in_subset / total_words) * 100).toFixed(2);
};

module.exports = PageSubset;
