"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, DOMParser */
var api = require('./api.js');
var corpora_utils = require('lib/corpora_utils.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;

function PageText(content_el) {
    this.current = {};

    /**
      * Scroll event: Find which chapter user is looking at, and send tweak event
      */
    this.scroll = function () {
        var title_els, body_el = document.getElementById('scrollable-body');

        // Find all titles that are above the bottom of the page
        title_els = Array.prototype.filter.call(document.querySelectorAll('#content .chapter-title'), function (el) {
            return el.offsetParent && el.offsetTop < (el.offsetParent.scrollTop + el.offsetParent.offsetHeight);
        });
        if (title_els.length > 0) {
            window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
                args: {
                    chapter_num: [title_els[title_els.length - 1].className.match(/chapter-(\d+)/)[1]],
                },
                state: {
                    "scroll-pos": body_el.scrollTop,
                },
            }}));
        } else {
            window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
                state: {
                    "scroll-pos": body_el.scrollTop,
                },
            }}));
        }
    };

    /**
      * Load the given text and add to page
      */
    this.reload = function reload(page_state) {
        // Hook into the scroll event, use it to keep the chapter_num parameter up-to-date
        document.getElementById('scrollable-body').onscroll = function event_fn(e) {
            var body_el = e.target;

            if (body_el.scroll_timeout) {
                // Clear any previous scroll timeouts
                window.clearTimeout(body_el.scroll_timeout);
            }
            body_el.scroll_timeout = window.setTimeout(function () {
                if (!body_el.querySelector(":scope > #content > .book-content")) {
                    // Not part of the page anymore, so tidy up
                    body_el.onscroll = undefined;
                    return;
                }
                this.scroll();

            }.bind(this), 300);
        }.bind(this);

        return Promise.resolve().then(function () {
            var args;

            if (!page_state.arg('book')) {
                content_el.innerHTML = '';
                throw new DisplayError("Please select a book", "warn");
            }

            if (JSON.stringify(page_state.arg('book')) !== this.current.book) {
                // NB: Rebuild this.current to invalidate anything else stored in it
                this.current = { book: JSON.stringify(page_state.arg('book')) };

                content_el.innerHTML = '';
                args = {
                    corpora: page_state.arg('book'),
                    regions: [
                        'metadata.title',
                        'metadata.author',
                        'chapter.part',
                        'chapter.title',
                        'chapter.sentence',
                        'quote.quote',
                        'quote.suspension.short',
                        'quote.suspension.long',
                        'quote.embedded',
                    ],
                };

                // Fetch book text, stash in page object
                return api.get('text', args).then(function (data) {
                    this.content = data.content;
                    this.regions = data.data;
                }.bind(this));
            }
        }.bind(this)).then(function () {
            var book_el, highlight_arr, rerendered = false;

            // Render book, highlighting any words in chapter_num (e.g. for concordance selection)
            if (JSON.stringify(page_state.arg('word-highlight')) !== this.current['word-highlight']) {
                this.current['word-highlight'] = JSON.stringify(page_state.arg('word-highlight'));

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
                rerendered = true;
            }

            // Add a highlight-class for each specified highlight
            content_el.childNodes[0].className = 'book-content ' + page_state.arg('chap-highlight').map(function (x) {
                return 'h-' + x.replace(/\./g, '-');
            }).join(" ");

            if (rerendered) {
                // Freshly loaded, try harder to find something to scroll to
                // NB: Timeout to let content attach to page
                window.setTimeout(function () {
                    if (page_state.arg('word-highlight') !== '0:0') {
                        content_el.querySelector('.book-content > .highlight').scrollIntoView({block: "center"});
                    } else if (page_state.arg('chapter_num') > 0) {
                        content_el.querySelector('.book-content > .chapter-title.chapter-' + page_state.arg('chapter_num')).scrollIntoView();
                    } else if (page_state.state('scroll-pos') > -1) {
                        document.getElementById('scrollable-body').scrollTop = page_state.state('scroll-pos');
                    }
                }, 100);
            } else {
                if (page_state.arg('chapter_num') > 0) {
                    content_el.querySelector('.book-content > .chapter-title.chapter-' + page_state.arg('chapter_num')).scrollIntoView();
                }
            }

            // Return data for ControlBar.prototype.new_data
            return {
                chapter_nums: corpora_utils.chapter_headings(this.content, this.regions),
                chapter_num_selected: page_state.arg('chapter_num'),
            };
        }.bind(this));
    };

    this.tweak = function tweak(page_state) {
        // Tell controlbar about the changes
        return Promise.resolve({
            chapter_num_selected: page_state.arg('chapter_num'),
        });
    };

    this.page_title = function () {
        return "CLiC text view";
    };
}

module.exports = PageText;
