"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, DOMParser */
var api = require('./api.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

function PageText(content_el) {
    this.current = {};
    /**
      * Load the given text and add to page
      */
    this.reload = function reload(page_state) {
        var p = Promise.resolve({}), force_update = false;

        function get_title(chapter_el, chapter_num) {
            var out, title_el = chapter_el.querySelector('title');

            if (title_el) {
                out = title_el.innerHTML;
            }

            if (!out) {
                out = 'Chapter ' + chapter_num;
            }

            return out;
        }

        if (JSON.stringify(page_state.arg('book')) !== this.current.book) {
            p = p.then(function (p_data) {
                var args;

                content_el.innerHTML = '';
                if (!page_state.arg('book')) {
                    throw new DisplayError("Please select a book", "warn");
                }
                args = {
                    corpora: page_state.arg('book'),
                };

                return api.get('text', args);
            }).then(function (data) {
                var i, chapter_el, doc, parser = new DOMParser();

                data.chapter_nums = [];
                for (i = 0; i < data.data.length; i++) {
                    doc = parser.parseFromString(data.data[i][2], 'application/xml');
                    if (doc.documentElement.nodeName === "parsererror") {
                        throw new Error("Cannot parse chapter: " + data.data[i][0] + '/' + data.data[i][1]);
                    }

                    chapter_el = document.createElement('DIV');
                    chapter_el.className = 'chapter';
                    chapter_el.setAttribute('data-book', data.data[i][0]);
                    chapter_el.setAttribute('data-num', data.data[i][1]);
                    chapter_el.appendChild(doc.documentElement);
                    content_el.appendChild(chapter_el);

                    // Tell controlbar about the chapter
                    data.chapter_nums.push({
                        id: data.data[i][1],
                        title: get_title(chapter_el, data.data[i][1]),
                    });
                }

                return data;
            });
            this.current.book = JSON.stringify(page_state.arg('book'));
            force_update = true;
        }

        if (force_update || JSON.stringify(page_state.arg('chapter_num')) !== this.current.chapter_num) {
            p = p.then(function (p_data) {
                var chapter_el = content_el.querySelector('.chapter[data-num="' + page_state.arg('chapter_num') + '"]');

                if (!chapter_el) {
                    // Not found, so select the first one
                    chapter_el = content_el.childNodes[0];
                }

                chapter_el.scrollIntoView();

                // Tell controlbar about the changes
                p_data.chapter_num_selected = chapter_el.getAttribute('data-num');

                return p_data;
            });
            this.current.chapter_num = JSON.stringify(page_state.arg('chapter_num'));
        }

        // Highlight any words in chapter_num (e.g. for concordance selection)
        if (force_update || JSON.stringify(page_state.arg('word-highlight')) !== this.current['word-highlight']) {
            p = p.then(function (p_data) {
                var highlight_arr = page_state.arg('word-highlight').split(':'),
                    start_node = parseInt(highlight_arr[1], 10),
                    end_node = parseInt(highlight_arr[2], 10),
                    word_nodes,
                    i,
                    chapter_el = content_el.querySelector('.chapter[data-num="' + highlight_arr[0] + '"]');

                if (!chapter_el || (start_node === 0 && end_node === 0)) {
                    return p_data;
                }

                word_nodes = chapter_el.getElementsByTagName("w");
                if (start_node >= word_nodes.length || end_node >= word_nodes.length) {
                    // Selection falls outside our range
                    return p_data;
                }

                for (i = start_node; i < end_node; i++) {
                    word_nodes[i].setAttribute('selected', 'selected');
                }
                word_nodes[start_node].scrollIntoView();

                return p_data;
            });
            this.current['word-highlight'] = JSON.stringify(page_state.arg('word-highlight'));
        }

        if (force_update || JSON.stringify(page_state.arg('chap-highlight')) !== this.current['chap-highlight']) {
            p = p.then(function (p_data) {
                Array.prototype.map.call(content_el.childNodes, function (chapter_el) {
                    // Add a highlight-class for each specified highlight
                    chapter_el.className = 'chapter ' +
                        page_state.arg('chap-highlight').map(function (x) { return 'highlight-' + x; }).join(" ");
                });

                return p_data;
            });
            this.current['chap-highlight'] = JSON.stringify(page_state.arg('chap-highlight'));
        }

        return p;
    };

    this.page_title = function () {
        return "CLiC text view";
    };
}

module.exports = PageText;
