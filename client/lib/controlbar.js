"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var noUiSlider = require('nouislider');
global.jQuery = jQuery;  // So chosen-js can find it
var chosen = require('chosen-js');
var api = require('./api.js');
var PanelTagColumns = require('./panel_tagcolumn.js');
var TagToggle = require('./tagtoggle.js');
var filesystem = require('./filesystem.js');

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
    'kwic-int-start': {
        start: 3,
        range: {min: 0, max: 10},
        step: 1,
        pips: {
            mode: 'steps',
            density: 10,
            filter: function (v, t) { return 2; },
        },
        connect: [true, false],
    },
    'kwic-int-end': {
        start: 3,
        range: {min: 0, max: 10},
        step: 1,
        direction: "rtl",
        pips: {
            mode: 'steps',
            density: 10,
            filter: function (v, t) { return 2; },
        },
        connect: [true, false],
    },
};

var state_defaults = {
    'corpora': [],
    'conc-subset': 'all',
    'conc-q': '',
    'conc-type': 'whole',
    'subset-subset': 'shortsus',
    'table-filter': '',
    'table-metadata': '',
    'kwic-span': '-5:5',
    'kwic-dir': 'start',
    'kwic-int-start': '3',
    'kwic-int-end': '3',
    'kwic-terms': [],
    'refcorpora': [],
    'subset': 'all',
    'refsubset': 'all',
    'clusterlength': 1,
    'pvalue': 0.0001,
};

function to_options_html(opts, group_label) {
    var out;

    function escapeHtml(s) {
        // https://bugs.jquery.com/ticket/11773
        return (String(s)
            .replace(/&(?!\w+;)/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')); // "
    }

    out = opts.map(function (t) {
        if (t.id && t.title) {
            return '<option value="' + escapeHtml(t.id) + '">' + escapeHtml(t.title) + "</option>";
        }
        return "<option>" + escapeHtml(t) + "</option>";
    }).join("");

    if (group_label) {
        out = '<optgroup label="' + escapeHtml(group_label) + '">' + out + '</optgroup>';
    }
    return out;
}

/** Was the click event somewhere on an element with (tagName) or (className)? */
function clickedOn(e, tagName, className) {
    var el = e.target;

    while (el) {
        if (!tagName || el.tagName === tagName) {
            if (!className || el.classList.contains(className)) {
                return true;
            }
        }
        el = el.parentElement;
    }
    return false;
}

function ControlBar(control_bar) {
    var self = this;

    this.control_bar = control_bar;
    this.form = control_bar.getElementsByTagName('FORM')[0];

    control_bar.addEventListener('click', function (e) {
        if (clickedOn(e, 'LEGEND', null)) {
            e.preventDefault();
            e.stopPropagation();

            self.page_state.new({
                doc: e.target.href,
                args: { corpora: self.page_state.arg('corpora', state_defaults.corpora) },
                state: {},
            }, 'push');
            return;
        }

        if (clickedOn(e, null, 'handle')) {
            control_bar.classList.toggle('in');
            return;
        }

        if (clickedOn(e, 'A', 'action')) {
            e.preventDefault();
            e.stopPropagation();

            if (clickedOn(e, 'A', 'clear')) {
                self.page_state.new({ args: {}, state: {}, }, 'push');
            } else if (clickedOn(e, 'A', 'save')) {
                filesystem.save(filesystem.format_dt(jQuery('#content table.dataTable').DataTable()));
            } else {
                throw new Error("Unknown action '" + e.target.className + "'");
            }

            return;
        }

        if (clickedOn(e, null, 'toggle-panel')) {
            e.preventDefault();
            e.stopPropagation();

            document.getElementById('panel-' + e.target.getAttribute('data-panel')).classList.toggle('in');

            return;
        }
    });

    control_bar.addEventListener('keypress', function (e) {
        if (e.keyCode === 13) {
            // Don't submit on enter, change instead
            e.preventDefault();
            if (e.target.tagName === "INPUT") {
                e.target.dispatchEvent(new window.Event('change', {"bubbles": true}));
            }
        }
    });

    self.form.addEventListener('change', function (e) {
        if (this.change_timeout) {
            window.clearTimeout(this.change_timeout);
        }
        this.change_timeout = window.setTimeout(function () {
            var new_search = {};

            jQuery(self.form).serializeArray().forEach(function (f) {
                if (Array.isArray(new_search[f.name])) {
                    new_search[f.name].push(f.value);
                } else if (new_search.hasOwnProperty(f.name)) {
                    new_search[f.name] = [new_search[f.name], f.value];
                } else {
                    new_search[f.name] = [f.value];
                }
            });

            // Unchecked checkboxes should be false
            Array.prototype.forEach.call(control_bar.querySelectorAll('fieldset:not([disabled]) input[type=checkbox]:not(:checked)'), function (el, i) {
                new_search[el.name] = [""];
            });

            // Empty select boxes should be empty
            Array.prototype.forEach.call(control_bar.querySelectorAll('fieldset:not([disabled]) select[multiple]'), function (el, i) {
                new_search[el.name] = jQuery(el).val();
            });

            self.page_state.update({args: new_search});
        }, 300);
    });

    if (window.screen.availWidth > 960) {
        this.control_bar.classList.add('in');
    }

    Array.prototype.forEach.call(this.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).chosen().change(function (e) {
            // Chosen's change event isn't bubbling to the form, do it ourselves.
            self.form.dispatchEvent(new window.Event('change', {"bubbles": true}));
        });
    });

    // Turn "nouislider"-type inputs into an actual nouislider
    Array.prototype.forEach.call(this.control_bar.querySelectorAll('input[type=nouislider]'), function (el, i) {
        var slider_div = document.createElement('DIV');

        el.style.display = 'none';
        el.parentNode.insertBefore(slider_div, el.nextSibling);

        noUiSlider.create(slider_div, noUiSlider_opts[el.name]);

        el.addEventListener('change', function (e) {
            var old_value = slider_div.noUiSlider.get();

            if (Array.isArray(old_value)) {
                old_value = old_value.join(':');
            }
            if (this.value !== old_value) {
                slider_div.noUiSlider.set(this.value.split(':'));
            }
        });

        slider_div.noUiSlider.on('update', function (values) {
            if (!el.value) {
                // Initial update, don't trigger anything
                el.value = values.join(':');
            } else if (el.value !== values.join(':')) {
                el.value = values.join(':');
                el.dispatchEvent(new window.Event('change', {"bubbles": true}));
            }
        });
    });

    // Init extra panels
    this.panels = {
        'tag-columns': new PanelTagColumns(window.document.getElementById('panel-tag-columns')),
    };
}

// Refresh controls based on page_state
ControlBar.prototype.reload = function reload(page_state) {
    var self = this;

    self.page_state = page_state; // Store this for events

    return Promise.resolve().then(function () {
        return self.corpora || api.get('corpora');
    }).then(function (corpora) {
        var tag_toggles_el;

        self.corpora = corpora;

        // Enable the fieldset for the page
        Array.prototype.forEach.call(self.form.elements, function (el, i) {
            if (el.tagName === 'FIELDSET') {
                el.disabled = ('/' + el.name !== page_state.doc());
            }
        });

        // Recreate tag toggles
        tag_toggles_el = self.control_bar.querySelectorAll('fieldset:not([disabled]) .tag-toggles')[0];
        if (tag_toggles_el) {
            tag_toggles_el.innerHTML = '';
            self.tag_toggles = Object.keys(page_state.state('tag_columns', {})).map(function (t) {
                var toggle = new TagToggle(t);

                toggle.onupdate = function (tag_state) {
                    var i, new_columns = JSON.parse(JSON.stringify(page_state.state('tag_columns', {})));

                    for (i = 0; i < self.table_selection.length; i++) {
                        if (tag_state === 'yes') {
                            new_columns[t][self.table_selection[i].DT_RowId] = true;
                        } else {
                            delete new_columns[t][self.table_selection[i].DT_RowId];
                        }
                    }

                    page_state.update({ state: { tag_columns: new_columns }});
                };

                tag_toggles_el.appendChild(toggle.dom());
                if (self.initial_selection) {
                    toggle.update(self.initial_selection);
                }
                return toggle;
            });
            self.initial_selection = null;
        }

        // Hide the KWIC direction slider we're not using
        if (page_state.arg('kwic-dir', 'start') === 'start') {
            self.form.elements['kwic-int-start'].disabled = false;
            self.form.elements['kwic-int-end'].disabled = true;
        } else {
            self.form.elements['kwic-int-start'].disabled = true;
            self.form.elements['kwic-int-end'].disabled = false;
        }

        // Set values from page options, or defaults
        Array.prototype.forEach.call(self.form.elements, function (el_or_array) {
            Array.prototype.forEach.call(Array.isArray(el_or_array) ? el_or_array : [el_or_array], function (el) {
                if (el.tagName === 'FIELDSET' || !state_defaults.hasOwnProperty(el.name)) {
                    Math.floor(0);
                } else if (el.tagName === 'INPUT' && el.type === "checkbox") {
                    el.checked = !!page_state.arg(el.name, state_defaults[el.name]);
                } else if (el.tagName === 'INPUT' && el.type === "radio") {
                    el.checked = page_state.arg(el.name, state_defaults[el.name]) === el.value;
                } else if (el.tagName === 'INPUT' && el.getAttribute('type') === "nouislider") {
                    // nouisliders need to be told that something happened
                    el.value = page_state.arg(el.name, state_defaults[el.name]);
                    el.dispatchEvent(new window.Event('change', {"bubbles": false}));
                } else if (el.tagName === 'SELECT') {
                    if (el.name === "kwic-terms") {
                        // Make sure we consider existing options valid
                        el.innerHTML = to_options_html(page_state.arg('kwic-terms', []));
                    } else if (el.name === "corpora" || el.name === "refcorpora") {
                        // Populate corpora dropdowns
                        el.innerHTML = to_options_html(corpora.corpora, 'Entire corpora') + corpora.corpora.map(function (c) {
                            return to_options_html(c.children, c.title);
                        }).join("");
                    }
                    jQuery(el).val(page_state.arg(el.name, state_defaults[el.name]));
                } else {
                    el.value = page_state.arg(el.name, state_defaults[el.name]);
                }
            });
        });

        // Tell all the chosen's that values are altered
        Array.prototype.forEach.call(self.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
            jQuery(el).trigger("chosen:updated");
        });
    }).then(function (data) {
        return Promise.all(Object.values(self.panels).map(function (p) { p.reload(page_state); })).then(function () {
            return data;
        });
    });
};

// Apply results of any search into data
ControlBar.prototype.new_data = function new_data(data) {
    if (data.allWords) {
        // Make sure KWIC term values already selected stay selectable
        Array.prototype.forEach.call(this.form.elements['kwic-terms'], function (el) {
            var prevVal = jQuery(el).val() || [];

            if (el.parentElement.parentElement.disabled) {
                // The fieldset is disabled, so don't bother
                return;
            }

            prevVal.map(function (t) {
                data.allWords[t] = true;
            });

            el.innerHTML = to_options_html(Object.keys(data.allWords || {}));
            jQuery(el).val(prevVal);
            jQuery(el).trigger("chosen:updated");
        });
    }

    this.control_bar.querySelectorAll("#kwic-total-matches")[0].innerText = (data.totalMatches || 0);
};

// New rows selected, process selection-based widgets
ControlBar.prototype.new_selection = function new_selection(data) {
    this.table_selection = data;

    if (!this.tag_toggles) {
        // Store selection until we're ready
        this.initial_selection = data;
    } else {
        // Tell the toggle to update itself
        this.tag_toggles.forEach(function (toggle) {
            toggle.update(data);
        });
    }
};

module.exports = ControlBar;
