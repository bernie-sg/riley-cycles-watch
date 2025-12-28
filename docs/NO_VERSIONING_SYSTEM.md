# No-Versioning System for askSlim Data

**Implemented:** 28-Dec-2025
**Reason:** User requested removal of versioning - "askSlim always has latest, no history needed"

---

## What Changed

### Old System (With Versioning)
```
askSlim scrapes → Marks old as SUPERSEDED, creates NEW version
Database keeps: v1 (SUPERSEDED), v2 (SUPERSEDED), ..., v13 (ACTIVE)
Result: 336 cycle_specs records, 178 SUPERSEDED
```

### New System (No Versioning)
```
askSlim scrapes → DELETES old record, creates NEW with version=1
Database keeps: Only v1 (ACTIVE)
Result: 154 cycle_specs records, 0 SUPERSEDED
```

---

## Implementation

### Modified Files

**1. `src/riley/modules/askslim/askslim_scraper.py`**

**Old logic (lines 200-248):**
- Check for existing ACTIVE spec
- Mark old as SUPERSEDED
- Insert new with version = old_version + 1

**New logic:**
```python
# Delete any existing cycle spec for this instrument/timeframe
DELETE FROM cycle_specs
WHERE instrument_id = ? AND timeframe = ? AND source = 'askSlim'

# Insert new record (always version=1)
INSERT INTO cycle_specs (..., version = 1, status = 'ACTIVE', ...)
```

**Key change:** Simple DELETE + INSERT, no version tracking

---

## Database Cleanup Performed

### 1. Deleted Old Records
```
Deleted 138 SUPERSEDED cycle_specs
Deleted 36 inactive cycle_projections
Total: 174 old records removed
```

### 2. Reset Versions to 1
```
Updated 154 askSlim specs from various versions (1-13) to version=1
```

---

## Current State

### cycle_specs (askSlim)
```
Total records: 154
Unique symbol/timeframe combos: 154
ACTIVE: 154
SUPERSEDED: 0
Version range: 1 to 1
```

**✅ PERFECT:** 1 record per symbol/timeframe, all version=1

### cycle_projections (askSlim, k=0)
```
Total: 145
Active: 145
Inactive: 0
```

**✅ PERFECT:** No inactive projections

---

## How It Works Now

### When askSlim Scraper Runs

**Step 1:** Scrape askSlim.com
```
Extract: median_date, cycle_length, support, resistance
```

**Step 2:** Update Database (NO VERSIONING)
```sql
-- Delete old record
DELETE FROM cycle_specs
WHERE instrument_id = ? AND timeframe = 'DAILY' AND source = 'askSlim';

-- Insert new record (always version=1)
INSERT INTO cycle_specs (
    instrument_id, timeframe, median_input_date_label,
    cycle_length_bars, source, version, status, ...
) VALUES (?, 'DAILY', '2025-12-31', 26, 'askSlim', 1, 'ACTIVE', ...);
```

**Step 3:** Rebuild Projections
```sql
-- Delete old projections for version=1
DELETE FROM cycle_projections
WHERE instrument_id = ? AND timeframe = 'DAILY' AND version = 1;

-- Create new projection (version=1)
INSERT INTO cycle_projections (..., version = 1, active = 1, ...);
```

**Result:** Database always has latest data only, no history

---

## Guarantees

### 1. Only One Record Per Symbol/Timeframe
```sql
SELECT instrument_id, timeframe, COUNT(*)
FROM cycle_specs
WHERE source = 'askSlim'
GROUP BY instrument_id, timeframe
-- Always returns count = 1
```

### 2. All Records at Version 1
```sql
SELECT DISTINCT version FROM cycle_specs WHERE source = 'askSlim'
-- Always returns: 1
```

### 3. No SUPERSEDED Records
```sql
SELECT COUNT(*) FROM cycle_specs WHERE source = 'askSlim' AND status = 'SUPERSEDED'
-- Always returns: 0
```

### 4. No Inactive Projections
```sql
SELECT COUNT(*) FROM cycle_projections cp
JOIN cycle_specs cs ON cs.cycle_id = cp.cycle_id
WHERE cs.source = 'askSlim' AND cp.active = 0 AND cp.k = 0
-- Always returns: 0
```

---

## Benefits

### ✅ Simpler Database
- 174 fewer records immediately
- No SUPERSEDED clutter
- No inactive projections

### ✅ Faster Queries
- No need to filter by status = 'ACTIVE'
- No need to check version numbers
- Less data to scan

### ✅ Cleaner Logic
- No version incrementing
- No SUPERSEDED marking
- Simple DELETE + INSERT

### ✅ Matches Philosophy
- "askSlim always has latest"
- No historical data needed
- Clean, current state only

---

## Trade-offs

### ⚠️ No Audit Trail
- Can't see what askSlim said yesterday vs today
- Can't debug "when did cycle date change?"
- Can't rollback to previous cycle dates

**User decision:** Acceptable - history not needed for askSlim data

### ⚠️ Can't Compare Versions
- Can't see how cycle specs evolved over time
- Can't track accuracy of askSlim predictions

**User decision:** Not needed for this use case

---

## Important Notes

### Only Affects askSlim Data

This no-versioning system **only applies to:**
- `cycle_specs` where `source = 'askSlim'`
- Related `cycle_projections`

**Other sources:**
- Manual cycle specs (if any) still use versioning
- Database schema still supports versioning
- Other tools can still use versioning if needed

### Versioning Still Supported

The database schema **still has version column**:
- Can be used by other data sources
- Can be re-enabled if needed
- askSlim just always uses version=1

---

## Example Workflow

### Initial State
```
ES DAILY: cycle_id=302, version=1, median=2025-12-28
```

### askSlim Scrapes (finds new data)
```
New median: 2025-12-31
```

### Database Update
```sql
-- Delete old
DELETE FROM cycle_specs WHERE instrument_id=1 AND timeframe='DAILY' AND source='askSlim'
-- Deleted 1 row (cycle_id=302)

-- Insert new
INSERT INTO cycle_specs (..., version=1, median='2025-12-31', ...)
-- Created cycle_id=337
```

### Result
```
ES DAILY: cycle_id=337, version=1, median=2025-12-31
(Old cycle_id=302 is GONE - deleted)
```

---

## Verification Commands

### Check No Duplicates
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect("db/riley.sqlite")
cursor = conn.cursor()

cursor.execute("""
    SELECT instrument_id, timeframe, COUNT(*)
    FROM cycle_specs
    WHERE source = 'askSlim'
    GROUP BY instrument_id, timeframe
    HAVING COUNT(*) > 1
""")

dupes = cursor.fetchall()
if dupes:
    print(f"❌ Found {len(dupes)} duplicates!")
else:
    print("✅ No duplicates - all clean!")
conn.close()
EOF
```

### Check All Version=1
```bash
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect("db/riley.sqlite")
cursor = conn.cursor()

cursor.execute("""
    SELECT DISTINCT version FROM cycle_specs WHERE source = 'askSlim'
""")
versions = [r[0] for r in cursor.fetchall()]

if versions == [1]:
    print("✅ All askSlim specs at version=1")
else:
    print(f"❌ Unexpected versions: {versions}")
conn.close()
EOF
```

---

## Future Considerations

### If History Needed Later

Can add separate audit log table:
```sql
CREATE TABLE cycle_specs_audit (
    audit_id INTEGER PRIMARY KEY,
    instrument_id INTEGER,
    timeframe TEXT,
    median_input_date_label TEXT,
    cycle_length_bars INTEGER,
    scraped_at TEXT,
    source TEXT
);
```

Then log each scrape before deleting:
```python
# Before DELETE
INSERT INTO cycle_specs_audit SELECT ... FROM cycle_specs WHERE ...
# Then DELETE old and INSERT new
```

This separates operational data from audit trail.

---

**Status:** ✅ Active and working
**Verified:** 28-Dec-2025
**Database cleaned:** All old versions removed

**End of No-Versioning Documentation**
