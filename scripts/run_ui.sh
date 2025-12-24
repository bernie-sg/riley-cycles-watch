#!/usr/bin/env bash
set -euo pipefail

# Riley Cycles Watch - UI Launcher
cd "/Users/bernie/Documents/AI/Riley Project"

echo "Starting Riley Cycles Watch UI..."
echo "Installing/updating dependencies..."
python3 -m pip install -q -r requirements.txt

echo "Launching Streamlit (multipage format)..."
exec streamlit run app/Home.py --server.port 8501
