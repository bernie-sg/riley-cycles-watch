#!/bin/bash
# Restart script for Cycles Detector production server
# Usage: ./restart_server.sh

echo "========================================"
echo "Cycles Detector - Server Restart Script"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Step 1: Stopping existing server...${NC}"
# Try graceful shutdown first
if [ -f logs/gunicorn.pid ]; then
    PID=$(cat logs/gunicorn.pid)
    echo "Found PID file: $PID"
    if kill -0 $PID 2>/dev/null; then
        kill $PID
        echo -e "${GREEN}✓ Sent shutdown signal to PID $PID${NC}"
        sleep 2
    else
        echo -e "${YELLOW}⚠ PID $PID not running, cleaning up PID file${NC}"
        rm -f logs/gunicorn.pid
    fi
else
    echo "No PID file found"
fi

# Force kill any remaining gunicorn processes
echo "Checking for remaining gunicorn processes..."
REMAINING=$(pgrep -f "gunicorn.*wsgi:app" || true)
if [ ! -z "$REMAINING" ]; then
    echo -e "${YELLOW}⚠ Found remaining processes: $REMAINING${NC}"
    pkill -f "gunicorn.*wsgi:app" || true
    sleep 1
    echo -e "${GREEN}✓ Killed remaining processes${NC}"
else
    echo -e "${GREEN}✓ No remaining processes${NC}"
fi

echo ""
echo -e "${YELLOW}Step 2: Creating logs directory...${NC}"
mkdir -p logs
echo -e "${GREEN}✓ Logs directory ready${NC}"

echo ""
echo -e "${YELLOW}Step 3: Starting production server...${NC}"
gunicorn -c gunicorn_config.py wsgi:app &
sleep 3

echo ""
echo -e "${YELLOW}Step 4: Verifying server is running...${NC}"
if pgrep -f "gunicorn.*wsgi:app" > /dev/null; then
    PID=$(pgrep -f "gunicorn.*wsgi:app" | head -1)
    echo -e "${GREEN}✓ Server is running! PID: $PID${NC}"
    echo ""
    echo "Access the application at: http://localhost:5001"
    echo "or http://YOUR_SERVER_IP:5001"
    echo ""
    echo "To view logs:"
    echo "  Error log:  tail -f logs/error.log"
    echo "  Access log: tail -f logs/access.log"
    echo ""
    echo -e "${GREEN}========================================"
    echo "Server restart completed successfully!"
    echo "========================================${NC}"
else
    echo -e "${RED}✗ Server failed to start!${NC}"
    echo ""
    echo "Check the error log for details:"
    echo "  tail -50 logs/error.log"
    echo ""
    echo -e "${RED}========================================"
    echo "Server restart FAILED!"
    echo "========================================${NC}"
    exit 1
fi
