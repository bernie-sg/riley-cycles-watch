#!/bin/bash
# Deploy updated files to remote server and restart

SERVER="raysudo@82.25.105.47"
REMOTE_PATH="~/webapp"  # Adjust this to your actual path on the server

echo "================================"
echo "Deploying to Remote Server"
echo "================================"
echo ""

# Files to deploy
FILES="data_manager.py app.py restart_server.sh"

echo "Step 1: Copying updated files to server..."
scp $FILES $SERVER:$REMOTE_PATH/

echo ""
echo "Step 2: Making restart script executable..."
ssh $SERVER "chmod +x $REMOTE_PATH/restart_server.sh"

echo ""
echo "Step 3: Restarting server..."
ssh $SERVER "cd $REMOTE_PATH && ./restart_server.sh"

echo ""
echo "================================"
echo "Deployment Complete!"
echo "================================"
