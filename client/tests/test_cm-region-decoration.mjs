import {createRequire} from 'node:module';
import {test} from 'tape';
import {JSDOM} from 'jsdom';

test('cm-region-decoration', async (t) => {
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
        const {
            config,
            view_update_regions,
            chapter_title_pos,
            chapter_range_at,
            view_update_visible_regions,
        } = await import('../lib/cm-region-decoration.mjs');
        const {EditorState} = globalThis.require('@codemirror/state');
        const {EditorView} = globalThis.require('@codemirror/view');

        // Walk every decoration set contributed to EditorView.decorations and return
        // [from, to, class] triples from region_decorations_field
        const region_ranges = (view) => {
            const out = [];
            for (const f of view.state.facet(EditorView.decorations)) {
                const set = typeof f === 'function' ? f(view) : f;
                if (!set || !set.iter) {
                    continue;
                }

                const iter = set.iter();
                while (iter.value) {
                    out.push([iter.from, iter.to, iter.value.spec.class]);
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

        // A fresh view has no region decorations
        {
            const {view, parent} = make_view('hello world');
            t.deepEqual(region_ranges(view), [], 'fresh view has no region decorations');
            view.destroy();
            parent.remove();
        }

        // view_update_regions applies a mark decoration per region, with dot-to-dash class
        {
            const {view, parent} = make_view('hello world');
            view_update_regions(view, [['some.region', 0, 5]]);
            t.deepEqual(
                region_ranges(view),
                [[0, 5, 'some-region']],
                'single region applied with dots-in-class replaced by dashes',
            );
            view.destroy();
            parent.remove();
        }

        // chapter.title regions get an extra chapter-N class using the rvalue
        {
            const {view, parent} = make_view('Ch1\nbody');
            view_update_regions(view, [['chapter.title', 0, 3, 1]]);
            t.deepEqual(
                region_ranges(view),
                [[0, 3, 'chapter-title chapter-1']],
                'chapter.title class includes chapter-<rvalue>',
            );
            view.destroy();
            parent.remove();
        }

        // Multiple regions are all applied
        {
            const {view, parent} = make_view('Ch1\nbody\nCh2\nmore');
            view_update_regions(view, [
                ['chapter.title', 0, 3, 1],
                ['chapter.text', 4, 8],
                ['chapter.title', 9, 12, 2],
            ]);
            t.deepEqual(
                region_ranges(view),
                [
                    [0, 3, 'chapter-title chapter-1'],
                    [4, 8, 'chapter-text'],
                    [9, 12, 'chapter-title chapter-2'],
                ],
                'multiple regions applied in order',
            );
            view.destroy();
            parent.remove();
        }

        // Regions extending beyond the doc, starting at/after doc end, or with end <= start are dropped
        {
            const {view, parent} = make_view('hello');
            view_update_regions(view, [
                ['ok', 0, 5], // valid — matches doc exactly
                ['past.end', 0, 6], // r[2] > docLen → dropped
                ['at.end', 5, 6], // r[1] >= docLen → dropped
                ['empty', 2, 2], // r[2] <= r[1] → dropped
                ['reversed', 3, 1], // r[2] <= r[1] → dropped
            ]);
            t.deepEqual(
                region_ranges(view),
                [[0, 5, 'ok']],
                'regions outside the doc or with empty/reversed ranges are filtered out',
            );
            view.destroy();
            parent.remove();
        }

        // A subsequent view_update_regions replaces the prior set
        {
            const {view, parent} = make_view('hello world');
            view_update_regions(view, [['first', 0, 5]]);
            t.deepEqual(region_ranges(view), [[0, 5, 'first']], 'initial region applied');

            view_update_regions(view, [['second', 6, 11]]);
            t.deepEqual(
                region_ranges(view),
                [[6, 11, 'second']],
                'second call replaces the previous region set',
            );
            view.destroy();
            parent.remove();
        }

        // Passing an empty array clears all regions
        {
            const {view, parent} = make_view('hello world');
            view_update_regions(view, [['a', 0, 5], ['b', 6, 11]]);
            t.equal(region_ranges(view).length, 2, 'regions applied before clear');

            view_update_regions(view, []);
            t.deepEqual(region_ranges(view), [], 'empty array clears all regions');
            view.destroy();
            parent.remove();
        }

        // Region positions map through subsequent document changes
        {
            const {view, parent} = make_view('hello world');
            view_update_regions(view, [['w', 6, 11]]);
            t.deepEqual(region_ranges(view), [[6, 11, 'w']], 'region covers "world"');

            view.dispatch({changes: {from: 0, insert: 'XYZ'}});
            t.equal(view.state.doc.toString(), 'XYZhello world', 'doc change applied');
            t.deepEqual(
                region_ranges(view),
                [[9, 14, 'w']],
                'region range shifts through mapped changes',
            );
            view.destroy();
            parent.remove();
        }

        // chapter_title_pos finds the chapter start by chapter number, or returns -1
        {
            //             0         1         2         3
            //             0123456789012345678901234567890123456789
            const doc = 'Ch1\nbody one\nCh2\nbody two\nCh3\nbody 3';
            const {view, parent} = make_view(doc);
            view_update_regions(view, [
                ['chapter.title', 0, 3, 1],
                ['chapter.title', 13, 16, 2],
                ['chapter.title', 25, 28, 3],
            ]);
            t.equal(chapter_title_pos(view, 1), 0, 'chapter 1 title at doc start');
            t.equal(chapter_title_pos(view, 2), 13, 'chapter 2 title after body one');
            t.equal(chapter_title_pos(view, 3), 25, 'chapter 3 title after body two');
            t.equal(chapter_title_pos(view, 4), -1, 'unknown chapter number returns -1');
            view.destroy();
            parent.remove();
        }

        // chapter_range_at returns [from, to] spanning the chapter that contains pos
        {
            //             0         1         2         3
            //             0123456789012345678901234567890123456789
            const doc = 'Ch1\nbody one\nCh2\nbody two\nCh3\nbody 3';
            const {view, parent} = make_view(doc);
            view_update_regions(view, [
                ['chapter.title', 0, 3, 1],
                ['chapter.title', 13, 16, 2],
                ['chapter.title', 25, 28, 3],
            ]);

            t.deepEqual(chapter_range_at(view, 0), [0, 13], 'pos on chapter 1 title returns chapter 1 range');
            t.deepEqual(chapter_range_at(view, 5), [0, 13], 'pos inside chapter 1 body returns chapter 1 range');
            t.deepEqual(chapter_range_at(view, 14), [13, 25], 'pos inside chapter 2 title returns chapter 2 range');
            t.deepEqual(chapter_range_at(view, 20), [13, 25], 'pos inside chapter 2 body returns chapter 2 range');
            t.deepEqual(
                chapter_range_at(view, 30),
                [25, doc.length],
                'pos inside last chapter runs to end of doc',
            );
            view.destroy();
            parent.remove();
        }

        // chapter_range_at returns null when pos is before any chapter title
        {
            const {view, parent} = make_view('preamble\nCh1\nbody');
            view_update_regions(view, [
                ['chapter.title', 9, 12, 1],
            ]);
            t.equal(chapter_range_at(view, 3), null, 'pos before any chapter title returns null');
            view.destroy();
            parent.remove();
        }

        // chapter_range_at returns null when no chapter.title regions exist
        {
            const {view, parent} = make_view('hello world');
            t.equal(chapter_range_at(view, 5), null, 'no chapter.title regions → null');
            view.destroy();
            parent.remove();
        }

        // view_update_visible_regions sets 'book-content' on the outer .cm-editor element
        {
            const {view, parent} = make_view('hello');
            view_update_visible_regions(view, []);
            t.ok(view.dom.classList.contains('book-content'), 'book-content class added');
            view.destroy();
            parent.remove();
        }

        // Each highlight becomes an h-<class> entry with dots replaced by dashes
        {
            const {view, parent} = make_view('hello');
            view_update_visible_regions(view, ['chapter.title', 'quote.direct']);
            t.ok(view.dom.classList.contains('book-content'), 'book-content still present');
            t.ok(view.dom.classList.contains('h-chapter-title'), 'h-chapter-title added');
            t.ok(view.dom.classList.contains('h-quote-direct'), 'h-quote-direct added');
            view.destroy();
            parent.remove();
        }

        // Passing undefined/null for chap_highlight is treated as no highlights
        {
            const {view, parent} = make_view('hello');
            view_update_visible_regions(view, undefined);
            t.ok(view.dom.classList.contains('book-content'), 'undefined chap_highlight still gives book-content');
            t.notOk(
                Array.from(view.dom.classList).some((c) => c.startsWith('h-')),
                'no h- classes added when chap_highlight is undefined',
            );
            view.destroy();
            parent.remove();
        }

        // A subsequent call replaces the prior highlight classes
        {
            const {view, parent} = make_view('hello');
            view_update_visible_regions(view, ['chapter.title']);
            t.ok(view.dom.classList.contains('h-chapter-title'), 'first highlight applied');

            view_update_visible_regions(view, ['quote.direct']);
            t.ok(view.dom.classList.contains('h-quote-direct'), 'second highlight applied');
            t.notOk(view.dom.classList.contains('h-chapter-title'), 'first highlight removed on reconfigure');
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
