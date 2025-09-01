#!/bin/bash

# Plant Whisperer Python Dependencies Lock Script
# This script compiles and locks Python dependencies

set -e  # Exit on any error

echo "🔒 Locking Python dependencies..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   bash scripts/setup_python_venv.sh"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Navigate to backend directory
cd backend

# Check if requirements.in exists
if [ ! -f "requirements.in" ]; then
    echo "❌ requirements.in not found. Please create it first."
    exit 1
fi

# Install pip-tools if not installed
if ! python -c "import piptools" 2>/dev/null; then
    echo "📋 Installing pip-tools..."
    pip install pip-tools
fi

# Compile requirements
echo "📦 Compiling requirements.in to requirements.txt..."
pip-compile requirements.in --upgrade

# Install the locked dependencies
echo "📥 Installing locked dependencies..."
pip install -r requirements.txt

echo "✅ Dependencies locked and installed successfully!"
echo ""
echo "Current locked versions:"
pip list
