"use strict";
var crypto = require('crypto');
var fs = require('fs');
var path = require('path');
var cheerio = require('cheerio');

function file_hash(file_path) {
    return new Promise(function (resolve) {
        var hash = crypto.createHash('sha1'), 
            stream = fs.createReadStream(file_path);

        stream.on('data', function (data) {
            hash.update(data, 'utf8');
        })
        stream.on('end', function () {
            resolve(".r" + hash.digest('hex').substr(0, 7));
        });
    });
}

/////////////////////////////

return new Promise(function (resolve) { 
    fs.readFile(process.argv[2], 'utf8', function(err, data) {
        if (err) {
            throw err;
        }
        resolve(data);
    });
}).then(function (html_string) {
    var $ = cheerio.load(html_string);

    return Promise.all($("link[rel=stylesheet],script").toArray().map(function (el) {
        var attr = el.tagName === 'script' ? 'src' : 'href';

        return file_hash("www/" + $(el).attr(attr)).then(function (hash) {
            $(el).attr(attr, $(el).attr(attr) + hash);
        });
    })).then(function () {
        process.stdout.write($.html());
    });
});