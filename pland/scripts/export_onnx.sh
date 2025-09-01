#!/bin/bash

# Plant Whisperer ONNX Export Script
# This script exports PyTorch models to ONNX format for optimized inference

set -e  # Exit on any error

echo "📦 Exporting PyTorch model to ONNX format..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Please run setup first:"
    echo "   bash scripts/setup_python_venv.sh"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Set environment variables
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# Check if model file exists
MODEL_PATH="storage/models/best.pt"
if [ ! -f "$MODEL_PATH" ]; then
    echo "❌ Model file not found: $MODEL_PATH"
    echo "   Please train a model first or check the model path."
    exit 1
fi

# Create models directory if it doesn't exist
mkdir -p storage/models

# Run the ONNX export script
echo "🔄 Converting PyTorch model to ONNX..."
python -m backend.app.ml.export_onnx \
    --model_path "$MODEL_PATH" \
    --output_path "storage/models/best.onnx" \
    --input_size 512

echo "✅ ONNX model exported successfully!"
echo "📁 Output: storage/models/best.onnx"
echo ""
echo "You can now use the ONNX model for faster inference."
