import {createRequire} from 'node:module';
import {test} from 'tape';
import {JSDOM} from 'jsdom';

test('cm-command', async (t) => {
    const jsdom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {url: 'http://localhost/'});
    // JSDOM omits requestAnimationFrame; CodeMirror schedules a measure pass through it on construction
    jsdom.window.requestAnimationFrame = (cb) => jsdom.window.setTimeout(cb, 0);
    jsdom.window.cancelAnimationFrame = (id) => jsdom.window.clearTimeout(id);
    // Expose the JSDOM globals CodeMirror pokes at during construction
    const exposed = ['window', 'document', 'navigator', 'MutationObserver', 'Node', 'Element', 'HTMLElement', 'Range', 'DocumentFragment', 'getComputedStyle', 'Event', 'CustomEvent', 'EventTarget'];
    // cm_command_plugin binds its listener to globalThis; bridge those methods to jsdom.window
    const bridged = ['addEventListener', 'removeEventListener', 'dispatchEvent'];
    const original = {require: globalThis.require};
    // Anchor require() at lib/ so relative imports inside lib modules resolve
    globalThis.require = createRequire(new URL('../lib/', import.meta.url));
    for (const k of exposed) {
        original[k] = global[k];
        global[k] = jsdom.window[k];
    }

    for (const k of bridged) {
        original[k] = global[k];
        global[k] = jsdom.window[k].bind(jsdom.window);
    }

    try {
        const {dispatch, cm_command_plugin} = await import('../lib/cm-command.mjs');
        const {EditorState, EditorSelection} = globalThis.require('@codemirror/state');
        const {EditorView} = globalThis.require('@codemirror/view');
        const {history} = globalThis.require('@codemirror/commands');

        // dispatch() fires a 'cm-command' CustomEvent on the given target
        {
            const events = [];
            const target = new jsdom.window.EventTarget();
            target.addEventListener('cm-command', e => events.push(e));

            dispatch(target, 'undo');
            t.equal(events.length, 1, 'dispatch fired one event');
            t.equal(events[0].type, 'cm-command', 'event type is cm-command');
            t.equal(events[0].detail.name, 'undo', 'detail.name is the command name');
            t.deepEqual(events[0].detail.args, [], 'detail.args defaults to []');
        }

        // dispatch() carries args through in detail.args
        {
            const events = [];
            const target = new jsdom.window.EventTarget();
            target.addEventListener('cm-command', e => events.push(e));

            dispatch(target, 'insert-quotation', ['“', '”']);
            t.deepEqual(
                events[0].detail.args,
                ['“', '”'],
                'detail.args carries the provided arguments',
            );
        }

        const make_view = (doc) => {
            const parent = globalThis.document.createElement('div');
            globalThis.document.body.append(parent);
            const view = new EditorView({
                state: EditorState.create({doc: doc, extensions: [history(), cm_command_plugin]}),
                parent: parent,
            });
            return {view, parent};
        };

        // Plugin routes a valid command name to the corresponding command (undo)
        {
            const {view, parent} = make_view('hello');
            view.dispatch({changes: {from: 5, insert: ' world'}});
            t.equal(view.state.doc.toString(), 'hello world', 'change applied before undo');

            dispatch(globalThis, 'undo');
            t.equal(view.state.doc.toString(), 'hello', 'undo command was invoked on the view');

            view.destroy();
            parent.remove();
        }

        // Plugin passes args through to the command (insert-quotation open/close chars)
        {
            const {view, parent} = make_view('word');
            view.dispatch({selection: EditorSelection.single(0, 4)});

            dispatch(globalThis, 'insert-quotation', ['“', '”']);
            t.equal(
                view.state.doc.toString(),
                '“word”',
                'insert-quotation received the provided open/close chars',
            );

            view.destroy();
            parent.remove();
        }

        // Only the alive view receives events; destroyed plugin instances unregister
        {
            const {view: v1, parent: p1} = make_view('one');
            const {view: v2, parent: p2} = make_view('two');

            // Destroy v1 first — its listener should be gone
            v1.destroy();
            p1.remove();

            // Now dispatch a change to v2 and undo via the plugin
            v2.dispatch({changes: {from: 3, insert: '!'}});
            t.equal(v2.state.doc.toString(), 'two!', 'change applied to surviving view');

            dispatch(globalThis, 'undo');
            t.equal(v2.state.doc.toString(), 'two', 'undo applied to surviving view');

            v2.destroy();
            p2.remove();
        }

        // With no views alive, no listener remains — dispatch is a no-op and does not throw
        t.doesNotThrow(
            () => dispatch(globalThis, 'undo'),
            'dispatch with no plugin instance attached does not throw',
        );
    } finally {
        globalThis.require = original.require;
        for (const k of [...exposed, ...bridged]) {
            global[k] = original[k];
        }
    }

    t.end();
});
