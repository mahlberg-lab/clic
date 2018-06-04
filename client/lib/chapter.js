"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var PagePromise = require('./page_promise.js');

var state_defaults = {
    'start': 0,
    'end': 0,
    'book': '',
    'chapter_num': 0,
    'chapter_id': -1,
};

var page;

function Chapter(content_el) {
    /**
      * Highlight terms between start and end, if args provided
      */
    this.highlight = function highlight(page_opts) {
        var start_node = parseInt(page_opts.arg('start'), 10),
            end_node = parseInt(page_opts.arg('end'), 10),
            word_nodes,
            i;

        if (start_node === 0 && end_node === 0) {
            return;
        }
        word_nodes = content_el.getElementsByTagName("w");
        for (i = start_node; i < end_node; i++) {
            word_nodes[i].setAttribute('selected', 'selected');
        }
        window.scrollTo(0, word_nodes[start_node].getBoundingClientRect().top
                           + window.pageYOffset
                           - (window.innerHeight / 2));
    };

    /**
      * Load the given chapter and add to page
      */
    this.reload = function reload(page_opts) {
        var self = this, args;

        if (page_opts.arg('chapter_id') > -1) {
            args = {
                chapter_id: page_opts.arg('chapter_id'),
            };
        } else {
            args = {
                book: page_opts.arg('book'),
                chapter_num: page_opts.arg('chapter_num'),
            };
        }

        return api.get('chapter', args).then(function (doc) {
            content_el.appendChild(doc.documentElement);
            self.highlight(page_opts);
        });
    };
}

function select_components(page_state) {
    if (!page) {
        page = new Chapter(document.getElementById('content'));
    }
    return [page];
}

var pp = new PagePromise(select_components, state_defaults);

if (window) {
    pp.wire_events();
}
