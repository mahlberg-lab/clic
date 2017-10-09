"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var dataTablesNet = require('datatables.net');
if (window && window.document) {
    dataTablesNet(window, jQuery);
}

function columns_string(columns) {
    return columns.map(function (c) {
        return c.data || '';
    }).join(':');
}

function shallow_clone(obj) {
    var out = obj.constructor(),
        attr;

    for (attr in obj) {
        if (obj.hasOwnProperty(attr)) {
            out[attr] = obj[attr];
        }
    }

    return out;
}

function PageTable(content_el) {
    content_el.innerHTML = '<table class="table" cellspacing="0" width="100%"></table>';
    this.table_el = content_el.children[0];
    this.table_opts = {};

    this.init();
}

PageTable.prototype.init = function init() {
    this.table_opts.deferRender = true;
    this.table_opts.filter = true;
    this.table_opts.sort = true;
    this.table_opts.paginate = true;
    this.table_opts.displayLength = 50;
    this.table_opts.dom = 'ritp';
};

PageTable.prototype.info_callback = function (settings, start, end, max, total, pre) {
    return pre + " " + (this.extra_info || []).join(", ");
};

PageTable.prototype.reload = function reload(page_state) {
    var self = this;

    self.page_state = page_state;

    return new Promise(function (resolve, reject) {
        var table_opts;

        self.table_el.classList.toggle('metadata-hidden', !page_state.arg('table-metadata'));

        if (self.table && self.init_cols === columns_string(self.table_opts.columns)) {
            self.table.search(page_state.arg('table-filter'));
            self.table.ajax.reload(function () {
                // We don't have a separate success / fail callback, so switch
                // on the data type
                if (self.last_fetched_data instanceof Error) {
                    reject(self.last_fetched_data);
                } else {
                    resolve(self.last_fetched_data);
                }
            });
        } else {
            if (self.table) {
                // Re-create table so we can add extra columns
                self.table.destroy();
                self.table_el.innerHTML = "";
            }

            table_opts = shallow_clone(self.table_opts);
            table_opts.fnInitComplete = function (table, data) {
                self.init_cols = columns_string(self.table_opts.columns);
                resolve(data);
            };
            table_opts.search = { search: page_state.arg('table-filter'), smart: false };
            table_opts.ajax = function (params, callback, settings) {
                new Promise(function (resolve) {
                    // NB: This has to be self.page_state, otherwise we make a closure
                    // around the initial page_state
                    resolve(self.reload_data(self.page_state));
                }).then(function (data) {
                    self.last_fetched_data = data;
                    callback(data);
                }).catch(function (err) {
                    // Reject the wider promise, to send the error up
                    self.last_fetched_data = err;
                    // Clear any old data in the table
                    self.table.clear().draw();
                    reject(err);
                });
            };
            // Shouldn't try to order by columns that no longer exist (read: tag columns)
            table_opts.order = table_opts.order.filter(function (o) {
                return o[0] < table_opts.columns.length;
            });
            table_opts.infoCallback = self.info_callback.bind(self);
            self.table = jQuery(self.table_el).DataTable(table_opts);

            if (self.hasOwnProperty('table_count_column')) {
                self.table.on('draw.dt', function () {
                    var pageStart = self.table.page.info().start,
                        pageCells = self.table.cells(null, self.table_count_column, {page: 'current', order: 'applied', search: 'applied'});

                    pageCells.nodes().each(function (cell, i) {
                        cell.innerHTML = pageStart + i + 1;
                    });
                });
            }

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
            selected = page_state.state('selected_rows');

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
