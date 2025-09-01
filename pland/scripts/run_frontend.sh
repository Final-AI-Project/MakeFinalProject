#!/bin/bash

# Plant Whisperer Frontend Run Script
# This script installs dependencies and runs the React frontend

set -e  # Exit on any error

echo "🎨 Starting Plant Whisperer Frontend..."

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 20.x LTS first."
    echo "   Download from: https://nodejs.org/"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -d'v' -f2 | cut -d'.' -f1)
if [ "$NODE_VERSION" -lt 20 ]; then
    echo "❌ Node.js version 20.x or higher is required. Current version: $(node --version)"
    echo "   Please upgrade to Node.js 20.x LTS"
    exit 1
fi

# Navigate to frontend directory
cd frontend

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Run the development server
echo "🌐 Starting Vite development server on http://localhost:5173"
echo "🔄 Hot reload enabled"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
