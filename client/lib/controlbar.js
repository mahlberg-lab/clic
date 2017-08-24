"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var noUiSlider = require('nouislider');
global.jQuery = jQuery;  // So chosen-js can find it
var chosen = require('chosen-js');

var noUiSlider_opts = {
    'kwic-span': {
        start: [-5, 5],
        range: {min: -5, "10%": -4, "20%": -3, "30%": -2, "40%": -1,
                "60%":  1, "70%":  2, "80%":  3, "90%":  4, max:  5},
        snap: true,
        pips: {
            mode: 'steps',
            density: 10,
            filter: function (v, t) { return v === 0 ? 1 : 2; },
            format: { to: function (v) { return (v > 0 ? 'R' : v < 0 ? 'L' : '') + Math.abs(v); } },
        },
        format: {
            to: function (value) { return value; },
            from: function (value) { return value.replace('L', '-').replace('R', ''); },
        },
        connect: true
    },
};

function ControlBar(control_bar) {
    this.control_bar = control_bar;

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

    control_bar.addEventListener('change', function (e) {
        if (this.change_timeout) {
            window.clearTimeout(this.change_timeout);
        }
        this.change_timeout = window.setTimeout(function () {
            var new_search = "?" + jQuery(control_bar).serialize();

            if (document.location.pathname === new_search) {
                return;
            }

            //TODO: If page != current page, then add an entry - or just make them links?
            window.history.replaceState(window.history.state, "", new_search);
            window.dispatchEvent(new window.CustomEvent('replacestate'));
        }, 300);
    });

    if (window.screen.availWidth > 960) {
        this.control_bar.classList.add('in');
    }

    Array.prototype.forEach.call(this.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).chosen().change(function (e) {
            // Chosen's change event isn't bubbling to the form, do it ourselves.
            control_bar.dispatchEvent(new window.Event('change', {"bubbles": true}));
        });
    });

    // Turn "nouislider"-type inputs into an actual nouislider
    Array.prototype.forEach.call(this.control_bar.querySelectorAll('input[type=nouislider]'), function (el, i) {
        var slider_div = document.createElement('DIV');

        el.style.display = 'none';
        el.parentNode.insertBefore(slider_div, el);

        noUiSlider.create(slider_div, noUiSlider_opts[el.name]);

        el.addEventListener('change', function (e) {
            if (this.value !== slider_div.noUiSlider.get().join(':')) {
                slider_div.noUiSlider.set(this.value.split(':'));
            }
        });

        slider_div.noUiSlider.on('update', function (values) {
            if (el.value !== values.join(':')) {
                el.value = values.join(':');
                el.dispatchEvent(new window.Event('change', {"bubbles": true}));
            }
        });
    });
}

// Refresh controls based on page_opts
ControlBar.prototype.reload = function reload(page_opts) {
    this.control_bar.elements['conc-subset'].value = page_opts['conc-subset'] || "all";
    this.control_bar.elements['conc-q'].value = page_opts['conc-q'] || "";
    this.control_bar.elements['conc-type'].value = page_opts['conc-type'] || "whole";
    this.control_bar.elements['kwic-span'].value = page_opts['kwic-span'] || "-5:5";
    this.control_bar.elements['kwic-terms'].value = page_opts['kwic-terms'];

    // Tell all the chosen's that values are altered
    Array.prototype.forEach.call(this.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).trigger("chosen:updated");
    });
};

// Apply results of any search into data
ControlBar.prototype.new_data = function new_data(data) {
    var prevVal, el;

    function escapeHtml(s) {
        // https://bugs.jquery.com/ticket/11773
        return (String(s)
            .replace(/&(?!\w+;)/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')); // "
    }

    if (data.allWords) {
        // Make sure values already selected stay selectable
        el = this.control_bar.elements['kwic-terms'];
        prevVal = jQuery(el).val() || [];
        prevVal.map(function (t, i) {
            data.allWords[t] = true;
        });

        jQuery(el).html(Object.keys(data.allWords).sort().map(function (t) {
            return "<option>" + escapeHtml(t) + "</option>";
        }).join("")).val(prevVal).trigger("chosen:updated");
    }

    this.control_bar.querySelectorAll("#kwic-total-matches")[0].innerText = (data.totalMatches || 0);
};

module.exports = ControlBar;
