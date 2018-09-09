"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */

/**
  * Generate a carousel
  * - slides_html: Array of HTML text for each carousel slide
  * - timeout: Time to show each slide, in seconds
  */
module.exports.gen_carousel = function (slides_html, timeout) {
    var carousel_el, interval;

    // We should repeat the first item at the bottom of the stack, so we can't see the loop
    slides_html.push(slides_html[0]);
    // Reverse slides so we pull them off the stack in the right order
    slides_html.reverse();

    carousel_el = document.createElement('UL');
    carousel_el.className = 'carousel';
    carousel_el.innerHTML = slides_html.join("");

    interval = window.setInterval(function next_slide(slide_els) {
        var i;

        if (!document.body.contains(carousel_el)) {
            // Been removed from DOM, so shut down
            window.clearInterval(interval);
            return;
        }

        // Look at slides in reverse order
        for (i = (slide_els.length - 1); i >= 0; i--) {
            if (i === 0) {
                // Got to final slide (repetition of first slide), shuffle everything back on-screen
                for (i = 0; i < slide_els.length; i++) {
                    slide_els[i].classList.remove('offscreen');
                }
                // Our time is already up, so advance as soon as DOM has caught up
                window.setTimeout(next_slide, 10, slide_els);
                return;
            }
            if (!slide_els[i].classList.contains('offscreen')) {
                // Found a slide that hasn't been moved offscreen, move it
                slide_els[i].classList.add('offscreen');
                return;
            }
        }
    }, timeout * 1000, carousel_el.childNodes);

    return carousel_el;
};
