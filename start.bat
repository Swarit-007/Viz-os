@echo off
REM VizOS quick start for Windows: creates a virtualenv, installs dependencies, runs the server.
cd /d "%~dp0"

python --version >nul 2>&1
if errorlevel 1 (
    echo Python 3.9+ is required but was not found.
    pause
    exit /b 1
)

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

call .venv\Scripts\activate.bat
pip install --quiet -r requirements.txt

if "%PORT%"=="" set PORT=5000
echo VizOS: http://localhost:%PORT%   API: http://localhost:%PORT%/api
python backend\app.py
