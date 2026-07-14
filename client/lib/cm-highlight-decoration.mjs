// NB: Use require() so we pull the same copy as page_text.js
const cmState = require('@codemirror/state');
const cmView = require('@codemirror/view');

// Detangle individual exports as import would have done
const Decoration = cmView.Decoration;
const StateField = cmState.StateField;
const StateEffect = cmState.StateEffect;
const EditorView = cmView.EditorView;

// Effect for swapping the decoration set
const highlight_decorations_set = StateEffect.define();

// State field that holds the current decoration set
const highlight_decorations_field = StateField.define({
    create: () => Decoration.none,
    update: (deco, tr) => {
        for (let i = 0; i < tr.effects.length; i++) {
            if (tr.effects[i].is(highlight_decorations_set)) {
                return tr.effects[i].value;
            }
        }

        return deco.map(tr.changes);
    },
    provide: function (f) {
        return EditorView.decorations.from(f);
    },
});

export const config = [
    highlight_decorations_field,
];

export function view_update_highlights(view, highlight_arr) {
    const marks = highlight_arr.map(h => Decoration.mark({class: 'highlight'}).range(h[0], h[1]));

    view.dispatch({
        effects: highlight_decorations_set.of(Decoration.set(marks, true)),
    });
}
