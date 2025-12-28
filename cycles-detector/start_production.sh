#!/bin/bash
# Production startup script for Cycles Detector

# Create logs directory if it doesn't exist
mkdir -p logs

# Activate virtual environment if you have one
# source venv/bin/activate

# Start Gunicorn with configuration
gunicorn -c gunicorn_config.py wsgi:app
