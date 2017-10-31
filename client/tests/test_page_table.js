"use strict";
/*jslint plusplus: true */
/*global Promise */
var test = require('tape');
var proxyquire =  require('proxyquire');

var req_count = 0;

global.window = { setTimeout: setTimeout };
var PageTable = proxyquire('../lib/page_table.js', {
    './api.js': {
        get: function (endpoint, qs) {
            return Promise.resolve({
                count: req_count++,
                endpoint: endpoint,
                qs: qs,
            });
        },
    },
});

test('cached_get', function (t) {
    var content_el = { children: [] },
        pt = new PageTable(content_el);

    return Promise.resolve(true).then(function () {
        // We should get data back
        return pt.cached_get('a', {moo: "yes"}).then(function (data) {
            t.deepEqual(data, {
                count: 0,
                endpoint: 'a',
                qs: {moo: 'yes'},
            });
        });

    }).then(function () {
        // Same request gets the same data back, even the count
        return pt.cached_get('a', {moo: "yes"}).then(function (data) {
            t.deepEqual(data, {
                count: 0,
                endpoint: 'a',
                qs: {moo: 'yes'},
            });
        });

    }).then(function () {
        // Altering the request ups the count
        return pt.cached_get('a', {moo: "no"}).then(function (data) {
            t.deepEqual(data, {
                count: 1,
                endpoint: 'a',
                qs: {moo: 'no'},
            });
        });

    }).then(function () {
        // Altering the request ups the count
        return pt.cached_get('a', {moo: "no", oink: [1, 2, 3]}).then(function (data) {
            t.deepEqual(data, {
                count: 2,
                endpoint: 'a',
                qs: {moo: 'no', oink: [1, 2, 3]},
            });
        });

    }).then(function () {
        // Altering the request ups the count
        return pt.cached_get('a', {moo: "no", oink: [1, 2, 4]}).then(function (data) {
            t.deepEqual(data, {
                count: 3,
                endpoint: 'a',
                qs: {moo: 'no', oink: [1, 2, 4]},
            });
        });

    }).then(function () {
        // Altering the request ups the count
        return pt.cached_get('b', {moo: "no", oink: [1, 2, 4]}).then(function (data) {
            t.deepEqual(data, {
                count: 4,
                endpoint: 'b',
                qs: {moo: 'no', oink: [1, 2, 4]},
            });
        });

    }).then(function () {
        t.end();
    }).catch(function (err) {
        setTimeout(function () { throw err; }, 0);
        t.end();
    });
});
