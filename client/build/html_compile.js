"use strict";
/*jslint todo: true, regexp: true, plusplus: true */
/*global Promise */
var fs = require('fs');
var path = require('path');
var nunjucks = require('nunjucks');

/** Return path/dir/base name for path (p), optionally stripping (ext) */
function path_forms(p, ext) {
    return {
        path: p,
        dir: path.dirname(p),
        base: path.basename(p, ext),
    };
}

/////////////////////////////

if (process.argv.length < 3) {
    throw new Error([
        "Usage:",
        process.argv[0],
        "(template file path)",
        "(output file path)",
    ].join(" "));
}

Promise.resolve({
    tmpl: path_forms(process.argv[2], '.html'),
    output: path_forms(process.argv[3]),
    env: process.env,
}).then(function (context) {
    var out = nunjucks.render(context.tmpl.path, context);

    return new Promise(function (resolve) {
        fs.writeFile(context.output.path, out, function (err) {
            if (err) {
                throw err;
            }
            resolve(out);
        });
    });
});
