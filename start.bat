@echo off
REM VizOS Quick Start Script for Windows
echo 🚀 Starting VizOS - Interactive OS Simulation Tool
echo ==================================================

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python 3.7 or higher.
    pause
    exit /b 1
)

REM Check if we're in the right directory
if not exist "backend\app.py" (
    echo ❌ Please run this script from the VizOS root directory
    pause
    exit /b 1
)

REM Navigate to backend directory
cd backend

REM Check if virtual environment exists
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo 📥 Installing dependencies...
pip install -r requirements.txt

REM Start the Flask server
echo 🌐 Starting VizOS application...
echo    Application: http://localhost:5000
echo    API Documentation: http://localhost:5000/api
echo.
echo Press Ctrl+C to stop the server
echo.

python app.py
