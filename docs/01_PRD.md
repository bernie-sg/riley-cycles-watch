Riley Project — Product Requirements Document (PRD)

1. Overview

1.1 Product Name

Riley Project

1.2 Purpose

The Riley Project is a human-in-the-loop institutional trading intelligence platform.

Its purpose is to:
	•	Collect market data daily
	•	Render full-context charts (weekly + daily)
	•	Integrate human-supplied cycle intelligence
	•	Compute volume, inventory, and gamma context
	•	Generate structured, actionable trading plans
	•	Persist all analysis in a database
	•	Present results via a dashboard and per-instrument reports

The system does not auto-trade.
It produces decision-ready trade plans.

⸻

2. Core Design Principles (Non-Negotiable)
	1.	Human authority over time (cycles)
	2.	Machine authority over computation and enforcement
	3.	Context before analysis
	4.	No intent inference by AI
	5.	Everything is logged and auditable

⸻

3. High-Level System Architecture

Data Sources
   ↓
Data Ingestion Layer
   ↓
Chart Generation Engine
   ↓
Context + Feature Computation
   ↓
LLM Analysis Engine
   ↓
Analysis Database
   ↓
Dashboard / Reports


⸻

4. Data Collection Layer

4.1 Instruments
	•	Equities
	•	Index ETFs
	•	Futures (ES, NQ, CL, GC, etc.)

4.2 Data Sources

Primary
	•	Interactive Brokers (IBKR)
	•	Daily bars
	•	Intraday (optional later)

Secondary / Manual Fallback
	•	TradingView CSV exports
	•	Used when IBKR history is insufficient (e.g. futures roll issues)
	•	User drops CSV into a predefined folder

4.3 Data Storage

Raw data is stored immutably:

/data/raw/{instrument}/{source}/{date}.csv

Processed data:

/data/processed/{instrument}/{timeframe}.parquet


⸻

5. Chart Generation Engine

5.1 Required Charts

For every instrument, daily:
	•	Weekly Context Chart (5Y or max available)
	•	Daily Context Chart (1Y)

5.2 Chart Requirements

Charts must include:
	•	Price
	•	Volume
	•	Major swing highs/lows
	•	Optional volume profile overlay
	•	Cycle window overlays (if supplied)

Charts are generated as:

/charts/{instrument}/{date}/weekly.png
/charts/{instrument}/{date}/daily.png

No analysis occurs without charts.

⸻

6. Cycle Input System (Critical)

6.1 Cycle Authority

Cycles are never inferred.
They are explicitly supplied by the user.

6.2 Cycle Input Format

Initial format: YAML or JSON

Example:

instrument: ES
cycle_type: daily_low_window
window_start: 2025-12-18
window_end: 2025-12-21
confidence: A
notes: "Expected short-term low"

6.3 Storage

/cycles/{instrument}/cycles.yaml

Cycles are versioned and timestamped.

⸻

7. Feature Computation Layer

7.1 Volume Engine

Computes:
	•	Volume profile
	•	POC (90D, 6M, 1Y)
	•	High/low volume nodes
	•	Inventory zones

Outputs stored as structured JSON.

⸻

7.2 Gamma Engine

Computes:
	•	Options open interest
	•	Gamma exposure by strike
	•	Dealer pressure zones
	•	Pinning vs acceleration regimes

Gamma is treated as present-tense constraint, not direction.

⸻

8. Context Classification Engine

Classifies each instrument daily:
	•	Regime (trend / range)
	•	Market state (Vacation / Build / War / Sprint)
	•	Location (high / mid / low of range)
	•	Volatility (expanding / contracting)

Outputs a Context Header used by the LLM.

⸻

9. LLM Analysis Engine

9.1 Inputs
	•	Context Header
	•	Weekly & Daily chart images
	•	Volume features
	•	Gamma features
	•	Active cycle windows

9.2 Responsibilities

The LLM:
	•	Does NOT guess intent
	•	Does NOT invent cycles
	•	Synthesizes provided inputs

9.3 Required Output (Structured)

For each instrument:
	•	Market state summary
	•	Valid trade direction:
	•	Long
	•	Short
	•	Wait
	•	Plan A
	•	Plan B (invalidation)
	•	Key levels:
	•	Entry zone
	•	Stop loss
	•	Take profit(s)
	•	Trade quality score (A/B/C)
	•	Rationale (concise)

Output format: JSON + Markdown summary.

⸻

10. Analysis Database

10.1 Purpose

To store every daily analysis for:
	•	Review
	•	Comparison
	•	Model improvement
	•	Accountability

10.2 Schema (High Level)
	•	Instrument
	•	Date
	•	Context Header
	•	Cycle references
	•	Volume snapshot
	•	Gamma snapshot
	•	LLM output
	•	Final trade plan

Database options:
	•	PostgreSQL (preferred)
	•	SQLite (Phase 1)

⸻

11. Dashboard & Front-End

11.1 Dashboard View
	•	Instrument list
	•	Current state
	•	Active cycle windows
	•	Trade direction (Long / Short / Wait)
	•	Trade quality score

11.2 Instrument Detail View

Click-through report:
	•	Charts
	•	Context summary
	•	Volume & gamma visuals
	•	Trade Plan (Plan A / B)

11.3 Report Persistence

Each report is stored and viewable historically.

⸻

12. Daily Automation Flow
	1.	Fetch latest data
	2.	Update processed datasets
	3.	Generate charts
	4.	Load active cycles
	5.	Compute volume & gamma
	6.	Generate context header
	7.	Run LLM analysis
	8.	Store results in database
	9.	Update dashboard

No step may be skipped.

⸻

13. Output Standard (End Product)

Every instrument, every day, ends with:

Actionable Trading Plan

	•	Do I go Long?
	•	Do I go Short?
	•	Do I wait?
	•	What must happen next?
	•	Where am I wrong?

If this cannot be answered, the analysis is invalid.

⸻

14. Phased Development

Phase 1
	•	Data ingestion
	•	Chart generation
	•	Manual cycle input
	•	LLM analysis
	•	File-based storage

Phase 2
	•	Database integration
	•	Scanner
	•	Dashboard UI

Phase 3
	•	Execution assistance
	•	Alerts
	•	Backtesting / review tools

⸻

15. Success Criteria

The system is successful if:
	•	Analysis is consistent day-to-day
	•	Context is preserved
	•	Trade plans are auditable
	•	Human insight is preserved
	•	Randomness is reduced

⸻

Final Requirement

Riley must never guess.

If context, cycles, or data are missing:

The correct output is: WAIT.