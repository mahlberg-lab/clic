"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise, DOMParser */


/**
  * Annotate regions onto content string, optionally incuding a highlight region
  */
module.exports.regions_to_html = function (content, regions, highlight_region) {
    var out = '<span>', i, start = 0, inserts = [], open_regions = {};

    // For each region, add opening and closing inserts
    for (i = 0; i < regions.length; i++) { // ["chapter.title", (lower), (upper), (rvalue)]
        inserts.push({
            pos: regions[i][1],
            opening: true,
            class: regions[i][0].replace(/\./g, '-')
                 + (regions[i][0] === "chapter.title" ? " chapter-" + regions[i][3] : ""),
            region_start: regions[i][1],
        });
        inserts.push({
            pos: regions[i][2],
            class: inserts[inserts.length - 1].class,
            region_start: regions[i][1],
        });
    }

    // Add highlight region if given
    if (highlight_region) {
        inserts.push({
            pos: highlight_region[0],
            opening: true,
            class: 'highlight',
            region_start: highlight_region[0],
        });
        inserts.push({
            pos: highlight_region[1],
            class: 'highlight',
            region_start: highlight_region[0],
        });
    }

    // Sort inserts by their position, then the region's start (so closes happen before opens)
    inserts.sort(function (a, b) { return a.pos - b.pos || a.region_start - b.region_start; });

    for (i = 0; i < inserts.length; i++) {
        // If text is available, start a span with correct regions and insert it
        if (inserts[i].pos > start) {
            out += '</span><span class="' + Object.keys(open_regions).join(" ") + '">';
            out += content.slice(start, inserts[i].pos);
            start = inserts[i].pos;
        }

        // Add / remove the region marker
        if (inserts[i].opening) {
            open_regions[inserts[i].class] = true;
        } else {
            delete open_regions[inserts[i].class];
        }
        if (inserts[i].class === 'chapter-sentence') {
            out += '</span><span class="boundary-sentence">';
        }
    }
    out += '</span>';
    return out;
};

/**
  * Extract chapter number / title from document, assuming 'chapter.title'
  * regions are available
  */
module.exports.chapter_headings = function (content, regions) {
    var i, out = [], title_prefix = "";

    // Pick out part/title headings, and put them in document order
    regions = regions.filter(function (r) {
        return r[0] === "chapter.part" || r[0] === "chapter.title";
    }).sort(function (a, b) { return a[1] - b[1]; });

    for (i = 0; i < regions.length; i++) { // ["chapter.title", (lower), (upper), (rvalue)]
        if (regions[i][0] === "chapter.part") {
            title_prefix = content.slice(regions[i][1], regions[i][2]) + " ";
        } else if (regions[i][0] === "chapter.title") {
            out.push({
                id: regions[i][3],
                title: title_prefix + content.slice(regions[i][1], regions[i][2]),
            });
        }
    }

    return out;
};
