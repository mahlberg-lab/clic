# -*- coding: utf-8 -*-
import json
import os

# Hack HOME var so cheshire3 can make a useless config directory
os.environ['HOME'] = "/tmp"

from flask import Flask, request, Response, jsonify, g
from flask_cors import CORS

from clic.clicdb import ClicDb
from clic.stream_json import stream_json, format_error

app = Flask(__name__)
CORS(app)
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

# ==== Metadata routes ====================================
import clic.metadata

@app.route('/api/corpora', methods=['GET'])
def corpora():
    out = clic.metadata.get_corpus_structure(clicdb())
    return jsonify(dict(corpora=out, version=clic_version()))

@app.route('/api/corpora/headlines', methods=['GET'])
def headlines():
    out = clic.metadata.get_corpus_headlines(clicdb())
    return jsonify(dict(data=out, version=clic_version()))

# ==== count route ========================================
import clic.count

@app.route('/api/count', methods=['GET'])
def word_count():
    out = clic.count.word_count(clicdb(), **request.args)
    header = out.next()
    header['version'] = clic_version()
    return Response(stream_json(out, header), content_type='application/json')

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

# ==== Text routes ========================================
import clic.text

@app.route('/api/text', methods=['GET'])
def text():
    out = clic.text.text(clicdb(), **request.args)
    header = out.next()
    header['version'] = clic_version()
    return Response(stream_json(out, header), content_type='application/json')

# ==== Error handlers =====================================
@app.errorhandler(404)
def handle_404(error):
    response = jsonify(dict(error=dict(
        message="This endpoint does not exist",
    )))
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
