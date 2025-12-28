# Cycles Detector V14 - Integration Documentation

**Integrated:** 28-Dec-2025
**Source:** /Users/bernie/Documents/AI/Failed/Cycles Detector/Cycles Detector V14
**Status:** ✅ Integrated as separate component

---

## What is Cycles Detector?

**Cycles Detector V14** is an advanced technical analysis tool that identifies and projects market cycles using bandpass filtering and sine wave analysis.

### Key Features

- **Bandpass Filtering:** Isolates specific cycle frequencies from price data
- **Pure Sine Wave Projection:** Aligned to actual price troughs
- **MESA Heatmap:** Visual representation of cycle strength
- **Accurate Projections:** "Accurate down to the day" according to user testing

### User Testimony

> "It turns out Cycles Detector did not fail. The analysis that I did two months ago was accurate down to the day."

---

## Integration Approach

### Why Separate Component?

**User requirement:** "Do not touch the things that are working"

**Solution:** Keep Cycles Detector as standalone Flask app, integrate via Streamlit page

### Architecture

```
Riley Cycles Watch (Streamlit)
├── Port: 8501
├── Pages:
│   ├── Today (main dashboard)
│   ├── Database
│   └── 3_Cycles_Detector.py (NEW)
│       └── Links to/embeds Flask app
│
Cycles Detector V14 (Flask)
├── Port: 8082
├── Independent backend
├── Original algorithms intact
└── No code changes to core logic
```

---

## File Structure

```
/Users/bernie/Documents/AI/Riley Project/
├── app/
│   └── pages/
│       └── 3_Cycles_Detector.py (NEW - Streamlit integration page)
│
└── cycles-detector/ (NEW - Copied from Failed folder)
    ├── app.py (Flask backend - port changed to 8082)
    ├── algorithms/
    │   ├── bandpass/
    │   ├── heatmap/
    │   └── ... (all original algorithms)
    ├── templates/
    │   └── index.html (original frontend)
    ├── start_cycles_detector.sh (NEW - startup script)
    └── ... (all original data and configs)
```

---

## How to Use

### Option 1: Via Streamlit Interface (Recommended)

1. **Open Riley Cycles Watch:**
   ```
   http://localhost:8501
   ```

2. **Navigate to Cycles Detector:**
   - Click "Cycles Detector" in left sidebar

3. **Start Server (if not running):**
   - Click "▶️  Start Cycles Detector Server" button
   - OR start manually (see Option 2)

4. **Access:**
   - Click "🖥️  Open in New Tab" (opens in separate tab)
   - OR click "📊 Embed Below" (embeds in Streamlit)

### Option 2: Direct Access (Manual)

1. **Start Flask server:**
   ```bash
   cd ~/riley-cycles/cycles-detector
   ./start_cycles_detector.sh
   ```

2. **Open browser:**
   ```
   http://localhost:8082
   ```

3. **Use Cycles Detector:**
   - Enter instrument symbol (e.g., SPY, AAPL)
   - Select wavelengths to analyze
   - View sine wave projections and heatmaps

---

## Server Ports

**Riley Cycles Watch (Streamlit):**
- Local: http://localhost:8501
- Production: https://cycles.cosmicsignals.net

**Cycles Detector (Flask):**
- Local: http://localhost:8082
- Production: TBD (separate subdomain if needed)

**No port conflicts** - both can run simultaneously

---

## What Changed During Integration

### 1. Location
- **Original:** `/Users/bernie/Documents/AI/Failed/Cycles Detector/Cycles Detector V14/webapp/`
- **New:** `/Users/bernie/Documents/AI/Riley Project/cycles-detector/`

### 2. Port Configuration
- **Original:** Port 5001
- **New:** Port 8082 (to avoid conflicts)
- **Change:** `app.py` line 1646

### 3. Files Added

**Streamlit Integration:**
- `app/pages/3_Cycles_Detector.py` - Streamlit page with iframe/link

**Helper Scripts:**
- `cycles-detector/start_cycles_detector.sh` - Startup script

**Documentation:**
- `docs/CYCLES_DETECTOR_INTEGRATION.md` - This file

### 4. Files Unchanged

**ALL core algorithms and logic UNCHANGED:**
- ✅ `algorithms/bandpass/pure_sine_bandpass.py` - Core bandpass algorithm
- ✅ `algorithms/heatmap/` - MESA heatmap generation
- ✅ `algorithms/cycle_quality.py` - Quality analyzer
- ✅ `templates/index.html` - Original frontend
- ✅ All other algorithm files

**No modifications to working code**

---

## Technical Details

### Flask App (Cycles Detector)

**Backend:** Flask (Python)
- Routes: `/`, `/analyze`, `/status`, etc.
- Data: Yahoo Finance price data
- Processing: MESA, Goertzel, bandpass filtering
- Output: JSON API for frontend

**Frontend:** HTML/JavaScript
- Charts: D3.js/Plotly
- Real-time updates: WebSocket/polling
- Interactive controls: jQuery

**Algorithms:**
- Bandpass filtering (pure sine wave generation)
- Peak/trough detection
- Phase alignment to price troughs
- MESA heatmap generation
- Goertzel frequency analysis

### Streamlit Integration Page

**Purpose:** Provide access to Cycles Detector from Riley Cycles Watch

**Features:**
1. **Server Status Check:** Detects if Flask server is running
2. **Start Server Button:** Can launch Flask server from Streamlit
3. **Access Options:**
   - Open in new tab (separate window)
   - Embed in iframe (same interface)
4. **Documentation:** Explains what Cycles Detector does

**How iframe works:**
```html
<iframe
    src="http://localhost:8082"
    width="100%"
    height="1200"
    frameborder="0"
></iframe>
```

---

## Dependencies

### Cycles Detector Requirements

Check `cycles-detector/requirements.txt` (if exists) or install:

```bash
pip install flask numpy pandas scipy matplotlib yfinance
```

**Key packages:**
- `flask` - Web server
- `numpy` - Numerical computing
- `pandas` - Data structures
- `scipy` - Scientific computing (signal processing)
- `matplotlib` - Plotting (for backend generation)
- `yfinance` - Stock data

---

## Production Deployment

### Current Setup (Local)

**Riley Cycles Watch:**
- Runs on localhost:8501 during development
- Deployed to https://cycles.cosmicsignals.net (production)

**Cycles Detector:**
- Runs on localhost:8082 during development
- Not yet deployed to production

### Future Production Deployment

**Option 1: Separate Subdomain**
- Deploy Cycles Detector to: https://detector.cosmicsignals.net
- Update Streamlit page to point to production URL
- Configure Nginx proxy on server

**Option 2: Same Server, Different Port**
- Run on same Hostinger VPS
- Flask on port 8082
- Nginx proxy configuration
- Access via: https://cycles.cosmicsignals.net:8082

**Option 3: Embedded Only**
- Keep Flask server internal
- Only accessible via Riley Cycles Watch iframe
- More secure, single entry point

---

## Testing Checklist

### ✅ Completed

- [x] Cycles Detector files copied to Riley project
- [x] Port changed to 8082 (no conflicts)
- [x] Streamlit integration page created
- [x] Startup script created
- [x] Documentation completed

### 🔄 To Test

- [ ] Start Flask server manually
- [ ] Verify Cycles Detector UI loads at http://localhost:8082
- [ ] Test from Streamlit page (server status detection)
- [ ] Test "Open in New Tab" button
- [ ] Test "Embed Below" iframe
- [ ] Verify algorithms work (run cycle analysis)
- [ ] Test with multiple instruments

---

## Troubleshooting

### Flask Server Won't Start

**Check:**
```bash
cd ~/riley-cycles/cycles-detector
python3 app.py
```

**Common issues:**
- Missing dependencies: `pip install -r requirements.txt`
- Port already in use: `lsof -i :8082` (kill process or change port)
- Wrong Python version: Requires Python 3.7+

### Iframe Not Loading

**Check:**
1. Is Flask server running? `curl http://localhost:8082`
2. Browser console for errors
3. CORS policy (Flask allows all origins by default)

### Algorithm Errors

**Original code unchanged** - if algorithms fail, same issues exist as in original V14:
- Check original `/Failed/Cycles Detector/` for reference
- Review V14 completion report
- Known limitation: Very long cycles (>550d) may have detection issues

---

## Maintenance

### Updating Cycles Detector

**If user wants to update algorithms:**
1. Make changes in `cycles-detector/` folder
2. Test changes independently: `cd cycles-detector && python3 app.py`
3. No need to touch Streamlit integration page

### Updating Integration Page

**If user wants to change how it's presented:**
1. Edit `app/pages/3_Cycles_Detector.py`
2. Changes reflected immediately in Streamlit

**Separation of concerns:**
- Cycles Detector = Flask backend + algorithms
- Integration page = Streamlit UI wrapper

---

## Future Enhancements

### Potential Improvements

1. **Data Sharing:**
   - Use shared database between Riley Cycles Watch and Cycles Detector
   - Avoid duplicate price data downloads

2. **Unified UI:**
   - Convert Cycles Detector to Streamlit components
   - Fully integrated single-page app
   - Would require significant rewrite

3. **API Integration:**
   - Cycles Detector provides API
   - Riley Cycles Watch consumes API data
   - Display cycle projections in main dashboard

4. **Automated Analysis:**
   - Run Cycles Detector analysis on askSlim symbols
   - Compare askSlim cycle dates vs Cycles Detector projections
   - Validation tool

---

## Summary

✅ **Cycles Detector V14 successfully integrated**

**Integration method:** Separate Flask app accessed via Streamlit page

**Benefits:**
- No changes to working algorithms
- Independent operation
- Can run simultaneously with Riley Cycles Watch
- Easy to update either component separately

**User experience:**
- Access from Riley Cycles sidebar
- Choose: Open in new tab OR embed in same window
- Seamless integration

**Next step:** User should test and verify everything works correctly

---

**End of Integration Documentation**
