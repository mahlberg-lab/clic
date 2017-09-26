"use strict";
/*jslint todo: true, regexp: true, nomen: true, browser: true */
var test = require('tape');

var concordance_utils = require('../lib/concordance_utils.js');

test('renderTokenArray:display', function (t) {
    var data;

    data = ['and', ' ', 'the', ' ', 'hammerhead', '-', 'sh<a>rk', ' ', 'said', ',', ' ', '"', [0, 2, 4, 6, 8]];
    data.matches = [];
    data.kwicSpan = {};

    // Words are marks, space is span, HTML is quoted
    t.equal(concordance_utils.renderTokenArray(data, 'display'),
            '<div class="l">' +
            '<mark>and</mark>' +
            '<span> </span>' +
            '<mark>the</mark>' +
            '<span> </span>' +
            '<mark>hammerhead</mark>' +
            '<span>-</span>' +
            '<mark>sh&lt;a&gt;rk</mark>' +
            '<span> </span>' +
            '<mark>said</mark>' +
            '<span>,</span>' +
            '<span> </span>' +
            '<span>&quot;</span>' +
            '</div>');

    // Reverse mode just changes the div class
    data.kwicSpan = { reverse: true };
    t.equal(concordance_utils.renderTokenArray(data, 'display'),
            '<div class="r">' +
            '<mark>and</mark>' +
            '<span> </span>' +
            '<mark>the</mark>' +
            '<span> </span>' +
            '<mark>hammerhead</mark>' +
            '<span>-</span>' +
            '<mark>sh&lt;a&gt;rk</mark>' +
            '<span> </span>' +
            '<mark>said</mark>' +
            '<span>,</span>' +
            '<span> </span>' +
            '<span>&quot;</span>' +
            '</div>');

    // Matches get added to class
    data.matches = [1, 3];
    t.equal(concordance_utils.renderTokenArray(data, 'display').replace(/>.*/, ">"), '<div class="r m1 m3">');
    data.kwicSpan = {};
    t.equal(concordance_utils.renderTokenArray(data, 'display').replace(/>.*/, ">"), '<div class="l m1 m3">');


    t.end();
});
