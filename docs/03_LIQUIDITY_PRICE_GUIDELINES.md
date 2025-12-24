# Riley Project — Liquidity & Price-Level Interpretation Guidelines

## Purpose

This document defines **how price levels are interpreted and used** inside Riley.

It does NOT define mechanical entries.
It defines **how to reason about price, liquidity, and inventory** once time permission exists.

Price levels are **candidates**, not signals.

---

## Core Principle

> **Price levels matter only when time makes them matter.**

Liquidity without timing is noise.  
Timing without liquidity is blind.

---

## Types of Price Levels (Hierarchy)

All price levels are ranked.  
They are not equal.

### Tier 1 — Structural Liquidity
*(Highest importance)*

- Weekly / Monthly swing highs & lows
- Major distribution or accumulation ranges
- Long-term consolidation boundaries

**Interpretation**
- Represents locations where large inventory exists
- Defines where *structural decisions* are made
- Especially important during **weekly cycle windows**

Tier 1 levels define **the battlefield**, not the entry.

---

### Tier 2 — Volume Inventory Levels
*(Contextual importance)*

- Volume Profile POCs (1Y, 6M, 90D)
- High Volume Nodes (HVN)
- Low Volume Nodes (LVN)

**Interpretation**
- Shows where business was done
- Indicates balance vs rejection zones
- Acts as *inventory reference*, not support/resistance

POCs do NOT cause bounces.
They show where reactions are *possible*.

---

### Tier 3 — Gamma-Driven Levels
*(Present-tense importance)*

- Call walls
- Put walls
- Gamma flips
- Dealer magnet zones

**Interpretation**
- Explains why price may stick, accelerate, or reject *now*
- Highly time-sensitive
- Strongest near expiry / OpEx

Gamma levels are **conditional** and must be re-evaluated daily.

---

### Tier 4 — Tactical Levels
*(Lowest importance)*

- VWAP
- Intraday highs/lows
- Short-term ranges

**Interpretation**
- Execution aids only
- Never decisive on their own

---

## How Liquidity Is Used (What Riley Does)

### Liquidity answers ONE question:
> **Where can institutions transact size?**

Liquidity does NOT answer:
- When price will arrive
- Which direction will win
- Whether a level will hold

---

## Interaction Between Time & Liquidity

### Outside Cycle Windows
- Liquidity is **descriptive only**
- Riley may observe but not commit
- Levels are noted, not acted upon

---

### Inside Weekly Window (No Daily Yet)
- Liquidity defines **zones of interest**
- Expect:
  - false breaks
  - stop runs
  - probing behavior
- Riley may hypothesize but not execute

---

### Inside Daily + Weekly Overlap
- Liquidity becomes **actionable context**
- Riley may:
  - Rank nearby levels
  - Ask: *Which level is price being drawn toward now?*
  - Combine with gamma for confirmation

This is where price × time × liquidity intersect.

---

## How Levels Are Interpreted (Critical)

### A level being hit does NOT mean:
- Buy
- Sell
- Bounce
- Reversal

It means:
> **Observe reaction quality.**

---

## Reaction Quality (What Matters)

At a level, Riley evaluates:

- Speed (fast vs slow approach)
- Volume response
- Acceptance vs rejection
- Gamma behavior
- Follow-through or failure

Good reactions:
- Strong displacement
- Clear rejection
- Gamma alignment

Bad reactions:
- Chop
- Overlapping bars
- No volume response

---

## Early / On-Time / Late Behavior at Levels

During dominant weekly cycles:
- Early reactions are valid
- Late reactions are common
- Multiple failures are expected

A failed reaction is **information**, not invalidation.

---

## Conflicting Levels

If multiple levels cluster:
- Expect higher volatility
- Expect whipsaws
- Reduce conviction
- Prefer WAIT unless clarity emerges

If levels are widely spaced:
- Moves tend to be faster
- Resolution clearer

---

## Liquidity vs Structure

Structure defines **importance**.  
Liquidity defines **participation**.

Neither overrides time.

---

## Language Discipline for Price Levels

Riley must say:
- “This level is a candidate”
- “Reaction here would be significant”
- “If price accepts above/below…”

Riley must NOT say:
- “This level will hold”
- “Guaranteed support”
- “This is the bottom”

---

## Final Guideline

> **Price levels are questions, not answers.**

Time decides *when to ask*.  
Flow decides *how price responds*.  
Riley’s job is to frame the question correctly.

---

## Integration Rule

No price-level analysis is valid unless:
- Time context is stated
- The level’s tier is identified
- Reaction criteria are defined