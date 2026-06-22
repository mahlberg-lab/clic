"use strict";
var test = require('tape');
var proxyquire =  require('proxyquire');
var Papa = require('papaparse');

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


var example_csv = [
    'ID,,Left,Node,Right,Book,In bk.,tag:bling,tag:bleu,f25a738,https://clic-fiction.com/concordance?conc-q=cloud%20*%20on&conc-subset=all&conc-type=whole&corpora=corpus%3ADNov&kwic-span=-5%3A5&table-filter=&table-type=basic',
    'DC:622085:622102,"cloud, ,lowering, ,on,0,2,4",seemed to have left the Doctor\'s roof with a dark ,cloud lowering on, it. The reverence that I had for his grey head,DC,622085/1937052,✓,✓,,',
    'OMF:424624:424636,"cloud,, ,so, ,on,0,2,4",business. ¶ As on the Secretary\'s face there was a nameless ,"cloud, so on", his manner there was a shadow equally indefinable. It was,OMF,424624/1818145,✓,✓,,',
    'TTC:54361:54377,"cloud, ,settled, ,on,0,2,4",would be red upon many there. ¶ And now that the ,cloud settled on," Saint Antoine, which a momentary gleam had driven from his",TTC,54361/758806,✓, ,,',
].join('\n');

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

    // CSV headers are parsed for tag columns; the query part of the URL is preserved
    t.deepEqual(filesystem.file_to_state(example_csv), {
        url: '/concordance?conc-q=cloud%20*%20on&conc-subset=all&conc-type=whole&corpora=corpus%3ADNov&kwic-span=-5%3A5&table-filter=&table-type=basic',
        state: {
            tag_columns: {
                // Only rows with a non-whitespace tag value are recorded
                bling: {
                    'DC:622085:622102': true,
                    'OMF:424624:424636': true,
                    'TTC:54361:54377': true,
                },
                bleu: {
                    'DC:622085:622102': true,
                    'OMF:424624:424636': true,
                },
            },
            tag_column_order: ['bling', 'bleu'],
        },
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
    last_saved.content = last_saved.content.join("").split("\r\n");
    t.deepEqual(last_saved, {
        filename: 'ut-path.csv',
        type: { type: 'text/csv;charset=utf-8' },
        content: [
            // Leading UTF-8 BOM so Excel opens as Unicode; quotes within values get escaped
            Papa.BYTE_ORDER_MARK + '"There were ""five"" carrots",left in the bag',
            // End-paragraphs get a ¶, just newlines are ignored
            'a,b¶ c d',
        ],
    });

    t.end();
});
