# askSlim Data Structure - Futures Hub

**Source:** https://askslim.com/futures-hub/
**Section:** Technical Details
**Discovered:** 2025-12-25

---

## Data Location

```
Futures Hub
  └── SPX (instrument)
      └── Technical Details
          ├── Cycle Low Dates
          │   ├── Weekly: 01/04/26
          │   └── Daily: 12/28/25
          └── Cycle Counts
              ├── Weekly Dominant Cycle: 37 Bars
              └── Daily Dominant Cycle: 26 Bars
```

---

## Data Format

### Cycle Low Dates
- **Format:** MM/DD/YY
- **Examples:**
  - Weekly: `01/04/26` → 2026-01-04
  - Daily: `12/28/25` → 2025-12-28

### Cycle Counts
- **Format:** "{Timeframe} Dominant Cycle {N} Bars"
- **Examples:**
  - Weekly: `37 Bars` → 37
  - Daily: `26 Bars` → 26

---

## Instrument Mapping

askSlim uses **SPX** (S&P 500 Index) in Futures Hub.

Riley uses **ES** (E-mini S&P 500 Futures) as canonical symbol.

**Mapping:**
- askSlim "SPX" → Riley "ES" (canonical)
- Both represent the same S&P 500 cycle analysis
- ES is the futures contract, SPX is the index

---

## Riley Database Schema

Data maps to `cycle_specs` table:

| askSlim Field | Riley Field | Example Value |
|--------------|-------------|---------------|
| Weekly Date | `median_input_date_label` (timeframe=W) | "2026-01-04" |
| Daily Date | `median_input_date_label` (timeframe=D) | "2025-12-28" |
| Weekly Bars | `cycle_length` (timeframe=W) | 37 |
| Daily Bars | `cycle_length` (timeframe=D) | 26 |
| - | `source` | "askSlim" |
| - | `canonical_symbol` | "ES" |

---

## Expected Data Fields

For each instrument in Futures Hub, extract:

1. **Instrument Name** (e.g., "SPX")
2. **Cycle Low Dates:**
   - Weekly date (MM/DD/YY)
   - Daily date (MM/DD/YY)
3. **Cycle Counts:**
   - Weekly Dominant Cycle (N bars)
   - Daily Dominant Cycle (N bars)

---

## Other Instruments

Futures Hub likely contains other instruments:
- NQ (Nasdaq)
- ES/SPX (S&P 500)
- Gold/GC
- Crude Oil/CL
- Bonds/ZB
- Currencies (EUR, JPY, etc.)
- Grains (ZC, ZS, ZW)
- Metals (SI, HG, PL)

Each should have the same "Technical Details" structure.

---

## Parsing Requirements

### Date Parsing
```python
# Input: "01/04/26"
# Output: "2026-01-04"

def parse_askslim_date(date_str: str) -> str:
    """
    Parse askSlim date format MM/DD/YY to YYYY-MM-DD.
    Assumes 20xx for years.
    """
    from datetime import datetime
    # Parse MM/DD/YY
    dt = datetime.strptime(date_str, "%m/%d/%y")
    # Return ISO format
    return dt.strftime("%Y-%m-%d")
```

### Cycle Count Parsing
```python
# Input: "37 Bars"
# Output: 37

def parse_cycle_bars(bars_str: str) -> int:
    """
    Parse cycle count from "N Bars" format.
    """
    # Extract number from "37 Bars"
    return int(bars_str.split()[0])
```

---

## Scraping Strategy

### Phase 2 Implementation Plan

1. **Navigate to Futures Hub:**
   ```python
   page.goto("https://askslim.com/futures-hub/")
   ```

2. **Find Instruments:**
   - Locate all instrument sections/cards
   - Extract instrument names

3. **For Each Instrument:**
   - Click into "Technical Details" or find the section
   - Locate "Cycle Low Dates"
   - Locate "Cycle Counts"
   - Extract all four values

4. **Parse Data:**
   - Convert dates from MM/DD/YY to YYYY-MM-DD
   - Extract integer cycle lengths from "N Bars"

5. **Map to Riley Symbols:**
   ```python
   SYMBOL_MAP = {
       "SPX": "ES",
       "NQ": "NQ",
       "Gold": "GC",
       "Crude": "CL",
       # ... etc
   }
   ```

6. **Update Database:**
   - For each timeframe (D, W):
     - Call `riley.database` or use existing scripts
     - Update `cycle_specs` table
     - Set source="askSlim"
     - Increment version_num

---

## Example Extracted Data

```json
{
  "instrument": "SPX",
  "riley_symbol": "ES",
  "cycle_low_dates": {
    "weekly": "2026-01-04",
    "daily": "2025-12-28"
  },
  "cycle_counts": {
    "weekly": 37,
    "daily": 26
  },
  "scraped_at": "2025-12-25T10:30:00Z",
  "source": "askSlim"
}
```

---

## DOM Selectors (To Be Discovered)

Need to identify:
- Futures Hub instrument list selector
- Technical Details section selector
- "Cycle Low Dates" label/values
- "Cycle Counts" label/values

**Next Step:** Use browser DevTools or Playwright inspector to find exact CSS selectors for these elements.

---

## Validation

After scraping, verify:
1. ✅ Dates are in valid YYYY-MM-DD format
2. ✅ Dates are reasonable (not in distant past/future)
3. ✅ Cycle lengths are positive integers
4. ✅ Cycle lengths are reasonable (e.g., 10-100 bars)
5. ✅ Instrument names map to known Riley symbols
6. ✅ Both daily and weekly data present

---

**Status:** Data structure documented, ready for Phase 2 implementation.
