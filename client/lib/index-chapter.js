"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
require('./polyfill.js');
var api = require('./api.js');
var Alerts = require('./alerts.js');
var State = require('./state.js');

var state_defaults = {
    'start': 0,
    'end': 0,
    'chapter_id': 0,
};

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
        var self = this,
            chapter_id = page_opts.arg('chapter_id');

        if (!chapter_id) {
            throw new Error("No chapter ID provided");
        }

        return api.get('chapter', {chapter_id: chapter_id}).then(function (doc) {
            content_el.appendChild(doc.documentElement);
            self.highlight(page_opts);
        });
    };
}

var page;

function page_load(e) {
    var page_state = new State(window, state_defaults),
        alerts = new Alerts(document.getElementById('alerts'));

    return Promise.resolve(page_state).then(function (page_state) {
        alerts.clear();

        if (!page || page_state.doc()) {
            page = new Chapter(document.getElementById('content'));
        }

        return Promise.all([
            page.reload(page_state),
        ]);
    }).then(function (rvs) {
        rvs.forEach(function (rv) {
            if (rv && rv.message) {
                alerts.show(rv.message);
            }
        });
        return;
    }).catch(function (err) {
        alerts.error(err);
        if (!err.level) {
            throw err;
        }
    });
}

if (window) {
    document.addEventListener('DOMContentLoaded', page_load);
    window.addEventListener('popstate', page_load);
}
