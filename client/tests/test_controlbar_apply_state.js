"use strict";
var test = require('tape');
var proxyquire = require('proxyquire');
var JSDOM = require('jsdom').JSDOM;

// Sibling test files clobber global.window / global.document at their own load
// time (they run their top-level requires before any test body executes). Keep
// our JSDOM references local, and reinstall them as globals at the start of
// each test so _apply_state's `window.Element` lookup still works.
var jsdom = new JSDOM('<!DOCTYPE html><html><body></body></html>', { url: 'http://localhost/' });
var jsdom_window = jsdom.window;
var jsdom_document = jsdom.window.document;

Object.defineProperty(global, 'window', { value: jsdom_window, configurable: true, writable: true });
Object.defineProperty(global, 'document', { value: jsdom_document, configurable: true, writable: true });
Object.defineProperty(global, 'navigator', { value: jsdom_window.navigator, configurable: true, writable: true });

var ControlBar = proxyquire.noCallThru().load('lib/controlbar.js', {
    './api.js': {},
    './panel_tagcolumn.js': function () {},
    './tagtoggle.js': function () {},
    './filesystem.js': {},
    './concordance_utils.js': {},
    './chosen_init.js': { init: function () {}, refresh: function () {} },
    './cm-command.mjs': { dispatch: function () {} },
    'browser-fs-access': {},
});

function fake_page_state(args) {
    return {
        arg: function (name) {
            return args[name];
        },
    };
}

function apply(elements, args, self) {
    // _apply_state resolves `window.Element` at runtime, so global.window has to
    // point at our JSDOM window during the call. Save-and-restore around it so
    // we don't disturb globals other test files rely on.
    var prev_window = global.window;
    var prev_document = global.document;
    global.window = jsdom_window;
    global.document = jsdom_document;
    try {
        ControlBar.prototype._apply_state.call(self || {}, elements, fake_page_state(args));
    } finally {
        global.window = prev_window;
        global.document = prev_document;
    }
}

function make_el(tagName) {
    return jsdom_document.createElement(tagName);
}

test('_apply_state: fieldset is skipped', function (t) {
    var fs = make_el('fieldset');
    fs.name = 'ignored';
    // arg() returning undefined for its name should not cause failure
    t.doesNotThrow(function () { apply([fs], {}); });
    t.end();
});

test('_apply_state: nameless element is skipped', function (t) {
    var el = make_el('input');
    el.type = 'text';
    el.value = 'untouched';
    // No name — even though arg() is queried, the element itself must not be mutated
    t.doesNotThrow(function () { apply([el], {}); });
    t.equal(el.value, 'untouched', 'value not overwritten');
    t.end();
});

test('_apply_state: radio inputs get checked=true only for matching value', function (t) {
    var r1 = make_el('input');
    r1.type = 'radio'; r1.name = 'conc-type'; r1.value = 'whole';
    r1.checked = true;
    var r2 = make_el('input');
    r2.type = 'radio'; r2.name = 'conc-type'; r2.value = 'any';
    var r3 = make_el('input');
    r3.type = 'radio'; r3.name = 'conc-type'; r3.value = 'inflect';

    apply([[r1, r2, r3]], { 'conc-type': 'any' });

    t.equal(r1.checked, false, 'r1 unchecked');
    t.equal(r2.checked, true, 'r2 checked (matches new_val)');
    t.equal(r3.checked, false, 'r3 unchecked');
    t.end();
});

test('_apply_state: checkboxes with array new_val', function (t) {
    var c1 = make_el('input');
    c1.type = 'checkbox'; c1.name = 'kwic-terms'; c1.value = 'a';
    var c2 = make_el('input');
    c2.type = 'checkbox'; c2.name = 'kwic-terms'; c2.value = 'b';
    var c3 = make_el('input');
    c3.type = 'checkbox'; c3.name = 'kwic-terms'; c3.value = 'c';
    c2.checked = true;  // start with a pre-existing (soon to be wrong) state

    apply([[c1, c2, c3]], { 'kwic-terms': ['a', 'c'] });

    t.equal(c1.checked, true, 'c1 in array → checked');
    t.equal(c2.checked, false, 'c2 not in array → unchecked');
    t.equal(c3.checked, true, 'c3 in array → checked');
    t.end();
});

test('_apply_state: single checkbox with scalar new_val', function (t) {
    var c = make_el('input');
    c.type = 'checkbox'; c.name = 'flag'; c.value = 'yes';

    apply([c], { flag: 'yes' });
    t.equal(c.checked, true, 'matching scalar → checked');

    apply([c], { flag: 'no' });
    t.equal(c.checked, false, 'non-matching scalar → unchecked');
    t.end();
});

test('_apply_state: nouislider element has slider set to split value', function (t) {
    var el = make_el('input');
    el.setAttribute('type', 'nouislider');  // JSDOM would normalise .type; use attribute
    el.name = 'kwic-span';
    var set_calls = [];
    el.slider_div = {
        noUiSlider: {
            set: function (v) { set_calls.push(v); },
        },
    };

    apply([el], { 'kwic-span': '-5:5' });

    t.deepEqual(set_calls, [['-5', '5']], 'slider .set called with split value');
    t.end();
});

test('_apply_state: multiple nousliders with same name throws', function (t) {
    function makeSlider() {
        var el = make_el('input');
        el.setAttribute('type', 'nouislider');
        el.name = 'kwic-span';
        el.slider_div = { noUiSlider: { set: function () {} } };
        return el;
    }

    t.throws(function () {
        apply([[makeSlider(), makeSlider()]], { 'kwic-span': '-5:5' });
    }, /only one nouislider/);
    t.end();
});

test('_apply_state: select value applied via jQuery.val()', function (t) {
    var sel = make_el('select');
    sel.name = 'clusterlength';
    ['3', '4', '5'].forEach(function (v) {
        var opt = make_el('option');
        opt.value = v;
        opt.textContent = v;
        sel.appendChild(opt);
    });

    apply([sel], { clusterlength: '4' });

    t.equal(sel.value, '4', 'select value set to "4"');
    t.end();
});

test('_apply_state: multiple selects with same name throws', function (t) {
    var s1 = make_el('select');
    s1.name = 'clusterlength';
    var s2 = make_el('select');
    s2.name = 'clusterlength';

    t.throws(function () {
        apply([[s1, s2]], { clusterlength: '4' });
    }, /only one select/);
    t.end();
});

test('_apply_state: corpora select resolves aliases', function (t) {
    var sel = make_el('select');
    sel.name = 'corpora';
    sel.multiple = true;
    ['a', 'b', 'c', 'd'].forEach(function (v) {
        var opt = make_el('option');
        opt.value = v;
        opt.textContent = v;
        sel.appendChild(opt);
    });

    apply(
        [sel],
        { corpora: ['dickens', 'b'] },
        { corpora: { aliases: { dickens: ['a', 'c'] } } }
    );

    var selected = Array.from(sel.options)
        .filter(function (o) { return o.selected; })
        .map(function (o) { return o.value; });
    t.deepEqual(selected.sort(), ['a', 'b', 'c'], 'dickens alias expanded to [a, c]');
    t.end();
});

test('_apply_state: refcorpora select also resolves aliases', function (t) {
    var sel = make_el('select');
    sel.name = 'refcorpora';
    sel.multiple = true;
    ['x', 'y'].forEach(function (v) {
        var opt = make_el('option');
        opt.value = v;
        opt.textContent = v;
        sel.appendChild(opt);
    });

    apply(
        [sel],
        { refcorpora: ['grp'] },
        { corpora: { aliases: { grp: ['x', 'y'] } } }
    );

    var selected = Array.from(sel.options)
        .filter(function (o) { return o.selected; })
        .map(function (o) { return o.value; });
    t.deepEqual(selected.sort(), ['x', 'y'], 'grp alias expanded');
    t.end();
});

test('_apply_state: unknown corpora selection falls through unchanged', function (t) {
    var sel = make_el('select');
    sel.name = 'corpora';
    sel.multiple = true;
    ['b'].forEach(function (v) {
        var opt = make_el('option');
        opt.value = v;
        sel.appendChild(opt);
    });

    apply(
        [sel],
        { corpora: ['b'] },
        { corpora: { aliases: {} } }
    );

    var selected = Array.from(sel.options)
        .filter(function (o) { return o.selected; })
        .map(function (o) { return o.value; });
    t.deepEqual(selected, ['b'], 'unaliased entry passes through');
    t.end();
});

test('_apply_state: text input value overwrites existing', function (t) {
    var el = make_el('input');
    el.type = 'text';
    el.name = 'conc-q';
    el.value = 'stale';

    apply([el], { 'conc-q': 'fresh' });
    t.equal(el.value, 'fresh', 'value replaced');
    t.end();
});

test('_apply_state: text input clones nodes for each array entry', function (t) {
    var parent = make_el('div');
    var el = make_el('input');
    el.type = 'text';
    el.name = 'q';
    parent.appendChild(el);

    apply([el], { q: ['alpha', 'beta', 'gamma'] });

    var inputs = parent.querySelectorAll('input');
    t.equal(inputs.length, 3, 'grew from 1 to 3 nodes');
    t.equal(inputs[0].value, 'alpha');
    t.equal(inputs[1].value, 'beta');
    t.equal(inputs[2].value, 'gamma');
    t.end();
});

test('_apply_state: text input removes trailing nodes when new_val is shorter', function (t) {
    var parent = make_el('div');
    var els = ['x', 'y', 'z'].map(function (v) {
        var el = make_el('input');
        el.type = 'text';
        el.name = 'q';
        el.value = v;
        parent.appendChild(el);
        return el;
    });

    apply([els], { q: ['only'] });

    var inputs = parent.querySelectorAll('input');
    t.equal(inputs.length, 1, 'shrank from 3 to 1 node');
    t.equal(inputs[0], els[0], 'the surviving node is the first one');
    t.equal(inputs[0].value, 'only', 'surviving node picked up new value');
    t.equal(inputs[0].disabled, false, 'not disabled — new_val is non-empty');
    t.end();
});

test('_apply_state: sole text input disabled (not infinite-looped) when new_val is empty', function (t) {
    var parent = make_el('div');
    var el = make_el('input');
    el.type = 'text';
    el.name = 'q';
    parent.appendChild(el);

    // If the shrink-loop's `all_els.length === 1` branch does not break, this
    // call would spin forever. tape aborts on timeout, so reaching the asserts
    // is itself part of the check.
    apply([el], { q: [] });

    t.equal(el.disabled, true, 'lone element marked disabled instead of removed');
    t.equal(parent.querySelectorAll('input').length, 1, 'element still attached to parent');
    t.end();
});

test('_apply_state: previously-disabled sole input is re-enabled and grown on re-apply', function (t) {
    var parent = make_el('div');
    var el = make_el('input');
    el.type = 'text';
    el.name = 'q';
    parent.appendChild(el);

    // First pass empties the state: element is kept but disabled.
    apply([el], { q: [] });
    t.equal(el.disabled, true, 'sanity: first pass disabled the element');

    // Second pass supplies values: the disabled element should come back to
    // life and the extras should be cloned in after it.
    apply([el], { q: ['x', 'y', 'z'] });

    var inputs = parent.querySelectorAll('input');
    t.equal(inputs.length, 3, 'grew back to 3 nodes');
    t.equal(inputs[0].disabled, false, 'original element re-enabled');
    t.equal(inputs[0].value, 'x');
    t.equal(inputs[1].value, 'y');
    t.equal(inputs[2].value, 'z');
    t.end();
});
