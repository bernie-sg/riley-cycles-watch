# Market Data Module Deployment Guide

## Overview

The Market Data module collects daily OHLCV price data from Yahoo Finance for the RRG sector universe (SPY + 11 sector ETFs) and stores it in the Riley SQLite database.

## Components

### Database
- **Table**: `price_bars_daily`
- **Location**: `db/riley.sqlite`
- **Columns**: symbol, date, open, high, low, close, adj_close, volume, source, created_at, updated_at
- **Primary Key**: (symbol, date)

### Modules
- **yfinance_collector.py**: Data collection from Yahoo Finance
- **store.py**: Database storage with upsert logic
- **export_rrg.py**: CSV export in Mode A format for RRG app
- **cli.py**: Command-line interface

### Scripts
- **scripts/riley_marketdata.py**: Main CLI wrapper
- **scripts/cron_marketdata_daily.sh**: Daily cron job
- **scripts/server_initial_backfill.sh**: One-time initial backfill

### Artifacts
- **artifacts/rrg/rrg_prices_daily.csv**: Exported data for RRG visualization

## RRG Sector Universe

The module tracks 12 symbols:
- **SPY**: S&P 500 (Benchmark)
- **XLK**: Technology
- **XLY**: Consumer Discretionary
- **XLC**: Communication Services
- **XLV**: Health Care
- **XLF**: Financials
- **XLE**: Energy
- **XLI**: Industrials
- **XLP**: Consumer Staples
- **XLU**: Utilities
- **XLB**: Materials
- **XLRE**: Real Estate

## Local Testing (Already Completed)

✅ Migration applied to database
✅ 2-year backfill completed (6,012 bars)
✅ Daily update tested (idempotent upsert)
✅ CSV export verified (Mode A format)
✅ All 12 symbols have data from 2023-12-27 to 2025-12-24

## Server Deployment Instructions

### 1. Prerequisites

Ensure server has:
- Python 3.9+
- pip
- Virtual environment (if used)
- SQLite database at `/home/riley/db/riley.sqlite`

### 2. Install Dependencies

SSH into server:
```bash
ssh riley@82.25.105.47
```

Install yfinance:
```bash
cd /home/riley
source venv/bin/activate  # If using venv
pip install yfinance>=0.2.0
```

### 3. Verify File Upload

Ensure these files are on server:
```bash
# Check migrations
ls -la db/migrations/006_price_bars_daily.sql

# Check modules
ls -la src/riley/modules/marketdata/

# Check scripts
ls -la scripts/riley_marketdata.py
ls -la scripts/cron_marketdata_daily.sh
ls -la scripts/server_initial_backfill.sh

# Check permissions
chmod +x scripts/riley_marketdata.py
chmod +x scripts/cron_marketdata_daily.sh
chmod +x scripts/server_initial_backfill.sh
```

### 4. Apply Database Migration

Run migration manually:
```bash
cd /home/riley
sqlite3 db/riley.sqlite < db/migrations/006_price_bars_daily.sql
```

Verify table creation:
```bash
sqlite3 db/riley.sqlite ".schema price_bars_daily"
```

Expected output:
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

### 5. Run Initial Backfill

Execute one-time backfill to populate 2 years of data:
```bash
cd /home/riley
./scripts/server_initial_backfill.sh | tee logs/initial_backfill_$(date +%Y%m%d).log
```

This will:
- Collect 730 days of historical data
- Store ~6,000+ bars in database
- Export CSV to artifacts/rrg/rrg_prices_daily.csv
- Run verification
- Display statistics

Expected output:
```
✅ Backfill complete: 6012 total bars stored
✅ All RRG symbols have data
Total Symbols: 12
Total Bars: 6,012
Date Range: 2023-12-27 to 2025-12-24
```

### 6. Verify Data

Check data integrity:
```bash
python3 scripts/riley_marketdata.py verify
python3 scripts/riley_marketdata.py stats
```

### 7. Configure Cron Job

Add daily cron job to run at 1:30 AM (after market close):
```bash
crontab -e
```

Add this line:
```cron
30 1 * * * /home/riley/scripts/cron_marketdata_daily.sh >> /home/riley/logs/marketdata_cron.log 2>&1
```

This schedule:
- Runs AFTER askSlim scraper (1:00 AM)
- Updates with 10-day overlap window (idempotent)
- Exports fresh CSV for RRG app
- Logs output to `logs/marketdata_cron.log`

### 8. Test Cron Job Manually

Run cron script manually to test:
```bash
./scripts/cron_marketdata_daily.sh
```

Check log output:
```bash
tail -50 logs/marketdata_cron.log
```

## Monitoring & Maintenance

### Check Logs
```bash
# View recent cron runs
tail -100 logs/marketdata_cron.log

# Check for errors
grep -i error logs/marketdata_cron.log

# View today's run
grep "$(date +%Y-%m-%d)" logs/marketdata_cron.log
```

### Verify Daily Updates
```bash
# Check latest date for each symbol
python3 scripts/riley_marketdata.py verify

# Show full statistics
python3 scripts/riley_marketdata.py stats
```

### Manual Operations

**Force Re-export CSV:**
```bash
python3 scripts/riley_marketdata.py export \
    --output artifacts/rrg/rrg_prices_daily.csv \
    --lookback-days 365
```

**Backfill Specific Symbols:**
```bash
python3 scripts/riley_marketdata.py backfill \
    --symbols SPY XLK XLF \
    --lookback-days 90
```

**Daily Update Only:**
```bash
python3 scripts/riley_marketdata.py update --overlap-days 10
```

## Troubleshooting

### Missing Data for Symbol
```bash
# Check if symbol has data
python3 scripts/riley_marketdata.py verify

# Re-backfill specific symbol
python3 scripts/riley_marketdata.py backfill --symbols XLK --lookback-days 730
```

### Cron Job Not Running
```bash
# Check crontab
crontab -l

# Check cron service status
sudo systemctl status cron

# Check permissions
ls -la scripts/cron_marketdata_daily.sh
```

### Database Locked Error
SQLite database may be locked if multiple processes access simultaneously.

Solution:
- Ensure cron jobs don't overlap in timing
- askSlim: 1:00 AM
- Market Data: 1:30 AM

### Yahoo Finance Rate Limiting
If fetching fails with rate limit errors:
- Increase retry delay in `yfinance_collector.py`
- Add rate limiting between symbols (already implemented with 0.5s delay)

## Integration with RRG App

The exported CSV at `artifacts/rrg/rrg_prices_daily.csv` is in Mode A format and can be directly uploaded to the RRG Sector Rotation Map app.

**CSV Format:**
```csv
date,symbol,open,high,low,close,volume
2023-12-27,SPY,463.97,465.16,463.43,465.01,68000300
...
```

**RRG App Location:**
- Local: `/Users/bernie/Documents/AI/Riley Project/sector-rotation-map/`
- Run locally: `streamlit run app.py`

## Database Schema Reference

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

CREATE INDEX idx_price_bars_date ON price_bars_daily(date);
CREATE INDEX idx_price_bars_symbol ON price_bars_daily(symbol);
CREATE INDEX idx_price_bars_symbol_date ON price_bars_daily(symbol, date);
```

## File Structure

```
riley-project/
├── db/
│   ├── riley.sqlite
│   └── migrations/
│       └── 006_price_bars_daily.sql
├── src/
│   └── riley/
│       └── modules/
│           └── marketdata/
│               ├── __init__.py
│               ├── yfinance_collector.py
│               ├── store.py
│               ├── export_rrg.py
│               └── cli.py
├── scripts/
│   ├── riley_marketdata.py
│   ├── cron_marketdata_daily.sh
│   └── server_initial_backfill.sh
├── artifacts/
│   └── rrg/
│       └── rrg_prices_daily.csv
├── logs/
│   └── marketdata_cron.log
└── requirements.txt (includes yfinance>=0.2.0)
```

## Success Criteria

✅ Database table created
✅ All 12 RRG symbols have data
✅ Date range covers at least 2 years
✅ CSV export generated in Mode A format
✅ Cron job configured and tested
✅ Daily updates running automatically
✅ Logs show successful runs
✅ RRG app can load exported CSV

## Support

For issues or questions:
1. Check logs: `logs/marketdata_cron.log`
2. Run verify: `python3 scripts/riley_marketdata.py verify`
3. Check database: `sqlite3 db/riley.sqlite "SELECT COUNT(*) FROM price_bars_daily;"`
4. Review this deployment guide

---

**Deployment Date**: 2025-12-26
**Last Updated**: 2025-12-26
**Module Version**: 1.0.0
