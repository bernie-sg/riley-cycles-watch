"""Database helper layer for Streamlit UI - DISPLAY DB VALUES ONLY"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
from config import get_db_path


class CyclesDB:
    """Database access layer - NO COMPUTATION, DISPLAY ONLY"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = get_db_path()
        self.db_path = str(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def resolve_symbol(self, input_symbol: str) -> str:
        """
        Resolve an alias to its canonical symbol.

        Args:
            input_symbol: Symbol to resolve (can be alias or canonical)

        Returns:
            Canonical symbol (or input if no match found)
        """
        if not input_symbol:
            return input_symbol

        s = input_symbol.upper().strip()
        conn = self._get_connection()
        cursor = conn.cursor()

        # First check if it's already a canonical symbol
        cursor.execute("SELECT symbol FROM instruments WHERE symbol = ?", (s,))
        if cursor.fetchone():
            conn.close()
            return s

        # Check if it's an alias
        cursor.execute("SELECT symbol, aliases FROM instruments WHERE aliases IS NOT NULL")
        for row in cursor.fetchall():
            if row['aliases']:
                aliases = [a.strip().upper() for a in row['aliases'].split(',')]
                if s in aliases:
                    canonical = row['symbol']
                    conn.close()
                    return canonical

        conn.close()
        # Return original if no match found
        return s

    def get_latest_scan_date(self) -> Optional[str]:
        """Get today's date from trading calendar"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Use a reasonable default "today" - can be overridden
        cursor.execute("""
            SELECT MAX(trading_date_label) as latest_date
            FROM trading_calendar_daily
            WHERE trading_date_label <= date('now')
        """)
        row = cursor.fetchone()
        conn.close()

        # If nothing found, use absolute max
        if not row or not row['latest_date']:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT MAX(trading_date_label) FROM trading_calendar_daily")
            row = cursor.fetchone()
            conn.close()

        return row['latest_date'] if row else '2025-12-23'

    def get_today_rows(self, scan_date: str, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get instrument status - COMPUTED FROM STORED DATES ONLY"""
        filters = filters or {}

        conn = self._get_connection()

        # Build query - use stored date labels ONLY
        query = """
            WITH daily_cycles AS (
                SELECT
                    i.instrument_id,
                    cs.median_input_date_label as daily_median,
                    cp.core_start_label as daily_start,
                    cp.core_end_label as daily_end,
                    cp.prewindow_start_label as daily_pre_start,
                    cp.prewindow_end_label as daily_pre_end,
                    cp.core_start_td_index as daily_core_start_index
                FROM instruments i
                JOIN cycle_specs cs ON cs.instrument_id = i.instrument_id
                JOIN cycle_projections cp ON cp.cycle_id = cs.cycle_id
                WHERE cs.timeframe = 'DAILY'
                    AND cs.status = 'ACTIVE'
                    AND cp.k = 0
                    AND cp.active = 1
                    AND i.active = 1
            ),
            weekly_cycles AS (
                SELECT
                    i.instrument_id,
                    cs.median_input_date_label as weekly_median,
                    cp.core_start_label as weekly_start,
                    cp.core_end_label as weekly_end,
                    cp.prewindow_start_label as weekly_pre_start,
                    cp.prewindow_end_label as weekly_pre_end,
                    cp.core_start_tw_index as weekly_core_start_index
                FROM instruments i
                JOIN cycle_specs cs ON cs.instrument_id = i.instrument_id
                JOIN cycle_projections cp ON cp.cycle_id = cs.cycle_id
                WHERE cs.timeframe = 'WEEKLY'
                    AND cs.status = 'ACTIVE'
                    AND cp.k = 0
                    AND cp.active = 1
                    AND i.active = 1
            )
            SELECT
                i.symbol,
                i.name,

                -- DAILY status (simple date comparison)
                CASE
                    WHEN d.daily_pre_start IS NOT NULL AND d.daily_pre_end IS NOT NULL
                        AND ? BETWEEN d.daily_pre_start AND d.daily_pre_end
                    THEN 'PREWINDOW'
                    WHEN d.daily_start IS NOT NULL AND d.daily_end IS NOT NULL
                        AND ? BETWEEN d.daily_start AND d.daily_end
                    THEN 'ACTIVATED'
                    ELSE 'NONE'
                END as daily_status,

                -- WEEKLY status (simple date comparison)
                CASE
                    WHEN w.weekly_pre_start IS NOT NULL AND w.weekly_pre_end IS NOT NULL
                        AND ? BETWEEN w.weekly_pre_start AND w.weekly_pre_end
                    THEN 'PREWINDOW'
                    WHEN w.weekly_start IS NOT NULL AND w.weekly_end IS NOT NULL
                        AND ? BETWEEN w.weekly_start AND w.weekly_end
                    THEN 'ACTIVATED'
                    ELSE 'NONE'
                END as weekly_status,

                -- Days to daily window start (bar-based using trading_calendar_daily)
                CASE
                    WHEN d.daily_start IS NULL THEN NULL
                    WHEN ? < d.daily_start THEN (
                        SELECT d.daily_core_start_index - tcd.td_index
                        FROM trading_calendar_daily tcd
                        WHERE tcd.instrument_id = i.instrument_id
                          AND tcd.trading_date_label = ?
                    )
                    WHEN ? BETWEEN d.daily_start AND d.daily_end THEN 0
                    ELSE NULL
                END as days_to_daily_core_start,

                -- Weeks to weekly window start (bar-based using trading_calendar_weekly)
                CASE
                    WHEN w.weekly_start IS NULL THEN NULL
                    WHEN ? < w.weekly_start THEN (
                        SELECT w.weekly_core_start_index - tcw.tw_index
                        FROM trading_calendar_weekly tcw
                        WHERE tcw.instrument_id = i.instrument_id
                          AND tcw.week_end_label >= ?
                        ORDER BY tcw.tw_index ASC
                        LIMIT 1
                    )
                    WHEN ? BETWEEN w.weekly_start AND w.weekly_end THEN 0
                    ELSE NULL
                END as weeks_to_weekly_core_start,

                -- Overlap flag (STRICT: both must be ACTIVATED and overlap)
                -- Only 1 when TODAY is within BOTH core windows
                CASE
                    WHEN d.daily_start IS NULL OR d.daily_end IS NULL THEN 0
                    WHEN w.weekly_start IS NULL OR w.weekly_end IS NULL THEN 0
                    WHEN ? BETWEEN d.daily_start AND d.daily_end
                        AND ? BETWEEN w.weekly_start AND w.weekly_end
                    THEN 1
                    ELSE 0
                END as overlap_flag,

                -- Store raw dates for debug
                d.daily_median,
                d.daily_start,
                d.daily_end,
                w.weekly_median,
                w.weekly_start,
                w.weekly_end

            FROM instruments i
            LEFT JOIN daily_cycles d ON d.instrument_id = i.instrument_id
            LEFT JOIN weekly_cycles w ON w.instrument_id = i.instrument_id
            WHERE i.active = 1
                AND i.role = 'CANONICAL'
        """

        params = [
            scan_date, scan_date,  # DAILY status (2 params)
            scan_date, scan_date,  # WEEKLY status (2 params)
            scan_date, scan_date, scan_date,  # days to daily (3 params: compare, lookup, compare)
            scan_date, scan_date, scan_date,  # weeks to weekly (3 params: compare, lookup, compare)
            scan_date, scan_date,  # overlap_flag (2 params)
        ]

        # Add filters
        # Note: group_name column doesn't exist in current schema
        # if filters.get('group_name'):
        #     query += " AND i.group_name = ?"
        #     params.append(filters['group_name'])

        # Note: sector column doesn't exist in current schema
        # if filters.get('sector'):
        #     query += " AND i.sector = ?"
        #     params.append(filters['sector'])

        # Status filter
        status_filter_applied = False
        if filters.get('status_filter'):
            status = filters['status_filter']
            if status == 'ACTIVATED':
                query += " AND (daily_status = 'ACTIVATED' OR weekly_status = 'ACTIVATED')"
                status_filter_applied = True
            elif status == 'PREWINDOW':
                query += " AND (daily_status = 'PREWINDOW' OR weekly_status = 'PREWINDOW')"
                status_filter_applied = True
            elif status == 'OVERLAP':
                query += " AND overlap_flag = 1"
                status_filter_applied = True

        # Order and limit
        query += " ORDER BY i.symbol LIMIT 50"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def get_instrument_detail(self, symbol: str, scan_date: str) -> Dict[str, Any]:
        """Get instrument details - DISPLAY STORED VALUES ONLY"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get instrument
        cursor.execute("SELECT * FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        instrument = dict(row) if row else {}

        if not instrument:
            conn.close()
            return {
                'instrument': {},
                'scan_row': {},
                'notes': [],
                'astro_events': [],
                'cycle_specs': []
            }

        instrument_id = instrument['instrument_id']

        # Get cycle specs with stored dates and key levels
        cursor.execute("""
            SELECT
                cs.timeframe,
                cs.median_input_date_label,
                cs.cycle_length_bars,
                cs.support_level,
                cs.resistance_level,
                cp.median_label,
                cp.core_start_label as window_start_date,
                cp.core_end_label as window_end_date,
                cp.prewindow_start_label,
                cp.prewindow_end_label,
                cp.version
            FROM cycle_specs cs
            JOIN cycle_projections cp ON cp.cycle_id = cs.cycle_id
            WHERE cs.instrument_id = ?
                AND cs.status = 'ACTIVE'
                AND cp.k = 0
                AND cp.active = 1
            ORDER BY cs.timeframe DESC
        """, (instrument_id,))
        cycle_specs = [dict(row) for row in cursor.fetchall()]

        # Get instrument analysis (directional bias and video URL)
        cursor.execute("""
            SELECT directional_bias, video_url
            FROM instrument_analysis
            WHERE instrument_id = ? AND status = 'ACTIVE'
            ORDER BY version DESC
            LIMIT 1
        """, (instrument_id,))
        analysis_row = cursor.fetchone()
        analysis = dict(analysis_row) if analysis_row else {'directional_bias': None, 'video_url': None}

        # Compute simple status
        scan_row = {}
        for spec in cycle_specs:
            if spec['timeframe'] == 'DAILY':
                if spec['prewindow_start_label'] and spec['prewindow_end_label']:
                    if spec['prewindow_start_label'] <= scan_date <= spec['prewindow_end_label']:
                        scan_row['daily_status'] = 'PREWINDOW'
                    elif spec['window_start_date'] <= scan_date <= spec['window_end_date']:
                        scan_row['daily_status'] = 'ACTIVATED'
                    else:
                        scan_row['daily_status'] = 'NONE'
                else:
                    scan_row['daily_status'] = 'NONE'
            elif spec['timeframe'] == 'WEEKLY':
                if spec['prewindow_start_label'] and spec['prewindow_end_label']:
                    if spec['prewindow_start_label'] <= scan_date <= spec['prewindow_end_label']:
                        scan_row['weekly_status'] = 'PREWINDOW'
                    elif spec['window_start_date'] <= scan_date <= spec['window_end_date']:
                        scan_row['weekly_status'] = 'ACTIVATED'
                    else:
                        scan_row['weekly_status'] = 'NONE'
                else:
                    scan_row['weekly_status'] = 'NONE'

        # Compute overlap_flag (STRICT: both must be ACTIVATED)
        daily_spec = next((s for s in cycle_specs if s['timeframe'] == 'DAILY'), None)
        weekly_spec = next((s for s in cycle_specs if s['timeframe'] == 'WEEKLY'), None)

        scan_row['overlap_flag'] = 0
        if (daily_spec and weekly_spec and
            daily_spec.get('window_start_date') and daily_spec.get('window_end_date') and
            weekly_spec.get('window_start_date') and weekly_spec.get('window_end_date')):
            # Check if scan_date is in BOTH windows
            in_daily = daily_spec['window_start_date'] <= scan_date <= daily_spec['window_end_date']
            in_weekly = weekly_spec['window_start_date'] <= scan_date <= weekly_spec['window_end_date']
            if in_daily and in_weekly:
                scan_row['overlap_flag'] = 1

        # Get desk notes
        cursor.execute("""
            SELECT * FROM desk_notes
            WHERE instrument_id = ?
            ORDER BY asof_td_label DESC
            LIMIT 3
        """, (instrument_id,))
        notes = [dict(row) for row in cursor.fetchall()]

        # Get astro events (DEDUPLICATED)
        cursor.execute("""
            SELECT DISTINCT
                event_label,
                role,
                name,
                category
            FROM astro_events
            WHERE instrument_id = ?
                AND event_label >= ?
            ORDER BY event_label
            LIMIT 5
        """, (instrument_id, scan_date))
        astro_events = [dict(row) for row in cursor.fetchall()]

        conn.close()

        return {
            'instrument': instrument,
            'scan_row': scan_row,
            'notes': notes,
            'astro_events': astro_events,
            'cycle_specs': cycle_specs,
            'analysis': analysis
        }

    def get_countdown_rows(self, scan_date: str, horizon_days: int = 30) -> pd.DataFrame:
        """Get countdown view - NOT IMPLEMENTED YET"""
        return pd.DataFrame()

    def get_instruments(self, filters: Dict[str, Any] = None) -> pd.DataFrame:
        """Get all instruments"""
        filters = filters or {}

        conn = self._get_connection()

        query = """
            SELECT
                symbol,
                name,
                role,
                canonical_symbol,
                active,
                notes as aliases
            FROM instruments
            WHERE 1=1
        """

        params = []

        if filters.get('active_only'):
            query += " AND active = 1"

        # Note: group_name, sector, and other taxonomy columns don't exist in current schema
        # if filters.get('group_name'):
        #     query += " AND group_name = ?"
        #     params.append(filters['group_name'])

        # if filters.get('sector'):
        #     query += " AND sector = ?"
        #     params.append(filters['sector'])

        query += " ORDER BY role, symbol"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()
        return df

    def update_instrument_taxonomy(self, symbol: str, fields: Dict[str, Any]) -> bool:
        """Update instrument taxonomy and aliases"""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Note: Only active and notes exist in current schema
        allowed_fields = ['active', 'notes']

        set_clause = []
        params = []

        for field, value in fields.items():
            if field in allowed_fields:
                set_clause.append(f"{field} = ?")
                params.append(value)

        if not set_clause:
            conn.close()
            return False

        params.append(symbol)
        query = f"UPDATE instruments SET {', '.join(set_clause)} WHERE symbol = ?"

        cursor.execute(query, params)
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success

    def get_group_names(self) -> List[str]:
        """Get distinct group names"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT group_name FROM instruments WHERE group_name IS NOT NULL ORDER BY group_name")
            groups = [row[0] for row in cursor.fetchall()]
        except:
            # Column doesn't exist, return empty list
            groups = []
        conn.close()
        return groups

    def get_sectors(self) -> List[str]:
        """Get distinct sectors"""
        conn = self._get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT DISTINCT sector FROM instruments WHERE sector IS NOT NULL ORDER BY sector")
            sectors = [row[0] for row in cursor.fetchall()]
        except:
            # Column doesn't exist, return empty list
            sectors = []
        conn.close()
        return sectors

    def get_next_astro_for_symbol(self, symbol: str, scan_date: str, role: str = 'PRIMARY') -> Optional[Dict[str, Any]]:
        """Get next astro event"""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT ae.event_label, ae.role, ae.name, ae.category, i.symbol
            FROM astro_events ae
            JOIN instruments i ON ae.instrument_id = i.instrument_id
            WHERE i.symbol = ?
                AND ae.role = ?
                AND ae.event_label >= ?
            ORDER BY ae.event_label
            LIMIT 1
        """, (symbol, role, scan_date))

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    # ========================================================================
    # FULL INSTRUMENT EDITOR - Backend Functions
    # ========================================================================

    def get_instrument_full(self, symbol: str) -> Dict[str, Any]:
        """
        Get complete instrument data for editing.

        Returns:
            - instrument: metadata (symbol, name, active, notes)
            - daily_cycle: {median, bars, window_start, window_end}
            - weekly_cycle: {median, bars, window_start, window_end}
            - astro: {primary_date, backup_date}
            - desk_note: {text, updated_at}
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get instrument metadata
        cursor.execute("""
            SELECT instrument_id, symbol, name, active, notes
            FROM instruments
            WHERE symbol = ? AND role = 'CANONICAL'
        """, (symbol,))
        row = cursor.fetchone()

        if not row:
            conn.close()
            return {'error': f'Instrument {symbol} not found'}

        instrument = dict(row)
        instrument_id = instrument['instrument_id']

        # Get DAILY cycle
        cursor.execute("""
            SELECT
                cs.median_input_date_label as median,
                cs.cycle_length_bars as bars,
                cp.median_label as computed_median,
                cp.core_start_label as window_start,
                cp.core_end_label as window_end
            FROM cycle_specs cs
            LEFT JOIN cycle_projections cp
                ON cp.instrument_id = cs.instrument_id
                AND cp.timeframe = cs.timeframe
                AND cp.version = cs.version
                AND cp.k = 0
                AND cp.active = 1
            WHERE cs.instrument_id = ?
                AND cs.timeframe = 'DAILY'
                AND cs.status = 'ACTIVE'
        """, (instrument_id,))
        daily_row = cursor.fetchone()
        daily_cycle = dict(daily_row) if daily_row else None

        # Get WEEKLY cycle
        cursor.execute("""
            SELECT
                cs.median_input_date_label as median,
                cs.cycle_length_bars as bars,
                cp.median_label as computed_median,
                cp.core_start_label as window_start,
                cp.core_end_label as window_end
            FROM cycle_specs cs
            LEFT JOIN cycle_projections cp
                ON cp.instrument_id = cs.instrument_id
                AND cp.timeframe = cs.timeframe
                AND cp.version = cs.version
                AND cp.k = 0
                AND cp.active = 1
            WHERE cs.instrument_id = ?
                AND cs.timeframe = 'WEEKLY'
                AND cs.status = 'ACTIVE'
        """, (instrument_id,))
        weekly_row = cursor.fetchone()
        weekly_cycle = dict(weekly_row) if weekly_row else None

        # Get astro dates (PRIMARY and BACKUP)
        cursor.execute("""
            SELECT role, event_label
            FROM astro_events
            WHERE instrument_id = ?
                AND role IN ('PRIMARY', 'BACKUP')
                AND event_label >= date('now')
            ORDER BY event_label
        """, (instrument_id,))
        astro_rows = cursor.fetchall()
        astro = {}
        for row in astro_rows:
            if row['role'] == 'PRIMARY' and 'primary_date' not in astro:
                astro['primary_date'] = row['event_label']
            elif row['role'] == 'BACKUP' and 'backup_date' not in astro:
                astro['backup_date'] = row['event_label']

        if 'primary_date' not in astro:
            astro['primary_date'] = None
        if 'backup_date' not in astro:
            astro['backup_date'] = None

        # Get all desk notes (for display in DATABASE view)
        cursor.execute("""
            SELECT note_id, asof_td_label, author, source, note_type, timeframe_scope,
                   price_reference, bullets_json, notes, created_at, updated_at
            FROM desk_notes
            WHERE instrument_id = ?
            ORDER BY asof_td_label DESC
            LIMIT 10
        """, (instrument_id,))
        note_rows = cursor.fetchall()
        desk_notes = [dict(row) for row in note_rows]

        # Get latest note for editor default value
        latest_note = desk_notes[0] if desk_notes else None
        desk_note_editor = {
            'text': latest_note['notes'] if latest_note and latest_note['notes'] else '',
            'updated_at': latest_note['updated_at'] if latest_note else None
        }

        conn.close()

        return {
            'instrument': instrument,
            'daily_cycle': daily_cycle,
            'weekly_cycle': weekly_cycle,
            'astro': astro,
            'desk_note': desk_note_editor,  # For editor default value
            'desk_notes_history': desk_notes  # For display
        }

    def update_cycles(
        self,
        symbol: str,
        daily_median: Optional[str] = None,
        daily_bars: Optional[int] = None,
        weekly_median: Optional[str] = None,
        weekly_bars: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update cycle medians and bars. Automatically recomputes windows.

        Args:
            symbol: Instrument symbol
            daily_median: DAILY median date (YYYY-MM-DD) or None to skip
            daily_bars: DAILY cycle length in bars or None to keep existing
            weekly_median: WEEKLY median date (YYYY-MM-DD) or None to skip
            weekly_bars: WEEKLY cycle length in bars or None to keep existing

        Returns:
            Dict with status and any errors
        """
        from pathlib import Path
        import sys

        # Add src to path for CycleService
        project_root = Path(self.db_path).parent.parent
        sys.path.insert(0, str(project_root))

        from src.riley.cycle_service import CycleService

        service = CycleService(self.db_path)
        results = {'status': 'success', 'daily': None, 'weekly': None}

        try:
            # Update DAILY cycle
            if daily_median is not None:
                daily_result = service.set_cycle_median(
                    symbol=symbol,
                    timeframe='DAILY',
                    median_label=daily_median,
                    cycle_length_bars=daily_bars,
                    versioning='REPLACE'
                )
                results['daily'] = daily_result

            # Update WEEKLY cycle
            if weekly_median is not None:
                weekly_result = service.set_cycle_median(
                    symbol=symbol,
                    timeframe='WEEKLY',
                    median_label=weekly_median,
                    cycle_length_bars=weekly_bars,
                    versioning='REPLACE'
                )
                results['weekly'] = weekly_result

            # CRITICAL: Recompute projections after updating cycle specs
            # Run a scan to regenerate cycle_projections with the new specs
            from datetime import datetime
            import subprocess

            asof_date = datetime.now().strftime('%Y-%m-%d')
            scan_script = project_root / "scripts" / "cycles_run_scan.py"

            try:
                subprocess.run(
                    [sys.executable, str(scan_script), "--asof", asof_date],
                    cwd=str(project_root),
                    capture_output=True,
                    timeout=60
                )
                results['scan'] = 'completed'
            except Exception as scan_err:
                results['scan'] = f'error: {str(scan_err)}'

            return results

        except Exception as e:
            return {'status': 'error', 'message': str(e)}

    def update_astro_dates(
        self,
        symbol: str,
        primary_date: Optional[str] = None,
        backup_date: Optional[str] = None
    ) -> bool:
        """
        Update astro primary and backup dates.

        Args:
            symbol: Instrument symbol
            primary_date: PRIMARY astro date (YYYY-MM-DD) or None to remove
            backup_date: BACKUP astro date (YYYY-MM-DD) or None to remove

        Returns:
            True if successful
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get instrument_id
            cursor.execute("""
                SELECT instrument_id
                FROM instruments
                WHERE symbol = ? AND role = 'CANONICAL'
            """, (symbol,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return False

            instrument_id = row['instrument_id']

            # Update PRIMARY date
            if primary_date is not None:
                # Get trading day index
                cursor.execute("""
                    SELECT td_index
                    FROM trading_calendar_daily
                    WHERE instrument_id = ?
                        AND trading_date_label = ?
                    LIMIT 1
                """, (instrument_id, primary_date))
                td_row = cursor.fetchone()

                if td_row:
                    td_index = td_row['td_index']

                    # Delete existing PRIMARY events for this instrument
                    cursor.execute("""
                        DELETE FROM astro_events
                        WHERE instrument_id = ? AND role = 'PRIMARY'
                    """, (instrument_id,))

                    # Insert new PRIMARY event
                    cursor.execute("""
                        INSERT INTO astro_events (
                            instrument_id, event_label, td_index, role,
                            name, category, created_at
                        )
                        VALUES (?, ?, ?, 'PRIMARY', 'Manual Entry', 'REVERSAL', datetime('now'))
                    """, (instrument_id, primary_date, td_index))

            # Update BACKUP date
            if backup_date is not None:
                # Get trading day index
                cursor.execute("""
                    SELECT td_index
                    FROM trading_calendar_daily
                    WHERE instrument_id = ?
                        AND trading_date_label = ?
                    LIMIT 1
                """, (instrument_id, backup_date))
                td_row = cursor.fetchone()

                if td_row:
                    td_index = td_row['td_index']

                    # Delete existing BACKUP events for this instrument
                    cursor.execute("""
                        DELETE FROM astro_events
                        WHERE instrument_id = ? AND role = 'BACKUP'
                    """, (instrument_id,))

                    # Insert new BACKUP event
                    cursor.execute("""
                        INSERT INTO astro_events (
                            instrument_id, event_label, td_index, role,
                            name, category, created_at
                        )
                        VALUES (?, ?, ?, 'BACKUP', 'Manual Entry', 'REVERSAL', datetime('now'))
                    """, (instrument_id, backup_date, td_index))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error updating astro dates: {e}")
            return False

    def update_desk_note(
        self,
        symbol: str,
        note_text: str,
        asof_date: Optional[str] = None
    ) -> bool:
        """
        Update or insert desk note for an instrument.

        Args:
            symbol: Instrument symbol
            note_text: Free text note content
            asof_date: Date for the note (defaults to today)

        Returns:
            True if successful
        """
        import json
        from datetime import datetime

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Get instrument_id
            cursor.execute("""
                SELECT instrument_id
                FROM instruments
                WHERE symbol = ? AND role = 'CANONICAL'
            """, (symbol,))
            row = cursor.fetchone()

            if not row:
                conn.close()
                return False

            instrument_id = row['instrument_id']

            # Use today if no asof_date provided
            if asof_date is None:
                asof_date = datetime.now().strftime('%Y-%m-%d')

            # Check if note exists for this date
            cursor.execute("""
                SELECT note_id
                FROM desk_notes
                WHERE instrument_id = ? AND asof_td_label = ?
            """, (instrument_id, asof_date))
            existing = cursor.fetchone()

            # Convert note_text to bullets_json format (simple list)
            bullets = [line.strip() for line in note_text.strip().split('\n') if line.strip()]
            bullets_json = json.dumps(bullets)

            if existing:
                # Update existing note
                cursor.execute("""
                    UPDATE desk_notes
                    SET notes = ?,
                        bullets_json = ?,
                        updated_at = datetime('now')
                    WHERE note_id = ?
                """, (note_text, bullets_json, existing['note_id']))
            else:
                # Insert new note
                cursor.execute("""
                    INSERT INTO desk_notes (
                        instrument_id, asof_td_label, author, source,
                        bullets_json, notes, created_at, updated_at
                    )
                    VALUES (?, ?, 'Bernard', 'Manual Entry', ?, ?, datetime('now'), datetime('now'))
                """, (instrument_id, asof_date, bullets_json, note_text))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error updating desk note: {e}")
            return False

    def get_notes(self, instrument_id: int) -> List[Dict[str, Any]]:
        """
        Get all desk notes for an instrument (canonical method).

        Returns list of dicts with ALL fields, ordered by asof_td_label DESC.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT note_id, asof_td_label, author, source, note_type,
                   timeframe_scope, price_reference, bullets_json, notes,
                   created_at, updated_at
            FROM desk_notes
            WHERE instrument_id = ?
            ORDER BY asof_td_label DESC
        """, (instrument_id,))

        notes = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return notes

    def get_note(self, instrument_id: int, asof_td_label: str) -> Optional[Dict[str, Any]]:
        """Get a specific desk note by instrument_id and date."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT note_id, asof_td_label, author, source, note_type,
                   timeframe_scope, price_reference, bullets_json, notes,
                   created_at, updated_at
            FROM desk_notes
            WHERE instrument_id = ? AND asof_td_label = ?
        """, (instrument_id, asof_td_label))

        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None

    def upsert_note(self,
                    instrument_id: int,
                    asof_td_label: str,
                    author: str = 'Bernard',
                    note_text: str = '',
                    source: Optional[str] = None,
                    timeframe_scope: Optional[str] = None,
                    note_type: Optional[str] = None,
                    price_reference: Optional[str] = None) -> bool:
        """
        Insert or update a desk note with ALL fields.

        Uses SQLite UPSERT (INSERT ... ON CONFLICT ... DO UPDATE).
        """
        import json

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # Convert note_text to bullets_json
            bullets = [line.strip() for line in note_text.strip().split('\n') if line.strip()]
            bullets_json = json.dumps(bullets)

            cursor.execute("""
                INSERT INTO desk_notes (
                    instrument_id, asof_td_label, author, source, note_type,
                    timeframe_scope, price_reference, bullets_json, notes,
                    created_at, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                ON CONFLICT(instrument_id, asof_td_label) DO UPDATE SET
                    author = excluded.author,
                    source = excluded.source,
                    note_type = excluded.note_type,
                    timeframe_scope = excluded.timeframe_scope,
                    price_reference = excluded.price_reference,
                    bullets_json = excluded.bullets_json,
                    notes = excluded.notes,
                    updated_at = datetime('now')
            """, (instrument_id, asof_td_label, author, source, note_type,
                  timeframe_scope, price_reference, bullets_json, note_text))

            conn.commit()
            conn.close()
            return True

        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error upserting desk note: {e}")
            return False

    def delete_note(self, instrument_id: int, asof_td_label: str) -> bool:
        """Delete a specific desk note."""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""
                DELETE FROM desk_notes
                WHERE instrument_id = ? AND asof_td_label = ?
            """, (instrument_id, asof_td_label))

            conn.commit()
            deleted = cursor.rowcount > 0
            conn.close()
            return deleted

        except Exception as e:
            conn.rollback()
            conn.close()
            print(f"Error deleting desk note: {e}")
            return False
