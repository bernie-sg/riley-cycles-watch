# Riley Project

Deterministic trading pipeline for quantitative analysis.

## Quick Start

### Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Initialize database
python -c "from src.riley.database import Database; db = Database(); db.run_migrations(); print('Database initialized')"
```

### Run Pipeline

```bash
# Run for a single instrument
python scripts/riley_run_one.py --symbol SPX

# Run for a specific date
python scripts/riley_run_one.py --symbol SPX --date 2025-01-15
```

### Run Tests

```bash
pytest
```

## Project Structure

```
/docs                      # Project documentation
/config                    # Configuration files
  /cycles                  # Cycle packs (user-supplied)
/data
  /raw                     # Immutable raw data
  /processed               # Standardized bars
/artifacts
  /charts                  # Generated charts
  /packets                 # Analysis packets
/reports
  /skeletons               # LLM-generated skeletons
  /final                   # Analyst-filled reports
/db                        # SQLite database
  /migrations              # Schema migrations
/src/riley                 # Python package
/tests                     # Unit tests
/scripts                   # CLI entry points
/logs                      # Run logs
```

## Pipeline Components

1. **Data Loading** - Load or stub market data
2. **Feature Computation** - Detect pivots, compute levels, regimes
3. **Chart Generation** - Create labeled weekly/daily charts
4. **Packet Writing** - Bundle all analysis data as JSON
5. **Report Skeleton** - Generate Markdown template for analyst
6. **Database Recording** - Track runs and analysis

## Output

For each run, the pipeline generates:

- **Charts**: `artifacts/charts/{symbol}/{YYYY-MM-DD}/weekly.png` and `daily.png`
- **Packets**: `artifacts/packets/{symbol}/{YYYY-MM-DD}/*.json`
- **Report**: `reports/skeletons/{symbol}/{YYYY-MM-DD}/{symbol}_{YYYY-MM-DD}_skeleton.md`

## Deterministic Design

- No LLM inference in pipeline
- No trading opinions generated
- Append-only data policy
- Singapore timezone (Asia/Singapore)
- Reproducible results

## Next Steps

1. Integrate IBKR data feed
2. Implement TradingView CSV ingestion
3. Add cycle pack support (YAML)
4. Build daily batch runner
5. Add diff computation (compare to previous day)
