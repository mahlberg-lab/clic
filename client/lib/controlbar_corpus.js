"use strict";
var api = require('./api.js');
var ControlBar = require('./controlbar.js');
var chosen_init = require('./chosen_init.js');
var bfa = require('browser-fs-access');
var Papa = require('papaparse');

const ALL_REGIONS = [
    'metadata.title',
    'metadata.author',
    'chapter.part',
    'chapter.title',
    'chapter.sentence',
    'quote.quote',
    'quote.suspension.short',
    'quote.suspension.long',
    'quote.embedded',
];

// ControlBarCorpus inherits ControlBar
function ControlBarCorpus(control_bar) {
    var self = this;

    // The book selector isn't part of the form, we just use it to trigger a file load
    self.recordEventListener(document.getElementById("ctlb-corpus-book"), "change", function (event) {
        event.preventDefault();
        event.stopPropagation();

        self.load_from_clic(event.target.value);
        event.target.selectedIndex = -1;
        chosen_init.refresh(event.target);
    });

    return ControlBar.apply(this, arguments);
}
ControlBarCorpus.prototype = Object.create(ControlBar.prototype);

ControlBarCorpus.prototype.load_from_clic = function (book) {
    return api.get('text', {corpora: book, regions: ALL_REGIONS}).then(function (data) {
        window.dispatchEvent(new window.CustomEvent('state_new', { detail: {
            state: {
                "corpus-filename": book + ".txt",
                "corpus-content": data.content,
                "corpus-regions": data.data,
            },
        }}));
    });
};

ControlBarCorpus.prototype.load_from_file = function () {
    return bfa.fileOpen({
        id: "clic-page-corpus-download-file",
        startIn: "downloads",
    }).then(file => {
        return file.text().then(content => ({content: content, filename: file.name}));
    }).then(function (dat) {
        window.dispatchEvent(new window.CustomEvent('state_new', { detail: {
            state: {
                "corpus-filename": dat.filename,
                "corpus-content": dat.content,
                "corpus-regions": ["__recalc"], // NB: Sentinel value page_corpus listens for
            },
        }}));
    }).catch(function (err) {
        if (err.name === 'AbortError') {
            // User pressed cancel, nothing to do
            return;
        }
        throw err;
    });
};

ControlBarCorpus.prototype.save_content = function (page_state) {
    const utf8encoder = new TextEncoder();
    const blob = new Blob(
        [utf8encoder.encode(page_state.state("corpus-content"))],
        {type: "text/plain"},
    );
    const filename = page_state.state("corpus-filename");

    return bfa.fileSave(blob, {
        id: "clic-cm-download-file",
        fileName: filename,
        startIn: "downloads",
    });
};

ControlBarCorpus.prototype.save_regions = function (page_state) {
    var csv, blob;

    csv = Papa.unparse(page_state.state('corpus-regions'), { newline: '\r\n' });

    // Prepend a UTF-8 BOM so Excel opens the file as Unicode
    blob = new Blob([Papa.BYTE_ORDER_MARK + csv], { type: "text/csv" });
    return bfa.fileSave(blob, { fileName: page_state.state("corpus-filename") + '.regions.csv' });
};

module.exports = ControlBarCorpus;
