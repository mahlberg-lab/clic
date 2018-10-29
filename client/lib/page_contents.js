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
        var carousel_el = self.content_el.querySelector('#content > .clic-contents > .carousel');

        function gen_carousel_item(d) {
            return [
                '<li style="background-image: url(/api/corpora/image?corpora=' + encodeURIComponent(d.id) + '"><a href="/concordance?corpora=' + d.id + '">',
                '  <h3>' + d.title + '</h3>',
                '  <strong>' + d.book_count.toLocaleString() + '</strong> books,<br/>',
                '  <strong>' + d.word_count.toLocaleString() + '</strong> total words</a>',
                '</li>',
            ].join("\n");
        }

        if (carousel_el) {
            // Replace carousel placeholder with a real carousel
            carousel_el.parentNode.replaceChild(
                gen_carousel(data.data.map(gen_carousel_item), 5),
                carousel_el
            );
        } else {
            // Reload page properly so clic-contents is available
            window.location.reload();
        }
    });

};

module.exports = PageContents;
