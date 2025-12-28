# Market Data Module - Server Deployment Steps

## ✅ Completed Locally

1. ✅ Database migration created (006_price_bars_daily.sql)
2. ✅ Market data module implemented (src/riley/modules/marketdata/)
3. ✅ CLI scripts created (scripts/riley_marketdata.py)
4. ✅ Cron job scripts created
5. ✅ RRG Sector Rotation Map app built
6. ✅ Local testing completed (6,012 bars backfilled)
7. ✅ Code committed to GitHub (commit ea8c0a0)
8. ✅ Code pushed to origin/main

## 📋 Server Deployment Checklist

### Step 1: SSH into Server

```bash
ssh raysudo@82.25.105.47
```

### Step 2: Navigate to Riley Project Directory

```bash
cd ~/riley-cycles
```

### Step 3: Pull Latest Changes from GitHub

```bash
git pull origin main
```

**Expected output:**
```
From https://github.com/bernie-sg/riley-cycles-watch
   29e6840..ea8c0a0  main -> main
Updating 29e6840..ea8c0a0
Fast-forward
 26 files changed, 2807 insertions(+)
 create mode 100644 MARKETDATA_DEPLOYMENT.md
 ...
```

### Step 4: Activate Virtual Environment

```bash
source venv/bin/activate
```

### Step 5: Install yfinance Dependency

```bash
pip install "yfinance>=0.2.0"
```

**Expected output:**
```
Successfully installed yfinance-0.2.66
```

### Step 6: Apply Database Migration

```bash
sqlite3 db/riley.sqlite < db/migrations/006_price_bars_daily.sql
```

**Verify table created:**
```bash
sqlite3 db/riley.sqlite ".schema price_bars_daily"
```

**Expected output:**
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

### Step 7: Create Required Directories

```bash
mkdir -p logs
mkdir -p artifacts/rrg
```

### Step 8: Make Scripts Executable

```bash
chmod +x scripts/riley_marketdata.py
chmod +x scripts/cron_marketdata_daily.sh
chmod +x scripts/server_initial_backfill.sh
```

### Step 9: Run Initial Backfill (2 Years of Data)

**This will take ~2-5 minutes to download and store data from Yahoo Finance:**

```bash
./scripts/server_initial_backfill.sh | tee logs/initial_backfill_$(date +%Y%m%d).log
```

**Expected output:**
```
==========================================
Market Data Initial Backfill (2 years)
Started: 2025-12-26 XX:XX:XX
==========================================
INFO:riley.modules.marketdata.cli:Starting backfill for 12 symbols
INFO:riley.modules.marketdata.cli:Lookback: 730 days
INFO:riley.modules.marketdata.yfinance_collector:Backfilling 12 symbols from 2023-12-27 to 2025-12-26
INFO:riley.modules.marketdata.yfinance_collector:Fetching SPY from 2023-12-27 to 2025-12-26 (attempt 1/3)
INFO:riley.modules.marketdata.yfinance_collector:✅ Successfully fetched 501 bars for SPY
...
INFO:riley.modules.marketdata.cli:✅ Backfill complete: 6012 total bars stored
...
============================================================
RRG SECTOR UNIVERSE VERIFICATION
============================================================
✅ SPY       501 bars  Latest: 2025-12-24
✅ XLK       501 bars  Latest: 2025-12-24
...
✅ All RRG symbols have data
============================================================
Total Symbols: 12
Total Bars: 6,012
Date Range: 2023-12-27 to 2025-12-24
```

### Step 10: Verify CSV Export

```bash
ls -lh artifacts/rrg/rrg_prices_daily.csv
head -10 artifacts/rrg/rrg_prices_daily.csv
```

**Expected:**
- File size: ~500-600 KB
- First line: `date,symbol,open,high,low,close,volume`
- Data rows for all 12 symbols

### Step 11: Configure Cron Job for Daily Updates

**Edit crontab:**
```bash
crontab -e
```

**Add this line (runs daily at 1:30 AM after askSlim scraper):**
```cron
30 1 * * * /home/raysudo/riley-cycles/scripts/cron_marketdata_daily.sh >> /home/raysudo/riley-cycles/logs/marketdata_cron.log 2>&1
```

**Save and exit.**

**Verify crontab entry:**
```bash
crontab -l | grep marketdata
```

### Step 12: Test Cron Script Manually

```bash
./scripts/cron_marketdata_daily.sh
```

**Expected output:**
```
==========================================
Market Data Daily Update
Started: 2025-12-26 XX:XX:XX
==========================================
INFO:riley.modules.marketdata.cli:Starting daily update for 12 symbols
...
✅ Update complete: 84 total bars upserted
✅ Exported 3000 rows (12 symbols) to artifacts/rrg/rrg_prices_daily.csv
```

### Step 13: Verify Installation

```bash
python3 scripts/riley_marketdata.py verify
python3 scripts/riley_marketdata.py stats
```

**Expected:**
- All 12 symbols show ✅
- Total bars: 6,000+
- Date range: ~2023-12-27 to latest

## 🎯 Success Criteria

After completing all steps, verify:

✅ Database table `price_bars_daily` exists
✅ All 12 RRG symbols have data (501 bars each)
✅ CSV export exists at `artifacts/rrg/rrg_prices_daily.csv`
✅ Cron job configured in crontab
✅ Manual test run successful
✅ Logs directory created with initial backfill log

## 📊 Daily Operation

**Once deployed, the cron job will:**
1. Run daily at 1:30 AM (after askSlim scraper at 1:00 AM)
2. Fetch latest 10 days of data (overlap window for safety)
3. Upsert to database (idempotent - safe to run multiple times)
4. Export fresh CSV to `artifacts/rrg/rrg_prices_daily.csv`
5. Verify all symbols have data
6. Log output to `logs/marketdata_cron.log`

**Monitor daily runs:**
```bash
tail -100 logs/marketdata_cron.log
grep "$(date +%Y-%m-%d)" logs/marketdata_cron.log
```

## 🔧 Troubleshooting

### If backfill fails:
```bash
# Check Python version
python3 --version  # Should be 3.9+

# Verify yfinance installed
pip list | grep yfinance

# Test yfinance manually
python3 -c "import yfinance as yf; print(yf.__version__)"

# Re-run backfill
./scripts/server_initial_backfill.sh
```

### If cron doesn't run:
```bash
# Check cron service
sudo systemctl status cron

# View cron logs
grep CRON /var/log/syslog

# Test script manually
./scripts/cron_marketdata_daily.sh
```

### If database locked:
- Ensure askSlim cron (1:00 AM) and marketdata cron (1:30 AM) don't overlap
- Check no other processes are accessing the database

## 📚 Documentation Reference

- Full deployment guide: `MARKETDATA_DEPLOYMENT.md`
- RRG app quick start: `sector-rotation-map/QUICKSTART.md`
- RRG app full docs: `sector-rotation-map/README.md`

## 🔗 Integration with RRG App

The exported CSV can be used with the RRG Sector Rotation Map:
1. Download `artifacts/rrg/rrg_prices_daily.csv` from server
2. Upload to RRG app at http://localhost:8501
3. App will compute RRG metrics and display interactive chart

## ⏭️  Next Steps After Deployment

1. Wait 24 hours for first automated cron run
2. Check logs: `tail -100 logs/marketdata_cron.log`
3. Verify data updated: `python3 scripts/riley_marketdata.py stats`
4. Test RRG app with exported CSV
5. Monitor daily for 1 week to ensure stability

---

**Deployment Date**: 2025-12-26
**Deployed By**: Bernard
**Module Version**: 1.0.0
**Git Commit**: ea8c0a0
