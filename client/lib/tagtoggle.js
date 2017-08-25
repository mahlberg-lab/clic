"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */

function TagToggle(tag_name, tag_desc) {
    this.tag_name = tag_name;
    this.tag_desc = tag_desc || tag_name;
    this.base_class = 'tag-toggle ';
}

TagToggle.prototype.dom = function () {
    var child;

    if (!this.el) {
        this.el = document.createElement('DIV');
        this.el.className = this.base_class;
        this.el.setAttribute('data-tag', this.tag_name);
        this.el.innerText = this.tag_desc;
        this.el.addEventListener('click', this.click.bind(this));

        child = document.createElement('SPAN');
        child.setAttribute('tagindex', 0);
        child.className = 'yes';
        child.innerText = '✓';
        this.el.appendChild(child);

        child = document.createElement('SPAN');
        child.setAttribute('tagindex', 0);
        child.className = 'no';
        child.innerText = '✕';
        this.el.appendChild(child);
    }

    return this.el;
};

TagToggle.prototype.get = function (state) {
    return this.el.className.replace(this.base_class, '');
};

TagToggle.prototype.set = function (state) {
    this.el.className = this.base_class + state;
    return state;
};

TagToggle.prototype.click = function (e) {
    if (e.target.className === 'yes') {
        this.set('yes');
    } else if (e.target.className === 'no') {
        this.set('no');
    } else {
        return;
    }

    // Tell upstream about it
    this.onupdate(e.target.className);
};

TagToggle.prototype.update = function (data) {
    // Return yes/no/mix, depending if the tag is true/false/combination
    function rows_match_tag(d, tag) {
        var i, generally_true;

        if (d.length === 0) {
            return 'mix';
        }

        generally_true = !!d[0][tag];
        for (i = 1; i < d.length; i++) {
            if (d[i][tag] !== generally_true) {
                return 'mix';
            }
        }
        return generally_true ? 'yes' : 'no';
    }

    return this.set(rows_match_tag(data, this.tag_name));
};

module.exports = TagToggle;
