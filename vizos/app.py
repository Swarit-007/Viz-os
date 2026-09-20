"""Flask application: JSON API plus the static front end."""

import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from . import __version__
from .algos import *  # noqa: F401,F403  (registers algorithms)
from .compare import RANK, compare
from .core import CATEGORIES, REGISTRY, ValidationError, random_params, run_algorithm

# Project root and the folder of static front-end files that Flask serves.
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(ROOT, 'web')


# Application factory: builds a fresh Flask app. Tests call it directly; the module-level `app` below is what Vercel and gunicorn use.
def create_app():
    app = Flask(__name__, static_folder=WEB, static_url_path='')
    # Requests are small JSON documents; refuse anything over 1 MiB.
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
    app.json.sort_keys = False

    # Parse the request body as a JSON object. An empty body is treated as {} so parameter-free calls work.
    def body():
        data = request.get_json(silent=True)
        if data is not None and not isinstance(data, dict):
            raise ValidationError('Request body must be a JSON object')
        return data or {}

    # Basic hardening headers on every response.
    @app.after_request
    def headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        if request.path.startswith('/api/catalog'):
            response.headers.setdefault('Cache-Control', 'public, max-age=300')
        return response

    # Bad input from the client is the client's problem: HTTP 400 with a message the UI can show inline.
    @app.errorhandler(ValidationError)
    def bad_input(error):
        return jsonify({'success': False, 'error': str(error)}), 400

    # Make framework errors (404, 405, ...) come back as JSON for /api paths so the front end can always parse them.
    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api'):
            return jsonify({'success': False, 'error': error.description}), error.code
        return error

    # Anything unexpected is logged on the server and reported generically, never leaking internals.
    @app.errorhandler(Exception)
    def crash(error):
        app.logger.exception('Unhandled error')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @app.route('/')
    def home():
        return send_from_directory(WEB, 'index.html')

    # The catalog is the front end's table of contents and form generator: metadata for all algorithms.
    @app.route('/api/catalog')
    def catalog():
        return jsonify({'version': __version__, 'categories': CATEGORIES, 'compare': sorted(RANK),
                        'algorithms': [a.public() for a in REGISTRY.values()]})

    # Run one algorithm. Body: {"params": {...}}. Response follows the contract documented in core.result().
    @app.route('/api/run/<alg_id>', methods=['POST'])
    def run(alg_id):
        return jsonify(run_algorithm(alg_id, body().get('params')))

    # Produce a valid random input for one algorithm. Optional body: {"seed": 3}.
    @app.route('/api/random/<alg_id>', methods=['POST'])
    def rand(alg_id):
        seed = body().get('seed')
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise ValidationError('seed must be a whole number')
        return jsonify({'success': True, 'params': random_params(alg_id, seed)})

    # Race every algorithm of a family on the same input.
    @app.route('/api/compare/<family>', methods=['POST'])
    def compare_route(family):
        return jsonify(compare(family, body().get('params')))

    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy', 'version': __version__, 'algorithms': len(REGISTRY)})

    return app


# Module-level instance: `from vizos.app import app` is what api/index.py (Vercel) imports.
app = create_app()


# `python -m vizos.app` starts a local development server. Debug mode is opt-in because the Werkzeug
# debugger allows remote code execution and must never be reachable from a network.
if __name__ == '__main__':
    host = os.environ.get('VIZOS_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', os.environ.get('VIZOS_PORT', 5000)))
    debug = os.environ.get('VIZOS_DEBUG', '').lower() in ('1', 'true', 'yes')
    print(f'VizOS {__version__}: http://{host}:{port}/  ({len(REGISTRY)} algorithms)')
    app.run(debug=debug, host=host, port=port)
