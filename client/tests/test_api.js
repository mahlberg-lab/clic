"use strict";
var test = require('tape');

// A minimal fetch Response for a JSON body, as consumed by lib/api.js
// (extra_headers) keys should be lower-case, as fetch's Headers would be
function json_response(body, extra_headers) {
    var headers = Object.assign({ 'content-type': 'application/json' }, extra_headers || {});

    return {
        status: 200,
        headers: {
            get: function (k) {
                return headers[k.toLowerCase()] || null;
            },
            forEach: function (fn) {
                Object.keys(headers).forEach(function (k) {
                    fn(headers[k], k);
                });
            },
        },
        json: function () { return Promise.resolve(body); },
        text: function () { return Promise.resolve(JSON.stringify(body)); },
    };
}

// Fresh copy of lib/api.js, so its memoised version-headers promise is reset
function fresh_api() {
    delete require.cache[require.resolve('../lib/api.js')];
    return require('../lib/api.js');
}

// Install a fake window.fetch driven by (responder), recording every call.
// Returns {calls: [...], restore: fn} so we leave global.window as we found it.
function install_fetch(responder) {
    var calls = [];
    var prev_window = global.window;

    global.window = { fetch: function (url, opts) {
        calls.push({ url: url, opts: opts || {} });
        return Promise.resolve(responder(url, opts));
    } };

    return {
        calls: calls,
        restore: function () { global.window = prev_window; },
    };
}

test('api.get adds X-Version-* headers from the uncached /api/version', function (t) {
    var fetch = install_fetch(function (url) {
        if (url === '/api/version') {
            return json_response({}, {
                'x-version-corpora': 'master:abc123',
                'x-version-clic': '2.3.0',
                'x-generated': '2026-10-03T00:00:00',
            });
        }
        return json_response({ corpora: [], version: { corpora: 'master:abc123' } });
    });

    fresh_api().get('corpora', { subset: 'quote' }).then(function (data) {
        t.deepEqual(data.corpora, [], 'Returns the parsed response body');

        t.equal(fetch.calls[0].url, '/api/version',
            'First request is to the uncached /api/version endpoint');
        t.notOk(
            fetch.calls[0].opts.headers['x-version-corpora'],
            'The /api/version request itself carries no data-version header'
        );

        t.equal(fetch.calls[1].url, '/api/corpora?subset=quote',
            'Then requests the actual endpoint');
        t.equal(
            fetch.calls[1].opts.headers['x-version-corpora'], 'master:abc123',
            'The endpoint request carries the current corpora version as a cache-busting header'
        );
        t.equal(
            fetch.calls[1].opts.headers['x-version-clic'], '2.3.0',
            'The endpoint request carries all other X-Version-* headers'
        );
        t.notOk(
            fetch.calls[1].opts.headers['x-generated'],
            'Non-version headers are not copied'
        );
    })['catch'](function (err) {
        t.fail(err);
    }).then(function () {
        fetch.restore();
        t.end();
    });
});

test('api.get fetches /api/version once and reuses the token', function (t) {
    var fetch = install_fetch(function () {
        return json_response({}, { 'x-version-corpora': 'v2' });
    });
    var api = fresh_api();

    api.get('corpora').then(function () {
        return api.get('corpora/headlines');
    }).then(function () {
        var version_calls = fetch.calls.filter(function (c) {
            return c.url === '/api/version';
        });
        t.equal(version_calls.length, 1,
            'Only one /api/version request is made for multiple api.get() calls');

        var last = fetch.calls[fetch.calls.length - 1];
        t.equal(last.opts.headers['x-version-corpora'], 'v2',
            'Subsequent requests reuse the cached version headers');
    })['catch'](function (err) {
        t.fail(err);
    }).then(function () {
        fetch.restore();
        t.end();
    });
});

test('api.get fails open without version headers if /api/version is unavailable', function (t) {
    var fetch = install_fetch(function (url) {
        if (url === '/api/version') {
            return Promise.reject(new Error('network down'));
        }
        return json_response({ corpora: [], version: {} });
    });

    fresh_api().get('corpora').then(function (data) {
        t.deepEqual(data.corpora, [], 'Request still succeeds');
        t.notOk(fetch.calls[1].opts.headers['x-version-corpora'],
            'Sends no version header rather than failing');
    })['catch'](function (err) {
        t.fail(err);
    }).then(function () {
        fetch.restore();
        t.end();
    });
});
