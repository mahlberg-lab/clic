# -*- coding: utf-8 -*-
import json
import os

# Hack HOME var so cheshire3 can make a useless config directory
os.environ['HOME'] = "/tmp"

from flask import Flask, request, Response, jsonify, g

from clic.clicdb import ClicDb

app = Flask(__name__)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
# Enable profiling per request
# from werkzeug.contrib.profiler import ProfilerMiddleware
# app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

def clicdb():
    if not getattr(g, '_clicdb', None):
        g._clicdb = ClicDb()
    return g._clicdb

_clic_version = None
def clic_version():
    global _clic_version
    if not _clic_version:
        _clic_version = ClicDb().get_clic_version()
    return _clic_version

@app.before_first_request
def warm_cache():
    clicdb().warm_cache()

@app.after_request
def add_header(response):
    # Everything can be cached for up to an hour
    response.cache_control.max_age = 3600
    response.cache_control.public = True
    return response

@app.teardown_appcontext
def close_db(exception):
    if getattr(g, 'clicdb', None):
        g.clicdb.close()

def format_error(e):
    import traceback

    level = getattr(e, 'level', 'error')
    return dict(
        error=e.__class__.__name__,
        level=level,
        message=e.message,
        stack=traceback.format_exc() if getattr(e, 'print_stack', True) else None,
    )

def stream_json(generator, header={}):
    """
    Stream output of generator as JSON.
    header is used as the containing dict,
    all other items will be added to a "data" array within it
    """
    # Initial JSON object based on first item returned
    header = json.dumps(header, separators=(',', ':'))
    if header[-1] != '}':
        raise ValueError("Initial item not a JSON object: %s" % header)
    if header == '{}':
        yield '{"data":['
    else:
        yield header[:-1] + ',"data":['

    separator = '\n'
    footer = None
    try:
        for x in generator:
            yield separator + json.dumps(x, separators=(',', ':'))
            separator = ',\n'
    except Exception as e:
        footer = dict(message=format_error(e))

    # End list and format footer
    footer = json.dumps(footer, separators=(',', ':'))
    if footer[0] == '{':
        yield '\n], ' + footer[1:]
    else:
        yield '\n]}'

# ==== Metadata routes ====================================
import clic.metadata

@app.route('/api/corpora', methods=['GET'])
def corpora():
    out = clic.metadata.get_corpus_structure(clicdb())
    return jsonify(dict(corpora=out, version=clic_version()))

@app.route('/api/corpora/details', methods=['GET'])
def corpora_details():
    out = clic.metadata.get_corpus_details(clicdb())
    return jsonify(dict(corpora=out, version=clic_version()))

# ==== Concordance routes =================================
import clic.concordance

@app.route('/api/concordance', methods=['GET'])
def concordances():
    out = clic.concordance.concordance(clicdb(), **request.args)
    header = out.next()
    header['version'] = clic_version()
    return Response(stream_json(out, header), content_type='application/json')

# ==== Subset routes ======================================
import clic.subset

@app.route('/api/subset', methods=['GET'])
def subset():
    out = clic.subset.subset(clicdb(), **request.args)
    header = out.next()
    header['version'] = clic_version()
    return Response(stream_json(out, header), content_type='application/json')

# ==== Keyword routes =====================================
import clic.keyword

@app.route('/api/keyword', methods=['GET'])
def keyword():
    out = clic.keyword.keyword(clicdb(), **request.args)
    header = out.next()
    header['version'] = clic_version()
    return Response(stream_json(out, header), content_type='application/json')

# ==== Cluster routes =====================================
import clic.cluster

@app.route('/api/cluster', methods=['GET'])
def cluster():
    out = clic.cluster.cluster(clicdb(), **request.args)
    header = out.next()
    header['version'] = clic_version()
    return Response(stream_json(out, header), content_type='application/json')

# ==== Chapter routes =====================================
import clic.chapter

@app.route('/api/chapter', methods=['GET'])
def chapter():
    out = clic.chapter.chapter(clicdb(), **request.args)
    return Response(out, content_type='application/xml')

# ==== Error handlers =====================================
@app.errorhandler(404)
def handle_404(error):
    response = jsonify(dict(
        error="NotFound",
        message="This endpoint does not exist",
    ))
    response.status_code = 404
    return response

@app.errorhandler(500)
def handle_500(error):
    import traceback
    response = jsonify(format_error(error))
    response.status_code = 500
    return response

# ==== Application ========================================
if __name__ == '__main__':
    app.run(
        port=5000,
        debug=True,
    )
