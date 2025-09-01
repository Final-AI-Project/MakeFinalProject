#!/bin/bash

# Plant Whisperer Backend Run Script
# This script activates the virtual environment and runs the FastAPI backend

set -e  # Exit on any error

echo "🚀 Starting Plant Whisperer Backend..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   bash scripts/setup_python_venv.sh"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Check if requirements are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "❌ Dependencies not installed. Please run setup first:"
    echo "   bash scripts/setup_python_venv.sh"
    exit 1
fi

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the FastAPI application
echo "🌐 Starting FastAPI server on http://localhost:8000"
echo "📚 API documentation: http://localhost:8000/docs"
echo "🔄 Auto-reload enabled"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload --log-level info
