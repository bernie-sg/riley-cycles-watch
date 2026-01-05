#!/bin/bash
# Verify scraper results

cd /Users/bernie/Documents/AI/Riley\ Project

echo "=========================================="
echo "SCRAPE VERIFICATION"
echo "=========================================="

echo -e "\n1. Chart Files on Disk:"
echo "   Futures charts: $(find media -name "*.png" -path "*/askslim/*" | grep -E "(ES|NQ|RTY|ZB|EURUSD|DXY|USDJPY|AUDUSD|GBPUSD|GC|SI|PL|HG|CL|NG|ZC|ZS|ZW)" | wc -l)"
echo "   Stock/ETF charts: $(find media -name "*.png" -path "*/askslim/*" | grep -E "(AAPL|MSFT|NVDA|GOOGL|META|AMD|AMZN|TSLA|JPM|GS)" | wc -l)"
echo "   Total charts: $(find media -name "*.png" -path "*/askslim/*" | wc -l)"

echo -e "\n2. Database Records:"
sqlite3 db/riley.sqlite "SELECT COUNT(*) as total_records FROM media_files WHERE category='askslim';"

echo -e "\n3. Charts by Upload Date:"
sqlite3 db/riley.sqlite "SELECT upload_date, COUNT(*) as count FROM media_files WHERE category='askslim' GROUP BY upload_date ORDER BY upload_date DESC;"

echo -e "\n4. File Path Check (should be relative):"
sqlite3 db/riley.sqlite "SELECT file_path FROM media_files WHERE category='askslim' LIMIT 5;"

echo -e "\n5. Instruments with Charts:"
sqlite3 db/riley.sqlite "
SELECT i.symbol, COUNT(DISTINCT mf.timeframe) as timeframes_count
FROM instruments i
JOIN media_files mf ON i.instrument_id = mf.instrument_id
WHERE mf.category = 'askslim'
GROUP BY i.symbol
ORDER BY i.symbol
" | head -20

echo -e "\n=========================================="
