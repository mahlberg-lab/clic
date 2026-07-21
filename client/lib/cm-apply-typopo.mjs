// NB: Use require() so we pull the same copy as page_text.js
const typopo = require('typopo');
const cm_region_decoration = require('./cm-region-decoration.mjs');

function range_change(doc, from, to) {
    // NB: locale should come from the document once available
    const docLocale = 'en-us';

    // https://github.com/surfinzap/typopo#api
    return {
        from: from,
        to: to,
        insert: typopo.fixTypos(doc.sliceString(from, to), docLocale, {
            removeLines: false,
        }),
    };
}

export function apply_typopo(view, scope) {
    const doc = view.state.doc;
    const changes = [];

    if (scope === 'all') {
        if (doc.length > 0) {
            changes.push(range_change(doc, 0, doc.length));
        }
    } else if (scope === 'selection') {
        for (const range of view.state.selection.ranges) {
            if (!range.empty) {
                changes.push(range_change(doc, range.from, range.to));
            }
        }
    } else if (scope === 'chapter') {
        const chapter = cm_region_decoration.chapter_range_at(
            view,
            view.state.selection.main.head,
        );
        if (chapter) {
            changes.push(range_change(doc, chapter[0], chapter[1]));
        }
    } else {
        throw new Error("Unknown apply_typopo scope: " + scope);
    }

    if (changes.length === 0) {
        return false;
    }

    view.dispatch({ changes: changes });
    return true;
}
