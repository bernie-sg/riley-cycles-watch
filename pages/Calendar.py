"""
Calendar View - 2-Month Cycle Windows Visualization

Apple Calendar-style grid showing DAILY/WEEKLY cycle windows as multi-day bars.
"""

import streamlit as st
from pathlib import Path
import sys
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import json

# Add parent directory to path (project root)
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.riley.calendar_events import (
    build_fullcalendar_events,
    get_available_symbols
)


# Page config (must be first Streamlit command)
st.set_page_config(
    page_title="Cycle Calendar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

DB_PATH = Path(__file__).parent.parent / "db" / "riley.sqlite"


def render_with_streamlit_calendar(events, initial_date):
    """Render calendar using streamlit-calendar package"""
    try:
        from streamlit_calendar import calendar as st_calendar

        calendar_options = {
            "initialView": "dayGridMonth",
            "initialDate": initial_date,
            "headerToolbar": {
                "left": "title",
                "center": "",
                "right": ""
            },
            "height": 600,
            "eventDisplay": "block",
            "displayEventTime": False,
        }

        custom_css = """
            .fc-event {
                border: none !important;
                font-size: 0.85em;
            }
            .overlap-event {
                z-index: 10 !important;
                font-weight: bold;
            }
            .astro-primary {
                font-size: 1.2em;
            }
            .astro-backup {
                font-size: 1em;
                opacity: 0.8;
            }
        """

        result = st_calendar(
            events=events,
            options=calendar_options,
            custom_css=custom_css
        )

        return result

    except ImportError:
        return None


def render_with_custom_html(events, initial_date, container_id):
    """Fallback: render using custom FullCalendar HTML"""

    events_json = json.dumps(events)

    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <link href='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.css' rel='stylesheet' />
        <script src='https://cdn.jsdelivr.net/npm/fullcalendar@6.1.10/index.global.min.js'></script>
        <style>
            #calendar-{container_id} {{
                max-width: 100%;
                margin: 0 auto;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            }}
            .fc-event {{
                border: none !important;
                font-size: 0.85em;
            }}
            .overlap-event {{
                z-index: 10 !important;
                font-weight: bold;
            }}
            .astro-primary {{
                font-size: 1.2em;
            }}
            .astro-backup {{
                font-size: 1em;
                opacity: 0.8;
            }}
        </style>
    </head>
    <body>
        <div id='calendar-{container_id}'></div>
        <script>
            document.addEventListener('DOMContentLoaded', function() {{
                var calendarEl = document.getElementById('calendar-{container_id}');
                var calendar = new FullCalendar.Calendar(calendarEl, {{
                    initialView: 'dayGridMonth',
                    initialDate: '{initial_date}',
                    headerToolbar: {{
                        left: 'title',
                        center: '',
                        right: ''
                    }},
                    height: 600,
                    events: {events_json},
                    displayEventTime: false,
                    eventDisplay: 'block'
                }});
                calendar.render();
            }});
        </script>
    </body>
    </html>
    """

    st.components.v1.html(html_code, height=650)


def main():
    st.title("📅 Cycle Calendar")
    st.markdown("**2-Month View** • Apple Calendar-style visualization of cycle windows")

    # Get available symbols
    try:
        all_symbols = get_available_symbols(str(DB_PATH))
    except Exception as e:
        st.error(f"Failed to load symbols: {e}")
        return

    # Sidebar controls
    st.sidebar.header("Filters")

    # Symbol multiselect
    selected_symbols = st.sidebar.multiselect(
        "Symbols",
        options=all_symbols,
        default=all_symbols[:5] if len(all_symbols) > 5 else all_symbols,
        help="Select symbols to display"
    )

    # Toggles
    st.sidebar.subheader("Display Options")
    show_daily = st.sidebar.checkbox("Show DAILY Windows", value=True)
    show_weekly = st.sidebar.checkbox("Show WEEKLY Windows", value=True)
    show_overlap = st.sidebar.checkbox("Show OVERLAP", value=True)
    show_astro = st.sidebar.checkbox("Show Astro Events", value=True)

    # Legend
    st.sidebar.markdown("---")
    st.sidebar.subheader("Legend")
    st.sidebar.markdown("""
    **Cycle Windows:**
    - 🔵 **DAILY** - Light blue bars
    - 🟣 **WEEKLY** - Light purple bars
    - 🟡 **OVERLAP** - Amber bars (both active)

    **Astro Events:**
    - 🔴 **PRIMARY** - Red dots
    - 🔵 **BACKUP** - Teal dots
    """)

    # Build events
    try:
        events = build_fullcalendar_events(
            db_path=str(DB_PATH),
            symbols=selected_symbols if selected_symbols else None,
            include_daily=show_daily,
            include_weekly=show_weekly,
            include_overlap=show_overlap,
            include_astro=show_astro
        )
    except Exception as e:
        st.error(f"Failed to build events: {e}")
        return

    if not events:
        st.warning("No events to display. Adjust filters or check database.")
        return

    # Calculate current month and next month
    today = datetime.now()
    current_month_start = today.replace(day=1).strftime('%Y-%m-%d')
    next_month_start = (today.replace(day=1) + relativedelta(months=1)).strftime('%Y-%m-%d')

    # Display info
    st.info(f"📊 Displaying **{len(events)}** events for **{len(selected_symbols)}** symbols")

    # Try streamlit-calendar first, fallback to custom HTML
    use_fallback = False

    # Current Month
    st.subheader(f"📅 {today.strftime('%B %Y')}")
    result = render_with_streamlit_calendar(events, current_month_start)

    if result is None:
        use_fallback = True
        render_with_custom_html(events, current_month_start, "current")

    st.markdown("---")

    # Next Month
    next_month_date = today.replace(day=1) + relativedelta(months=1)
    st.subheader(f"📅 {next_month_date.strftime('%B %Y')}")

    if use_fallback:
        render_with_custom_html(events, next_month_start, "next")
    else:
        render_with_streamlit_calendar(events, next_month_start)

    # Footer
    st.markdown("---")
    st.caption("💡 Click on events to see details (interactive mode coming soon)")

    if use_fallback:
        st.caption("⚠️ Using fallback calendar renderer. Install `streamlit-calendar` for enhanced features.")


if __name__ == "__main__":
    main()
