"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */

function getCookie(name) {
    var c = "; " + document.cookie.split("; " + name + "=");
    if (c.length === 2) {
        return c.pop().split(";").shift();
    }
}


function x() {
    document.cookie = 'testCookie=testValue; expires=Fri, 31 Dec 2024 23:59:59 GMT';
    console.log(getCookie('test'));
}

module.exports = x;
