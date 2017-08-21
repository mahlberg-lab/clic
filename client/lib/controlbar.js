"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */

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
}

if (window) {
    document.addEventListener('DOMContentLoaded', function (e) {
        controlbar_init(document.getElementById('control-bar'));
    });
}
