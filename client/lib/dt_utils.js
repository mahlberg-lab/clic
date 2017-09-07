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

function isWord(s) {
    return (/\w/).test(s);
}

// Column is an array of tokens, mark these up as words, only sort on word content
function renderTokenArray(reverseSort, data, type, full, meta) {
    var i, t, count = 0, out = "";

    if (type === 'display') {
        for (i = 0; i < data.length; i++) {
            out += escapeHtml(isWord(data[i]) ? 'mark' : 'span', data[i]);
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
        return data[0];
    }

    xVal = (data[0] / data[1]) * 50; // word in book / total word count
    return '<a href="#" class="bookLink" title="Click to display concordance in book" target="_blank">' +
           '<svg width="50px" height="15px" xmlns="http://www.w3.org/2000/svg">' +
           '<rect x="0" y="4" width="50" height="7" fill="#ccc"/>' +
           '<line x1="' + xVal + '" x2="' + xVal + '" y1="0" y2="15" stroke="black" stroke-width="2px"/>' +
           '</svg></a>';
};
