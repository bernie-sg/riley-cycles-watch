# Cycles Detector - Quick Start Guide

**Last Updated:** 29-Dec-2025
**Status:** ✅ Working on localhost | ⚠️ Production needs verification

---

## Accessing Cycles Detector

### Local (Working)

1. **Start Riley:**
   ```bash
   cd /Users/bernie/Documents/AI/Riley\ Project
   streamlit run app/Home.py
   ```

2. **Navigate to Cycles Detector:**
   - Open browser: http://localhost:8501
   - Click "Cycles Detector" in left sidebar

3. **Start Cycles Detector Server:**
   - Click "▶️ Start Server" button in sidebar
   - Wait ~5 seconds for server to start
   - Page will refresh automatically

4. **Use Cycles Detector:**
   - Cycles Detector appears embedded in page
   - Enter symbol (e.g., SPY, AAPL, MSFT)
   - Select analysis parameters
   - View cycle projections and heatmaps

### Production

1. **Access Riley:**
   - Open browser: https://cycles.cosmicsignals.net:8081

2. **Navigate to Cycles Detector:**
   - Click "Cycles Detector" in left sidebar

3. **Start Server (if not running):**
   - Click "▶️ Start Server"
   - Wait for server to start
   - Page refreshes automatically

---

## Features Available

### All Cycles Detector V14 Features

- ✅ **MESA Cycle Detection** - Maximum Entropy Spectral Analysis
- ✅ **Morlet Wavelet Analysis** - Time-frequency decomposition
- ✅ **Bandpass Filtering** - Pure sine wave projection
- ✅ **Cycle Heatmaps** - Visual evolution over time
- ✅ **Quality Metrics** - Bartels test, component yield, health scores
- ✅ **Multi-Algorithm Support** - Compare different detection methods
- ✅ **Progress Tracking** - Real-time analysis updates
- ✅ **Interactive Charts** - D3.js/Plotly visualizations

### Data Integration

- ✅ **Shared CSV System** - Uses `data/price_history/`
- ✅ **Auto-Download** - Fetches symbol on first use
- ✅ **Auto-Update** - Appends new bars when outdated
- ✅ **RRG Compatible** - Shares data with RRG feature

---

## Common Symbols to Test

### Market Indices
- **SPY** - S&P 500
- **QQQ** - Nasdaq 100
- **DIA** - Dow Jones
- **IWM** - Russell 2000

### Sector ETFs
- **XLK** - Technology
- **XLF** - Financials
- **XLE** - Energy
- **XLV** - Healthcare

### Popular Stocks
- **AAPL** - Apple
- **MSFT** - Microsoft
- **TSLA** - Tesla
- **NVDA** - Nvidia

---

## Typical Workflow

1. **Enter Symbol**
   - Type ticker in symbol field
   - Click "Analyze" or press Enter

2. **Set Parameters**
   - Min wavelength: 5-20 bars (short cycles)
   - Max wavelength: 20-100 bars (longer cycles)
   - Projection length: 20-60 bars forward

3. **Select Algorithm**
   - **MESA** - Best for dominant cycles
   - **Morlet** - Best for multi-timeframe analysis
   - **Bandpass** - Best for pure sine projection

4. **View Results**
   - **Price Chart** - Current price with cycle overlay
   - **Cycle Projection** - Forward projection based on detected cycle
   - **Heatmap** - Evolution of cycles over time
   - **Quality Metrics** - Statistical measures of cycle strength

5. **Interpret Quality Metrics**
   - **Bartels Test** - Higher is better (>0.7 good)
   - **Component Yield** - Percent variance explained
   - **Cycle Health** - Overall quality score

---

## Data Storage

### Price History Files
All symbol price data stored in:
```
data/price_history/
├── spy_history.csv
├── aapl_history.csv
├── msft_history.csv
└── ... (auto-created on first use)
```

### CSV Format
```csv
Date,Close
2020-01-02,324.87
2020-01-03,322.94
...
2025-12-26,690.31
```

### Automatic Updates
- **First download:** Full history from Yahoo Finance (~10-30 years)
- **Updates:** Appends only new bars since last date
- **Frequency:** Checked on each access, updates if >1 day old

---

## Server Management

### Manual Start (If Auto-Start Fails)

**Local:**
```bash
cd /Users/bernie/Documents/AI/Riley\ Project/cycles-detector
python3 app.py
```

**Production:**
```bash
ssh raysudo@82.25.105.47
cd riley-cycles/cycles-detector
source ../venv/bin/activate
python3 app.py
```

### Check Server Status

**Local:**
```bash
lsof -i :8082 | grep LISTEN
curl http://localhost:8082 | head -20
```

**Production:**
```bash
ssh raysudo@82.25.105.47
lsof -i :8082 | grep LISTEN
curl http://localhost:8082 | head -20
```

### Stop Server

**Local:**
```bash
pkill -f "python3.*cycles-detector.*app.py"
```

**Production:**
```bash
ssh raysudo@82.25.105.47
pkill -f "python3.*cycles-detector.*app.py"
```

Or use the "🛑 Stop Server" button in the Cycles Detector page sidebar.

---

## Troubleshooting

### Server Won't Start

**Check port availability:**
```bash
lsof -i :8082
```

**If port in use, kill the process:**
```bash
kill -9 <PID>
```

**Then try starting again:**
```bash
cd cycles-detector
python3 app.py
```

### Page Shows Empty

1. **Clear browser cache** - Ctrl+Shift+R (or Cmd+Shift+R on Mac)
2. **Restart Riley** - Stop and restart Streamlit
3. **Check Flask** - Verify port 8082 is listening
4. **Check browser console** - F12 → Console for errors

### Symbol Not Found

**Symptom:** "No data available for symbol XYZ"

**Cause:** Invalid ticker or delisted stock

**Solution:** Verify ticker exists on Yahoo Finance

### Analysis Fails

**Symptom:** "Analysis failed" or blank charts

**Possible causes:**
- Not enough data (need >100 bars minimum)
- Wavelength range too narrow
- Recent IPO with limited history

**Solution:**
- Increase max wavelength
- Use longer history symbol
- Check data file has sufficient bars

### Slow Performance

**Symptom:** Analysis takes >30 seconds

**Causes:**
- Large dataset (>10,000 bars)
- Wide wavelength range
- Multiple algorithm comparison

**Solutions:**
- Reduce date range
- Narrow wavelength range
- Run one algorithm at a time

---

## Advanced Tips

### Finding Dominant Cycle

1. Start with wide wavelength range (5-100)
2. Run MESA analysis
3. Note wavelength with highest amplitude
4. Re-run with narrow range around that wavelength
5. Check heatmap for consistency over time

### Comparing Algorithms

1. Run same symbol through MESA, Morlet, and Bandpass
2. Compare detected wavelengths
3. If all agree → high confidence
4. If divergent → cycle may be weak or changing

### Time Range Selection

**Short cycles (intraday traders):**
- Min: 5 bars
- Max: 20 bars
- Best for: Daily charts, short-term swings

**Medium cycles (swing traders):**
- Min: 10 bars
- Max: 40 bars
- Best for: Daily/weekly charts, multi-week swings

**Long cycles (position traders):**
- Min: 20 bars
- Max: 100 bars
- Best for: Weekly charts, multi-month trends

### Quality Metrics Interpretation

**Bartels Test:**
- > 0.8 - Excellent cycle strength
- 0.6-0.8 - Good cycle strength
- 0.4-0.6 - Moderate cycle strength
- < 0.4 - Weak or no cycle

**Component Yield:**
- > 30% - Dominant cycle explains significant variance
- 15-30% - Moderate contribution
- < 15% - Weak cycle influence

---

## Integration with Riley

### Shared Data with RRG

Cycles Detector and RRG both use the same price history files:
- **Symbol:** SPY, XLK, XLY, etc.
- **Location:** `data/price_history/`
- **Format:** Date, Close columns
- **Updates:** Automatic append on access

### Use with Cycle Specs

After detecting a cycle in Cycles Detector:

1. Note the dominant wavelength (e.g., 37 bars)
2. Note a recent cycle low date (e.g., 2026-01-04)
3. Add to Riley cycle specs:
   ```bash
   python3 scripts/cycles_set_spec.py \
     --symbol ES --tf WEEKLY \
     --anchor 2026-01-04 --len 37 \
     --source "Cycles Detector MESA"
   ```

4. Run scan to get projections:
   ```bash
   python3 scripts/cycles_run_scan.py --asof 2025-12-29
   ```

---

## Performance Notes

### Typical Analysis Times

- **MESA:** ~3-8 seconds
- **Morlet:** ~5-12 seconds
- **Bandpass:** ~2-5 seconds
- **Heatmap:** +5-10 seconds

### Dataset Sizes

- **SPY:** ~8,000 bars (30+ years)
- **AAPL:** ~10,000 bars (40+ years)
- **Recent IPO:** ~500-1000 bars

### Memory Usage

- Flask server: ~100-200 MB
- Analysis peak: ~300-500 MB
- CSV files: ~50-200 KB each

---

## Summary

**Access:** Riley → Cycles Detector → Start Server → Analyze

**Features:** MESA, Morlet, Bandpass, Heatmaps, Quality Metrics

**Data:** Shared CSV files, auto-download, auto-update

**Integration:** Works with Riley cycle specs and RRG data

**Status:** Fully functional locally, production needs browser cache clear

---

**End of Quick Start Guide**
