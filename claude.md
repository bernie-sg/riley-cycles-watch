# CLAUDE.md — Riley Cycles Watch (v2.0.0)

**Last Updated:** 28-Dec-2025
**System Version:** 2.0.0
**Purpose:** Complete project guide for Claude Code sessions

---

## READ THIS FIRST: Active System Inventory

**Before any file operations, read:** `ACTIVE_SYSTEM_INVENTORY.md`

This file lists **every actively used file and folder**. Do NOT delete anything listed there without explicit user approval.

---

## What is Riley Cycles Watch?

Riley Cycles Watch is a **trading cycles analysis platform** that tracks and analyzes market cycles for futures, equities, and ETFs. It provides real-time cycle window tracking, automated data collection, and sector rotation visualization.

### Current Phase: v2.0.0 (Complete Integration)
- ✅ askSlim scraper (automated data collection)
- ✅ Market data module (Yahoo Finance integration)
- ✅ Cycle scanner (window analysis)
- ✅ RRG sector rotation map
- ✅ System Status admin panel
- ✅ Streamlit web UI

---

## Your Role

You are Claude Code operating inside this repository at:
```
/Users/bernie/Documents/AI/Riley Project
```

### How Bernard Uses the System

**Bernard does NOT run Python scripts manually anymore.**

Instead, Bernard uses the **System Status page** in the Streamlit UI:
- **Location:** `app/pages/2_System_Status.py`
- **Access:** Via browser at localhost:8501 or cycles.cosmicsignals.net
- **Features:** Manual control buttons for all operations

### Your Responsibilities

1. **Read ACTIVE_SYSTEM_INVENTORY.md** - Understand what's running
2. **Follow absolute rules** (see below) - Never break these
3. **Use System Status page** - Bernard's interface
4. **Update documentation** - Keep docs current
5. **Test thoroughly** - Show proof of changes
6. **Ask before deletions** - Especially database operations

---

## Architecture Overview

### Single Source of Truth: SQLite Database
```
db/riley.sqlite
```

**Critical:** This is the ONLY database file. Never delete it.

### Key Tables (Active)
- **instruments** - Canonical instruments + aliases
- **cycle_specs** - DAILY/WEEKLY cycle configurations
- **instrument_analysis** - askSlim data (bias, video_url, support/resistance)
- **price_bars_daily** - Market data from Yahoo Finance
- **trading_calendar_daily** - Trading day index (TD)
- **trading_calendar_weekly** - Trading week index (TW)
- **daily_scan_runs** - Scan execution records
- **daily_scan_rows** - Scan results per instrument
- **desk_notes** - User notes
- **astro_events** - Astrological event dates

### Streamlit UI Structure
```
app/
├── Home.py                    # Main dashboard (entry point)
├── db.py                      # Database access layer (CyclesDB class)
├── config.py                  # Configuration management
└── pages/
    └── 2_System_Status.py     # Admin control panel
```

### Source Modules
```
src/riley/
├── modules/
│   ├── askslim/              # askSlim scraper
│   └── marketdata/           # Market data collector
└── calendar_events.py         # Calendar view builder
```

### Scripts (Called by System Status Page)
```
scripts/
├── riley_marketdata.py        # Market data CLI
├── cycles_run_scan.py         # Cycle scanner
└── cycles_*.py                # Other utilities
```

---

## Components (What's Running)

### 1. askSlim Scraper
**Purpose:** Automated data collection from askSlim.com

**What it collects:**
- Cycle anchor dates and lengths (DAILY/WEEKLY)
- Directional bias (Bullish/Bearish)
- Support and resistance levels
- Video analysis URLs

**Coverage:**
- 18 Futures (ES, NQ, GC, CL, etc.)
- 55 Equities/ETFs (AAPL, MSFT, SPY, sector ETFs, etc.)
- Total: 73 instruments

**Automation:**
- Cron job runs daily at 1:00 AM (server)
- Updates `cycle_specs` and `instrument_analysis` tables
- Logs to `logs/askslim_daily.log`

**Manual operation:** System Status page → "Run Scraper Now" button

**Location:**
- Main: `src/riley/modules/askslim/askslim_run_daily.py`
- Login: `src/riley/modules/askslim/askslim_login.py`
- Test: `src/riley/modules/askslim/askslim_smoketest.py`

---

### 2. Market Data Module
**Purpose:** Fetch price data from Yahoo Finance for RRG

**What it collects:**
- 12 symbols (SPY + 11 sector ETFs)
- Daily OHLCV bars
- 2+ years of historical data

**Automation:**
- Cron job runs daily at 1:30 AM (server)
- Updates `price_bars_daily` table
- Exports to `artifacts/rrg/rrg_prices_daily.csv`
- Logs to `logs/marketdata_cron.log`

**Manual operation:** System Status page → "Update Market Data" button

**Location:**
- Main: `scripts/riley_marketdata.py`
- Module: `src/riley/modules/marketdata/`

---

### 3. Cycle Scanner
**Purpose:** Analyze cycle windows and generate priority lists

**What it does:**
- Reads `cycle_specs` and `trading_calendar_*` tables
- Computes window status (PREWINDOW, ACTIVATED, etc.)
- Updates `daily_scan_runs` and `daily_scan_rows` tables
- Generates ranked instrument lists

**Manual operation:** System Status page → "Run Cycle Scanner" button

**Location:** `scripts/cycles_run_scan.py`

---

### 4. RRG Sector Rotation Map
**Purpose:** Visualize sector rotation using Relative Rotation Graph

**What it shows:**
- 12 sector ETFs positioned in 4 quadrants
- Leading, Improving, Lagging, Weakening sectors
- Historical tails showing rotation over time

**Integration:**
- Embedded in Home.py (RRG view)
- Standalone app at `sector-rotation-map/app.py`
- Reads from `price_bars_daily` table

**Location:** `sector-rotation-map/`

---

## Data Flow (How Everything Connects)

### Daily Operations Timeline (Server)

```
1:00 AM - askSlim Scraper runs
   ↓
   Updates: cycle_specs, instrument_analysis
   Logs to: logs/askslim_daily.log

1:30 AM - Market Data Update runs
   ↓
   Updates: price_bars_daily
   Exports to: artifacts/rrg/rrg_prices_daily.csv
   Logs to: logs/marketdata_cron.log

On-demand - Cycle Scanner
   ↓
   Reads: cycle_specs, trading_calendar_*
   Updates: daily_scan_runs, daily_scan_rows

On-demand - User browsing
   ↓
   Streamlit UI reads all tables
   Displays: TODAY view, DATABASE view, CALENDAR view, RRG view
```

### User Interaction Flow

```
Bernard opens browser
   ↓
https://cycles.cosmicsignals.net (or localhost:8501)
   ↓
Loads: app/Home.py
   ↓
Imports: app/db.py (CyclesDB class)
   ↓
Connects to: db/riley.sqlite
   ↓
Renders 4 views:
   - TODAY: Priority instruments in window
   - DATABASE: Full instrument editor
   - CALENDAR: 2-month cycle window calendar
   - RRG: Sector rotation map
   ↓
Bernard clicks System Status page
   ↓
Manual buttons to run:
   - askSlim Scraper
   - Market Data Update
   - Cycle Scanner
```

---

## Absolute Rules (NEVER BREAK THESE)

### 1. Database Protection
**NEVER delete or reset `db/riley.sqlite`** unless Bernard explicitly says: "delete/reset the database"

- Do NOT run: `rm -f db/riley.sqlite`
- Do NOT truncate tables without approval
- For tests: Use `db/riley_test.sqlite` or in-memory SQLite

### 2. Trading Bars for Logic, Calendar Days for Labels
- **DAILY cycles:** Use TD (trading day) indices for calculations
- **WEEKLY cycles:** Use TW (trading week) indices for calculations
- **Calendar days:** Labels only, NEVER for calculations

### 3. Deterministic Snapping
If anchor date is not a trading day:
- **Always snap to NEXT trading day**
- NEVER snap backwards
- No exceptions

### 4. Global Defaults (Unless Explicitly Overridden)
- **Window:** ±3 bars
- **Pre-window:** 2 bars
- **Snap rule:** NEXT_TRADING_DAY
- **Projection ranges:**
  - DAILY: k = -2..+8
  - WEEKLY: k = -2..+6

### 5. Canonical Instrument Model
- One canonical instrument per symbol (e.g., ES)
- Aliases (SPX, SPY) resolve to canonical
- Notes/levels can reference different symbols (e.g., SPX) without creating duplicates

### 6. No Half-Done State
If you start a change:
- Finish it completely
- Show proof it works
- Test end-to-end
- Update documentation

### 7. Date Formatting Consistency
**All dates in UI must use:** DD-Mon-YYYY format (e.g., 28-Dec-2025)
- NOT: YYYY-MM-DD
- NOT: MM/DD/YYYY
- Consistent across all views

### 8. System Status Page is User Interface
Bernard does NOT run Python scripts manually.
- All operations via System Status page buttons
- You run scripts during development/testing
- Production: Bernard clicks buttons

---

## What is OUT OF SCOPE (Do Not Work On)

Unless Bernard explicitly asks, these are out of scope:

- IBKR connectivity
- Charting (except RRG)
- Volume profile / pivots
- Gamma
- Trade plan generation
- Backtesting
- Predictive models
- Alerting systems

---

## Documentation Structure

### Core Knowledge Base (docs/)
**All numbered files are ACTIVE and current:**
- `00_MANIFESTO.md` - Philosophy
- `01_PRD.md` - Product requirements
- `02-12_*.md` - Trading interpretation, rules, protocols
- `CYCLE_FIREWALL.md` - Cycle calculation rules

**Never delete these. They are the foundation.**

### Deployment (docs/deployment/)
- `PRODUCTION.md` - Server deployment guide
- `COMPONENTS.md` - askSlim + Market Data deployment

### Archive (docs/archive/)
- `CHANGELOG_ARCHIVE.md` - Historical completion logs

### Component Documentation
- `sector-rotation-map/README.md` - RRG overview
- `src/riley/modules/askslim/README.md` - askSlim module
- `src/riley/modules/askslim/DATA_STRUCTURE.md` - Data schema
- `src/riley/modules/askslim/INSTRUMENT_MAPPING.md` - Symbol mappings

---

## Active Data Folders (DO NOT DELETE)

### Essential Folders
- **`db/`** - Database storage (riley.sqlite)
- **`logs/`** - Application logs (askslim_daily.log, marketdata_cron.log)
- **`media/`** - User-uploaded charts (per symbol folders)
- **`artifacts/`** - Exports (RRG CSV)
- **`reports/`** - Generated reports (countdown, watchlist, skeletons)
- **`migrations/`** - Database schema versioning

### Code Folders
- **`app/`** - Streamlit UI
- **`src/riley/`** - Source modules
- **`scripts/`** - CLI scripts
- **`sector-rotation-map/`** - RRG component

---

## How to Interact with Bernard

### When Making Changes

1. **Read ACTIVE_SYSTEM_INVENTORY.md first**
2. **Test your changes** before committing
3. **Show proof:** Screenshots, command output, test results
4. **Update documentation** if behavior changes
5. **Ask before deletions** - Especially database operations

### When Bernard Requests Features

1. **Clarify requirements** - Ask questions if unclear
2. **Check out of scope** - Remind if item is out of scope
3. **Plan before coding** - Show architecture if complex
4. **Test thoroughly** - Prove it works
5. **Update docs** - Keep ACTIVE_SYSTEM_INVENTORY.md current

### Communication Style

- **Be concise** - Bernard is experienced
- **Show, don't tell** - Provide proof of changes
- **Highlight issues** - If something is risky, say so
- **Respect rules** - Never break absolute rules
- **Ask when uncertain** - Better to ask than to break things

---

## Server Deployment (Production)

### Server Details
- **IP:** 82.25.105.47
- **User:** raysudo
- **SSH Key:** ~/.ssh/berryfit_key
- **Domain:** https://cycles.cosmicsignals.net
- **Port:** 8081 (Streamlit)

### Cron Jobs
```bash
# askSlim Scraper (1:00 AM daily)
0 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_run_daily.py >> logs/askslim_daily.log 2>&1

# Market Data (1:30 AM daily)
30 1 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 scripts/riley_marketdata.py update --export artifacts/rrg/rrg_prices_daily.csv >> logs/marketdata_cron.log 2>&1
```

### Deployment Guide
See: `docs/deployment/PRODUCTION.md`

---

## Common Operations (How You Help Bernard)

### 1. Add New Instrument
Bernard will usually do this via DATABASE view in UI, but if asked:
```bash
python3 scripts/cycles_add_instrument.py --canonical GC --alias GOLD
```

### 2. Set Cycle Spec
Bernard will usually do this via DATABASE view in UI, but if asked:
```bash
python3 scripts/riley_set_cycle.py --symbol ES --timeframe WEEKLY --anchor 2026-01-04 --length 37
```

### 3. Run Daily Scan
Bernard clicks "Run Cycle Scanner" button in System Status page.

You might run this during testing:
```bash
python3 scripts/cycles_run_scan.py --asof 2025-12-28
```

### 4. Update Market Data
Bernard clicks "Update Market Data" button in System Status page.

You might run this during testing:
```bash
python3 scripts/riley_marketdata.py update --export artifacts/rrg/rrg_prices_daily.csv
```

### 5. Run askSlim Scraper
Bernard clicks "Run Scraper Now" button in System Status page.

You might run this during testing:
```bash
python3 src/riley/modules/askslim/askslim_run_daily.py
```

---

## Git Workflow

### Current Repository
- **GitHub:** bernie-sg/riley-cycles-watch
- **Branch:** main
- **Version:** v2.0.0 (tagged)

### When Making Changes
1. Commit frequently with clear messages
2. Tag major versions (v2.0.0, v2.1.0, etc.)
3. Push to GitHub for backup
4. Include comprehensive commit messages

### Commit Message Format
```
Brief description (50 chars or less)

Detailed explanation:
- What changed
- Why it changed
- How to test

Affected files:
- app/Home.py
- scripts/riley_marketdata.py
```

---

## Testing Protocol

### Before Committing Changes

1. **Read tests work:**
   ```bash
   python3 -c "from app.db import CyclesDB; db = CyclesDB(); print(db.get_latest_scan_date())"
   ```

2. **Scripts run:**
   ```bash
   python3 scripts/cycles_run_scan.py --asof 2025-12-28
   ```

3. **Streamlit loads:**
   ```bash
   streamlit run app/Home.py
   # Check http://localhost:8501
   ```

4. **Show proof:**
   - Screenshots of working UI
   - Command output
   - Database query results

---

## Troubleshooting Quick Reference

### Database Issues
```bash
# Check database exists
ls -lh db/riley.sqlite

# Test connection
python3 -c "from app.db import CyclesDB; db = CyclesDB(); print('Connected')"

# Count records
python3 -c "from app.db import CyclesDB; db = CyclesDB(); print(f'Instruments: {db._get_connection().execute(\"SELECT COUNT(*) FROM instruments\").fetchone()[0]}')"
```

### Streamlit Issues
```bash
# Check process running
ps aux | grep streamlit

# Kill and restart
pkill -f streamlit
streamlit run app/Home.py
```

### Component Status
```bash
# Check askSlim logs
tail -20 logs/askslim_daily.log

# Check market data logs
tail -20 logs/marketdata_cron.log

# Check database updates
python3 -c "from app.db import CyclesDB; db = CyclesDB(); print(db.get_latest_scan_date())"
```

---

## Session Restart Checklist

When this session restarts, the new Claude instance should:

1. ✅ Read `ACTIVE_SYSTEM_INVENTORY.md` - Understand active system
2. ✅ Read this file (`CLAUDE.md`) - Understand project
3. ✅ Read `docs/00-12_*.md` - Understand methodology
4. ✅ Read `docs/CYCLE_FIREWALL.md` - Understand cycle rules
5. ❌ NEVER delete `db/riley.sqlite`
6. ❌ NEVER delete files in ACTIVE_SYSTEM_INVENTORY.md
7. ❌ NEVER break absolute rules
8. ✅ Always ask before risky operations

---

## Quick Reference: Key Files

### Most Important Files (Never Delete)
1. `db/riley.sqlite` - The database
2. `app/Home.py` - Main UI entry point
3. `app/db.py` - Database access layer
4. `app/pages/2_System_Status.py` - Admin panel
5. `CLAUDE.md` - This file
6. `ACTIVE_SYSTEM_INVENTORY.md` - System inventory

### Most Important Docs
1. `docs/CYCLE_FIREWALL.md` - Cycle calculation rules
2. `docs/00-12_*.md` - Core knowledge
3. `docs/deployment/PRODUCTION.md` - Server deployment
4. `docs/deployment/COMPONENTS.md` - Component deployment

### Most Important Scripts
1. `scripts/cycles_run_scan.py` - Daily scanner
2. `scripts/riley_marketdata.py` - Market data CLI
3. `src/riley/modules/askslim/askslim_run_daily.py` - askSlim scraper

---

## Summary: Riley Cycles Watch v2.0.0

**What it is:** Trading cycles analysis platform with automated data collection

**Main components:**
- Streamlit UI (Home.py + System Status page)
- askSlim scraper (automated cycle data)
- Market data module (Yahoo Finance prices)
- Cycle scanner (window analysis)
- RRG map (sector rotation)

**How Bernard uses it:**
- Opens browser → cycles.cosmicsignals.net
- Clicks buttons in System Status page
- Views cycle windows in TODAY view
- Edits instruments in DATABASE view
- Checks sector rotation in RRG view

**How you help:**
- Read ACTIVE_SYSTEM_INVENTORY.md first
- Follow absolute rules always
- Test changes thoroughly
- Show proof of changes
- Ask before risky operations
- Keep documentation updated

**Most important rule:**
**NEVER delete `db/riley.sqlite`** unless explicitly requested

---

**End of CLAUDE.md**
