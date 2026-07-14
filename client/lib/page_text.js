"use strict";
var api = require('./api.js');
var corpora_utils = require('lib/corpora_utils.js');
var DisplayError = require('./alerts.js').prototype.DisplayError;
var cm_region_decoration = require('./cm-region-decoration.mjs');
var cm_highlight_decoration = require('./cm-highlight-decoration.mjs');
var cm_command = require('./cm-command.mjs');

var cm_state = require('@codemirror/state');
var cm_view = require('@codemirror/view');

const ALL_REGIONS = [
    'metadata.title',
    'metadata.author',
    'chapter.part',
    'chapter.title',
    'chapter.sentence',
    'quote.quote',
    'quote.suspension.short',
    'quote.suspension.long',
    'quote.embedded',
];

function PageText(content_el) {
    this.current = {};

    /**
      * Scroll event: Find which chapter user is looking at, and send tweak event
      */
    this.scroll = function () {
        var body_el = document.getElementById('scrollable-body'),
            scroller_bottom = body_el.getBoundingClientRect().bottom,
            title_els;

        // All chapter titles above the bottom of the viewport
        title_els = Array.prototype.filter.call(
            document.querySelectorAll('#content .chapter-title'),
            function (el) {
                return el.getBoundingClientRect().top < scroller_bottom;
            }
        );
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
      * Tear down the current CodeMirror view, if any
      */
    this.destroy_view = function () {
        if (this.view) {
            this.view.destroy();
            this.view = null;
        }
    };

    /**
      * Build a fresh EditorView for the loaded content + regions + state.
      */
    this.build_view = function (init_content) {
        var state;

        this.destroy_view();
        content_el.innerHTML = '';

        state = cm_state.EditorState.create({
            doc: init_content,
            extensions: [
                cm_view.EditorView.lineWrapping,
                // NB: highlights first cause highlights to sit atop regions
                cm_highlight_decoration.config,
                cm_region_decoration.config,
                cm_command.cm_command_plugin,
                // Let the outer #scrollable-body do the scrolling, not the editor
                cm_view.EditorView.theme({
                    "&": { height: "auto" },
                    ".cm-scroller": { overflow: "visible", fontFamily: "inherit" },
                    ".cm-content": { padding: 0, fontFamily: "inherit" },
                    ".cm-line": { padding: 0 }
                }),
                // Set editor to readonly
                cm_state.EditorState.readOnly.of(true),
                cm_view.EditorView.editable.of(false),
                cm_view.EditorView.theme({
                    ".cm-content": { caretColor: "transparent" },
                }),
            ]
        });

        this.view = new cm_view.EditorView({
            state: state,
            parent: content_el
        });
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
                if (!body_el.querySelector(":scope > #content > .cm-editor")) {
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
                this.destroy_view();
                content_el.innerHTML = '';
                throw new DisplayError("Please select a book", "warn");
            }

            if (JSON.stringify(page_state.arg('book')) !== this.current.book) {
                // Rebuild this.current to invalidate anything else stored in it
                this.current = { book: JSON.stringify(page_state.arg('book')) };

                args = {
                    corpora: page_state.arg('book'),
                    regions: ALL_REGIONS,
                };

                return api.get('text', args).then(function (data) {
                    return { content: data.content, regions: data.data };
                });
            }

            return {};
        }.bind(this)).then(function (data) {
            var highlight_arr, pos, rerendered = false;

            if (!this.view) {
                this.build_view(data.content);
                rerendered = true;
            } else {
                data.content = this.view.state.doc.toString();
            }
            if (data.regions) {
                cm_region_decoration.view_update_regions(this.view, data.regions);
            }
            cm_region_decoration.view_update_visible_regions(this.view, page_state.arg('chap-highlight'));

            // (Re)build the view if the highlighted word range changed (or it's a new book)
            if (JSON.stringify(page_state.arg('word-highlight')) !== this.current['word-highlight']) {
                this.current['word-highlight'] = JSON.stringify(page_state.arg('word-highlight'));

                // Turn word-highlight into an array of start/stop pairs
                highlight_arr = page_state.arg('word-highlight').map(s => {
                    return s.split(':').map(x => parseInt(x, 10));
                });

                cm_highlight_decoration.view_update_highlights(this.view, highlight_arr);
            }

            if (rerendered) {
                // Freshly loaded, try harder to find something to scroll to
                // NB: Timeout to let content attach to page
                window.setTimeout(function () {
                    var target = -1, block = "center";
                    if (page_state.arg('word-highlight').length > 0) {
                        target = parseInt(page_state.arg('word-highlight')[0].split(':')[0], 10);
                    } else if (page_state.arg('chapter_num') > 0) {
                        target = cm_region_decoration.chapter_title_pos(this.view, page_state.arg('chapter_num'));
                        block = "start";
                    } else if (page_state.state('scroll-pos') > -1) {
                        document.getElementById('scrollable-body').scrollTop = page_state.state('scroll-pos');
                        return;
                    }
                    if (target >= 0) {
                        this.view.dispatch({
                            selection: { anchor: target },
                            effects: cm_view.EditorView.scrollIntoView(target, { y: block }),
                        });
                    }
                }.bind(this), 100);
            } else if (page_state.arg('chapter_num') > 0) {
                pos = cm_region_decoration.chapter_title_pos(this.view, page_state.arg('chapter_num'));
                if (pos >= 0) {
                    this.view.dispatch({
                        selection: { anchor: pos },
                        effects: cm_view.EditorView.scrollIntoView(pos, { y: "start" }),
                    });
                }
            }

            return {
                chapter_nums: data.content && data.regions ? corpora_utils.chapter_headings(data.content, data.regions) : undefined,
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

    this.shutdown = function () {
        return Promise.resolve(this.destroy_view());
    }.bind(this);

    this.page_title = function () {
        return "CLiC text view";
    };
}

module.exports = PageText;
