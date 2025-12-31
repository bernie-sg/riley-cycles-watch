# Production Cycles Detector Status

**Date:** 29-Dec-2025
**Issue:** Cycles Detector page showing empty on production (cycles.cosmicsignals.net)

---

## Local Status ✅

**Confirmed Working:**
- Flask server running on port 8082 (PIDs: 28840, 28853)
- Flask responding correctly to HTTP requests
- Cycles Detector page code compiles without errors
- Path resolution working correctly
- iframe configured correctly to http://localhost:8082
- Full Cycles Detector functionality available

**Test Results:**
```bash
curl http://localhost:8082
# Returns full HTML page with Cycles Detector UI
```

---

## Production Status (Last Verified)

**Server:** 82.25.105.47 (raysudo@cycles.cosmicsignals.net)
**Riley Port:** 8081
**Flask Port:** 8082

**Last Verified Actions:**
1. ✅ Flask server installed and running on port 8082
2. ✅ Dependencies installed (Flask, scipy, requests)
3. ✅ Riley restarted (PID: 1107922)
4. ✅ Page file exists: `/home/raysudo/riley-cycles/app/pages/3_Cycles_Detector.py`
5. ✅ Flask responds to localhost curl requests

**Current SSH Status:** ⚠️ Connection requires re-authentication

---

## Potential Issues & Solutions

### Issue 1: Browser Cache
**Symptom:** Page shows empty or old content
**Solution:** Clear browser cache and hard refresh (Ctrl+Shift+R or Cmd+Shift+R)

### Issue 2: Streamlit Not Detecting New Page
**Symptom:** Page not appearing in sidebar
**Solution:**
```bash
ssh raysudo@82.25.105.47
cd riley-cycles
pkill -f streamlit
source venv/bin/activate
nohup streamlit run app/Home.py --server.port 8081 --server.address 0.0.0.0 > logs/riley.log 2>&1 &
```

### Issue 3: Flask Server Not Running
**Symptom:** iframe shows connection error
**Solution:**
```bash
ssh raysudo@82.25.105.47
cd riley-cycles/cycles-detector
source ../venv/bin/activate
nohup python3 app.py > ../logs/flask.log 2>&1 &
```

**Verify Flask:**
```bash
lsof -i :8082 | grep LISTEN
curl http://localhost:8082 | head -20
```

### Issue 4: Port Not Accessible
**Symptom:** iframe shows "connection refused"
**Solution:**
```bash
# Check if port is listening
sudo lsof -i :8082

# Check firewall rules
sudo ufw status

# If needed, allow port
sudo ufw allow 8082
```

### Issue 5: iframe Cross-Origin Issues
**Symptom:** iframe shows blank but Flask works
**Check:** Browser console for CORS errors

**Solution:** Verify Flask app.py has:
```python
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    return response
```

---

## Verification Steps

### 1. Check Flask Server
```bash
ssh raysudo@82.25.105.47
lsof -i :8082 | grep LISTEN
curl http://localhost:8082 | head -50
```

**Expected:** HTML content starting with `<!DOCTYPE html>`

### 2. Check Riley Server
```bash
lsof -i :8081 | grep LISTEN
ps aux | grep streamlit
```

**Expected:** Streamlit process running on port 8081

### 3. Check Page File
```bash
cat /home/raysudo/riley-cycles/app/pages/3_Cycles_Detector.py | head -30
```

**Expected:** File contains Streamlit page code with iframe

### 4. Check Logs
```bash
tail -50 /home/raysudo/riley-cycles/logs/riley.log
tail -50 /home/raysudo/riley-cycles/logs/flask.log
```

**Look for:** Any errors or exceptions

### 5. Test from Browser
1. Go to https://cycles.cosmicsignals.net:8081
2. Click "Cycles Detector" in sidebar
3. Check browser console for errors (F12 → Console)
4. Check Network tab for failed requests

---

## File Locations

### Production Server
```
/home/raysudo/riley-cycles/
├── app/
│   └── pages/
│       └── 3_Cycles_Detector.py     ← Streamlit page with iframe
├── cycles-detector/
│   ├── app.py                        ← Flask server (port 8082)
│   ├── data_manager.py              ← Uses shared CSV files
│   └── templates/
│       └── index.html               ← Cycles Detector UI
├── data/
│   └── price_history/               ← Shared CSV files
├── venv/                             ← Python environment
└── logs/
    ├── riley.log                     ← Streamlit logs
    └── flask.log                     ← Flask logs
```

### Local (Working)
```
/Users/bernie/Documents/AI/Riley Project/
├── app/pages/3_Cycles_Detector.py   ← Same page (confirmed working)
├── cycles-detector/app.py           ← Same Flask app (confirmed working)
└── data/price_history/              ← Same CSV structure
```

---

## Next Steps

### If Page Shows Empty:

1. **Clear browser cache** - Most likely cause
2. **Restart Riley** - Ensure page is loaded
3. **Check Flask** - Verify it's actually running
4. **Check logs** - Look for any errors
5. **Browser console** - Check for JavaScript errors or failed requests

### If Still Not Working:

1. **Compare files** - Ensure production matches local
2. **Test Flask directly** - Access http://cycles.cosmicsignals.net:8082 directly (if port forwarded)
3. **Check iframe restrictions** - Some browsers block localhost in iframe
4. **Try different browser** - Rule out browser-specific issues

---

## Working Configuration (Local Reference)

### Page Code (Lines 104-124)
```python
# Main content
if server_running:
    # Embed Flask app in iframe - full screen
    st.markdown("""
    <style>
        /* Remove default Streamlit padding */
        .main .block-container {
            padding-top: 0rem;
            padding-bottom: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
        /* Make iframe fill entire viewport */
        iframe {
            width: 100%;
            height: calc(100vh - 100px);
            border: none;
        }
    </style>
    """, unsafe_allow_html=True)

    st.components.v1.iframe("http://localhost:8082", height=2000, scrolling=True)
```

### Flask Server Status (Local)
```bash
$ lsof -i :8082 | grep LISTEN
Python   28840 bernie    7u  IPv4 ... TCP *:us-cli (LISTEN)
Python   28853 bernie    7u  IPv4 ... TCP *:us-cli (LISTEN)

$ curl http://localhost:8082 | head -10
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    ...
```

---

## Summary

**Status:** Local environment fully functional, production requires verification

**Most Likely Issue:** Browser cache or Streamlit needs restart to detect new page

**Immediate Action:** Clear browser cache and hard refresh

**If That Fails:** SSH into production and verify Flask + Riley are both running

---

**End of Status Document**
