"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, DOMParser */

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

module.exports.get = function (endpoint, qs) {
    var opts = {
        headers: {
            'Accept': 'application/json, application/xml',
        },
    };

    return window.fetch('/api/' + endpoint + '?' + to_query_string(qs), opts).then(function (response) {
        if (response.status === 200) {
            if (response.headers.get('Content-Type') === 'application/json') {
                return response.json();
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
            var e = new Error("Failed to fetch data: " + data.message);

            console.log("API Debug info: " + JSON.stringify(data, null, 2));
            e.stack = data.stack || '';
            throw e;
        });
    });
};
