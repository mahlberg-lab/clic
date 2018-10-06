"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, DOMParser */
var api = require('./api.js');
var corpora_utils = require('lib/corpora_utils.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

function PageText(content_el) {
    this.current = {};
    /**
      * Load the given text and add to page
      */
    this.reload = function reload(page_state) {
        var p = Promise.resolve({}), force_update = false;

        if (JSON.stringify(page_state.arg('book')) !== this.current.book) {
            p = p.then(function (p_data) {
                var args;

                content_el.innerHTML = '';
                if (!page_state.arg('book')) {
                    throw new DisplayError("Please select a book", "warn");
                }
                args = {
                    corpora: page_state.arg('book'),
                    regions: [
                        'metadata.title',
                        'metadata.author',
                        'chapter.title',
                        'chapter.sentence',
                        'quote.quote',
                        'quote.suspension.short',
                        'quote.suspension.long',
                        'quote.embedded',
                        'quote.embedded.suspension.short',
                        'quote.embedded.suspension.long',
                    ],
                };

                return api.get('text', args);
            }.bind(this)).then(function (data) {
                this.content = data.content;
                this.regions = data.data;

                data.chapter_nums = corpora_utils.chapter_headings(this.content, this.regions);

                return data;
            }.bind(this));
            this.current.book = JSON.stringify(page_state.arg('book'));
            force_update = true;
        }

        // Highlight any words in chapter_num (e.g. for concordance selection)
        if (force_update || JSON.stringify(page_state.arg('word-highlight')) !== this.current['word-highlight']) {
            p = p.then(function (p_data) {
                var book_el, highlight_arr;

                highlight_arr = page_state.arg('word-highlight').split(':').map(function (x) {
                    return parseInt(x, 10);
                });
                if (highlight_arr[0] === 0 && highlight_arr[1] === 0) {
                    highlight_arr = null;
                }

                content_el.innerHTML = '';
                book_el = document.createElement('DIV');
                book_el.className = 'book-content';
                book_el.innerHTML = corpora_utils.regions_to_html(this.content, this.regions, highlight_arr);
                content_el.appendChild(book_el);

                if (highlight_arr) {
                    content_el.querySelector('.book-content > .highlight').scrollIntoView();
                }

                return p_data;
            }.bind(this));
            this.current['word-highlight'] = JSON.stringify(page_state.arg('word-highlight'));
        }

        if (force_update || JSON.stringify(page_state.arg('chapter_num')) !== this.current.chapter_num) {
            p = p.then(function (p_data) {
                // Find chapter to scroll to, or top of page
                var chapter_el = content_el.querySelector(
                    '.chapter-title.chapter-' + page_state.arg('chapter_num')
                );

                if (chapter_el) {
                    chapter_el.scrollIntoView();

                    // Tell controlbar about the changes
                    p_data.chapter_num_selected = chapter_el.getAttribute('data-num');
                }

                return p_data;
            });
            this.current.chapter_num = JSON.stringify(page_state.arg('chapter_num'));
        }

        if (force_update || JSON.stringify(page_state.arg('chap-highlight')) !== this.current['chap-highlight']) {
            p = p.then(function (p_data) {
                // Add a highlight-class for each specified highlight
                content_el.childNodes[0].className = 'book-content ' +
                    page_state.arg('chap-highlight').map(function (x) {
                        return 'h-' + x.replace(/\./g, '-');
                    }).join(" ");

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
