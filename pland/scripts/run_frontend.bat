@echo off
REM Plant Whisperer Frontend Run Script for Windows
REM This script installs dependencies and runs the React frontend

echo 🎨 Starting Plant Whisperer Frontend...

REM Check if Node.js is installed
node --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Node.js is not installed. Please install Node.js 20.x LTS first.
    echo    Download from: https://nodejs.org/
    pause
    exit /b 1
)

REM Check Node.js version
for /f "tokens=1,2 delims=." %%a in ('node --version') do set NODE_VERSION=%%a
set NODE_VERSION=%NODE_VERSION:~1%
if %NODE_VERSION% LSS 20 (
    echo ❌ Node.js version 20.x or higher is required. Current version: 
    node --version
    echo    Please upgrade to Node.js 20.x LTS
    pause
    exit /b 1
)

REM Navigate to frontend directory
cd frontend

REM Check if node_modules exists
if not exist "node_modules" (
    echo 📦 Installing frontend dependencies...
    npm install
)

REM Run the development server
echo 🌐 Starting Vite development server on http://localhost:5173
echo 🔄 Hot reload enabled
echo.
echo Press Ctrl+C to stop the server
echo.

npm run dev
