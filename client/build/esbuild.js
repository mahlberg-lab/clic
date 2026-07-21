"use strict";
var esbuild = require('esbuild');

// Global on which library modules are exposed by the libraries bundle, so
// that the main bundle can resolve `require('jquery/...')` etc. at runtime.
// Matches the browserify -r/-x split this script replaces.
var LIB_GLOBAL = '__clic_libs';

function escape_re(s) {
    return s.replace(/[.*+?\^${}()|\[\]\\]/g, '\\$&');
}

function quote(s) {
    return JSON.stringify(s);
}

// esbuild plugin: redirect `require('jquery')` (and friends) to a lookup on
// the LIB_GLOBAL populated by the libraries bundle.
function external_globals_plugin(libs) {
    var filter = new RegExp('^(' + libs.map(escape_re).join('|') + ')$');
    return {
        name: 'external-globals',
        setup: function (build) {
            build.onResolve({ filter: filter }, function (args) {
                return { path: args.path, namespace: 'external-globals' };
            });
            build.onLoad(
                { filter: /.*/, namespace: 'external-globals' },
                function (args) {
                    return {
                        contents: 'module.exports = window.' + LIB_GLOBAL
                                + '[' + quote(args.path) + '];',
                    };
                }
            );
        },
    };
}

function build_libraries(outfile, libs) {
    // jQuery plugins (chosen-js, datatables.net, ...) look up jQuery on the
    // global at module-init time. Browserify hid this with lazy `-r` modules;
    // we evaluate eagerly, so we have to make jQuery global before any plugin
    // is required.
    var jquery_lib, ordered, lines, entry;
    jquery_lib = libs.find(function (l) {
        return l === 'jquery' || l.indexOf('jquery/') === 0;
    });
    ordered = jquery_lib
        ? [jquery_lib].concat(libs.filter(function (l) { return l !== jquery_lib; }))
        : libs;
    lines = [];
    ordered.forEach(function (l) {
        lines.push('g[' + quote(l) + '] = require(' + quote(l) + ');');
        if (l === jquery_lib) {
            lines.push('globalThis.jQuery = g[' + quote(l) + '];');
        }
    });
    entry = [
        '"use strict";',
        'var g = (window.' + LIB_GLOBAL + ' = window.' + LIB_GLOBAL + ' || {});',
        lines.join("\n"),
    ].join("\n");

    return esbuild.build({
        stdin: {
            contents: entry,
            resolveDir: process.cwd(),
            loader: 'js',
        },
        bundle: true,
        minify: true,
        outfile: outfile,
        nodePaths: [process.cwd()],
        logLevel: 'info',
    });
}

function build_main(infile, outfile, libs) {
    return esbuild.build({
        entryPoints: [infile],
        bundle: true,
        minify: true,
        sourcemap: true,
        outfile: outfile,
        plugins: [external_globals_plugin(libs)],
        nodePaths: [process.cwd()],
        logLevel: 'info',
    });
}

/////////////////////////////

if (process.argv.length < 4) {
    throw new Error([
        "Usage:",
        process.argv[0],
        process.argv[1],
        "libraries (outfile) (lib...)",
        "| main (infile) (outfile) (lib...)",
    ].join(" "));
}

var mode = process.argv[2];
var args = process.argv.slice(3);
var p;

if (mode === 'libraries') {
    p = build_libraries(args[0], args.slice(1));
} else if (mode === 'main') {
    p = build_main(args[0], args[1], args.slice(2));
} else {
    throw new Error("Unknown mode: " + mode);
}

p.catch(function (err) {
    process.stderr.write(String(err) + '\n');
    process.exit(1);
});
