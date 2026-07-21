"use strict";
var cm_region_decoration = require('./cm-region-decoration.mjs');
var cm_command = require('./cm-command.mjs');
var cm_dirtyflag = require('./cm-dirtyflag.mjs');
var jsclictagger = require('./jsclictagger.js');

var cm_commands = require('@codemirror/commands');
var cm_state = require('@codemirror/state');
var cm_view = require('@codemirror/view');

const ViewPlugin = cm_view.ViewPlugin;

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

let updateContentTimeout = null;

const updateContentPlugin = ViewPlugin.fromClass(class {
    constructor(view) {
        this.view = view;
    }

    update(update) {
        if (update.docChanged) {
            globalThis.clearTimeout(updateContentTimeout);
            updateContentTimeout = globalThis.setTimeout(() => {
                globalThis.dispatchEvent(new globalThis.CustomEvent('state_tweak', {
                    detail: {
                        state: {
                            "corpus-content": this.view.state.doc.toString(),
                            // NB: Any regions are now invalid, so if page re-loads they should be regenerated
                            "corpus-regions": ["__recalc"],
                        },
                    },
                }));
            }, 300);
        }
    }
});

function PageCorpus(content_el) {
    this.current = {};

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
                cm_commands.history(),
                cm_view.keymap.of(cm_commands.historyKeymap),
                cm_region_decoration.config,
                cm_dirtyflag.config,
                updateContentPlugin,
                cm_command.cm_command_plugin,
                // Let the outer #scrollable-body do the scrolling, not the editor
                cm_view.EditorView.theme({
                    "&": { height: "auto" },
                    ".cm-scroller": { overflow: "visible", fontFamily: "inherit" },
                    ".cm-content": { padding: 0, fontFamily: "inherit" },
                    ".cm-line": { padding: 0 }
                }),
            ]
        });

        this.view = new cm_view.EditorView({
            state: state,
            parent: content_el
        });

        // Add region-refresh button to recalc regions when dirty
        content_el.insertAdjacentHTML("beforeend", '<div id="confirm-region-refresh" class="button-group"><button><div class="icon">↺</div><div class="text">Recalc Regions</div></button></div>');
        content_el.lastElementChild.addEventListener("click", function (event) {
            event.preventDefault();
            event.stopPropagation();

            window.dispatchEvent(new window.CustomEvent('state_update', { detail: {
                state: {
                    "corpus-content": this.view.state.doc.toString(),
                    "corpus-regions": ["__recalc", "parp"],
                },
            }}));
        }.bind(this));
    };

    /**
      * Load the given text and add to page
      */
    this.reload = function reload(page_state) {
        return Promise.resolve().then(function () {
            // If we don't have a view or this is a new state (read: load new file), recreate editor
            if (!this.view || page_state.state("corpus-editoractive") === 'no') {
                this.build_view(page_state.state('corpus-content'));
            }

            return page_state.state('corpus-regions')[0] === "__recalc" || this.view.dom.classList.contains("df-dirty") ? jsclictagger.regionsFromContent({
              content: this.view.state.doc.toString(),
              highlight: ALL_REGIONS,
            }) : page_state.state('corpus-regions');
        }.bind(this)).then(function (regions) {
            cm_dirtyflag.clear(this.view);
            cm_region_decoration.view_update_regions(this.view, regions);
            cm_region_decoration.view_update_visible_regions(this.view, page_state.arg('chap-highlight'));

            window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
                state: {
                    "corpus-regions": regions,
                    // NB: This will be cleared on state_new, so don't need to explictly handle it
                    "corpus-editoractive": 'yes',
                },
            }}));
        }.bind(this));
    };

    this.shutdown = function () {
        // NB: This shouldn't clear HTML, as we may have repopulated with new content already
        return Promise.resolve(this.destroy_view());
    }.bind(this);

    this.page_title = function (page_state) {
        return "CLiC corpus editor - " + page_state.state("corpus-filename");
    };
}

module.exports = PageCorpus;
