"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var PageTable = require('./page_table.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

// PageKeyword inherits PageTable
function PageKeyword() {
    return PageTable.apply(this, arguments);
}
PageKeyword.prototype = Object.create(PageTable.prototype);

PageKeyword.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.autoWidth = false;
    this.table_opts.columns = [
        { title: "", defaultContent: "", width: "3rem", sortable: false, searchable: false },
        { title: "N-gram", data: "1"},
        { title: "Target frequency", data: "2"},
        { title: "Ref frequency", data: "4"},
        { title: "LL", data: "8"},
        { title: "P", data: "10", class: "nowrapColumn"},
    ];
    this.table_opts.order = [[4, "desc"]];
    this.table_count_column = 0;
};

PageKeyword.prototype.page_title = function (page_state) {
    return "CLiC keywords search";
};

PageKeyword.prototype.reload_data = function reload(page_state) {
    var api_opts = {};

    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora');
    api_opts.subset = page_state.arg('subset');
    api_opts.refcorpora = page_state.arg('refcorpora');
    api_opts.refsubset = page_state.arg('refsubset');
    api_opts.clusterlength = page_state.arg('clusterlength');
    api_opts.pvalue = page_state.arg('pvalue');

    if (api_opts.corpora.length === 0) {
        throw new DisplayError("Please select the target corpora", "warn");
    }
    if (api_opts.refcorpora.length === 0) {
        throw new DisplayError("Please select the reference corpora", "warn");
    }
    if (!api_opts.subset) {
        throw new DisplayError("Please select a subset", "warn");
    }
    if (!api_opts.refsubset) {
        throw new DisplayError("Please select a reference subset", "warn");
    }

    return this.cached_get('keyword', api_opts);
};

module.exports = PageKeyword;
