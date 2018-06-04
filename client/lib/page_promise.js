"use strict";
/*jslint todo: true, regexp: true, browser: true */
/*global Promise */
var State = require('./state.js');
var Alerts = require('./alerts.js');

/* Some kind of page navigation event has occured, do any state updating and re-render page if necessary */
function state_event(mode, e) {
    // NB: Wait for current_promise before we do anything, further calls then
    // wait for us. This serialises rapid link-pressing
    this.current_promise = this.current_promise.then(function () {
        var modified,
            comp_fn = 'reload',
            page_state = new State(window, this.state_defaults);

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

        return modified ? this.page_load(Promise.resolve(page_state), comp_fn) : null;
    }.bind(this));
}

function PagePromise(select_components, state_defaults) {
    this.select_components = select_components;
    this.state_defaults = state_defaults;
    this.current_promise = Promise.resolve();
}

/** Attach our events to the main window */
PagePromise.prototype.wire_events = function () {
    this.alerts = new Alerts(window.document.getElementById('alerts'));

    window.document.addEventListener('DOMContentLoaded', state_event.bind(this, 'initial'));
    window.addEventListener('popstate', state_event.bind(this, 'initial'));
    window.addEventListener('state_tweak', state_event.bind(this, 'tweak'));
    window.addEventListener('state_update', state_event.bind(this, 'update'));
    window.addEventListener('state_new', state_event.bind(this, 'new'));
};

PagePromise.prototype.page_load = function (p, comp_fn) {
    var self = this;

    return p.then(function (page_state) {
        var page_components = self.select_components(page_state);

        self.alerts.clear();
        document.body.classList.add('loading');

        return Promise.all(page_components.map(function (x) {
            var fn = x[comp_fn] || function () { return Promise.resolve({}); };

            return (fn.call(x, page_state)).catch(function (err) {
                // Turn any error output back into a level: { message: ... } object
                var rv = { a: self.alerts.err_to_alert(err) };
                if (rv.a[1] === 'error') { console.error(err); }

                rv[rv.a[1]] = rv.a[0];
                return rv;
            });
        })).then(function (rvs) {
            // Trigger post-load actions with main data
            page_components.map(function (x) {
                if (rvs[0] && x.new_data) {
                    x.new_data(rvs[0]);
                }
            });
            return rvs;
        });
    }).then(function (rvs) {
        rvs.forEach(function (rv) {
            if (rv && rv.info) { self.alerts.show(rv.info, 'info'); }
            if (rv && rv.warn) { self.alerts.show(rv.warn, 'warn'); }
            if (rv && rv.error) { self.alerts.show(rv.error, 'error'); }
        });

        document.body.classList.remove('loading');
    }).catch(function (err) {
        self.alerts.error(err);
        console.error(err);
        document.body.classList.remove('loading');
    });
};


module.exports = PagePromise;
