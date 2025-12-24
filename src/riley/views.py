"""Cycles Watch views - watchlist snapshots and window countdown"""
import json
from pathlib import Path
from typing import Dict, List, Any
import pandas as pd


def generate_watchlist_snapshot(
    db,
    symbol: str,
    asof_td_label: str,
    notes_limit: int = 3,
    out_root: Path = None
) -> Dict[str, Any]:
    """
    Generate watchlist snapshot for a single instrument.

    Args:
        db: Database instance
        symbol: Canonical symbol
        asof_td_label: As-of trading date label
        notes_limit: Number of recent notes to include
        out_root: Output root directory

    Returns:
        Dict with snapshot data
    """
    # Get instrument info
    aliases = db.get_aliases(symbol)

    # Get calendars
    daily_cal = db.get_daily_calendar(symbol)
    weekly_cal = db.get_weekly_calendar(symbol)

    if not daily_cal:
        return {
            'symbol': symbol,
            'asof_td_label': asof_td_label,
            'status': 'MISSING_CALENDAR',
            'message': 'No daily calendar found'
        }

    # Convert to DataFrame for easier lookup
    df_daily = pd.DataFrame(daily_cal)
    df_weekly = pd.DataFrame(weekly_cal) if weekly_cal else pd.DataFrame()

    # Find asof_td_index
    asof_row = df_daily[df_daily['trading_date_label'] == asof_td_label]
    if asof_row.empty:
        return {
            'symbol': symbol,
            'asof_td_label': asof_td_label,
            'status': 'INVALID_ASOF_DATE',
            'message': f'Date {asof_td_label} not in calendar'
        }

    asof_td_index = int(asof_row.iloc[0]['td_index'])

    # Get cycle specs
    daily_spec = db.get_active_cycle_spec(symbol, 'DAILY')
    weekly_spec = db.get_active_cycle_spec(symbol, 'WEEKLY')

    # Get best projections for asof date
    daily_proj = db.get_best_projection_for_asof(symbol, 'DAILY', asof_td_index) if daily_spec else None
    weekly_proj = None
    asof_tw_index = None

    if weekly_spec and not df_weekly.empty:
        # Find current week index
        week_row = df_weekly[df_weekly['week_end_label'] >= asof_td_label]
        if not week_row.empty:
            asof_tw_index = int(week_row.iloc[0]['tw_index'])
            weekly_proj = db.get_best_projection_for_asof(symbol, 'WEEKLY', asof_tw_index)

    # Build snapshot data
    snapshot = {
        'symbol': symbol,
        'aliases': aliases,
        'asof_td_label': asof_td_label,
        'asof_td_index': asof_td_index,
        'asof_tw_index': asof_tw_index,
        'cycle_specs': {},
        'cycle_proximity': {},
        'overlap': {},
        'notes': []
    }

    # Cycle specs
    if daily_spec:
        snapshot['cycle_specs']['DAILY'] = {
            'version': daily_spec['version'],
            'length': daily_spec['cycle_length_bars'],
            'anchor': daily_spec['anchor_input_date_label']
        }

    if weekly_spec:
        snapshot['cycle_specs']['WEEKLY'] = {
            'version': weekly_spec['version'],
            'length': weekly_spec['cycle_length_bars'],
            'anchor': weekly_spec['anchor_input_date_label']
        }

    # Cycle proximity - DAILY
    if daily_proj:
        status, days_to_core = _compute_status(asof_td_index, daily_proj)
        snapshot['cycle_proximity']['DAILY'] = {
            'status': status,
            'prewindow_start': _index_to_label(df_daily, daily_proj['prewindow_start_index']),
            'prewindow_end': _index_to_label(df_daily, daily_proj['prewindow_end_index']),
            'core_start': _index_to_label(df_daily, daily_proj['core_start_index']),
            'core_end': _index_to_label(df_daily, daily_proj['core_end_index']),
            'median': daily_proj['median_label'],
            'days_to_core_start': days_to_core
        }
    else:
        snapshot['cycle_proximity']['DAILY'] = {'status': 'NONE'}

    # Cycle proximity - WEEKLY
    if weekly_proj and asof_tw_index is not None:
        status, weeks_to_core = _compute_status(asof_tw_index, weekly_proj)
        snapshot['cycle_proximity']['WEEKLY'] = {
            'status': status,
            'prewindow_start': _index_to_label(df_weekly, weekly_proj['prewindow_start_index']),
            'prewindow_end': _index_to_label(df_weekly, weekly_proj['prewindow_end_index']),
            'core_start': _index_to_label(df_weekly, weekly_proj['core_start_index']),
            'core_end': _index_to_label(df_weekly, weekly_proj['core_end_index']),
            'median': weekly_proj['median_label'],
            'weeks_to_core_start': weeks_to_core
        }
    else:
        snapshot['cycle_proximity']['WEEKLY'] = {'status': 'NONE'}

    # Overlap check
    if daily_proj and weekly_proj:
        daily_start = daily_proj['core_start_index']
        daily_end = daily_proj['core_end_index']
        weekly_start_label = _index_to_label(df_weekly, weekly_proj['core_start_index'])
        weekly_end_label = _index_to_label(df_weekly, weekly_proj['core_end_index'])

        # Convert weekly labels to daily indices
        weekly_start_td = df_daily[df_daily['trading_date_label'] >= weekly_start_label].iloc[0]['td_index'] if not df_daily[df_daily['trading_date_label'] >= weekly_start_label].empty else None
        weekly_end_td = df_daily[df_daily['trading_date_label'] <= weekly_end_label].iloc[-1]['td_index'] if not df_daily[df_daily['trading_date_label'] <= weekly_end_label].empty else None

        if weekly_start_td and weekly_end_td:
            overlaps = not (daily_end < weekly_start_td or daily_start > weekly_end_td)
            snapshot['overlap'] = {
                'daily_core_overlaps_weekly_core': overlaps,
                'daily_core': f"{_index_to_label(df_daily, daily_start)} → {_index_to_label(df_daily, daily_end)}",
                'weekly_core': f"{weekly_start_label} → {weekly_end_label}"
            }

    # Notes
    notes = db.get_latest_notes(symbol, asof_td_label, notes_limit)
    snapshot['notes'] = [
        {
            'author': n['author'],
            'note_type': n['note_type'],
            'scope': n['timeframe_scope'],
            'price_reference': n['price_reference'],
            'bullets': json.loads(n['bullets_json']),
            'asof': n['asof_td_label']
        }
        for n in notes
    ]

    # Astro events
    astro_data = db.list_upcoming_astro(symbol, asof_td_index, horizon_td=15)
    snapshot['astro'] = {
        'next_primary': None,
        'backup_events': []
    }

    if astro_data['next_primary']:
        primary = astro_data['next_primary']
        days_to_primary = primary['td_index'] - asof_td_index
        snapshot['astro']['next_primary'] = {
            'date': primary['event_label'],
            't_minus_td': days_to_primary,
            'name': primary.get('name'),
            'category': primary.get('category'),
            'confidence': primary.get('confidence')
        }

    if astro_data['backup_events']:
        for backup in astro_data['backup_events'][:3]:  # Limit to 3
            days_to_backup = backup['td_index'] - asof_td_index
            snapshot['astro']['backup_events'].append({
                'date': backup['event_label'],
                't_minus_td': days_to_backup,
                'name': backup.get('name'),
                'category': backup.get('category'),
                'confidence': backup.get('confidence')
            })

    # Write outputs if out_root provided
    if out_root:
        out_dir = out_root / "watchlist" / symbol / asof_td_label
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(out_dir / "snapshot.json", 'w') as f:
            json.dump(snapshot, f, indent=2)

        # Write Markdown
        md_content = _format_snapshot_markdown(snapshot)
        with open(out_dir / "snapshot.md", 'w') as f:
            f.write(md_content)

    return snapshot


def generate_window_countdown(
    db,
    asof_td_label: str,
    horizon_td: int = 15,
    horizon_tw: int = 6,
    out_root: Path = None
) -> Dict[str, Any]:
    """
    Generate window countdown view across all instruments.

    Args:
        db: Database instance
        asof_td_label: As-of trading date label
        horizon_td: Daily horizon in trading days
        horizon_tw: Weekly horizon in trading weeks
        out_root: Output root directory

    Returns:
        Dict with countdown data
    """
    instruments = db.list_canonical_instruments()

    countdown_rows = []

    for inst in instruments:
        symbol = inst['symbol']

        # Get calendars
        daily_cal = db.get_daily_calendar(symbol)
        if not daily_cal:
            continue

        df_daily = pd.DataFrame(daily_cal)
        asof_row = df_daily[df_daily['trading_date_label'] == asof_td_label]
        if asof_row.empty:
            continue

        asof_td_index = int(asof_row.iloc[0]['td_index'])

        # Get daily projection
        daily_proj = db.get_best_projection_for_asof(symbol, 'DAILY', asof_td_index)
        daily_status = 'NONE'
        daily_core_start_label = None
        daily_core_end_label = None
        daily_median_label = None
        days_to_daily_core = None

        if daily_proj:
            daily_status, days_to_daily_core = _compute_status(asof_td_index, daily_proj)
            daily_core_start_label = _index_to_label(df_daily, daily_proj['core_start_index'])
            daily_core_end_label = _index_to_label(df_daily, daily_proj['core_end_index'])
            daily_median_label = daily_proj['median_label']

        # Get weekly projection
        weekly_cal = db.get_weekly_calendar(symbol)
        weekly_proj = None
        weekly_status = 'NONE'
        weekly_core_start_label = None
        weekly_core_end_label = None
        weekly_median_label = None
        weeks_to_weekly_core = None
        df_weekly = None

        if weekly_cal:
            df_weekly = pd.DataFrame(weekly_cal)
            week_row = df_weekly[df_weekly['week_end_label'] >= asof_td_label]
            if not week_row.empty:
                asof_tw_index = int(week_row.iloc[0]['tw_index'])
                weekly_proj = db.get_best_projection_for_asof(symbol, 'WEEKLY', asof_tw_index)

                if weekly_proj:
                    weekly_status, weeks_to_weekly_core = _compute_status(asof_tw_index, weekly_proj)
                    weekly_core_start_label = _index_to_label(df_weekly, weekly_proj['core_start_index'])
                    weekly_core_end_label = _index_to_label(df_weekly, weekly_proj['core_end_index'])
                    weekly_median_label = weekly_proj['median_label']

        # Get astro events
        astro_data = db.list_upcoming_astro(symbol, asof_td_index, horizon_td=horizon_td)
        primary_astro_label = None
        backup_astro_label = None

        if astro_data['next_primary']:
            primary = astro_data['next_primary']
            days_to_primary = primary['td_index'] - asof_td_index
            primary_astro_label = f"{primary['event_label']} (T-{days_to_primary})"

        if astro_data['backup_events']:
            backup = astro_data['backup_events'][0]  # Next backup
            days_to_backup = backup['td_index'] - asof_td_index
            backup_astro_label = f"{backup['event_label']} (T-{days_to_backup})"

        # Compute priority score
        priority_score = 0
        if daily_status == 'IN_WINDOW' and weekly_status == 'IN_WINDOW':
            priority_score += 100
        elif (daily_status == 'IN_WINDOW' and weekly_status == 'PREWINDOW') or \
             (daily_status == 'PREWINDOW' and weekly_status == 'IN_WINDOW'):
            priority_score += 60
        elif daily_status == 'IN_WINDOW' or weekly_status == 'IN_WINDOW':
            priority_score += 30
        elif daily_status == 'PREWINDOW' or weekly_status == 'PREWINDOW':
            priority_score += 10

        # Astro priority scoring
        if astro_data['next_primary'] and daily_proj:
            primary_td = astro_data['next_primary']['td_index']
            # Check if primary falls in daily prewindow or core
            if daily_proj['prewindow_start_index'] <= primary_td <= daily_proj['core_end_index']:
                priority_score += 15

        if astro_data['next_primary'] and weekly_proj:
            primary_td = astro_data['next_primary']['td_index']
            # Get weekly window bounds in td_index
            weekly_pre_start_label = _index_to_label(df_weekly, weekly_proj['prewindow_start_index'])
            weekly_core_end_label = _index_to_label(df_weekly, weekly_proj['core_end_index'])
            weekly_pre_start_td = df_daily[df_daily['trading_date_label'] >= weekly_pre_start_label].iloc[0]['td_index'] if not df_daily[df_daily['trading_date_label'] >= weekly_pre_start_label].empty else None
            weekly_core_end_td = df_daily[df_daily['trading_date_label'] <= weekly_core_end_label].iloc[-1]['td_index'] if not df_daily[df_daily['trading_date_label'] <= weekly_core_end_label].empty else None
            if weekly_pre_start_td and weekly_core_end_td:
                if weekly_pre_start_td <= primary_td <= weekly_core_end_td:
                    priority_score += 10

        # Check if any backup falls in any core window
        for backup in astro_data['backup_events']:
            backup_td = backup['td_index']
            in_daily_core = daily_proj and (daily_proj['core_start_index'] <= backup_td <= daily_proj['core_end_index'])
            in_weekly_core = False
            if weekly_proj:
                weekly_core_start_label = _index_to_label(df_weekly, weekly_proj['core_start_index'])
                weekly_core_end_label = _index_to_label(df_weekly, weekly_proj['core_end_index'])
                weekly_core_start_td = df_daily[df_daily['trading_date_label'] >= weekly_core_start_label].iloc[0]['td_index'] if not df_daily[df_daily['trading_date_label'] >= weekly_core_start_label].empty else None
                weekly_core_end_td = df_daily[df_daily['trading_date_label'] <= weekly_core_end_label].iloc[-1]['td_index'] if not df_daily[df_daily['trading_date_label'] <= weekly_core_end_label].empty else None
                if weekly_core_start_td and weekly_core_end_td:
                    in_weekly_core = weekly_core_start_td <= backup_td <= weekly_core_end_td
            if in_daily_core or in_weekly_core:
                priority_score += 5
                break  # Only add once

        countdown_rows.append({
            'symbol': symbol,
            'daily_status': daily_status,
            'daily_core_start': daily_core_start_label,
            'daily_core_end': daily_core_end_label,
            'daily_median': daily_median_label,
            'days_to_core': days_to_daily_core,
            'weekly_status': weekly_status,
            'weekly_core_start': weekly_core_start_label,
            'weekly_core_end': weekly_core_end_label,
            'weekly_median': weekly_median_label,
            'weeks_to_core': weeks_to_weekly_core,
            'primary_astro': primary_astro_label if primary_astro_label else '—',
            'backup_astro': backup_astro_label if backup_astro_label else '—',
            'priority_score': priority_score
        })

    # Sort by priority
    countdown_rows.sort(key=lambda r: (
        -r['priority_score'],
        r['days_to_core'] if r['days_to_core'] is not None else 999,
        r['weeks_to_core'] if r['weeks_to_core'] is not None else 999
    ))

    countdown = {
        'asof_td_label': asof_td_label,
        'horizon_td': horizon_td,
        'horizon_tw': horizon_tw,
        'rows': countdown_rows
    }

    # Write outputs if out_root provided
    if out_root:
        out_dir = out_root / "countdown" / asof_td_label
        out_dir.mkdir(parents=True, exist_ok=True)

        # Write JSON
        with open(out_dir / "countdown.json", 'w') as f:
            json.dump(countdown, f, indent=2)

        # Write Markdown
        md_content = _format_countdown_markdown(countdown)
        with open(out_dir / "countdown.md", 'w') as f:
            f.write(md_content)

    return countdown


def _compute_status(asof_index: int, projection: dict) -> tuple:
    """Compute status and distance to core start"""
    pre_start = projection['prewindow_start_index']
    pre_end = projection['prewindow_end_index']
    core_start = projection['core_start_index']
    core_end = projection['core_end_index']

    if pre_start <= asof_index <= pre_end:
        return 'PREWINDOW', core_start - asof_index
    elif core_start <= asof_index <= core_end:
        return 'IN_WINDOW', 0
    elif asof_index > core_end:
        return 'POST', None
    else:
        return 'NONE', core_start - asof_index if asof_index < core_start else None


def _index_to_label(df: pd.DataFrame, index: int) -> str:
    """Convert index to label"""
    if 'td_index' in df.columns:
        col = 'td_index'
        label_col = 'trading_date_label'
    else:
        col = 'tw_index'
        label_col = 'week_end_label'

    row = df[df[col] == index]
    if row.empty:
        return f"[{index}]"
    return row.iloc[0][label_col]


def _format_snapshot_markdown(snapshot: Dict[str, Any]) -> str:
    """Format watchlist snapshot as Markdown"""
    lines = []
    lines.append(f"# Watchlist Snapshot — {snapshot['symbol']}")
    lines.append("")

    if snapshot.get('status') in ['MISSING_CALENDAR', 'INVALID_ASOF_DATE']:
        lines.append(f"**Status:** {snapshot['status']}")
        lines.append(f"**Message:** {snapshot.get('message', '')}")
        return "\n".join(lines)

    lines.append(f"**Instrument:** {snapshot['symbol']}")
    if snapshot.get('aliases'):
        lines.append(f"**Aliases:** {', '.join(snapshot['aliases'])}")
    lines.append(f"**As-of Date:** {snapshot['asof_td_label']}")
    lines.append("")

    # Cycle specs
    lines.append("## Cycle Specifications")
    specs = snapshot.get('cycle_specs', {})
    if specs.get('DAILY'):
        d = specs['DAILY']
        lines.append(f"- **DAILY** v{d['version']}: length={d['length']}, anchor={d['anchor']}")
    if specs.get('WEEKLY'):
        w = specs['WEEKLY']
        lines.append(f"- **WEEKLY** v{w['version']}: length={w['length']}, anchor={w['anchor']}")
    lines.append("")

    # Cycle proximity
    lines.append("## Cycle Proximity")
    prox = snapshot.get('cycle_proximity', {})

    if prox.get('DAILY') and prox['DAILY']['status'] != 'NONE':
        d = prox['DAILY']
        lines.append(f"### DAILY")
        lines.append(f"- **Status:** {d['status']}")
        lines.append(f"- **Prewindow:** {d['prewindow_start']} → {d['prewindow_end']}")
        lines.append(f"- **Core:** {d['core_start']} → {d['core_end']}")
        lines.append(f"- **Median:** {d['median']}")
        if d.get('days_to_core_start') is not None:
            lines.append(f"- **Days to Core Start:** {d['days_to_core_start']}")
        lines.append("")

    if prox.get('WEEKLY') and prox['WEEKLY']['status'] != 'NONE':
        w = prox['WEEKLY']
        lines.append(f"### WEEKLY")
        lines.append(f"- **Status:** {w['status']}")
        lines.append(f"- **Prewindow:** {w['prewindow_start']} → {w['prewindow_end']}")
        lines.append(f"- **Core:** {w['core_start']} → {w['core_end']}")
        lines.append(f"- **Median:** {w['median']}")
        if w.get('weeks_to_core_start') is not None:
            lines.append(f"- **Weeks to Core Start:** {w['weeks_to_core_start']}")
        lines.append("")

    # Overlap
    overlap = snapshot.get('overlap', {})
    if overlap:
        lines.append("## Overlap Analysis")
        lines.append(f"- **Daily Core Overlaps Weekly Core:** {overlap.get('daily_core_overlaps_weekly_core', False)}")
        if overlap.get('daily_core'):
            lines.append(f"- **Daily Core Window:** {overlap['daily_core']}")
        if overlap.get('weekly_core'):
            lines.append(f"- **Weekly Core Window:** {overlap['weekly_core']}")
        lines.append("")

    # Notes
    notes = snapshot.get('notes', [])
    if notes:
        lines.append("## Recent Desk Notes")
        for note in notes:
            lines.append(f"### {note['asof']} — {note['author']} ({note['note_type']})")
            lines.append(f"- **Scope:** {note['scope']}")
            lines.append(f"- **Price Reference:** {note['price_reference']}")
            lines.append("- **Bullets:**")
            for bullet in note['bullets']:
                lines.append(f"  - {bullet}")
            lines.append("")

    # Astro events
    astro = snapshot.get('astro', {})
    if astro.get('next_primary') or astro.get('backup_events'):
        lines.append("## Astro Events")

        if astro.get('next_primary'):
            p = astro['next_primary']
            lines.append(f"### Next PRIMARY")
            lines.append(f"- **Date:** {p['date']} (T-{p['t_minus_td']} TD)")
            if p.get('name'):
                lines.append(f"- **Name:** {p['name']}")
            if p.get('category'):
                lines.append(f"- **Category:** {p['category']}")
            if p.get('confidence'):
                lines.append(f"- **Confidence:** {p['confidence']}")
            lines.append("")

        if astro.get('backup_events'):
            lines.append("### BACKUP Events")
            for b in astro['backup_events']:
                name_str = f" — {b['name']}" if b.get('name') else ""
                cat_str = f" [{b['category']}]" if b.get('category') else ""
                lines.append(f"- **{b['date']} (T-{b['t_minus_td']} TD)**{name_str}{cat_str}")
            lines.append("")
    else:
        lines.append("## Astro Events")
        lines.append("*None in next horizon*")
        lines.append("")

    return "\n".join(lines)


def _format_countdown_markdown(countdown: Dict[str, Any]) -> str:
    """Format window countdown as Markdown"""
    lines = []
    lines.append(f"# Window Countdown — {countdown['asof_td_label']}")
    lines.append("")
    lines.append(f"**Horizon:** Next {countdown['horizon_td']} trading days, {countdown['horizon_tw']} trading weeks")
    lines.append("")

    # Table header
    lines.append("| Symbol | Daily Status | Days to Core | Weekly Status | Weeks to Core | Primary Astro (TD) | Backup Astro (TD) | Priority |")
    lines.append("|--------|-------------|--------------|---------------|---------------|-------------------|------------------|----------|")

    for row in countdown['rows']:
        days_str = str(row['days_to_core']) if row['days_to_core'] is not None else "-"
        weeks_str = str(row['weeks_to_core']) if row['weeks_to_core'] is not None else "-"

        lines.append(
            f"| {row['symbol']} | {row['daily_status']} | {days_str} | "
            f"{row['weekly_status']} | {weeks_str} | {row['primary_astro']} | "
            f"{row['backup_astro']} | {row['priority_score']} |"
        )

    return "\n".join(lines)
