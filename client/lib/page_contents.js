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
        var clic_contents_el = self.content_el.querySelector('#content > .clic-contents');

        function gen_carousel_item(d) {
            return [
                '<li style="background-image: url(/carousel-images/' + d.id + '_0.4.jpg)"><a href="/concordance?corpora=' + d.id + '">',
                '  <h3>' + d.title + '</h3>',
                '  <strong>' + d.book_count.toLocaleString() + '</strong> books,<br/>',
                '  <strong>' + d.word_count.toLocaleString() + '</strong> total words</a>',
                '</li>',
            ].join("\n");
        }

        if (clic_contents_el) {
            // Add carousel to top of clic-contents
            clic_contents_el.insertBefore(
                gen_carousel(data.data.map(gen_carousel_item), 5),
                clic_contents_el.firstChild
            );
        } else {
            // Reload page properly so clic-contents is available
            window.location.reload();
        }
    });

};

module.exports = PageContents;
