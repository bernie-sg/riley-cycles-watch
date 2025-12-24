# Cycle Write Firewall - Documentation

## Overview

The Cycle Write Firewall ensures that cycle inputs can **ONLY** be changed through one canonical API, preventing database corruption.

**Key Principles:**
- DAILY cycles use `trading_calendar_daily` (TD indices)
- WEEKLY cycles use `trading_calendar_weekly` (TW indices)
- Never mix calendars
- Window = median ±3 bars (defaults)
- Exactly ONE projection per spec (k=0 only)
- All changes trigger deterministic rebuild + validation

## Operator Flow (Bernard)

### Setting a Cycle Median

```bash
# Set ES DAILY median
python3 scripts/riley_set_cycle.py ES DAILY 2025-12-28

# Set ES WEEKLY median
python3 scripts/riley_set_cycle.py ES WEEKLY 2026-01-04

# Create new version (instead of replacing)
python3 scripts/riley_set_cycle.py ES DAILY 2026-01-10 --bump

# Custom window size
python3 scripts/riley_set_cycle.py PL DAILY 2025-12-24 --window-minus 5 --window-plus 5
```

### Running Scan (Read-Only)

```bash
python3 scripts/cycles_run_scan.py --asof 2025-12-23
```

The scan will **refuse to run** if cycle validation fails (tripwire protection).

### Viewing Cycles

UI at http://localhost:8501 shows cycles with validation banner if invalid.

## API Reference

### CycleService (src/riley/cycle_service.py)

```python
from src.riley.cycle_service import CycleService

service = CycleService()

# Set cycle median (THE CANONICAL WAY)
result = service.set_cycle_median(
    symbol='ES',
    timeframe='DAILY',
    median_label='2025-12-28',
    window_minus_bars=3,  # Default
    window_plus_bars=3,   # Default
    versioning='REPLACE'  # or 'BUMP' for new version
)

# Update window defaults
service.add_or_update_cycle_defaults(
    symbol='ES',
    timeframe='DAILY',
    window_minus_bars=5,
    window_plus_bars=5
)

# Get cycle info (read-only)
info = service.get_cycle_info('ES', 'DAILY')
```

### Validation (src/riley/cycle_validation.py)

```python
from src.riley.cycle_validation import validate_cycles, CycleValidationError

conn = sqlite3.connect('db/riley.sqlite')

try:
    validate_cycles(conn)  # All instruments
    # or
    validate_cycles(conn, symbol='ES')  # Specific instrument
except CycleValidationError as e:
    print(f"Validation failed: {e}")
```

## Validation Checks (Tripwires)

The firewall validates:

1. **No duplicate projections** - Unique (instrument_id, timeframe, version, k)
2. **Exactly one k=0 per active spec** - No missing/extra projections
3. **Math correctness:**
   - DAILY: `core_start_td_index = median_td_index - window_minus_bars`
   - WEEKLY: `core_start_tw_index = median_tw_index - window_minus_bars`
4. **Label resolution** - All label columns non-NULL
5. **No cross-calendar contamination:**
   - DAILY: TD fields set, TW fields NULL
   - WEEKLY: TW fields set, TD fields NULL

## Architecture

### Write Path (ONE WAY ONLY)

```
User/Bernard
    ↓
riley_set_cycle.py (CLI)
    ↓
CycleService.set_cycle_median()
    ↓
CyclesRebuilder.rebuild_one()
    ↓
cycle_projections (deterministic INSERT)
    ↓
validate_cycles() (tripwire)
```

### Read Path (Many Consumers)

```
cycle_projections.{core_start_label, core_end_label}
    ↓
├── Scanner (scripts/cycles_run_scan.py)
├── UI (app/db.py)
├── Reports (scripts/cycles_watchlist_snapshot.py)
└── Countdown (scripts/cycles_window_countdown.py)
```

**IMPORTANT:** Readers use label columns directly, NEVER join trading calendars to infer windows.

## Test Coverage

Run tests:
```bash
pytest tests/test_cycle_firewall.py -v
```

Tests prove:
- ✓ DAILY cycles use TD indices only
- ✓ WEEKLY cycles use TW indices only
- ✓ No duplicates on rebuild
- ✓ Version bumping works correctly
- ✓ Tampering is detected by validation
- ✓ NULL labels caught
- ✓ Cross-calendar contamination caught
- ✓ Updating defaults triggers rebuild

## Migration from Old System

The old system had:
- Ambiguous `core_start_index` (could be TD or TW)
- Multiple k iterations (k=-2 to k=2)
- Manual calendar joins
- No validation

The new system:
- Explicit `*_td_index` and `*_tw_index` fields
- Single projection (k=0 only)
- Pre-computed label columns
- Strict validation enforced

Existing projections were:
1. Deleted (corrupted)
2. Rebuilt deterministically from specs
3. Validated (all 44 projections PASS)

## Maintenance

### Adding a New Instrument

```bash
# 1. Add instrument to instruments table (via data management script)

# 2. Set cycles
python3 scripts/riley_set_cycle.py NEWINST DAILY 2026-01-15
python3 scripts/riley_set_cycle.py NEWINST WEEKLY 2026-01-10
```

### Changing Window Defaults

```python
from src.riley.cycle_service import CycleService
service = CycleService()

# Update to ±5 bars instead of ±3
service.add_or_update_cycle_defaults(
    'ES', 'DAILY',
    window_minus_bars=5,
    window_plus_bars=5
)
```

### Troubleshooting

If validation fails:
```bash
# 1. Run repair to rebuild all projections
python3 scripts/riley_repair_cycles.py --all

# 2. Verify validation passes
python3 -c "
from src.riley.cycle_validation import validate_cycles
import sqlite3
conn = sqlite3.connect('db/riley.sqlite')
validate_cycles(conn)
print('✓ All cycles valid')
"
```

## File Inventory

### Core Modules
- `src/riley/cycle_service.py` - Canonical write API (**ONLY** legal write path)
- `src/riley/cycles_rebuild.py` - Deterministic projection builder
- `src/riley/cycle_validation.py` - Tripwire validation checks

### Scripts
- `scripts/riley_set_cycle.py` - CLI for Bernard to set medians
- `scripts/riley_repair_cycles.py` - Full rebuild (emergency use)

### Tests
- `tests/test_cycle_firewall.py` - Proves corruption cannot recur

### Readers (NO WRITES)
- `app/db.py` - UI database layer
- `scripts/cycles_run_scan.py` - Scanner
- `scripts/cycles_watchlist_snapshot.py` - Reports
- `scripts/cycles_window_countdown.py` - Countdown

## Security Guarantees

✓ **No duplicate projections** - UNIQUE index enforced at DB level
✓ **No silent drift** - validate_cycles() called before scan/UI
✓ **No calendar mixing** - DAILY uses TD, WEEKLY uses TW
✓ **No stale windows** - Rebuild always triggered on change
✓ **No ambiguity** - Label columns pre-computed and stored

## Migration Checklist

✅ Deleted all corrupted projections
✅ Rebuilt 44 projections deterministically
✅ All validation checks pass
✅ Tests prove tampering is caught
✅ CLI entrypoint created
✅ UI uses label columns only
✅ Scan validates before running
✅ Documentation complete
