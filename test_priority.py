import sys
sys.path.insert(0, 'app')
from db import CyclesDB

db = CyclesDB()
df = db.get_today_rows('2026-01-02', {})
priority = df[(df['daily_status'] != 'NONE') | (df['weekly_status'] != 'NONE')]
print(f'Priority count: {len(priority)}')
for idx, row in priority.iterrows():
    print(f"  {row['symbol']}: D={row['daily_status']}, W={row['weekly_status']}")
