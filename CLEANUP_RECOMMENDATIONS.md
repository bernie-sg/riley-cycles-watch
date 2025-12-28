# Cleanup Recommendations - December 28, 2025

Based on investigation of all folders and files.

---

## ✅ CONFIRMED: Can Delete Immediately

### 1. Old/Outdated Files (Not Used Anymore)

**IBKR-related (you said not needed):**
- ❌ `IBKR_CONFIG_LOCK_PROOF.md` (completion proof from old session)

**Empty/Dead Files:**
- ❌ `riley.db` (0 bytes, dead file - real DB is in `db/riley.sqlite`)
- ❌ `config/` folder (completely empty)

**Old README (completely outdated):**
- ❌ `README.md` (18 Dec - describes old "pipeline" approach, not current Cycles Watch system)

**Orphaned Calendar page:**
- ❌ `pages/Calendar.py` (old version, not in app/pages/ anymore - Calendar feature may have been removed)

### 2. Old Data Folders (No Longer Used)

**`data/` folder structure:**
```
data/
├── raw/
│   ├── ibkr/ES/D.csv (old IBKR data)
│   └── tradingview/ES/D.csv (old TradingView data)
└── processed/
    └── ES/D.parquet, W.parquet (old processed data)
```
**Status:** These are from old pipeline approach (19 Dec). Current system uses:
- `db/riley.sqlite` for all data storage
- `price_bars_daily` table for market data
- No longer using parquet files or raw CSV processing

**Recommendation:** ❌ Delete entire `data/` folder

**`history bars/` folder:**
- Contains 13 CSV files from TradingView (19 Dec)
- Old downloaded futures contracts data
- No longer used (price data now in SQLite database)

**Recommendation:** ❌ Delete entire `history bars/` folder

### 3. Completion/Fix Logs (Consolidate Then Delete)

These are session completion summaries from past work:
- ❌ `CALENDAR_FIXES_COMPLETE.txt`
- ❌ `CALENDAR_SIDEBAR_INTEGRATION.txt`
- ❌ `CALENDAR_VIEW_IMPLEMENTATION.txt`
- ❌ `CALENDAR_VIEW_TEST_REPORT.txt`
- ❌ `MULTIPAGE_DISCOVERY_FIX.txt`
- ❌ `STREAMLIT_ENTRYPOINT_FIX.txt`
- ❌ `CYCLE_FIREWALL_SUMMARY.txt`
- ❌ `DB_REPAIR_VERIFICATION.txt`

**Action:** Consolidate into `docs/archive/CHANGELOG_ARCHIVE.md` then delete

---

## ⚠️ REVIEW FIRST (Might Be Useful)

### 1. pytest.ini
**Content:** Simple pytest configuration
```ini
[pytest]
testpaths = tests
python_files = test_*.py
```

**Status:** Still valid if you run pytest
**Question:** Do you run tests? If yes, keep it. If no, delete.

### 2. Calendar Documentation
- `CALENDAR_VIEW_README.md`
- `QUICK_START_CALENDAR.md`

**Question:** Is Calendar view feature still in the app? I don't see it in `app/pages/`
- If removed: Delete these docs
- If still exists elsewhere: Keep and consolidate

### 3. logs/ folder
```
logs/
├── (askSlim logs go here)
└── (market data logs go here)
```

**Status:** Created for askSlim and market data logging
**Recommendation:** ✅ KEEP - This is functional and needed

---

## 🔄 CONSOLIDATE (Multiple Related Files)

### Deployment Documentation (3 files → 1)
- `DEPLOYMENT.md` (production deployment to Hostinger)
- `MARKETDATA_DEPLOYMENT.md` (market data module)
- `MARKETDATA_SERVER_DEPLOYMENT_STEPS.md` (server steps)
- `ASKSLIM_DEPLOYMENT_COMPLETE.md` (askSlim deployment)

**Action:** Create `docs/deployment/` folder and consolidate:
- `docs/deployment/PRODUCTION.md` (from DEPLOYMENT.md)
- `docs/deployment/COMPONENTS.md` (consolidate market data + askSlim)

### askSlim Module Documentation
Current files in `src/riley/modules/askslim/`:
- ✅ `README.md` - Keep
- ✅ `DATA_STRUCTURE.md` - Keep
- ✅ `INSTRUMENT_MAPPING.md` - Keep
- ❌ `PHASE1_COMPLETE.md` - Delete (askSlim is complete now)
- ❌ `PHASE2_REQUIREMENTS.md` - Delete (askSlim is complete now)

---

## 📝 MAJOR UPDATE NEEDED: claude.md

**Current Status:** Outdated (from 20 Dec), only covers basic Cycles Watch

**Needs to Include:**

### 1. Project Overview
- What is Riley Cycles Watch
- Current phase: Complete integration (v2.0.0)
- Main components: askSlim scraper, Market data, Cycle scanner, RRG

### 2. Architecture
- Database: `db/riley.sqlite` (single source of truth)
- Tables: instruments, cycle_specs, instrument_analysis, price_bars_daily, trading_calendar_daily/weekly, daily_scan_runs/rows
- Streamlit UI: `app/Home.py` + `app/pages/2_System_Status.py`

### 3. Data Flow
- askSlim scraper → cycle_specs + instrument_analysis tables
- Market data (yfinance) → price_bars_daily table
- Cycle scanner → daily_scan_runs/rows tables
- RRG app → reads price_bars_daily

### 4. Components
- **askSlim Scraper:** Automated extraction (headless mode), stores cycle dates, lengths, bias, support/resistance
- **Market Data:** Yahoo Finance daily bars for RRG sectors
- **Cycle Scanner:** Analyzes windows, generates priority lists
- **RRG Map:** Sector rotation visualization
- **System Status:** Admin page for manual operations

### 5. User Scripts (What Bernard Uses)
- System Status page buttons (not manual Python scripts)
- Location: http://localhost:8501 → System Status page

### 6. Database Schema
- Key tables and their purposes
- Versioning approach (status='ACTIVE'/'SUPERSEDED')

### 7. Deployment
- Local: Streamlit on localhost:8501
- Server: Hostinger VPS 82.25.105.47, domain cycles.cosmicsignals.net
- Cron jobs for automation

### 8. What NOT to Do
- Never delete database without explicit request
- Never run Python scripts manually (use System Status page)
- Never modify core cycle logic without firewall rules
- Out of scope: IBKR connectivity, Volume profile, Gamma

---

## 📊 SUMMARY

### Delete Immediately (18 files/folders):
1. `IBKR_CONFIG_LOCK_PROOF.md`
2. `riley.db`
3. `config/` (empty folder)
4. `README.md` (outdated)
5. `pages/Calendar.py` (orphaned)
6. `data/` (entire folder - 4 files)
7. `history bars/` (entire folder - 13 CSV files)
8. 8 × .txt completion logs (after consolidating)
9. `PHASE1_COMPLETE.md`, `PHASE2_REQUIREMENTS.md` in askslim/

### Keep:
- `logs/` folder (functional)
- `pytest.ini` (if you run tests)
- `docs/` numbered files (core knowledge)
- Component READMEs (RRG, askSlim)
- Generated reports in `reports/`

### Consolidate:
- 4 deployment docs → 2 organized docs in `docs/deployment/`
- 8 completion logs → `docs/archive/CHANGELOG_ARCHIVE.md`
- 2 calendar docs → Either delete or consolidate (if feature still exists)

### Update:
- **claude.md** → Comprehensive project guide (see outline above)
- **CyclesUpdate.md** → Either consolidate into claude.md or keep as separate user-facing doc

---

## 🎯 PROPOSED FOLDER STRUCTURE (After Cleanup)

```
/
├── claude.md (UPDATED - comprehensive guide)
├── CyclesUpdate.md (or consolidated into claude.md)
├── requirements.txt
├── pytest.ini (if keeping tests)
│
├── docs/
│   ├── 00-12_*.md (keep all)
│   ├── CYCLE_FIREWALL.md
│   ├── archive/
│   │   └── CHANGELOG_ARCHIVE.md (new - all completion logs)
│   ├── deployment/
│   │   ├── PRODUCTION.md (Hostinger VPS)
│   │   └── COMPONENTS.md (askSlim + Market Data)
│   └── features/ (if Calendar still exists)
│       └── CALENDAR_VIEW.md
│
├── app/
├── db/
├── artifacts/
├── media/
├── migrations/
├── logs/ (keep)
├── reports/
├── scripts/
├── sector-rotation-map/
├── src/
└── tests/
```

---

## ✅ NEXT ACTIONS

**Awaiting your confirmation:**

1. ✅ Delete all items in "Delete Immediately" section?
2. ❓ Keep or delete `pytest.ini`?
3. ❓ Is Calendar view still in the app? If not, delete calendar docs.
4. ✅ Proceed with consolidation plan?
5. ✅ Update `claude.md` with comprehensive guide?

**No deletions will occur until you approve!**
