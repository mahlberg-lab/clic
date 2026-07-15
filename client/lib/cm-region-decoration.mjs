// NB: Use require() so we pull the same copy as page_text.js
const cmState = require('@codemirror/state');
const cmView = require('@codemirror/view');

// Detangle individual exports as import would have done
const Compartment = cmState.Compartment;
const Decoration = cmView.Decoration;
const StateField = cmState.StateField;
const StateEffect = cmState.StateEffect;
const EditorView = cmView.EditorView;

// Effect for swapping the decoration set
const region_decorations_set = StateEffect.define();

// State field that holds the current decoration set
const region_decorations_field = StateField.define({
    create: () => Decoration.none,
    update: (deco, tr) => {
        for (let i = 0; i < tr.effects.length; i++) {
            if (tr.effects[i].is(region_decorations_set)) {
                return tr.effects[i].value;
            }
        }

        return deco.map(tr.changes);
    },
    provide: function (f) {
        return EditorView.decorations.from(f);
    },
});

// Compartment whose contents control the class attribute on the editor's outer element
const visible_region_compartment = new Compartment();

export const config = [
    region_decorations_field,
    visible_region_compartment.of(EditorView.editorAttributes.of({class: []})),
];

// Convert region into the CSS class string to add on the decoration
// r should contain [(rclass), (start), (end), (rvalue)]
function region_to_class(r) {
    let cls = r[0].replaceAll('.', '-');
    if (r[0] === 'chapter.title') {
        cls += ' chapter-' + r[3];
    }

    return cls;
}

/**
  * Build a CM6 decoration set from the regions array
  */
export function view_update_regions(view, regions) {
    let i, r;
    const marks = [];
    const docLen = view.state.doc.length;

    for (i = 0; i < regions.length; i++) {
        r = regions[i];
        // Doc might have changed since we generated regions, ignore any outside document
        if (r[1] < docLen && r[2] <= docLen && r[2] > r[1]) {
            marks.push(Decoration.mark({class: region_to_class(r)}).range(r[1], r[2]));
        }
    }

    // NB: Decoration.set expects ranges sorted by from; pass sort=true to let CM sort
    view.dispatch({
        effects: region_decorations_set.of(Decoration.set(marks, true)),
    });
}

/**
  * Find document position of the chapter.title region for a given chapter_num,
  * or -1 if not found.
  */
export function chapter_title_pos(view, chapter_num) {
    const decorations = view.state.field(region_decorations_field);
    const cls = region_to_class(['chapter.title', undefined, undefined, chapter_num]);
    let pos = -1;
    decorations.between(0, view.state.doc.length, (from, to, deco) => {
        if (deco.spec.class === cls) {
            pos = from;
            return false;
        }
    });
    return pos;
}

/**
  * Build the editor-attributes extension that adds the book-content + per-region
  * highlight classes to the outer .cm-editor element.
  */
export function view_update_visible_regions(view, chap_highlight) {
    const classes = ['book-content'].concat((chap_highlight || []).map(x => 'h-' + x.replaceAll('.', '-'))).join(' ');

    view.dispatch({
        effects: visible_region_compartment.reconfigure(EditorView.editorAttributes.of({class: classes})),
    });
}
