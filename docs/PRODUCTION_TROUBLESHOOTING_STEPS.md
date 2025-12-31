# Production Cycles Detector Troubleshooting Steps

**Issue:** Blank screen when accessing Cycles Detector page
**Status Shows:** Server Running (green checkmark)
**Actual Result:** Empty iframe

---

## Step 1: Verify Flask is Actually Running

SSH into the server and check:

```bash
ssh raysudo@82.25.105.47

# Check if Flask is running
lsof -i :8082 | grep LISTEN

# Check Flask process
ps aux | grep "app.py" | grep -v grep

# Test Flask response
curl http://localhost:8082 | head -30
```

**Expected:**
- `lsof` should show Python listening on port 8082
- `ps aux` should show app.py process
- `curl` should return HTML content starting with `<!DOCTYPE html>`

**If Flask is NOT running:**
```bash
cd /home/raysudo/riley-cycles/cycles-detector
source ../venv/bin/activate
nohup python3 app.py > ../logs/flask.log 2>&1 &
```

---

## Step 2: Check Flask Logs

```bash
cd /home/raysudo/riley-cycles
tail -50 logs/flask.log
```

**Look for:**
- Any error messages
- Port binding errors
- Module import errors

---

## Step 3: Check Riley Logs

```bash
tail -50 logs/riley.log
```

**Look for:**
- Streamlit errors
- Page loading errors
- Import errors

---

## Step 4: Verify Page File

```bash
cat /home/raysudo/riley-cycles/app/pages/3_Cycles_Detector.py | head -50
```

**Should see:**
- Import statements for streamlit, requests, subprocess
- check_server_running() function
- iframe embedding code

---

## Step 5: Test Direct Flask Access

From your local browser, try accessing:
```
http://82.25.105.47:8082
```

**If this works:**
- Flask is running and accessible
- Issue is with iframe or Streamlit integration

**If this doesn't work:**
- Port 8082 may not be open to external access
- This is actually EXPECTED - Flask should only be accessible on localhost
- The iframe uses localhost:8082, which works when Streamlit is on the same server

---

## Step 6: Check Browser Console

On the blank Cycles Detector page:
1. Press F12 to open developer tools
2. Go to Console tab
3. Look for errors

**Common errors:**
- "Refused to display in a frame" - iframe blocking
- "net::ERR_CONNECTION_REFUSED" - Flask not running
- "Mixed Content" - HTTP/HTTPS mismatch

Take a screenshot of any errors and share them.

---

## Step 7: Restart Everything

If still not working, restart both services:

```bash
ssh raysudo@82.25.105.47
cd /home/raysudo/riley-cycles

# Stop Flask
pkill -f "app.py"

# Stop Riley
pkill -f "streamlit"

# Start Flask
cd cycles-detector
source ../venv/bin/activate
nohup python3 app.py > ../logs/flask.log 2>&1 &
cd ..

# Wait 3 seconds
sleep 3

# Start Riley
nohup streamlit run app/Home.py --server.port 8081 --server.address 0.0.0.0 > logs/riley.log 2>&1 &

# Verify both running
sleep 3
lsof -i :8082 | grep LISTEN  # Flask
lsof -i :8081 | grep LISTEN  # Riley
```

Then refresh your browser (hard refresh: Ctrl+Shift+R).

---

## Step 8: Alternative - Manual Flask Window

If iframe continues to fail, you can access Flask directly:

1. Keep Flask running on port 8082
2. Set up SSH tunnel from your local machine:
   ```bash
   ssh -L 8082:localhost:8082 raysudo@82.25.105.47
   ```
3. Access in browser: `http://localhost:8082`

This bypasses the iframe and gives you direct access to Cycles Detector.

---

## Quick Diagnostic Script

Save this as `check_cycles.sh` and run it:

```bash
#!/bin/bash
echo "=== Cycles Detector Diagnostic ==="
echo ""
echo "1. Flask Server:"
lsof -i :8082 | grep LISTEN || echo "   ❌ NOT RUNNING"
echo ""
echo "2. Riley Server:"
lsof -i :8081 | grep LISTEN || echo "   ❌ NOT RUNNING"
echo ""
echo "3. Flask Response:"
curl -s http://localhost:8082 | head -5 || echo "   ❌ NO RESPONSE"
echo ""
echo "4. Recent Flask Logs:"
tail -10 logs/flask.log
echo ""
echo "5. Recent Riley Logs:"
tail -10 logs/riley.log
```

Run with:
```bash
cd /home/raysudo/riley-cycles
bash check_cycles.sh
```

---

**End of Troubleshooting Steps**
