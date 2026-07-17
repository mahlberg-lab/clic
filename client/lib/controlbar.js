"use strict";
var jQuery = require('jquery/dist/jquery.slim.js');
var noUiSlider = require('nouislider');
var bfa = require('browser-fs-access');
var api = require('./api.js');
var PanelTagColumns = require('./panel_tagcolumn.js');
var TagToggle = require('./tagtoggle.js');
var filesystem = require('./filesystem.js');
var concordance_utils = require('./concordance_utils.js');
var chosen_init = require('./chosen_init.js');
var cm_command = require('./cm-command.mjs');

var noUiSlider_opts = {
    'kwic-span': {
        start: [-5, 5],
        range: {min: -5, "10%": -4, "20%": -3, "30%": -2, "40%": -1,
                "60%":  1, "70%":  2, "80%":  3, "90%":  4, max:  5},
        snap: true,
        pips: {
            mode: 'steps',
            density: 10,
            filter: function (v, t) { return v === 0 ? 0 : 2; },
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
        if (Object.hasOwn(t, 'id') && Object.hasOwn(t, 'title')) {
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

    arg_swaps.split(",").forEach(function (str) {
        var to_swap = str.split(":");

        if (to_swap.length === 2) {
            detail.args[to_swap[0]] = page_state.arg(to_swap[1]);
            detail.args[to_swap[1]] = page_state.arg(to_swap[0]);
        }
    });

    return page_state.clone(detail).to_url();
}

function scrollDetailsIntoView(el) {
    // Wait until animation has finished, then scroll controlbar form into view if needed
    window.setTimeout(function () {
        var rect = el.getBoundingClientRect();
        if (rect.top < 0 || rect.bottom > window.innerHeight) {
            el.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }
    }, 500);
}


function ControlBar(control_bar) {
    var self = this;

    this.control_bar = control_bar;

    self.recordEventListener(window.document.querySelectorAll('nav + .handle')[0], 'click', function (e) {
        e.preventDefault();
        e.stopPropagation();
        control_bar.classList.toggle('in');
    });

    self.recordEventListener(control_bar, "click", function (e) {
        var el;

        el = e.target.closest('summary');
        if (el) {
            e.preventDefault();
            e.stopPropagation();

            window.dispatchEvent(new window.CustomEvent('state_new', { detail: {
                doc: el.firstChild.pathname,
                args: { corpora: self.page_state ? self.page_state.arg('corpora') : [] },
                state: {},
            }}));

            scrollDetailsIntoView(el.parentElement);
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
                self.load_state('load');
            } else if (clickedOn(e, 'A', 'merge')) {
                self.load_state('merge');
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

        el = e.target.closest('button[data-cm-command]');
        if (el) {
            e.stopPropagation();
            e.preventDefault();

            cm_command.dispatch(
                window,
                el.getAttribute("data-cm-command"),
                JSON.parse(el.getAttribute("data-cm-command-args") || "[]"),
            );
            return;
        }
    });

    self.recordEventListener(control_bar, "keypress", function (e) {
        if (e.keyCode === 13) {
            // Don't submit on enter, change instead
            e.preventDefault();
            if (e.target.tagName === "INPUT") {
                e.target.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            }
        }
    });

    self.recordEventListener(control_bar, "change", function (e) {
        if (this.change_timeout) {
            window.clearTimeout(this.change_timeout);
        }
        this.change_timeout = window.setTimeout(function () {
            var new_search = {},
                form = control_bar.querySelector('details[open] form');
            if (!form) {
                // Don't try and commit changes until there's a current section (i.e. the form has finished loading)
                // NB: This is triggered by updating noUiSlider on load
                return;
            }

            // Unchecked checkboxes should be emptied if not mentioned
            Array.prototype.forEach.call(control_bar.querySelectorAll('details[open] input[type=checkbox]:not(:checked)'), function (el, i) {
                new_search[el.name] = [];
            });

            jQuery(form).serializeArray().forEach(function (f) {
                if (Array.isArray(new_search[f.name])) {
                    new_search[f.name].push(f.value);
                } else if (Object.hasOwn(new_search, f.name)) {
                    new_search[f.name] = [new_search[f.name], f.value];
                } else {
                    new_search[f.name] = [f.value];
                }
            });

            // Empty select boxes should be empty
            Array.prototype.forEach.call(control_bar.querySelectorAll('details[open] select[multiple]'), function (el, i) {
                new_search[el.name] = jQuery(el).val();
            });

            // NB: We use flush to get rid of now-non-existant form fields, such as deleted flexiconc algorithms
            window.dispatchEvent(new window.CustomEvent('state_speculative_update', { detail: {args: new_search, flush: true}}));
        }, 300);
    });

    if (window.screen.availWidth > 960) {
        this.control_bar.classList.add('in');
    }

    chosen_init.init(this.control_bar);

    // Turn "nouislider"-type inputs into an actual nouislider
    Array.prototype.forEach.call(this.control_bar.querySelectorAll('input[type=nouislider]'), function (el, i) {
        if (el.slider_div) {
            // Already init'ed.
            return;
        }
        el.slider_div = document.createElement('DIV');
        el.style.display = 'none';
        el.parentNode.insertBefore(el.slider_div, el.nextSibling);

        noUiSlider.create(el.slider_div, noUiSlider_opts[el.name]);

        el.slider_div.noUiSlider.on('update', function (values) {
            var val_string = values.map(Math.round).join(':');

            // NB: The form element has to have the default value set in HTML, or this will trigger an erronous change event
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
}

ControlBar.prototype.load_state = function load_state(load_mode) {
    var self = this;

    return bfa.fileOpen().then(function (file) {
        return file.text();
    }).then(function (content) {
        var new_state = filesystem.file_to_state(content);

        if (load_mode === 'merge') {
            new_state.state = concordance_utils.merge_tags({
                tag_columns: self.page_state.state('tag_columns'),
                tag_column_order: self.page_state.state('tag_column_order'),
            }, new_state.state);
        }

        window.dispatchEvent(new window.CustomEvent('state_new', { detail: new_state }));
    }).catch(function (err) {
        if (err.name !== 'AbortError') { throw err; }
    });
};

/** addEventListner, but record entries in self.event_listeners for removal on shutdown */
ControlBar.prototype.recordEventListener = function (target, type, listener) {
    if (!this.event_listeners) {
        this.event_listeners = [];
    }
    target.addEventListener(type, listener);
    this.event_listeners.push([target, type, listener]);
};

ControlBar.prototype.shutdown = function shutdown(page_state) {
    var self = this;

    return new Promise(function (resolve) {
        // Remove any registered event listeners
        (self.event_listeners || []).forEach(function (x) {
            x[0].removeEventListener(x[1], x[2]);
        });
        self.event_listeners = undefined;
        resolve();
    });
};

// Refresh controls based on page_state
ControlBar.prototype.reload = function reload(page_state) {
    var self = this;

    self.page_state = page_state; // Store this for events

    return Promise.resolve().then(function () {
        return self.corpora || api.get('corpora');
    }).then(function (corpora) {
        var tag_toggles_el, elements;

        self.corpora = corpora;

        // Enable the section for the page
        Array.prototype.forEach.call(self.control_bar.querySelectorAll('details[data-name]'), function (el, i) {
            if ('/' + el.getAttribute('data-name') === page_state.doc()) {
                el.setAttribute('open', 'open');

                scrollDetailsIntoView(el);
            } else {
                el.removeAttribute('open');
            }
        });
        elements = (self.control_bar.querySelector('details[open] form') || {elements: []}).elements;

        // Recreate tag toggles
        tag_toggles_el = self.control_bar.querySelectorAll('details[open] .tag-toggles')[0];
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

        // Populate selects that need dynamic content
        Array.prototype.forEach.call(elements, function (el) {
            if (!el.name || el.tagName === 'FIELDSET') {
                Math.floor(0);
            } else if (el.name === 'kwic-int-start') {
                // Hide the KWIC direction slider we're not using
                el.disabled = page_state.arg('kwic-dir') !== 'start';
            } else if (el.name === 'kwic-int-end') {
                // Hide the KWIC direction slider we're not using
                el.disabled = page_state.arg('kwic-dir') === 'start';
            } else if (el.name === "kwic-terms") {
                // Make sure we consider existing options valid
                el.innerHTML = to_options_html(page_state.arg('kwic-terms'));
            } else if (el.name === "corpora" || el.name === "refcorpora") {
                // Populate corpora dropdowns
                el.innerHTML = to_options_html(self.corpora.corpora, 'CLiC corpora') + self.corpora.corpora.map(function (c) {
                    return to_options_html(c.children.map(function (child) {
                        return { id: child.id, title: child.title + (child.author ? ' (' + child.author + ')' : '') };
                    }), c.title);
                }).join("");
            } else if (el.name === "book") {
                // Populate book dropdowns
                el.innerHTML = self.corpora.corpora.map(function (c) {
                    return to_options_html(c.children.map(function (child) {
                        return { id: child.id, title: child.title + (child.author ? ' (' + child.author + ')' : '') };
                    }), c.title);
                }).join("");
            }
            if (el.tagName === "SELECT" && el.classList.contains("allow-add-items")) {
                // We should add any missing items for an allow-add-items
                const existingOptions = new window.Set(Array.from(el.options).map(function (o) { return o.value; }));

                el.append.apply(el, page_state.arg(el.name).filter(function (x) {
                    // Only want to add items not already in the list
                    // TODO: When creating new algorithms via. JS, the value is [null]?
                    return x && !existingOptions.has(x);
                }).map(function (x) {
                    // Turn them into an already-selected Option
                    return new Option(x, x, true, true);
                }));
            }
        });

        self._apply_state(elements, page_state);

        // Tell all the chosen's that values are altered
        Array.prototype.forEach.call(self.control_bar.querySelectorAll('.chosen-select,.tomselect'), function (el, i) {
            chosen_init.refresh(el);
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
        return Promise.all(Object.keys(self.panels).map(function (n) { return self.panels[n].reload(page_state); })).then(function () {
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
        el = this.control_bar.querySelector('details[open] form').elements['kwic-terms'];

        if (el) {
            // Make sure KWIC term values already selected stay selectable
            prevVal = jQuery(el).val() || [];

            prevVal.forEach(function (t) {
                data.allWords[t] = true;
            });

            el.innerHTML = to_options_html(Object.keys(data.allWords || {}).sort());
            jQuery(el).val(prevVal);
            chosen_init.refresh(el);
        }
    }

    if (data.chapter_nums || data.chapter_num_selected) {
        el = this.control_bar.querySelector('details[open] form').elements.chapter_num;

        if (el) {
            if (data.chapter_nums) {
                el.innerHTML = to_options_html(data.chapter_nums);
            }
            jQuery(el).val(data.chapter_num_selected || data.chapter_nums[0]);
            chosen_init.refresh(el);
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

ControlBar.prototype._apply_state = function (elements, page_state) {
    var self = this;

    // Set values from page options, or defaults
    Array.prototype.forEach.call(elements, function (el_or_array) {
        var all_els = el_or_array instanceof window.Element ? [el_or_array] : Array.from(el_or_array);
        var first_el = all_els[0];
        var new_val = page_state.arg(first_el.name);

        if (first_el.tagName === 'FIELDSET' || !first_el.name) {
            Math.floor(0);
        } else if (first_el.tagName === 'INPUT' && first_el.type === "checkbox") {
            all_els.forEach(function (el) {
                el.checked = Array.isArray(new_val) ? new_val.indexOf(el.value) > -1 : (new_val === el.value);
            });
        } else if (first_el.tagName === 'INPUT' && first_el.type === "radio") {
            all_els.forEach(function (el) {
                el.checked = new_val === el.value;
            });
        } else if (first_el.tagName === 'INPUT' && first_el.getAttribute('type') === "nouislider") {
            if (all_els.length > 1) {
                throw new Error("There should be only one nouislider with given name");
            }
            // Trigger slider update
            first_el.slider_div.noUiSlider.set(new_val.split(':'));
        } else if (first_el.tagName === 'SELECT') {
            if (all_els.length > 1) {
                throw new Error("There should be only one select with given name");
            }
            if (first_el.name === "corpora" || first_el.name === "refcorpora") {
                // Resolve aliases in corpora selection, and turn back into a flat list
                new_val = [].concat.apply([], new_val.map(function (c) {
                    return self.corpora.aliases[c] || [c];
                }));
            }
            jQuery(first_el).val(new_val);
        } else {
            if (!Array.isArray(new_val)) {
                new_val = [new_val];
            }

            while (all_els.length > 1 && all_els.length > new_val.length) {
                // Element list too long: Remove some (but stop before we empty the list)
                all_els[all_els.length - 1].parentElement.removeChild(all_els[all_els.length - 1]);
                all_els.pop();
            }

            // First item should be disabled (instead of removed) iff new_val is empty
            all_els[0].disabled = (new_val.length === 0);

            while (all_els.length < new_val.length) {
                // Element list too short: Clone first element to add further elements
                all_els.push(all_els[0].cloneNode());
                all_els[all_els.length - 2].insertAdjacentElement("afterend", all_els[all_els.length - 1]);
            }
            all_els.forEach(function (el, i) {
                el.value = new_val[i];
            });
        }
    });
};

module.exports = ControlBar;
