@echo off
REM Plant Whisperer Backend Run Script for Windows
REM This script activates the virtual environment and runs the FastAPI backend

echo 🚀 Starting Plant Whisperer Backend...

REM Check if virtual environment exists
if not exist "venv" (
    echo ❌ Virtual environment not found. Please run setup first:
    echo    scripts\setup_python_venv.bat
    pause
    exit /b 1
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if requirements are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo ❌ Dependencies not installed. Please run setup first:
    echo    scripts\setup_python_venv.bat
    pause
    exit /b 1
)

REM Set environment variables
set PYTHONPATH=%PYTHONPATH%;%CD%

REM Create logs directory if it doesn't exist
if not exist "logs" mkdir logs

REM Run the FastAPI application
echo 🌐 Starting FastAPI server on http://localhost:8000
echo 📚 API documentation: http://localhost:8000/docs
echo 🔄 Auto-reload enabled
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
