"""
Cycle Service - Canonical Write API

THE ONLY LEGAL WAY to modify cycle inputs.
All cycle changes must go through this module.
Every change triggers deterministic rebuild + validation.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from .cycles_rebuild import CyclesRebuilder
from .cycle_validation import validate_cycles


class CycleService:
    """Canonical API for cycle operations"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "db" / "riley.sqlite"
        self.db_path = str(db_path)
        self.rebuilder = CyclesRebuilder(db_path)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _resolve_instrument(self, conn: sqlite3.Connection, symbol: str) -> int:
        """Resolve symbol to canonical instrument_id"""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT instrument_id
            FROM instruments
            WHERE symbol = ? AND role = 'CANONICAL'
        """, (symbol,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument not found: {symbol}")
        return row['instrument_id']

    def set_cycle_median(
        self,
        symbol: str,
        timeframe: str,
        median_label: str,
        cycle_length_bars: Optional[int] = None,
        window_minus_bars: int = 3,
        window_plus_bars: int = 3,
        prewindow_lead_bars: int = 2,
        source: Optional[str] = None,
        versioning: str = 'BUMP'
    ) -> Dict[str, Any]:
        """
        Set cycle median (THE CANONICAL WAY to modify cycles).

        Args:
            symbol: Instrument symbol (e.g., 'PL', 'ES')
            timeframe: 'DAILY' or 'WEEKLY'
            median_label: User-provided median date (YYYY-MM-DD)
            cycle_length_bars: Cycle length in bars (optional)
            window_minus_bars: Bars before median (default 3)
            window_plus_bars: Bars after median (default 3)
            prewindow_lead_bars: Prewindow lead bars (default 2)
            source: Source of this cycle (optional)
            versioning: 'BUMP' to increment version, 'REPLACE' to update existing

        Returns:
            Dict with cycle details including snapped median and window dates
        """
        if timeframe not in ('DAILY', 'WEEKLY'):
            raise ValueError(f"Invalid timeframe: {timeframe}")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN TRANSACTION")

            # Resolve instrument
            instrument_id = self._resolve_instrument(conn, symbol)

            # Get existing spec
            cursor.execute("""
                SELECT cycle_id, version
                FROM cycle_specs
                WHERE instrument_id = ? AND timeframe = ? AND status = 'ACTIVE'
            """, (instrument_id, timeframe))
            existing = cursor.fetchone()

            if versioning == 'BUMP' and existing:
                # Mark existing as SUPERSEDED
                cursor.execute("""
                    UPDATE cycle_specs
                    SET status = 'SUPERSEDED', updated_at = ?
                    WHERE cycle_id = ?
                """, (datetime.now().isoformat(), existing['cycle_id']))
                new_version = existing['version'] + 1
            elif existing:
                # REPLACE mode - update existing
                new_version = existing['version']
                cycle_id = existing['cycle_id']
            else:
                # No existing spec - create v1
                new_version = 1

            # Create or update cycle spec
            if versioning == 'BUMP' or not existing:
                # Determine cycle_length_bars
                if cycle_length_bars is None:
                    # Use default based on timeframe
                    cycle_length_bars = 35 if timeframe == 'DAILY' else 36

                cursor.execute("""
                    INSERT INTO cycle_specs (
                        instrument_id, timeframe, anchor_input_date_label,
                        median_input_date_label, snap_rule, cycle_length_bars,
                        window_minus_bars, window_plus_bars, prewindow_lead_bars,
                        version, status, source, created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, 'NEXT_BAR', ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?)
                """, (
                    instrument_id, timeframe, median_label, median_label,
                    cycle_length_bars, window_minus_bars, window_plus_bars,
                    prewindow_lead_bars, new_version, source,
                    datetime.now().isoformat(), datetime.now().isoformat()
                ))
                cycle_id = cursor.lastrowid
            else:
                # Update existing spec
                cursor.execute("""
                    UPDATE cycle_specs
                    SET median_input_date_label = ?,
                        anchor_input_date_label = ?,
                        window_minus_bars = ?,
                        window_plus_bars = ?,
                        prewindow_lead_bars = ?,
                        cycle_length_bars = COALESCE(?, cycle_length_bars),
                        source = COALESCE(?, source),
                        updated_at = ?
                    WHERE cycle_id = ?
                """, (
                    median_label, median_label,
                    window_minus_bars, window_plus_bars, prewindow_lead_bars,
                    cycle_length_bars, source,
                    datetime.now().isoformat(), cycle_id
                ))

            conn.commit()

            # IMMEDIATELY rebuild projection (deterministic)
            rebuild_result = self.rebuilder.rebuild_one(
                instrument_id, timeframe, new_version
            )

            if rebuild_result['status'] != 'success':
                raise RuntimeError(f"Rebuild failed: {rebuild_result.get('reason')}")

            # Validate
            validate_cycles(conn, symbol=symbol)

            # Get final projection data
            cursor.execute("""
                SELECT
                    cp.median_label,
                    cp.core_start_label,
                    cp.core_end_label,
                    cp.median_td_index,
                    cp.core_start_td_index,
                    cp.core_end_td_index,
                    cp.median_tw_index,
                    cp.core_start_tw_index,
                    cp.core_end_tw_index
                FROM cycle_projections cp
                WHERE cp.instrument_id = ?
                    AND cp.timeframe = ?
                    AND cp.version = ?
                    AND cp.k = 0
                    AND cp.active = 1
            """, (instrument_id, timeframe, new_version))
            projection = cursor.fetchone()

            if not projection:
                raise RuntimeError("Projection not found after rebuild")

            projection = dict(projection)

            return {
                'status': 'success',
                'symbol': symbol,
                'timeframe': timeframe,
                'version': new_version,
                'cycle_id': cycle_id,
                'median_input': median_label,
                'median_snapped': projection['median_label'],
                'window_start': projection['core_start_label'],
                'window_end': projection['core_end_label'],
                'indices': {
                    'td': {
                        'median': projection['median_td_index'],
                        'start': projection['core_start_td_index'],
                        'end': projection['core_end_td_index']
                    } if timeframe == 'DAILY' else None,
                    'tw': {
                        'median': projection['median_tw_index'],
                        'start': projection['core_start_tw_index'],
                        'end': projection['core_end_tw_index']
                    } if timeframe == 'WEEKLY' else None
                }
            }

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to set cycle median: {str(e)}") from e
        finally:
            conn.close()

    def add_or_update_cycle_defaults(
        self,
        symbol: str,
        timeframe: str,
        window_minus_bars: int = 3,
        window_plus_bars: int = 3,
        prewindow_lead_bars: int = 2
    ) -> Dict[str, Any]:
        """
        Update window defaults on ACTIVE cycle spec.
        Immediately rebuilds and validates.
        """
        if timeframe not in ('DAILY', 'WEEKLY'):
            raise ValueError(f"Invalid timeframe: {timeframe}")

        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            conn.execute("BEGIN TRANSACTION")

            # Resolve instrument
            instrument_id = self._resolve_instrument(conn, symbol)

            # Get existing ACTIVE spec
            cursor.execute("""
                SELECT cycle_id, version, median_input_date_label
                FROM cycle_specs
                WHERE instrument_id = ? AND timeframe = ? AND status = 'ACTIVE'
            """, (instrument_id, timeframe))
            spec = cursor.fetchone()

            if not spec:
                raise ValueError(f"No active cycle spec found for {symbol} {timeframe}")

            spec = dict(spec)

            # Update defaults
            cursor.execute("""
                UPDATE cycle_specs
                SET window_minus_bars = ?,
                    window_plus_bars = ?,
                    prewindow_lead_bars = ?,
                    updated_at = ?
                WHERE cycle_id = ?
            """, (
                window_minus_bars, window_plus_bars, prewindow_lead_bars,
                datetime.now().isoformat(), spec['cycle_id']
            ))

            conn.commit()

            # IMMEDIATELY rebuild
            rebuild_result = self.rebuilder.rebuild_one(
                instrument_id, timeframe, spec['version']
            )

            if rebuild_result['status'] != 'success':
                raise RuntimeError(f"Rebuild failed: {rebuild_result.get('reason')}")

            # Validate
            validate_cycles(conn, symbol=symbol)

            return {
                'status': 'success',
                'symbol': symbol,
                'timeframe': timeframe,
                'version': spec['version'],
                'window_minus_bars': window_minus_bars,
                'window_plus_bars': window_plus_bars,
                'prewindow_lead_bars': prewindow_lead_bars
            }

        except Exception as e:
            conn.rollback()
            raise RuntimeError(f"Failed to update cycle defaults: {str(e)}") from e
        finally:
            conn.close()

    def get_cycle_info(self, symbol: str, timeframe: str) -> Dict[str, Any]:
        """Get current cycle information (read-only)"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            instrument_id = self._resolve_instrument(conn, symbol)

            cursor.execute("""
                SELECT
                    cs.cycle_id,
                    cs.version,
                    cs.median_input_date_label,
                    cs.cycle_length_bars,
                    cs.window_minus_bars,
                    cs.window_plus_bars,
                    cs.prewindow_lead_bars,
                    cp.median_label as median_snapped,
                    cp.core_start_label,
                    cp.core_end_label
                FROM cycle_specs cs
                LEFT JOIN cycle_projections cp
                    ON cp.instrument_id = cs.instrument_id
                    AND cp.timeframe = cs.timeframe
                    AND cp.version = cs.version
                    AND cp.k = 0
                    AND cp.active = 1
                WHERE cs.instrument_id = ?
                    AND cs.timeframe = ?
                    AND cs.status = 'ACTIVE'
            """, (instrument_id, timeframe))

            row = cursor.fetchone()
            if not row:
                return {'status': 'not_found'}

            return dict(row)

        finally:
            conn.close()
