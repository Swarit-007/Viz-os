import sys
import os

# Ensure project root (parent of 'backend') is on sys.path so 'backend' package can be imported
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
