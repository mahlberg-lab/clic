"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */

function getCookie(name) {

    // Convert cookies string to list
    var c_list = document.cookie.split("; "),
        i = 0,
        c,
        c_name,
        c_value;
    // Loop through cookies list to find a match
    for (i = 0; i < c_list.length; i++) {
        // Find cookie
        c = c_list[i].split('=');
        c_name = c[0];
        c_value = c[1];
        // Return cookie value if cookie name matches
        if (c_name === name) {
            return c_value;
        }
    }
    // If no cookie found with given name, return null
    return null;
}


function x() {
    document.cookie = 'testCookie=testValue; expires=Fri, 31 Dec 2024 23:59:59 GMT';
    console.log(getCookie('testCookie'));
}

module.exports = x;
