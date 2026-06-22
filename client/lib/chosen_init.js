"use strict";
var jQuery = require('jquery/dist/jquery.slim.js');
require('chosen-js');  // NB: Registers jQuery .chosen() plugin
var TomSelect = require('tom-select');

module.exports.init = function chosen_init(el) {
    el.querySelectorAll('select.tomselect').forEach(function (elSelect) {
        var opts = {
            create: elSelect.classList.contains("allow-add-items"),
            plugins: { dropdown_input: true },
        };
        if (elSelect.multiple) {
            opts.plugins.remove_button = { title: 'Remove this item' };
        }
        if (!elSelect.classList.contains("tomselected")) {
            elSelect.tomselect = new TomSelect(elSelect, opts);
        }
    });
    window.jQuery(el).find('.chosen-select').chosen({ width: '100%', search_contains: true }).change(function (e) {
        // Chosen's change event isn't bubbling to the form, do it ourselves.
        e.target.form.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
    });
};

module.exports.refresh = function chosen_refresh(el) {
    if (el.tomselect) {
        el.tomselect.sync();
    } else {
        jQuery(el).trigger("chosen:updated");
    }
};
