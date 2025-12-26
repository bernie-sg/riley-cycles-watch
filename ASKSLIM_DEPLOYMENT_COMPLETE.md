# askSlim Scraper - Server Deployment Summary

**Date:** December 26, 2025  
**Server:** 82.25.105.47 (raysudo@riley-cycles)  
**Status:** ⚠️  AWAITING FINAL STEP - System Dependencies Installation

---

## ✅ What's Been Deployed

### 1. Code & Scripts
- ✅ askSlim scraper modules (`src/riley/modules/askslim/`)
- ✅ All Python scraper scripts (login, futures, equities)
- ✅ Database migration applied
- ✅ Database with all 73 instruments scraped

### 2. Dependencies
- ✅ Python packages: `playwright==1.57.0`, `python-dotenv==1.2.1`
- ✅ Playwright Chromium Headless Shell (173 MB)
- ✅ FFMPEG for media support

### 3. Configuration
- ✅ `.env` file with askSlim credentials (headless mode enabled)
- ✅ Session state file (`storage_state.json`)
- ✅ All 89 analysis records with scraped data

### 4. Scraped Data Already On Server
- ✅ 73 instruments (18 futures + 55 equities/ETFs)
- ✅ Directional bias for all instruments
- ✅ Video URLs where available
- ✅ Support/resistance levels
- ✅ Cycle specs with anchors and lengths

---

## ⚠️  FINAL STEP REQUIRED

**System libraries are missing** - Chromium needs these to run in headless mode.

### Install Command (Requires sudo)

```bash
cd ~/riley-cycles
sudo bash install_chromium_deps.sh
```

This will install:
- libnss3, libnspr4 (Network Security)
- libatk1.0-0, libatk-bridge2.0-0 (Accessibility)
- libcups2 (Printing)
- libdrm2, libgbm1 (Graphics)
- libxkbcommon0, libxcomposite1, libxdamage1, libxfixes3, libxrandr2 (X11)
- libpango-1.0-0, libcairo2 (Text rendering)
- libasound2 (Audio)
- libatspi2.0-0 (Assistive tech)

**Time required:** ~30 seconds

---

## 🧪 Testing After Installation

### 1. Smoke Test
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_smoketest.py
```

**Expected output:** "✅ Smoketest passed - askSlim is accessible"

### 2. Test Single Instrument (GC - Gold)
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/demo_gc.py
```

**Expected:** Successfully scrapes GC data and updates database

### 3. Full Futures Scrape (18 instruments)
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_scraper.py
```

**Expected:** 18/18 instruments scraped successfully (~5-10 minutes)

### 4. Full Equities Scrape (55 instruments)
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_equities_scraper.py
```

**Expected:** 55/55 instruments scraped successfully (~15-20 minutes)

---

## 🔄 Daily Automation Setup

### Option 1: Single Daily Run Script

Run both futures and equities in one command:

```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_run_daily.py
```

### Option 2: Cron Job (Recommended)

Add to crontab for daily automation at 1 AM server time:

```bash
crontab -e
```

Add this line:
```cron
0 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_run_daily.py >> logs/askslim_daily.log 2>&1
```

**What this does:**
- Runs every day at 1:00 AM
- Scrapes all futures (18) and equities (55)
- Updates database with latest cycle specs
- Rebuilds cycle projections
- Logs output to `logs/askslim_daily.log`

### Option 3: Separate Cron Jobs

If you want to run futures and equities at different times:

```cron
# Futures at 1 AM
0 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_scraper.py >> logs/askslim_futures.log 2>&1

# Equities at 2 AM
0 2 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_equities_scraper.py >> logs/askslim_equities.log 2>&1
```

---

## 📊 Monitoring

### Check Scraper Logs
```bash
# Daily automation log
tail -f ~/riley-cycles/logs/askslim_daily.log

# Futures scraper log
tail -f ~/riley-cycles/logs/askslim_futures.log

# Equities scraper log
tail -f ~/riley-cycles/logs/askslim_equities.log
```

### Verify Database Updates
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 << 'PYEOF'
import sqlite3
from datetime import datetime

conn = sqlite3.connect('db/riley.sqlite')
cursor = conn.cursor()

# Check last update
cursor.execute("""
    SELECT MAX(updated_at) as last_update 
    FROM instrument_analysis
""")
print(f"Last askSlim update: {cursor.fetchone()[0]}")

# Count active instruments
cursor.execute("""
    SELECT COUNT(*) FROM instrument_analysis WHERE status = 'ACTIVE'
""")
print(f"Active instruments: {cursor.fetchone()[0]}")
conn.close()
PYEOF
```

---

## 🔐 Security Notes

- askSlim credentials stored in `.env` (not in git)
- Session state persisted in `storage_state.json`
- Headless mode enabled (no display required)
- 4-8 second delays between requests (bot detection avoidance)
- Session auto-refresh if login expires

---

## 📝 Quick Reference

```bash
# Install dependencies (ONE TIME - requires sudo)
sudo bash ~/riley-cycles/install_chromium_deps.sh

# Test scraper
cd ~/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_smoketest.py

# Run daily scrape manually
cd ~/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_run_daily.py

# Set up cron job
crontab -e
# Add: 0 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_run_daily.py >> logs/askslim_daily.log 2>&1

# Check logs
tail -f ~/riley-cycles/logs/askslim_daily.log

# Restart Riley Cycles app after updates
pkill -f 'streamlit.*riley'; cd ~/riley-cycles && nohup ./run_riley.sh > logs/riley.log 2>&1 &
```

---

## ✅ Next Steps

1. **Install system dependencies:**
   ```bash
   sudo bash ~/riley-cycles/install_chromium_deps.sh
   ```

2. **Test the scraper:**
   ```bash
   cd ~/riley-cycles && source venv/bin/activate
   python3 src/riley/modules/askslim/askslim_smoketest.py
   ```

3. **Set up daily cron job:**
   ```bash
   crontab -e
   # Add the cron line from above
   ```

4. **Verify in Riley Cycles UI:**
   - Visit: https://cycles.cosmicsignals.net
   - Check "Today" page shows all active instruments
   - Verify askSlim data appears in instrument details

---

**Deployment completed by:** Claude Code  
**GitHub backup:** Committed and pushed to main branch  
**Commit:** Major: Add askSlim scraper integration with full automation

