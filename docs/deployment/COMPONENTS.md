# Riley Cycles Watch - Component Deployment Guide

**Last Updated:** 28-Dec-2025
**Components:** askSlim Scraper, Market Data Module

---

## Overview

This guide covers deployment of the two main data collection components:
1. **askSlim Scraper** - Collects cycle data from askSlim.com
2. **Market Data Module** - Fetches price data from Yahoo Finance for RRG

Both components are **fully deployed and operational** on the server.

---

# 1. askSlim Scraper

## Purpose
Automated scraper that collects cycle analysis data from askSlim.com using headless Chromium.

## What It Collects
- Cycle anchor dates and lengths (DAILY/WEEKLY)
- Directional bias (Bullish/Bearish)
- Support and resistance levels
- Video analysis URLs

## Instruments Covered
- **18 Futures:** ES, NQ, RTY, GC, SI, CL, NG, HG, PL, PA, ZC, ZW, ZS, BTC, ETH, etc.
- **55 Equities/ETFs:** AAPL, MSFT, NVDA, SPY, QQQ, sector ETFs, etc.
- **Total:** 73 instruments

---

## Server Deployment Status

### ✅ Fully Deployed Components

1. **Code & Modules**
   - ✅ All scraper scripts in `src/riley/modules/askslim/`
   - ✅ Database migration applied
   - ✅ 73 instruments configured in database

2. **Dependencies**
   - ✅ Python packages: `playwright==1.57.0`, `python-dotenv==1.2.1`
   - ✅ Playwright Chromium Headless Shell (173 MB)
   - ✅ System libraries for headless mode
   - ✅ FFMPEG for media support

3. **Configuration**
   - ✅ `.env` file with credentials (headless mode enabled)
   - ✅ Session state file (`storage_state.json`)
   - ✅ All 89 analysis records with scraped data

4. **Automation**
   - ✅ Cron job configured (runs daily at 1:00 AM)

---

## Files & Scripts

### Main Scraper Scripts
- **`askslim_login.py`** - Authenticate to askSlim.com
- **`askslim_smoketest.py`** - Verify session validity
- **`askslim_run_daily.py`** - Daily orchestrator (futures + equities)
- **`askslim_scraper.py`** - Futures scraper
- **`askslim_equities_scraper.py`** - Equities scraper

### Database Updates
Scraper updates these tables:
- `cycle_specs` - Cycle anchor dates and lengths
- `instrument_analysis` - Directional bias, support/resistance, video URLs

---

## Daily Automation

### Cron Job Configuration
```cron
0 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_run_daily.py >> logs/askslim_daily.log 2>&1
```

**Schedule:** Daily at 1:00 AM server time

**What it does:**
1. Verifies session is valid
2. Scrapes all 18 futures instruments
3. Scrapes all 55 equities instruments
4. Updates database with latest cycle specs
5. Rebuilds cycle projections
6. Logs output to `logs/askslim_daily.log`

**Duration:** ~20-30 minutes total

---

## Manual Operations

### Verify Session
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_smoketest.py
```

**Expected:** "✅ Smoketest passed - askSlim is accessible"

### Run Full Scraper Manually
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_run_daily.py
```

### Run Futures Only
```bash
python3 src/riley/modules/askslim/askslim_scraper.py
```

### Run Equities Only
```bash
python3 src/riley/modules/askslim/askslim_equities_scraper.py
```

---

## Monitoring

### Check Scraper Logs
```bash
# View recent runs
tail -100 ~/riley-cycles/logs/askslim_daily.log

# Follow live
tail -f ~/riley-cycles/logs/askslim_daily.log

# Check for errors
grep -i error ~/riley-cycles/logs/askslim_daily.log
```

### Verify Database Updates
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('db/riley.sqlite')
cursor = conn.cursor()

# Check last update
cursor.execute("SELECT MAX(updated_at) FROM instrument_analysis")
print(f"Last askSlim update: {cursor.fetchone()[0]}")

# Count active instruments
cursor.execute("SELECT COUNT(*) FROM instrument_analysis WHERE status = 'ACTIVE'")
print(f"Active instruments: {cursor.fetchone()[0]}")
conn.close()
EOF
```

---

## Troubleshooting

### Session Expired
If scraper fails with authentication errors:
```bash
# Re-login (manual browser required for CAPTCHA)
cd ~/riley-cycles
source venv/bin/activate
python3 src/riley/modules/askslim/askslim_login.py
```

### Chromium Crashes
If headless browser crashes:
```bash
# Check system libraries installed
dpkg -l | grep libnss3
dpkg -l | grep libatk

# Reinstall if needed
sudo bash ~/riley-cycles/install_chromium_deps.sh
```

### Rate Limiting
askSlim may rate-limit if too many requests:
- Scraper includes 4-8 second delays between requests
- If rate-limited, wait 30 minutes before retrying

---

# 2. Market Data Module

## Purpose
Collects daily OHLCV price data from Yahoo Finance for RRG sector universe.

## Data Collected
- **12 Symbols:** SPY, XLK, XLY, XLC, XLV, XLF, XLE, XLI, XLP, XLU, XLB, XLRE
- **Timeframe:** Daily bars
- **Source:** Yahoo Finance (via yfinance library)
- **Storage:** `price_bars_daily` table in database
- **Export:** CSV file for RRG visualization

---

## Server Deployment Status

### ✅ Fully Deployed Components

1. **Database**
   - ✅ Migration applied (`006_price_bars_daily.sql`)
   - ✅ Table created with indexes
   - ✅ 2-year backfill completed (6,000+ bars)

2. **Modules**
   - ✅ `yfinance_collector.py` - Data fetcher
   - ✅ `store.py` - Database storage
   - ✅ `export_rrg.py` - CSV export
   - ✅ `cli.py` - Command-line interface

3. **Scripts**
   - ✅ `scripts/riley_marketdata.py` - Main CLI
   - ✅ Cron job script for daily updates

4. **Automation**
   - ✅ Cron job configured (runs daily at 1:30 AM)

---

## Files & Scripts

### Main Scripts
- **`scripts/riley_marketdata.py`** - CLI wrapper for all operations
- **`src/riley/modules/marketdata/cli.py`** - Core CLI logic
- **`src/riley/modules/marketdata/yfinance_collector.py`** - Yahoo Finance fetcher
- **`src/riley/modules/marketdata/store.py`** - Database storage with upsert
- **`src/riley/modules/marketdata/export_rrg.py`** - CSV export in Mode A format

### Database Schema
```sql
CREATE TABLE price_bars_daily (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    adj_close REAL,
    volume INTEGER,
    source TEXT DEFAULT 'yfinance',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date)
);
```

---

## Daily Automation

### Cron Job Configuration
```cron
30 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 scripts/riley_marketdata.py update --export artifacts/rrg/rrg_prices_daily.csv >> logs/marketdata_cron.log 2>&1
```

**Schedule:** Daily at 1:30 AM server time (after askSlim scraper)

**What it does:**
1. Fetches latest 10 days of data (overlap window)
2. Upserts to database (idempotent - safe to run multiple times)
3. Exports CSV to `artifacts/rrg/rrg_prices_daily.csv`
4. Verifies all symbols have data
5. Logs output to `logs/marketdata_cron.log`

**Duration:** ~2-5 minutes

---

## Manual Operations

### Update Market Data
```bash
cd ~/riley-cycles
source venv/bin/activate
python3 scripts/riley_marketdata.py update --export artifacts/rrg/rrg_prices_daily.csv
```

### Verify Data
```bash
python3 scripts/riley_marketdata.py verify
```

**Expected output:**
```
✅ SPY       501 bars  Latest: 2025-12-28
✅ XLK       501 bars  Latest: 2025-12-28
...
✅ All RRG symbols have data
```

### Show Statistics
```bash
python3 scripts/riley_marketdata.py stats
```

**Expected output:**
```
Total Symbols: 12
Total Bars: 6,012
Date Range: 2023-12-27 to 2025-12-28
```

### Backfill Specific Symbols
```bash
python3 scripts/riley_marketdata.py backfill --symbols SPY XLK --lookback-days 90
```

### Force Re-export CSV
```bash
python3 scripts/riley_marketdata.py export \
    --output artifacts/rrg/rrg_prices_daily.csv \
    --lookback-days 365
```

---

## Monitoring

### Check Logs
```bash
# View recent runs
tail -100 ~/riley-cycles/logs/marketdata_cron.log

# Follow live
tail -f ~/riley-cycles/logs/marketdata_cron.log

# Check for errors
grep -i error ~/riley-cycles/logs/marketdata_cron.log

# View today's run
grep "$(date +%Y-%m-%d)" ~/riley-cycles/logs/marketdata_cron.log
```

### Verify Daily Updates
```bash
# Check latest date for each symbol
python3 scripts/riley_marketdata.py verify

# Show full statistics
python3 scripts/riley_marketdata.py stats
```

---

## Integration with RRG App

The exported CSV at `artifacts/rrg/rrg_prices_daily.csv` is in Mode A format and can be directly used by the RRG Sector Rotation Map app.

**CSV Format:**
```csv
date,symbol,open,high,low,close,volume
2023-12-27,SPY,463.97,465.16,463.43,465.01,68000300
...
```

**RRG App:**
- Embedded in Home.py (RRG view)
- Standalone at `sector-rotation-map/app.py`
- Reads price data directly from database (no CSV needed for embedded view)

---

## Troubleshooting

### Missing Data for Symbol
```bash
# Check if symbol has data
python3 scripts/riley_marketdata.py verify

# Re-backfill specific symbol
python3 scripts/riley_marketdata.py backfill --symbols XLK --lookback-days 730
```

### Yahoo Finance Rate Limiting
If fetching fails with rate limit errors:
- Scraper includes 0.5s delay between symbols
- Wait 15-30 minutes before retrying
- If persistent, reduce lookback days

### Database Locked Error
SQLite database may be locked if multiple processes access simultaneously.

**Solution:**
- Ensure cron jobs don't overlap
- askSlim: 1:00 AM
- Market Data: 1:30 AM (30-minute gap prevents conflicts)

### Cron Job Not Running
```bash
# Check crontab
crontab -l | grep marketdata

# Check cron service status
sudo systemctl status cron

# Check permissions
ls -la ~/riley-cycles/scripts/riley_marketdata.py

# Run manually to test
cd ~/riley-cycles && source venv/bin/activate && python3 scripts/riley_marketdata.py update
```

---

## Component Integration

### Data Flow in Riley Cycles Watch

```
askSlim Scraper (1:00 AM)
  ↓
Updates: cycle_specs, instrument_analysis
  ↓
Market Data (1:30 AM)
  ↓
Updates: price_bars_daily
  ↓
Exports: artifacts/rrg/rrg_prices_daily.csv
  ↓
System Status Page (User Interface)
  ↓
Displays: Latest scraper run times and data freshness
```

### Component Status Monitoring

Both components report status in:
1. **System Status Page** (app/pages/2_System_Status.py)
   - Last askSlim run timestamp
   - Last market data update date
   - Manual operation buttons

2. **Home Page Sidebar**
   - Component status indicators
   - Quick health check

---

## Quick Reference

### askSlim Scraper Commands
```bash
# Verify session
python3 src/riley/modules/askslim/askslim_smoketest.py

# Run full daily scrape
python3 src/riley/modules/askslim/askslim_run_daily.py

# Check logs
tail -f ~/riley-cycles/logs/askslim_daily.log
```

### Market Data Commands
```bash
# Update data
python3 scripts/riley_marketdata.py update --export artifacts/rrg/rrg_prices_daily.csv

# Verify data
python3 scripts/riley_marketdata.py verify

# Show stats
python3 scripts/riley_marketdata.py stats

# Check logs
tail -f ~/riley-cycles/logs/marketdata_cron.log
```

### Combined Health Check
```bash
# Check both component logs
tail -20 ~/riley-cycles/logs/askslim_daily.log
tail -20 ~/riley-cycles/logs/marketdata_cron.log

# Verify database updates
sqlite3 ~/riley-cycles/db/riley.sqlite << 'SQL'
SELECT 'askSlim', MAX(updated_at) FROM instrument_analysis
UNION ALL
SELECT 'Market Data', MAX(date) FROM price_bars_daily;
SQL
```

---

**End of Component Deployment Guide**
