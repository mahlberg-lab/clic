import {createRequire} from 'node:module';
import {test} from 'tape';
import {JSDOM} from 'jsdom';

test('cm-apply-typopo', async (t) => {
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
        const {apply_typopo} = await import('../lib/cm-apply-typopo.mjs');
        const cm_region_decoration = await import('../lib/cm-region-decoration.mjs');
        const {EditorState, EditorSelection} = globalThis.require('@codemirror/state');
        const {EditorView} = globalThis.require('@codemirror/view');

        const make_view = (doc) => {
            const parent = globalThis.document.createElement('div');
            globalThis.document.body.append(parent);
            const view = new EditorView({
                state: EditorState.create({
                    doc: doc,
                    extensions: [cm_region_decoration.config],
                }),
                parent: parent,
            });
            return {view, parent};
        };

        // scope='all' on an empty doc is a no-op
        {
            const {view, parent} = make_view('');
            t.notOk(apply_typopo(view, 'all'), 'scope=all on empty doc returns false');
            t.equal(view.state.doc.toString(), '', 'empty doc still empty');
            view.destroy();
            parent.remove();
        }

        // scope='all' rewrites the whole doc
        {
            const {view, parent} = make_view('She said "hello"... and left.');
            t.ok(apply_typopo(view, 'all'), 'scope=all with content returns true');
            t.equal(
                view.state.doc.toString(),
                'She said “hello”… and left.',
                'scope=all applied curly quotes and ellipsis across whole doc',
            );
            view.destroy();
            parent.remove();
        }

        // scope='selection' with only an empty selection is a no-op
        {
            const {view, parent} = make_view('She said "hello"... and left.');
            view.dispatch({selection: {anchor: 3}});
            t.notOk(apply_typopo(view, 'selection'), 'scope=selection with empty selection returns false');
            t.equal(
                view.state.doc.toString(),
                'She said "hello"... and left.',
                'doc unchanged when selection is empty',
            );
            view.destroy();
            parent.remove();
        }

        // scope='selection' only rewrites the selected range
        {
            const {view, parent} = make_view('She said "hello"... and "bye"...');
            //                                  0         1         2         3
            //                                  0123456789012345678901234567890123
            view.dispatch({selection: EditorSelection.single(9, 19)});
            t.ok(apply_typopo(view, 'selection'), 'scope=selection with range returns true');
            t.equal(
                view.state.doc.toString(),
                'She said “hello”… and "bye"...',
                'only the selected range was rewritten',
            );
            view.destroy();
            parent.remove();
        }

        // scope='chapter' with no chapter regions is a no-op
        {
            const {view, parent} = make_view('Some "text"... with no regions.');
            t.notOk(apply_typopo(view, 'chapter'), 'scope=chapter with no regions returns false');
            t.equal(
                view.state.doc.toString(),
                'Some "text"... with no regions.',
                'doc unchanged when chapter cannot be found',
            );
            view.destroy();
            parent.remove();
        }

        // scope='chapter' rewrites only the chapter containing the cursor
        {
            //           0         1         2         3         4         5
            //           0123456789012345678901234567890123456789012345678901234567
            const doc = 'Ch1\n"a"... more.\nCh2\n"b"... more.\nCh3\n"c"... more.';
            const {view, parent} = make_view(doc);
            cm_region_decoration.view_update_regions(view, [
                ['chapter.title', 0, 3, 1],
                ['chapter.title', 17, 20, 2],
                ['chapter.title', 34, 37, 3],
            ]);
            // Cursor inside chapter 2
            view.dispatch({selection: {anchor: 22}});
            t.ok(apply_typopo(view, 'chapter'), 'scope=chapter returns true when chapter found');
            t.equal(
                view.state.doc.toString(),
                'Ch1\n"a"... more.\nCh2\n“b”… more.\nCh3\n"c"... more.',
                'only chapter 2 rewritten; chapters 1 and 3 untouched',
            );
            view.destroy();
            parent.remove();
        }

        // Unknown scope throws
        {
            const {view, parent} = make_view('hello');
            t.throws(
                () => apply_typopo(view, 'bogus'),
                /Unknown apply_typopo scope: bogus/v,
                'unknown scope throws',
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
