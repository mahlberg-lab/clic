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

    if (!api_opts.corpora || api_opts.corpora.length === 0) {
        throw new DisplayError("Please select a corpus to search in", "warn");
    }
    if (!api_opts.subset) {
        throw new DisplayError("Please select a subset", "warn");
    }

    return api.get('subset', api_opts).then(this.post_process.bind(this, page_state, kwicTerms, kwicSpan));
};

module.exports = PageSubset;
