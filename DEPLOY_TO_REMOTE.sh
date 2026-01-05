#!/bin/bash
# Deploy fixes to remote server
# Run this from your local Mac

set -e

REMOTE_USER="raysudo"
REMOTE_HOST="45.76.168.214"
REMOTE_DIR="/home/raysudo/riley-cycles"
LOCAL_DIR="/Users/bernie/Documents/AI/Riley Project"

echo "🚀 Deploying Riley fixes to remote server..."
echo ""

# Test SSH connectivity first
echo "1️⃣ Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} "echo 'Connected'" 2>/dev/null; then
    echo "❌ SSH connection failed!"
    echo ""
    echo "Please check:"
    echo "  - Is the server running?"
    echo "  - Is SSH service running on the server?"
    echo "  - Can you manually SSH: ssh ${REMOTE_USER}@${REMOTE_HOST}"
    echo ""
    exit 1
fi

echo "✅ SSH connection OK"
echo ""

# Deploy db.py with filter fixes
echo "2️⃣ Deploying db.py with filter fixes..."
scp "${LOCAL_DIR}/app/db.py" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/app/db.py
echo "✅ db.py deployed"
echo ""

# Deploy sector fix script
echo "3️⃣ Deploying sector fix script..."
scp "${LOCAL_DIR}/scripts/fix_remote_sectors.py" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/fix_sectors.py
echo "✅ Sector fix script deployed"
echo ""

# Deploy chart migration script
echo "4️⃣ Deploying chart migration script..."
scp "${LOCAL_DIR}/scripts/migrate_existing_charts.py" ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_DIR}/migrate_charts.py
echo "✅ Chart migration script deployed"
echo ""

# Run fixes on remote
echo "5️⃣ Running fixes on remote server..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'EOF'
cd /home/raysudo/riley-cycles

echo "  → Fixing instrument sectors..."
python3 fix_sectors.py

echo ""
echo "  → Migrating charts..."
python3 migrate_charts.py

echo ""
echo "  → Restarting Streamlit service..."
sudo systemctl restart riley-cycles-streamlit

echo ""
echo "  → Waiting for service to start..."
sleep 3

echo ""
echo "  → Service status:"
sudo systemctl status riley-cycles-streamlit --no-pager | head -10

echo ""
echo "✅ All fixes applied on remote server!"
EOF

echo ""
echo "🎉 Deployment complete!"
echo ""
echo "Next steps:"
echo "  1. Open https://cycles.cosmicalsignals.net"
echo "  2. Verify sectors are no longer UNCLASSIFIED"
echo "  3. Verify Group/Sector filters work"
echo "  4. Click through instruments and verify charts are displaying"
echo ""
