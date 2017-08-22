"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
global.jQuery = jQuery;  // So chosen-js can find it
var chosen = require('chosen-js');

function controlbar_init(control_bar) {
    control_bar.addEventListener('click', function (e) {
        var i;

        function clickedOn(className) {
            var el = e.target;

            while (el.parentElement) {
                if (el.classList.contains(className)) {
                    return true;
                }
                el = el.parentElement;
            }
            return false;
        }

        if (e.target.tagName === 'LEGEND') {
            for (i = 0; i < control_bar.elements.length; i++) {
                if (control_bar.elements[i].tagName === 'FIELDSET') {
                    control_bar.elements[i].disabled = (control_bar.elements[i].name !== e.target.parentElement.name);
                }
            }
            control_bar.dispatchEvent(new window.Event('change'));
            return;
        }

        if (clickedOn('handle')) {
            control_bar.classList.toggle('in');
            return;
        }
    });

    if (window.screen.availWidth > 960) {
        control_bar.classList.add('in');
    }

    Array.prototype.forEach.call(control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).chosen();
    });
}

if (window) {
    document.addEventListener('DOMContentLoaded', function (e) {
        controlbar_init(document.getElementById('control-bar'));
    });
}
