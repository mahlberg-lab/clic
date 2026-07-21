import {createRequire} from 'node:module';
import {test} from 'tape';
import {JSDOM} from 'jsdom';

test('cm-highlight-decoration', async (t) => {
    const jsdom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {url: 'http://localhost/'});
    // JSDOM omits requestAnimationFrame; CodeMirror schedules a measure pass through it on construction
    jsdom.window.requestAnimationFrame = (cb) => jsdom.window.setTimeout(cb, 0);
    jsdom.window.cancelAnimationFrame = (id) => jsdom.window.clearTimeout(id);
    // Expose the JSDOM globals CodeMirror pokes at during construction
    const exposed = ['window', 'document', 'navigator', 'MutationObserver', 'Node', 'Element', 'HTMLElement', 'Range', 'DocumentFragment', 'getComputedStyle'];
    const original = {require: globalThis.require};
    // Anchor require() at lib/ so relative imports inside lib modules resolve
    globalThis.require = createRequire(new URL('../lib/', import.meta.url));
    for (const k of exposed) {
        original[k] = global[k];
        global[k] = jsdom.window[k];
    }

    try {
        const {config, view_update_highlights} = await import('../lib/cm-highlight-decoration.mjs');
        const {EditorState} = globalThis.require('@codemirror/state');
        const {EditorView} = globalThis.require('@codemirror/view');

        // Walk every decoration set contributed to EditorView.decorations and return highlight ranges
        const highlight_ranges = (view) => {
            const out = [];
            for (const f of view.state.facet(EditorView.decorations)) {
                const set = typeof f === 'function' ? f(view) : f;
                if (!set || !set.iter) {
                    continue;
                }

                const iter = set.iter();
                while (iter.value) {
                    if (iter.value.spec && iter.value.spec.class === 'highlight') {
                        out.push([iter.from, iter.to]);
                    }

                    iter.next();
                }
            }

            return out;
        };

        const make_view = (doc) => {
            const parent = globalThis.document.createElement('div');
            globalThis.document.body.append(parent);
            const view = new EditorView({
                state: EditorState.create({doc: doc, extensions: [config]}),
                parent: parent,
            });
            return {view, parent};
        };

        // A fresh view has no highlight decorations
        {
            const {view, parent} = make_view('hello world');
            t.deepEqual(highlight_ranges(view), [], 'fresh view has no highlights');
            view.destroy();
            parent.remove();
        }

        // view_update_highlights adds a mark decoration covering the given range
        {
            const {view, parent} = make_view('hello world');
            view_update_highlights(view, [[0, 5]]);
            t.deepEqual(highlight_ranges(view), [[0, 5]], 'single highlight is applied');
            t.equal(
                view.dom.querySelectorAll('.highlight').length,
                1,
                'a .highlight span is rendered in the DOM',
            );
            view.destroy();
            parent.remove();
        }

        // Multiple ranges each produce their own mark decoration
        {
            const {view, parent} = make_view('hello world foo bar');
            view_update_highlights(view, [[0, 5], [6, 11], [12, 15]]);
            t.deepEqual(
                highlight_ranges(view),
                [[0, 5], [6, 11], [12, 15]],
                'multiple highlights are applied in order',
            );
            t.equal(
                view.dom.querySelectorAll('.highlight').length,
                3,
                'three .highlight spans are rendered',
            );
            view.destroy();
            parent.remove();
        }

        // A subsequent view_update_highlights replaces the prior set
        {
            const {view, parent} = make_view('hello world');
            view_update_highlights(view, [[0, 5]]);
            t.deepEqual(highlight_ranges(view), [[0, 5]], 'initial highlight applied');

            view_update_highlights(view, [[6, 11]]);
            t.deepEqual(
                highlight_ranges(view),
                [[6, 11]],
                'second call replaces the previous highlight set',
            );

            view.destroy();
            parent.remove();
        }

        // Passing an empty array clears all highlights
        {
            const {view, parent} = make_view('hello world');
            view_update_highlights(view, [[0, 5], [6, 11]]);
            t.equal(highlight_ranges(view).length, 2, 'highlights applied before clear');

            view_update_highlights(view, []);
            t.deepEqual(highlight_ranges(view), [], 'empty array clears all highlights');
            view.destroy();
            parent.remove();
        }

        // Highlight positions map through subsequent document changes
        {
            const {view, parent} = make_view('hello world');
            view_update_highlights(view, [[6, 11]]);
            t.deepEqual(highlight_ranges(view), [[6, 11]], 'highlight covers "world"');

            // Insert 3 chars before the highlight; the range should shift by +3
            view.dispatch({changes: {from: 0, insert: 'XYZ'}});
            t.equal(view.state.doc.toString(), 'XYZhello world', 'doc change applied');
            t.deepEqual(
                highlight_ranges(view),
                [[9, 14]],
                'highlight range shifts through mapped changes',
            );
            view.destroy();
            parent.remove();
        }
    } finally {
        globalThis.require = original.require;
        for (const k of exposed) {
            global[k] = original[k];
        }
    }

    t.end();
});
