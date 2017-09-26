"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */

function escapeHtml(tag, s) {
    // https://bugs.jquery.com/ticket/11773
    return '<' + tag + '>' + (String(s)
        .replace(/&(?!\w+;)/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')) + '</' + tag + '>';
}

// Column is an array of tokens, mark these up as words, only sort on word content
module.exports.renderTokenArray = function renderTokenArray(data, type, full, meta) {
    var i, t, count = 0, out = "", word_indices = data[data.length - 1];

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

    if (type === 'export') {
        return data.join("");
    }

    for (i = 0; i < data.length - 1; i++) {
        t = data[data.kwicSpan.reverse ? data.length - i - 1 : i];
        if (word_indices.indexOf(i) > -1) {
            count++;
            out += t + ":";
            if (count >= 3) {
                return out;
            }
        }
    }
    return out;
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
            t = tokens[word_indices[span.reverse ? word_indices.length - i - 1 : i]].toLowerCase();
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

