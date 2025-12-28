# Riley Cycles Calendar View

**Last Updated:** 28-Dec-2025
**Feature Status:** Active
**Location:** Home.py → CALENDAR view

---

## Overview

Apple Calendar-style 2-month view showing cycle windows as multi-day spanning bars. This is the CALENDAR view accessible from the main Streamlit navigation.

---

## Quick Start

### Access the Calendar

1. **Open browser** → http://localhost:8501 (or cycles.cosmicsignals.net)
2. **Look at sidebar** on the left
3. **Click "CALENDAR"** in the navigation radio buttons

### What You'll See

**Two Month Grids:**
- Current month
- Next month

**Multi-Day Bars Spanning Across Days:**
- 🔵 Light blue bars = DAILY cycle windows
- 🟣 Light purple bars = WEEKLY cycle windows
- 🟡 Amber bars = OVERLAP (where DAILY + WEEKLY intersect)

**Dots on Specific Dates:**
- 🔴 Red dots = PRIMARY astro events
- 🔵 Teal dots = BACKUP astro events

---

## Features

### Window Types
- **DAILY** - Light blue bars (trading day calendar)
- **WEEKLY** - Light purple bars (trading week calendar)
- **OVERLAP** - Amber bars (where DAILY + WEEKLY windows intersect)

### Astro Events
- **PRIMARY** - Red dots on specific dates
- **BACKUP** - Teal dots on specific dates

### Filtering Options

**Symbols Multiselect:**
- Select which instruments to display
- Default: All symbols available
- Click to add/remove symbols

**Display Toggles:**
- ☑ Show DAILY Windows
- ☑ Show WEEKLY Windows
- ☑ Show OVERLAP
- ☑ Show Astro Events

Turn off any type you don't want to see.

---

## Example View

For **ES** (when selected):
- **DAILY window:** Multi-day light blue bar spanning cycle window
- **WEEKLY window:** Multi-day light purple bar spanning cycle window
- **OVERLAP:** Amber bar where both windows are active
- **Astro events:** Red/teal dots on specific dates

---

## Data Source

All data read from `db/riley.sqlite`:
- **Cycle windows:** From `cycle_projections` table
  - Uses `core_start_label` and `core_end_label` columns
- **Astro events:** From `astro_events` table
  - Uses `event_label` column

**Important:** This view is **100% READ-ONLY** - No database modifications.

---

## Implementation

### Service Layer
**File:** `src/riley/calendar_events.py`

**Functions:**
- `build_fullcalendar_events()` - Main builder
- `get_cycle_events()` - Extract cycle windows
- `get_astro_events()` - Extract astro dates
- `get_available_symbols()` - Get symbol list

### UI Layer
**File:** `app/Home.py` (render_calendar_view function)

**Renderer:** Uses `streamlit-calendar` package
- Primary: streamlit-calendar component
- Fallback: Custom HTML with FullCalendar CDN if package unavailable

### Dependencies
Added to `requirements.txt`:
- `streamlit-calendar>=0.6.0`
- `python-dateutil>=2.8.0`

---

## Architecture

```
User selects filters (symbols, display options)
    ↓
build_fullcalendar_events(db_path, symbols, filters)
    ↓
get_cycle_events() + get_astro_events()
    ↓
Read from cycle_projections.{core_start_label, core_end_label}
Read from astro_events.{event_label}
    ↓
Format as FullCalendar JSON events
    ↓
Render 2 calendars:
  - Current month grid
  - Next month grid
```

---

## Overlap Computation

**Important:** The overlap computation does NOT re-calculate windows.

**How it works:**
1. Reads DAILY and WEEKLY window dates from database
2. Compares the stored date ranges
3. If both windows overlap, creates OVERLAP event
4. OVERLAP event spans only the intersection days

**Never modifies:** Database windows remain unchanged

---

## Event Format (FullCalendar JSON)

### Cycle Window Event
```json
{
  "title": "ES • DAILY",
  "start": "2025-12-25",
  "end": "2026-01-01",
  "allDay": true,
  "color": "#E3F2FD",
  "display": "block",
  "extendedProps": {
    "symbol": "ES",
    "timeframe": "DAILY",
    "median": "2025-12-28",
    "kind": "cycle_window"
  }
}
```

### Astro Event
```json
{
  "title": "🔴 New Moon",
  "start": "2025-12-30",
  "allDay": true,
  "color": "#F44336",
  "display": "list-item",
  "extendedProps": {
    "role": "PRIMARY",
    "kind": "astro"
  }
}
```

**Note:** `end` is **exclusive** for FullCalendar all-day events, so we add 1 day to the inclusive end_label.

---

## Color Coding

### Cycle Windows
- **DAILY:** Light blue (`#E3F2FD`)
- **WEEKLY:** Light purple (`#F3E5F5`)
- **OVERLAP:** Amber (`#FFF9C4`)

### Astro Events
- **PRIMARY:** Red (`#F44336`)
- **BACKUP:** Teal (`#00BCD4`)

---

## Legend

Full legend displayed in sidebar shows:
- Color coding for each window type
- Symbol meanings for astro events
- Examples for each instrument

---

## Troubleshooting

### Calendar not showing?
**Check:**
1. Sidebar filters - Ensure at least one symbol selected
2. Display toggles - Ensure at least one toggle is ON
3. Database has cycle data - Run cycle scanner if empty

### App not accessible?
**Solution:**
```bash
# Start Streamlit
streamlit run app/Home.py

# Wait for message:
# "You can now view your Streamlit app in your browser"

# Navigate to:
http://localhost:8501
```

### Want to restart?
**Solution:**
```bash
# Press Ctrl+C in terminal where Streamlit is running
# Then restart:
streamlit run app/Home.py
```

### Events not showing for specific symbol?
**Check:**
1. Symbol has cycle specs configured (DATABASE view)
2. Cycle scanner has run (System Status page)
3. Symbol is selected in filters

---

## Example Workflow

1. Open http://localhost:8501
2. Sidebar → Click **"CALENDAR"** radio button
3. Filters → Select symbols: ES, PL, GC (or any you want)
4. View current month grid:
   - See multi-day bars spanning across days
   - Each bar represents a cycle window
5. Scroll to next month grid:
   - Notice continuation of cycle windows
   - See overlap bars (amber) where DAILY + WEEKLY intersect
6. Toggle filters to isolate specific window types:
   - Turn off DAILY to see only WEEKLY
   - Turn off OVERLAP to see windows separately
7. Add/remove symbols to focus analysis

---

## Future Enhancements

Potential future features:
- Click event to show sidebar with symbol details + desk notes
- Export calendar to ICS format
- Sync with external calendar applications
- Mobile responsive view
- Historical calendar (past months)
- Print-friendly view

---

## Technical Notes

### Why Multi-Day Bars?
Traditional calendar apps show events as per-day badges. This makes it hard to see multi-day windows at a glance.

**Solution:** FullCalendar's "block" display mode renders events as spanning bars across multiple days, similar to Apple Calendar.

### Why Two Separate Calendars?
Rather than a single scrollable calendar, we show two fixed months. This provides:
- Clear visual boundary between months
- No scrolling needed for 2-month outlook
- Easier to compare current vs next month

### Performance Considerations
- Events are pre-computed at render time
- No real-time updates (user must refresh page)
- All data read from database (no API calls)
- Lightweight rendering (hundreds of events load instantly)

---

**End of Calendar View Documentation**
