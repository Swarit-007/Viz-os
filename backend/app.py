#!/usr/bin/env python3
"""
VizOS Backend - Flask API Server
Interactive Operating System Simulation Tool
"""

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import json
import sys
import os

# If this file is executed directly from inside the `backend/` folder (
# e.g. `cd backend && python3 app.py`), Python's import system will not
# find the top-level `backend` package unless the project root is on
# sys.path. Add the project root to sys.path early so package-qualified
# imports like `from backend.modules...` work both when running as a
# module (python -m backend.app) and when running the script directly.
# This is a minimal, explicit fix that avoids changing other import paths.
proj_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if proj_root not in sys.path:
    sys.path.insert(0, proj_root)

# Use package imports (backend.modules) -- backend and backend/modules
# must be packages (have __init__.py)
from backend.modules.fcfs_module import FCFSModule
from backend.modules.sjf_module import SJFModule
from backend.modules.priority_module import PriorityModule
from backend.modules.roundrobin_module import RoundRobinModule
from backend.modules.bankers_module import BankersModule
from backend.modules.deadlock_module import DeadlockModule
from backend.modules.page_replacement_module import PageReplacementModule
from backend.modules.memory_allocation_module import MemoryAllocationModule

app = Flask(__name__, 
            static_folder='../frontend',
            static_url_path='',
            template_folder='../frontend')
CORS(app)  # Enable CORS for frontend communication

# Initialize algorithm modules
fcfs = FCFSModule()
sjf = SJFModule()
priority = PriorityModule()
roundrobin = RoundRobinModule()
bankers = BankersModule()
deadlock = DeadlockModule()
page_replacement = PageReplacementModule()
memory_allocation = MemoryAllocationModule()

@app.route('/')
def home():
    """Serve the main VizOS application"""
    return send_from_directory('../frontend', 'index.html')

@app.route('/api')
def api_home():
    """API Home endpoint"""
    return jsonify({
        'message': 'VizOS API Server',
        'version': '1.0.0',
            'endpoints': {
                'cpu_scheduling': {
                    'fcfs': '/api/scheduling/fcfs',
                    'sjf': '/api/scheduling/sjf',
                    'priority': '/api/scheduling/priority',
                    'roundrobin': '/api/scheduling/roundrobin'
                },
                'bankers': '/api/bankers',
                'deadlock': '/api/deadlock',
                'page_replacement': '/api/page-replacement',
                'memory_allocation': '/api/memory-allocation'
            }
    })

@app.route('/api/scheduling/fcfs', methods=['POST'])
def api_fcfs():
    """FCFS CPU Scheduling API endpoint"""
    try:
        data = request.get_json()
        processes = data.get('processes', [])
        
        if not processes:
            return jsonify({'error': 'No processes provided'}), 400
        
        result = fcfs.simulate(processes)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduling/sjf', methods=['POST'])
def api_sjf():
    """SJF CPU Scheduling API endpoint"""
    try:
        data = request.get_json()
        processes = data.get('processes', [])
        
        if not processes:
            return jsonify({'error': 'No processes provided'}), 400
        
        result = sjf.simulate(processes)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduling/priority', methods=['POST'])
def api_priority():
    """Priority CPU Scheduling API endpoint"""
    try:
        data = request.get_json()
        processes = data.get('processes', [])
        
        if not processes:
            return jsonify({'error': 'No processes provided'}), 400
        
        result = priority.simulate(processes)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/scheduling/roundrobin', methods=['POST'])
def api_roundrobin():
    """Round Robin CPU Scheduling API endpoint"""
    try:
        data = request.get_json()
        processes = data.get('processes', [])
        time_quantum = data.get('time_quantum', 2)
        
        if not processes:
            return jsonify({'error': 'No processes provided'}), 400
        
        result = roundrobin.simulate(processes, time_quantum)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/bankers', methods=['POST'])
def api_bankers():
    """Banker's Algorithm API endpoint"""
    try:
        data = request.get_json()
        num_processes = data.get('num_processes', 3)
        num_resources = data.get('num_resources', 3)
        allocation = data.get('allocation')
        max_matrix = data.get('max')
        available = data.get('available')
        
        result = bankers.simulate(num_processes, num_resources, allocation, max_matrix, available)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/deadlock', methods=['POST'])
def api_deadlock():
    """Deadlock Detection API endpoint"""
    try:
        data = request.get_json()
        num_processes = data.get('num_processes', 4)
        num_resources = data.get('num_resources', 3)
        allocation = data.get('allocation')
        request_matrix = data.get('request')
        available = data.get('available')
        
        result = deadlock.simulate(num_processes, num_resources, allocation, request_matrix, available)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/page-replacement', methods=['POST'])
def api_page_replacement():
    """Page Replacement API endpoint"""
    try:
        data = request.get_json()
        algorithm = data.get('algorithm', 'fifo')
        frames = data.get('frames', 3)
        page_requests = data.get('page_requests', [])
        
        if not page_requests:
            return jsonify({'error': 'No page requests provided'}), 400
        
        if frames < 1:
            return jsonify({'error': 'Number of frames must be at least 1'}), 400
        
        result = page_replacement.simulate(algorithm, frames, page_requests)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/memory-allocation', methods=['POST'])
def api_memory_allocation():
    """Memory Allocation API endpoint"""
    try:
        data = request.get_json()
        blocks = data.get('blocks', [])
        processes = data.get('processes', [])
        strategy = data.get('strategy', 'best')
        
        if not blocks:
            return jsonify({'error': 'No memory blocks provided'}), 400
        
        if not processes:
            return jsonify({'error': 'No processes provided'}), 400
        
        if strategy not in ['best', 'first', 'worst']:
            return jsonify({'error': 'Invalid strategy. Must be "best", "first", or "worst"'}), 400
        
        result = memory_allocation.allocate_memory(blocks, processes, strategy)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'VizOS API is running'
    })

# Serve static files
@app.route('/<path:filename>')
def serve_static(filename):
    """Serve static files from frontend directory"""
    return send_from_directory('../frontend', filename)

if __name__ == '__main__':
    print("Starting VizOS - Interactive OS Simulation Tool")
    print("=" * 50)
    print("Application: http://localhost:5000/")
    print("API Documentation: http://localhost:5000/api")
    print("Health Check: http://localhost:5000/api/health")
    print("=" * 50)
    print("Press Ctrl+C to stop the server")
    print("")
    app.run(debug=True, host='0.0.0.0', port=5000)
