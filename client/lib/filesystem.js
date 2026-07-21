"use strict";
var bfa = require('browser-fs-access');
var Papa = require('papaparse');

module.exports.format_dt = function (dt) {
    var out = [], row = [],
        row_ids = dt.rows({ search: 'applied' }).ids().toArray(),
        include_column = dt.columns().visible().toArray();

    // Format header row
    row = ['ID'];
    dt.columns().header().each(function (el, i) {
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
    row.push(dt.table().node().getAttribute('data-corpora-version'));
    row.push(window.location.href); // Add the URL so we can regenerate this page
    out.push(row);

    // Format each cell, skipping over the ones we don't care about.
    row = [row_ids[0]];
    dt.cells({ search: 'applied' }).render('export').each(function (c, i) {
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
    var csv, blob, filename = window.location.pathname.replace('/', 'clic-') + '.csv';

    csv = Papa.unparse(data.map(function (row) {
        return row.map(function (val) {
            return (val || '').toString().replace(/\n{2,}/g, "¶ ").replace(/\n+/g, ' ');
        });
    }), { newline: '\r\n' });
    // Prepend a UTF-8 BOM so Excel opens the file as Unicode
    blob = new Blob([Papa.BYTE_ORDER_MARK + csv], { type: "text/csv" });
    return bfa.fileSave(blob, { fileName: filename });
};

/** Turn a CSV file into state object **/
module.exports.file_to_state = function (file) {
    var i, header, rows,
        tag_column_offset = null,
        tag_columns = {},
        tag_column_order = [];

    // Is the file actually JSON?
    if (file.startsWith("{") && file.endsWith("}")) {
        return JSON.parse(file);
    }

    rows = Papa.parse(file, { skipEmptyLines: true }).data;
    header = rows[0] || [];

    // Find tags in header
    for (i = 0; i < header.length; i++) {
        if (header[i].indexOf("tag:") === 0) {
            if (tag_column_offset === null) {
                tag_column_offset = i;
            }
            tag_column_order.push(header[i].substr(4));
            tag_columns[header[i].substr(4)] = {};
        }
    }

    // Populate tag values if any where found
    (tag_column_offset !== null ? rows.slice(1) : []).forEach(function (line) {
        var j;

        for (j = 0; j < tag_column_order.length; j++) {
            if (line[tag_column_offset + j] > ' ') {
                tag_columns[tag_column_order[j]][line[0]] = true;
            }
        }
    });

    return {
        url: header.slice(-1)[0].replace(/^.*\/(\w+\?)/, "/$1"),
        state: {
            tag_columns: tag_columns,
            tag_column_order: tag_column_order,
        }
    };
};
