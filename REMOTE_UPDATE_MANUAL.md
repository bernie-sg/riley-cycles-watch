# Manual Remote Server Update Instructions

## Problem
Remote server (cycles.cosmicalsignals.net) has:
- ❌ All instruments showing "UNCLASSIFIED" sectors
- ❌ No charts displaying
- ❌ Filters not working

## Solution
You need to manually update the remote server. Here's how:

---

## Step 1: SSH into Remote Server

```bash
ssh raysudo@45.76.168.214
# OR use whatever method you normally use to access the server
```

---

## Step 2: Update Instruments with Proper Sectors

Save this Python script and run it on the remote server:

```bash
cd /home/raysudo/riley-cycles
```

Create file: `/home/raysudo/riley-cycles/fix_instruments_sectors.py`

```python
#!/usr/bin/env python3
"""Fix instrument sectors on remote server"""
import sqlite3

DB_PATH = '/home/raysudo/riley-cycles/db/riley.sqlite'

# Proper sector mappings
instruments = [
    # FUTURES
    ("ES", "INDICES"), ("NQ", "INDICES"), ("RTY", "INDICES"),
    ("CL", "ENERGY"), ("NG", "ENERGY"),
    ("GC", "METALS"), ("SI", "METALS"), ("PL", "METALS"), ("HG", "METALS"),
    ("ZC", "AGRICULTURE"), ("ZS", "AGRICULTURE"), ("ZW", "AGRICULTURE"),
    ("ZB", "FIXED_INCOME"),

    # FX
    ("DXY", "CURRENCIES"), ("EURUSD", "CURRENCIES"), ("GBPUSD", "CURRENCIES"),
    ("USDJPY", "CURRENCIES"), ("AUDUSD", "CURRENCIES"),

    # CRYPTO
    ("BTC", "DIGITAL_ASSETS"),

    # EQUITY - Technology
    ("AAPL", "TECHNOLOGY"), ("GOOGL", "TECHNOLOGY"), ("MSFT", "TECHNOLOGY"),
    ("META", "TECHNOLOGY"), ("NVDA", "TECHNOLOGY"), ("CRM", "TECHNOLOGY"),
    ("ORCL", "TECHNOLOGY"), ("AVGO", "TECHNOLOGY"), ("AMD", "TECHNOLOGY"),
    ("AMAT", "TECHNOLOGY"), ("MU", "TECHNOLOGY"), ("TMUS", "TECHNOLOGY"),
    ("NFLX", "TECHNOLOGY"), ("BIDU", "TECHNOLOGY"), ("BABA", "TECHNOLOGY"),

    # EQUITY - Financials
    ("JPM", "FINANCIALS"), ("GS", "FINANCIALS"), ("MS", "FINANCIALS"),
    ("V", "FINANCIALS"), ("PYPL", "FINANCIALS"),

    # EQUITY - Consumer Discretionary
    ("AMZN", "CONSUMER_DISCRETIONARY"), ("DIS", "CONSUMER_DISCRETIONARY"),
    ("SBUX", "CONSUMER_DISCRETIONARY"), ("MCD", "CONSUMER_DISCRETIONARY"),
    ("NKE", "CONSUMER_DISCRETIONARY"), ("TSLA", "CONSUMER_DISCRETIONARY"),
    ("HD", "CONSUMER_DISCRETIONARY"), ("TOL", "CONSUMER_DISCRETIONARY"),
    ("LVS", "CONSUMER_DISCRETIONARY"), ("WYNN", "CONSUMER_DISCRETIONARY"),
    ("UBER", "CONSUMER_DISCRETIONARY"), ("UAL", "CONSUMER_DISCRETIONARY"),
    ("LUV", "CONSUMER_DISCRETIONARY"),

    # EQUITY - Consumer Staples
    ("WMT", "CONSUMER_STAPLES"), ("COST", "CONSUMER_STAPLES"), ("PEP", "CONSUMER_STAPLES"),

    # EQUITY - Energy
    ("XOM", "ENERGY"), ("CVX", "ENERGY"), ("FCX", "ENERGY"), ("FSLR", "ENERGY"),

    # EQUITY - Industrials
    ("CAT", "INDUSTRIALS"), ("BA", "INDUSTRIALS"), ("DE", "INDUSTRIALS"), ("FDX", "INDUSTRIALS"),

    # EQUITY - Materials
    ("NEM", "MATERIALS"), ("PAAS", "MATERIALS"),

    # EQUITY - Healthcare
    ("AMGN", "HEALTHCARE"),

    # ETF
    ("XLE", "ENERGY"), ("XLF", "FINANCIALS"), ("XLI", "INDUSTRIALS"),
    ("XLK", "TECHNOLOGY"), ("XLP", "CONSUMER_STAPLES"), ("SMH", "TECHNOLOGY"),
    ("XBI", "HEALTHCARE"), ("XRT", "CONSUMER_DISCRETIONARY"),
    ("EEM", "INTERNATIONAL"), ("FEZ", "INTERNATIONAL"), ("FXI", "INTERNATIONAL"),
    ("GDX", "METALS"),
]

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

updated = 0
for symbol, sector in instruments:
    cursor.execute("UPDATE instruments SET sector = ? WHERE symbol = ?", (sector, symbol))
    if cursor.rowcount > 0:
        updated += 1

conn.commit()
conn.close()

print(f"✅ Updated {updated} instruments with proper sectors")
```

Run it:
```bash
python3 fix_instruments_sectors.py
```

---

## Step 3: Update db.py to Enable Filters

Edit file: `/home/raysudo/riley-cycles/app/db.py`

Find around **line 222** (in `get_today_rows()` method):
```python
# Note: group_name column doesn't exist in current schema
# if filters.get('group_name'):
#     query += " AND i.group_name = ?"
#     params.append(filters['group_name'])

# Note: sector column doesn't exist in current schema
# if filters.get('sector'):
#     query += " AND i.sector = ?"
#     params.append(filters['sector'])
```

**Replace with:**
```python
if filters.get('group_name'):
    query += " AND i.group_name = ?"
    params.append(filters['group_name'])

if filters.get('sector'):
    query += " AND i.sector = ?"
    params.append(filters['sector'])
```

Find around **line 408** (in `get_instruments()` method):
```python
# Note: group_name, sector, and other taxonomy columns don't exist in current schema
# if filters.get('group_name'):
#     query += " AND group_name = ?"
#     params.append(filters['group_name'])

# if filters.get('sector'):
#     query += " AND sector = ?"
#     params.append(filters['sector'])
```

**Replace with:**
```python
if filters.get('group_name'):
    query += " AND group_name = ?"
    params.append(filters['group_name'])

if filters.get('sector'):
    query += " AND sector = ?"
    params.append(filters['sector'])
```

**OR** just copy the fixed file from local:
```bash
# From your local machine:
scp /Users/bernie/Documents/AI/Riley\ Project/app/db.py raysudo@45.76.168.214:/home/raysudo/riley-cycles/app/db.py
```

---

## Step 4: Migrate Charts to Categorized Folders

Create file: `/home/raysudo/riley-cycles/migrate_charts.py`

```python
#!/usr/bin/env python3
"""Migrate charts to categorized folders on remote"""
import sys
from pathlib import Path
from datetime import datetime
import re

sys.path.insert(0, '/home/raysudo/riley-cycles/src')
from riley.database import Database

MEDIA_PATH = Path('/home/raysudo/riley-cycles/media')

def migrate():
    db = Database()
    moved = 0
    tracked = 0

    pattern = re.compile(r'^(weekly|daily)_(\d{8})\.png$')

    for symbol_dir in sorted(MEDIA_PATH.iterdir()):
        if not symbol_dir.is_dir() or symbol_dir.name.startswith('.'):
            continue

        symbol = symbol_dir.name
        askslim_dir = symbol_dir / "askslim"

        for chart_file in symbol_dir.glob("*.png"):
            if pattern.match(chart_file.name):
                askslim_dir.mkdir(exist_ok=True)
                new_path = askslim_dir / chart_file.name

                chart_file.rename(new_path)
                moved += 1
                print(f"  Moved: {symbol}/{chart_file.name}")

                match = re.match(r'(weekly|daily)_(\d{8})\.png', chart_file.name)
                if match:
                    timeframe = match.group(1).upper()
                    date_str = match.group(2)
                    upload_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"

                    try:
                        db.insert_media_file(
                            instrument_symbol=symbol,
                            category='askslim',
                            timeframe=timeframe,
                            file_path=str(new_path),
                            file_name=chart_file.name,
                            upload_date=upload_date,
                            source='scraper'
                        )
                        tracked += 1
                    except Exception as e:
                        print(f"  ⚠ Failed: {e}")

    db.close()
    print(f"\n✅ Moved: {moved}, Tracked: {tracked}")

if __name__ == "__main__":
    migrate()
```

Run it:
```bash
python3 migrate_charts.py
```

---

## Step 5: Restart Streamlit Service

```bash
sudo systemctl restart riley-cycles-streamlit
sudo systemctl status riley-cycles-streamlit
```

---

## Step 6: Verify

1. Reload web page: https://cycles.cosmicalsignals.net
2. Check that sectors are no longer "UNCLASSIFIED"
3. Check that Group/Sector filters work
4. Click through instruments and verify charts are displaying
5. Check that chart tabs show counts (e.g., "📊 AskSlim (2)")

---

## Quick Copy-Paste Version

If you just want to copy-paste commands:

```bash
# SSH into server
ssh raysudo@45.76.168.214

# Copy fixed db.py from local (run this from your Mac)
scp /Users/bernie/Documents/AI/Riley\ Project/app/db.py raysudo@45.76.168.214:/home/raysudo/riley-cycles/app/db.py

# Then on remote server, create and run the fix scripts:
cd /home/raysudo/riley-cycles

# Download fix_instruments_sectors.py (you'll need to create this file)
# Download migrate_charts.py (you'll need to create this file)

python3 fix_instruments_sectors.py
python3 migrate_charts.py

# Restart service
sudo systemctl restart riley-cycles-streamlit
```

---

## Summary of What Needs Fixing on Remote

1. **Instruments:** All have sector = "UNCLASSIFIED", need to be updated to proper sectors
2. **Charts:** Not migrated to categorized folders, not tracked in database
3. **Filters:** db.py has filter code commented out, needs to be uncommented
4. **Service:** Needs restart after changes

All of these issues are already fixed on the LOCAL server. You just need to replicate the fixes to REMOTE.
