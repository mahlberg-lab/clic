"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
global.jQuery = jQuery;  // So chosen-js can find it
var chosen = require('chosen-js');

function controlbar_init(control_bar) {
    control_bar.addEventListener('click', function (e) {
        var i;
        if (e.target.tagName === 'LEGEND') {
            for (i = 0; i < control_bar.elements.length; i++) {
                if (control_bar.elements[i].tagName === 'FIELDSET') {
                    control_bar.elements[i].disabled = (control_bar.elements[i].name !== e.target.parentElement.name);
                }
            }
        }
    });

    Array.prototype.forEach.call(control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).chosen();
    });
}

if (window) {
    document.addEventListener('DOMContentLoaded', function (e) {
        controlbar_init(document.getElementById('control-bar'));
    });
}
