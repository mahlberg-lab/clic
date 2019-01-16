"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, Blob, FileReader */
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
    row.push(dt.table().node().getAttribute('data-corpora-version'));
    row.push(window.location.href); // Add the URL so we can regenerate this page
    out.push(row);

    // Format each cell, skipping over the ones we don't care about.
    row = [row_ids[0]];
    dt.cells({ search: 'applied' }).render('export').map(function (c, i) {
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
            return '"' + val.toString().replace(/"/g, '""').replace(/\n{2,}/g, "¶ ").replace(/\n+/g, ' ') + '"';
        }).join(',') + '\r\n';
    }), { type: "text/csv;charset=utf-8" });
    FileSaver.saveAs(blob, filename);
};

/** Turn a CSV file into state object **/
module.exports.file_to_state = function (file) {
    var i, header,
        tag_column_offset = null,
        lines = file.split('\r\n'),
        tag_columns = {},
        tag_column_order = [];

    // Turn a CSV line string into an array of values
    function parse_line(line) {
        return line.split(/^"|","|"$/).slice(1, -1).map(function (val) {
            return val.replace(/""/g, '"');
        });
    }

    // Find tags in header
    header = parse_line(lines[0]);
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
    (tag_column_offset !== null ? lines.splice(1) : []).map(function (line_str) {
        var j, line = parse_line(line_str);

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

/** Generate a hidden file field attached to page which tries to upload when trigger is called */
module.exports.file_loader = function file_loader(document, fn) {
    var el = document.createElement('SPAN');

    // Create input element
    el.innerHTML = '<input type="file" style="visibility: hidden; position: absolute; top: 0px; left: 0px; height: 0px; width: 0px;">';
    el = el.children[0];
    document.body.appendChild(el);

    // Attach events
    el.addEventListener('change', function (e) {
        var reader = new FileReader();

        reader.onload = function (load_ev) {
            fn.apply(this, [load_ev.target.result].concat(el.trigger_args));
        };
        reader.readAsText(e.target.files[0], "utf-8");

        // Clear value so we can do it again later
        el.value = "";
    });

    // Trigger function
    el.trigger = function () {
        el.trigger_args = Array.prototype.slice.call(arguments);
        el.click();
    };
    return el;
};
