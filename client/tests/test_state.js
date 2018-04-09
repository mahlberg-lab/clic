"use strict";
/*jslint todo: true, regexp: true, nomen: true, browser: true */
var test = require('tape');

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

test('to_args', function (t) {
    var s;

    // No arguments at all
    s = new State(fake_window('/cow', '', {}));
    t.deepEqual(s.doc(), '/cow');
    t.deepEqual(s.arg(), []);
    t.deepEqual(s.to_args(), [{}, '', '/cow']);

    // Only positional arguments
    s = new State(fake_window('/moo/doc', '?cuthbert&dibble&grub', {}));
    t.deepEqual(s.doc(), '/moo/doc');
    t.deepEqual(s.arg(), ['cuthbert', 'dibble', 'grub']);
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cuthbert&dibble&grub']);

    // Positional & named mixed, end up sorted, positional at end
    s = new State(fake_window('/moo/doc', '?cuthbert&pigs=no&dibble&grub&cows=daisy', {}));
    t.deepEqual(s.doc(), '/moo/doc');
    t.deepEqual(s.arg(), ['cuthbert', 'dibble', 'grub']);
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cuthbert&dibble&grub&cows=daisy&pigs=no']);

    // State for page also returned as-was
    s = new State(fake_window('/moo/doc', '?cuthbert&pigs=no&dibble&grub&cows=daisy', {animals: {duck: 2, goat: 3}}));
    t.deepEqual(s.doc(), '/moo/doc');
    t.deepEqual(s.arg(), ['cuthbert', 'dibble', 'grub']);
    t.deepEqual(s.to_args(), [
        { animals: { duck: 2, goat: 3 } },
        '',
        '/moo/doc?cuthbert&dibble&grub&cows=daisy&pigs=no',
    ]);

    t.end();
});

test('to_url', function (t) {
    var s;

    // to_url just returns the url part of any state
    s = new State(fake_window('/moo/doc', '?cuthbert&pigs=no&dibble&grub&cows=daisy', {animals: {duck: 2, goat: 3}}));
    t.deepEqual(s.to_url(), '/moo/doc?cuthbert&dibble&grub&cows=daisy&pigs=no');

    t.end();
});

test('arg:defaults', function (t) {
    var s;

    // Can't fetch without defining default
    s = new State(fake_window('/moo/doc', '?cows=daisy', {}));
    t.deepEqual(s.doc(), '/moo/doc');
    t.deepEqual(s.arg(), []);
    t.throws(function () {
        return s.arg('cows');
    }, /Unknown/);

    // Define cows with single default, multiple arguments concatenated
    s = new State(fake_window('/moo/doc', '?', {}), {cows: "bob"});
    t.deepEqual(s.arg('cows'), 'bob');
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc']);
    s = new State(fake_window('/moo/doc', '?cows=bob', {}), {cows: "bob"});
    t.deepEqual(s.arg('cows'), 'bob');
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cows=bob']); //NB: We're not stripping away useless defaults, yet.
    s = new State(fake_window('/moo/doc', '?cows=daisy', {}), {cows: "bob"});
    t.deepEqual(s.arg('cows'), 'daisy');
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cows=daisy']);
    s = new State(fake_window('/moo/doc', '?cows=daisy&cows=daisy', {}), {cows: "bob"});
    t.deepEqual(s.arg('cows'), 'daisydaisy');
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cows=daisy&cows=daisy']); //NB: We preserve array-ness from original URL

    // Define cows with array default, multiple arguments go in array
    s = new State(fake_window('/moo/doc', '?', {}), {cows: []});
    t.deepEqual(s.arg('cows'), []);
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc']);
    s = new State(fake_window('/moo/doc', '?cows=daisy', {}), {cows: []});
    t.deepEqual(s.arg('cows'), ['daisy']);
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cows=daisy']);
    s = new State(fake_window('/moo/doc', '?cows=daisy&cows=daisy', {}), {cows: []});
    t.deepEqual(s.arg('cows'), ['daisy', 'daisy']);
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cows=daisy&cows=daisy']);

    t.end();
});

test('update', function (t) {
    var s;

    s = new State(fake_window('/moo/doc', '?cows=daisy', {}));
    t.deepEqual(s.to_args(), [{}, '', '/moo/doc?cows=daisy']);
    s.update({ doc: '/oink' });
    t.deepEqual(s.to_args(), [{}, '', '/oink?cows=daisy']);
    s.update({ doc: '' }); // NB: empty doc value will cause it to stay the same
    t.deepEqual(s.to_args(), [{}, '', '/oink?cows=daisy']);

    s.update({ doc: '/oink', args: { pigs: 'george' } });
    t.deepEqual(s.to_args(),
        [{}, '', '/oink?cows=daisy&pigs=george'],
        "Adding arguments doesn't affect existing ones");

    s.update({ doc: '/oink', args: { pigs: 'gerald', duck: 'alfred' } });
    t.deepEqual(s.to_args(),
        [{}, '', '/oink?cows=daisy&duck=alfred&pigs=gerald'],
        "Can alter existing arguments");

    s.update({}, true);
    t.deepEqual(s.to_args(),
        [{}, '', '/oink?cows=daisy&duck=alfred&pigs=gerald'],
        "Flush without changes still leaves everything the same");

    s.update({ doc: '/oink', args: { duck: 'arnold' } }, true);
    t.deepEqual(s.to_args(),
        [{}, '', '/oink?duck=arnold'],
        "Flush removes unmentioned arguments");

    s.update({ url: '/bark?pigs=george&pigs=gerald' }, true);
    t.deepEqual(s.to_args(),
        [{}, '', '/bark?pigs=george&pigs=gerald'],
        "Can use url option instead to specify both doc/args");

    s.update({ state: { chicken: 5 }, args: { pigs: "george" }});
    t.deepEqual(s.to_args(),
        [{ chicken: 5 }, '', '/bark?pigs=george'],
        "Can add state arguments");

    s.update({ state: { chicken: 5, beef: 8 }, args: { pigs: "george" }});
    t.deepEqual(s.to_args(),
        [{ chicken: 5, beef: 8 }, '', '/bark?pigs=george'],
        "Can add in extra state arguments");

    s.update({ state: { beef: 3 }});
    t.deepEqual(s.to_args(),
        [{ chicken: 5, beef: 3 }, '', '/bark?pigs=george'],
        "Can modify state arguments");

    s.update({ state: { beef: 9 }}, true);
    t.deepEqual(s.to_args(),
        [{ beef: 9 }, '', '/bark?pigs=george'],
        "Flush removes any other state arguments");

    t.end();
});
