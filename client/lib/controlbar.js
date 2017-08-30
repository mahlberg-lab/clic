"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var noUiSlider = require('nouislider');
global.jQuery = jQuery;  // So chosen-js can find it
var chosen = require('chosen-js');
var TagToggle = require('./tagtoggle.js');

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

function to_options_html(opts) {
    function escapeHtml(s) {
        // https://bugs.jquery.com/ticket/11773
        return (String(s)
            .replace(/&(?!\w+;)/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')); // "
    }

    return opts.map(function (t) {
        return "<option>" + escapeHtml(t) + "</option>";
    }).join("");
}

function ControlBar(control_bar) {
    this.control_bar = control_bar;

    control_bar.addEventListener('click', function (e) {
        function clickedOn(tagName, className) {
            var el = e.target;

            while (el.parentElement) {
                if (tagName && el.tagName === tagName) {
                    return true;
                }
                if (className && el.classList.contains(className)) {
                    return true;
                }
                el = el.parentElement;
            }
            return false;
        }

        if (clickedOn('LEGEND', null)) {
            e.preventDefault();
            e.stopPropagation();

            window.history.pushState({}, "", e.target.href);
            window.dispatchEvent(new window.CustomEvent('replacestate'));
            return;
        }

        if (clickedOn(null, 'handle')) {
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
    var self = this,
        tag_toggles_el = self.control_bar.querySelectorAll('fieldset:not([disabled]) .tag-toggles')[0],
        page_state = window.history.state || {};

    // Enable the fieldset for the page
    Array.prototype.forEach.call(self.control_bar.elements, function (el, i) {
        if (el.tagName === 'FIELDSET') {
            el.disabled = ('/' + el.name !== page_opts.doc);
        }
    });

    // TODO: Hard-code the tag state for now
    if (!page_state.tag_columns) {
        page_state.tag_columns = {
            'Pablo-BP-CONC': {}, //TODO: Hardcoding for now
            'MB-BP-CONC': {},
        };
    }
    window.history.replaceState(page_state, "", "");

    // Recreate tag toggles
    tag_toggles_el.innerHTML = '';
    this.tag_toggles = Object.keys(page_state.tag_columns).map(function (t) {
        var toggle = new TagToggle(t);

        toggle.onupdate = function (tag_state) {
            var i, new_state = window.history.state;

            for (i = 0; i < self.table_selection.length; i++) {
                new_state.tag_columns[t][self.table_selection[i].DT_RowId] = tag_state === 'yes' ? true : false;
            }

            window.history.replaceState(new_state, "", "");
            window.dispatchEvent(new window.CustomEvent('replacestate'));
        };

        tag_toggles_el.appendChild(toggle.dom());
        return toggle;
    });

    // Make sure we consider existing options valid
    this.control_bar.elements['kwic-terms'].innerHTML = to_options_html([page_opts['kwic-terms']]);

    this.control_bar.elements['conc-subset'].value = page_opts['conc-subset'] || "all";
    this.control_bar.elements['conc-q'].value = page_opts['conc-q'] || "";
    this.control_bar.elements['conc-type'].value = page_opts['conc-type'] || "whole";
    this.control_bar.elements['kwic-span'].value = page_opts['kwic-span'] || "-5:5";
    this.control_bar.elements['kwic-terms'].value = page_opts['kwic-terms'] || [];

    // Tell all the chosen's that values are altered
    Array.prototype.forEach.call(this.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).trigger("chosen:updated");
    });
};

// Apply results of any search into data
ControlBar.prototype.new_data = function new_data(data) {
    var prevVal, el;

    if (data.allWords) {
        // Make sure values already selected stay selectable
        el = this.control_bar.elements['kwic-terms'];
        prevVal = jQuery(el).val() || [];
        prevVal.map(function (t, i) {
            data.allWords[t] = true;
        });

        el.innerHTML = to_options_html(Object.keys(data.allWords));
        el.value = prevVal;
        jQuery(el).trigger("chosen:updated");
    }

    this.control_bar.querySelectorAll("#kwic-total-matches")[0].innerText = (data.totalMatches || 0);
};

// New rows selected, process selection-based widgets
ControlBar.prototype.new_selection = function new_selection(data) {
    this.table_selection = data;

    // All toggles update themselves
    this.tag_toggles.forEach(function (toggle) {
        toggle.update(data);
    });
};

module.exports = ControlBar;
