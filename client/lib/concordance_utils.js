"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var quoteattr = require('./quoteattr.js').quoteattr;
var unidecode = require('unidecode');

function choose_name(tag_columns, base_tag_name) {
    var new_tag_name = base_tag_name,
        i = 1;

    while (tag_columns[new_tag_name]) {
        new_tag_name = base_tag_name + "-" + i++;
    }
    return new_tag_name;
}

function escapeHtml(tag, s) {
    // https://bugs.jquery.com/ticket/11773
    return '<' + tag + '>' + (String(s)
        .replace(/&(?!\w+;)/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')) + '</' + tag + '>';
}

/*
 * Convert token string tok to it's equivalent type. e.g. Oliv£r’s --> "olivPSr's"
 *
 * NB: This code should be developed in lock-step with server/clic/tokenizer.py
 */
function tokenToType(tok) {
    return unidecode(tok.toLowerCase());
}

// Column is an array of tokens, mark these up as words, only sort on word content
module.exports.renderTokenArray = function renderTokenArray(data, type, full, meta) {
    var i, t, out = "", word_indices = data[data.length - 1];

    if (type === 'display') {
        out = '<div class="' + (data.kwicSpan.reverse ? 'r' : 'l');
        for (i = 0; i < data.matches.length; i++) {
            out += ' m' + data.matches[i];
        }
        out += '">';

        for (i = 0; i < data.length - 1; i++) {
            out += escapeHtml(word_indices.indexOf(i) > -1 ? 'mark' : 'span', data[i]);
        }

        return out + '</div>';
    }

    if (type === 'sort') {
        for (i = 0; i < Math.min(word_indices.length, 3); i++) {
            t = data[word_indices[data.kwicSpan.reverse ? word_indices.length - i - 1 : i]];
            out += t + ":";
        }
        return out;
    }

    // type === filter/type/(undefined)/export: Just return string
    return data.slice(0, -1).join("");
};

/*
 * Annotate rows with KWICGrouper information, specifically:
 * For each column...
 * - matches: Array of KWIC match positions
 * - kwicSpan: The kwicSpan settings used
 * For the entire row...
 * - kwic: Overall match count
 * Return Overall match count
 */
module.exports.generateKwicRow = function (kwicTerms, kwicSpan, d, allWords) {
    var matchingTypes = {};

    // Check if list (tokens) contains any of the (kwicTerms) between (span.start) and (span.stop) inclusive
    // considering (tokens) in reverse if (span.reverse) is true
    function testList(tokens, span) {
        var i, t, out = [], word_indices = tokens[tokens.length - 1];

        if (span.start === undefined) {
            // Ignoring this row
            return out;
        }

        for (i = 0; i < word_indices.length; i++) {
            t = tokenToType(tokens[word_indices[span.reverse ? word_indices.length - i - 1 : i]]);
            allWords[t] = true;

            if ((i + 1) >= span.start && kwicTerms.hasOwnProperty(t)) {
                // Matching has started and matches a terms, return which match it is
                matchingTypes[t] = true;
                out.push(i + 1);
            }
            if (span.stop !== undefined && (i + 1) >= span.stop) {
                // Finished matching now, give up.
                break;
            }
        }

        return out;
    }

    // Annotate left/node/right with matches, and the span information used
    d[0].matches = testList(d[0], kwicSpan[0]);
    d[1].matches = testList(d[1], kwicSpan[1]);
    d[2].matches = testList(d[2], kwicSpan[2]);
    d[0].kwicSpan = kwicSpan[0];
    d[1].kwicSpan = kwicSpan[1];
    d[2].kwicSpan = kwicSpan[2];
    d.kwic = Object.keys(matchingTypes).length;
    return d.kwic;
};

/** Merge tags in old and new state, old state gets to keep it's original names */
module.exports.merge_tags = function (old_state, new_state) {
    var i, new_name,
        out_state = JSON.parse(JSON.stringify(old_state));

    for (i = 0; i < new_state.tag_column_order.length; i++) {
        new_name = choose_name(out_state.tag_columns, new_state.tag_column_order[i]);

        // Using new name, append tag column to the end of existing ones
        out_state.tag_column_order.push(new_name);
        out_state.tag_columns[new_name] = new_state.tag_columns[new_state.tag_column_order[i]];
    }

    return out_state;
};

/* Render full book title, optionally as hover-over */
module.exports.renderBook = function (render_mode, data, type) {
    if (type === 'display' && this.book_titles[data]) {
        //NB: Edge needs persuasion to get abbr to word-wrap
        return '<a href="/text?book=' + data + '"><abbr style="' +
                'display: block;' +
                (render_mode === 'full' ? 'width: 9.5rem' : '') +
            '" title="' + quoteattr(this.book_titles[data][0] + ' (' + this.book_titles[data][1] + ')') + '">' +
            quoteattr(render_mode === 'full' ? this.book_titles[data][0] : data) + '</abbr></a>';
    }

    return render_mode === 'full' ? this.book_titles[data][0] : data;
};
