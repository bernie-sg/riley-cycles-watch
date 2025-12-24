#!/usr/bin/env python3
"""
Verify database consistency across modules.

Confirms that all modules use the same DB path and show same data.
"""

import sys
from pathlib import Path

# Add parent to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "app"))

from config import get_db_path, get_db_info
from db import CyclesDB

print("=" * 80)
print("RILEY DATABASE CONSISTENCY VERIFICATION")
print("=" * 80)
print()

# 1. Check DB path from config
db_path_config = get_db_path()
print(f"1. DB Path from config.get_db_path():")
print(f"   {db_path_config}")
print()

# 2. Check DB path from CyclesDB
db = CyclesDB()
print(f"2. DB Path from CyclesDB():")
print(f"   {db.db_path}")
print()

# 3. Verify they match
if str(db_path_config) == str(db.db_path):
    print("✅ PASS: Both modules use the SAME database file")
else:
    print("❌ FAIL: Database paths DO NOT MATCH!")
    print(f"   config.py:  {db_path_config}")
    print(f"   CyclesDB(): {db.db_path}")
print()

# 4. Get DB info diagnostics
info = get_db_info()
print("3. Database Diagnostics:")
print(f"   Exists: {info['exists']}")
print(f"   Modified: {info.get('modified', 'N/A')}")
print(f"   Latest Scan: {info.get('latest_scan', 'N/A')}")
print(f"   Total Instruments: {info.get('instrument_count', 'N/A')}")
print(f"   ES Notes Count: {info.get('es_notes_count', 'N/A')}")
print(f"   ES Latest Note Date: {info.get('es_latest_note', 'N/A')}")
print()

# 5. Check ES notes in detail
print("4. ES Desk Notes Detail:")
import sqlite3
conn = sqlite3.connect(str(db_path_config))
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

cursor.execute("SELECT instrument_id FROM instruments WHERE symbol='ES' AND role='CANONICAL'")
row = cursor.fetchone()
if row:
    es_id = row['instrument_id']
    cursor.execute("""
        SELECT asof_td_label, note_type, timeframe_scope, price_reference,
               substr(notes, 1, 50) as note_preview
        FROM desk_notes
        WHERE instrument_id = ?
        ORDER BY asof_td_label DESC
    """, (es_id,))

    notes = cursor.fetchall()
    if notes:
        for note in notes:
            print(f"   Date: {note['asof_td_label']}")
            print(f"   Type: {note['note_type'] or '—'}")
            print(f"   Scope: {note['timeframe_scope'] or '—'}")
            print(f"   Ref: {note['price_reference'] or '—'}")
            print(f"   Preview: {note['note_preview']}")
            print()
    else:
        print("   No notes found for ES")
else:
    print("   ES instrument not found")

conn.close()

print("=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print()
print("Expected results:")
print("  ✅ Both DB paths match")
print("  ✅ ES Notes Count = 1")
print("  ✅ ES Latest Note = 2025-12-19")
print("  ✅ NULL fields show as '—' not '(None)'")
print()
