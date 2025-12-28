# Documentation Audit - December 28, 2025

**Purpose:** Review all Markdown files and stray files to identify what's current, outdated, or should be consolidated.

---

## 📁 ROOT-LEVEL DOCUMENTATION

### ✅ KEEP AS-IS (Current & Functional)

1. **claude.md** - Current instructions for Claude Code, actively used ✅
2. **README.md** - Main project documentation, needs minor update but keep ✅
3. **DEPLOYMENT.md** - Production deployment guide for Hostinger VPS ✅
4. **MARKETDATA_SERVER_DEPLOYMENT_STEPS.md** - Recent (v2.0.0), still relevant ✅

### 🔄 NEEDS REVIEW/UPDATE (Partially Outdated)

5. **ASKSLIM_DEPLOYMENT_COMPLETE.md** (Dec 26)
   - Status: Marked "AWAITING FINAL STEP"
   - **Question:** Is askSlim deployment complete now after v2.0.0? If yes, consolidate into main DEPLOYMENT.md
   - **Recommendation:** Update or merge into DEPLOYMENT.md

6. **MARKETDATA_DEPLOYMENT.md**
   - Similar content to MARKETDATA_SERVER_DEPLOYMENT_STEPS.md
   - **Recommendation:** Consolidate these two into one

7. **CyclesUpdate.md**
   - Describes how cycle updates work
   - Some overlap with claude.md
   - **Recommendation:** Either consolidate into claude.md or keep separate if it's user-facing documentation

### 📦 CONSOLIDATE (Multiple .txt files with similar purpose)

8. **CALENDAR_FIXES_COMPLETE.txt**
9. **CALENDAR_SIDEBAR_INTEGRATION.txt**
10. **CALENDAR_VIEW_IMPLEMENTATION.txt**
11. **CALENDAR_VIEW_TEST_REPORT.txt**
12. **MULTIPAGE_DISCOVERY_FIX.txt**
13. **STREAMLIT_ENTRYPOINT_FIX.txt**
14. **CYCLE_FIREWALL_SUMMARY.txt**
15. **DB_REPAIR_VERIFICATION.txt**

**Status:** These are completion/fix logs from past sessions
**Recommendation:** Create `docs/archive/CHANGELOG_ARCHIVE.md` and consolidate all these into one historical log, then delete individual .txt files

### ❓ SPECIAL CASES

16. **CALENDAR_VIEW_README.md**
    - Describes calendar view feature
    - **Question:** Is this still accurate? Calendar view working?
    - **Recommendation:** If current, move to `docs/features/CALENDAR_VIEW.md`

17. **QUICK_START_CALENDAR.md**
    - Quick start guide for calendar
    - **Recommendation:** Consolidate with CALENDAR_VIEW_README.md or move to docs/

18. **IBKR_CONFIG_LOCK_PROOF.md**
    - Completion proof from past session
    - **Recommendation:** Move to docs/archive/ if keeping, or delete if no longer needed

---

## 📁 docs/ FOLDER (Appears Well-Organized)

### ✅ KEEP ALL (Systematic Documentation)

- `00_MANIFESTO.md` - Philosophy/vision ✅
- `01_PRD.md` - Product requirements ✅
- `02_INTERPRETATION_GUIDELINES.md` - Trading interpretation ✅
- `03_LIQUIDITY_PRICE_GUIDELINES.md` - Price analysis rules ✅
- `04_DAILY_TRADER_REPORT.md` - Report format ✅
- `05_DECISION_INTEGRITY_PROTOCOL.md` - Decision making ✅
- `06_STATE_AND_REGIME_MODEL.md` - Market state model ✅
- `07_NARRATIVE_CONTINUITY_RULES.md` - Narrative guidelines ✅
- `08_EVIDENCE_WEIGHTING_GUIDELINES.md` - Evidence assessment ✅
- `09_SCANNER_VS_ANALYST_ROLES.md` - Role definitions ✅
- `10_AUDIT_AND_ACCOUNTABILITY_MODEL.md` - Accountability ✅
- `11_NON_GOALS.md` - What we don't do ✅
- `12_LANGUAGE_AND_TONE_CONTRACT.md` - Communication style ✅
- `CYCLE_FIREWALL.md` - Cycle isolation rules ✅

**Status:** These are well-numbered, systematic documentation
**Recommendation:** KEEP ALL, this is the core knowledge base

---

## 📁 reports/ FOLDER

### ✅ KEEP (Generated Data/Reports)

- `reports/countdown/` - Daily countdown reports
- `reports/skeletons/` - Analysis skeletons
- `reports/watchlist/` - Instrument snapshots

**Status:** These are generated reports, not documentation
**Recommendation:** KEEP - this is data/output, not documentation to clean up

---

## 📁 sector-rotation-map/

### ✅ KEEP (Component Documentation)

- `QUICKSTART.md` - How to run RRG app ✅
- `README.md` - RRG component overview ✅

**Status:** Component-specific docs
**Recommendation:** KEEP - these are current and relevant

---

## 📁 src/riley/modules/askslim/

### ✅ KEEP (Component Documentation)

- `README.md` - askSlim module overview ✅
- `DATA_STRUCTURE.md` - Data structure docs ✅
- `INSTRUMENT_MAPPING.md` - Symbol mapping ✅

### 🔄 REVIEW (May Be Outdated)

- `PHASE1_COMPLETE.md` - Phase 1 completion marker
- `PHASE2_REQUIREMENTS.md` - Phase 2 requirements

**Question:** Are we still in phases, or is askSlim integration complete?
**Recommendation:** If complete, consolidate these into README.md history section

---

## 📁 OTHER FILES

### ⚠️ STRAY FILES (Not in proper locations)

- `./app/app.py` - **Question:** Is this used? Main app is Home.py
- `./pages/Calendar.py` - **Question:** Should this be in `app/pages/`?
- `./migrations/004_add_askslim_extended_fields.sql` - Migrations should be in organized folder

**Recommendation:** Check if these are used and move to proper locations

---

## 🎯 PROPOSED CLEANUP ACTIONS

### Phase 1: Consolidation (No Deletions Yet)

1. **Create `docs/archive/` folder**
2. **Create `docs/archive/CHANGELOG_ARCHIVE.md`** - Consolidate all .txt completion logs:
   - CALENDAR_FIXES_COMPLETE.txt
   - CALENDAR_SIDEBAR_INTEGRATION.txt
   - CALENDAR_VIEW_IMPLEMENTATION.txt
   - CALENDAR_VIEW_TEST_REPORT.txt
   - MULTIPAGE_DISCOVERY_FIX.txt
   - STREAMLIT_ENTRYPOINT_FIX.txt
   - CYCLE_FIREWALL_SUMMARY.txt
   - DB_REPAIR_VERIFICATION.txt

3. **Create `docs/deployment/` folder** - Move deployment docs:
   - DEPLOYMENT.md → `docs/deployment/PRODUCTION.md`
   - MARKETDATA_DEPLOYMENT.md + MARKETDATA_SERVER_DEPLOYMENT_STEPS.md → `docs/deployment/MARKETDATA.md` (consolidated)
   - ASKSLIM_DEPLOYMENT_COMPLETE.md → `docs/deployment/ASKSLIM.md` (update status)

4. **Create `docs/features/` folder** - Move feature docs:
   - CALENDAR_VIEW_README.md → `docs/features/CALENDAR_VIEW.md`
   - QUICK_START_CALENDAR.md → merge into `docs/features/CALENDAR_VIEW.md`

5. **Update ROOT README.md** - Add links to organized docs

### Phase 2: Verification (Before Any Deletions)

**Questions for you:**

1. Is the askSlim deployment fully complete now (after v2.0.0)?
2. Is `./app/app.py` still used, or is `Home.py` the only entrypoint?
3. Is `./pages/Calendar.py` the same as `app/pages/1_Calendar.py` or different?
4. Are the PHASE1/PHASE2 docs in askslim/ still relevant, or is the module complete?
5. Can we archive IBKR_CONFIG_LOCK_PROOF.md or delete it?

### Phase 3: Deletions (After Your Approval)

After consolidation and your verification, delete:
- Individual .txt completion logs (after consolidating)
- Duplicate deployment docs (after consolidating)
- Any confirmed-unused files

---

## 📊 SUMMARY

**Total Markdown Files:** 147 files
- **Root Level:** 17 files (10 need review/consolidation)
- **docs/:** 14 files (all good, keep)
- **reports/:** 116 files (generated data, keep)
- **Component docs:** 7 files (mostly good, 2 need review)

**Stray Files Identified:** 8 files need location verification

**Proposed New Structure:**
```
/
├── README.md (updated with links)
├── claude.md (current instructions)
├── CyclesUpdate.md (keep or consolidate?)
├── docs/
│   ├── 00-12_*.md (core docs - keep all)
│   ├── CYCLE_FIREWALL.md
│   ├── archive/
│   │   ├── CHANGELOG_ARCHIVE.md (new - consolidates all .txt logs)
│   │   └── IBKR_CONFIG_LOCK_PROOF.md (if keeping)
│   ├── deployment/
│   │   ├── PRODUCTION.md
│   │   ├── MARKETDATA.md (consolidated)
│   │   └── ASKSLIM.md (updated)
│   └── features/
│       └── CALENDAR_VIEW.md (consolidated)
├── sector-rotation-map/
│   ├── README.md
│   └── QUICKSTART.md
└── src/riley/modules/askslim/
    ├── README.md
    ├── DATA_STRUCTURE.md
    └── INSTRUMENT_MAPPING.md
```

---

## ⏭️ NEXT STEPS

**Awaiting your approval on:**

1. Consolidation plan (Phase 1)
2. Answers to verification questions (Phase 2)
3. Which files to delete after consolidation (Phase 3)

**No files will be deleted without your explicit approval.**
