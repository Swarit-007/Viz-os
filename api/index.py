"""Vercel serverless entry point: exposes the Flask WSGI app as the module-level name `app`."""
import os
import sys

# Make the project root importable so `vizos` resolves inside the serverless bundle.
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Vercel finds the module-level `app` name, so this import must stay even though it looks unused.
from vizos.app import app  # noqa: E402, F401
