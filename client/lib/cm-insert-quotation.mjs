// Chars we recognise as already-installed quotation marks. If a selection is
// surrounded by one of these, clicking a button replaces them rather than
// nesting a new pair around them.
const KNOWN_QUOTE_CHARS = new Set([
    '"',
    "'",
    '“',
    '”',
    '‘',
    '’',
    '«',
    '»',
    '‹',
    '›',
    '„',
    '‚',
]);

export function insert_quotation(view, open_char, close_char) {
    const doc = view.state.doc;
    const changes = [];

    for (const range of view.state.selection.ranges) {
        if (range.from > 0 && KNOWN_QUOTE_CHARS.has(doc.sliceString(range.from - 1, range.from))) {
            // Quote mark outside selection, replace it
            changes.push({ from: range.from - 1, to: range.from, insert: open_char });
        } else if (range.from < doc.length && KNOWN_QUOTE_CHARS.has(doc.sliceString(range.from, range.from + 1))) {
            // Quote mark inside selection, replace it
            changes.push({ from: range.from, to: range.from + 1, insert: open_char });
        } else {
            changes.push({ from: range.from, insert: open_char });
        }

        if (range.to < doc.length && KNOWN_QUOTE_CHARS.has(doc.sliceString(range.to, range.to + 1))) {
            // Quote mark outside selection, replace it
            changes.push({ from: range.to, to: range.to + 1, insert: close_char });
        } else if (range.to > 0 && KNOWN_QUOTE_CHARS.has(doc.sliceString(range.to - 1, range.to))) {
            // Quote mark inside selection, replace it
            changes.push({ from: range.to - 1, to: range.to, insert: close_char });
        } else {
            changes.push({ from: range.to, insert: close_char });
        }
    }

    if (changes.length === 0) {
        return false;
    }

    view.dispatch({ changes: changes });
    return true;
}
