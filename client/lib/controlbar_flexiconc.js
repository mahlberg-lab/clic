"use strict";
var ControlBar = require('./controlbar.js');
var chosen_init = require('./chosen_init.js');
var flexiclic = require('./flexiclic.js').flexiclic;
var util_flexiconc = require('./util_flexiconc.js');
var bfa = require('browser-fs-access');

// lineid-picker: Create the iframe, pull values back
function lineid_picker_init(el, page_state) {
    el.querySelectorAll(":scope .lineid-picker").forEach(function (elPicker) {
        var i, argRe;

        // Build regex selecting non-algo or previous algo arguments
        argRe = '^(?!algo)';
        for (i = 0; i < parseInt(elPicker.name.match(/algo\[(\d+)\]/)[1], 10); i++) {
            argRe += "|^algo\\[" + i + "\\]";
        }

        elPicker.onclick = function (event) {
            var elOverlay;

            event.stopPropagation();
            event.preventDefault();

            document.body.insertAdjacentHTML("afterbegin", [
                '<div class="lineid-picker-overlay"><div>',
                '<iframe></iframe>',
                '<div class="button-group"><button class="ok immutable">OK</button></div>',
                '<div class="button-group"><button class="cancel">Cancel</button></div>',
                '</div></div>',
            ].join("\n"));
            elOverlay = document.querySelector("body > .lineid-picker-overlay");
            elOverlay.querySelector(":scope iframe").src = [
                page_state.to_url(argRe),
                "fc-select-type=" + elPicker.getAttribute("data-fc-select-type"),
                "fc-select=" + (elPicker.value || "[]"),
            ].join("&");
            elOverlay.querySelector(":scope button.ok").onclick = function (ev2) {
                // Update hidden input with selected values
                elPicker.value = JSON.stringify(elOverlay.querySelector(":scope iframe").contentWindow.fc_select_data());
                elPicker.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
                document.body.removeChild(elOverlay);
            };
            elOverlay.querySelector(":scope button.cancel").onclick = function (ev2) {
                document.body.removeChild(elOverlay);
            };
        };
    });
}

// ControlBarFlexiConc inherits ControlBar
function ControlBarFlexiConc() {
    return ControlBar.apply(this, arguments);
}
ControlBarFlexiConc.prototype = Object.create(ControlBar.prototype);

ControlBarFlexiConc.prototype.shutdown = function shutdown(page_state) {
    return ControlBar.prototype.shutdown.apply(this, arguments).then(function () {
        return flexiclic ? flexiclic.shutdown() : {};
    });
};

ControlBarFlexiConc.prototype.reload = function reload(page_state) {
    var self = this,
        nested_args = util_flexiconc.renest_args(page_state.all_args(/^(?:algo|annotation)\[/));

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

            elNew.querySelectorAll("*[aria-label='Fork']").forEach(function (elButton) { elButton.onclick = function (event) {
                var elAlgo = event.target.closest(".algorithm"),
                    elAllAlgos = Array.from(elAlgo.parentNode.children),
                    elAlgoIdx = elAllAlgos.indexOf(elAlgo);

                event.stopPropagation();
                event.preventDefault();

                // Enable algorithms up to and including elAlgo
                elAllAlgos.forEach(function (el, idx) {
                    el.disabled = idx > elAlgoIdx;
                    if (idx > elAlgoIdx && el.classList.contains("algorithm")) {
                        // Remove subsequent algorithms
                        el.parentNode.removeChild(el);
                    } else {
                        // Re-enable if current path is immutable
                        el.disabled = false;
                    }
                });

                // Update fc-path to next free path
                document.getElementById("ctlb-flexiconc-fc-path-next").checked = true;

                elAlgo.form.dispatchEvent(new window.CustomEvent('change', {"bubbles": true}));
            }; });

            return elNew;
        });
    }

    return Promise.all(Array.from(window.document.querySelectorAll("#control-bar details[data-name='flexiconc'] .algorithm-group")).map(function (elAlgoGroup) {
        var algo_class = elAlgoGroup.getAttribute('data-algorithm-class'),
            arg_algo = nested_args[algo_class] || [],
            elAddSelect = elAlgoGroup.querySelector(":scope > .algorithm-add > select"),
            elsExisting = Array.from(elAlgoGroup.querySelectorAll(":scope > .algorithm:not(.fixed)")),
            cur_algo_names = arg_algo.map(function (x) { return x.algorithm_name; });

        // Wire up change event to populate new algorithm
        elAddSelect.onchange = function (event) {
            // Count existing algorithms, new one will be one higher
            var newPrefix = algo_class + "[" + elAlgoGroup.querySelectorAll(":scope > .algorithm:not(.fixed)").length + "]",
                el = event.target;

            newAlgoHtml(el.options[el.selectedIndex].value, newPrefix).then(function (elNew) {
                // Insert algorithm before the "algorithm-add" select
                el.closest('.algorithm-add').insertAdjacentElement("beforebegin", elNew);
                chosen_init.init(elNew);
                lineid_picker_init(elNew, page_state);
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

            return newAlgoHtml(algo_name, prefix).then(function (el) {
                if (el.outerHTML === elsExisting[i].fcOrigOuterHTML) {
                    // Algorithm's HTML hasn't changed since it was created leave as-is
                    elsExisting[i].disabled = false;
                } else {
                    // Replace old elements with new algo
                    el.fcOrigOuterHTML = el.outerHTML;  // NB HTML won't match afterwards, values change & tomselect selects
                    elsExisting[i].replaceWith(el);
                    chosen_init.init(el);
                    lineid_picker_init(el, page_state);
                }
            });
        }));
    })).then(function () {
        // Update path-chooser
        var fcAllPaths = Object.assign({"0": {}}, page_state.state("fc-all-paths")),
            fcPath = page_state.arg("fc-path"),
            nextPathId = 1;

        // Get number of mutable path, or null if it isn't a mutable path
        function getMutablePathNumber(k) {
            return k !== "0" && k.match(/^\d+$/) ? parseInt(k, 10) : null;
        }

        // Generate HTML for path chooser items for a path named (k)
        function newPathChooserItem(k) {
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
                '/><label for="ctlb-flexiconc-fc-path-' + k + '"',
                'class="',
                (getMutablePathNumber(k) === null ? "immutable" : ""),
                '" >',
                // Pad single-character length keys, as min-length is used for flexbox-sizing
                (k.length === 1 ? " " + k + " " : k),
                '</label>',
            ].join(" ");
        }

        // Sync allPaths with current path (NB: Storing flattened form)
        fcAllPaths[fcPath] = page_state.all_args(/^algo\[/);
        window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
            state: { "fc-all-paths": fcAllPaths },
        }}));

        // Create all available path options & hidden next option
        document.querySelector(".flexiconc-path-chooser").innerHTML = Array.from(Object.keys(fcAllPaths)).map(function (k) {
            while (nextPathId <= getMutablePathNumber(k)) {
                // nextPathId should be a bigger integer than any existing key
                nextPathId++;
            }
            return newPathChooserItem(k);
        }).join("\n") + [
            '<input type="radio" name="fc-path" value = "' + nextPathId + '" id="ctlb-flexiconc-fc-path-next" />',
            '<label for="ctlb-flexiconc-fc-path-next" title="Add empty path" aria-label="add"><span style="position: relative; top: 3px; line-height: 0; font-size: 20px" aria-hidden="true">+</span></label>',
        ].join("\n");

        // Scroll selected path into view
        document.getElementById("ctlb-flexiconc-fc-path-" + fcPath).scrollIntoView({inline: "nearest"});

        // Clear save field, shouldn't be re-using old names
        document.querySelector(".flexiconc-path-save input[name=save-name]").value = "";

        // Disable algorithms / add / save iff path immutable
        document.querySelectorAll(".algorithm-group[data-algorithm-class=algo]").forEach(function (el) {
            el.classList.toggle("disabled", getMutablePathNumber(fcPath) === null);
        });
        document.querySelectorAll(".algorithm-group[data-algorithm-class=algo] > fieldset.algorithm").forEach(function (el) {
            el.disabled = getMutablePathNumber(fcPath) === null;
        });
        document.querySelectorAll(".algorithm-group[data-algorithm-class=algo] > .algorithm-add select").forEach(function (el) {
            el.disabled = getMutablePathNumber(fcPath) === null;
        });
        document.querySelector(".flexiconc-path-save").classList.toggle("disabled", getMutablePathNumber(fcPath) === null);
        document.querySelector(".flexiconc-path-save").style.display = fcPath === "0" ? "none" : "";
        document.querySelector(".flexiconc-tree-save").style.display = fcPath !== "0" ? "none" : "";

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

        document.querySelector(".flexiconc-tree-save").onclick = function (event) {
            event.stopPropagation();
            event.preventDefault();

            if (event.target.classList.contains("action-save")) {
                var blob = new window.Blob([JSON.stringify(page_state.to_json())], { type: "application/json" });
                bfa.fileSave(blob, { fileName: "clic-analysis-tree.json" });
            } else if (event.target.classList.contains("action-load")) {
                self.load_state('load');
            }

            return false;
        };

        document.querySelector(".flexiconc-path-save").onkeypress = function (event) {
            // Don't let the default submit->change event happen
            event.stopPropagation();
        };
        document.querySelector(".flexiconc-path-save").onchange = function (event) {
            // Don't let the default form change event happen
            event.stopPropagation();
            event.preventDefault();
            return false;
        };
        document.querySelector("#ctlb-flexiconc-save-form").onsubmit = function (event) {
            var fcNewPath, elNewPath;
            event.stopPropagation();
            event.preventDefault();

            fcNewPath = event.target.elements["save-name"].value;
            if (fcNewPath === "") {
                // Ignore attempts to save empty name
                return;
            }
            if (getMutablePathNumber(fcNewPath) !== null || fcNewPath === "0") {
                window.alert("Saved branch names cannot be numeric");
                return;
            }
            fcAllPaths = Object.assign({"0": {}}, page_state.state("fc-all-paths"));
            fcAllPaths[fcNewPath] = page_state.all_args(/^algo\[/);
            window.dispatchEvent(new window.CustomEvent('state_tweak', { detail: {
                state: { "fc-all-paths": fcAllPaths },
            }}));

            document.querySelector("#ctlb-flexiconc-fc-path-next").insertAdjacentHTML("beforebegin", newPathChooserItem(fcNewPath));
            elNewPath = document.querySelector("#ctlb-flexiconc-fc-path-" + fcNewPath + " + label");

            // Scroll to path-chooser to make it obvious there's a new item
            document.querySelector(".flexiconc-path-chooser").scrollIntoView({inline: "center", block: "center"});
            elNewPath.scrollIntoView({inline: "center", block: "nearest"});

            // Blink new item
            elNewPath.classList.add("new");
            window.setTimeout(function () {
                elNewPath.classList.remove("new");
            }, 100);

            event.target.elements["save-name"].value = "";

            return false;
        };
    }).then(ControlBar.prototype.reload.bind(this, page_state));
};

module.exports = ControlBarFlexiConc;
