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

function State(win, use_hash) {
    this.win = win;
    this._args = search_to_obj(use_hash ? win.location.hash.replace(/^\#!?/, '') : win.location.search.replace(/^\?/, ''));
    this._use_hash = use_hash;
}

State.prototype.doc = function () {
    return this.win.location.pathname.replace(/^.*\//, '/');
};

/** Fetch named a named argument (i.e. querystring), or all positional args */
State.prototype.arg = function (name, def) {
    if (!name) {
        return this.args('#', []);
    }
    if (Array.isArray(def)) {
        return this._args[name] || def;
    }
    return (this._args[name] || []).join("") || def;
};

/** Fetch key out of window.history.state object */
State.prototype.state = function (name, def) {
    return (this.win.history.state || {})[name] || def;
};

/**
  * Update page state
  * - changes: contains some of doc,args,state to change
  * - notify: 'silent', 'force' or nothing, in which case it compares first
  * Returns true iff the state is different to before
  */
State.prototype.update = function (changes, notify) {
    var self = this,
        new_doc = self.doc(),
        new_args = self._args,
        hist_state = this.win.history.state || {},
        modified = false;

    if (changes.hasOwnProperty('doc') && changes.doc !== self._doc) {
        self._doc = changes.doc;
        modified = true;
    }
    Array.prototype.forEach.call(Object.keys(changes.args || {}), function (k) {
        if (changes.args.hasOwnProperty(k) && JSON.stringify(changes.args[k]) !== JSON.stringify(new_args[k])) {
            new_args[k] = changes.args[k];
            modified = true;
        }
    });
    Array.prototype.forEach.call(Object.keys(changes.state || {}), function (k) {
        if (changes.state.hasOwnProperty(k) && JSON.stringify(changes.state[k]) !== JSON.stringify(hist_state[k])) {
            hist_state[k] = changes.state[k];
            modified = true;
        }
    });

    self.win.history.replaceState(hist_state, "", new_doc + '?' + obj_to_search(new_args));
    if (notify === 'force' || (!notify && modified)) {
        self.win.dispatchEvent(new self.win.CustomEvent('replacestate'));
    }

    return modified;
};

/**
  * Create a new page state in history
  * new_state: contains some of doc,args,state to change
  * - notify: 'silent', or nothing, in which case it notifies
  */
State.prototype.new = function (new_state, notify) {
    this.win.history.pushState(
        new_state.state || {},
        "",
        (new_state.doc || '') + '?' + obj_to_search(new_state.args || {})
    );
    if (notify !== 'silent') {
        this.win.dispatchEvent(new this.win.CustomEvent('replacestate'));
    }
};

module.exports = State;
