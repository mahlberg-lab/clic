"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var ControlBar = require('./controlbar.js');
var chosen_init = require('./chosen_init.js');
var flexiclic = require('./flexiclic.js').flexiclic;
var util_flexiconc = require('./util_flexiconc.js');

// ControlBarFlexiConc inherits ControlBar
function ControlBarFlexiConc() {
    return ControlBar.apply(this, arguments);
}
ControlBarFlexiConc.prototype = Object.create(ControlBar.prototype);

ControlBarFlexiConc.prototype.shutdown = function shutdown(page_state) {
    // Not a flexiconc page, shutdown if needed & carry on
    return flexiclic ? flexiclic.shutdown() : Promise.resolve({});
};

ControlBarFlexiConc.prototype.reload = function reload(page_state) {
    /** Promise to return DOM element for an (algo_name) with element names prefixed by (newPrefix) */
    function newAlgoHtml(algo_name, newPrefix) {
        return flexiclic.algorithm_render_html({algo_name: algo_name, prefix: newPrefix}).then(function (algoHtml) {
            var elNew = document.createElement("fieldset");
            elNew.className = "algorithm";
            elNew.innerHTML = algoHtml.join("\n");

            // Wire up event to close button
            elNew.querySelectorAll("button[aria-label='Close']").forEach(function (elButton) { elButton.onclick = function (event) {
                var el, elAlgo = event.target.closest(".algorithm"), elForm = elAlgo.form;

                function renumberElements(els) {
                    Array.from(els).forEach(function (elField) {
                        elField.name = elField.name.replace(/^(\w+)\[(\d+)\]/, function (m, g1, g2) {
                            return g1 + "[" + (parseInt(g2, 10) - 1) + "]";
                        });
                    });
                }

                // Renumber subsequent algorithms to hide gap
                el = elAlgo;
                while (el) {
                    // NB: add-algorithm isn't a fieldset, so has no elements
                    renumberElements(el.elements || []);
                    el = el.nextElementSibling;
                }

                elAlgo.parentNode.removeChild(elAlgo);
                event.stopPropagation();
                event.preventDefault();

                elForm.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            }; });

            elNew.querySelectorAll("button[aria-label='Fork']").forEach(function (elButton) { elButton.onclick = function (event) {
                var el, elAlgo = event.target.closest(".algorithm"), elForm = elAlgo.form;

                // Update fc-path to next free path
                document.getElementById("ctlb-flexiconc-fc-path-next").checked = true;

                // Remove subsequent algorithms
                el = elAlgo.nextElementSibling;
                while (el) {
                    if (el.classList.contains("algorithm")) {  // NB: skip over algorithm-add
                        elAlgo.parentNode.removeChild(el);
                    }
                    el = el.nextElementSibling;
                }

                event.stopPropagation();
                event.preventDefault();

                elForm.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            }; });

            return elNew;
        });
    }

    var nested_args = util_flexiconc.renest_args(page_state.all_args(/^(?:algo|annotation)\[/));

    return flexiclic.algorithms_by_class().then(function (algorithms_by_class) {
        return Promise.all(Array.from(window.document.querySelectorAll("#control-bar section[data-name='flexiconc'] .algorithm-group")).map(function (elAlgoGroup) {
            var algo_class = elAlgoGroup.getAttribute('data-algorithm-class'),
                arg_algo = nested_args[algo_class] || [],
                elAddSelect = elAlgoGroup.querySelector(":scope > .algorithm-add > select"),
                elsExisting = Array.from(elAlgoGroup.querySelectorAll(":scope > .algorithm:not(.fixed)")),
                cur_algo_names = arg_algo.map(function (x) { return x.algorithm_name; });

            // Fill add select with available algorithms
            // NB: Blank option so we show placeholder: https://harvesthq.github.io/chosen/#default-text-support
            elAddSelect.innerHTML = '<option></option>' + algorithms_by_class[algo_class].map(function (a) {
                return (new Option(a.label, a.name)).outerHTML;
            });

            // Wire up change event to populate new algorithm
            elAddSelect.onchange = function (event) {
                // Count existing algorithms, new one will be one higher
                var newPrefix = algo_class + "[" + elAlgoGroup.querySelectorAll(":scope > .algorithm:not(.fixed)").length + "]",
                    el = event.target;

                newAlgoHtml(el.options[el.selectedIndex].value, newPrefix).then(function (elNew) {
                    // Insert algorithm before the "algorithm-add" select
                    el.closest('.algorithm-add').insertAdjacentElement("beforebegin", elNew);
                    chosen_init.init(elNew);
                });
            };

            // Remove excess entries, both from DOM & elExisting array
            while (elsExisting.length > cur_algo_names.length) {
                elsExisting.pop().remove();
            }

            // Add dummy entries for entries that need to be created
            while (elsExisting.length < cur_algo_names.length) {
                elsExisting.push(document.createElement("fieldset"));
                elAlgoGroup.lastElementChild.insertAdjacentElement("beforebegin", elsExisting[elsExisting.length - 1]);
            }

            // Ensure everything in elsExisting & cur_algo_names are for the same algorithm
            return Promise.all(cur_algo_names.map(function (algo_name, i) {
                var prefix = algo_class + "[" + i + "]";

                if (algo_name === (elsExisting[i].elements[prefix + "[algorithm_name]"] || {}).value) {
                    // algo_name matches, leave HTML as-is.
                    return Promise.resolve();
                }
                return newAlgoHtml(algo_name, prefix).then(function (el) {
                    // Replace old elements with new algo
                    elsExisting[i].replaceWith(el);
                    chosen_init.init(el);
                });
            }));
        }));
    }).then(function () {
        // Update path-chooser
        var fcAllPaths = Object.assign({"0": {}}, page_state.state("fc-all-paths")),
            // NB: No stored paths --> force current path to be numbered "1"
            fcPath = Object.keys(fcAllPaths).length > 1 ? page_state.arg("fc-path") : "1",
            nextPathId = 1;

        // Sync allPaths with current path (NB: Storing flattened form)
        fcAllPaths[fcPath] = page_state.all_args(/^algo\[/);
        window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
            args: { "fc-path": fcPath },
            state: { "fc-all-paths": fcAllPaths },
        }}));

        // Create all available path options & hidden next option
        document.querySelector(".flexiconc-path-chooser").innerHTML = Array.from(Object.keys(fcAllPaths)).map(function (k) {
            while (nextPathId <= parseInt(k, 10)) {
                // nextPathId should be a bigger integer than any existing key
                nextPathId++;
            }
            if (k === "0") {
                // 0 is the special tree path
                return [
                    '<input type="radio" name="fc-path" value="0" id="ctlb-flexiconc-fc-path-0" />',
                    '<label for="ctlb-flexiconc-fc-path-0"><img src="/icons/tree.svg" width="17" height="23" style="position: relative;top:-1px" alt="See full analysis tree"></label>',
                ].join(" ");
            }
            return [
                '<input type="radio" name="fc-path"',
                'value="' + k + '"',
                'id="ctlb-flexiconc-fc-path-' + k + '"',
                (k === fcPath ? 'checked' : ''),
                '/><label for="ctlb-flexiconc-fc-path-' + k + '">' + k + '</label>',
            ].join(" ");
        }).join("\n") + [
            '<input type="radio" name="fc-path" value = "' + nextPathId + '" id="ctlb-flexiconc-fc-path-next" />',
            '<label for="ctlb-flexiconc-fc-path-next" title="Add empty path" aria-label="add"><span style="position: relative; top: 3px; line-height: 0; font-size: 20px" aria-hidden="true">+</span></label>',
        ].join("\n");

        // Scroll selected path into view
        document.getElementById("ctlb-flexiconc-fc-path-" + fcPath).scrollIntoView({inline: "nearest"});

        // If viewing tree, hide algo group (thus add algorithm button)
        document.querySelector(".algorithm-group[data-algorithm-class=algo]").style.display = fcPath === "0" ? "none" : "";

        document.querySelector(".flexiconc-path-chooser").onchange = function (event) {
            // Click on "+", start with an empty set of algorithms
            // NB: This isn't triggered by fork buttons, as they change the form, not the radio controls
            if (event.target.id === "ctlb-flexiconc-fc-path-next") {
                document.querySelectorAll(".algorithm-group[data-algorithm-class=algo] .algorithm").forEach(function (el) {
                    el.parentNode.removeChild(el);
                });
            }

            flexiclic.tidy_paths({
                paths: util_flexiconc.renest_all(page_state.state("fc-all-paths")),
            }).then(function () {
                // Instead of letting form update, set state to match fc-all-paths for selected value
                window.dispatchEvent(new window.CustomEvent('state_update', { detail: {
                    args: Object.assign(
                        {},
                        // Everything non-algo from the current state
                        page_state.all_args(/^(?!algo\[)/),
                        // All stored algo[ args from fc-all-paths
                        fcAllPaths[event.target.value] || [],
                        // New fc-path pointer
                        { "fc-path": [event.target.value] }
                    ),
                    flush: true,
                }}));
            });
            event.stopPropagation();
            event.preventDefault();
        };
    }).then(ControlBar.prototype.reload.bind(this, page_state));
};

module.exports = ControlBarFlexiConc;
