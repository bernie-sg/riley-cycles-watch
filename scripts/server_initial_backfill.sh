#!/bin/bash
#
# One-Time Server Initial Backfill
# Run once during server deployment to populate 2 years of historical data
#

set -e  # Exit on error

# Configuration
PROJECT_ROOT="/home/riley"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/riley_marketdata.py"
EXPORT_PATH="${PROJECT_ROOT}/artifacts/rrg/rrg_prices_daily.csv"
LOG_DIR="${PROJECT_ROOT}/logs"

# Ensure directories exist
mkdir -p "${LOG_DIR}"
mkdir -p "${PROJECT_ROOT}/artifacts/rrg"

# Timestamp
echo "=========================================="
echo "Market Data Initial Backfill (2 years)"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Activate virtual environment if it exists
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# Run backfill with 2 years of data
python3 "${SCRIPT_PATH}" backfill \
    --lookback-days 730 \
    --export "${EXPORT_PATH}"

# Verify data
python3 "${SCRIPT_PATH}" verify

# Show stats
python3 "${SCRIPT_PATH}" stats

echo "=========================================="
echo "Backfill completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Configure cron job for daily updates"
echo "2. Add to crontab: 30 1 * * * ${PROJECT_ROOT}/scripts/cron_marketdata_daily.sh >> ${LOG_DIR}/marketdata_cron.log 2>&1"
