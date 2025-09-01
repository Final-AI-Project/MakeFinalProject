#!/bin/bash

# Plant Whisperer Python Environment Setup Script
# This script sets up a Python virtual environment and installs dependencies

set -e  # Exit on any error

echo "🌱 Setting up Plant Whisperer Python environment..."

# Check if Python 3.11 is available
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Python 3.11 is not installed. Please install Python 3.11.9 first."
    echo "   Download from: https://www.python.org/downloads/"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3.11 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️  Upgrading pip..."
pip install --upgrade pip

# Install pip-tools for dependency management
echo "📋 Installing pip-tools..."
pip install pip-tools

# Install dependencies from requirements.txt if it exists
if [ -f "backend/requirements.txt" ]; then
    echo "📥 Installing Python dependencies..."
    pip install -r backend/requirements.txt
else
    echo "⚠️  requirements.txt not found. Creating from requirements.in..."
    if [ -f "backend/requirements.in" ]; then
        cd backend
        pip-compile requirements.in
        pip install -r requirements.txt
        cd ..
    else
        echo "❌ requirements.in not found. Please create it first."
        exit 1
    fi
fi

# Create storage directories
echo "📁 Creating storage directories..."
mkdir -p storage/uploads
mkdir -p storage/samples
mkdir -p storage/models
mkdir -p logs

# Create .gitkeep files
touch storage/uploads/.gitkeep
touch storage/samples/.gitkeep
touch storage/models/.gitkeep

echo "✅ Python environment setup complete!"
echo ""
echo "To activate the environment manually:"
echo "  source venv/bin/activate"
echo ""
echo "To run the backend:"
echo "  bash scripts/run_backend.sh"
