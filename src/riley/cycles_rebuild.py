"""
Cycle Projections Rebuild Module

Single authority for rebuilding cycle projections with proper calendar unit separation.
DAILY cycles use trading_calendar_daily (TD indices).
WEEKLY cycles use trading_calendar_weekly (TW indices).
Never mix them.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional


class CyclesRebuilder:
    """Rebuild cycle projections with proper DAILY/WEEKLY calendar separation"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "db" / "riley.sqlite"
        self.db_path = str(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def snap_daily_next(self, conn: sqlite3.Connection, instrument_id: int,
                       date_label: str) -> Tuple[int, str]:
        """
        Snap to next valid trading day.
        Returns (td_index, trading_date_label)
        """
        cursor = conn.cursor()

        # Try exact match first
        cursor.execute("""
            SELECT td_index, trading_date_label
            FROM trading_calendar_daily
            WHERE trading_date_label = ?
            LIMIT 1
        """, (date_label,))

        row = cursor.fetchone()
        if row:
            return row['td_index'], row['trading_date_label']

        # Get next trading day after date_label
        cursor.execute("""
            SELECT td_index, trading_date_label
            FROM trading_calendar_daily
            WHERE trading_date_label > ?
            ORDER BY trading_date_label ASC
            LIMIT 1
        """, (date_label,))

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No trading day found on or after {date_label}")

        return row['td_index'], row['trading_date_label']

    def snap_weekly_next(self, conn: sqlite3.Connection, instrument_id: int,
                        week_end_label: str) -> Tuple[int, str]:
        """
        Snap to next valid trading week.
        Returns (tw_index, week_end_label)
        """
        cursor = conn.cursor()

        # Try exact match first
        cursor.execute("""
            SELECT tw_index, week_end_label
            FROM trading_calendar_weekly
            WHERE week_end_label = ?
            LIMIT 1
        """, (week_end_label,))

        row = cursor.fetchone()
        if row:
            return row['tw_index'], row['week_end_label']

        # Get next week after week_end_label
        cursor.execute("""
            SELECT tw_index, week_end_label
            FROM trading_calendar_weekly
            WHERE week_end_label > ?
            ORDER BY week_end_label ASC
            LIMIT 1
        """, (week_end_label,))

        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No trading week found on or after {week_end_label}")

        return row['tw_index'], row['week_end_label']

    def get_daily_label(self, conn: sqlite3.Connection, td_index: int) -> str:
        """Get trading_date_label for given td_index"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT trading_date_label
            FROM trading_calendar_daily
            WHERE td_index = ?
        """, (td_index,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No trading day found for td_index {td_index}")
        return row['trading_date_label']

    def get_weekly_label(self, conn: sqlite3.Connection, tw_index: int) -> str:
        """Get week_end_label for given tw_index"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT week_end_label
            FROM trading_calendar_weekly
            WHERE tw_index = ?
        """, (tw_index,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"No trading week found for tw_index {tw_index}")
        return row['week_end_label']

    def rebuild_one(self, instrument_id: int, timeframe: str, version: int) -> Dict[str, Any]:
        """
        Rebuild projections for one (instrument_id, timeframe, version).
        Creates exactly ONE projection with k=0.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN TRANSACTION")

            # Load cycle spec
            cursor.execute("""
                SELECT *
                FROM cycle_specs
                WHERE instrument_id = ?
                  AND timeframe = ?
                  AND version = ?
                  AND status = 'ACTIVE'
            """, (instrument_id, timeframe, version))

            spec = cursor.fetchone()
            if not spec:
                conn.rollback()
                return {
                    'status': 'skipped',
                    'reason': 'No active spec found'
                }

            spec = dict(spec)

            # Get median input label (fallback to anchor if needed)
            median_input = spec.get('median_input_date_label')
            if not median_input:
                median_input = spec.get('anchor_input_date_label')
                if not median_input:
                    conn.rollback()
                    return {
                        'status': 'error',
                        'reason': 'No median_input_date_label or anchor_input_date_label'
                    }
                # Update spec to use median going forward
                cursor.execute("""
                    UPDATE cycle_specs
                    SET median_input_date_label = ?
                    WHERE cycle_id = ?
                """, (median_input, spec['cycle_id']))

            # Get window parameters
            window_minus = spec.get('window_minus_bars', 3)
            window_plus = spec.get('window_plus_bars', 3)
            prewindow_lead = spec.get('prewindow_lead_bars', 2)

            # Compute indices and labels based on timeframe
            projection_data = {
                'instrument_id': instrument_id,
                'cycle_id': spec['cycle_id'],
                'timeframe': timeframe,
                'version': version,
                'k': 0,
                'active': 1,
                'computed_at': datetime.now().isoformat(),
                'anchor_index': 0,  # deprecated but keep for compat
                'anchor_label': median_input,  # deprecated but keep for compat
                'median_index': 0,  # deprecated but keep for compat
                'core_start_index': 0,  # deprecated but keep for compat
                'core_end_index': 0,  # deprecated but keep for compat
                'prewindow_start_index': 0,  # deprecated but keep for compat
                'prewindow_end_index': 0,  # deprecated but keep for compat
                'notes': None
            }

            if timeframe == 'DAILY':
                # Use DAILY calendar (TD indices)
                median_td_index, median_label = self.snap_daily_next(conn, instrument_id, median_input)

                core_start_td_index = median_td_index - window_minus
                core_end_td_index = median_td_index + window_plus
                prewindow_start_td_index = core_start_td_index - prewindow_lead
                prewindow_end_td_index = core_start_td_index - 1

                # Handle edge cases with early calendar dates
                if core_start_td_index < 0:
                    core_start_td_index = 0

                # If prewindow would go negative or violate constraints, disable it
                if prewindow_start_td_index < 0 or prewindow_end_td_index < 0 or prewindow_end_td_index >= core_start_td_index:
                    prewindow_start_td_index = None
                    prewindow_end_td_index = None
                    prewindow_start_label = None
                    prewindow_end_label = None
                else:
                    prewindow_start_label = self.get_daily_label(conn, prewindow_start_td_index)
                    prewindow_end_label = self.get_daily_label(conn, prewindow_end_td_index)

                # Resolve core labels
                core_start_label = self.get_daily_label(conn, core_start_td_index)
                core_end_label = self.get_daily_label(conn, core_end_td_index)

                # Validate
                if not (core_start_td_index <= median_td_index <= core_end_td_index):
                    raise ValueError("Invalid window: start > median or median > end")

                # Populate TD fields
                projection_data.update({
                    'median_label': median_label,
                    'median_td_index': median_td_index,
                    'core_start_td_index': core_start_td_index,
                    'core_end_td_index': core_end_td_index,
                    'prewindow_start_td_index': prewindow_start_td_index,
                    'prewindow_end_td_index': prewindow_end_td_index,
                    'core_start_label': core_start_label,
                    'core_end_label': core_end_label,
                    'prewindow_start_label': prewindow_start_label,
                    'prewindow_end_label': prewindow_end_label,
                    # Populate deprecated fields for backward compat (use 0 if None to satisfy NOT NULL)
                    'median_index': median_td_index,
                    'core_start_index': core_start_td_index,
                    'core_end_index': core_end_td_index,
                    'prewindow_start_index': prewindow_start_td_index if prewindow_start_td_index is not None else 0,
                    'prewindow_end_index': prewindow_end_td_index if prewindow_end_td_index is not None else 0,
                })

            elif timeframe == 'WEEKLY':
                # Use WEEKLY calendar (TW indices)
                median_tw_index, median_label = self.snap_weekly_next(conn, instrument_id, median_input)

                core_start_tw_index = median_tw_index - window_minus
                core_end_tw_index = median_tw_index + window_plus
                prewindow_start_tw_index = core_start_tw_index - prewindow_lead
                prewindow_end_tw_index = core_start_tw_index - 1

                # Handle edge cases with early calendar dates
                if core_start_tw_index < 0:
                    core_start_tw_index = 0

                # If prewindow would go negative or violate constraints, disable it
                if prewindow_start_tw_index < 0 or prewindow_end_tw_index < 0 or prewindow_end_tw_index >= core_start_tw_index:
                    prewindow_start_tw_index = None
                    prewindow_end_tw_index = None
                    prewindow_start_label = None
                    prewindow_end_label = None
                else:
                    prewindow_start_label = self.get_weekly_label(conn, prewindow_start_tw_index)
                    prewindow_end_label = self.get_weekly_label(conn, prewindow_end_tw_index)

                # Resolve core labels
                core_start_label = self.get_weekly_label(conn, core_start_tw_index)
                core_end_label = self.get_weekly_label(conn, core_end_tw_index)

                # Validate
                if not (core_start_tw_index <= median_tw_index <= core_end_tw_index):
                    raise ValueError("Invalid window: start > median or median > end")

                # Populate TW fields
                projection_data.update({
                    'median_label': median_label,
                    'median_tw_index': median_tw_index,
                    'core_start_tw_index': core_start_tw_index,
                    'core_end_tw_index': core_end_tw_index,
                    'prewindow_start_tw_index': prewindow_start_tw_index,
                    'prewindow_end_tw_index': prewindow_end_tw_index,
                    'core_start_label': core_start_label,
                    'core_end_label': core_end_label,
                    'prewindow_start_label': prewindow_start_label,
                    'prewindow_end_label': prewindow_end_label,
                    # Populate deprecated fields for backward compat (use 0 if None to satisfy NOT NULL)
                    'median_index': median_tw_index,
                    'core_start_index': core_start_tw_index,
                    'core_end_index': core_end_tw_index,
                    'prewindow_start_index': prewindow_start_tw_index if prewindow_start_tw_index is not None else 0,
                    'prewindow_end_index': prewindow_end_tw_index if prewindow_end_tw_index is not None else 0,
                })
            else:
                raise ValueError(f"Unknown timeframe: {timeframe}")

            # IMPORTANT: Deactivate ALL old active projections for this (instrument_id, timeframe)
            # This prevents accumulation of duplicate active projections when versions change
            cursor.execute("""
                UPDATE cycle_projections
                SET active = 0
                WHERE instrument_id = ? AND timeframe = ? AND active = 1
            """, (instrument_id, timeframe))

            # Delete existing projections for this specific version (cleanup)
            cursor.execute("""
                DELETE FROM cycle_projections
                WHERE instrument_id = ? AND timeframe = ? AND version = ?
            """, (instrument_id, timeframe, version))

            # Insert new projection (k=0 only)
            cursor.execute("""
                INSERT INTO cycle_projections (
                    cycle_id, instrument_id, timeframe, version,
                    anchor_index, anchor_label, k, median_index, median_label,
                    core_start_index, core_end_index,
                    prewindow_start_index, prewindow_end_index,
                    median_td_index, core_start_td_index, core_end_td_index,
                    prewindow_start_td_index, prewindow_end_td_index,
                    median_tw_index, core_start_tw_index, core_end_tw_index,
                    prewindow_start_tw_index, prewindow_end_tw_index,
                    core_start_label, core_end_label,
                    prewindow_start_label, prewindow_end_label,
                    computed_at, active, notes
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                projection_data['cycle_id'],
                projection_data['instrument_id'],
                projection_data['timeframe'],
                projection_data['version'],
                projection_data['anchor_index'],
                projection_data['anchor_label'],
                projection_data['k'],
                projection_data['median_index'],
                projection_data['median_label'],
                projection_data['core_start_index'],
                projection_data['core_end_index'],
                projection_data['prewindow_start_index'],
                projection_data['prewindow_end_index'],
                projection_data.get('median_td_index'),
                projection_data.get('core_start_td_index'),
                projection_data.get('core_end_td_index'),
                projection_data.get('prewindow_start_td_index'),
                projection_data.get('prewindow_end_td_index'),
                projection_data.get('median_tw_index'),
                projection_data.get('core_start_tw_index'),
                projection_data.get('core_end_tw_index'),
                projection_data.get('prewindow_start_tw_index'),
                projection_data.get('prewindow_end_tw_index'),
                projection_data.get('core_start_label'),
                projection_data.get('core_end_label'),
                projection_data.get('prewindow_start_label'),
                projection_data.get('prewindow_end_label'),
                projection_data['computed_at'],
                projection_data['active'],
                projection_data['notes']
            ))

            conn.commit()

            return {
                'status': 'success',
                'projection_data': projection_data
            }

        except Exception as e:
            conn.rollback()
            return {
                'status': 'error',
                'reason': str(e)
            }
        finally:
            conn.close()

    def rebuild_all(self, symbol: Optional[str] = None) -> Dict[str, Any]:
        """
        Rebuild all active cycle specs.
        Optionally filter by symbol.
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get all active specs
        if symbol:
            cursor.execute("""
                SELECT cs.instrument_id, cs.timeframe, cs.version, i.symbol
                FROM cycle_specs cs
                JOIN instruments i ON i.instrument_id = cs.instrument_id
                WHERE cs.status = 'ACTIVE'
                  AND i.symbol = ?
                  AND i.role = 'CANONICAL'
                ORDER BY i.symbol, cs.timeframe, cs.version
            """, (symbol,))
        else:
            cursor.execute("""
                SELECT cs.instrument_id, cs.timeframe, cs.version, i.symbol
                FROM cycle_specs cs
                JOIN instruments i ON i.instrument_id = cs.instrument_id
                WHERE cs.status = 'ACTIVE'
                  AND i.role = 'CANONICAL'
                ORDER BY i.symbol, cs.timeframe, cs.version
            """)

        specs = cursor.fetchall()
        conn.close()

        results = {
            'rebuilt': 0,
            'skipped': 0,
            'errors': 0,
            'details': []
        }

        for spec in specs:
            spec_dict = dict(spec)
            result = self.rebuild_one(
                spec_dict['instrument_id'],
                spec_dict['timeframe'],
                spec_dict['version']
            )

            result['symbol'] = spec_dict['symbol']
            result['timeframe'] = spec_dict['timeframe']
            result['version'] = spec_dict['version']

            results['details'].append(result)

            if result['status'] == 'success':
                results['rebuilt'] += 1
                print(f"✓ {spec_dict['symbol']} {spec_dict['timeframe']} v{spec_dict['version']}")
            elif result['status'] == 'skipped':
                results['skipped'] += 1
                print(f"- {spec_dict['symbol']} {spec_dict['timeframe']} v{spec_dict['version']}: {result['reason']}")
            else:
                results['errors'] += 1
                print(f"✗ {spec_dict['symbol']} {spec_dict['timeframe']} v{spec_dict['version']}: {result['reason']}")

        return results
