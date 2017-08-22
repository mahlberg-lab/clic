"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */
require('./polyfill.js');
var controlbar = require('./controlbar.js');

function page_load(e) {
    controlbar.init(document.getElementById('control-bar'));
}

if (window) {
    document.addEventListener('DOMContentLoaded', page_load);
    window.addEventListener('popstate', page_load);
}
