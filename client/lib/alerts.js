"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */

function Alerts(alert_el) {
    this.alert_el = alert_el;
}

Alerts.prototype.clear = function () {
    this.alert_el.innerHTML = "";
};

Alerts.prototype.show = function (msg, level) {
    // If handed an array, display all of them
    if (Array.isArray(msg)) {
        return msg.forEach(this.show.bind(this));
    }

    // Escape HTML if necessary
    if (!msg.is_html) {
        msg.message = '<div>' + new Option(msg.message).innerHTML + '</div>';
    }

    // Append any stack output
    if (msg.stack) {
        msg.message += '<pre>' + new Option(msg.stack).innerHTML + '</pre>';
    }

    // Append to output
    this.alert_el.insertAdjacentHTML(
        'beforeend',
        '<div class="level-' + (level || 'info') + '">' + msg.message + '</div>'
    );
};

/* Convert an error object into an alert / level pair */
Alerts.prototype.err_to_alert = function (err) {
    return [
        { message: err.message, stack: err.stack },
        err.level || 'error',
    ];
};

/* Convert an error into a message, and show it */
Alerts.prototype.error = function (err) {
    return this.show.apply(this, this.err_to_alert(err));
};

/* Error class to use for throwing styled errors */
Alerts.prototype.DisplayError = function (message, level) {
    this.message = message;
    this.level = level;
    this.stack = null; // We don't need a stack trace, these errors are ~expected
};
Alerts.prototype.DisplayError.prototype = Error.prototype;

module.exports = Alerts;
