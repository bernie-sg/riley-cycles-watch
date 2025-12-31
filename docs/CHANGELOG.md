# Riley Project - Changelog

All notable changes to the Riley Project are documented here.

---

## [v2.1.0] - 2025-12-29

### 🎯 Major Features

#### Cycles Detector V14 Integration
- **Embedded** Cycles Detector in Riley as native component
- **One-click access** via sidebar navigation
- **Auto-start controls** for Flask server management
- **Full-screen embedded view** via iframe
- **All original features preserved**: MESA, Morlet, Bandpass, Heatmaps, Quality Metrics
- **Documentation**: `CYCLES_DETECTOR_EMBEDDED.md`, `CYCLES_DETECTOR_QUICK_START.md`

#### Shared CSV Price Data System
- **Created** unified CSV price manager in `src/riley/modules/marketdata/csv_price_manager.py`
- **Shared data** between RRG and Cycles Detector
- **Auto-download** on first use (full history)
- **Auto-update** appends new bars only (no re-download)
- **Manageable files** ~50-200 KB per symbol
- **Database separation** Price bars in CSV, cycle data in SQLite
- **31+ symbols** pre-loaded including all RRG sectors
- **Documentation**: `SHARED_CSV_PRICE_DATA.md`

### 🔧 Major Changes

#### Removed Database Versioning for askSlim
- **Simplified** askSlim data management
- **Changed** from version increment to DELETE + INSERT
- **Always version=1** for askSlim specs
- **Database cleanup** removed 178 SUPERSEDED specs, 76 inactive projections
- **Faster operations** no version tracking overhead
- **Documentation**: `NO_VERSIONING_SYSTEM.md`

#### Fixed Calendar Duplicate Projections
- **Added** deactivation logic in `cycles_rebuild.py`
- **Prevents** duplicate active projections at k=0
- **Cleaned** database of existing duplicates (40 removed)
- **Verified** no duplicates remain

### 📝 Files Modified

#### New Files
- `app/pages/3_Cycles_Detector.py` - Embedded Cycles Detector page
- `src/riley/modules/marketdata/csv_price_manager.py` - Shared price data manager
- `docs/CYCLES_DETECTOR_EMBEDDED.md` - Integration documentation
- `docs/CYCLES_DETECTOR_QUICK_START.md` - User guide
- `docs/SHARED_CSV_PRICE_DATA.md` - Data system documentation
- `docs/NO_VERSIONING_SYSTEM.md` - Versioning removal explanation
- `docs/PRODUCTION_CYCLES_DETECTOR_STATUS.md` - Troubleshooting guide
- `docs/CURRENT_STATUS_29DEC2025.md` - System status report

#### Modified Files
- `src/riley/cycles_rebuild.py` - Added projection deactivation logic
- `src/riley/modules/askslim/askslim_scraper.py` - Removed versioning, simple DELETE+INSERT
- `cycles-detector/data_manager.py` - Now uses shared CSV price manager
- `cycles-detector/app.py` - Changed port from 5001 to 8082
- `app/Home.py` - Loads RRG from CSV files instead of database

### 🚀 Production Deployment

#### Deployed to cycles.cosmicsignals.net
- **Server**: 82.25.105.47 (raysudo@hostinger)
- **Riley Port**: 8081
- **Flask Port**: 8082
- **Deployment Package**: 7.4 MB tar.gz
- **Dependencies Installed**: Flask, scipy, requests
- **Status**: ⚠️ Awaiting browser cache clear for verification

### 📊 Data Status

#### CSV Files
- **Location**: `data/price_history/`
- **Count**: 31+ symbols
- **Size**: ~15-20 MB total
- **RRG Symbols**: All 12 sectors (SPY, XLK, XLY, XLC, XLV, XLF, XLE, XLI, XLP, XLU, XLB, XLRE)
- **Latest Update**: SPY (8285 bars, updated 2025-12-27)

#### Database
- **Size**: ~500 KB (cycle data only)
- **Tables**: 6 (instruments, calendars, cycle_specs, cycle_projections, desk_notes, alembic)
- **Status**: Clean, no duplicates
- **Note**: price_bars_daily table no longer used

### ✅ Testing

#### Local Environment (All Passed)
- ✅ Data manager loads 8285 bars for SPY
- ✅ Auto-update adds new bars (1 added today)
- ✅ Flask server running on port 8082
- ✅ Streamlit page compiles without errors
- ✅ Path resolution correct
- ✅ iframe embedding works
- ✅ Full Cycles Detector functionality

#### Production Environment (Pending)
- ⚠️ Browser cache clear needed
- ✅ Files deployed
- ✅ Dependencies installed
- ✅ Services started

### 🐛 Fixes

#### Fixed Path Import Error
- **Issue**: UnboundLocalError in `app/Home.py`
- **Cause**: Duplicate import statements
- **Fix**: Removed duplicate imports, Path already imported at top

#### Fixed iframe Height
- **Issue**: Cycles Detector not filling panel
- **Fix**: Removed padding, set iframe height to `calc(100vh - 100px)`

#### Fixed Production Dependencies
- **Issue**: ModuleNotFoundError for flask and scipy
- **Fix**: Installed in venv, activated for Flask startup

### 📚 Documentation

All documentation updated and comprehensive:
- System architecture explained
- Integration methods documented
- Troubleshooting guides created
- Quick start guide for users
- Production deployment procedure
- Current status fully documented

---

## [v2.0.0] - 2025-12-20 to 2025-12-27

### Initial Riley Cycles Management System

#### Core Features
- **Database Schema**: SQLite with Alembic migrations
- **Instruments Management**: Canonical symbols with aliases
- **Trading Calendars**: Daily and weekly indices
- **Cycle Specs**: Anchor dates, wavelengths, windows
- **Cycle Projections**: Forward/backward k-bar projections
- **Desk Notes**: Structured trading notes
- **askSlim Scraper**: Automated cycle spec updates (with versioning)
- **RRG Visualization**: Relative Rotation Graphs

#### Scripts
- `cycles_add_instrument.py` - Add instruments and aliases
- `cycles_import_calendar.py` - Import trading calendars
- `cycles_set_spec.py` - Set cycle specifications
- `cycles_run_scan.py` - Daily cycle scanning
- `cycles_add_note.py` - Add desk notes

#### Database Tables
- `instruments` - Canonical symbols and aliases
- `trading_calendars_daily` - Trading day indices
- `trading_calendars_weekly` - Trading week indices
- `cycle_specs` - Cycle specifications (with versioning)
- `cycle_projections` - Generated projections
- `desk_notes` - Trading notes
- `price_bars_daily` - Price history (later moved to CSV)

---

## Version Comparison

### v2.1.0 vs v2.0.0

**What's New:**
- ✅ Cycles Detector V14 integrated
- ✅ Shared CSV price data system
- ✅ No-versioning for askSlim data
- ✅ Fixed duplicate projections
- ✅ Production deployment

**What Changed:**
- 📊 Price data moved from database to CSV files
- 🗑️ Database versioning removed for askSlim
- 🔧 askSlim scraper simplified (DELETE+INSERT)
- 📈 RRG loads from CSV instead of database
- 🎨 Cycles Detector embedded in Riley

**What's Better:**
- 🚀 One-click access to Cycles Detector
- 💾 Manageable file sizes (CSV vs database)
- ⚡ Faster updates (append only)
- 🔄 Shared data eliminates duplication
- 🧹 Cleaner database (cycle data only)
- 📖 Comprehensive documentation

---

## Upgrade Notes

### From v2.0.0 to v2.1.0

#### Data Migration
1. Price data automatically migrated to CSV files on first use
2. Old `price_bars_daily` table can be emptied (no longer used)
3. All RRG symbols auto-downloaded to `data/price_history/`

#### Configuration Changes
1. Cycles Detector now runs on port 8082 (was 5001)
2. Access via Riley sidebar, not separate URL
3. Auto-start controls in Streamlit page

#### Script Changes
1. askSlim scraper now deletes old records (no versioning)
2. All askSlim specs reset to version=1
3. Cycle rebuild deactivates old projections before creating new ones

#### File Structure Changes
```
NEW: data/price_history/           ← CSV files for price data
NEW: app/pages/3_Cycles_Detector.py
NEW: src/riley/modules/marketdata/csv_price_manager.py
MODIFIED: cycles-detector/data_manager.py
MODIFIED: app/Home.py
MODIFIED: src/riley/cycles_rebuild.py
MODIFIED: src/riley/modules/askslim/askslim_scraper.py
```

---

## Known Issues

### Production (v2.1.0)
- ⚠️ Cycles Detector page may show empty (browser cache issue)
- **Fix**: Clear cache and hard refresh

### Local (v2.1.0)
- ✅ No known issues

---

## Future Roadmap

### Not Planned (Out of Scope for Phase 1)
- IBKR connectivity
- Advanced charting
- Volume profile analysis
- Gamma analysis
- Trade plan generation
- Backtesting engine

### Potential Future Enhancements
- Multi-symbol cycle correlation
- Automated cycle detection from Cycles Detector
- Historical cycle performance tracking
- Mobile-responsive Cycles Detector
- Export cycle analysis reports

---

## Contributors

- Claude Code (AI Assistant)
- Bernard (Project Owner)

---

**Last Updated**: 2025-12-29 19:40 SGT
