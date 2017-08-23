"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */

function escapeHtml(s) {
    // https://bugs.jquery.com/ticket/11773
    return (String(s)
        .replace(/&(?!\w+;)/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')); // "
}

function isWord(s) {
    return (/\w/).test(s);
}

// Column is an array of tokens, mark these up as words, only sort on word content
function renderTokenArray(reverseSort, data, type, full, meta) {
    var i, t, count = 0, out = "", span_class;

    if (type === 'display') {
        for (i = 0; i < data.length; i++) {
            t = data[reverseSort ? data.length - i - 1 : i];
            if (isWord(t)) {
                count++;
                span_class = "w node-" + count;
            } else {
                span_class = "";
            }

            if (reverseSort) {
                out = '<span class="' + span_class + '">' + escapeHtml(t) + "</span>" + out;
            } else {
                out = out + '<span class="' + span_class + '">' + escapeHtml(t) + "</span>";
            }
        }
    } else {
        for (i = 0; i < data.length; i++) {
            t = data[reverseSort ? data.length - i - 1 : i];
            if (isWord(t)) {
                count++;
                out += t + ":";
                if (count >= 3) {
                    return out;
                }
            }
        }
    }

    return out;
}
module.exports.renderForwardTokenArray = renderTokenArray.bind(null, false);
module.exports.renderReverseTokenArray = renderTokenArray.bind(null, true);

/* Column represents a fractional position in book */
module.exports.renderPosition = function (data, type, full, meta) {
    var xVal;

    if (type !== 'display') {
        return data[2];
    }

    xVal = (data[2] / data[3]) * 50; // word in book / total word count
    return '<a href="#" class="bookLink" title="Click to display concordance in book" target="_blank">' +
           '<svg width="50px" height="15px" xmlns="http://www.w3.org/2000/svg">' +
           '<rect x="0" y="4" width="50" height="7" fill="#ccc"/>' +
           '<line x1="' + xVal + '" x2="' + xVal + '" y1="0" y2="15" stroke="black" stroke-width="2px"/>' +
           '</svg></a>';
};

// Kwicmatches are sorted by # of KWICGrouper types this row matches, i.e. the first item in the list
module.exports.renderKwicMatch = function (data, type, row, meta) {
    return data[0];
};
