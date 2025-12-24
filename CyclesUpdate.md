# Riley Project — Cycles Watch
## How Updates Are Entered (Authoritative Guide)

This document defines **how data is updated** in the Cycles Watch system.
All updates are deterministic and database-backed.
Bernard does NOT run Python manually — Claude Code executes all steps.

---

## GLOBAL RULES (DO NOT CHANGE)

- Logic uses **TRADING BARS ONLY**
  - DAILY → Trading Days (TD)
  - WEEKLY → Trading Weeks (TW)
- Calendar dates are **labels only**
- If a provided date is not a trading day:
  - Snap to the **next trading day**
  - Never snap backward
- Defaults (implicit, unless explicitly overridden):
  - Window: ±3 bars
  - Pre-window: 2 bars
- Canonical instrument model:
  - ES is canonical
  - SPX / SPY are aliases
  - All logic attaches to ES
  - Notes may reference SPX prices

---

## TYPES OF UPDATES

There are **only three** types of updates in Phase 1:

1. Cycle updates (weekly / daily)
2. Desk note updates (bullet points)
3. Daily scan runs (read-only)

No other updates exist.

---

## 1) CYCLE UPDATE (WEEKLY or DAILY)

### What Bernard provides (conceptual input)

- Instrument
- Timeframe (DAILY or WEEKLY)
- Anchor date (median / trough estimate)
- Cycle length (bars)
- Source (optional)

Window and pre-window are assumed from defaults.

---

### Example — WEEKLY cycle update (ES)

**Conceptual input:**
- Instrument: ES
- Timeframe: WEEKLY
- Anchor date: 2026-01-04
- Cycle length: 37 bars
- Source: AskSlim

**What Claude Code does automatically:**
- Snap anchor to next trading week
- Version the cycle
- Supersede prior weekly cycle (if any)
- Project forward/backward troughs
- Store projections

**Executed command (Claude runs):**
```bash
python scripts/cycles_set_spec.py \
  --symbol ES \
  --tf WEEKLY \
  --anchor 2026-01-04 \
  --len 37 \
  --source "AskSlim"
```

---

### Example — DAILY cycle update (ES)

**Conceptual input:**
- Instrument: ES
- Timeframe: DAILY
- Anchor date: 2025-12-28
- Cycle length: 26 bars
- Source: AskSlim

**Executed command (Claude runs):**
```bash
python scripts/cycles_set_spec.py \
  --symbol ES \
  --tf DAILY \
  --anchor 2025-12-28 \
  --len 26 \
  --source "AskSlim"
```

---

### Important behavior
- You do NOT restate window size or pre-window
- You do NOT calculate dates
- If the cycle changes later:
  - The cycle is re-entered
  - Version increments
  - Old projections are preserved but marked inactive

Cycles are dynamic by design.

---

## 2) DESK NOTE UPDATE (Narrative / Levels / Risk)

Desk notes capture how you interpret the market, not signals.

### What Bernard provides
- Instrument (always ES)
- As-of date
- Bullet points
- Optional structured fields (zones, ranges)
- Price reference (SPX if using cash index levels)

---

### Example — Desk note (ES, SPX-referenced levels)

**Bullet content (example):**
- Still in a trading range, upside is capped – Weekly chart
- AI plays are getting weaker; 2026 likely differs from 2025
- Weekly cycle trough due 12-01 to 01-19
- Downside zone 6668–6601; break below is concerning

**Bullets file (notes/es_2025-12-20.json):**
```json
[
  "Still in a trading range, upside is capped – Weekly chart",
  "AI plays are getting weaker; 2026 likely differs from 2025",
  "Weekly cycle trough due 12-01 to 01-19",
  "Downside zone 6668–6601; break below is concerning"
]
```

**Executed command (Claude runs):**
```bash
python scripts/cycles_add_note.py \
  --symbol ES \
  --asof 2025-12-20 \
  --author Bernard \
  --scope BOTH \
  --type SUMMARY \
  --ref SPX \
  --bullets-file notes/es_2025-12-20.json
```

---

### Notes behavior
- Notes always attach to ES
- `price_reference` explains level origin
- Notes are historical and never overwritten
- Multiple notes per day are allowed

---

## 3) DAILY SCAN (READ-ONLY)

The scan checks time proximity to cycle windows.
No price logic in Phase 1.

### What Bernard says

"Run scan"

**Executed command (Claude runs):**
```bash
python scripts/cycles_run_scan.py --asof 2025-12-20
```

### Output includes
- Instruments approaching daily windows
- Instruments approaching weekly windows
- Pre-window vs in-window status
- Overlap flag (daily inside weekly)
- Priority ranking

Scans are stored for audit.

---

## SUMMARY — HOW YOU USE THE SYSTEM

- **Cycles:** tell the system what you believe (update when it changes)
- **Notes:** record how you interpret the environment
- **Scan:** shows what deserves attention next

No charts.
No price modeling.
No discretion inside the system.

This is the foundation.
