"use strict";

function to_query_string(params) {
    if (!params) {
        return "";
    }

    return Object.keys(params).map(function (k) {
        if (Array.isArray(params[k])) {
            return params[k].map(function (v) {
                return encodeURIComponent(k) + '=' + encodeURIComponent(v);
            }).join('&');
        }
        return encodeURIComponent(k) + '=' + encodeURIComponent(params[k]);
    }).join('&');
}

function parse_xml(str_promise, content_type) {
    var parser = new DOMParser();

    return str_promise.then(function (str) {
        var doc = parser.parseFromString(str, content_type);

        if (doc.documentElement.nodeName === "parsererror") {
            throw new Error("Cannot parse XML document: " + str);
        }
        return doc;
    });
}

function api_error_object(data) {
    var e = new Error("Failed to fetch data: " + data.error.message);

    console.log("API Debug info: " + JSON.stringify(data, null, 2));
    e.stack = data.error.stack || '';
    return e;
}

// Cache the X-Version-* headers returned by "/api/version"
var version_headers_promise = null;

module.exports.get = function (endpoint, qs) {
    var opts = {
        headers: {
            'Accept': 'application/json, application/xml',
        },
    };

    // Resolve (once) to the X-Version-* headers from /api/version, which we send on
    // every API request. X-Version-Corpora forms part of the NGINX cache key (see
    // client/install.sh), so a corpora re-import naturally busts the cache: new
    // clients fetch the new version and key their requests under it.
    //
    // /api/version is deliberately uncached in NGINX config
    if (!version_headers_promise) {
        version_headers_promise = window.fetch('/api/version', {
            headers: { 'Accept': 'application/json' },
        }).then(function (response) {
            var version_headers = {};

            response.headers.forEach(function (v, k) {
                if (k.toLowerCase().indexOf('x-version-') === 0) {
                    version_headers[k] = v;
                }
            });
            return version_headers;
        })['catch'](function () {
            // Fail open: behave as before, without any version headers
            return {};
        });
    }

    return version_headers_promise.then(function (version_headers) {
        // Send version headers to use as part of cache-busting key
        Object.keys(version_headers).forEach(function (k) {
            opts.headers[k] = version_headers[k];
        });
        return window.fetch('/api/' + endpoint + '?' + to_query_string(qs), opts);
    }).then(function (response) {
        if (response.status === 200) {
            if (response.headers.get('Content-Type') === 'application/json') {
                return response.json().then(function (data) {
                    // Check for any run-time error
                    if (data.error) {
                        throw api_error_object(data);
                    }
                    return data;
                });
            }
            if (response.headers.get('Content-Type') === 'application/xml') {
                return parse_xml(response.text(), response.headers.get('Content-Type'));
            }
            return { data: response.text() };
        }

        // It's an error, try and parse it, but throw an error in either case
        return response.json()['catch'](function (parse_err) {
            console.log("API Parse error: " + parse_err);

            throw new Error("Failed to fetch data: Could not communicate with server (" + response.statusText + ")");
        }).then(function (data) {
            throw api_error_object(data);
        });
    });
};
