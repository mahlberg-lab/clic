import {createRequire} from 'node:module';
import {test} from 'tape';
import {JSDOM} from 'jsdom';

test('cm-insert-quotation', async (t) => {
    const jsdom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {url: 'http://localhost/'});
    // JSDOM omits requestAnimationFrame; CodeMirror schedules a measure pass through it on construction
    jsdom.window.requestAnimationFrame = (cb) => jsdom.window.setTimeout(cb, 0);
    jsdom.window.cancelAnimationFrame = (id) => jsdom.window.clearTimeout(id);
    // Expose the JSDOM globals CodeMirror pokes at during construction
    const exposed = ['window', 'document', 'navigator', 'MutationObserver', 'Node', 'Element', 'HTMLElement', 'Range', 'DocumentFragment', 'getComputedStyle'];
    const original = {require: globalThis.require};
    globalThis.require = createRequire(import.meta.url);
    for (const k of exposed) {
        original[k] = global[k];
        global[k] = jsdom.window[k];
    }

    try {
        const {insert_quotation} = await import('../lib/cm-insert-quotation.mjs');
        const {EditorState, EditorSelection} = globalThis.require('@codemirror/state');
        const {EditorView} = globalThis.require('@codemirror/view');

        const make_view = (doc, extensions = []) => {
            const parent = globalThis.document.createElement('div');
            globalThis.document.body.append(parent);
            const view = new EditorView({
                state: EditorState.create({doc: doc, extensions: extensions}),
                parent: parent,
            });
            return {view, parent};
        };

        // Non-empty selection with no neighbouring quotes gets wrapped
        {
            const {view, parent} = make_view('word here');
            view.dispatch({selection: EditorSelection.single(0, 4)});
            t.ok(insert_quotation(view, '“', '”'), 'returns true when insertion happens');
            t.equal(view.state.doc.toString(), '“word” here', 'selection wrapped in open/close chars');
            view.destroy();
            parent.remove();
        }

        // Empty selection: both quotes inserted at the cursor
        {
            const {view, parent} = make_view('hello world');
            view.dispatch({selection: {anchor: 5}});
            t.ok(insert_quotation(view, '“', '”'), 'returns true for empty selection');
            t.equal(view.state.doc.toString(), 'hello“” world', 'both quotes inserted at cursor position');
            view.destroy();
            parent.remove();
        }

        // Existing straight quotes just outside the selection are replaced
        //             0         1
        //             0123456789012345678
        //             He said "hello" now
        {
            const {view, parent} = make_view('He said "hello" now');
            view.dispatch({selection: EditorSelection.single(9, 14)});
            t.ok(insert_quotation(view, '“', '”'), 'returns true when swapping outer quotes');
            t.equal(view.state.doc.toString(), 'He said “hello” now', 'straight quotes outside selection replaced');
            view.destroy();
            parent.remove();
        }

        // Existing straight quotes included in the selection are replaced
        {
            const {view, parent} = make_view('He said "hello" now');
            view.dispatch({selection: EditorSelection.single(8, 15)});
            t.ok(insert_quotation(view, '“', '”'), 'returns true when swapping inner quotes');
            t.equal(view.state.doc.toString(), 'He said “hello” now', 'straight quotes inside selection replaced');
            view.destroy();
            parent.remove();
        }

        // Any KNOWN_QUOTE_CHARS (not just ") outside the selection are swapped
        {
            const {view, parent} = make_view('He said «hello» now');
            view.dispatch({selection: EditorSelection.single(9, 14)});
            insert_quotation(view, '“', '”');
            t.equal(view.state.doc.toString(), 'He said “hello” now', 'guillemets outside selection replaced');
            view.destroy();
            parent.remove();
        }

        // When quotes appear both outside and inside, the outside ones are replaced (outside branch wins)
        //             0        1
        //             012345678
        //             ""hello""
        {
            const {view, parent} = make_view('""hello""');
            view.dispatch({selection: EditorSelection.single(1, 8)});
            insert_quotation(view, '“', '”');
            t.equal(view.state.doc.toString(), '“"hello"”', 'outer quotes replaced, inner ones left alone');
            view.destroy();
            parent.remove();
        }

        // Multiple selection ranges each get wrapped independently
        //             0         1
        //             0123456789012345
        //             alpha beta gamma
        {
            const {view, parent} = make_view('alpha beta gamma', [
                EditorState.allowMultipleSelections.of(true),
            ]);
            view.dispatch({
                selection: EditorSelection.create([
                    EditorSelection.range(0, 5),
                    EditorSelection.range(11, 16),
                ]),
            });
            t.ok(insert_quotation(view, '“', '”'));
            t.equal(view.state.doc.toString(), '“alpha” beta “gamma”', 'each range wrapped independently');
            view.destroy();
            parent.remove();
        }

        // Selecting the whole doc handles missing neighbours at both ends
        {
            const {view, parent} = make_view('abc');
            view.dispatch({selection: EditorSelection.single(0, 3)});
            t.ok(insert_quotation(view, '“', '”'));
            t.equal(view.state.doc.toString(), '“abc”', 'whole-doc selection wrapped without out-of-bounds reads');
            view.destroy();
            parent.remove();
        }

        // Empty selection between two adjacent quote chars replaces both
        {
            const {view, parent} = make_view('""');
            view.dispatch({selection: {anchor: 1}});
            insert_quotation(view, '“', '”');
            t.equal(view.state.doc.toString(), '“”', 'both surrounding quote chars replaced');
            view.destroy();
            parent.remove();
        }

        // Arbitrary open/close chars pass through verbatim
        {
            const {view, parent} = make_view('word');
            view.dispatch({selection: EditorSelection.single(0, 4)});
            insert_quotation(view, '«', '»');
            t.equal(view.state.doc.toString(), '«word»', 'accepts arbitrary open/close chars');
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
