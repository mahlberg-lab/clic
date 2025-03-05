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

test('renest_all', function (t) {
    // renest_all will include empty paths (so we show them attached to the root), but ignore the 0'th path
    t.deepEqual(util_flexiconc.renest_all({
        "0": {},
        "1": {},
    }), {
        "1": [],
    });

    // Full example
    t.deepEqual(util_flexiconc.renest_all({
        "0": {},
        "1": {
            "algo[0][case_sensitive]": [],
            "algo[0][algorithm_name]": ["KWIC Patterns"],
            "algo[0][positions]": ["-1"],
            "algo[0][tokens_attribute]": ["word"],
            "algo[1][algorithm_name]": ["Sort by Corpus Position"]
        },
        "2": {
            "algo[1][case_sensitive]": [],
            "algo[0][algorithm_name]": ["Random Sample"],
            "algo[0][sample_size]": ["10"],
            "algo[0][seed]": ["10"],
            "algo[1][algorithm_name]": ["KWIC Patterns"],
            "algo[1][positions]": ["-1"],
            "algo[1][tokens_attribute]": ["word"]
        },
        "3": {
            "algo[0][case_sensitive]": [],
            "algo[0][algorithm_name]": ["KWIC Patterns"],
            "algo[0][positions]": ["-1"],
            "algo[0][tokens_attribute]": ["word"],
            "algo[1][algorithm_name]": ["Select Slot"],
            "algo[1][slot_id]": ["5"]
        },
        "4": {},
    }), {
        "1": [
            { case_sensitive: null, algorithm_name: 'KWIC Patterns', positions: '-1', tokens_attribute: 'word' },
            { algorithm_name: 'Sort by Corpus Position' },
        ],
        "2": [
            { algorithm_name: 'Random Sample', sample_size: '10', seed: '10' },
            { case_sensitive: null, algorithm_name: 'KWIC Patterns', positions: '-1', tokens_attribute: 'word' },
        ],
        "3": [
            { case_sensitive: null, algorithm_name: 'KWIC Patterns', positions: '-1', tokens_attribute: 'word' },
            { algorithm_name: 'Select Slot', slot_id: '5' },
        ],
        "4": [],
    });

    t.end();
});
