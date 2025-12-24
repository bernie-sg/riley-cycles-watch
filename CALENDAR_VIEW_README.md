# Riley Cycles Calendar View

## Overview

Apple Calendar-style 2-month view showing cycle windows as multi-day spanning bars.

## Features

- **2-Month Grid**: Current month + next month displayed simultaneously
- **Multi-Day Bars**: Cycle windows span across days (not per-day badges)
- **Window Types**:
  - 🔵 **DAILY** - Light blue bars (trading day calendar)
  - 🟣 **WEEKLY** - Light purple bars (trading week calendar)
  - 🟡 **OVERLAP** - Amber bars (where DAILY + WEEKLY intersect)
- **Astro Events**: Dots on specific dates
  - 🔴 **PRIMARY** - Red dots
  - 🔵 **BACKUP** - Teal dots
- **Filtering**: Multi-select symbols, toggle window types

## Running the App

```bash
# From project root
streamlit run app/Home.py
```

Then navigate to "Calendar" in the sidebar.

## Data Source

All data read from `db/riley.sqlite`:
- `cycle_projections` table (label columns: core_start_label, core_end_label)
- `astro_events` table (event_label)

**Read-only**: This view does NOT modify the database.

## Implementation

- **Service**: `src/riley/calendar_events.py` - Query DB and build FullCalendar events
- **UI**: `pages/Calendar.py` - Streamlit multipage app
- **Renderer**: Uses `streamlit-calendar` package (fallback to custom HTML if unavailable)

## Dependencies

Added to `requirements.txt`:
- `streamlit-calendar>=0.6.0`
- `python-dateutil>=2.8.0`

## Architecture

```
User selects filters
    ↓
build_fullcalendar_events()
    ↓
get_cycle_events() + get_astro_events()
    ↓
Read from cycle_projections.{core_start_label, core_end_label}
    ↓
Format as FullCalendar JSON
    ↓
Render 2 calendars (current month + next month)
```

## Overlap Computation

- **NOT** re-computing windows in UI
- **IS** comparing already-stored window dates from DB
- If a symbol has both DAILY and WEEKLY windows that intersect, create OVERLAP event spanning only the intersection days

## Event Format (FullCalendar)

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

Note: `end` is **exclusive** for FullCalendar all-day events, so we add 1 day to the inclusive end_label.

## Future Enhancements

- Click event to show sidebar with symbol details + desk notes
- Export calendar to ICS
- Sync with external calendars
- Mobile responsive view

