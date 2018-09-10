"use strict";
/*jslint todo: true, regexp: true, browser: true, unparam: true, plusplus: true */
/*global Promise */
var api = require('./api.js');
var gen_carousel = require('lib/carousel.js').gen_carousel;

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

    return api.get('corpora/headlines').then(function (data) {
        function gen_carousel_item(d) {
            return [
                '<li style="background-image: url(/carousel-images/' + d.id + '_0.4.jpg)"><a href="/concordance?corpora=' + d.id + '">',
                '  <h3>' + d.title + '</h3>',
                '  <strong>' + d.book_count.toLocaleString() + '</strong> books,<br/>',
                '  <strong>' + d.word_count.toLocaleString() + '</strong> total words</a>',
                '</li>',
            ].join("\n");
        }

        self.content_el.innerHTML =
            '<div class="clic-contents">' +
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

        // Add carousel to top of clic-contents
        self.content_el.firstChild.insertBefore(
            gen_carousel(data.data.map(gen_carousel_item), 5),
            self.content_el.firstChild.firstChild
        );
    });

};

module.exports = PageContents;
