# Quick Start - Calendar View

## Access the Calendar

The app is **already running** at: **http://localhost:8501**

1. Open browser → http://localhost:8501
2. Look at the **sidebar** on the left
3. Click **"Calendar"** page

## What You'll See

**Two Month Grids:**
- December 2025 (current month)
- January 2026 (next month)

**Multi-Day Bars Spanning Across Days:**
- 🔵 Light blue bars = DAILY cycle windows
- 🟣 Light purple bars = WEEKLY cycle windows  
- 🟡 Amber bars = OVERLAP (where DAILY + WEEKLY intersect)

**Dots on Specific Dates:**
- 🔴 Red dots = PRIMARY astro events
- 🔵 Teal dots = BACKUP astro events

## Filters (Sidebar)

**Symbols Multiselect:**
- Default: First 5 symbols selected
- Click to add/remove symbols
- Choose which instruments to display

**Display Toggles:**
- ☑ Show DAILY Windows
- ☑ Show WEEKLY Windows
- ☑ Show OVERLAP
- ☑ Show Astro Events

Turn off any type you don't want to see.

## Sample View

For **ES** (default selected):
- DAILY window: Jan 12-20, 2026 (light blue bar spanning 9 days)
- WEEKLY window: Dec 19, 2025 - Jan 30, 2026 (light purple bar spanning 43 days)
- OVERLAP: Jan 12-20, 2026 (amber bar - where both windows active)
- 5 astro events (red/teal dots on specific dates)

## Legend

Full legend in sidebar shows:
- Color coding for each window type
- Symbol meanings for astro events

## Data Source

All data read from `db/riley.sqlite`:
- Cycle windows from `cycle_projections.core_start_label`, `core_end_label`
- Astro events from `astro_events.event_label`

**100% READ-ONLY** - No database modifications.

## Troubleshooting

**Calendar not showing?**
- Check sidebar filters - ensure at least one symbol selected
- Ensure at least one display toggle is ON

**App not accessible?**
- Run: `streamlit run app/Home.py`
- Wait for "You can now view your Streamlit app in your browser"
- Navigate to http://localhost:8501

**Want to restart?**
- Ctrl+C in terminal where Streamlit is running
- Run: `streamlit run app/Home.py`

## Example Workflow

1. Open http://localhost:8501
2. Sidebar → Click "Calendar"
3. Select symbols: ES, PL, GC (or any you want)
4. Look at December 2025 grid
5. See multi-day bars spanning across days
6. Scroll down to January 2026 grid
7. Notice overlap bars (amber) where DAILY + WEEKLY intersect
8. Toggle filters to isolate specific window types

---

**That's it!** The calendar view is ready to use.
