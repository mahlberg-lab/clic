"use strict";
var jQuery = require('jquery/dist/jquery.slim.js');

// Add accessibility attributes to the dynamically added content that has to be added retrospectively
// (e.g. content inserted by a 3rd party library)
module.exports.add_attributes = function () {
    // 'chosen-search-input' fields (added by chosen.js plugin)
    jQuery('.chosen-search-input').each(function(index, object) {
        jQuery(object).attr('title', 'chosen-search-input');
        console.log(1);
    });

};