"use strict";
/*jslint todo: true, browser: true */
/*global Promise */

function Analytics() {
    return this;
}

/**
  * On reload, log the event in google
  */
Analytics.prototype.reload = function reload() {
    if (window.ga) {
        window.ga('set', 'location', window.location.href);
        window.ga('send', 'pageview');
    }

    return Promise.resolve({});
};

module.exports = Analytics;
