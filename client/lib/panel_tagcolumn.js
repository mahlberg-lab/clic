"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */

function choose_name(tag_columns, base_tag_name) {
    var new_tag_name,
        i = 1;

    // Purely numeric tag names confuse datatables, so avoid them.
    if (base_tag_name.match('^[0-9]+$')) {
        base_tag_name = 'n' + base_tag_name;
    }
    new_tag_name = base_tag_name;

    while (tag_columns[new_tag_name]) {
        new_tag_name = base_tag_name + "-" + i++;
    }
    return new_tag_name;
}

function PanelTagColumns(panel_el) {
    var self = this;

    self.panel_el = panel_el;
    self.taglist_el = panel_el.querySelector('ul.tag-list');
    self.rename_el = panel_el.querySelector("input[name='tag-column-rename']");

    // The new tag selection has changed
    self.taglist_el.addEventListener('click', function (e) {
        if (e.target.tagName !== 'LI') {
            return;
        }
        Array.prototype.forEach.call(e.target.parentNode.children, function (tag_el) {
            tag_el.classList.toggle('selected', tag_el === e.target);
        });
        self.rename_el.value = e.target.innerText;
        self.rename_el.select();
        self.page_state.update({state: {tag_column_selected: e.target.innerText}}, 'silent');
    });

    // The tag has been renamed
    self.rename_el.addEventListener('change', self.do.bind(self, 'rename'));
    self.panel_el.querySelector("button[name='tag-column-add']").addEventListener('click', self.do.bind(self, 'add'));
    self.panel_el.querySelector("button[name='tag-column-delete']").addEventListener('click', self.do.bind(self, 'delete'));
}

PanelTagColumns.prototype.do = function (action, e) {
    var self = this,
        tag_columns = self.page_state.state('tag_columns'),
        tag_column_order = self.page_state.state('tag_column_order'),
        tag_column_selected = self.page_state.state('tag_column_selected'),
        new_tag_name;

    e.preventDefault();
    e.stopPropagation();

    // Clone tag columns
    tag_columns = JSON.parse(JSON.stringify(tag_columns));

    if (action === 'add') {
        new_tag_name = choose_name(tag_columns, 'new-tag');
        tag_columns[new_tag_name] = {};
        tag_column_order = tag_column_order.concat([new_tag_name]);

    } else if (action === 'delete') {
        if (!tag_column_selected) {
            return;
        }
        if (!window.confirm("Removing the tag '" + tag_column_selected + "' will lose any information it stores. Are you sure?")) {
            return;
        }
        delete tag_columns[tag_column_selected];
        tag_column_order = tag_column_order.filter(function (t) {
            return t !== tag_column_selected;
        });

    } else if (action === 'rename') {
        new_tag_name = choose_name(tag_columns, e.target.value.toLowerCase().replace(/\W/g, "-"));
        if (!tag_column_selected) {
            return;
        }
        tag_columns[new_tag_name] = tag_columns[tag_column_selected];
        delete tag_columns[tag_column_selected];
        tag_column_order = tag_column_order.map(function (t) {
            return t === tag_column_selected ? new_tag_name : t;
        });
    }

    self.page_state.update({state: {
        tag_columns: tag_columns,
        tag_column_order: tag_column_order,
        tag_column_selected: '',
    }});
};

// Refresh controls based on page_state
PanelTagColumns.prototype.reload = function reload(page_state) {
    var self = this,
        tag_column_order = page_state.state('tag_column_order'),
        tag_column_selected = page_state.state('tag_column_selected');

    self.page_state = page_state;

    // Recreate all list items
    self.rename_el.value = '';
    self.taglist_el.innerHTML = tag_column_order.map(function (tag) {
        var item_class = '';

        if (tag === tag_column_selected) {
            item_class = 'selected';
            self.rename_el.value = tag;
            self.rename_el.select();
        }

        return '<li tabindex="0" class="' + item_class  + '">' + (new Option(tag).innerHTML) + '</li>';
    }).join("");
};

module.exports = PanelTagColumns;
