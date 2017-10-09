"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true */
/*global Promise */

function Alerts(alert_el) {
    this.alert_el = alert_el;
}

Alerts.prototype.clear = function () {
    this.alert_el.innerHTML = "";
};

Alerts.prototype.show = function (msg) {
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
        '<div class="level-' + (msg.level || 'info') + '">' + msg.message + '</div>'
    );
};

/* Convert an error into a message, and show it */
Alerts.prototype.error = function (err) {
    return this.show({
        level: err.level || 'error',
        message: err.message,
        stack: err.stack,
    });
};

/* Error class to use for throwing styled errors */
Alerts.prototype.DisplayError = function (message, level) {
    this.message = message;
    this.level = level;
};
Alerts.prototype.DisplayError.prototype = Error.prototype;

module.exports = Alerts;
