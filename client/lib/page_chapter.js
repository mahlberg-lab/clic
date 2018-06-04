"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

function Chapter(content_el) {
    /**
      * Highlight terms between start and end, if args provided
      */
    this.highlight = function highlight(page_opts) {
        var highlight_arr = page_opts.arg('word-highlight').split(':'),
            start_node = parseInt(highlight_arr[0], 10),
            end_node = parseInt(highlight_arr[1], 10),
            word_nodes,
            i;

        if (start_node === 0 && end_node === 0) {
            return;
        }
        word_nodes = content_el.getElementsByTagName("w");
        if (start_node >= word_nodes.length || end_node >= word_nodes.length) {
            // Selection falls outside our range
            return;
        }
        for (i = start_node; i < end_node; i++) {
            word_nodes[i].setAttribute('selected', 'selected');
        }
        document.getElementById('scrollable-body').scrollTo(
            0,
            word_nodes[start_node].getBoundingClientRect().top
                + window.pageYOffset
                - (window.innerHeight / 2)
        );
    };

    /**
      * Load the given chapter and add to page
      */
    this.reload = function reload(page_opts) {
        var self = this;

        content_el.innerHTML = '';
        return Promise.resolve().then(function () {
            var args;

            if (page_opts.arg('chapter_id') > -1) {
                args = {
                    chapter_id: page_opts.arg('chapter_id'),
                };
            } else {
                if (!page_opts.arg('book')) {
                    throw new DisplayError("Please select a book", "warn");
                }
                args = {
                    book: page_opts.arg('book'),
                    chapter_num: page_opts.arg('chapter_num'),
                };
            }

            return api.get('chapter', args);
        }).then(function (doc) {
            var chapter_el = document.createElement('DIV');

            // Add a highlight-class for each specified highlight
            chapter_el.className = 'chapter ' + page_opts.arg('chap-highlight').map(function (x) { return 'highlight-' + x; }).join(" ");

            chapter_el.appendChild(doc.documentElement);
            content_el.appendChild(chapter_el);
            self.highlight(page_opts);
        });
    };

    this.page_title = function () {
        return "CLiC chapter view";
    };
}

module.exports = Chapter;