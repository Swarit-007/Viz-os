"""
Vercel serverless function handler for Flask app
"""
import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Change to project root directory for proper path resolution
os.chdir(project_root)

# Import the Flask app
from backend.app import app

# Export the app for Vercel Python runtime
# Vercel automatically detects the 'app' variable and wraps it as a WSGI handler

