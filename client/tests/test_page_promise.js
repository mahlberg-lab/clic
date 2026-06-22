"use strict";
var test = require('tape');

// Fake DOM elements to satisfy page_load's direct document.* references
function make_element() {
    var classes = {}, el;
    el = {
        innerHTML: '',
        innerText: '',
        classList: {
            add: function (c) { classes[c] = true; },
            remove: function (c) { delete classes[c]; },
            toggle: function (c, on) {
                if (on === true) { classes[c] = true; return; }
                if (on === false) { delete classes[c]; return; }
                if (classes[c]) { delete classes[c]; return; }
                classes[c] = true;
            },
            contains: function (c) { return !!classes[c]; },
        },
    };
    return el;
}

var confirm_update_el = make_element();
var confirm_update_text_el = make_element();
var body_el = make_element();

global.document = {
    body: body_el,
    querySelector: function (sel) {
        if (sel === '#confirm-update') { return confirm_update_el; }
        if (sel === '#confirm-update .text') { return confirm_update_text_el; }
        throw new Error("Unexpected querySelector: " + sel);
    },
};

// Silence expected console.error calls from tests that intentionally trigger errors
global.console.error = function () { return; };

var PagePromise = require('../lib/page_promise.js');

// Minimal alerts stub matching what page_load calls
function fake_alerts() {
    var a = {
        cleared: 0,
        shown: [],
        errors: [],
        clear: function () { a.cleared += 1; },
        show: function (msg, level) { a.shown.push({ msg: msg, level: level }); },
        error: function (err) { a.errors.push(err); },
        err_to_alert: function (err) {
            return [
                { message: err.message, stack: err.stack },
                err.level || 'error',
            ];
        },
    };
    return a;
}

function make_pp(components) {
    var pp = new PagePromise(function () { return components; }, {});
    pp.alerts = fake_alerts();
    return pp;
}

// Reset shared DOM element state between tests that inspect it
function reset_dom() {
    body_el.classList.remove('loading');
    confirm_update_el.classList.remove('visible');
    confirm_update_text_el.innerText = '';
}

test('page_load: missing comp_fn on component is skipped', function (t) {
    var pp = make_pp([{}, {}]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        t.equal(pp.alerts.shown.length, 0, "No alerts shown");
        t.equal(pp.alerts.errors.length, 0, "Top-level catch not hit");
        t.equal(pp.alerts.cleared, 1, "Alerts cleared once on reload");
        t.equal(pp.active_loads, 0, "Loading banner cleared");
        t.end();
    });
});

test('page_load: rejected promise from comp_fn shown as error alert', function (t) {
    var pp = make_pp([{}, {
        reload: function () { return Promise.reject(new Error("Async oh no!")); },
    }]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        t.equal(pp.alerts.shown.length, 1, "One alert shown");
        t.equal(pp.alerts.shown[0].level, 'error', "Alert shown at error level");
        t.equal(pp.alerts.shown[0].msg.message, 'Async oh no!', "Original error message preserved");
        t.equal(pp.alerts.errors.length, 0, "Top-level catch not hit");
        t.equal(pp.active_loads, 0, "Loading banner cleared");
        t.end();
    });
});

test('page_load: synchronous throw from comp_fn shown as error alert', function (t) {
    // Regression test: previously a synchronous throw would escape the
    // Promise.all machinery and land in the outer catch, losing the per-component
    // formatting. It should now be treated identically to a rejected Promise.
    var pp = make_pp([{}, {
        reload: function () { throw new Error("Sync oh no!"); },
    }]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        t.equal(pp.alerts.shown.length, 1, "One alert shown");
        t.equal(pp.alerts.shown[0].level, 'error', "Alert shown at error level");
        t.equal(pp.alerts.shown[0].msg.message, 'Sync oh no!', "Original error message preserved");
        t.equal(pp.alerts.errors.length, 0, "Top-level catch not hit");
        t.equal(pp.active_loads, 0, "Loading banner cleared");
        t.end();
    });
});

test('page_load: synchronous throw honours err.level', function (t) {
    var pp = make_pp([{}, {
        reload: function () {
            var e = new Error("Sync warn!");
            e.level = 'warn';
            throw e;
        },
    }]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        t.equal(pp.alerts.shown.length, 1, "One alert shown");
        t.equal(pp.alerts.shown[0].level, 'warn', "Alert shown at level from the error");
        t.equal(pp.alerts.shown[0].msg.message, 'Sync warn!', "Original error message preserved");
        t.end();
    });
});

test('page_load: sibling components still run when one throws synchronously', function (t) {
    var thrower = {
            reload: function () { throw new Error("Sync boom!"); },
        },
        good = {
            reload: function () { return Promise.resolve({ info: { message: "worked" } }); },
        },
        pp = make_pp([good, thrower]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        var levels = pp.alerts.shown.map(function (a) { return a.level; }).sort();
        t.deepEqual(levels, ['error', 'info'], "Info from good component + error from thrower");
        t.equal(pp.alerts.errors.length, 0, "Sync throw did not reach top-level catch");
        t.end();
    });
});

test('loading_banner: single increment/decrement toggles loading class', function (t) {
    reset_dom();
    var pp = make_pp([]);

    pp.loading_banner(1);
    t.equal(pp.active_loads, 1, "active_loads incremented");
    t.ok(body_el.classList.contains('loading'), "body has loading class");

    pp.loading_banner(-1);
    t.equal(pp.active_loads, 0, "active_loads decremented");
    t.notOk(body_el.classList.contains('loading'), "loading class removed at zero");

    t.end();
});

test('loading_banner: nested increments need balanced decrements', function (t) {
    reset_dom();
    var pp = make_pp([]);

    pp.loading_banner(1);
    pp.loading_banner(1);
    t.equal(pp.active_loads, 2, "two active loads");
    t.ok(body_el.classList.contains('loading'), "loading class present");

    pp.loading_banner(-1);
    t.equal(pp.active_loads, 1, "one still active");
    t.ok(body_el.classList.contains('loading'), "loading class still present");

    pp.loading_banner(-1);
    t.equal(pp.active_loads, 0, "all cleared");
    t.notOk(body_el.classList.contains('loading'), "loading class removed");

    t.end();
});

test('loading_banner: over-decrementing clamps at zero', function (t) {
    reset_dom();
    var pp = make_pp([]);

    pp.loading_banner(-1);
    t.equal(pp.active_loads, 0, "clamps at 0");
    t.notOk(body_el.classList.contains('loading'), "no loading class");

    pp.loading_banner(-5);
    t.equal(pp.active_loads, 0, "still 0");

    // A single subsequent increment still shows loading (i.e. the counter did
    // not go negative under the hood)
    pp.loading_banner(1);
    t.equal(pp.active_loads, 1, "increment works from clamped zero");
    t.ok(body_el.classList.contains('loading'), "loading class shown");

    t.end();
});

test('page_load: tweak mode does not clear alerts or reset confirm banner', function (t) {
    reset_dom();
    confirm_update_el.classList.add('visible');
    var pp = make_pp([{}, {
        tweak: function () { return Promise.resolve({}); },
    }]);

    return pp.page_load(Promise.resolve({}), 'tweak').then(function () {
        t.equal(pp.alerts.cleared, 0, "Alerts not cleared on tweak");
        t.ok(confirm_update_el.classList.contains('visible'), "Existing confirm banner preserved");
        t.equal(pp.active_loads, 0, "Loading banner cleared");
        t.end();
    });
});

test('page_load: info and warn results are surfaced as alerts', function (t) {
    reset_dom();
    var pp = make_pp([{}, {
        reload: function () {
            return Promise.resolve({
                info: { message: "informative" },
                warn: { message: "watch out" },
            });
        },
    }]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        var by_level = {};
        pp.alerts.shown.forEach(function (a) { by_level[a.level] = a.msg.message; });
        t.deepEqual(by_level, {
            info: "informative",
            warn: "watch out",
        }, "info and warn shown at their respective levels");
        t.equal(pp.alerts.errors.length, 0, "Top-level catch not hit");
        t.end();
    });
});

test('page_load: confirm result reveals the confirm-update banner with its message', function (t) {
    reset_dom();
    var pp = make_pp([{}, {
        reload: function () {
            return Promise.resolve({ confirm: { message: "are you sure?" } });
        },
    }]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        t.ok(confirm_update_el.classList.contains('visible'), "confirm-update made visible");
        t.equal(confirm_update_text_el.innerText, "are you sure?", "confirm message text set");
        t.end();
    });
});

test('page_load: new_data called on every component with the main components result', function (t) {
    reset_dom();
    var new_data_calls = [],
        main_result = { some: "data" },
        pp = make_pp([
            {
                reload: function () { return Promise.resolve({}); },
                new_data: function (data) { new_data_calls.push({ who: 'a', data: data }); },
            },
            {
                reload: function () { return Promise.resolve(main_result); },
                new_data: function (data) { new_data_calls.push({ who: 'b', data: data }); },
            },
            {
                reload: function () { return Promise.resolve({}); },
                new_data: function (data) { new_data_calls.push({ who: 'c', data: data }); },
            },
        ]);

    return pp.page_load(Promise.resolve({}), 'reload').then(function () {
        t.equal(new_data_calls.length, 3, "new_data fired on every component with one");
        new_data_calls.forEach(function (call) {
            t.equal(call.data, main_result, call.who + " received the [1] components data");
        });
        t.end();
    });
});

test('page_load: rejected input promise routed to top-level catch', function (t) {
    reset_dom();
    var pp = make_pp([]);

    return pp.page_load(Promise.reject(new Error("bad state")), 'reload').then(function () {
        t.equal(pp.alerts.errors.length, 1, "Top-level catch fired");
        t.equal(pp.alerts.errors[0].message, "bad state", "Original error passed through");
        t.equal(pp.alerts.shown.length, 0, "No per-component alert produced");
        t.equal(pp.active_loads, 0, "Loading banner cleared");
        t.end();
    });
});
