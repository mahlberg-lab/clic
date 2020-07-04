"use strict";
/*jslint todo: true, regexp: true, browser: true */
/*global Promise */

// Add accessibility attributes to the dynamically added content that has to be added retrospectively
// (e.g. content inserted by a 3rd party library)
module.exports.add_attributes = function () {
    // 'chosen-search-input' fields (added by chosen.js plugin)
    var inputs = document.getElementsByClassName("chosen-search-input");
    // for (var i = 0; i < inputs.length; i++) {
    //     inputs.item(i).setAttribute("title", "test"); 
    // }
};