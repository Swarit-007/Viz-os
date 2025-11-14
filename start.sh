#!/bin/bash

# VizOS Quick Start Script
echo "🚀 Starting VizOS - Interactive OS Simulation Tool"
echo "=================================================="
# ...existing code...

python app.py --port=5001
# ...existing code...
# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    exit 1
fi

# Check if we're in the right directory
if [ ! -f "backend/app.py" ]; then
    echo "❌ Please run this script from the VizOS root directory"
    exit 1
fi

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -r requirements.txt

# Start the Flask server
echo "🌐 Starting VizOS application..."
echo "   Application: http://localhost:5000"
echo "   API Documentation: http://localhost:5000/api"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
