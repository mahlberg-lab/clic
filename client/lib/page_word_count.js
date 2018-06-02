"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var State = require('./state.js');
var PageTable = require('./page_table.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;
var concordance_utils = require('./concordance_utils.js');

// PageChapter inherits PageTable
function PageChapter() {
    return PageTable.apply(this, arguments);
}
PageChapter.prototype = Object.create(PageTable.prototype);

PageChapter.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.table_opts.deferRender = true;
    this.table_opts.autoWidth = false;
    this.table_opts.columns = [
        { title: "", defaultContent: "", width: "3rem", sortable: false, searchable: false },
        { title: "Book", data: "0", render: concordance_utils.renderBook.bind(this, 'full'), width: "10rem", searchable: true },
        { title: "Total Words", data: "1", className: "numeric" },
        { title: "In Quotes", data: "2", className: "numeric" },
        { title: "In Non-quotes", data: "3", className: "numeric" },
        { title: "In Suspensions", data: "4", className: "numeric" },
        { title: "In Long suspensions", data: "5", className: "numeric" },
    ];
    this.table_opts.order = [[1, "desc"]];
    this.table_count_column = 0;
};

PageChapter.prototype.page_title = function (page_state) {
    return "CLiC word counts";
};

/** On tweak make sure the selected row is open */
PageChapter.prototype.tweak = function tweak(page_state) {
    var self = this;

    return PageTable.prototype.tweak.apply(this, arguments).then(function (data) {
        // Hide any rows that aren't selected any more
        self.table.rows('.open').every(function () {
            if (page_state.state('selected_rows').indexOf(this.id()) === -1) {
                this.child.hide();
                this.node().classList.remove('open');
            }
        });

        self.table.rows(page_state.state('selected_rows').map(function (x) { return "#" + x; })).every(function () {
            var book_id = this.data()[0];

            this.node().classList.add('open');
            this.child('View chapter: ' + this.data().chapters.map(function (ch_num) {
                if (ch_num === '_end') {
                    return '';
                }
                return '<a href="/chapter?book_id=' + book_id + '&chapter_num=' + ch_num + '">' + ch_num + '</a>';
            }).join(", &nbsp;")).show();
        });
    });
};

PageChapter.prototype.reload_data = function reload(page_state) {
    var api_opts = {};

    // Mangle page_state into the API's required parameters
    api_opts.corpora = page_state.arg('corpora');
    api_opts.subset = ['all', 'quote', 'nonquote', 'shortsus', 'longsus'];
    api_opts.metadata = ['book_titles', 'chapter_start'];

    if (api_opts.corpora.length === 0) {
        throw new DisplayError("Please select the corpora to search in", "warn");
    }

    return this.cached_get('word-count', api_opts).then(this.post_process.bind(this, page_state));
};

PageChapter.prototype.post_process = function (page_state, raw_data) {
    var i, totals = [0, 0, 0, 0, 0],
        data = raw_data.data || [];

    for (i = 0; i < data.length; i++) {
        // Use book IDs as row IDs
        data[i].DT_RowId = data[i][0];

        // Sum up counts for extra_info
        totals[0] += data[i][1];
        totals[1] += data[i][2];
        totals[2] += data[i][3];
        totals[3] += data[i][4];
        totals[4] += data[i][5];

        // Add chapter counts for book
        data[i].chapters = Object.keys(raw_data.chapter_start[data[i][0]] || {});
    }

    // Save book_titles ready for the renderer function
    this.book_titles = raw_data.book_titles || {};

    this.extra_info = [
        totals[0] + " total words",
        totals[1] + " in Quotes",
        totals[2] + " in Non-quotes",
        totals[3] + " in Suspensions",
        totals[4] + " in Long suspensions",
    ];

    return raw_data;
};

module.exports = PageChapter;
