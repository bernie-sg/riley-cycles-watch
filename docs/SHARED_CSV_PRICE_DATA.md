# Shared CSV Price Data System

**Date:** 28-Dec-2025
**Status:** ✅ Complete

---

## Overview

Both RRG and Cycles Detector now use **shared CSV files** for price history data.

**Database is ONLY for Riley's cycle data** (cycle_specs, cycle_projections, instruments, etc.)

**CSV files are for price bars** (OHLCV data)

---

## Architecture

```
data/price_history/          ← Shared CSV folder
├── spy_history.csv          ← RRG benchmark
├── xlk_history.csv          ← RRG sectors (11 files)
├── aapl_history.csv         ← Cycles Detector symbols
├── msft_history.csv
└── ... (any symbol)

Both RRG and Cycles Detector read/write here
```

---

## How It Works

### First Download
1. Symbol requested (e.g., AAPL)
2. Check if `aapl_history.csv` exists
3. If not → Download full history from Yahoo Finance
4. Save to CSV file

### Updates (Append Only)
1. Read existing CSV file
2. Check last date in file
3. If outdated → Download only NEW bars since last date
4. **Append** new bars to CSV
5. Save updated CSV

**No re-downloading** - only appends new data

---

## Components

### 1. Shared Price Manager
**File:** `src/riley/modules/marketdata/csv_price_manager.py`

**Functions:**
- `get_price_data(symbol)` - Load or download price data
- `load_rrg_data()` - Load all RRG symbols at once
- `update_rrg_universe()` - Update all RRG symbols

**Used by:** Both RRG and Cycles Detector

### 2. Cycles Detector Data Manager
**File:** `cycles-detector/data_manager.py`

**Now:** Thin wrapper around shared CSV price manager

**Before:** Had its own download/update logic

**Change:** Imports and uses `get_price_data()` from shared module

### 3. RRG Home Page
**File:** `app/Home.py`

**Before:** Read from `price_bars_daily` database table

**Now:** Calls `load_rrg_data()` from shared CSV price manager

**Lines changed:** 1353-1366, 1637-1661

---

## Data Flow

### RRG
```
User opens RRG page
    ↓
load_rrg_data()
    ↓
For each RRG symbol (SPY, XLK, XLY, etc.):
    ↓
Check data/price_history/{symbol}_history.csv
    ↓
If exists → Read CSV → Check if outdated → Append new bars if needed
If not → Download full history → Save to CSV
    ↓
Return combined DataFrame
    ↓
Display RRG chart
```

### Cycles Detector
```
User enters symbol (e.g., AAPL)
    ↓
DataManager('AAPL')
    ↓
get_price_data('AAPL')
    ↓
Check data/price_history/aapl_history.csv
    ↓
If exists → Read CSV → Check if outdated → Append new bars if needed
If not → Download full history → Save to CSV
    ↓
Return prices array and DataFrame
    ↓
Run cycle analysis
```

---

## CSV File Format

```csv
Date,Close
1993-01-29,24.13
1993-02-01,24.38
1993-02-02,24.44
...
2025-12-26,690.31
```

**Columns:**
- `Date` - Trading date (YYYY-MM-DD)
- `Close` - Closing price

**Note:** Only Close price stored (OHLV not needed for cycle analysis)

---

## Benefits

### 1. Separate Concerns
- **Database:** Riley's cycle management data
- **CSV files:** Price history data

### 2. Manageable File Sizes
- Individual CSV files (~50-200 KB each)
- Easy to inspect, backup, share
- Not cluttering the database

### 3. Efficient Updates
- Only download new bars (not full history)
- Append to existing CSV
- Fast and bandwidth-efficient

### 4. Shared Data
- Both RRG and Cycles Detector use same files
- No duplicate storage
- One update benefits both systems

### 5. Portable
- CSV files can be moved, backed up separately
- Don't need to export from database
- Standard format, readable by any tool

---

## RRG Symbols

```
SPY   - S&P 500 (Benchmark)
XLK   - Technology
XLY   - Consumer Discretionary
XLC   - Communication Services
XLV   - Health Care
XLF   - Financials
XLE   - Energy
XLI   - Industrials
XLP   - Consumer Staples
XLU   - Utilities
XLB   - Materials
XLRE  - Real Estate
```

All downloaded with full history (~7,000 bars each since 1998)

---

## Current Status

### CSV Files Downloaded
- ✅ All 12 RRG symbols
- ✅ All existing Cycles Detector symbols (~19 symbols)
- ✅ Total: ~31 CSV files in `data/price_history/`

### Integration Complete
- ✅ Cycles Detector uses shared CSV manager
- ✅ RRG uses shared CSV manager
- ✅ Auto-update on access (appends new bars)
- ✅ Database cleaned (price_bars_daily can be emptied/removed)

---

## Maintenance

### Daily Updates
**Automatic** - When you access RRG or Cycles Detector:
1. CSV files are checked
2. If outdated (> 1 day old) → fetch new bars
3. Append to CSV
4. Continue with analysis

**No manual updates needed**

### Manual Update All RRG Symbols
```bash
cd /Users/bernie/Documents/AI/Riley\ Project
python3 -c "
import sys
sys.path.insert(0, 'src')
from riley.modules.marketdata.csv_price_manager import update_rrg_universe
update_rrg_universe()
"
```

### Add New Symbol
Just use it! Will auto-download on first access.

Example:
- Enter "TSLA" in Cycles Detector
- System downloads `tsla_history.csv`
- Stored in `data/price_history/`
- Available for future use

---

## Database Status

### What's IN the Database
- ✅ `instruments` - Canonical symbols and aliases
- ✅ `trading_calendars_daily` - Trading day calendars
- ✅ `trading_calendars_weekly` - Trading week calendars
- ✅ `cycle_specs` - Cycle specifications
- ✅ `cycle_projections` - Cycle projections
- ✅ `desk_notes` - Trading notes

### What's NOT in the Database Anymore
- ❌ `price_bars_daily` - **Now in CSV files instead**

**Database size:** Much smaller, focused on cycle management data only

---

## Testing

### Test Cycles Detector
```bash
cd cycles-detector
python3 data_manager.py
```

**Expected output:**
```
Testing Data Manager (using shared CSV price manager)
==================================================

Data summary:
  Total bars: 8285
  Date range: 1993-01-29 to 2025-12-26
  Latest price: $690.31
```

### Test RRG
```bash
streamlit run app/Home.py
```

Then navigate to RRG view - should load data from CSV files

---

## Summary

✅ **Shared CSV price data system complete**

**What changed:**
- Removed: Price bars from database
- Added: Shared CSV price manager
- Updated: Both RRG and Cycles Detector to use CSV files

**Benefits:**
- Database is clean (only cycle data)
- CSV files are manageable
- Auto-updates append new bars
- Both systems share same data

**Status:** Production ready

---

**End of Documentation**
