"""Flask application: JSON API plus the static front end."""

import os

from flask import Flask, jsonify, request, send_from_directory
from werkzeug.exceptions import HTTPException

from . import __version__
from .algos import *  # noqa: F401,F403  (registers algorithms)
from .compare import RANK, compare
from .core import CATEGORIES, REGISTRY, ValidationError, random_params, run_algorithm

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
WEB = os.path.join(ROOT, 'web')


def create_app():
    app = Flask(__name__, static_folder=WEB, static_url_path='')
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024
    app.json.sort_keys = False

    def body():
        data = request.get_json(silent=True)
        if data is not None and not isinstance(data, dict):
            raise ValidationError('Request body must be a JSON object')
        return data or {}

    @app.after_request
    def headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        if request.path.startswith('/api/catalog'):
            response.headers.setdefault('Cache-Control', 'public, max-age=300')
        return response

    @app.errorhandler(ValidationError)
    def bad_input(error):
        return jsonify({'success': False, 'error': str(error)}), 400

    @app.errorhandler(HTTPException)
    def http_error(error):
        if request.path.startswith('/api'):
            return jsonify({'success': False, 'error': error.description}), error.code
        return error

    @app.errorhandler(Exception)
    def crash(error):
        app.logger.exception('Unhandled error')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @app.route('/')
    def home():
        return send_from_directory(WEB, 'index.html')

    @app.route('/api/catalog')
    def catalog():
        return jsonify({'version': __version__, 'categories': CATEGORIES, 'compare': sorted(RANK),
                        'algorithms': [a.public() for a in REGISTRY.values()]})

    @app.route('/api/run/<alg_id>', methods=['POST'])
    def run(alg_id):
        return jsonify(run_algorithm(alg_id, body().get('params')))

    @app.route('/api/random/<alg_id>', methods=['POST'])
    def rand(alg_id):
        seed = body().get('seed')
        if seed is not None and (isinstance(seed, bool) or not isinstance(seed, int)):
            raise ValidationError('seed must be a whole number')
        return jsonify({'success': True, 'params': random_params(alg_id, seed)})

    @app.route('/api/compare/<family>', methods=['POST'])
    def compare_route(family):
        return jsonify(compare(family, body().get('params')))

    @app.route('/api/health')
    def health():
        return jsonify({'status': 'healthy', 'version': __version__, 'algorithms': len(REGISTRY)})

    return app


app = create_app()


if __name__ == '__main__':
    host = os.environ.get('VIZOS_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', os.environ.get('VIZOS_PORT', 5000)))
    debug = os.environ.get('VIZOS_DEBUG', '').lower() in ('1', 'true', 'yes')
    print(f'VizOS {__version__}: http://{host}:{port}/  ({len(REGISTRY)} algorithms)')
    app.run(debug=debug, host=host, port=port)
