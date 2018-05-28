"use strict";
/*jslint todo: true, regexp: true, browser: true */
/*global Promise */
var State = require('./state.js');
var ControlBar = require('./controlbar.js');
var Alerts = require('./alerts.js');
var Analytics = require('./analytics.js');

var page_classes = {
    '/concordance': require('./page_concordance.js'),
    '/clusters': require('./page_cluster.js'),
    '/subsets': require('./page_subset.js'),
    '/keywords': require('./page_keyword.js'),
    '/': require('./page_contents.js'),
    '': function () {
        this.page_title = function () {
            return "Page not found";
        };
        this.reload = function (page_state) {
            throw new Error("Unknown page: " + page_state.doc());
        };
    },
};

var state_defaults = {
    'corpora': [],
    'conc-subset': 'all',
    'conc-q': '',
    'conc-type': 'whole',
    'subset-subset': '',
    'kwic-span': '-5:5',
    'kwic-dir': 'start',
    'kwic-int-start': '3',
    'kwic-int-end': '3',
    'kwic-terms': [],
    'refcorpora': [],
    'subset': '',
    'refsubset': '',
    'clusterlength': 1,
    'pvalue': '0.0001',

    'tag_columns': {},
    'tag_column_order': [],
    'tag_column_selected': '',

    'table-type': 'basic',
    'table-filter': '',
    'selected_rows': [],
};

var page, cb, ga, alerts, current_page = null,
    current_promise = Promise.resolve();

function page_components(page_state) {
    var PageConstructor;

    if (!page || page_state.doc() !== current_page) {
        PageConstructor = page_classes[page_state.doc()] || page_classes[''];
        page = new PageConstructor(document.getElementById('content'));
        current_page = page_state.doc();
    }

    if (!cb) {
        cb = new ControlBar(document.getElementById('control-bar'));
    }

    if (!ga) {
        ga = new Analytics();
    }

    window.document.title = page.page_title(page_state);
    return [page, cb, ga];
}

function page_load(p, comp_fn) {
    return p.then(function (page_state) {
        alerts.clear();
        document.body.classList.add('loading');

        return Promise.all(page_components(page_state).map(function (x) {
            var fn = x[comp_fn] || function () { return Promise.resolve({}); };

            return (fn.call(x, page_state)).catch(function (err) {
                // Turn any error output back into a level: { message: ... } object
                var rv = { a: alerts.err_to_alert(err) };

                rv[rv.a[1]] = rv.a[0];
                return rv;
            });
        }));
    }).then(function (rvs) {
        rvs.forEach(function (rv) {
            if (rv && rv.info) { alerts.show(rv.info, 'info'); }
            if (rv && rv.warn) { alerts.show(rv.warn, 'warn'); }
            if (rv && rv.error) { alerts.show(rv.error, 'error'); }
        });

        if (rvs[0]) {
            cb.new_data(rvs[0]);
        }
        document.body.classList.remove('loading');
    }).catch(function (err) {
        alerts.error(err);
        document.body.classList.remove('loading');
        throw err;
    });
}

/* Some kind of page navigation event has occured, do any state updating and re-render page if necessary */
function state_event(mode, e) {
    // NB: Wait for current_promise before we do anything, further calls then
    // wait for us. This serialises rapid link-pressing
    current_promise = current_promise.then(function () {
        var modified,
            comp_fn = 'reload',
            page_state = new State(window, state_defaults);

        if (mode === 'initial') {  // page load - we need to init page based on external state change
            modified = true;
        } else if (mode === 'tweak') { // Minor page update, call tweak instead of reload
            modified = page_state.update(e.detail);
            comp_fn = 'tweak';
            window.history.replaceState.apply(window.history, page_state.to_args());
        } else if (mode === 'update') { // Update state, update page to match (but break if no changes)
            modified = page_state.update(e.detail);
            window.history.replaceState.apply(window.history, page_state.to_args());
        } else if (mode === 'new') { // Push a new state (i.e. clicking a link)
            page_state.update(e.detail, true);
            modified = true;
            window.history.pushState.apply(window.history, page_state.to_args());
        } else {
            throw new Error("Unknown mode " + mode);
        }

        return modified ? page_load(Promise.resolve(page_state), comp_fn) : null;
    });
}

if (window) {
    alerts = new Alerts(document.getElementById('alerts'));

    document.addEventListener('DOMContentLoaded', state_event.bind(null, 'initial'));
    window.addEventListener('popstate', state_event.bind(null, 'initial'));
    window.addEventListener('state_tweak', state_event.bind(null, 'tweak'));
    window.addEventListener('state_update', state_event.bind(null, 'update'));
    window.addEventListener('state_new', state_event.bind(null, 'new'));
}
