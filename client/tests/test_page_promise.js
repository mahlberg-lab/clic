"use strict";
/*jslint todo: true, regexp: true, nomen: true, browser: true */
/*global Promise */
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
