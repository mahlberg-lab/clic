"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var noUiSlider = require('nouislider');
global.jQuery = jQuery;  // So chosen-js can find it
var chosen = require('chosen-js');

module.exports.chosen_init = function chosen_init(el) {
    window.jQuery(el).find('.chosen-select').chosen({ width: '100%', search_contains: true }).change(function (e) {
        // Chosen's change event isn't bubbling to the form, do it ourselves.
        e.target.form.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
    });

    window.jQuery(el).find('.chosen-select.allow-add-items').on('chosen:no_results', function (event, data) {
        var elChosen = event.target,
            elNoResults = elChosen.nextElementSibling.querySelector(":scope .no-results");

        elNoResults.innerText = "Add '" + data.chosen.get_search_text() + "'";
        elNoResults.setAttribute("data-value", data.chosen.get_search_text());
        elNoResults.style.fontWeight = "bold";
        elNoResults.style.color = "black";
        elNoResults.style.textAlign = "center";
        elNoResults.onclick = function (e) {
            elChosen.appendChild(new Option(
                elNoResults.getAttribute("data-value"),
                elNoResults.getAttribute("data-value"),
                false,
                true
            ));
            elChosen.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            window.setTimeout(function () {
                elChosen.nextElementSibling.querySelector(":scope .chosen-search-input").focus();
            }, 100);
        };
    }).next(".chosen-container").keydown(function (e) {
        var stroke = e.which !== null ? e.which : e.keyCode,
            elNoResults;

        if (stroke === 9 || stroke === 13) {
            // Find the no-results element, if it's there click it.
            elNoResults = e.target.closest(".chosen-container").querySelector(":scope .no-results");

            if (elNoResults) {
                elNoResults.click();
                e.stopPropagation();
                e.preventDefault();
            }
        }
    });
};
