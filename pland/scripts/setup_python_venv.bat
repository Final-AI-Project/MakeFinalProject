@echo off
REM Plant Whisperer Python Environment Setup Script for Windows
REM This script sets up a Python virtual environment and installs dependencies

echo 🌱 Setting up Plant Whisperer Python environment...

REM Check if Python 3.11 is available
python --version 2>nul
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH. Please install Python 3.11.9 first.
    echo    Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install pip-tools for dependency management
echo 📋 Installing pip-tools...
pip install pip-tools

REM Install dependencies from requirements.txt if it exists
if exist "backend\requirements.txt" (
    echo 📥 Installing Python dependencies...
    pip install -r backend\requirements.txt
) else (
    echo ⚠️  requirements.txt not found. Creating from requirements.in...
    if exist "backend\requirements.in" (
        cd backend
        pip-compile requirements.in
        pip install -r requirements.txt
        cd ..
    ) else (
        echo ❌ requirements.in not found. Please create it first.
        pause
        exit /b 1
    )
)

REM Create storage directories
echo 📁 Creating storage directories...
if not exist "storage\uploads" mkdir storage\uploads
if not exist "storage\samples" mkdir storage\samples
if not exist "storage\models" mkdir storage\models
if not exist "logs" mkdir logs

REM Create .gitkeep files
echo. > storage\uploads\.gitkeep
echo. > storage\samples\.gitkeep
echo. > storage\models\.gitkeep

echo ✅ Python environment setup complete!
echo.
echo To activate the environment manually:
echo   venv\Scripts\activate.bat
echo.
echo To run the backend:
echo   scripts\run_backend.bat
echo.
pause
