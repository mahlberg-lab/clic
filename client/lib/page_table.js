"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
if (window && window.document) {
    var dataTablesNet = require('datatables.net');
    dataTablesNet(window, jQuery);
}
var api = require('./api.js');
var shallow_clone = require('./shallow_clone.js').shallow_clone;

function columns_string(columns) {
    return columns.map(function (c) {
        return c.data || '';
    }).join(':');
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
    this.table_opts.dom = 'ri<"data-version">tp';
};

PageTable.prototype.info_callback = function (settings, start, end, max, total, pre) {
    return pre + ", " + (this.extra_info || []).join(", ");
};

PageTable.prototype.reload = function reload(page_state) {
    var self = this;

    self.page_state = page_state;

    return new Promise(function (resolve, reject) {
        var table_opts, add_events = true, old_page;

        self.table_el.classList.toggle('metadata-hidden', page_state.arg('table-type') === 'basic');

        if (self.table && self.init_cols === columns_string(self.table_opts.columns)) {
            old_page = self.table.page();

            self.table.search(page_state.arg('table-filter'));
            self.table.ajax.reload(function () {
                // We don't have a separate success / fail callback, so switch
                // on the data type
                if (self.last_fetched_data instanceof Error) {
                    reject(self.last_fetched_data);
                } else {
                    // Only switch pages if...
                    // * The querystring still matches (i.e. KWICGrouper goes to start, tagging stays in same place)
                    // * There's enough data available, and we won't switch to an empty page.
                    // The net result should be only staying on current page when tags are applied.
                    if (self.init_querystring === window.location.search && self.table.page.info().pages > old_page) {
                        self.table.page(old_page).draw('page');
                    }
                    self.init_querystring = window.location.search;
                    resolve(self.last_fetched_data);
                }
            }, true); // i.e. reset the current page (we'll handle switching back ourselves)
        } else {
            if (self.table) {
                // Re-create table so we can add extra columns
                self.table.destroy();
                self.table_el.innerHTML = "";
                add_events = false; // Events are attached to the table element, which remains
            }
            self.init_cols = null; // If this load fails, we should do a full redraw afterwards

            table_opts = shallow_clone(self.table_opts);
            table_opts.fnInitComplete = function (table, data) {
                self.init_cols = columns_string(self.table_opts.columns);
                self.init_querystring = window.location.search;
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
                    document.querySelector('div.data-version').innerText = data.version.corpora;
                    document.querySelector('div.data-version').setAttribute('title', 'The version of the corpora repository used to generate this table');
                    self.table.table().node().setAttribute('data-corpora-version', data.version.corpora);
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

            if (add_events) {
                self.add_events();
            }
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
        // We want to remove this selection on next click
        if (selected.length > 0) {
            self.initial_selection = true;
        }

        // Add data for selected rows, so control panel can update
        data.selected_data = self.table.rows('.selected').data().toArray();

        return data;
    });
};

/** On tweak make sure selected_data is available for updating toggles */
PageTable.prototype.tweak = function tweak(page_state) {
    var self = this;

    return new Promise(function (resolve) {
        resolve({
            selected_data: self.table.rows('.selected').data().toArray(),
        });
    });
};

/** Record selection in page_state, trigger a tweak-update */
PageTable.prototype.select_rows = function () {
    window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
        state: {
            selected_rows: this.table.rows('.selected').ids().toArray(),
        },
    }}));
};

PageTable.prototype.reload_data = function (page_state) {
    throw new Error("Not implemented");
};

/** Wire up events to a new table */
PageTable.prototype.add_events = function add_events() {
    var self = this;

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
        if (!this.classList.contains('child')) {
            this.classList.toggle('selected');
        }
        self.select_rows();
    });
};

/**
  * Wrap around api.get, store result of previous query and return it if same
  * Browser caches only work up to ~5MB, so we can't rely on them
  */
PageTable.prototype.cached_get = function (endpoint, qs) {
    var self = this;

    function cmp(a, b) {
        return JSON.stringify(a, Object.keys(a).sort()) === JSON.stringify(b, Object.keys(b).sort());
    }

    if (this.prev_get && endpoint === this.prev_get.endpoint && cmp(qs, this.prev_get.qs)) {
        return new Promise(function (resolve) {
            // Delay it a bit so the browser has time to show the spinner
            window.setTimeout(resolve.bind(null, self.prev_get.data), 0);
        });
    }
    return api.get(endpoint, qs).then(function (data) {
        self.prev_get = {
            endpoint: endpoint,
            qs: qs,
            data: data,
        };
        return data;
    });
};

module.exports = PageTable;
