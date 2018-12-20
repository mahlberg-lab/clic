"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var State = require('./state.js');
var PageTable = require('./page_table.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

/* Clusters should link back to an equivalent concordance */
function renderCluster(data, type, full, meta) {
    if (type === 'display') {
        return '<a title="Click to find individual concordances" target="_blank"' +
               ' onclick="event.stopPropagation();"' +
               ' href="' + full.cluster_url_prefix + '&conc-q=' + encodeURIComponent(data) + '"' +
               '>' + data + '</a>';
    }

    return data;
}

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
        { title: "Cluster", data: "0", render: renderCluster },
        { title: "Frequency", data: "1"},
    ];
    this.table_opts.order = [[2, "desc"]];
    this.table_opts.orderFixed = { post: [['1', 'asc']] };
    this.table_count_column = 0;
};

PageCluster.prototype.page_title = function (page_state) {
    return "CLiC clusters search";
};

PageCluster.prototype.reload = function reload(page_state) {
    // Make a URL pointing at the concordance page, with the same corpora, use this in cluster links
    this.table_opts.columns[1].render = renderCluster;

    return PageTable.prototype.reload.apply(this, arguments);
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

    return this.cached_get('cluster', api_opts).then(this.post_process.bind(this, page_state));
};

PageCluster.prototype.post_process = function (page_state, raw_data) {
    var i, url_prefix,
        data = raw_data.data || [];

    url_prefix = page_state.clone({doc: 'concordance', args: {
        corpora: page_state.arg('corpora'),
        'conc-subset': page_state.arg('subset'),
    }}, true).to_url();

    for (i = 0; i < data.length; i++) {
        // Add cluster URL prefix for use in the render function
        data[i].cluster_url_prefix = url_prefix;
    }

    return raw_data;
};

module.exports = PageCluster;
