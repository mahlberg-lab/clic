from flask import Flask, request, Response, jsonify, g, stream_with_context
from flask_cors import CORS

import clic.concordance
import clic.cluster
import clic.count
import clic.metadata
import clic.keyword
import clic.subset
import clic.text
from clic.db.cursor import get_pool_cursor, put_pool_cursor
from clic.db.version import clic_version
from clic.stream_json import stream_json, format_error, JSONEncoder


# API endpoint functions and their view type (see to_view_func)
API_ENDPOINTS = [
    (clic.cluster.cluster, 'stream'),
    (clic.concordance.concordance, 'stream'),
    (clic.count.count, 'stream'),
    (clic.keyword.keyword, 'stream'),
    (clic.subset.subset, 'stream'),
    (clic.text.text, 'stream'),
    (clic.metadata.corpora, 'json'),
    (clic.metadata.corpora_headlines, 'json'),
    (clic.metadata.corpora_image, 'raw'),
]


def create_app(config=None, app_name=None):
    app = Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
    app.json_encoder = JSONEncoder

    # Register a view for all API endpoints
    for ep in API_ENDPOINTS:
        app.add_url_rule(**to_view_func(*ep))

    # Extensions
    CORS(app)

    # Enable profiling per request
    # from werkzeug.contrib.profiler import ProfilerMiddleware
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

    @app.before_request
    def get_cursor():
        # Fetch a DB cursor for this request
        g.cur = get_pool_cursor()
        g.clic_versions = clic_version(g.cur)

    @app.teardown_request
    def put_cursor(request):
        # Put it back again, regardless of result
        put_pool_cursor(g.cur)

    @app.after_request
    def add_header(response):
        # Everything can be cached for up to an hour
        response.cache_control.max_age = 3600
        response.cache_control.public = True
        response.vary.add('Accept-Encoding')

        # Add CLiC version headers, tell the browser to vary based on them
        for k, v in g.clic_versions.items():
            k = 'X-Version-%s' % k.title()
            response.headers[k] = v
            response.vary.add(k)
        return response

    @app.errorhandler(404)
    def handle_404(error):
        response = jsonify(dict(error=dict(
            message="This endpoint does not exist",
        )))
        response.status_code = 404
        return response

    @app.errorhandler(500)
    def handle_500(error):
        response = jsonify(format_error(error))
        response.status_code = 500
        return response

    return app


def to_view_func(fn, output_mode):
    """
    Turn a function call into one of several views, defined by output_mode
    - stream: Function call is a generator that generates output suitable for stream_json()
    - json: Function call returns a dict suitable for jsonify()
    """
    def stream_view_func():
        out = fn(g.cur, **request.args)
        return Response(
            # NB: We need stream_with_context() to make sure the database stays open
            stream_with_context(stream_json(out, dict(version=g.clic_versions), cls=JSONEncoder)),
            content_type='application/json',
        )
    if output_mode == 'stream':
        view_func = stream_view_func

    def json_view_func():
        out = fn(g.cur, **request.args)
        out['version'] = g.clic_versions
        return jsonify(out)
    if output_mode == 'json':
        view_func = json_view_func

    def raw_view_func():
        out = fn(g.cur, **request.args)
        return Response(**out)
    if output_mode == 'raw':
        view_func = raw_view_func

    return dict(
        rule='/api/' + fn.__name__.replace('_', '/'),
        endpoint=fn.__name__,
        methods=['GET'],
        view_func=view_func,
    )
