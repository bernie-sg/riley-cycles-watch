"""
Calendar Events Service - Build FullCalendar Event JSON

Reads cycle windows and astro events from DB and formats them for FullCalendar.
"""

import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set


# Per-instrument base colors
SYMBOL_COLORS = {
    'ES': '#1f77b4',    # blue
    'BTC': '#ff7f0e',   # orange
    'NQ': '#2ca02c',    # green
    'RTY': '#d62728',   # red
    'HG': '#9467bd',    # purple
    'GC': '#8c564b',    # brown
    'SI': '#e377c2',    # pink
    'PL': '#7f7f7f',    # gray
    'CL': '#bcbd22',    # yellow-green
    'NG': '#17becf',    # cyan
    'ZB': '#aec7e8',    # light blue
    'ZW': '#ffbb78',    # light orange
    'ZC': '#98df8a',    # light green
    'ZS': '#ff9896',    # light red
    'EURUSD': '#c5b0d5', # light purple
    'GBPUSD': '#c49c94', # light brown
    'AUDUSD': '#f7b6d2', # light pink
    'USDJPY': '#c7c7c7', # light gray
    'USDCAD': '#dbdb8d', # light yellow
    'DXY': '#9edae5',   # light cyan
    'XLE': '#393b79',   # dark blue
    'NVDA': '#637939',  # olive
}

DEFAULT_COLOR = '#7f7f7f'  # gray for unknown symbols


def lighten_color(hex_color: str, factor: float = 0.4) -> str:
    """Lighten a hex color by blending with white"""
    # Remove # if present
    hex_color = hex_color.lstrip('#')

    # Convert to RGB
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    # Blend with white
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)

    # Clamp to 0-255
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return f'#{r:02x}{g:02x}{b:02x}'


def darken_color(hex_color: str, factor: float = 0.3) -> str:
    """Darken a hex color"""
    hex_color = hex_color.lstrip('#')

    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)

    r = int(r * (1 - factor))
    g = int(g * (1 - factor))
    b = int(b * (1 - factor))

    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))

    return f'#{r:02x}{g:02x}{b:02x}'


def get_cycle_events(
    db_path: str,
    symbols: Optional[List[str]] = None,
    include_daily: bool = True,
    include_weekly: bool = True,
    include_overlap: bool = True
) -> List[Dict]:
    """
    Get cycle window events from database.

    Args:
        db_path: Path to SQLite database
        symbols: Filter by symbols (None = all)
        include_daily: Include DAILY windows
        include_weekly: Include WEEKLY windows
        include_overlap: Compute and include OVERLAP events

    Returns:
        List of FullCalendar event dicts
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Build query
    query = """
        SELECT
            i.symbol,
            cp.timeframe,
            cp.core_start_label,
            cp.core_end_label,
            cp.median_label
        FROM cycle_projections cp
        JOIN instruments i ON i.instrument_id = cp.instrument_id
        WHERE cp.k = 0
            AND cp.active = 1
            AND i.active = 1
    """

    params = []
    if symbols:
        placeholders = ','.join('?' * len(symbols))
        query += f" AND i.symbol IN ({placeholders})"
        params.extend(symbols)

    query += " ORDER BY i.symbol, cp.timeframe"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    events = []

    # Track windows per symbol for overlap computation
    windows_by_symbol = {}

    # Debug: track ES DAILY
    es_daily_found = False

    for symbol, timeframe, start_label, end_label, median_label in rows:
        # Skip based on filters
        if timeframe == 'DAILY' and not include_daily:
            continue
        if timeframe == 'WEEKLY' and not include_weekly:
            continue

        # Track ES DAILY for assertion
        if symbol == 'ES' and timeframe == 'DAILY':
            es_daily_found = True

        # Parse dates
        start_date = datetime.strptime(start_label, '%Y-%m-%d')
        end_date = datetime.strptime(end_label, '%Y-%m-%d')

        # FullCalendar uses exclusive end for all-day events
        fc_end = end_date + timedelta(days=1)

        # Per-instrument color coding
        base_color = SYMBOL_COLORS.get(symbol, DEFAULT_COLOR)

        if timeframe == 'DAILY':
            # DAILY = lightened base color
            bg_color = lighten_color(base_color, 0.5)
            text_color = darken_color(base_color, 0.2)
        else:  # WEEKLY
            # WEEKLY = medium base color
            bg_color = lighten_color(base_color, 0.2)
            text_color = darken_color(base_color, 0.4)

        event = {
            'title': f'{symbol} • {timeframe}',
            'start': start_label,
            'end': fc_end.strftime('%Y-%m-%d'),
            'allDay': True,
            'backgroundColor': bg_color,
            'borderColor': base_color,
            'textColor': text_color,
            'display': 'block',
            'extendedProps': {
                'symbol': symbol,
                'timeframe': timeframe,
                'median': median_label,
                'kind': 'cycle_window'
            }
        }

        events.append(event)

        # Track for overlap calculation
        if symbol not in windows_by_symbol:
            windows_by_symbol[symbol] = {}
        windows_by_symbol[symbol][timeframe] = {
            'start': start_date,
            'end': end_date,
            'median': median_label
        }

    # Assertion: ES DAILY must be present if ES is in symbols filter
    if symbols is None or 'ES' in symbols:
        if include_daily:
            assert es_daily_found, "ES DAILY window missing from database query results"

    # Compute overlap events
    if include_overlap:
        overlap_events = _compute_overlap_events(windows_by_symbol)
        events.extend(overlap_events)

    return events


def _compute_overlap_events(windows_by_symbol: Dict) -> List[Dict]:
    """
    Compute overlap events where DAILY and WEEKLY windows intersect.

    Args:
        windows_by_symbol: Dict of {symbol: {timeframe: {start, end, median}}}

    Returns:
        List of overlap event dicts
    """
    overlap_events = []

    for symbol, windows in windows_by_symbol.items():
        if 'DAILY' not in windows or 'WEEKLY' not in windows:
            continue

        daily = windows['DAILY']
        weekly = windows['WEEKLY']

        # Find intersection
        overlap_start = max(daily['start'], weekly['start'])
        overlap_end = min(daily['end'], weekly['end'])

        # Check if valid overlap exists
        if overlap_start <= overlap_end:
            # FullCalendar exclusive end
            fc_end = overlap_end + timedelta(days=1)

            # OVERLAP = saturated/dark base color
            base_color = SYMBOL_COLORS.get(symbol, DEFAULT_COLOR)
            overlap_bg = base_color  # Full saturation
            overlap_border = darken_color(base_color, 0.2)
            overlap_text = '#FFFFFF'  # White text on saturated background

            event = {
                'title': f'{symbol} • OVERLAP',
                'start': overlap_start.strftime('%Y-%m-%d'),
                'end': fc_end.strftime('%Y-%m-%d'),
                'allDay': True,
                'backgroundColor': overlap_bg,
                'borderColor': overlap_border,
                'textColor': overlap_text,
                'display': 'block',
                'extendedProps': {
                    'symbol': symbol,
                    'timeframe': 'OVERLAP',
                    'kind': 'overlap'
                },
                'classNames': ['overlap-event']  # Higher z-index via CSS
            }

            overlap_events.append(event)

    return overlap_events


def get_astro_events(
    db_path: str,
    symbols: Optional[List[str]] = None
) -> List[Dict]:
    """
    Get astro events from database.

    Args:
        db_path: Path to SQLite database
        symbols: Filter by symbols (None = all)

    Returns:
        List of FullCalendar event dicts
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    query = """
        SELECT
            i.symbol,
            ae.event_label,
            ae.role,
            ae.name,
            ae.category
        FROM astro_events ae
        JOIN instruments i ON i.instrument_id = ae.instrument_id
        WHERE i.active = 1
    """

    params = []
    if symbols:
        placeholders = ','.join('?' * len(symbols))
        query += f" AND i.symbol IN ({placeholders})"
        params.extend(symbols)

    query += " ORDER BY ae.event_label, i.symbol"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    events = []

    for symbol, event_label, role, name, category in rows:
        # Different styling for PRIMARY vs BACKUP
        if role == 'PRIMARY':
            color = '#FF6B6B'  # Red dot
            class_name = 'astro-primary'
        else:
            color = '#95E1D3'  # Teal dot
            class_name = 'astro-backup'

        title = f'• {symbol}'
        if name:
            title += f' {name}'

        event = {
            'title': title,
            'start': event_label,
            'allDay': True,
            'display': 'list-item',
            'color': color,
            'extendedProps': {
                'symbol': symbol,
                'role': role,
                'name': name,
                'category': category,
                'kind': 'astro'
            },
            'classNames': [class_name]
        }

        events.append(event)

    return events


def build_fullcalendar_events(
    db_path: str,
    symbols: Optional[List[str]] = None,
    include_daily: bool = True,
    include_weekly: bool = True,
    include_overlap: bool = True,
    include_astro: bool = True
) -> List[Dict]:
    """
    Build complete FullCalendar events list.

    Args:
        db_path: Path to SQLite database
        symbols: Filter by symbols (None = all)
        include_daily: Include DAILY cycle windows
        include_weekly: Include WEEKLY cycle windows
        include_overlap: Include OVERLAP events
        include_astro: Include astro events

    Returns:
        List of FullCalendar event dicts
    """
    events = []

    # Add cycle events
    cycle_events = get_cycle_events(
        db_path,
        symbols=symbols,
        include_daily=include_daily,
        include_weekly=include_weekly,
        include_overlap=include_overlap
    )
    events.extend(cycle_events)

    # Add astro events
    if include_astro:
        astro_events = get_astro_events(db_path, symbols=symbols)
        events.extend(astro_events)

    return events


def get_available_symbols(db_path: str) -> List[str]:
    """
    Get list of active symbols with cycle projections.

    Args:
        db_path: Path to SQLite database

    Returns:
        List of symbol strings
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT DISTINCT i.symbol
        FROM instruments i
        JOIN cycle_projections cp ON cp.instrument_id = i.instrument_id
        WHERE i.active = 1
            AND cp.k = 0
            AND cp.active = 1
        ORDER BY i.symbol
    """)

    symbols = [row[0] for row in cursor.fetchall()]
    conn.close()

    return symbols
