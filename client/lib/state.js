"use strict";
/*jslint todo: true, regexp: true, nomen: true */

function search_to_obj(search) {
    var out = {};
    search.split(/;|&/).filter(function (str) {
        // Remove empty entries from an empty search/hash
        return str.length > 0;
    }).map(function (str) {
        var m = /(.*?)\=(.*)/.exec(str);

        if (!m) {
            // No key, so add it to a special "#" key.
            m = [null, '#', str];
        }

        if (!out[m[1]]) {
            out[m[1]] = [];
        }
        out[m[1]].push(decodeURIComponent(m[2]));
    });

    return out;
}

function obj_to_search(obj) {
    return Object.keys(obj).map(function (k) {
        if (Array.isArray(obj[k])) {
            return obj[k].map(function (v) {
                return encodeURIComponent(k) + '=' + encodeURIComponent(v);
            }).join('&');
        }
        return encodeURIComponent(k) + '=' + encodeURIComponent(obj[k]);
    }).join('&');
}

function State(win, defaults) {
    this.win = win;
    this.defaults = defaults;
    this._args = search_to_obj(win.location.search.replace(/^\?/, ''));
}

State.prototype.doc = function () {
    return this.win.location.pathname.replace(/^.*\//, '/');
};

/** Fetch named a named argument (i.e. querystring), or all positional args */
State.prototype.arg = function (name) {
    if (!name) {
        return this.args('#', []);
    }

    if (!this.defaults.hasOwnProperty(name)) {
        throw new Error("Unknown arg " + name);
    }

    if (Array.isArray(this.defaults[name])) {
        return this._args[name] || this.defaults[name];
    }
    return this._args.hasOwnProperty(name) ? (this._args[name] || []).join("") : this.defaults[name];
};

/** Fetch key out of window.history.state object */
State.prototype.state = function (name) {
    if (!this.defaults.hasOwnProperty(name)) {
        throw new Error("Unknown state variable " + name);
    }

    return (this.win.history.state || {})[name] || this.defaults[name];
};

/**
  * Update page state
  * - changes: contains some of doc,args,state to change
  * returns true iff the changes result in a different state
  */
State.prototype.update = function (changes) {
    var self = this,
        new_doc = self.doc(),
        new_args = self._args,
        hist_state = this.win.history.state || {},
        modified = false;

    function compare(existing, change) {
        if (existing === undefined) {
            // An empty array is a missing item in URL speak
            existing = [];
        }

        if (JSON.stringify(change) !== JSON.stringify(existing)) {
            return false;
        }
        return true;
    }

    if (changes.hasOwnProperty('doc') && changes.doc !== self._doc) {
        self._doc = changes.doc;
        modified = true;
    }
    Array.prototype.forEach.call(Object.keys(changes.args || {}), function (k) {
        if (!compare(new_args[k], changes.args[k])) {
            new_args[k] = changes.args[k];
            modified = true;
        }
    });
    Array.prototype.forEach.call(Object.keys(changes.state || {}), function (k) {
        if (!compare(hist_state[k], changes.state[k])) {
            hist_state[k] = changes.state[k];
            modified = true;
        }
    });

    self.win.history.replaceState(
        hist_state || {},
        "",
        new_doc + '?' + obj_to_search(new_args || {})
    );
    return modified;
};

/**
  * Create a new page state in history
  * new_state: contains some of doc,args,state to change
  */
State.prototype.new = function (new_state) {
    this.win.history.pushState(
        new_state.state || {},
        "",
        new_state.url || ((new_state.doc || '') + '?' + obj_to_search(new_state.args || {}))
    );
};

State.prototype.alter = function (event_type, changes) {
    if (event_type === "new") {
        this.new(changes);
        return true;
    }
    if (event_type === "alter") {
        this.update(changes);
        return false;
    }
    if (event_type === "update") {
        return this.update(changes);
    }
    throw new Error("Unknown state event type " + event_type);
};

module.exports = State;
