"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var PageTable = require('./page_table.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

// PageCluster inherits PageTable
function PageCluster() {
    return PageTable.apply(this, arguments);
}
PageCluster.prototype = Object.create(PageTable.prototype);

PageCluster.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.autoWidth = false;
    this.table_opts.columns = [
        { title: "", defaultContent: "", width: "3rem", sortable: false, searchable: false },
        { title: "Cluster", data: "0"},
        { title: "Frequency", data: "1"},
    ];
    this.table_opts.order = [[2, "desc"]];
    this.table_count_column = 0;
};

PageCluster.prototype.page_title = function (page_state) {
    return "CLiC clusters search";
};

PageCluster.prototype.reload_data = function reload(page_state) {
    var api_opts = {};

    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora');
    api_opts.subset = page_state.arg('subset');
    api_opts.clusterlength = page_state.arg('clusterlength');

    if (api_opts.corpora.length === 0) {
        throw new DisplayError("Please select the corpora to search in", "warn");
    }
    if (!api_opts.subset) {
        throw new DisplayError("Please select a subset", "warn");
    }

    return this.cached_get('cluster', api_opts);
};

module.exports = PageCluster;
