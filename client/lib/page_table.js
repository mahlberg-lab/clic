"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var dataTablesNet = require('datatables.net');
if (window && window.document) {
    dataTablesNet(window, jQuery);
}

function PageTable(content_el) {
    content_el.innerHTML = '<table class="table" cellspacing="0" width="100%"></table>';
    this.table_el = content_el.children[0];
    this.table_opts = {};

    this.init();
}

PageTable.prototype.init = function init() {
    var self = this;

    this.table_opts.deferRender = true;
    this.table_opts.filter = true;
    this.table_opts.sort = true;
    this.table_opts.paginate = true;
    this.table_opts.displayLength = 50;
    this.table_opts.dom = 'ritp';
    this.table_opts.ajax = function (params, callback, settings) {
        self.reload_data(self.page_state).then(function (data) {
            callback(data);
        }).catch(function (err) {
            // Reject the wider promise, to send the error up
            self.ajax_reject(err);
        });
    };
};

PageTable.prototype.reload = function reload(page_state) {
    var self = this;

    return new Promise(function (resolve, reject) {
        var table_opts;

        function resolve_second(table, data) {
            // Ditch the first argument, resolve with the data
            resolve(data);
        }

        self.table_el.classList.toggle('metadata-hidden', !page_state.arg('table-metadata', ""));

        // Make available for ajax / reload_data
        self.page_state = page_state;
        self.ajax_reject = reject;

        if (self.table) {
            self.table.search(page_state.arg('table-filter', ''));
            self.table.reload(resolve_second);
        } else {
            table_opts = self.table_opts;
            table_opts.fnInitComplete = resolve_second;
            table_opts.search = { search: page_state.arg('table-filter', '') };
            self.table = jQuery(self.table_el).DataTable(table_opts);

            // TODO: This relies on column definition in lib/page_concordance.js
            self.table.on('draw.dt', function () {
                var pageStart = self.table.page.info().start,
                    pageCells = self.table.cells(null, 1, {page: 'current', order: 'applied', search: 'applied'});

                pageCells.nodes().each(function (cell, i) {
                    cell.innerHTML = pageStart + i + 1;
                });
            });

            self.table.on('click', 'tr', function () {
                if (self.initial_selection) {
                    // Remove initial selection before continuing
                    self.table.rows('.selected').nodes().each(function (el) {
                        el.classList.remove('selected');
                    });
                    self.initial_selection = false;
                }
                this.classList.toggle('selected');
                self.select_rows();
            });
        }
    }).then(function (data) {
        var i, n,
            selected = page_state.state('selected_rows', []);

        // Make sure previously selected rows are still selected
        for (i = 0; i < selected.length; i++) {
            n = document.getElementById(selected[i]);

            if (n) {
                n.classList.add('selected');
            }
        }
        // Trigger event so controlpanel updates
        if (selected.length > 0) {
            self.initial_selection = true;  // We want to remove this selection on next click
            self.select_rows();
        }

        return data;
    });
};

PageTable.prototype.select_rows = function () {
    var selected_data = this.table.rows('.selected').data();

    // Record selection in page state
    this.page_state.update({state: {
        selected_rows: [].concat.apply([], selected_data.map(function (d) {
            return d.DT_RowId;
        })),
    }}, 'silent');

    this.table_el.dispatchEvent(new window.CustomEvent('tableselection', {
        detail: selected_data,
        bubbles: true,
    }));
};

PageTable.prototype.reload_data = function (page_state) {
    throw new Error("Not implemented");
};

module.exports = PageTable;
