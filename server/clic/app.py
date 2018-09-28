from flask import Flask, request, Response, jsonify
from flask_cors import CORS

import clic.concordance
from clic.db.cursor import get_pool_cursor
from clic.db.version import clic_version
from clic.stream_json import stream_json, format_error

STREAMING_APIS = [
    clic.concordance.concordance,
]


def create_app(config=None, app_name=None):
    app = Flask(__name__)
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False

    # Register a view for all regular API calls
    for fn in STREAMING_APIS:
        def view_func():
            with get_pool_cursor() as cur:
                header = dict(version=clic_version(cur))
                out = fn(cur, **request.args)
                return Response(
                    stream_json(out, header),
                    content_type='application/json'
                )
        app.add_url_rule(
            '/api/' + fn.__name__,
            methods=['GET'],
            view_func=view_func,
        )

    # Extensions
    CORS(app)

    # Enable profiling per request
    # from werkzeug.contrib.profiler import ProfilerMiddleware
    # app.wsgi_app = ProfilerMiddleware(app.wsgi_app)

    @app.after_request
    def add_header(response):
        # Everything can be cached for up to an hour
        response.cache_control.max_age = 3600
        response.cache_control.public = True
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
