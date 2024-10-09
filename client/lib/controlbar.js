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
var concordance_utils = require('./concordance_utils.js');

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
        connect: true
    },
    'kwic-int-start': {
        start: 3,
        range: {min: 1, max: 10},
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
        range: {min: 1, max: 10},
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
        if (t.hasOwnProperty('id') && t.hasOwnProperty('title')) {
            if (t.id === null) {
                // A null ID means we're trying to hide this option (read: all authors)
                return '';
            }
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

/**
  * Given a string 'from:to,from_1:to_1', swap page state around and return URL
  */
function swaps_to_url(page_state, arg_swaps) {
    var detail = { args: {} };

    arg_swaps.split(",").map(function (str) {
        var to_swap = str.split(":");

        if (to_swap.length === 2) {
            detail.args[to_swap[0]] = page_state.arg(to_swap[1]);
            detail.args[to_swap[1]] = page_state.arg(to_swap[0]);
        }
    });

    return page_state.clone(detail).to_url();
}

function ControlBar(control_bar) {
    var self = this;

    this.control_bar = control_bar;

    window.document.querySelectorAll('nav + .handle')[0].addEventListener('click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        control_bar.classList.toggle('in');
    });

    control_bar.addEventListener('click', function (e) {
        if (clickedOn(e, 'LEGEND', null)) {
            e.preventDefault();
            e.stopPropagation();

            window.dispatchEvent(new window.CustomEvent('state_new', { detail: {
                doc: e.target.pathname,
                args: { corpora: self.page_state ? self.page_state.arg('corpora') : [] },
                state: {},
            }}));

            // Wait until animation has finished, then scroll viewport
            window.setTimeout(function () {
                e.target.scrollIntoView({ behavior: "smooth" });
            }, 300);
            return;
        }

        if (clickedOn(e, 'A', 'action')) {
            e.preventDefault();
            e.stopPropagation();

            if (clickedOn(e, 'A', 'clear')) {
                window.dispatchEvent(new window.CustomEvent('state_new', { detail: { args: {}, state: {}, }}));
            } else if (clickedOn(e, 'A', 'save')) {
                if (window.dt) {
                    filesystem.save(filesystem.format_dt(window.dt));
                }
            } else if (clickedOn(e, 'A', 'load')) {
                self.file_loader.trigger('load');
            } else if (clickedOn(e, 'A', 'merge')) {
                self.file_loader.trigger('merge');
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
                e.target.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            }
        }
    });

    self.control_bar.addEventListener('change', function (e) {
        if (this.change_timeout) {
            window.clearTimeout(this.change_timeout);
        }
        this.change_timeout = window.setTimeout(function () {
            var new_search = {},
                form = control_bar.querySelector('fieldset.current form');

            // Unchecked checkboxes should be emptied if not mentioned
            Array.prototype.forEach.call(control_bar.querySelectorAll('fieldset.current input[type=checkbox]:not(:checked)'), function (el, i) {
                new_search[el.name] = [];
            });

            jQuery(form).serializeArray().forEach(function (f) {
                if (Array.isArray(new_search[f.name])) {
                    new_search[f.name].push(f.value);
                } else if (new_search.hasOwnProperty(f.name)) {
                    new_search[f.name] = [new_search[f.name], f.value];
                } else {
                    new_search[f.name] = [f.value];
                }
            });

            // Empty select boxes should be empty
            Array.prototype.forEach.call(control_bar.querySelectorAll('fieldset.current select[multiple]'), function (el, i) {
                new_search[el.name] = jQuery(el).val();
            });

            window.dispatchEvent(new window.CustomEvent('state_update', { detail: {args: new_search}}));
        }, 300);
    });

    if (window.screen.availWidth > 960) {
        this.control_bar.classList.add('in');
    }

    Array.prototype.forEach.call(this.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
        jQuery(el).chosen({ width: '100%', search_contains: true }).change(function (e) {
            // Chosen's change event isn't bubbling to the form, do it ourselves.
            self.control_bar.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
        });
    });

    // Turn "nouislider"-type inputs into an actual nouislider
    Array.prototype.forEach.call(this.control_bar.querySelectorAll('input[type=nouislider]'), function (el, i) {
        el.slider_div = document.createElement('DIV');
        el.style.display = 'none';
        el.parentNode.insertBefore(el.slider_div, el.nextSibling);

        noUiSlider.create(el.slider_div, noUiSlider_opts[el.name]);

        el.slider_div.noUiSlider.on('update', function (values) {
            var val_string = values.map(Math.round).join(':');

            if (el.value !== val_string) {
                el.value = val_string;
                el.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            }
        });
    });

    // Init extra panels
    this.panels = {};
    if (window.document.getElementById('panel-tag-columns')) {
        this.panels['tag-columns'] = new PanelTagColumns(window.document.getElementById('panel-tag-columns'));
    }

    // Add file loader
    this.file_loader = filesystem.file_loader(document, function (file, load_mode) {
        var new_state = filesystem.file_to_state(file);

        if (load_mode === 'merge') {
            new_state.state = concordance_utils.merge_tags({
                tag_columns: self.page_state.state('tag_columns'),
                tag_column_order: self.page_state.state('tag_column_order'),
            }, new_state.state);
        }

        window.dispatchEvent(new window.CustomEvent('state_new', { detail: new_state }));
    });
}

// Refresh controls based on page_state
ControlBar.prototype.reload = function reload(page_state) {
    var self = this;

    self.page_state = page_state; // Store this for events

    return Promise.resolve().then(function () {
        return self.corpora || api.get('corpora');
    }).then(function (corpora) {
        var tag_toggles_el, elements;

        self.corpora = corpora;

        // Enable the fieldset for the page
        Array.prototype.forEach.call(self.control_bar.querySelectorAll('fieldset'), function (el, i) {
            el.classList.toggle('current', '/' + el.getAttribute('data-name') === page_state.doc());
        });
        elements = (self.control_bar.querySelector('fieldset.current form') || {elements: []}).elements;

        // Recreate tag toggles
        tag_toggles_el = self.control_bar.querySelectorAll('fieldset.current .tag-toggles')[0];
        if (tag_toggles_el) {
            tag_toggles_el.innerHTML = '';
            self.tag_toggles = Object.keys(page_state.state('tag_columns')).map(function (t) {
                var toggle = new TagToggle(t);

                toggle.onupdate = function (tag_state) {
                    var i, new_columns = JSON.parse(JSON.stringify(page_state.state('tag_columns')));

                    for (i = 0; i < self.table_selection.length; i++) {
                        if (tag_state === 'yes') {
                            new_columns[t][self.table_selection[i].DT_RowId] = true;
                        } else {
                            delete new_columns[t][self.table_selection[i].DT_RowId];
                        }
                    }

                    window.dispatchEvent(new window.CustomEvent('state_update', { detail: {
                        state: { tag_columns: new_columns }
                    }}));
                };

                tag_toggles_el.appendChild(toggle.dom());
                return toggle;
            });
        }

        // Hide the KWIC direction slider we're not using
        if (elements['kwic-int-start'] && elements['kwic-int-end']) {
            if (page_state.arg('kwic-dir') === 'start') {
                elements['kwic-int-start'].disabled = false;
                elements['kwic-int-end'].disabled = true;
            } else {
                elements['kwic-int-start'].disabled = true;
                elements['kwic-int-end'].disabled = false;
            }
        }

        // Set values from page options, or defaults
        Array.prototype.forEach.call(elements, function (el_or_array) {
            Array.prototype.forEach.call(Array.isArray(el_or_array) ? el_or_array : [el_or_array], function (el) {
                var new_val = page_state.arg(el.name);

                if (el.tagName === 'FIELDSET' || !page_state.defaults.hasOwnProperty(el.name)) {
                    Math.floor(0);
                } else if (el.tagName === 'INPUT' && el.type === "checkbox") {
                    el.checked = Array.isArray(new_val) ? new_val.indexOf(el.value) > -1 : (new_val === el.value);
                } else if (el.tagName === 'INPUT' && el.type === "radio") {
                    el.checked = new_val === el.value;
                } else if (el.tagName === 'INPUT' && el.getAttribute('type') === "nouislider") {
                    // Trigger slider update
                    el.slider_div.noUiSlider.set(new_val.split(':'));
                } else if (el.tagName === 'SELECT') {
                    if (el.name === "kwic-terms") {
                        // Make sure we consider existing options valid
                        el.innerHTML = to_options_html(page_state.arg('kwic-terms'));
                    } else if (el.name === "corpora" || el.name === "refcorpora") {
                        // Populate corpora dropdowns
                        el.innerHTML = to_options_html(self.corpora.corpora, 'CLiC corpora') + self.corpora.corpora.map(function (c) {
                            return to_options_html(c.children.map(function (child) {
                                return { id: child.id, title: child.title + (child.author ? ' (' + child.author + ')' : '') };
                            }), c.title);
                        }).join("");
                        // Resolve aliases in corpora selection, and turn back into a flat list
                        new_val = [].concat.apply([], new_val.map(function (c) {
                            return corpora.aliases[c] || [c];
                        }));
                    } else if (el.name === "book") {
                        // Populate book dropdowns
                        el.innerHTML = self.corpora.corpora.map(function (c) {
                            return to_options_html(c.children.map(function (child) {
                                return { id: child.id, title: child.title + (child.author ? ' (' + child.author + ')' : '') };
                            }), c.title);
                        }).join("");
                    }
                    jQuery(el).val(new_val);
                } else {
                    el.value = new_val;
                }
            });
        });

        // Tell all the chosen's that values are altered
        Array.prototype.forEach.call(self.control_bar.querySelectorAll('.chosen-select'), function (el, i) {
            jQuery(el).trigger("chosen:updated");
            // Add accessibility attributes to each element
            jQuery(el).attr('title', 'chosen-select');
        });

        Array.prototype.forEach.call(self.control_bar.querySelectorAll('.chosen-search-input'), function (el, i) {
            // Add accessibility attributes to each element
            jQuery(el).attr('title', 'chosen-search-input');
        });

        // Update swaps URLs
        Array.prototype.forEach.call(self.control_bar.querySelectorAll('.swap-state'), function (el, i) {
            el.setAttribute('href', swaps_to_url(
                page_state,
                el.getAttribute('data-arg')
            ));
        });
    }).then(function (data) {
        return Promise.all(Object.keys(self.panels).map(function (n) { self.panels[n].reload(page_state); })).then(function () {
            return data;
        });
    });
};

// Apply results of any search into data
ControlBar.prototype.new_data = function new_data(data) {
    var prevVal, el;

    if (data.selected_data && this.tag_toggles) {
        this.table_selection = data.selected_data;

        // Tell the toggle to update itself
        this.tag_toggles.forEach(function (toggle) {
            toggle.update(data.selected_data);
        });
    }

    if (data.allWords) {
        el = this.control_bar.querySelector('fieldset.current form').elements['kwic-terms'];

        if (el) {
            // Make sure KWIC term values already selected stay selectable
            prevVal = jQuery(el).val() || [];

            prevVal.map(function (t) {
                data.allWords[t] = true;
            });

            el.innerHTML = to_options_html(Object.keys(data.allWords || {}).sort());
            jQuery(el).val(prevVal);
            jQuery(el).trigger("chosen:updated");
        }
    }

    if (data.chapter_nums || data.chapter_num_selected) {
        el = this.control_bar.querySelector('fieldset.current form').elements.chapter_num;

        if (el) {
            if (data.chapter_nums) {
                el.innerHTML = to_options_html(data.chapter_nums);
            }
            jQuery(el).val(data.chapter_num_selected || data.chapter_nums[0]);
            jQuery(el).trigger("chosen:updated");
        }
    }
};

// Update panes with new page_state
ControlBar.prototype.tweak = function tweak(page_state) {
    var self = this;

    return Promise.all(Object.keys(self.panels).map(function (n) {
        return self.panels[n].tweak(page_state);
    }));
};

module.exports = ControlBar;
