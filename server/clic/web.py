# -*- coding: utf-8 -*-
import json
import os

# Hack HOME var so cheshire3 can make a useless config directory
os.environ['HOME'] = "/tmp"

from flask import Flask, request, Response, jsonify, g

from clic.clicdb import ClicDb

app = Flask(__name__)

def clicdb():
    if not getattr(g, '_clicdb', None):
        g._clicdb = ClicDb()
    return g._clicdb

@app.teardown_appcontext
def close_db(exception):
    if getattr(g, 'clicdb', None):
        g.clicdb.close()

def stream_json(generator):
    """
    Turn a generator's output into JSON
    First item has to be an object, and will be used as the initial
    header structure,
    All other items will be added to a "results" array
    """
    # Initial JSON object based on first item returned
    header = json.dumps(generator.next(), separators=(',', ':'))
    if header[-1] != '}':
        raise ValueError("Initial item not a JSON object: %s" % header)
    if header == '{}':
        yield '{"results":['
    else:
        yield header[:-1] + ',"results":['

    separator = '\n'
    for x in generator:
        yield separator + json.dumps(x, separators=(',', ':'))
        separator = ',\n'
    yield ']}'

# ==== Metadata routes ====================================
@app.route('/api/corpora', methods=['GET'])
def corpora():
    out = clicdb().get_corpus_structure()
    return jsonify(dict(corpora=out))

# ==== Concordance routes =================================
import clic.concordance

@app.route('/api/concordance', methods=['GET'])
def concordances():
    out = clic.concordance.concordance(clicdb(), **request.args)
    return Response(stream_json(out), content_type='application/json')

# ==== Subset routes ======================================
import clic.subset

@app.route('/api/subset', methods=['GET'])
def subset():
    out = clic.subset.subset(clicdb(), **request.args)
    return Response(stream_json(out), content_type='application/json')

# ==== Admin routes =======================================
import clic.c3chapter

@app.route('/api/warm/', methods=['GET'])
def concordance_warm():
    out = clic.c3chapter.warm_cache()
    return Response(out, mimetype='text/plain')


# ==== Error handlers =====================================
@app.errorhandler(404)
def handle_404(error):
    response = jsonify(dict(error=str(error)))
    response.status_code = 404
    return response

@app.errorhandler(500)
def handle_500(error):
    response = jsonify(dict(error=str(error)))
    response.status_code = 500
    return response

# ==== Application ========================================
def create_app():
    return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        port=5000,
        debug=False,
    )
