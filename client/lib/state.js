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

/**
  * Create a new state object based on the current page
  * - win: Global window object
  * - defaults: Object containing defaults for args & state
  */
function State(win, defaults) {
    this.defaults = defaults;
    this._doc = win.location.pathname.replace(/^.*\//, '/');
    this._state = win.history.state || {};
    this._args = search_to_obj(win.location.search.replace(/^\?/, ''));
}

/** Return the current document */
State.prototype.doc = function () {
    return this._doc;
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

    return this._state[name] || this.defaults[name];
};

/**
  * Turn the state object back into argument array that can be passed to
  * push/replaceState
  */
State.prototype.to_args = function () {
    return [
        this._state,
        "",
        this._doc + '?' + obj_to_search(this._args),
    ];
};

/**
  * Update page state
  * - changes: contains some of doc,args,state to change
  * returns true iff the changes result in a different state
  */
State.prototype.update = function (changes) {
    var self = this,
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
        if (!compare(self._args[k], changes.args[k])) {
            self._args[k] = changes.args[k];
            modified = true;
        }
    });

    Array.prototype.forEach.call(Object.keys(changes.state || {}), function (k) {
        if (!compare(self._state[k], changes.state[k])) {
            self._state[k] = changes.state[k];
            modified = true;
        }
    });

    return modified;
};

/**
  * Create a new page state in history
  * new_state: contains some of doc,args,state to change
  */
State.prototype.replace = function (new_state) {
    var parts;

    if (new_state.url) {
        parts = new_state.url.split('?');
        new_state.doc = parts[0];
        new_state.args = search_to_obj(parts[1] || "");
    }

    if (new_state.doc) { this._doc = new_state.doc; }
    if (new_state.args) { this._args = new_state.args; }
    if (new_state.state) { this._state = new_state.state; }
};

module.exports = State;
