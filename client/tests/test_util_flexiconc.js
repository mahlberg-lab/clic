"use strict";
/*jslint todo: true, regexp: true, nomen: true, browser: true */
var test = require('tape');

var util_flexiconc = require('../lib/util_flexiconc.js');
var State = require('../lib/state.js');

/** Generate a fake window object */
function fake_window(pathname, search, hist_state) {
    return {
        location: {
            pathname: pathname,
            search: search,
        },
        history: {
            state: hist_state,
        },
    };
}

test('nested_args', function (t) {
    var s;

    // Nested args don't have default, assume array
    s = new State(fake_window('/moo/doc', '?animals[cows][]=daisy&animals[cows][]=freda&animals[pig][a]=frank', {}), {animals: {}});
    t.deepEqual(s.arg("animals[cows][]"), ["daisy", "freda"]);
    t.deepEqual(s.arg("animals[pig][a]"), ["frank"]);
    t.deepEqual(s.arg("animals[ducks][]"), []);

    t.deepEqual(util_flexiconc.renest_args(s.all_args()), { animals: {
        cows: [ 'daisy', 'freda' ],
        pig: { a: 'frank' },
    }});

    // Nested args are preserved in URL
    t.deepEqual(s.to_url(), "/moo/doc?animals[cows][]=daisy&animals[cows][]=freda&animals[pig][a]=frank");

    t.end();
});
