"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true, nomen: true */
/*global Promise, Set */
var PageTable = require('./page_table.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;
var concordance_utils = require('./concordance_utils.js');
var quoteattr = require('./quoteattr.js').quoteattr;
var shallow_clone = require('./shallow_clone.js').shallow_clone;
var flexiclic = require('./flexiclic.js').flexiclic;
var util_flexiconc = require('./util_flexiconc.js');

/* Column represents a fractional position in book */
function renderPosition(data, type, full, meta) {
    var xVal, pos_start = data[1];

    if (pos_start === "" && full[7].hasOwnProperty("rowcount")) {
        // Partition/cluster header row, show rowcount instead of position
        return '<span style="text-wrap: nowrap" title="Click to open/close partition">' + concordance_utils.plural(full[7].rowcount, "line") + '</span>';
    }

    if (type === 'display') {
        xVal = (pos_start / full.chapter_start._end) * 50; // word in book / total word count

        return '<a class="bookLink" title="Click to display concordance in book"' +
               ' onclick="event.stopPropagation();" target="_blank"' +
               ' href="/text?book=' + data[0] + '&word-highlight=' + data[1] + '%3A' + data[2] + '" >' +
               '<svg width="50px" height="15px" xmlns="http://www.w3.org/2000/svg">' +
               '<rect x="0" y="4" width="50" height="7" fill="#D6E1E8"/>' +
               '<line x1="' + xVal + '" x2="' + xVal + '" y1="0" y2="15" stroke="black" stroke-width="2px"/>' +
               '</svg></a>';
    }

    if (type === 'export') {
        return pos_start + '/' + full.chapter_start._end;
    }

    return pos_start;
}

function renderFlexiConcLineId(data, type, full, meta) {
    if (type === "display" && data === "") {
        // NB: width is bodge to ensure we're ~as wide as the 3 digit numbers within
        return '<div class="partition-toggle" style="width:21px" role="button" title="Click to open/close partition" data-partition-id="' + full[5] + '"></div>';
    }
    return data;
}

/** Generate concordance API opts from page state */
function api_opts(page_state) {
    var out = {};

    // Mangle page_state into the API's required parameters
    out.corpora = page_state.arg('corpora');
    out.subset = page_state.arg('conc-subset');
    out.q = page_state.arg('conc-q');
    out.contextsize = 10;
    out.metadata = ['chapter_start', 'word_count_all'];

    if (out.corpora.length === 0) {
        throw new DisplayError("Please select the corpora to search in", "warn");
    }
    if (!out.q) {
        throw new DisplayError("Please provide some terms to search for", "warn");
    }
    if (!out.subset) {
        throw new DisplayError("Please select a subset", "warn");
    }
    if (page_state.arg('conc-type') === 'any') {
        out.q = out.q.split(/(\s+)/).filter(function (t) {
            return (/\w/).test(t);
        });
    }

    return out;
}

// PageFlexiConc inherits PageTable
function PageFlexiConc() {
    return PageTable.apply(this, arguments);
}
PageFlexiConc.prototype = Object.create(PageTable.prototype);

PageFlexiConc.prototype.init = function () {
    PageTable.prototype.init.apply(this, arguments);

    this.book_titles = {};
    this.table_opts.deferRender = true;
    this.table_opts.autoWidth = false;
    // NB: FlexiConc should be ordering
    this.table_opts.order = [];
    this.table_opts.ordering = false;
};

PageFlexiConc.prototype.add_events = function () {
    var self = this;

    self.table.on('click', 'tr', function (event, type, action) {
        // https://datatables.net/reference/api/row().data()
        var partitionId, elCheckbox, dtRow;

        // lineid-picker integration: update table data with checkboxes, select all in summary row
        if (event.target.closest("td").classList.contains("tagColumn")) {
            dtRow = self.table.row(this);
            partitionId = dtRow.data()[5];

            // fc-select checkbox column
            if (event.target.tagName === "INPUT") {
                elCheckbox = event.target;
            } else {
                // Allow some leeway, clicks on the td also trigger a check
                elCheckbox = event.target.querySelector(":scope input");
                elCheckbox.checked = !elCheckbox.checked;
            }

            // Add checkbox state back to data
            dtRow.data()["fc-select"] = elCheckbox.checked;

            if (this.classList.contains("fc-partition-summary")) {
                // Open regardless of previous state
                self.fcPartitions.add(partitionId);
                this.classList.add("open");

                // Set check for every row in this partition
                self.table.rows().every(function () {
                    if (this.data()[5] === partitionId) {
                        this.data()["fc-select"] = elCheckbox.checked;
                        this.invalidate();
                    }
                });
            }

            // Redraw to apply any new checkbox checks
            self.table.draw();

            return;
        }

        // Open/close summary rows
        if (this.classList.contains("fc-partition-summary")) {
            partitionId = parseInt(this.querySelector(":scope *[data-partition-id]").getAttribute("data-partition-id"), 10);

            // Toggle the current partition ID on/off
            if (self.fcPartitions.has(partitionId)) {
                self.fcPartitions.delete(partitionId);
                this.classList.remove("open");
            } else {
                self.fcPartitions.add(partitionId);
                this.classList.add("open");
            }

            // Redraw to re-apply self.table.search
            self.table.draw();

            return;
        }
    });

    // NB: Not inheriting standard add_events(), doesn't offer anything useful
};

PageFlexiConc.prototype.page_title = function (page_state) {
    return "CLiC FlexiConc";
};

PageFlexiConc.prototype.reload = function reload(page_state) {
    var self = this;

    this.table_opts.non_tag_columns = [
        { visible: false, sortable: false, searchable: false },
        // NB: This is line-id, not a table_count_column as in other views
        { title: "ID", data: "6", width: "4rem", className: "fc-line-id numeric", render: renderFlexiConcLineId, sortable: false, searchable: false },
        { title: "Left", data: "0", width: "50%", render: concordance_utils.renderTokenArray, className: "context left", sortable: false }, // Left
        { title: "Node", data: "1", render: concordance_utils.renderTokenArray, className: "context node", sortable: false }, // Node
        { title: "Right", data: "2", width: "50%", render: concordance_utils.renderTokenArray, className: "context right", sortable: false }, // Right
        { title: "Book", data: "3.0", render: concordance_utils.renderBook.bind(this, 'abbr'), searchable: false, sortable: false }, // Book
        // NB: Relies on page_table re-applying visible on existing tables
        { title: "Ch.", data: "4.0", visible: (page_state.arg('table-type') === 'full'), searchable: false, sortable: false }, // Chapter
        { title: "Par.", data: "4.1", visible: (page_state.arg('table-type') === 'full'), searchable: false, sortable: false }, // Paragraph-in-chapter
        { title: "Sent.", data: "4.2", visible: (page_state.arg('table-type') === 'full'), searchable: false, sortable: false }, // Sentence-in-chapter
        { title: "In&nbsp;bk.", data: "3", width: "52px", render: renderPosition, searchable: false, sortable: false, orderData: [5, 9] }, // Book graph
    ];

    // lineid-picker: Add select columns for use with line/partition selection
    if (page_state.arg("fc-select-type") === "line_id") {
        this.table_opts.non_tag_columns.splice(2, 0, {
            className: "tagColumn",
            sortable: false,
            searchable: false,
            data: 6,
            render: function (data, type, full, meta) {
                if (type !== "display") {
                    return data;
                }
                return [
                    '&nbsp;<input',
                    'type="checkbox"',
                    'name="fc-select"',
                    'value="' + data + '"',
                    (full["fc-select"] ? "checked" : ""),
                    // Summary rows have grey checks to indicate they aren't part of the selection
                    (full[6] !== "" ? '' : 'style="accent-color: #666"'),
                    '/>',
                ].join(" ");
            }
        });
    } else if (page_state.arg("fc-select-type").startsWith("partition_")) {  // i.e. id or label
        this.table_opts.non_tag_columns.splice(2, 0, {
            className: "tagColumn",
            sortable: false,
            searchable: false,
            data: 5,
            render: function (data, type, full, meta) {
                if (type !== "display") {
                    return data;
                }
                return full[6] !== "" ? "" : [
                    '&nbsp;<input',
                    'type="checkbox"',
                    'name="fc-select"',
                    'value="' + data + '"',
                    (full["fc-select"] ? "checked" : ""),
                    '/>',
                ].join(" ");
            }
        });
    }

    // Generate column list based on tag_columns
    this.table_opts.columns = this.table_opts.non_tag_columns;

    if (page_state.arg("fc-path") === "0") {
        // Switch to tree-mode, remove table & replace with tree
        if (this.table) {
            this.table.destroy();
            this.table = undefined;
            // reset table DOM node, throwing away any attached events
            this.table_el.outerHTML = '<table class="table" cellspacing="0" width="100%"></table>';
            this.table_el = document.querySelector("#content > table");
        }
        if (!this.tree_el) {
            this.tree_el = document.createElement("DIV");
            this.tree_el.className = "analysis-tree";
            this.table_el.insertAdjacentElement("afterend", this.tree_el);
        }
        this.tree_el.style.display = "";

        // NB: Re-attaching event on each page update so page_state is up-to-date
        this.tree_el.onclick = function (event) {
            var button_el = event.target.closest("button"),
                path_name = button_el ? button_el.parentElement.getAttribute("data-path-name") : null;

            if (!button_el) {
                return;
            }
            event.stopPropagation();
            event.preventDefault();

            if (button_el.getAttribute("aria-label") === "Delete") {
                // Remove data-path-name from fc-all-paths and update
                window.dispatchEvent(new window.CustomEvent('state_update', { detail: {
                    state: { "fc-all-paths": util_flexiconc.remove_path(
                        page_state.state("fc-all-paths"),
                        path_name
                    ) },
                }}));
            } else {
                // Switch to path
                window.dispatchEvent(new window.CustomEvent('state_update', { detail: {
                    args: Object.assign(
                        {},
                        // Everything non-algo from the current state
                        page_state.all_args(/^(?!algo\[)/),
                        // All stored algo[ args from fc-all-paths
                        page_state.state("fc-all-paths")[path_name] || [],
                        // New fc-path pointer
                        { "fc-path": [path_name] }
                    ),
                    flush: true,
                }}));
            }
        };

        return flexiclic.render_tree_html({
            opts: api_opts(page_state),
            annotations: util_flexiconc.renest_args(page_state.all_args(/^(?:annotation)\[/)).annotation || [],
            paths: util_flexiconc.renest_all(page_state.state("fc-all-paths")),
        }).then(function (tree_html) {
            this.tree_el.innerHTML = tree_html.join("\n");
            this.tree_el.querySelectorAll(":scope > ul > li > .node").forEach(function (el) {
                el.scrollIntoView({block: "center", inline: "start"});
            });
        }.bind(this));
    }
    if (this.tree_el) {
        this.tree_el.style.display = "none";
    }

    // For single-word nodes, we want to keep the node column narrow to balance the table nicely
    this.table_el.classList.toggle('narrow-node',
        page_state.arg('table-type') !== 'dist_plot' &&
        page_state.arg('conc-q') && /* Subsets won't have conc-q, but will ~always be wide */
        (page_state.arg('conc-type') === 'any' || (page_state.arg('conc-q').match(/\s+/g) || []).length < 6)
        );

    return PageTable.prototype.reload.apply(this, arguments).then(function (data) {
        // Add fixed filter for collapsed groups
        self.table.search.fixed("fc-grouping", function (searchStr, data, index) {
            if (data[6] === "") {
                // Always show summary rows
                return true;
            }

            return self.fcPartitions.has(data[5]);
        }).draw();

        return data;
    });
};

/* Override PageTable, don't bother trying to update toggles (which aren't there in tree mode) */
PageFlexiConc.prototype.tweak = function tweak(page_state) {
    return new Promise(function (resolve) {
        resolve({});
    });
};

PageFlexiConc.prototype.reload_data = function reload(page_state) {
    var self = this,
        fcSelect = new Set(JSON.parse(page_state.arg("fc-select"))),
        fcSelectFn = null,
        fcPartitionLabels = {},
        nested_args = util_flexiconc.renest_args(page_state.all_args(/^(?:algo|annotation)\[/));

    // Reset fcPartitions, so we only show the first partition if results are partitioned
    self.fcPartitions = new Set([0]);

    // lineid-picker integration: Generate function to select value from data row
    if (page_state.arg("fc-select-type") === "line_id") {
        fcSelectFn = function (d) { return d[6]; };
    } else if (page_state.arg("fc-select-type") === "partition_id") {
        fcSelectFn = function (d) { return d[5]; };
    } else if (page_state.arg("fc-select-type") === "partition_label") {
        fcSelectFn = function (d) { return fcPartitionLabels[d[5]]; };
    }

    // lineid-picker integration: Expose fc_select_data for outer frame to fetch results
    window.fc_select_data = function () {
        // https://datatables.net/reference/api/data%28%29
        var out = new Set();

        // Gather value of all rows that are selected
        self.table.data().each(function (d) {
            if (d["fc-select"] && fcSelectFn(d) !== "") {
                out.add(fcSelectFn(d));
            }
        });

        return Array.from(out);
    };

    return flexiclic.compute_path({
        opts: api_opts(page_state),
        annotations: nested_args.annotation || [],
        path: nested_args.algo || [],
        speculative: page_state.speculative,
    }).then(function (data) {
        var i, out, lastSummaryIdx;

        // Assume first item in data array is CLiC metadata
        out = data.shift();
        out.data = data;

        for (i = 0; i < data.length; i++) {
            // Annotate context with kwicSpan/matches for renderTokenArray()
            data[i][0].kwicSpan = { reverse: true };
            data[i][1].kwicSpan = { reverse: false };
            data[i][2].kwicSpan = { reverse: false };
            data[i][0].matches = (data[i][7].matches || [])[0];
            data[i][1].matches = (data[i][7].matches || [])[1];
            data[i][2].matches = (data[i][7].matches || [])[2];
            // Need to annotate each row for renderPosition()
            data[i].chapter_start = out.chapter_start[data[i][3][0]];

            if (data[i][6] === "") {
                data[i].DT_RowClass = "fc-partition-summary" + (self.fcPartitions.has(data[i][5]) ? " open" : "");
                // Save ID -> label map for returning fc-select by label
                fcPartitionLabels[data[i][5]] = data[i][2][0];
                lastSummaryIdx = i;
            }
            // lineid-picker integration: Add fc-select for any preselected items
            if (fcSelectFn !== null && fcSelect.has(fcSelectFn(data[i]))) {
                data[i]["fc-select"] = true;

                // Non-summary rows should announce their state on the summary row
                if (page_state.arg("fc-select-type") === "line_id" && i !== lastSummaryIdx) {
                    data[lastSummaryIdx]["fc-select"] = true;
                }
            }
        }

        return out;
    });
};

module.exports = PageFlexiConc;
