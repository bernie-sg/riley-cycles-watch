# Active System Inventory - Riley Cycles Watch
**Created:** 28-Dec-2025
**Purpose:** Document all actively used files, scripts, modules, and data flows

**CRITICAL:** This document lists everything currently in use. Do NOT delete any file listed here without explicit approval.

---

## 1. STREAMLIT WEB APPLICATION (Main User Interface)

### Entry Point
- **`app/Home.py`** - Main Streamlit dashboard
  - **Used by:** User access via browser (localhost:8501 or cycles.cosmicsignals.net)
  - **Calls:** app/db.py, app/config.py
  - **Views:** TODAY, DATABASE, CALENDAR, RRG
  - **Status:** ACTIVE - Primary user interface

### Pages
- **`app/pages/2_System_Status.py`** - Admin control panel
  - **Used by:** User manual operations
  - **Calls scripts:**
    - `src/riley/modules/askslim/askslim_login.py`
    - `src/riley/modules/askslim/askslim_smoketest.py`
    - `src/riley/modules/askslim/askslim_run_daily.py`
    - `scripts/riley_marketdata.py`
    - `scripts/cycles_run_scan.py`
  - **Status:** ACTIVE - Main admin interface

### Supporting Modules
- **`app/db.py`** - Database access layer (CyclesDB class)
  - **Used by:** Home.py, all views
  - **Accesses:** db/riley.sqlite
  - **Status:** ACTIVE - Core database module

- **`app/config.py`** - Configuration management
  - **Used by:** Home.py, db.py
  - **Returns:** Database paths, configuration
  - **Status:** ACTIVE - Core config module

---

## 2. ACTIVE PYTHON SCRIPTS (Called by System Status Page)

### askSlim Scraper Scripts (src/riley/modules/askslim/)
- **`askslim_login.py`** - Authenticates to askSlim.com
  - **Called by:** System Status page "Login to askSlim" button
  - **Creates:** .askslim-session files
  - **Status:** ACTIVE

- **`askslim_smoketest.py`** - Verifies session validity
  - **Called by:** System Status page "Verify Session" button
  - **Checks:** .askslim-session files
  - **Status:** ACTIVE

- **`askslim_run_daily.py`** - Main scraper (headless mode)
  - **Called by:** System Status page "Run Scraper Now" button
  - **Updates:** cycle_specs, instrument_analysis tables
  - **Logs to:** logs/askslim_daily.log
  - **Status:** ACTIVE - Main data collection script

- **`askslim_scraper.py`** - Core scraper module
  - **Called by:** askslim_run_daily.py
  - **Status:** ACTIVE - Supporting module

### Market Data Scripts (scripts/)
- **`scripts/riley_marketdata.py`** - Market data updater
  - **Called by:** System Status page "Update Market Data" button
  - **Updates:** price_bars_daily table
  - **Exports to:** artifacts/rrg/rrg_prices_daily.csv
  - **Logs to:** logs/marketdata_cron.log
  - **Source:** Yahoo Finance (yfinance)
  - **Status:** ACTIVE - Main market data script

### Cycle Scanner Scripts (scripts/)
- **`scripts/cycles_run_scan.py`** - Daily cycle scanner
  - **Called by:** System Status page "Run Cycle Scanner" button
  - **Updates:** daily_scan_runs, daily_scan_rows tables
  - **Status:** ACTIVE - Main scanner script

### Other Active Scripts (scripts/)
- **`scripts/cycles_add_instrument.py`** - Add/manage instruments
  - **Status:** ACTIVE - Admin utility

- **`scripts/riley_set_cycle.py`** - Set cycle specs
  - **Status:** ACTIVE - Admin utility

- **`scripts/cycles_watchlist_snapshot.py`** - Generate watchlist reports
  - **Status:** ACTIVE - Reporting utility

- **`scripts/cycles_window_countdown.py`** - Generate countdown reports
  - **Status:** ACTIVE - Reporting utility

---

## 3. SOURCE MODULES (src/riley/)

### askSlim Module (src/riley/modules/askslim/)
**Purpose:** Scrape cycle data from askSlim.com

**Core Files (ACTIVE):**
- `askslim_login.py` - Login handler
- `askslim_smoketest.py` - Session validator
- `askslim_run_daily.py` - Daily scraper orchestrator
- `askslim_scraper.py` - Core scraper logic
- `__init__.py` - Module initialization

**Documentation (ACTIVE):**
- `README.md` - Module overview
- `DATA_STRUCTURE.md` - Data schema
- `INSTRUMENT_MAPPING.md` - Symbol mappings

**Exploration/Testing Scripts (DEVELOPMENT - Keep for debugging):**
- `askslim_explore_instruments.py`
- `askslim_explore_spx.py`
- `askslim_manual_navigator.py`
- Various test_*.py and explore_*.py files

**Status:** ACTIVE MODULE - Core functionality

### Market Data Module (src/riley/modules/marketdata/)
**Purpose:** Fetch and store price data from Yahoo Finance

**Core Files (ACTIVE):**
- `store.py` - Database storage
- `export_rrg.py` - Export for RRG component
- `yahoo.py` - Yahoo Finance fetcher
- `__init__.py` - Module initialization

**Status:** ACTIVE MODULE - Core functionality

### Calendar Events Module (src/riley/)
- **`src/riley/calendar_events.py`** - Calendar view data builder
  - **Called by:** Home.py Calendar view
  - **Builds:** FullCalendar events from cycle windows + astro events
  - **Status:** ACTIVE - Calendar feature support

---

## 4. RRG COMPONENT (sector-rotation-map/)

### Standalone RRG App
- **`sector-rotation-map/app.py`** - Standalone RRG Streamlit app
  - **Status:** ACTIVE - Can run independently
  - **Note:** Also embedded in Home.py RRG view

### RRG Modules (sector-rotation-map/rrg/)
- `compute.py` - RRG calculations
- `chart.py` - Plotly chart generation
- `constants.py` - Sector definitions, parameters
- `__init__.py` - Module initialization

**Documentation (ACTIVE):**
- `QUICKSTART.md` - How to run
- `README.md` - Component overview

**Status:** ACTIVE COMPONENT - Integrated into main app

---

## 5. DATABASE (Single Source of Truth)

### Main Database
- **`db/riley.sqlite`** - SQLite database
  - **Size:** Variable (growing)
  - **Tables in use:**
    - `instruments` - Canonical instruments + aliases
    - `cycle_specs` - DAILY/WEEKLY cycle configurations
    - `instrument_analysis` - askSlim scraper data (bias, video_url)
    - `price_bars_daily` - Market data from Yahoo Finance
    - `trading_calendar_daily` - Trading day index
    - `trading_calendar_weekly` - Trading week index
    - `daily_scan_runs` - Scan execution records
    - `daily_scan_rows` - Scan results per instrument
    - `desk_notes` - User notes
    - `astro_events` - Astrological event dates
  - **Status:** ACTIVE - DO NOT DELETE

### Migrations (migrations/)
- **All .sql files in migrations/** - Database schema versions
  - **Status:** ACTIVE - Required for schema management

---

## 6. DATA & MEDIA FOLDERS (Active Storage)

### Media Storage
- **`media/`** - Chart and image storage
  - **Structure:** `media/{SYMBOL}/image.png`
  - **Used by:** Home.py DATABASE view (chart upload/display)
  - **Status:** ACTIVE - User uploaded content

### Artifacts & Exports
- **`artifacts/rrg/`** - RRG data exports
  - **File:** `rrg_prices_daily.csv` - Exported by riley_marketdata.py
  - **Used by:** RRG component (optional)
  - **Status:** ACTIVE - Export destination

### Logs
- **`logs/`** - Application logging
  - **Files:**
    - `askslim_daily.log` - askSlim scraper logs
    - `marketdata_cron.log` - Market data update logs
  - **Used by:** All scraper scripts
  - **Status:** ACTIVE - DO NOT DELETE

### Reports
- **`reports/`** - Generated reports
  - **Subfolders:**
    - `countdown/` - Countdown reports
    - `skeletons/` - Analysis skeletons
    - `watchlist/` - Instrument snapshots
  - **Generated by:** scripts/cycles_window_countdown.py, cycles_watchlist_snapshot.py
  - **Status:** ACTIVE - Report outputs

---

## 7. CONFIGURATION FILES

### Python Dependencies
- **`requirements.txt`** - Python package dependencies
  - **Used by:** pip install, deployment
  - **Status:** ACTIVE - REQUIRED

### Session Files (Hidden)
- **`.askslim-session`** - Browser session cookies
  - **Created by:** askslim_login.py
  - **Used by:** askslim_run_daily.py, askslim_smoketest.py
  - **Status:** ACTIVE - Authentication

- **`.askslim-session-equities`** - Equities session cookies
  - **Status:** ACTIVE - Authentication for equities scraper

---

## 8. DOCUMENTATION (Actively Referenced)

### Core Project Documentation
- **`CLAUDE.md`** - Project instructions for Claude Code
  - **Status:** ACTIVE - New session onboarding
  - **Priority:** KEEP - Critical reference

### Structured Documentation (docs/)
- **ALL numbered files (00-12):**
  - `00_MANIFESTO.md`
  - `01_PRD.md`
  - `02_INTERPRETATION_GUIDELINES.md`
  - `03_LIQUIDITY_PRICE_GUIDELINES.md`
  - `04_DAILY_TRADER_REPORT.md`
  - `05_DECISION_INTEGRITY_PROTOCOL.md`
  - `06_STATE_AND_REGIME_MODEL.md`
  - `07_NARRATIVE_CONTINUITY_RULES.md`
  - `08_EVIDENCE_WEIGHTING_GUIDELINES.md`
  - `09_SCANNER_VS_ANALYST_ROLES.md`
  - `10_AUDIT_AND_ACCOUNTABILITY_MODEL.md`
  - `11_NON_GOALS.md`
  - `12_LANGUAGE_AND_TONE_CONTRACT.md`
  - **Status:** ACTIVE - Core knowledge base

- **`docs/CYCLE_FIREWALL.md`** - Cycle calculation rules
  - **Status:** ACTIVE - Critical rules

### Component Documentation
- **`sector-rotation-map/README.md`** - RRG overview
  - **Status:** ACTIVE

- **`sector-rotation-map/QUICKSTART.md`** - RRG quick start
  - **Status:** ACTIVE

- **`src/riley/modules/askslim/README.md`** - askSlim module overview
  - **Status:** ACTIVE

- **`src/riley/modules/askslim/DATA_STRUCTURE.md`** - askSlim data schema
  - **Status:** ACTIVE

- **`src/riley/modules/askslim/INSTRUMENT_MAPPING.md`** - Symbol mappings
  - **Status:** ACTIVE

---

## 9. DATA FLOW SUMMARY

### Daily Operations Flow

**askSlim Scraper (Daily):**
```
User clicks "Run Scraper Now" (System Status page)
  → Calls: src/riley/modules/askslim/askslim_run_daily.py
  → Reads: .askslim-session (authentication)
  → Scrapes: askSlim.com (cycle dates, bias, support/resistance)
  → Updates: cycle_specs, instrument_analysis tables in db/riley.sqlite
  → Logs to: logs/askslim_daily.log
```

**Market Data Update (Daily):**
```
User clicks "Update Market Data" (System Status page)
  → Calls: scripts/riley_marketdata.py update --export {path}
  → Fetches: Yahoo Finance (yfinance library)
  → Updates: price_bars_daily table in db/riley.sqlite
  → Exports to: artifacts/rrg/rrg_prices_daily.csv
  → Logs to: logs/marketdata_cron.log
```

**Cycle Scanner (Daily):**
```
User clicks "Run Cycle Scanner" (System Status page)
  → Calls: scripts/cycles_run_scan.py --asof {date}
  → Reads: cycle_specs, trading_calendar_daily/weekly tables
  → Computes: Window status (PREWINDOW, ACTIVATED, etc.)
  → Updates: daily_scan_runs, daily_scan_rows tables
  → Outputs: Console log (shown in System Status page)
```

### User Interface Flow

**Streamlit App:**
```
User browses to: localhost:8501 or cycles.cosmicsignals.net
  → Loads: app/Home.py
  → Imports: app/db.py, app/config.py
  → Connects to: db/riley.sqlite
  → Renders views:
    - TODAY: Daily scan results, instrument details
    - DATABASE: Full instrument editor
    - CALENDAR: 2-month cycle window calendar
    - RRG: Sector rotation map
  → Reads media from: media/{SYMBOL}/
```

---

## 10. WHAT IS SAFE TO DELETE (From CLEANUP_RECOMMENDATIONS.md)

### Files/Folders NOT USED by Active System

**Old Pipeline Files (18-19 Dec):**
- `data/` folder (old parquet files, no longer used)
- `history bars/` folder (old CSV files, no longer used)
- `riley.db` (0 bytes, dead file)
- `config/` folder (empty)
- `README.md` (outdated pipeline description)
- `pages/Calendar.py` (orphaned, not in app/pages/)

**Completion Logs (.txt files):**
- After consolidating into docs/archive/CHANGELOG_ARCHIVE.md:
  - CALENDAR_FIXES_COMPLETE.txt
  - CALENDAR_SIDEBAR_INTEGRATION.txt
  - CALENDAR_VIEW_IMPLEMENTATION.txt
  - CALENDAR_VIEW_TEST_REPORT.txt
  - MULTIPAGE_DISCOVERY_FIX.txt
  - STREAMLIT_ENTRYPOINT_FIX.txt
  - CYCLE_FIREWALL_SUMMARY.txt
  - DB_REPAIR_VERIFICATION.txt

**Phase Documentation:**
- `src/riley/modules/askslim/PHASE1_COMPLETE.md`
- `src/riley/modules/askslim/PHASE2_REQUIREMENTS.md`

**IBKR Proof:**
- `IBKR_CONFIG_LOCK_PROOF.md`

---

## 11. IMPORTANT: DO NOT DELETE

### Critical Files
1. **Database:** db/riley.sqlite
2. **All Python scripts in scripts/** (even if unused, may be needed for recovery)
3. **All source modules in src/riley/**
4. **All documentation in docs/**
5. **CLAUDE.md**
6. **requirements.txt**
7. **logs/ folder** (ongoing logging)
8. **media/ folder** (user content)
9. **artifacts/ folder** (exports)
10. **reports/ folder** (generated reports)
11. **migrations/ folder** (schema versioning)

### Folders in Active Use
- `app/` - Streamlit application
- `db/` - Database storage
- `scripts/` - Active scripts
- `src/riley/` - Source modules
- `sector-rotation-map/` - RRG component
- `docs/` - Documentation
- `logs/` - Logging
- `media/` - User uploads
- `artifacts/` - Exports
- `reports/` - Reports
- `migrations/` - Schema

---

## 12. AUTOMATED PROCESSES (Server Deployment)

### Cron Jobs (On Hostinger VPS)
**Location:** cycles.cosmicsignals.net (82.25.105.47)

**Daily Scraper (askSlim):**
```bash
# Runs daily at 6 AM server time
0 6 * * * /path/to/python3 /path/to/askslim_run_daily.py >> /path/to/logs/askslim_daily.log 2>&1
```

**Market Data Update:**
```bash
# Runs daily at 5 PM server time (after market close)
0 17 * * * /path/to/python3 /path/to/riley_marketdata.py update --export /path/to/artifacts/rrg/rrg_prices_daily.csv >> /path/to/logs/marketdata_cron.log 2>&1
```

**Note:** Check DEPLOYMENT.md and MARKETDATA_SERVER_DEPLOYMENT_STEPS.md for exact cron configurations

---

## 13. SUMMARY: SAFE DELETION CANDIDATES

Based on this inventory, **ONLY these items** are safe to delete (after user approval):

1. `data/` folder (entire folder - old pipeline)
2. `history bars/` folder (entire folder - old CSV files)
3. `riley.db` (0 bytes dead file)
4. `config/` folder (empty)
5. `README.md` (outdated from 18-Dec)
6. `pages/Calendar.py` (orphaned old version)
7. 8 × .txt completion logs (after consolidating)
8. `src/riley/modules/askslim/PHASE1_COMPLETE.md`
9. `src/riley/modules/askslim/PHASE2_REQUIREMENTS.md`
10. `IBKR_CONFIG_LOCK_PROOF.md`

**Everything else is actively used and must be kept.**

---

## 14. NEW SESSION CHECKLIST

When this session restarts, a new Claude instance should:

1. **Read this file first** - Understand active system
2. **Read CLAUDE.md** - Understand project rules
3. **Read docs/00-12 files** - Understand methodology
4. **Never delete:**
   - db/riley.sqlite (database)
   - Any file listed in sections 1-8 above
5. **User interactions:**
   - User accesses via System Status page (app/pages/2_System_Status.py)
   - User does NOT run Python scripts manually
   - All operations via Streamlit UI buttons

---

**END OF ACTIVE SYSTEM INVENTORY**
