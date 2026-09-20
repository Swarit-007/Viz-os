#!/usr/bin/env python3
"""VizOS backend - Flask API server for the OS algorithm simulator."""

import os
import sys

# Allow `python backend/app.py` and `cd backend && python app.py` as well as
# `python -m backend.app`: put the project root on sys.path so the
# package-qualified imports below resolve in every case.
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request, send_from_directory  # noqa: E402
from flask_cors import CORS  # noqa: E402
from werkzeug.exceptions import HTTPException  # noqa: E402

from backend.modules.bankers_module import BankersModule  # noqa: E402
from backend.modules.common import ValidationError  # noqa: E402
from backend.modules.deadlock_module import DeadlockModule  # noqa: E402
from backend.modules.fcfs_module import FCFSModule  # noqa: E402
from backend.modules.memory_allocation_module import MemoryAllocationModule  # noqa: E402
from backend.modules.page_replacement_module import PageReplacementModule  # noqa: E402
from backend.modules.priority_module import PriorityModule  # noqa: E402
from backend.modules.roundrobin_module import RoundRobinModule  # noqa: E402
from backend.modules.sjf_module import SJFModule  # noqa: E402
from backend.modules.srtf_module import SRTFModule  # noqa: E402

__version__ = '2.0.0'

FRONTEND_PATH = os.path.join(PROJECT_ROOT, 'frontend')

SECURITY_HEADERS = {
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'no-referrer',
}


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_PATH, static_url_path='')
    app.config['MAX_CONTENT_LENGTH'] = 1024 * 1024  # 1 MiB request bodies are plenty

    # The frontend is served from the same origin. Cross-origin access is opt-in:
    # VIZOS_CORS_ORIGINS="https://example.com,https://other.example".
    origins = [o.strip() for o in os.environ.get('VIZOS_CORS_ORIGINS', '').split(',') if o.strip()]
    if origins:
        CORS(app, resources={r'/api/*': {'origins': origins}})

    schedulers = {
        'fcfs': FCFSModule(),
        'sjf': SJFModule(),
        'srtf': SRTFModule(),
        'priority': PriorityModule(),
    }
    roundrobin = RoundRobinModule()
    bankers = BankersModule()
    deadlock = DeadlockModule()
    page_replacement = PageReplacementModule()
    memory_allocation = MemoryAllocationModule()

    def json_body():
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            raise ValidationError('Request body must be a JSON object')
        return data

    @app.after_request
    def add_security_headers(response):
        for header, value in SECURITY_HEADERS.items():
            response.headers.setdefault(header, value)
        return response

    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        return jsonify({'success': False, 'error': str(error)}), 400

    @app.errorhandler(HTTPException)
    def handle_http_error(error):
        if request.path.startswith('/api'):
            return jsonify({'success': False, 'error': error.description}), error.code
        return error

    @app.errorhandler(Exception)
    def handle_unexpected_error(error):
        app.logger.exception('Unhandled error')
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    @app.route('/')
    def home():
        return send_from_directory(FRONTEND_PATH, 'index.html')

    @app.route('/api')
    def api_home():
        return jsonify({
            'message': 'VizOS API Server',
            'version': __version__,
            'endpoints': {
                'cpu_scheduling': {
                    'fcfs': '/api/scheduling/fcfs',
                    'sjf': '/api/scheduling/sjf',
                    'srtf': '/api/scheduling/srtf',
                    'priority': '/api/scheduling/priority',
                    'roundrobin': '/api/scheduling/roundrobin',
                },
                'bankers': '/api/bankers',
                'deadlock': '/api/deadlock',
                'page_replacement': '/api/page-replacement',
                'memory_allocation': '/api/memory-allocation',
                'health': '/api/health',
            },
        })

    @app.route('/api/scheduling/<algorithm>', methods=['POST'])
    def api_scheduling(algorithm):
        data = json_body()
        if algorithm == 'roundrobin':
            return jsonify(roundrobin.simulate(data.get('processes'), data.get('time_quantum', 2)))
        if algorithm not in schedulers:
            raise ValidationError(f'Unknown scheduling algorithm: {algorithm}')
        return jsonify(schedulers[algorithm].simulate(data.get('processes')))

    @app.route('/api/bankers', methods=['POST'])
    def api_bankers():
        data = json_body()
        return jsonify(bankers.simulate(
            data.get('num_processes', 3), data.get('num_resources', 3),
            data.get('allocation'), data.get('max'), data.get('available')))

    @app.route('/api/deadlock', methods=['POST'])
    def api_deadlock():
        data = json_body()
        return jsonify(deadlock.simulate(
            data.get('num_processes', 4), data.get('num_resources', 3),
            data.get('allocation'), data.get('request'), data.get('available')))

    @app.route('/api/page-replacement', methods=['POST'])
    def api_page_replacement():
        data = json_body()
        return jsonify(page_replacement.simulate(
            data.get('algorithm', 'fifo'), data.get('frames', 3), data.get('page_requests')))

    @app.route('/api/memory-allocation', methods=['POST'])
    def api_memory_allocation():
        data = json_body()
        return jsonify(memory_allocation.allocate_memory(
            data.get('blocks'), data.get('processes'), data.get('strategy', 'best')))

    @app.route('/api/health')
    def health_check():
        return jsonify({'status': 'healthy', 'message': 'VizOS API is running', 'version': __version__})

    return app


app = create_app()


if __name__ == '__main__':
    host = os.environ.get('VIZOS_HOST', '127.0.0.1')
    port = int(os.environ.get('PORT', os.environ.get('VIZOS_PORT', 5000)))
    # The Werkzeug debugger allows remote code execution: opt in explicitly, never by default.
    debug = os.environ.get('VIZOS_DEBUG', '').lower() in ('1', 'true', 'yes')
    print(f'VizOS {__version__} running at http://{host}:{port}/  (API docs: /api)')
    app.run(debug=debug, host=host, port=port)
