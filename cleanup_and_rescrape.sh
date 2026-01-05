#!/bin/bash
# Clean up all charts and rescrape from scratch

cd /home/raysudo/riley-cycles

echo "=========================================="
echo "CLEANUP & RESCRAPE"
echo "=========================================="

# 1. Delete all chart files
echo -e "\n1. Deleting all askslim chart files..."
find media -name "*.png" -path "*/askslim/*" -delete
echo "✓ Charts deleted"

# 2. Clean media_files table
echo -e "\n2. Cleaning media_files table..."
sqlite3 db/riley.sqlite "DELETE FROM media_files WHERE category='askslim';"
echo "✓ Database cleaned"

# 3. Activate venv
source venv/bin/activate

# 4. Deploy updated scripts
echo -e "\n3. Scripts already deployed"

# 5. Run complete scraper
echo -e "\n4. Running complete scraper (Futures + Equities)..."
python3 src/riley/modules/askslim/askslim_run_daily.py

echo -e "\n=========================================="
echo "COMPLETE"
echo "=========================================="
