#!/bin/bash
#
# Quick start script for Sector Rotation Map
#

echo "🚀 Starting Sector Rotation Map..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Run Streamlit app
echo "✅ Launching app..."
echo ""
streamlit run app.py
