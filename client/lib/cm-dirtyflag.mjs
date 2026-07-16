// NB: Use require() so we pull the same copy as page_text.js
const cmState = require('@codemirror/state');
const cmView = require('@codemirror/view');

// Detangle individual exports as import would have done
const Compartment = cmState.Compartment;
const EditorState = cmState.EditorState;
const EditorView = cmView.EditorView;

const comp = new Compartment();

const txExtender = EditorState.transactionExtender.of(tr => {
    if (!tr.docChanged) {
        return null;
    }

    return {
        effects: comp.reconfigure(EditorView.editorAttributes.of({class: "df-dirty"})),
    };
});

export const config = [
    comp.of(EditorView.editorAttributes.of({class: "df-clean"})),
    txExtender,
];

/**
  * Clear the dirty flag on the given view.
  */
export function clear(view) {
    view.dispatch({
        effects: comp.reconfigure(EditorView.editorAttributes.of({class: "df-clean"})),
    });
}
