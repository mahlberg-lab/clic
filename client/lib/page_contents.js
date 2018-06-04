"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var jQuery = require('jquery/dist/jquery.slim.js');
var api = require('./api.js');

function escapeHTML(s) {
    return new Option(s).innerHTML;
}

function PageContents(content_el) {
    this.content_el = content_el;
}

PageContents.prototype.page_title = function (page_state) {
    return "CLiC";
};

PageContents.prototype.reload = function reload(page_state) {
    var self = this;

    return Promise.resolve().then(function () {
        self.content_el.innerHTML =
            '<div class="clic-contents">' +
            '<p>Welcome to CLiC. The CLiC web app has been developed as part of the <a href="https://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic/index.aspx">CLiC Dickens project</a>, ' +
            'which demonstrates through corpus stylistics how computer-assisted methods can be used to study literary texts and lead to new insights into how readers perceive fictional characters.</p>' +
            '<p>Please choose a function in the control bar to the right (click the icon in the top right if it is not displayed).</p>' +
            '<div>' +
            '</div></div>';
    });

};

module.exports = PageContents;
