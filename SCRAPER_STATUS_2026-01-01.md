# Scraper Status & Fixes - 2026-01-01

## What Was Broken

### 1. **Database Had NO Projections** ✅ FIXED
- Remote database was corrupted - 50+ cycles had ZERO projections
- This caused "No cycle specs" to show everywhere
- **Fix:** Copied working local database to remote
- **Status:** Remote now has 190 cycle projections

### 2. **Scraper Import Error** ✅ FIXED
- `ModuleNotFoundError: No module named 'src'`
- Script was missing sys.path setup
- **Fix:** Added project root to sys.path in askslim_run_daily.py
- **Deployed:** Updated script to remote

### 3. **Outdated Scraper Modules** ✅ FIXED
- Remote had old versions of scraper files
- **Deployed:**
  - askslim_run_daily.py (with sys.path fix)
  - askslim_smoketest.py (latest version)
  - askslim_scraper.py (with media tracking)

### 4. **Last Scrape Date**
- Database shows: **December 27, 2025**
- User said they scraped yesterday
- Discrepancy suggests scraper isn't saving to DB properly

---

## Current Status

### What's Working ✅
- Database structure correct (78 instruments, proper sectors)
- Database has 190 cycle projections
- Home.py and db.py synchronized
- Streamlit service running
- Sector column displaying correctly in code
- Cron job configured: `0 6 * * *` (6:00 AM daily)

### What Needs Testing ⚠️
- **Scraper execution** - Playwright may have issues
- **Session state** - May need to re-login
- **Browser installation** - Playwright browsers may not be installed
- **Cron job** - May never have run successfully

---

## How to Test Scraper Manually

### 1. SSH into Remote
```bash
ssh raysudo@82.25.105.47
cd /home/raysudo/riley-cycles
source venv/bin/activate
```

### 2. Test Scraper
```bash
python3 src/riley/modules/askslim/askslim_run_daily.py
```

### 3. Check for Errors
If you see:
- **"Session is invalid"** → Need to login: `python3 src/riley/modules/askslim/askslim_login.py`
- **Playwright errors** → Install browsers: `playwright install chromium`
- **Permission errors** → Check file permissions
- **Import errors** → Verify sys.path fix was applied

### 4. Verify Charts Saved
```bash
# Check media directory
ls -la media/ES/askslim/

# Check database
sqlite3 db/riley.sqlite "SELECT COUNT(*) FROM media_files WHERE upload_date = DATE('now')"
```

---

## Cron Job Status

**Schedule:** 6:00 AM SGT daily
```
0 6 * * * cd /home/raysudo/riley-cycles && source venv/bin/activate && python3 src/riley/modules/askslim/askslim_run_daily.py >> logs/askslim_daily.log 2>&1
```

**Issues:**
- No `logs/askslim_daily.log` file exists → Cron never ran or failed silently
- Need to check if cron service is running: `systemctl status cron`
- Need to verify cron has permissions to write to logs/

---

## Playwright Browser Installation

If scraper fails with Playwright errors, run:

```bash
cd /home/raysudo/riley-cycles
source venv/bin/activate
playwright install chromium
playwright install-deps chromium  # Install system dependencies
```

---

## Session Management

The scraper needs valid askSlim.com session. If session expired:

```bash
python3 src/riley/modules/askslim/askslim_login.py
```

This will:
1. Open browser
2. Let you login manually
3. Save session state for future scrapes

Session state saved to: `~/.askslim_session/storage_state.json`

---

## What To Do Next

1. **Test scraper manually first**
   - SSH in and run the scraper
   - Verify it completes without errors
   - Check that charts are saved to media/ and database

2. **Fix any Playwright issues**
   - Install browsers if needed
   - Check session state validity

3. **Verify cron is working**
   - Check cron service status
   - Manually trigger cron command
   - Check log file gets created

4. **Monitor daily runs**
   - Check logs/askslim_daily.log each day
   - Verify media_files table gets new entries
   - Verify charts appear in Streamlit UI

---

## Files Deployed to Remote

| File | Status | Purpose |
|------|--------|---------|
| db/riley.sqlite | ✅ Replaced | Working database with all projections |
| app/Home.py | ✅ Updated | Latest UI with sector column |
| app/db.py | ✅ Updated | Latest queries with sector SELECT |
| src/riley/modules/askslim/askslim_run_daily.py | ✅ Fixed | Added sys.path setup |
| src/riley/modules/askslim/askslim_smoketest.py | ✅ Updated | Latest version |
| src/riley/modules/askslim/askslim_scraper.py | ✅ Updated | Media tracking enabled |

---

## Summary

**Fixed:**
- ✅ Database projections restored
- ✅ Scraper import errors fixed
- ✅ All scraper modules updated
- ✅ Streamlit showing correct data

**Needs Manual Testing:**
- ⚠️ Run scraper and verify it works
- ⚠️ Check Playwright browsers installed
- ⚠️ Verify session state valid
- ⚠️ Confirm cron job executes

**The scraper SHOULD work now, but needs manual execution test to confirm Playwright and session state are configured correctly.**
