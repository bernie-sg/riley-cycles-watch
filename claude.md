# CLAUDE.md — Riley Project (Cycles Watch Mode)

You are Claude Code operating inside this repository.

## Your role (Phase 1: Cycles Watch)
You run the work end-to-end. Bernard should not have to run Python commands manually.
Your output should be *commands executed + proof output*.

Scope for Phase 1:
- Maintain a **Cycles Watch database** for instruments.
- Maintain **trading calendars** (TD/TW index ↔ date labels).
- Maintain **cycle specs** (anchor + cycle length + defaults).
- Generate **cycle projections** (k forward/backward).
- Store **desk notes** (bullets + optional structured fields).
- Run **daily scans** (pre-window / in-window flags + ranking).

Out of scope (do not work on unless explicitly asked):
- IBKR connectivity
- Charting
- Volume profile / pivots
- Gamma
- Trade plan generation
- Backtesting

## Absolute rules
1) **Do not delete or reset the database** unless Bernard explicitly says: “delete/reset the database”.
   - In particular: never run `rm -f db/riley.sqlite`.
2) **Trading bars only for logic**
   - DAILY uses TD indices.
   - WEEKLY uses TW indices.
   - Calendar days are labels only.
3) **Deterministic snapping**
   - If anchor date is not a trading day: snap to the **next trading day** (never snap backwards).
4) **Global defaults (unless explicitly overridden)**
   - Window: ±3 bars
   - Pre-window: 2 bars
   - Snap rule: NEXT_TRADING_DAY
   - Projection ranges:
     - DAILY: k = -2..+8
     - WEEKLY: k = -2..+6
5) **Canonical instrument model**
   - One canonical instrument (e.g., ES).
   - Aliases (SPX, SPY) must point to the canonical instrument.
   - Notes/levels can carry `price_reference` (e.g., SPX) without creating a separate canonical instrument.
6) **No half-done state**
   - If you start a change that affects schema/scripts, you must finish it to a runnable state and show proof.

## Repository workflow
- Work from repo root: `/Users/bernie/Documents/AI/Riley Project`
- Keep changes small and testable.
- Prefer additive changes (new scripts/modules) over risky refactors.

## User-facing commands (you run these, not Bernard)
These scripts are the official interface for Phase 1:

1) Add instruments + aliases
```bash
python3 scripts/cycles_add_instrument.py --canonical ES --alias SPX --alias SPY
```

2) Import trading calendar (daily CSV) and build weekly calendar
```bash
python3 scripts/cycles_import_calendar.py --symbol ES --daily-csv "calendars/ES_daily.csv"
```

3) Set cycle spec (uses defaults unless provided)
```bash
python3 scripts/cycles_set_spec.py --symbol ES --tf WEEKLY --anchor 2026-01-04 --len 37 --source "AskSlim"
python3 scripts/cycles_set_spec.py --symbol ES --tf DAILY  --anchor 2025-12-28 --len 26 --source "AskSlim"
```

4) Add desk note (bullets JSON file)
```bash
python3 scripts/cycles_add_note.py --symbol ES --asof 2025-12-20 --author Bernard --scope BOTH --type SUMMARY --ref SPX --bullets-file notes/es_2025-12-20.json
```

5) Run daily scan
```bash
python3 scripts/cycles_run_scan.py --asof 2025-12-20
```

## Proof requirements (every time)
After you make changes, you must show:

- migrations applied (if schema changed)
- `pytest -q` result
- a real end-to-end run demonstrating:
  - instruments exist (ES + aliases)
  - calendar imported (TD/TW present)
  - cycle spec saved and versioned
  - projections generated
  - scan prints ranked output

## IMPORTANT NOTE FROM TERMINAL REVIEW
I saw a command that removed the DB file (`rm -f db/riley.sqlite`) during testing.
That must never happen again unless Bernard explicitly requests a DB reset.

If you need a clean test DB:
- create a separate file like `db/riley_test.sqlite` and point tests to it, or
- use an in-memory SQLite DB inside tests.
