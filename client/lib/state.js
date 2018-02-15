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
    return Object.keys(obj).sort().map(function (k) {
        if (Array.isArray(obj[k])) {
            return obj[k].map(function (v) {
                return (k === "#" ? '' : encodeURIComponent(k) + '=') + encodeURIComponent(v);
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
    var k;

    this.defaults = { '#': [] };
    if (defaults) {
        for (k in defaults) {
            if (defaults.hasOwnProperty(k)) {
                this.defaults[k] = defaults[k];
            }
        }
    }

    this._doc = win.location.pathname;
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
        return this.arg('#');
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
    var querystring = obj_to_search(this._args);

    if (querystring) {
        querystring = '?' + querystring;
    }

    return [
        this._state,
        "",
        this._doc + querystring,
    ];
};

/**
  * Update page state
  * - changes: Object containing any of the following optional items:
  *   - doc: New document path, if it should change
  *   - args: New querystring arguments
  *   - state: New state arguments
  *   - url: Shortcut, replaces doc/args with parsed URL before proceeding
  * - flush: Replaces args/state rather than merging with existing
  * returns true iff the changes result in a different state
  */
State.prototype.update = function (changes, flush) {
    var self = this,
        parts,
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

    if (changes.url) {
        parts = changes.url.split('?');
        changes.doc = parts[0];
        changes.args = search_to_obj(parts[1] || "");
    }

    if (changes.doc && changes.doc !== self._doc) {
        self._doc = changes.doc;
        modified = true;
    }

    if (flush) {
        if (changes.args) { this._args = changes.args; }
        if (changes.state) { this._state = changes.state; }
        return true;
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

module.exports = State;
