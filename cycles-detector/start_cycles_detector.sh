#!/bin/bash
# Start Cycles Detector Flask Server
# This script starts the Cycles Detector V14 web application

cd "$(dirname "$0")"

echo "Starting Cycles Detector V14..."
echo "Port: 8082"
echo "URL: http://localhost:8082"
echo ""

# Run Flask app
python3 app.py
