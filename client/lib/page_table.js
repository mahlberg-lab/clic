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
    this.table_opts.dom = 'Bfr<"clear"i>tip';
    this.table_opts.buttons = [
        'csv', 'copy',
        { text: 'Toggle Metadata', action: function (e, dt, node, config) {
            var i, col;

            /* TODO: Make this generic? */
            for (i = 6; i < 9; i++) {
                col = dt.column(i);
                col.visible(!col.visible());
            }
        }},
    ];
    this.table_opts.ajax = function (params, callback, settings) {
        self.reload_data(self.page_opts).then(function (data) {
            callback(data);
        }).catch(function (err) {
            // Reject the wider promise, to send the error up
            self.ajax_reject(err);
        });
    };
};

PageTable.prototype.reload = function reload(page_opts) {
    var self = this;

    return new Promise(function (resolve, reject) {
        var table_opts;

        function resolve_second(table, data) {
            // Ditch the first argument, resolve with the data
            resolve(data);
        }

        // Make available for ajax / reload_data
        self.page_opts = page_opts;
        self.ajax_reject = reject;

        if (self.table) {
            self.table.reload(resolve_second);
        } else {
            table_opts = self.table_opts;
            table_opts.fnInitComplete = resolve_second;
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
                jQuery(this).toggleClass('selected');
            });
        }
    });
};

PageTable.prototype.reload_data = function (page_opts) {
    throw new Error("Not implemented");
};

module.exports = PageTable;
