"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var api = require('./api.js');

function escapeHTML(s) {
    return new Option(s).innerHTML;
}

function renderSubsetInfo(si) {
    if (!si) {
        return "";
    }

    return Object.keys(si).map(function (k) {
        return {
            all: "",
            shortsus: "Short Suspensions: ",
            longsus: "Long suspensions: ",
            quote: "Quotes: ",
            nonquote: "Non-quotes: ",
        }[k] + si[k] + (si[k] > 1 ? " words" : " word");
    }).join(", ");
}

function renderChapters(items) {
    return items.map(function (i) {
        return '<a href="/chapter?chapter_id=' + i.id + '" title="' + renderSubsetInfo(i.subset_info) + '">' + escapeHTML(i.title) + "</a>";
    }).join(", ");
}

function renderBooks(items) {
    return items.map(function (i) {
        return "<h3>" + escapeHTML(i.title) + ": <small>" + renderSubsetInfo(i.subset_info) + "</small></h3>" +
            renderChapters(i.children || []);
    }).join("\n");
}

function renderCorpora(items) {
    return items.map(function (i) {
        return "<h2>" + escapeHTML(i.title) + ": <small>" + renderSubsetInfo(i.subset_info) + "</small></h2>" +
            renderBooks(i.children || []);
    }).join("\n");
}

function PageContents(content_el) {
    this.content_el = content_el;
}

PageContents.prototype.reload = function reload(page_state) {
    var self = this;

    return api.get('corpora/details').then(function (details) {
        self.content_el.innerHTML = renderCorpora(details.corpora);
    });

};

module.exports = PageContents;
