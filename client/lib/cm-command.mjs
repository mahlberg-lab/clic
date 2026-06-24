// NB: Use require() so we pull the same copy as page_text.js
const cmView = require('@codemirror/view');
const cmCommands = require('@codemirror/commands');
const cm_apply_typopo = require('./cm-apply-typopo.mjs');
const cm_insert_quotation = require('./cm-insert-quotation.mjs');

const ViewPlugin = cmView.ViewPlugin;

const COMMANDS = {
    undo: cmCommands.undo,
    redo: cmCommands.redo,
    'apply-typopo': cm_apply_typopo.apply_typopo,
    'insert-quotation': cm_insert_quotation.insert_quotation,
};

/**
  * Dispatch a cm-command request at the given EventTarget (typically window).
  * name must be a key of COMMANDS above. Any extra args are passed to the command
  * after the view.
  */
export function dispatch(target, name, args) {
    target.dispatchEvent(new CustomEvent('cm-command', {
        detail: { name: name, args: args || [] },
    }));
}

export const cm_command_plugin = ViewPlugin.fromClass(class {
    constructor(view) {
        this.view = view;
        this.handler = e => {
            const cmd = COMMANDS[e.detail.name];
            if (!cmd) {
                throw new Error("Unknown cm-command: " + e.detail.name);
            }

            cmd(this.view, ...(e.detail.args || []));
        };

        globalThis.addEventListener('cm-command', this.handler);
    }

    destroy() {
        globalThis.removeEventListener('cm-command', this.handler);
    }
});
