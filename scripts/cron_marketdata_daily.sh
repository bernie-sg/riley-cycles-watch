#!/bin/bash
#
# Daily Market Data Collection Cron Job
# Run daily to update OHLCV prices and export to RRG CSV
#
# Recommended cron schedule: 01:30 daily (after market close)
# 30 1 * * * /home/riley/scripts/cron_marketdata_daily.sh >> /home/riley/logs/marketdata_cron.log 2>&1

set -e  # Exit on error

# Configuration
PROJECT_ROOT="/home/riley"
SCRIPT_PATH="${PROJECT_ROOT}/scripts/riley_marketdata.py"
EXPORT_PATH="${PROJECT_ROOT}/artifacts/rrg/rrg_prices_daily.csv"
LOG_DIR="${PROJECT_ROOT}/logs"

# Ensure log directory exists
mkdir -p "${LOG_DIR}"

# Timestamp
echo "=========================================="
echo "Market Data Daily Update"
echo "Started: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="

# Activate virtual environment if it exists
if [ -f "${PROJECT_ROOT}/venv/bin/activate" ]; then
    source "${PROJECT_ROOT}/venv/bin/activate"
fi

# Run daily update with export
python3 "${SCRIPT_PATH}" update \
    --overlap-days 10 \
    --export "${EXPORT_PATH}"

# Verify data
python3 "${SCRIPT_PATH}" verify

# Show stats
python3 "${SCRIPT_PATH}" stats

echo "=========================================="
echo "Completed: $(date '+%Y-%m-%d %H:%M:%S')"
echo "=========================================="
echo ""
