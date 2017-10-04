"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, Blob */
var FileSaver = require('file-saver');

module.exports.format_dt = function (dt) {
    var out = [], row = [],
        row_ids = dt.rows().ids().toArray(),
        include_column = dt.columns().visible().toArray();

    // Format header row
    row = ['ID'];
    dt.columns().header().map(function (el, i) {
        if (include_column[i]) {
            if (el.classList.contains('sorting_disabled')) {
                // It's the count column, ignore that
                include_column[i] = false;
            } else if (el.classList.contains('tagColumn')) {
                // Tag columns need a prefix
                row.push("tag:" + el.innerText);
            } else {
                row.push(el.innerText);
            }
        }
    });
    row.push(window.location.href); // Add the URL so we can regenerate this page
    out.push(row);

    // Format each cell, skipping over the ones we don't care about.
    row = [row_ids[0]];
    dt.cells().render('export').map(function (c, i) {
        var col = i % include_column.length;

        if (include_column[col]) {
            row.push(c);
        }

        if (col === (include_column.length - 1)) {
            // End of a row, start a new one.
            out.push(row);
            row = [row_ids[Math.floor((i + 1) / include_column.length)]];
        }
    });

    return out;
};

/**
  * Save (data), probably from format_dt(), to disk
  */
module.exports.save = function (data) {
    var blob, filename = window.location.pathname.replace('/', 'clic-') + '.csv';

    blob = new Blob(data.map(function (d) {
        return d.map(function (val) {
            return '"' + val.toString().replace(/"/g, '""') + '"';
        }).join(',') + '\r\n';
    }), { type: "text/csv;charset=utf-8" });
    FileSaver.saveAs(blob, filename);
};
