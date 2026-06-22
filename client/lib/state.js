"use strict";
/*jslint todo: true, regexp: true, unparam: true, nomen: true */
/*global globalThis */

function search_to_obj(search) {
    var out = {};
    search.split(/;|&/).filter(function (str) {
        // Remove empty entries from an empty search/hash
        return str.length > 0;
    }).map(function (str) {
        var k, m = /(.*?)\=(.*)/.exec(str);

        if (!m) {
            // No key, so add it to a special "#" key.
            m = [null, '#', str];
        }
        k = decodeURIComponent(m[1]);

        if (!out[k]) {
            out[k] = [];
        }
        out[k].push(decodeURIComponent(m[2]));
    });

    return out;
}

function obj_to_search(obj) {
    return Object.keys(obj).sort().map(function (k) {
        if (Array.isArray(obj[k])) {
            return obj[k].map(function (v) {
                return (k === "#" ? '' : k + '=') + encodeURIComponent(v);
            }).join('&');
        }
        return k + '=' + encodeURIComponent(obj[k]);
    }).filter(function (s) { return !!s; }).join('&');
}

/**
  * Create a new state object based on the current page
  * - win: Global window object / previous state
  * - defaults: Object containing defaults for args & state (if above isn't a previous state)
  */
function State(win, defaults) {
    var k;

    // Handed a previous object, clone all properties and use that
    if (win instanceof State) {
        this.defaults = JSON.parse(JSON.stringify(win.defaults));
        this._doc = JSON.parse(JSON.stringify(win._doc));
        this._state = JSON.parse(JSON.stringify(win._state));
        this._args = JSON.parse(JSON.stringify(win._args));
        return;
    }

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

/** Fetch all available args, optionally filtered by a regex */
State.prototype.all_args = function (regex) {
    if (!regex) {
        return this._args;
    }
    regex = new RegExp(regex);
    return Object.keys(this._args).reduce(function (r, k) {
        if (regex.test(k)) {
            r[k] = this._args[k];
        }
        return r;
    }.bind(this), {});
};

/** Fetch named a named argument (i.e. querystring), or all positional args */
State.prototype.arg = function (name) {
    if (!name) {
        return this.arg('#');
    }

    if (name.match(/^\w+\[/)) {
        // Deep reference to arg, assume array-default
        return this._args[name] || [];
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
        this.to_url(),
    ];
};

/**
  * Turn the state object back into a URL string
  *
  * - regex: Optional regex, if provided only matching arguments will be included
  */
State.prototype.to_url = function (regex) {
    var querystring = obj_to_search(this.all_args(regex));

    if (querystring) {
        querystring = '?' + querystring;
    }

    return this._doc + querystring;
};

State.prototype.to_json = function () {
    return {
        doc: this._doc,
        args: this._args,
        state: this._state,
    };
};


/**
  * Update page state
  * - changes: Object containing any of the following optional items:
  *   - doc: New document path, if it should change
  *   - args: New querystring arguments
  *   - state: New state arguments
  *   - url: Shortcut, replaces doc/args with parsed URL before proceeding
  *   - flush: Synonym for flush argument
  * - flush: Replaces args/state rather than merging with existing
  * returns true iff the changes result in a different state
  */
State.prototype.update = function (changes, flush) {
    var self = this,
        parts,
        modified = false;

    function compare(existing, change) {
        function replacer(item_key, value) {
            if (value instanceof globalThis.Set) {
                // Sets don't stringify by default: https://stackoverflow.com/a/46491780
                return Array.from(value);
            }
            return value;
        }

        if (existing === undefined) {
            // An empty array is a missing item in URL speak
            existing = [];
        }

        if (JSON.stringify(change, replacer) !== JSON.stringify(existing, replacer)) {
            return false;
        }
        return true;
    }

    // Allow flush to be overriden in changes
    if (changes.flush) {
        flush = changes.flush;
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

/**
  * Return a clone of this state object, optionally modified
  * - changes: As per update()
  * - flush: As per update()
  */
State.prototype.clone = function (changes, flush) {
    var new_state = new State(this);
    new_state.update(changes || {}, flush);
    return new_state;
};

module.exports = State;
