"use strict";
require("cookieconsent");  // NB: Creates window.cookieconsent

function ga() {
    if (!window.ga) {
        window.ga = function () {
            window.ga.q = window.ga.q || [];
            window.ga.q.push(arguments);
        };
        window.ga.l = +new Date();
    }

    window.ga.apply(null, arguments);
}

function statusEvent() {
    var el;

    if (this.hasConsented()) {
        if (!document.getElementById("script-google-analytics")) {
            el = document.createElement("script");
            el.setAttribute("id", "script-google-analytics");
            el.setAttribute("async", "");
            el.setAttribute("src", "https://www.google-analytics.com/analytics.js");

            document.body.appendChild(el);
        }
    } else {
        window.ga = null;

        el = document.getElementById("script-google-analytics");
        if (el) {
            el.remove();
        }
    }
}

function Analytics() {
    if (!window.ga_key) {
        return;
    }
    ga('create', window.ga_key, 'auto');

    // https://www.osano.com/cookieconsent/documentation/javascript-api/
    window.cookieconsent.initialise({
        content: {
            message: "We would like to use Google Analytics to help us improve our website, by collecting and reporting information on its usage.",
            href: 'https://clic.bham.ac.uk/TODO:',
            allow: 'Allow',
            deny: 'Decline',
        },
        type: "opt-in",
        palette: {
            popup: { background: "rgb(165, 183, 197)", text: "#333" },
            button: { background: "#f0ad4e", text: "#333" },
            link: { text: "#333" }
        },
        revokable: true,
        onInitialise: statusEvent,
        onStatusChange: statusEvent,
        law: {
            regionalLaw: false,
            countryCode: "DE",
        },
    });

    return this;
}

/**
  * On reload, log the event in google
  */
Analytics.prototype.reload = function reload() {
    ga('set', 'location', window.location.href);
    ga('send', 'pageview');

    return Promise.resolve({});
};

module.exports = Analytics;
