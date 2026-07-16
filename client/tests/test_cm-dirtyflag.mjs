import {createRequire} from 'node:module';
import {test} from 'tape';
import {JSDOM} from 'jsdom';

test('cm-dirtyflag', async (t) => {
    const jsdom = new JSDOM('<!DOCTYPE html><html><body></body></html>', {url: 'http://localhost/'});
    // JSDOM omits requestAnimationFrame; CodeMirror schedules a measure pass through it on construction
    jsdom.window.requestAnimationFrame = (cb) => jsdom.window.setTimeout(cb, 0);
    jsdom.window.cancelAnimationFrame = (id) => jsdom.window.clearTimeout(id);
    // Expose the JSDOM globals CodeMirror pokes at during construction
    const exposed = ['window', 'document', 'navigator', 'MutationObserver', 'Node', 'Element', 'HTMLElement', 'Range', 'DocumentFragment', 'getComputedStyle'];
    const original = {require: globalThis.require};
    globalThis.require = createRequire(import.meta.url);
    for (const k of exposed) {
        original[k] = globalThis[k];
        globalThis[k] = jsdom.window[k];
    }

    try {
        const {config, clear} = await import('../lib/cm-dirtyflag.mjs');
        const {EditorState} = globalThis.require('@codemirror/state');
        const {EditorView} = globalThis.require('@codemirror/view');

        const parent = globalThis.document.createElement('div');
        globalThis.document.body.append(parent);
        const view = new EditorView({
            state: EditorState.create({doc: 'hello', extensions: [config]}),
            parent: parent,
        });

        t.ok(view.dom.classList.contains('df-clean'), 'new view starts df-clean');
        t.notOk(view.dom.classList.contains('df-dirty'), 'new view is not df-dirty');

        // Selection-only changes do not flip the flag
        view.dispatch({selection: {anchor: 1}});
        t.ok(view.dom.classList.contains('df-clean'), 'selection change keeps df-clean');
        t.notOk(view.dom.classList.contains('df-dirty'), 'selection change does not set df-dirty');

        // A doc change flips df-clean → df-dirty
        view.dispatch({changes: {from: 5, insert: ' world'}});
        t.equal(view.state.doc.toString(), 'hello world', 'doc change applied');
        t.ok(view.dom.classList.contains('df-dirty'), 'doc change sets df-dirty');
        t.notOk(view.dom.classList.contains('df-clean'), 'doc change clears df-clean');

        // clear() resets back to df-clean without touching the doc
        clear(view);
        t.equal(view.state.doc.toString(), 'hello world', 'clear() leaves doc alone');
        t.ok(view.dom.classList.contains('df-clean'), 'clear() sets df-clean');
        t.notOk(view.dom.classList.contains('df-dirty'), 'clear() clears df-dirty');

        // A further doc change re-dirties
        view.dispatch({changes: {from: 0, insert: '!'}});
        t.ok(view.dom.classList.contains('df-dirty'), 'subsequent doc change re-sets df-dirty');

        view.destroy();
        parent.remove();
    } finally {
        globalThis.require = original.require;
        for (const k of exposed) {
            globalThis[k] = original[k];
        }
    }

    t.end();
});
