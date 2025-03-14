"use strict";
/*jslint plusplus: true, nomen: true */
/*global Promise */
var test = require('tape');
var proxyquire =  require('proxyquire');

var last_saved = {};

var filesystem = proxyquire.noCallThru().load('lib/filesystem.js', {
    'file-saver': {
        saveAs: function (blob, filename) {
            last_saved = {
                filename: filename,
                type: blob.type,
                content: blob.arr,
            };
        },
    },
});



test('file_to_state', function (t) {
    global.window.location = { pathname: 'ut-path' };
    global.Blob = function (blob_arr, type) {
        this.arr = blob_arr;
        this.type = type;
    };

    // JSON is read ~as-is
    t.deepEqual(filesystem.file_to_state('{ "doc": "/flexiconc", "args": {"a": 1}, "state": {"b": 2} }'), {
        "doc": "/flexiconc",
        "args": {"a": 1},
        "state": {"b": 2},
    });

    t.end();
});


test('save', function (t) {
    global.window.location = { pathname: 'ut-path' };
    global.Blob = function (blob_arr, type) {
        this.arr = blob_arr;
        this.type = type;
    };

    // Each line of the CSV is a separate entry in the Blob
    filesystem.save([
        ['There were "five" carrots', 'left in the bag'],  // Quotes escaped
        ['a', 'b\n\nc\nd'],  // Paragraphs escaped to ¶
    ]);
    t.deepEqual(last_saved, {
        filename: 'ut-path.csv',
        type: { type: 'text/csv;charset=utf-8' },
        content: [
            // Quotes within values get escaped
            '"There were ""five"" carrots","left in the bag"\r\n',
            // End-paragraphs get a ¶, just newlines are ignored
            '"a","b¶ c d"\r\n',
        ],
    });

    t.end();
});
