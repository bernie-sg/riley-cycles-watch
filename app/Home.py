"""Riley Cycles Watch - Streamlit Dashboard"""
import streamlit as st
import pandas as pd
from pathlib import Path
import sys
import json
from datetime import datetime
from typing import Any
import subprocess

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# Import from local db module
from db import CyclesDB
from config import get_db_path, get_db_info


# Page config
st.set_page_config(
    page_title="Riley Cycles Watch",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database (NO CACHING)
def get_db():
    return CyclesDB()

db = get_db()


def format_status(status: str) -> str:
    """Format status with color indicator"""
    if status == 'ACTIVATED' or status == 'IN_WINDOW':
        return '🔴 ACTIVATED'
    elif status == 'PREWINDOW':
        return '🟡 PREWINDOW'
    elif status == 'APPROACHING':
        return '🟢 APPROACHING'
    elif status == 'NONE':
        return '⚪ NONE'
    else:
        return f'⚪ {status}'


def format_date(date_str: str) -> str:
    """Format date from YYYY-MM-DD to DD MMM YYYY"""
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        return dt.strftime('%d %b %Y')
    except:
        return date_str


def format_null(value: Any, default: str = "—") -> str:
    """Format NULL/None values to show default string instead of '(None)'"""
    if value is None or value == '' or str(value).strip() == '':
        return default
    return str(value)


def pill(text: str, bg: str, fg: str = "#0f5132", border: str = "#badbcc"):
    """Render a compact inline status pill"""
    st.markdown(
        f"""
        <div style="
            display: inline-block;
            padding: 6px 10px;
            border-radius: 8px;
            background: {bg};
            color: {fg};
            border: 1px solid {border};
            font-weight: 600;
            font-size: 14px;
            line-height: 1;
            margin: 4px 0 8px 0;
            ">
            {text}
        </div>
        """,
        unsafe_allow_html=True
    )


def fmt(x):
    """Format value, returning '—' for None/NaN"""
    return "—" if x is None or (isinstance(x, float) and pd.isna(x)) else str(x)


def run_daily_scan(asof_date: str):
    """Run the daily scan script"""
    project_root = Path(__file__).parent.parent
    script_path = project_root / "scripts" / "cycles_run_scan.py"

    try:
        result = subprocess.run(
            [sys.executable, str(script_path), "--asof", asof_date],
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Scan timed out after 5 minutes"
    except Exception as e:
        return False, "", str(e)


def render_today_view(scan_date: str, filters: dict, selected_symbol: str = None):
    """Render TODAY view"""
    st.header("TODAY - What's Up Now")
    st.caption(f"Scan Date: {format_date(scan_date)}")

    # Get data (NO CACHING - fresh every render)
    df = db.get_today_rows(scan_date, filters)

    if df.empty:
        st.info("No instruments match the current filters.")
        return

    # FILTER: Keep only PRIORITY instruments (PREWINDOW or ACTIVATED)
    # Priority = any instrument with daily_status OR weekly_status in ('PREWINDOW', 'ACTIVATED')
    # NEVER promote an instrument if BOTH statuses are 'NONE' (even if overlap_flag=1)
    priority_df = df[
        (df['daily_status'].isin(['PREWINDOW', 'ACTIVATED'])) |
        (df['weekly_status'].isin(['PREWINDOW', 'ACTIVATED']))
    ].copy()

    if priority_df.empty:
        st.info("No priority instruments at this time.")
        return

    # IMPORTANCE RANKING + SORTING
    # Create activation and prewindow flags
    priority_df['daily_is_activated'] = (priority_df['daily_status'] == 'ACTIVATED')
    priority_df['weekly_is_activated'] = (priority_df['weekly_status'] == 'ACTIVATED')
    priority_df['daily_is_prewindow'] = (priority_df['daily_status'] == 'PREWINDOW')
    priority_df['weekly_is_prewindow'] = (priority_df['weekly_status'] == 'PREWINDOW')

    # Create bucket flags
    priority_df['bucket_1_both_activated'] = priority_df['daily_is_activated'] & priority_df['weekly_is_activated']
    priority_df['bucket_2_act_pre'] = (
        (priority_df['daily_is_activated'] & priority_df['weekly_is_prewindow']) |
        (priority_df['weekly_is_activated'] & priority_df['daily_is_prewindow'])
    )
    priority_df['bucket_3_single_activated'] = (
        (priority_df['daily_is_activated'] & ~priority_df['weekly_is_activated'] & ~priority_df['weekly_is_prewindow']) |
        (priority_df['weekly_is_activated'] & ~priority_df['daily_is_activated'] & ~priority_df['daily_is_prewindow'])
    )
    priority_df['bucket_4_prewindow_only'] = (
        (priority_df['daily_is_prewindow'] | priority_df['weekly_is_prewindow']) &
        ~priority_df['daily_is_activated'] & ~priority_df['weekly_is_activated']
    )

    # Assign importance rank (higher = more important)
    # Tier 1: Both ACTIVATED
    # Tier 2: One ACTIVATED + other PREWINDOW
    # Tier 3: One ACTIVATED only
    # Tier 4: PREWINDOW only (daily or weekly)
    priority_df['importance_rank'] = 1  # default
    priority_df.loc[priority_df['bucket_4_prewindow_only'], 'importance_rank'] = 1
    priority_df.loc[priority_df['bucket_3_single_activated'], 'importance_rank'] = 2
    priority_df.loc[priority_df['bucket_2_act_pre'], 'importance_rank'] = 3
    priority_df.loc[priority_df['bucket_1_both_activated'], 'importance_rank'] = 4

    # Prepare sort columns (replace NULL with large number for sorting)
    priority_df['days_sort'] = pd.to_numeric(priority_df['days_to_daily_core_start'], errors='coerce').fillna(10**9)
    priority_df['weeks_sort'] = pd.to_numeric(priority_df['weeks_to_weekly_core_start'], errors='coerce').fillna(10**9)

    # Sort by importance
    priority_df = priority_df.sort_values(
        by=['importance_rank', 'overlap_flag', 'days_sort', 'weeks_sort', 'symbol'],
        ascending=[False, False, True, True, True]
    ).reset_index(drop=True)

    # Display table
    st.subheader(f"Top {len(priority_df)} Priority Instruments")

    # Format display dataframe from priority_df
    display_df = priority_df.copy()

    # Cast countdown columns to Int64 for consistent display
    if 'days_to_daily_core_start' in display_df.columns:
        display_df['days_to_daily_core_start'] = pd.to_numeric(display_df['days_to_daily_core_start'], errors='coerce').astype('Int64')
    if 'weeks_to_weekly_core_start' in display_df.columns:
        display_df['weeks_to_weekly_core_start'] = pd.to_numeric(display_df['weeks_to_weekly_core_start'], errors='coerce').astype('Int64')

    display_df['Daily'] = display_df['daily_status'].apply(format_status)
    display_df['Weekly'] = display_df['weekly_status'].apply(format_status)

    # Format countdowns - show "—" for NULL, integers otherwise
    display_df['→D'] = display_df['days_to_daily_core_start'].apply(
        lambda x: f"{x} days" if pd.notna(x) else "—"
    )
    display_df['→W'] = display_df['weeks_to_weekly_core_start'].apply(
        lambda x: f"{x} wks" if pd.notna(x) else "—"
    )
    # Overlap icon - STRICT: only show if overlap_flag=1 AND both ACTIVATED
    def overlap_icon(row):
        if (row.get('overlap_flag') == 1 and
            row.get('daily_status') == 'ACTIVATED' and
            row.get('weekly_status') == 'ACTIVATED'):
            return '⚠️'
        return ''
    display_df['Overlap'] = display_df.apply(overlap_icon, axis=1)

    # Ensure sector column exists
    if 'sector' not in display_df.columns:
        display_df['sector'] = 'UNCLASSIFIED'

    # Ensure directional_bias column exists and format with colors
    if 'directional_bias' not in display_df.columns:
        display_df['directional_bias'] = 'N/A'

    # Format bias column with colored indicators (st.dataframe doesn't support custom cell styling)
    # Map bias values exactly as scraped from askSlim
    def format_bias(bias):
        if bias == 'Bullish':
            return '🟢 Bullish'
        elif bias == 'Bearish':
            return '🔴 Bearish'
        elif bias == 'Neutral':
            return '⚪ Neutral'
        return bias if bias else 'N/A'

    display_df['directional_bias'] = display_df['directional_bias'].apply(format_bias)

    # Show table with row selection (small radio button column on left)
    # Order: symbol, name, Daily, →D, Weekly, →W, Bias, sector, Overlap
    cols_to_show = ['symbol', 'name', 'Daily', '→D', 'Weekly', '→W', 'directional_bias', 'sector', 'Overlap']
    display_df = display_df[cols_to_show]

    event = st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        column_config={
            "directional_bias": st.column_config.TextColumn(
                "Bias",
                help="Directional bias from askSlim (exactly as scraped)"
            )
        }
    )

    # Determine which instrument to show
    # Priority: 1) Sidebar search, 2) Table row selection
    show_symbol = selected_symbol  # From sidebar search

    if not show_symbol and event.selection and event.selection.rows:
        # From table row selection (only if no search selection)
        selected_idx = event.selection.rows[0]
        show_symbol = priority_df.iloc[selected_idx]['symbol']

    # Show instrument details
    if show_symbol:
        st.divider()
        st.subheader(show_symbol)
        render_instrument_detail(show_symbol, scan_date)


def render_instrument_detail(symbol: str, scan_date: str):
    """Render detailed view for an instrument"""
    detail = db.get_instrument_detail(symbol, scan_date)

    col1, col2 = st.columns(2)

    with col1:
        # Directional Bias
        analysis = detail.get('analysis', {})
        if analysis and analysis.get('directional_bias'):
            bias = analysis['directional_bias']
            # Format bias with colored emoji to match table display
            if bias == 'Bullish':
                bias_display = '🟢 Bullish'
            elif bias == 'Bearish':
                bias_display = '🔴 Bearish'
            elif bias == 'Neutral':
                bias_display = '⚪ Neutral'
            else:
                bias_display = bias

            st.markdown(f"### {bias_display}")

            if analysis.get('video_url'):
                st.markdown(f"[📹 Watch Video Analysis]({analysis['video_url']})")

            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

        # Cycle Status (moved under bias)
        st.markdown("### Cycle Status")
        scan_row = detail['scan_row']
        cycle_specs = detail['cycle_specs']

        if scan_row:
            # Show sync status at the top
            if scan_row.get('overlap_flag') == 1:
                pill("✓ IN SYNC", bg="#d1e7dd", fg="#0f5132", border="#badbcc")

            # Build daily status text
            daily_lines = [f"**DAILY:**  \nStatus: {format_status(scan_row.get('daily_status', 'UNKNOWN'))}"]

            # Calculate days remaining if in window
            if scan_row.get('daily_status') == 'IN_WINDOW':
                # Find daily cycle spec to get window end date
                daily_spec = next((s for s in cycle_specs if s['timeframe'] == 'DAILY'), None)
                if daily_spec and daily_spec.get('window_end_date'):
                    from datetime import datetime
                    scan_dt = datetime.strptime(scan_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(daily_spec['window_end_date'], '%Y-%m-%d')
                    days_left = (end_dt - scan_dt).days
                    if days_left >= 0:
                        daily_lines.append(f"Days left in window: {days_left}")
                    else:
                        daily_lines.append("Window closed")
                else:
                    daily_lines.append("In window")
            elif scan_row.get('days_to_daily_core_start') is not None:
                days = int(scan_row['days_to_daily_core_start'])
                if days >= 0:
                    daily_lines.append(f"Days to start: {days}")
                else:
                    daily_lines.append("Started")

            st.markdown("  \n".join(daily_lines))

            # Build weekly status text
            weekly_lines = [f"**WEEKLY:**  \nStatus: {format_status(scan_row.get('weekly_status', 'UNKNOWN'))}"]

            # Calculate weeks remaining if in window
            if scan_row.get('weekly_status') == 'IN_WINDOW':
                weekly_spec = next((s for s in cycle_specs if s['timeframe'] == 'WEEKLY'), None)
                if weekly_spec and weekly_spec.get('window_end_date'):
                    from datetime import datetime
                    scan_dt = datetime.strptime(scan_date, '%Y-%m-%d')
                    end_dt = datetime.strptime(weekly_spec['window_end_date'], '%Y-%m-%d')
                    weeks_left = (end_dt - scan_dt).days // 7
                    if weeks_left >= 0:
                        weekly_lines.append(f"Weeks left in window: {weeks_left}")
                    else:
                        weekly_lines.append("Window closed")
                else:
                    weekly_lines.append("In window")
            elif scan_row.get('weeks_to_weekly_core_start') is not None:
                weeks = int(scan_row['weeks_to_weekly_core_start'])
                if weeks >= 0:
                    weekly_lines.append(f"Weeks to start: {weeks}")
                else:
                    weekly_lines.append("Started")

            st.markdown("  \n".join(weekly_lines))

        # Astro events (moved under Cycle Status)
        st.markdown("### Upcoming Astro Events")
        if detail['astro_events']:
            for event in detail['astro_events'][:5]:
                role_icon = '' if event['role'] == 'PRIMARY' else ''
                st.write(f"{role_icon} **{format_date(event['event_label'])}** - {event.get('name', 'Astro event')} ({event.get('category', 'N/A')})")
        else:
            pill("No upcoming astro events", bg="#e7f1ff", fg="#084298", border="#b6d4fe")

    with col2:
        # Cycles section (moved from left column)
        st.markdown("### Cycles")
        if detail['cycle_specs']:
            # Separate WEEKLY and DAILY for organized display
            weekly_spec = next((s for s in detail['cycle_specs'] if s['timeframe'] == 'WEEKLY'), None)
            daily_spec = next((s for s in detail['cycle_specs'] if s['timeframe'] == 'DAILY'), None)

            # WEEKLY block
            if weekly_spec:
                median = weekly_spec.get('median_input_date_label')
                start = weekly_spec.get('window_start_date')
                end = weekly_spec.get('window_end_date')
                bars = weekly_spec.get('cycle_length_bars')
                support = weekly_spec.get('support_level')
                resistance = weekly_spec.get('resistance_level')

                weekly_trough = format_date(median) if median else '—'
                weekly_start_fmt = format_date(start) if start else '—'
                weekly_end_fmt = format_date(end) if end else '—'
                weekly_bars_fmt = fmt(bars)
                weekly_support_fmt = fmt(support) if support else '—'
                weekly_resistance_fmt = fmt(resistance) if resistance else '—'

                st.markdown(
                    f"""
**WEEKLY**<br>
Trough Date: {weekly_trough}<br>
Window: {weekly_start_fmt} → {weekly_end_fmt}<br>
Bars: {weekly_bars_fmt}<br>
Support: {weekly_support_fmt} | Resistance: {weekly_resistance_fmt}
""".strip(),
                    unsafe_allow_html=True
                )

                # Small gap between WEEKLY and DAILY
                st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)

            # DAILY block
            if daily_spec:
                median = daily_spec.get('median_input_date_label')
                start = daily_spec.get('window_start_date')
                end = daily_spec.get('window_end_date')
                bars = daily_spec.get('cycle_length_bars')
                support = daily_spec.get('support_level')
                resistance = daily_spec.get('resistance_level')

                daily_trough = format_date(median) if median else '—'
                daily_start_fmt = format_date(start) if start else '—'
                daily_end_fmt = format_date(end) if end else '—'
                daily_bars_fmt = fmt(bars)
                daily_support_fmt = fmt(support) if support else '—'
                daily_resistance_fmt = fmt(resistance) if resistance else '—'

                st.markdown(
                    f"""
**DAILY**<br>
Trough Date: {daily_trough}<br>
Window: {daily_start_fmt} → {daily_end_fmt}<br>
Bars: {daily_bars_fmt}<br>
Support: {daily_support_fmt} | Resistance: {daily_resistance_fmt}
""".strip(),
                    unsafe_allow_html=True
                )
        else:
            st.info("No cycle specs")

    # FULL WIDTH SECTIONS BELOW COLUMNS
    st.divider()

    # Desk Notes - Editable with toggle
    st.markdown("### Desk Notes")
    existing_note = detail['notes'][0] if detail['notes'] else None
    existing_formatted = existing_note.get('bullets_formatted', '') if existing_note else ''

    # Toggle between view and edit mode
    edit_notes_key = f"edit_notes_{symbol}"
    if edit_notes_key not in st.session_state:
        st.session_state[edit_notes_key] = False

    if not st.session_state[edit_notes_key]:
        # Display mode
        if existing_formatted:
            st.markdown(existing_formatted)
        else:
            st.info("No desk notes yet")

        if st.button("✏️ Edit Notes", key=f"btn_edit_notes_{symbol}"):
            st.session_state[edit_notes_key] = True
            st.rerun()
    else:
        # Edit mode
        with st.form(f"desk_notes_{symbol}", clear_on_submit=False):
            desk_notes_text = st.text_area(
                "Markdown supported: **bold** *italic* # Heading - bullet > quote",
                value=existing_formatted,
                height=300,
                key=f"desk_notes_today_{symbol}"
            )

            col_a, col_b = st.columns([1, 5])
            with col_a:
                save_notes = st.form_submit_button("💾 Save", width='stretch')
            with col_b:
                cancel_notes = st.form_submit_button("✖️ Cancel", width='content')

            if save_notes:
                success = db.update_desk_note_formatted(symbol, scan_date, desk_notes_text)
                if success:
                    st.session_state[edit_notes_key] = False
                    st.success("Notes saved!")
                    st.rerun()
                else:
                    st.error("Failed to save notes")

            if cancel_notes:
                st.session_state[edit_notes_key] = False
                st.rerun()

    # Analysis - Editable with toggle
    st.markdown("### Analysis")
    existing_analysis = existing_note.get('analysis', '') if existing_note else ''

    # Toggle between view and edit mode
    edit_analysis_key = f"edit_analysis_{symbol}"
    if edit_analysis_key not in st.session_state:
        st.session_state[edit_analysis_key] = False

    if not st.session_state[edit_analysis_key]:
        # Display mode
        if existing_analysis:
            st.markdown(existing_analysis)
        else:
            st.info("No analysis yet")

        if st.button("✏️ Edit Analysis", key=f"btn_edit_analysis_{symbol}"):
            st.session_state[edit_analysis_key] = True
            st.rerun()
    else:
        # Edit mode
        with st.form(f"analysis_{symbol}", clear_on_submit=False):
            analysis_text = st.text_area(
                "Markdown supported - write your full analysis here",
                value=existing_analysis,
                height=400,
                placeholder="Market context, trade setup, risk assessment, technical analysis...",
                key=f"analysis_today_{symbol}"
            )

            col_a, col_b = st.columns([1, 5])
            with col_a:
                save_analysis = st.form_submit_button("💾 Save", width='stretch')
            with col_b:
                cancel_analysis = st.form_submit_button("✖️ Cancel", width='content')

            if save_analysis:
                success = db.update_desk_note_analysis(symbol, scan_date, analysis_text)
                if success:
                    st.session_state[edit_analysis_key] = False
                    st.success("Analysis saved!")
                    st.rerun()
                else:
                    st.error("Failed to save analysis")

            if cancel_analysis:
                st.session_state[edit_analysis_key] = False
                st.rerun()

    # Charts / Media - FULL WIDTH BELOW COLUMNS with categorized tabs
    st.divider()
    st.markdown("### Charts")

    # Get media files from database
    askslim_media = db.get_media_files(symbol, category='askslim')
    tradingview_media = db.get_media_files(symbol, category='tradingview')
    other_media = db.get_media_files(symbol, category='other')

    # Create tabs for different media categories
    tab1, tab2, tab3 = st.tabs([
        f"📊 AskSlim ({len(askslim_media)})",
        f"📈 TradingView ({len(tradingview_media)})",
        f"📁 Other ({len(other_media)})"
    ])

    with tab1:
        if askslim_media:
            for media in askslim_media:
                caption = f"{media['timeframe']} - {media['upload_date']}" if media['timeframe'] else media['upload_date']
                with st.expander(f"{media['file_name']}", expanded=True):
                    st.image(media['file_path'], caption=caption, width='stretch')
                    if media.get('notes'):
                        st.caption(media['notes'])
        else:
            st.info("No AskSlim charts available. Charts will appear here after running the scraper.")

    with tab2:
        # Upload form for TradingView charts
        with st.form(f"upload_tv_{symbol}", clear_on_submit=True):
            st.markdown("**Upload TradingView Chart**")
            uploaded_file = st.file_uploader("Select image", type=['png', 'jpg', 'jpeg'], key=f"tv_upload_{symbol}")
            notes = st.text_input("Notes (optional)", key=f"tv_notes_{symbol}")

            if st.form_submit_button("📤 Upload"):
                if uploaded_file:
                    from pathlib import Path
                    from datetime import datetime

                    # Save file
                    media_folder = Path(f"media/{symbol}/tradingview")
                    media_folder.mkdir(parents=True, exist_ok=True)
                    file_path = media_folder / uploaded_file.name

                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # Track in database
                    db.insert_media_file(
                        symbol=symbol,
                        category='tradingview',
                        file_path=str(file_path),
                        file_name=uploaded_file.name,
                        upload_date=datetime.now().strftime("%Y-%m-%d"),
                        source='manual',
                        notes=notes if notes else None
                    )

                    st.success(f"Uploaded {uploaded_file.name}")
                    st.rerun()
                else:
                    st.error("Please select a file")

        st.divider()

        # Display existing charts
        if tradingview_media:
            for media in tradingview_media:
                caption = media.get('notes') or media['file_name']
                with st.expander(f"{media['file_name']}", expanded=True):
                    st.image(media['file_path'], caption=caption, width='stretch')
                    st.caption(f"Uploaded: {media['upload_date']}")
        else:
            st.info("No TradingView charts yet")

    with tab3:
        # Upload form for Other charts
        with st.form(f"upload_other_{symbol}", clear_on_submit=True):
            st.markdown("**Upload Other Chart**")
            uploaded_file = st.file_uploader("Select image", type=['png', 'jpg', 'jpeg'], key=f"other_upload_{symbol}")
            notes = st.text_input("Notes (optional)", key=f"other_notes_{symbol}")

            if st.form_submit_button("📤 Upload"):
                if uploaded_file:
                    from pathlib import Path
                    from datetime import datetime

                    # Save file
                    media_folder = Path(f"media/{symbol}/other")
                    media_folder.mkdir(parents=True, exist_ok=True)
                    file_path = media_folder / uploaded_file.name

                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # Track in database
                    db.insert_media_file(
                        symbol=symbol,
                        category='other',
                        file_path=str(file_path),
                        file_name=uploaded_file.name,
                        upload_date=datetime.now().strftime("%Y-%m-%d"),
                        source='manual',
                        notes=notes if notes else None
                    )

                    st.success(f"Uploaded {uploaded_file.name}")
                    st.rerun()
                else:
                    st.error("Please select a file")

        st.divider()

        # Display existing charts
        if other_media:
            for media in other_media:
                caption = media.get('notes') or media['file_name']
                with st.expander(f"{media['file_name']}", expanded=True):
                    st.image(media['file_path'], caption=caption, width='stretch')
                    st.caption(f"Uploaded: {media['upload_date']}")
        else:
            st.info("No other charts yet")


def render_database_view(filters: dict = None):
    """Render DATABASE view"""
    st.header("DATABASE - Full Instrument Editor")

    # ========================================================================
    # SINGLE SOURCE OF TRUTH: db_selected_symbol in session_state
    # ========================================================================

    # Initialize session state
    if "db_selected_symbol" not in st.session_state:
        st.session_state["db_selected_symbol"] = None
    if "db_prev_symbol" not in st.session_state:
        st.session_state["db_prev_symbol"] = None

    # SEARCH BOX (with alias resolution)
    search_input = st.text_input(
        "Search instrument (symbol or alias)",
        placeholder="e.g., ES, SPY, QQQ",
        help="Enter a symbol or alias to jump to that instrument",
        key="db_search_input"
    )
    search_button = st.button("Search", width='stretch')

    # Handle search with alias resolution
    if search_button and search_input:
        canonical_symbol = db.resolve_symbol(search_input)
        all_instruments = db.get_instruments({'active_only': False})
        matches = all_instruments[all_instruments['symbol'].str.upper() == canonical_symbol.upper()]

        if not matches.empty:
            st.session_state["db_selected_symbol"] = matches.iloc[0]['symbol']
            if canonical_symbol.upper() != search_input.strip().upper():
                st.info(f"'{search_input}' → {canonical_symbol}")
            st.rerun()
        else:
            st.error(f"Instrument '{search_input}' not found")

    st.divider()

    # Merge filters from main() with active_only checkbox
    view_filters = filters.copy() if filters else {}
    col1, col2, col3 = st.columns(3)
    with col1:
        active_only = st.checkbox("Active only", value=True, key="db_active_only")
        if active_only:
            view_filters['active_only'] = True

    df = db.get_instruments(view_filters)

    if df.empty:
        st.warning("No instruments found")
        return

    st.subheader(f"Total Instruments: {len(df)}")

    # ========================================================================
    # TABLE SELECTION (like TODAY page)
    # ========================================================================
    st.markdown("**Select an instrument from the table:**")

    display_cols = ['symbol', 'name', 'instrument_type', 'sector', 'active', 'aliases']
    display_df = df[[c for c in display_cols if c in df.columns]].copy()

    # Add row selection using dataframe selection
    event = st.dataframe(
        display_df,
        width='stretch',
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
        key="db_instrument_table"
    )

    # Handle table selection
    if event.selection.rows:
        selected_idx = event.selection.rows[0]
        new_symbol = df.iloc[selected_idx]['symbol']
        if st.session_state["db_selected_symbol"] != new_symbol:
            st.session_state["db_selected_symbol"] = new_symbol
            st.rerun()

    # If no selection yet, default to first instrument
    if st.session_state["db_selected_symbol"] is None:
        st.session_state["db_selected_symbol"] = df.iloc[0]['symbol']

    # Get current selected symbol
    symbol = st.session_state["db_selected_symbol"]

    # Verify symbol exists in current filtered list
    if symbol not in df['symbol'].tolist():
        symbol = df.iloc[0]['symbol']
        st.session_state["db_selected_symbol"] = symbol

    st.divider()

    # ========================================================================
    # DROPDOWN SELECTOR (alternative to table, with on_change)
    # ========================================================================

    def handle_db_symbol_change():
        """Handle dropdown selection change"""
        new_symbol = st.session_state["db_dropdown"]
        if st.session_state["db_selected_symbol"] != new_symbol:
            st.session_state["db_selected_symbol"] = new_symbol

    default_idx = 0
    if symbol in df['symbol'].tolist():
        default_idx = df['symbol'].tolist().index(symbol)

    st.selectbox(
        "OR select from dropdown:",
        df['symbol'].tolist(),
        index=default_idx,
        key="db_dropdown",
        on_change=handle_db_symbol_change
    )

    # ========================================================================
    # FETCH DATA FOR SELECTED INSTRUMENT (single source of truth)
    # ========================================================================
    full_data = db.get_instrument_full(symbol)

    if 'error' in full_data:
        st.error(full_data['error'])
        return

    instrument = full_data['instrument']
    daily_cycle = full_data.get('daily_cycle')
    weekly_cycle = full_data.get('weekly_cycle')
    astro_data = full_data.get('astro', {})
    note_data = full_data.get('desk_note', {})

    st.success(f"✏️ Editing: **{symbol}** - {instrument.get('name', 'N/A')}")

    st.divider()

    # ========================================================================
    # SECTION 1: INSTRUMENT METADATA EDITOR
    # ========================================================================
    st.subheader("1. Instrument Metadata")
    with st.form(f"edit_instrument_{symbol}"):  # Form key namespaced by symbol

        col1, col2 = st.columns(2)

        with col1:
            # Show instrument type as readonly
            st.text_input(
                "Instrument Type (readonly)",
                value=instrument.get('instrument_type', 'FUTURES'),
                disabled=True,
                key=f"instrument_type_{symbol}"
            )
            sector = st.text_input(
                "Sector",
                value=instrument.get('sector', 'UNCLASSIFIED'),
                help="Classification sector (e.g., METALS, INDICES, ENERGY)",
                key=f"sector_{symbol}"
            )

        with col2:
            aliases = st.text_area(
                "Aliases (comma-separated)",
                value=instrument.get('aliases', '') or '',
                placeholder="SPX, SPY, ES.c",
                help="Alternative symbols that resolve to this canonical instrument",
                key=f"aliases_{symbol}"
            )

        submitted = st.form_submit_button("💾 Save Metadata")

        if submitted:
            fields = {
                'sector': sector,
                'aliases': aliases.strip() if aliases else None
            }
            success = db.update_instrument_taxonomy(symbol, fields)
            if success:
                st.success(f"✅ Updated {symbol} metadata successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to update {symbol}")

    st.divider()

    # ========================================================================
    # SECTION 2: CYCLES EDITOR
    # ========================================================================
    st.subheader("2. Cycles Editor")

    with st.form(f"edit_cycles_{symbol}"):  # Form key namespaced by symbol
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("**DAILY Cycle**")
            daily_median = st.date_input(
                "Daily Trough Median",
                value=pd.to_datetime(daily_cycle['median']).date() if daily_cycle and daily_cycle.get('median') else None,
                help="The median date of the DAILY cycle trough",
                key=f"daily_median_{symbol}"
            )
            daily_bars = st.number_input(
                "Daily Cycle Bars",
                min_value=1,
                max_value=200,
                value=int(daily_cycle['bars']) if daily_cycle and daily_cycle.get('bars') else 35,
                help="Number of bars in DAILY cycle",
                key=f"daily_bars_{symbol}"
            )
            if daily_cycle and daily_cycle.get('window_start') and daily_cycle.get('window_end'):
                st.caption(f"Window: {daily_cycle['window_start']} → {daily_cycle['window_end']}")
            else:
                st.caption("No DAILY cycle configured")

        with col2:
            st.markdown("**WEEKLY Cycle**")
            weekly_median = st.date_input(
                "Weekly Trough Median",
                value=pd.to_datetime(weekly_cycle['median']).date() if weekly_cycle and weekly_cycle.get('median') else None,
                help="The median date of the WEEKLY cycle trough",
                key=f"weekly_median_{symbol}"
            )
            weekly_bars = st.number_input(
                "Weekly Cycle Bars",
                min_value=1,
                max_value=200,
                value=int(weekly_cycle['bars']) if weekly_cycle and weekly_cycle.get('bars') else 36,
                help="Number of bars in WEEKLY cycle",
                key=f"weekly_bars_{symbol}"
            )
            if weekly_cycle and weekly_cycle.get('window_start') and weekly_cycle.get('window_end'):
                st.caption(f"Window: {weekly_cycle['window_start']} → {weekly_cycle['window_end']}")
            else:
                st.caption("No WEEKLY cycle configured")

        st.info("⚠️ Saving cycles will automatically recompute window dates using trading day logic")

        cycles_submitted = st.form_submit_button("💾 Save Cycles")

        if cycles_submitted:
            # Convert date inputs to string
            daily_median_str = daily_median.strftime('%Y-%m-%d') if daily_median else None
            weekly_median_str = weekly_median.strftime('%Y-%m-%d') if weekly_median else None

            result = db.update_cycles(
                symbol=symbol,
                daily_median=daily_median_str,
                daily_bars=daily_bars,
                weekly_median=weekly_median_str,
                weekly_bars=weekly_bars
            )

            if result.get('status') == 'success':
                st.success(f"✅ Updated cycles for {symbol} successfully!")
                if result.get('daily'):
                    st.info(f"DAILY: Window {result['daily']['window_start']} → {result['daily']['window_end']}")
                if result.get('weekly'):
                    st.info(f"WEEKLY: Window {result['weekly']['window_start']} → {result['weekly']['window_end']}")
                st.rerun()
            else:
                st.error(f"❌ Failed to update cycles: {result.get('message', 'Unknown error')}")

    st.divider()

    # ========================================================================
    # SECTION 3: ASTRO DATES EDITOR
    # ========================================================================
    st.subheader("3. Astro Dates")

    with st.form(f"edit_astro_{symbol}"):  # Form key namespaced by symbol
        col1, col2 = st.columns(2)

        with col1:
            primary_date = st.date_input(
                "Primary Astro Date",
                value=pd.to_datetime(astro_data.get('primary_date')).date() if astro_data.get('primary_date') else None,
                help="Primary astro event date",
                key=f"primary_date_{symbol}"
            )

        with col2:
            backup_date = st.date_input(
                "Backup Astro Date",
                value=pd.to_datetime(astro_data.get('backup_date')).date() if astro_data.get('backup_date') else None,
                help="Backup astro event date",
                key=f"backup_date_{symbol}"
            )

        astro_submitted = st.form_submit_button("💾 Save Astro Dates")

        if astro_submitted:
            primary_str = primary_date.strftime('%Y-%m-%d') if primary_date else None
            backup_str = backup_date.strftime('%Y-%m-%d') if backup_date else None

            success = db.update_astro_dates(
                symbol=symbol,
                primary_date=primary_str,
                backup_date=backup_str
            )

            if success:
                st.success(f"✅ Updated astro dates for {symbol} successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to update astro dates")

    st.divider()

    # ========================================================================
    # SECTION 4: DESK NOTES EDITOR
    # ========================================================================
    st.subheader("4. Desk Notes")

    # Display notes history first (if any) - SAME FORMAT AS TODAY VIEW
    notes_history = full_data.get('desk_notes_history', [])
    if notes_history:
        st.markdown("**Notes History** (newest first):")
        for note in notes_history:
            # Try formatted content first, fall back to bullets_json
            formatted = note.get('bullets_formatted')
            if formatted:
                st.markdown(formatted)
            else:
                try:
                    bullets = json.loads(note.get('bullets_json', '[]'))
                    for bullet in bullets:
                        st.write(f"- {bullet}")
                except:
                    # Fallback to notes field if bullets_json fails
                    text = note.get('notes', '')
                    if text:
                        st.markdown(text)
            st.divider()
    else:
        st.info("No notes history for this instrument.")

    st.markdown("**Edit Note:**")

    # Get instrument_id and latest note date
    instrument_id = full_data['instrument'].get('instrument_id')

    # Get the latest note's date (or use today if no notes exist)
    latest_note = notes_history[0] if notes_history else None
    note_date = latest_note['asof_td_label'] if latest_note else datetime.now().strftime('%Y-%m-%d')

    # Get existing note content - prefer formatted over plain text
    existing_formatted = note_data.get('bullets_formatted', '')
    existing_text = note_data.get('text', '')

    # Use formatted if available, otherwise fall back to plain text
    editor_content = existing_formatted if existing_formatted else existing_text

    with st.form(f"edit_notes_{symbol}"):
        # Markdown-enabled text area with formatting controls
        st.markdown("**Format with Markdown:** `**bold**` `*italic*` `# Heading` `- bullet` `> quote`")
        note_text = st.text_area(
            "Desk Notes (Markdown Supported)",
            value=editor_content,
            height=200,
            help="Use markdown formatting: **bold**, *italic*, # headings, - bullets, > quotes, [links](url)",
            placeholder="# Trading Notes\n\n**Key Levels:**\n- Support: 5000\n- Resistance: 5100\n\n> Market showing bullish momentum",
            key=f"note_text_{symbol}"
        )

        # Show when this note was last updated
        if note_data.get('updated_at'):
            st.caption(f"Last updated: {note_data['updated_at']} | Note date: {note_date}")
        else:
            st.caption(f"New note will be saved with date: {note_date}")

        notes_submitted = st.form_submit_button("💾 Save Note")

        if notes_submitted:
            # Save to bullets_formatted field (markdown content)
            # Also save to legacy fields for backwards compatibility
            success = db.upsert_note(
                instrument_id=instrument_id,
                asof_td_label=note_date,
                author='Bernard',
                note_text=note_text,
                source='Manual Entry'
            )

            # Update formatted content
            if success:
                db.update_desk_note_formatted(symbol, note_date, note_text)
                st.success(f"✅ Saved desk note for {symbol} successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to save desk note")

    st.divider()

    # ========================================================================
    # SECTION 4.5: ANALYSIS JOURNAL
    # ========================================================================
    st.subheader("4.5. Analysis Journal")

    # Get existing analysis
    existing_analysis = note_data.get('analysis', '')

    with st.form(f"edit_analysis_{symbol}"):
        analysis_text = st.text_area(
            "Long-form Analysis",
            value=existing_analysis,
            height=300,
            help="Write your detailed analysis, trade plan, or journal entry here. Supports markdown formatting.",
            placeholder="Market context, trade setup, risk assessment, technical analysis...\n\nSupports:\n- **bold**, *italic*\n- # Headings\n- [links](url)\n- > quotes",
            key=f"analysis_text_{symbol}"
        )

        st.caption(f"Analysis for date: {note_date}")
        analysis_submitted = st.form_submit_button("💾 Save Analysis")

        if analysis_submitted:
            success = db.update_desk_note_analysis(
                symbol,
                note_date,
                analysis_text
            )

            if success:
                st.success(f"✅ Saved analysis for {symbol} successfully!")
                st.rerun()
            else:
                st.error(f"❌ Failed to save analysis")

    st.divider()

    # ========================================================================
    # SECTION 5: MEDIA UPLOAD (CHARTS/IMAGES) - Categorized Management
    # ========================================================================
    st.subheader("5. Charts & Media Management")

    # Get media folder for this symbol
    project_root = Path(get_db_path()).parent.parent
    media_folder = project_root / "media" / symbol
    media_folder.mkdir(parents=True, exist_ok=True)

    # Create tabs for upload and management
    upload_tab, manage_tab = st.tabs(["📤 Upload Charts", "🗂️ Manage Charts"])

    with upload_tab:
        st.markdown("**Upload TradingView or Other Charts** *(AskSlim charts are auto-managed by scraper)*")

        with st.form(f"upload_media_{symbol}"):
            col1, col2 = st.columns(2)

            with col1:
                category = st.selectbox(
                    "Category",
                    ["tradingview", "other"],
                    format_func=lambda x: "📈 TradingView" if x == "tradingview" else "📁 Other"
                )

            with col2:
                timeframe = st.selectbox(
                    "Timeframe (optional)",
                    [None, "DAILY", "WEEKLY"],
                    format_func=lambda x: "Not specified" if x is None else x
                )

            notes = st.text_input("Notes (optional)", help="Add context about this chart")

            uploaded_files = st.file_uploader(
                "Select image files",
                type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
                accept_multiple_files=True,
                key=f"media_upload_{symbol}"
            )

            upload_submitted = st.form_submit_button(f"💾 Upload {len(uploaded_files) if uploaded_files else 0} file(s)")

            if upload_submitted and uploaded_files:
                # Create category subfolder
                category_folder = media_folder / category
                category_folder.mkdir(parents=True, exist_ok=True)

                for uploaded_file in uploaded_files:
                    # Save file
                    file_path = category_folder / uploaded_file.name
                    with open(file_path, 'wb') as f:
                        f.write(uploaded_file.getbuffer())

                    # Track in database
                    try:
                        db.insert_media_file(
                            symbol=symbol,
                            category=category,
                            file_path=str(file_path),
                            file_name=uploaded_file.name,
                            upload_date=datetime.now().strftime("%Y-%m-%d"),
                            source='manual',
                            timeframe=timeframe,
                            notes=notes
                        )
                    except Exception as e:
                        st.error(f"Database error: {e}")

                st.success(f"✅ Uploaded {len(uploaded_files)} file(s) to {category.upper()} category!")
                st.rerun()

    with manage_tab:
        st.markdown("**All Charts** *(grouped by category)*")

        # Get all media from database
        all_media = db.get_media_files(symbol)

        if all_media:
            # Group by category
            askslim_charts = [m for m in all_media if m['category'] == 'askslim']
            tv_charts = [m for m in all_media if m['category'] == 'tradingview']
            other_charts = [m for m in all_media if m['category'] == 'other']

            # AskSlim section (read-only - managed by scraper)
            if askslim_charts:
                st.markdown("#### 📊 AskSlim Charts (Auto-managed)")
                st.caption("⚠️ These are automatically managed by the scraper and cannot be manually deleted")
                for media in askslim_charts[:5]:  # Show latest 5
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**{media['file_name']}** - {media['timeframe']} ({media['upload_date']})")
                    with col2:
                        if Path(media['file_path']).exists():
                            st.image(media['file_path'], width=100)

            # TradingView section (user can delete)
            if tv_charts:
                st.markdown("#### 📈 TradingView Charts")
                for media in tv_charts:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{media['file_name']}**")
                        if media.get('notes'):
                            st.caption(media['notes'])
                        st.caption(f"Uploaded: {media['upload_date']}")
                    with col2:
                        if Path(media['file_path']).exists():
                            st.image(media['file_path'], width=100)
                    with col3:
                        if st.button("🗑️", key=f"del_tv_{media['media_id']}"):
                            # Delete from database
                            db.delete_media_file(media['media_id'])
                            # Delete file
                            if Path(media['file_path']).exists():
                                Path(media['file_path']).unlink()
                            st.success("Deleted!")
                            st.rerun()

            # Other section (user can delete)
            if other_charts:
                st.markdown("#### 📁 Other Charts")
                for media in other_charts:
                    col1, col2, col3 = st.columns([3, 1, 1])
                    with col1:
                        st.write(f"**{media['file_name']}**")
                        if media.get('notes'):
                            st.caption(media['notes'])
                        st.caption(f"Uploaded: {media['upload_date']}")
                    with col2:
                        if Path(media['file_path']).exists():
                            st.image(media['file_path'], width=100)
                    with col3:
                        if st.button("🗑️", key=f"del_other_{media['media_id']}"):
                            # Delete from database
                            db.delete_media_file(media['media_id'])
                            # Delete file
                            if Path(media['file_path']).exists():
                                Path(media['file_path']).unlink()
                            st.success("Deleted!")
                            st.rerun()

        else:
            st.info("No charts available. Upload some or run the askSlim scraper.")


def render_calendar_view():
    """Render CALENDAR view - 2-month cycle windows visualization"""
    from datetime import date, timedelta
    from dateutil.relativedelta import relativedelta

    st.header("Calendar - This Month + Next Month")

    # Get DB path (centralized)
    db_path = get_db_path()

    # Import calendar events builder
    from src.riley.calendar_events import build_fullcalendar_events, get_available_symbols

    # Filters in expander
    with st.expander("Calendar Filters", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            # Get all symbols
            try:
                all_symbols = get_available_symbols(str(db_path))

                selected_symbols = st.multiselect(
                    "Symbols",
                    options=all_symbols,
                    default=all_symbols,  # All symbols by default
                    help="Select symbols to display"
                )
            except Exception as e:
                st.error(f"Failed to load symbols: {e}")
                return

        with col2:
            show_daily = st.checkbox("Show DAILY Windows", value=True)
            show_weekly = st.checkbox("Show WEEKLY Windows", value=True)
            show_overlap = st.checkbox("Show OVERLAP", value=True)
            show_astro = st.checkbox("Show Astro Events", value=True)

    # Build events
    try:
        events = build_fullcalendar_events(
            db_path=str(db_path),
            symbols=selected_symbols if selected_symbols else None,
            include_daily=show_daily,
            include_weekly=show_weekly,
            include_overlap=show_overlap,
            include_astro=show_astro
        )
    except Exception as e:
        st.error(f"Failed to build events: {e}")
        st.exception(e)
        return

    if not events:
        st.warning("No events to display. Adjust filters or check database.")
        return

    # Display info
    st.info(f"Displaying **{len(events)}** events for **{len(selected_symbols)}** symbols")

    # Calculate months
    today = date.today()
    current_month = today.replace(day=1)
    next_month = (current_month.replace(day=28) + timedelta(days=4)).replace(day=1)

    # Try streamlit-calendar first
    try:
        from streamlit_calendar import calendar as st_calendar

        # Current month
        st_calendar(
            events=events,
            options={
                "initialView": "dayGridMonth",
                "initialDate": str(current_month),
                "headerToolbar": {
                    "left": "title",
                    "center": "",
                    "right": ""
                },
                "height": "auto",
                "contentHeight": "auto",
                "expandRows": True,
                "aspectRatio": 3.2,
                "eventDisplay": "block",
                "displayEventTime": False
            },
            custom_css="""
                .fc-event {
                    border: none !important;
                    font-size: 0.85em;
                }
                .overlap-event {
                    z-index: 10 !important;
                    font-weight: bold;
                }
                .fc-view-harness {
                    height: auto !important;
                }
                .fc-scroller {
                    overflow: hidden !important;
                }
                .fc-daygrid-day {
                    min-height: 90px;
                }
            """,
            key="cal_current"
        )

        st.divider()

        # Next month
        st_calendar(
            events=events,
            options={
                "initialView": "dayGridMonth",
                "initialDate": str(next_month),
                "headerToolbar": {
                    "left": "title",
                    "center": "",
                    "right": ""
                },
                "height": "auto",
                "contentHeight": "auto",
                "expandRows": True,
                "aspectRatio": 3.2,
                "eventDisplay": "block",
                "displayEventTime": False
            },
            custom_css="""
                .fc-event {
                    border: none !important;
                    font-size: 0.85em;
                }
                .overlap-event {
                    z-index: 10 !important;
                    font-weight: bold;
                }
                .fc-view-harness {
                    height: auto !important;
                }
                .fc-scroller {
                    overflow: hidden !important;
                }
                .fc-daygrid-day {
                    min-height: 90px;
                }
            """,
            key="cal_next"
        )

    except ImportError:
        st.warning("⚠️ streamlit-calendar not available; using HTML fallback.")

        import streamlit.components.v1 as components

        # FullCalendar CDN fallback
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <link href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css" rel="stylesheet">
            <script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
            <style>
                html, body {{
                    height: 100%;
                    margin: 0;
                    padding: 0;
                    overflow: hidden;
                }}
                .calwrap {{
                    max-width: 1800px;
                    width: 100%;
                    margin: 0 auto;
                    padding: 8px;
                }}
                .cal {{
                    margin-bottom: 20px;
                }}
                .cal-title {{
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 10px;
                }}
                .fc {{
                    font-size: 13px;
                }}
                .fc-event {{
                    border-width: 1px !important;
                    font-size: 0.85em;
                    font-weight: 500;
                }}
                .overlap-event {{
                    z-index: 10 !important;
                    font-weight: 700 !important;
                }}
                .fc-view-harness {{
                    height: auto !important;
                }}
                .fc-scroller {{
                    overflow: hidden !important;
                }}
                .fc-daygrid-body {{
                    min-height: 520px;
                }}
                .fc-daygrid-day {{
                    min-height: 90px;
                }}
            </style>
        </head>
        <body>
            <div class="calwrap">
                <div class="cal-title">{current_month.strftime('%B %Y')}</div>
                <div id="calA" class="cal"></div>

                <div class="cal-title">{next_month.strftime('%B %Y')}</div>
                <div id="calB" class="cal"></div>
            </div>

            <script>
                const events = {json.dumps(events)};

                function renderCal(elId, initialDate) {{
                    const el = document.getElementById(elId);
                    const cal = new FullCalendar.Calendar(el, {{
                        initialView: 'dayGridMonth',
                        initialDate: initialDate,
                        height: 'auto',
                        contentHeight: 'auto',
                        expandRows: true,
                        events: events,
                        eventDisplay: 'block',
                        displayEventTime: false,
                        headerToolbar: {{
                            left: 'title',
                            center: '',
                            right: ''
                        }},
                        aspectRatio: 3.2
                    }});
                    cal.render();
                }}

                renderCal('calA', '{current_month}');
                renderCal('calB', '{next_month}');
            </script>
        </body>
        </html>
        """

        components.html(html, height=1400, scrolling=False)

    # Legend
    st.divider()
    st.subheader("Legend")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        **Color Coding:**
        - **Color** = Instrument (each symbol has unique color)
        - **Shade** = Cycle Type
          - Light shade = DAILY window
          - Medium shade = WEEKLY window
          - Dark/saturated = OVERLAP (both active)
        """)

    with col2:
        st.markdown("""
        **Astro Events:**
        - 🔴 **PRIMARY** - Red dots
        - 🔵 **BACKUP** - Teal dots

        **Examples:**
        - ES = Blue shades
        - BTC = Orange shades
        - NQ = Green shades
        """)


def render_rrg_view():
    """Render RRG Sector Rotation Map view"""
    st.header("RRG - Sector Rotation Map")
    st.caption("Relative Rotation Graph for US Sector ETFs")

    # Import RRG components
    try:
        # Add sector-rotation-map to path
        rrg_path = Path(__file__).parent.parent / "sector-rotation-map"
        if str(rrg_path) not in sys.path:
            sys.path.insert(0, str(rrg_path))

        # Add src to path for riley modules
        src_path = Path(__file__).parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        from rrg.compute import compute_rrg_metrics
        from rrg.chart import create_rrg_chart
        from rrg.constants import DEFAULT_PARAMS, US_SECTORS

        # Import market data module
        from riley.modules.marketdata.store import get_db_path
        from riley.modules.marketdata.export_rrg import get_export_stats

    except ImportError as e:
        st.error(f"Failed to import RRG modules: {e}")
        st.info("Make sure the sector-rotation-map module is available")
        return

    # Check if market data exists
    try:
        stats = get_export_stats()

        if stats['total_bars'] == 0:
            st.warning("No market data available yet")
            st.info("To collect market data, run:\n```bash\npython3 scripts/riley_marketdata.py backfill --lookback-days 730\n```")
            return

        # Display data stats
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Symbols", stats['total_symbols'])
        with col2:
            st.metric("Total Bars", f"{stats['total_bars']:,}")
        with col3:
            date_range = stats['date_range']
            # Format dates as "24 Dec 2025"
            min_date = pd.to_datetime(date_range['min']).strftime('%d %b %Y')
            max_date = pd.to_datetime(date_range['max']).strftime('%d %b %Y')
            st.metric("Date Range", f"{min_date} to {max_date}")

        st.divider()

        # Sidebar controls
        st.sidebar.divider()
        st.sidebar.subheader("RRG Controls")

        # Sector Selection
        with st.sidebar.expander("Select Sectors", expanded=True):
            select_all = st.checkbox("Select All", value=True)

            sector_list = list(US_SECTORS.keys())
            if select_all:
                selected_sectors = st.multiselect(
                    "Sectors to Display",
                    options=sector_list,
                    default=sector_list,
                    help="Choose which sectors to display on the chart"
                )
            else:
                selected_sectors = st.multiselect(
                    "Sectors to Display",
                    options=sector_list,
                    default=[],
                    help="Choose which sectors to display on the chart"
                )

        # Quick Select Presets
        st.sidebar.divider()
        st.sidebar.subheader("Quick Select Groups")

        preset_groups = {
            "📈 Stock Sectors": "XLK,XLY,XLC,XLV,XLF,XLE,XLI,XLP,XLU,XLB,XLRE",
            "🥇 Commodities": "GC=F,SI=F,CL=F,NG=F,HG=F,PL=F,ZC=F,ZW=F,ZS=F",
            "💎 Precious Metals": "GLD,SLV,GC=F,SI=F,PALL,PPLT",
            "⛽ Energy": "USO,UNG,CL=F,NG=F,XLE,OIH",
            "🌾 Agriculture": "CORN,WEAT,SOYB,ZC=F,ZW=F,ZS=F,DBA",
            "🏦 Major Indices": "SPY,QQQ,DIA,IWM,VTI",
            "🌍 International": "EWJ,EWG,EWU,EWC,EWA,FXI,EWZ",
            "₿ Crypto": "BTC-USD,ETH-USD,BNB-USD,SOL-USD,ADA-USD"
        }

        cols = st.sidebar.columns(2)
        preset_selected = None
        for idx, (name, symbols) in enumerate(preset_groups.items()):
            col = cols[idx % 2]
            if col.button(name, width='stretch', key=f"preset_{idx}"):
                preset_selected = symbols

        # Custom instruments input
        if preset_selected:
            custom_symbols_input = st.sidebar.text_input(
                "Custom Instruments (comma-separated)",
                value=preset_selected,
                help="Enter stock symbols separated by commas to add to the chart"
            )
            # Auto-switch to Absolute mode for commodities
            if "Commodities" in [k for k, v in preset_groups.items() if v == preset_selected][0]:
                st.sidebar.info("💡 Tip: Select 'Absolute' benchmark below for commodity analysis")
        else:
            custom_symbols_input = st.sidebar.text_input(
                "Custom Instruments (comma-separated)",
                placeholder="e.g., AAPL, MSFT, NVDA",
                help="Enter stock symbols separated by commas to add to the chart"
            )

        # Parse custom symbols
        custom_symbols = []
        if custom_symbols_input:
            custom_symbols = [s.strip().upper() for s in custom_symbols_input.split(',') if s.strip()]
            if custom_symbols:
                st.sidebar.caption(f"Adding: {', '.join(custom_symbols)}")

        # Benchmark selection
        st.sidebar.divider()
        benchmark_options = ['SPY (S&P 500)', 'QQQ (Nasdaq)', 'DIA (Dow)', 'IWM (Russell 2000)', '--- Absolute (No Benchmark) ---'] + custom_symbols
        benchmark_choice = st.sidebar.selectbox(
            "Benchmark Symbol",
            options=benchmark_options,
            index=0,
            help="Symbol to use as benchmark for relative strength calculations. Select 'Absolute' to show pure momentum without comparison."
        )

        # Parse benchmark choice
        if 'Absolute' in benchmark_choice:
            benchmark_symbol = None  # No benchmark - absolute mode
            st.sidebar.caption("📊 Absolute mode: Showing pure momentum")
        else:
            benchmark_symbol = benchmark_choice.split('(')[0].strip()  # Extract ticker from display name

        # Zoom level control
        zoom_level = st.sidebar.select_slider(
            "Default Zoom Level",
            options=["Tight", "Normal", "Wide", "Auto"],
            value="Wide",
            help="Tight = Zoomed in close, Wide = Zoomed out more, Auto = Fits all data"
        )

        # Tail length control
        tail_weeks = st.sidebar.slider(
            "Tail Length (weeks)",
            min_value=1,
            max_value=12,
            value=1,  # Default to 1 week
            help="Number of weeks to show in historical tails"
        )

        # Parameters
        with st.sidebar.expander("Advanced Parameters", expanded=False):
            rs_smoothing = st.number_input(
                "RS Smoothing",
                min_value=1,
                max_value=50,
                value=DEFAULT_PARAMS['rs_smoothing'],
                help="EMA period for relative strength smoothing"
            )

            ratio_lookback = st.number_input(
                "RS-Ratio Lookback",
                min_value=1,
                max_value=50,
                value=DEFAULT_PARAMS['ratio_lookback'],
                help="SMA period for RS-Ratio calculation"
            )

            momentum_lookback = st.number_input(
                "RS-Momentum Lookback",
                min_value=1,
                max_value=50,
                value=DEFAULT_PARAMS['momentum_lookback'],
                help="SMA period for RS-Momentum calculation"
            )

        with st.sidebar.expander("Display Options", expanded=True):
            show_tails = st.checkbox("Show Historical Tails", value=True)
            show_labels = st.checkbox("Show Symbol Labels", value=True)

        # Load data from CSV files
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from riley.modules.marketdata.csv_price_manager import load_rrg_data

        df_raw = load_rrg_data()

        if df_raw.empty:
            st.error("No price data found in CSV files")
            return

        # Convert date column (already datetime from CSV load)
        df_raw['date'] = pd.to_datetime(df_raw['date'])

        # Fetch custom symbols if provided
        if custom_symbols:
            with st.spinner(f"Fetching data for {', '.join(custom_symbols)}..."):
                import yfinance as yf
                from datetime import timedelta

                # Get date range from existing data
                if not df_raw.empty:
                    start_date = df_raw['date'].min()
                    end_date_fetch = df_raw['date'].max() + timedelta(days=1)
                else:
                    # Default to 2 years if no data
                    end_date_fetch = pd.Timestamp.now()
                    start_date = end_date_fetch - timedelta(days=730)

                custom_data = []
                for symbol in custom_symbols:
                    try:
                        # Check if symbol already exists in database
                        existing_symbol_data = df_raw[df_raw['symbol'] == symbol]

                        if not existing_symbol_data.empty:
                            # Symbol exists - only fetch new data after last date
                            last_date = existing_symbol_data['date'].max()
                            fetch_start = last_date + timedelta(days=1)
                            st.sidebar.caption(f"📊 {symbol}: Updating from {fetch_start.strftime('%Y-%m-%d')}")
                        else:
                            # New symbol - fetch full history
                            fetch_start = start_date
                            st.sidebar.caption(f"📥 {symbol}: Downloading full history")

                        ticker = yf.Ticker(symbol)
                        hist = ticker.history(start=fetch_start, end=end_date_fetch)

                        if not hist.empty:
                            hist_reset = hist.reset_index()
                            hist_reset['symbol'] = symbol
                            hist_reset = hist_reset.rename(columns={
                                'Date': 'date',
                                'Open': 'open',
                                'High': 'high',
                                'Low': 'low',
                                'Close': 'close',
                                'Volume': 'volume'
                            })
                            # Strip timezone to match database data (tz-naive)
                            hist_reset['date'] = pd.to_datetime(hist_reset['date']).dt.tz_localize(None)
                            custom_data.append(hist_reset[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']])
                    except Exception as e:
                        st.sidebar.warning(f"⚠️ Could not fetch {symbol}: {str(e)[:100]}")

                if custom_data:
                    df_custom = pd.concat(custom_data, ignore_index=True)
                    df_raw = pd.concat([df_raw, df_custom], ignore_index=True)

        # Ensure benchmark symbol data is available
        if benchmark_symbol is None:
            # Absolute mode - create synthetic flat benchmark
            if not df_raw.empty:
                unique_dates = df_raw['date'].unique()
                benchmark_data = pd.DataFrame({
                    'date': unique_dates,
                    'symbol': '__ABSOLUTE__',
                    'open': 100.0,
                    'high': 100.0,
                    'low': 100.0,
                    'close': 100.0,
                    'volume': 0
                })
                df_raw = pd.concat([df_raw, benchmark_data], ignore_index=True)
                benchmark_symbol = '__ABSOLUTE__'
        elif benchmark_symbol not in df_raw['symbol'].unique():
            with st.spinner(f"Fetching benchmark data for {benchmark_symbol}..."):
                import yfinance as yf
                from datetime import timedelta

                if not df_raw.empty:
                    start_date = df_raw['date'].min()
                    end_date_fetch = df_raw['date'].max() + timedelta(days=1)
                else:
                    end_date_fetch = pd.Timestamp.now()
                    start_date = end_date_fetch - timedelta(days=730)

                try:
                    ticker = yf.Ticker(benchmark_symbol)
                    hist = ticker.history(start=start_date, end=end_date_fetch)
                    if not hist.empty:
                        hist_reset = hist.reset_index()
                        hist_reset['symbol'] = benchmark_symbol
                        hist_reset = hist_reset.rename(columns={
                            'Date': 'date',
                            'Open': 'open',
                            'High': 'high',
                            'Low': 'low',
                            'Close': 'close',
                            'Volume': 'volume'
                        })
                        hist_reset['date'] = pd.to_datetime(hist_reset['date']).dt.tz_localize(None)
                        benchmark_data = hist_reset[['date', 'symbol', 'open', 'high', 'low', 'close', 'volume']]
                        df_raw = pd.concat([df_raw, benchmark_data], ignore_index=True)
                except Exception as e:
                    st.error(f"Could not fetch benchmark {benchmark_symbol}: {str(e)}")
                    return

        # Compute RRG metrics
        with st.spinner("Computing RRG metrics..."):
            df_processed = compute_rrg_metrics(
                df_raw,
                benchmark_symbol=benchmark_symbol,
                rs_smoothing=rs_smoothing,
                ratio_lookback=ratio_lookback,
                momentum_lookback=momentum_lookback
            )

        # Get unique symbols and end date
        all_symbols = [s for s in df_processed['symbol'].unique() if s != benchmark_symbol]

        # Filter to selected sectors and add custom symbols
        if selected_sectors:
            symbols = [s for s in all_symbols if s in selected_sectors]
        else:
            symbols = []

        # Add custom symbols to display list
        symbols.extend([s for s in custom_symbols if s in all_symbols])

        if not symbols:
            st.warning("No sectors or symbols selected. Please select at least one.")
            return

        end_date = df_processed['date'].max()

        # Get benchmark price and name for title
        if benchmark_symbol == '__ABSOLUTE__':
            benchmark_price = None
            benchmark_display_name = 'Absolute Mode'
        else:
            benchmark_data = df_processed[
                (df_processed['symbol'] == benchmark_symbol) &
                (df_processed['date'] == end_date)
            ]
            benchmark_price = benchmark_data['close'].iloc[0] if not benchmark_data.empty else None
            benchmark_display_name = benchmark_symbol

        # Filter data for visualization
        df_filtered = df_processed[df_processed['symbol'].isin(symbols + [benchmark_symbol])].copy()

        # Create RRG chart
        fig = create_rrg_chart(
            df_filtered,
            symbols=symbols,
            end_date=end_date,
            tail_weeks=tail_weeks,
            show_tails=show_tails,
            show_labels=show_labels,
            benchmark_symbol=benchmark_display_name,
            benchmark_price=benchmark_price,
            zoom_level=zoom_level
        )

        # Display chart with zoom/pan enabled
        config = {
            'displayModeBar': True,
            'modeBarButtonsToAdd': ['zoom2d', 'pan2d', 'zoomIn2d', 'zoomOut2d', 'autoScale2d', 'resetScale2d'],
            'scrollZoom': True
        }
        st.plotly_chart(fig, width='stretch', config=config)

        st.divider()

        # Show sector table with current positions
        st.subheader("Current Sector Positions")

        latest_data = df_processed[df_processed['date'] == end_date].copy()
        latest_data = latest_data[latest_data['symbol'].isin(symbols)]

        # Add sector names
        latest_data['sector_name'] = latest_data['symbol'].map(US_SECTORS)

        # Determine quadrant
        def get_quadrant(row):
            if row['rs_ratio'] >= 100 and row['rs_momentum'] >= 100:
                return '🟢 Leading'
            elif row['rs_ratio'] < 100 and row['rs_momentum'] >= 100:
                return '🔵 Improving'
            elif row['rs_ratio'] < 100 and row['rs_momentum'] < 100:
                return '🟡 Lagging'
            else:
                return '🔴 Weakening'

        latest_data['quadrant'] = latest_data.apply(get_quadrant, axis=1)

        # Format display
        display_df = latest_data[['symbol', 'sector_name', 'rs_ratio', 'rs_momentum', 'quadrant']].copy()
        display_df = display_df.rename(columns={
            'symbol': 'Symbol',
            'sector_name': 'Sector',
            'rs_ratio': 'RS-Ratio',
            'rs_momentum': 'RS-Momentum',
            'quadrant': 'Quadrant'
        })

        # Sort by quadrant then RS-Ratio
        quadrant_order = {'🟢 Leading': 1, '🔵 Improving': 2, '🔴 Weakening': 3, '🟡 Lagging': 4}
        display_df['sort_order'] = display_df['Quadrant'].map(quadrant_order)
        display_df = display_df.sort_values(['sort_order', 'RS-Ratio'], ascending=[True, False])
        display_df = display_df.drop('sort_order', axis=1)

        # Format numbers
        display_df['RS-Ratio'] = display_df['RS-Ratio'].apply(lambda x: f"{x:.2f}")
        display_df['RS-Momentum'] = display_df['RS-Momentum'].apply(lambda x: f"{x:.2f}")

        # Calculate appropriate height based on number of rows (35px per row + 38px header)
        table_height = min(len(display_df) * 35 + 38, 500)
        st.dataframe(display_df, width='stretch', hide_index=True, height=table_height)

        # Export button
        st.divider()
        if st.button("📥 Export Data to CSV"):
            from riley.modules.marketdata.export_rrg import export_rrg_sectors

            export_path = Path(__file__).parent.parent / "artifacts" / "rrg" / "rrg_prices_daily.csv"
            export_rrg_sectors(str(export_path), lookback_days=365)
            st.success(f"✅ Exported to {export_path}")

    except Exception as e:
        st.error(f"Error loading RRG data: {e}")
        st.exception(e)


def main():
    """Main app"""
    st.title("Riley Cycles Watch")

    # Sidebar
    st.sidebar.title("Navigation")

    # Component Status
    st.sidebar.subheader("Component Status")

    # Get latest scan date
    latest_scan = db.get_latest_scan_date()
    if not latest_scan:
        st.error("No scan data found in database. Please run a daily scan first.")
        return

    # Cycle Scanner status
    st.sidebar.caption("🔍 Cycle Scanner")
    st.sidebar.success(f"Last: {format_date(latest_scan)}")

    # Get other component statuses from database
    conn = db._get_connection()
    cursor = conn.cursor()

    # askSlim Scraper status
    cursor.execute("""
        SELECT MAX(updated_at) as last_update
        FROM instrument_analysis
        WHERE status = 'ACTIVE'
    """)
    row = cursor.fetchone()
    if row and row[0]:
        scraper_time = pd.to_datetime(row[0]).strftime('%d-%b-%Y %H:%M')
        st.sidebar.caption("📡 askSlim Scraper")
        st.sidebar.success(f"Last: {scraper_time}")
    else:
        st.sidebar.caption("📡 askSlim Scraper")
        st.sidebar.warning("Never run")

    conn.close()

    # Market Data status (from CSV files)
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from riley.modules.marketdata.csv_price_manager import get_price_history_dir

        price_dir = get_price_history_dir()
        csv_file = price_dir / "spy_history.csv"

        if csv_file.exists():
            df_check = pd.read_csv(csv_file)
            last_date = pd.to_datetime(df_check['Date']).max()
            market_date = last_date.strftime('%d-%b-%Y')
            st.sidebar.caption("📈 Market Data")
            st.sidebar.success(f"Last: {market_date}")
        else:
            st.sidebar.caption("📈 Market Data")
            st.sidebar.warning("No CSV data")
    except Exception as e:
        st.sidebar.caption("📈 Market Data")
        st.sidebar.warning(f"Error: {str(e)[:30]}")

    st.sidebar.caption("Use System Status page for manual updates")
    st.sidebar.divider()

    # View selector
    view = st.sidebar.radio(
        "Select View",
        ["TODAY", "DATABASE", "CALENDAR", "RRG"],
        index=0
    )

    # Instrument Search (for TODAY view only)
    # Initialize session state for search selection
    if "today_selected_symbol" not in st.session_state:
        st.session_state["today_selected_symbol"] = None

    selected_instrument = st.session_state["today_selected_symbol"]

    if view == "TODAY":
        st.sidebar.divider()
        st.sidebar.subheader("Instrument Search")

        search_input = st.sidebar.text_input(
            "Enter Symbol",
            placeholder="e.g., PL, ES, BTC",
            key="instrument_search"
        )

        col_search, col_clear = st.sidebar.columns([2, 1])
        with col_search:
            search_button = st.button("Search", width='stretch')
        with col_clear:
            clear_button = st.button("Clear", width='stretch')

        if search_button and search_input:
            # Resolve alias to canonical symbol
            canonical_symbol = db.resolve_symbol(search_input)

            # Check if canonical symbol exists
            all_instruments = db.get_instruments({'active_only': True})
            matches = all_instruments[all_instruments['symbol'].str.upper() == canonical_symbol.upper()]

            if not matches.empty:
                st.session_state["today_selected_symbol"] = matches.iloc[0]['symbol']
                selected_instrument = st.session_state["today_selected_symbol"]
                # Show resolution message if alias was used
                if canonical_symbol.upper() != search_input.strip().upper():
                    st.sidebar.info(f"'{search_input}' → {canonical_symbol}")
            else:
                st.sidebar.error(f"Instrument '{search_input}' not found")

        if clear_button:
            st.session_state["today_selected_symbol"] = None
            selected_instrument = None
            st.rerun()

    # Global filters
    st.sidebar.divider()
    st.sidebar.subheader("Filters")

    groups = db.get_group_names()
    sectors = db.get_sectors()

    group_filter = st.sidebar.selectbox("Group", ["All"] + groups, index=0)
    sector_filter = st.sidebar.selectbox("Sector", ["All"] + sectors, index=0)

    if view == "TODAY":
        status_filter = st.sidebar.selectbox(
            "Status Filter",
            ["All", "ACTIVATED", "PREWINDOW", "OVERLAP"],
            index=0
        )
    else:
        status_filter = None

    # Refresh button (no caching, just rerun)
    if st.sidebar.button("Refresh Data"):
        st.rerun()

    # Build filters dict
    filters = {}
    if group_filter != "All":
        filters['group_name'] = group_filter
    if sector_filter != "All":
        filters['sector'] = sector_filter
    if status_filter and status_filter != "All":
        filters['status_filter'] = status_filter

    # Render selected view
    st.divider()


    if view == "TODAY":
        render_today_view(latest_scan, filters, selected_instrument)
    elif view == "DATABASE":
        render_database_view(filters)
    elif view == "CALENDAR":
        render_calendar_view()
    elif view == "RRG":
        render_rrg_view()


if __name__ == "__main__":
    main()
