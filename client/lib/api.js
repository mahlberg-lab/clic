"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */

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

module.exports.get = function (endpoint, qs) {
    return window.fetch('/api/' + endpoint + '?' + to_query_string(qs)).then(function (response) {
        if (response.status === 200) {
            return response.json();
        }

        // It's an error, try and parse it, but throw an error in either case
        return response.json()['catch'](function (parse_err) {
            console.log("API Parse error: " + parse_err);

            throw new Error("Failed to fetch data: Could not communicate with server (" + response.statusText + ")");
        }).then(function (data) {
            console.log("API Debug info: " + JSON.stringify(data, null, 2));
            throw new Error("API failed to communicate with server: " + data.message);
        });
    });
};
