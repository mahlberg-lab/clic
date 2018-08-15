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
            '  <ul class="carousel">' +
            '    <li style="background-image: url(/carousel-images/dickens_0.4.jpg)"><a href="/concordance?corpora=dickens">' +
            '      <h3>DNov - Dickens\'s Novels</h3>' +
            '      <strong>15</strong> books,<br/>' +
            '      <strong>3,835,807</strong> total words</a>' +
            '    </li>' +
            '    <li style="background-image: url(/carousel-images/ntc_0.4.jpg)"><a href="/concordance?corpora=ntc">' +
            '      <h3>19C - 19th Century Reference Corpus</h3>' +
            '      <strong>29</strong> books,<br/>' +
            '      <strong>4,513,070</strong> total words</a>' +
            '    </li>' +
            '    <li style="background-image: url(/carousel-images/ChiLit_0.4.jpg)"><a href="/concordance?corpora=ChiLit">' +
            '      <h3>ChiLit - 19th Century Children\'s Literature Corpus</h3>' +
            '      <strong>71</strong> books,<br/>' +
            '      <strong>4,443,542</strong> total words' +
            '    </a></li>' +
            '    <li style="background-image: url(/carousel-images/Other_0.4.jpg)"><a href="/concordance?corpora=ChiLit">' +
            '      <h3>ArTs - Additional Requested Texts</h3>' +
            '      <strong>23</strong> books,<br/>' +
            '      <strong>2,259,103</strong> total words' +
            '    </a></li>' +
            '  </ul>' +
            '  <p><span class="first-letter">W</span><span class="first-sentence">elcome to CLiC.</span> The CLiC web app has been developed as part of the <a href="https://www.birmingham.ac.uk/schools/edacs/departments/englishlanguage/research/projects/clic/index.aspx">CLiC Dickens project</a>, which demonstrates through corpus stylistics how computer-assisted methods can be used to study literary texts and lead to new insights into how readers perceive fictional characters.</p>' +
            '  <p>Please choose a function in the control bar to the right (click the icon in the top right if it is not displayed).</p>' +
            '  <h2>Citing CLiC</h2>' +
            '  <p>When you use CLiC in your work, please cite this article:</p>' +
            '  <p><cite>' +
            '    Mahlberg, M., Stockwell, P., de Joode, J., Smith, C., &amp; O’Donnell, M. B. (2016).' +
            '    CLiC Dickens: Novel uses of concordances for the integration of corpus stylistics and cognitive poetics.' +
            '    Corpora, 11(3), 433–463.' +
            '  </cite></p>' +
            '  <p>If possible, please also include a link to <a href="https://clic.bham.ac.uk">clic.bham.ac.uk</a>.</p>' +
            '</div>';
    });

};

module.exports = PageContents;
