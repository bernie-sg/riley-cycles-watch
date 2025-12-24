"""Database operations for Riley Project"""
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional


class Database:
    """SQLite database manager for Riley Project"""

    def __init__(self, db_path: str = None):
        if db_path is None:
            project_root = Path(__file__).parent.parent.parent
            db_path = project_root / "db" / "riley.sqlite"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = None

    def connect(self):
        """Establish database connection"""
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        return self.conn

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def run_migrations(self):
        """Run all SQL migrations in order"""
        project_root = Path(__file__).parent.parent.parent
        migrations_dir = project_root / "db" / "migrations"

        if not migrations_dir.exists():
            raise FileNotFoundError(f"Migrations directory not found: {migrations_dir}")

        migration_files = sorted(migrations_dir.glob("*.sql"))

        conn = self.connect()
        cursor = conn.cursor()

        for migration_file in migration_files:
            print(f"Running migration: {migration_file.name}")
            with open(migration_file, 'r') as f:
                sql = f.read()
                cursor.executescript(sql)

        conn.commit()
        return len(migration_files)

    def create_run(self, as_of_date: str) -> int:
        """Create a new run record"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO runs (as_of_date, started_at, status) VALUES (?, ?, ?)",
            (as_of_date, datetime.now().isoformat(), "running")
        )
        conn.commit()
        return cursor.lastrowid

    def finish_run(self, run_id: int, status: str):
        """Mark run as finished"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE runs SET finished_at = ?, status = ? WHERE run_id = ?",
            (datetime.now().isoformat(), status, run_id)
        )
        conn.commit()

    def upsert_instrument(self, symbol: str, type_: str = None, source_preference: str = None,
                          role: str = 'CANONICAL', canonical_symbol: str = None,
                          alias_of_symbol: str = None, active: bool = True, name: str = None, notes: str = None):
        """Insert or update instrument record (Cycles Watch schema)"""
        conn = self.connect()
        cursor = conn.cursor()

        # If canonical_symbol not provided, use symbol
        if canonical_symbol is None:
            canonical_symbol = symbol

        # Get alias_of_instrument_id if alias_of_symbol provided
        alias_of_instrument_id = None
        if alias_of_symbol:
            cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (alias_of_symbol,))
            row = cursor.fetchone()
            if row:
                alias_of_instrument_id = row[0]

        cursor.execute(
            """INSERT INTO instruments (symbol, name, role, canonical_symbol, alias_of_instrument_id, active, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(symbol) DO UPDATE SET
                   name = COALESCE(?, name),
                   role = ?,
                   canonical_symbol = ?,
                   alias_of_instrument_id = COALESCE(?, alias_of_instrument_id),
                   active = ?,
                   notes = COALESCE(?, notes)
            """,
            (symbol, name, role, canonical_symbol, alias_of_instrument_id, int(active), notes,
             name, role, canonical_symbol, alias_of_instrument_id, int(active), notes)
        )
        conn.commit()
        return cursor.lastrowid

    # Cycles Watch methods
    def upsert_daily_calendar(self, instrument_symbol: str, rows: list):
        """Upsert daily calendar rows"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (instrument_symbol,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument {instrument_symbol} not found")
        instrument_id = row[0]

        for r in rows:
            cursor.execute(
                """INSERT INTO trading_calendar_daily (instrument_id, td_index, trading_date_label)
                   VALUES (?, ?, ?)
                   ON CONFLICT(instrument_id, td_index) DO UPDATE SET
                       trading_date_label = excluded.trading_date_label
                """,
                (instrument_id, r['td_index'], r['trading_date_label'])
            )
        conn.commit()

    def upsert_weekly_calendar(self, instrument_symbol: str, rows: list):
        """Upsert weekly calendar rows"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (instrument_symbol,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument {instrument_symbol} not found")
        instrument_id = row[0]

        for r in rows:
            cursor.execute(
                """INSERT INTO trading_calendar_weekly (instrument_id, tw_index, week_end_label)
                   VALUES (?, ?, ?)
                   ON CONFLICT(instrument_id, tw_index) DO UPDATE SET
                       week_end_label = excluded.week_end_label
                """,
                (instrument_id, r['tw_index'], r['week_end_label'])
            )
        conn.commit()

    def create_cycle_spec(self, instrument_symbol: str, timeframe: str, anchor_input_date_label: str,
                          cycle_length_bars: int, window_minus_bars: int, window_plus_bars: int,
                          prewindow_lead_bars: int, source: str = None, confidence: int = None,
                          notes: str = None, snap_rule: str = 'NEXT_TRADING_DAY') -> int:
        """Create cycle spec"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (instrument_symbol,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument {instrument_symbol} not found")
        instrument_id = row[0]

        # Determine next version
        cursor.execute(
            "SELECT COALESCE(MAX(version), 0) + 1 FROM cycle_specs WHERE instrument_id = ? AND timeframe = ?",
            (instrument_id, timeframe)
        )
        version = cursor.fetchone()[0]

        now = datetime.now().isoformat()

        cursor.execute(
            """INSERT INTO cycle_specs
               (instrument_id, timeframe, anchor_input_date_label, snap_rule,
                cycle_length_bars, window_minus_bars, window_plus_bars, prewindow_lead_bars,
                version, status, source, confidence, notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'ACTIVE', ?, ?, ?, ?, ?)
            """,
            (instrument_id, timeframe, anchor_input_date_label, snap_rule,
             cycle_length_bars, window_minus_bars, window_plus_bars, prewindow_lead_bars,
             version, source, confidence, notes, now, now)
        )
        conn.commit()
        return cursor.lastrowid

    def supersede_cycle_spec(self, cycle_id: int):
        """Mark cycle spec as superseded"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE cycle_specs SET status = 'SUPERSEDED', updated_at = ? WHERE cycle_id = ?",
            (datetime.now().isoformat(), cycle_id)
        )
        conn.commit()

    def write_cycle_projections(self, cycle_id: int, version: int, projections: list):
        """Write cycle projections"""
        conn = self.connect()
        cursor = conn.cursor()

        now = datetime.now().isoformat()

        for p in projections:
            cursor.execute(
                """INSERT INTO cycle_projections
                   (cycle_id, instrument_id, timeframe, version, anchor_index, anchor_label,
                    k, median_index, median_label, core_start_index, core_end_index,
                    prewindow_start_index, prewindow_end_index, computed_at, active, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (cycle_id, p['instrument_id'], p['timeframe'], version, p['anchor_index'], p['anchor_label'],
                 p['k'], p['median_index'], p['median_label'], p['core_start_index'], p['core_end_index'],
                 p['prewindow_start_index'], p['prewindow_end_index'], now, p.get('active', 1), p.get('notes'))
            )
        conn.commit()

    def create_desk_note(self, instrument_symbol: str, asof_td_label: str, author: str,
                         timeframe_scope: str, note_type: str, price_reference: str, bullets_json: str,
                         source: str = None, tags_json: str = None, range_state: str = None,
                         cycle_trough_start_label: str = None, cycle_trough_end_label: str = None,
                         downside_zone_low: float = None, downside_zone_high: float = None,
                         invalidation_rule: str = None, notes: str = None) -> int:
        """Create or update desk note (UPSERT)

        If a note exists for this instrument/date, it will be updated.
        If no note exists, a new one will be created.
        This ensures ONE note per (instrument, asof_date).
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (instrument_symbol,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument {instrument_symbol} not found")
        instrument_id = row[0]

        now = datetime.now().isoformat()

        cursor.execute(
            """INSERT INTO desk_notes
               (instrument_id, asof_td_label, author, source, timeframe_scope, note_type,
                price_reference, bullets_json, tags_json, range_state, cycle_trough_start_label,
                cycle_trough_end_label, downside_zone_low, downside_zone_high, invalidation_rule,
                notes, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(instrument_id, asof_td_label) DO UPDATE SET
                   author = excluded.author,
                   source = excluded.source,
                   timeframe_scope = excluded.timeframe_scope,
                   note_type = excluded.note_type,
                   price_reference = excluded.price_reference,
                   bullets_json = excluded.bullets_json,
                   tags_json = excluded.tags_json,
                   range_state = excluded.range_state,
                   cycle_trough_start_label = excluded.cycle_trough_start_label,
                   cycle_trough_end_label = excluded.cycle_trough_end_label,
                   downside_zone_low = excluded.downside_zone_low,
                   downside_zone_high = excluded.downside_zone_high,
                   invalidation_rule = excluded.invalidation_rule,
                   notes = excluded.notes,
                   updated_at = excluded.updated_at
            """,
            (instrument_id, asof_td_label, author, source, timeframe_scope, note_type,
             price_reference, bullets_json, tags_json, range_state, cycle_trough_start_label,
             cycle_trough_end_label, downside_zone_low, downside_zone_high, invalidation_rule,
             notes, now, now)
        )
        conn.commit()

        # Get the note_id (either just inserted or existing)
        cursor.execute(
            "SELECT note_id FROM desk_notes WHERE instrument_id = ? AND asof_td_label = ?",
            (instrument_id, asof_td_label)
        )
        return cursor.fetchone()[0]

    def create_scan_run(self, scan_td_label: str) -> int:
        """Create scan run"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO daily_scan_runs (scan_td_label, created_at) VALUES (?, ?)",
            (scan_td_label, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid

    def create_scan_rows(self, scan_id: int, rows: list):
        """Create scan rows"""
        conn = self.connect()
        cursor = conn.cursor()

        for r in rows:
            cursor.execute(
                """INSERT INTO daily_scan_rows
                   (scan_id, instrument_id, daily_status, weekly_status,
                    days_to_daily_core_start, weeks_to_weekly_core_start,
                    overlap_flag, priority_score, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (scan_id, r['instrument_id'], r['daily_status'], r['weekly_status'],
                 r.get('days_to_daily_core_start'), r.get('weeks_to_weekly_core_start'),
                 r.get('overlap_flag', 0), r.get('priority_score', 0), r.get('notes'))
            )
        conn.commit()

    # Read helpers for views
    def list_canonical_instruments(self) -> list:
        """List all canonical instruments"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT instrument_id, symbol, name FROM instruments WHERE role = 'CANONICAL' AND active = 1"
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_aliases(self, canonical_symbol: str) -> list:
        """Get aliases for a canonical symbol"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT symbol FROM instruments
               WHERE role = 'ALIAS' AND canonical_symbol = ? AND active = 1""",
            (canonical_symbol,)
        )
        return [row[0] for row in cursor.fetchall()]

    def get_active_cycle_spec(self, symbol: str, timeframe: str):
        """Get active cycle spec for symbol/timeframe"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            return None
        instrument_id = row[0]

        cursor.execute(
            """SELECT * FROM cycle_specs
               WHERE instrument_id = ? AND timeframe = ? AND status = 'ACTIVE'
               ORDER BY version DESC LIMIT 1""",
            (instrument_id, timeframe)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_active_projections(self, symbol: str, timeframe: str) -> list:
        """Get all active projections for symbol/timeframe"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            return []
        instrument_id = row[0]

        cursor.execute(
            """SELECT * FROM cycle_projections
               WHERE instrument_id = ? AND timeframe = ? AND active = 1
               ORDER BY median_index""",
            (instrument_id, timeframe)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_best_projection_for_asof(self, symbol: str, timeframe: str, asof_index: int):
        """Get most relevant projection for asof_index"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            return None
        instrument_id = row[0]

        # Find projection where asof is in prewindow or core window, or closest future projection
        cursor.execute(
            """SELECT * FROM cycle_projections
               WHERE instrument_id = ? AND timeframe = ? AND active = 1
                 AND (
                   (? BETWEEN prewindow_start_index AND core_end_index)
                   OR (median_index >= ?)
                 )
               ORDER BY
                 CASE WHEN ? BETWEEN prewindow_start_index AND core_end_index THEN 0 ELSE 1 END,
                 ABS(median_index - ?)
               LIMIT 1""",
            (instrument_id, timeframe, asof_index, asof_index, asof_index, asof_index)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_latest_notes(self, symbol: str, asof_td_label: str, limit: int = 3) -> list:
        """Get latest N notes for symbol up to asof date"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            return []
        instrument_id = row[0]

        cursor.execute(
            """SELECT * FROM desk_notes
               WHERE instrument_id = ? AND asof_td_label <= ?
               ORDER BY asof_td_label DESC, created_at DESC
               LIMIT ?""",
            (instrument_id, asof_td_label, limit)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_daily_calendar(self, symbol: str) -> list:
        """Get daily trading calendar for symbol"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            return []
        instrument_id = row[0]

        cursor.execute(
            """SELECT td_index, trading_date_label FROM trading_calendar_daily
               WHERE instrument_id = ?
               ORDER BY td_index""",
            (instrument_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_weekly_calendar(self, symbol: str) -> list:
        """Get weekly trading calendar for symbol"""
        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (symbol,))
        row = cursor.fetchone()
        if not row:
            return []
        instrument_id = row[0]

        cursor.execute(
            """SELECT tw_index, week_end_label FROM trading_calendar_weekly
               WHERE instrument_id = ?
               ORDER BY tw_index""",
            (instrument_id,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def add_astro_event(self, instrument_symbol: str, event_label: str, role: str,
                       name: str = None, category: str = None, confidence: int = None,
                       source: str = None, notes: str = None) -> int:
        """Add astro event for instrument

        Args:
            instrument_symbol: Instrument symbol (will resolve to canonical)
            event_label: Date label (YYYY-MM-DD)
            role: PRIMARY or BACKUP
            name: Event name
            category: REVERSAL/RISK/VOL/LIQUIDITY/OTHER
            confidence: Confidence level (0-100)
            source: Source of the event
            notes: Additional notes

        Returns:
            astro_id
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Resolve to canonical instrument
        cursor.execute(
            "SELECT instrument_id, canonical_symbol FROM instruments WHERE symbol = ?",
            (instrument_symbol,)
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument {instrument_symbol} not found")

        instrument_id = row['instrument_id']
        canonical_symbol = row['canonical_symbol']

        # Get daily calendar to resolve td_index
        daily_cal = self.get_daily_calendar(canonical_symbol)
        if not daily_cal:
            raise ValueError(f"No daily calendar for {canonical_symbol}")

        # Find td_index for event_label (snap to next trading day >= event_label)
        td_index = None
        for day in daily_cal:
            if day['trading_date_label'] >= event_label:
                td_index = day['td_index']
                break

        if td_index is None:
            raise ValueError(f"Event date {event_label} is beyond calendar range")

        # Insert astro event
        cursor.execute(
            """INSERT INTO astro_events
               (instrument_id, event_label, td_index, role, name, category,
                confidence, source, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (instrument_id, event_label, td_index, role, name, category,
             confidence, source, notes, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid

    def list_upcoming_astro(self, instrument_symbol: str, asof_td_index: int,
                           horizon_td: int = 15) -> dict:
        """List upcoming astro events

        Args:
            instrument_symbol: Instrument symbol
            asof_td_index: Current td_index
            horizon_td: Horizon in trading days

        Returns:
            {
                'next_primary': {...} or None,
                'backup_events': [...]
            }
        """
        conn = self.connect()
        cursor = conn.cursor()

        # Get canonical instrument_id
        cursor.execute(
            "SELECT instrument_id, canonical_symbol FROM instruments WHERE symbol = ?",
            (instrument_symbol,)
        )
        row = cursor.fetchone()
        if not row:
            return {'next_primary': None, 'backup_events': []}

        instrument_id = row['instrument_id']

        # Get next PRIMARY event
        cursor.execute(
            """SELECT * FROM astro_events
               WHERE instrument_id = ? AND role = 'PRIMARY' AND td_index >= ?
               ORDER BY td_index LIMIT 1""",
            (instrument_id, asof_td_index)
        )
        next_primary = cursor.fetchone()
        next_primary_dict = dict(next_primary) if next_primary else None

        # Get BACKUP events within horizon
        cursor.execute(
            """SELECT * FROM astro_events
               WHERE instrument_id = ? AND role = 'BACKUP'
               AND td_index >= ? AND td_index < ?
               ORDER BY td_index""",
            (instrument_id, asof_td_index, asof_td_index + horizon_td)
        )
        backup_events = [dict(row) for row in cursor.fetchall()]

        return {
            'next_primary': next_primary_dict,
            'backup_events': backup_events
        }

    def append_desk_note_bullets(self, instrument_symbol: str, asof_td_label: str,
                                 new_bullets: list) -> bool:
        """Append bullets to existing desk note or create new one if doesn't exist

        Args:
            instrument_symbol: Instrument symbol
            asof_td_label: As-of trading date
            new_bullets: List of bullet points to append

        Returns:
            True if appended to existing, False if created new
        """
        import json

        conn = self.connect()
        cursor = conn.cursor()

        # Get instrument_id
        cursor.execute("SELECT instrument_id FROM instruments WHERE symbol = ?", (instrument_symbol,))
        row = cursor.fetchone()
        if not row:
            raise ValueError(f"Instrument {instrument_symbol} not found")
        instrument_id = row['instrument_id']

        # Check if note exists
        cursor.execute(
            """SELECT note_id, bullets_json FROM desk_notes
               WHERE instrument_id = ? AND asof_td_label = ?""",
            (instrument_id, asof_td_label)
        )
        existing = cursor.fetchone()

        if existing:
            # Append to existing note
            current_bullets = json.loads(existing['bullets_json'])

            # Remove SPX asterisk if present (will re-add at end)
            current_bullets = [b for b in current_bullets if b != "*Price levels reference SPX, not ES"]
            new_bullets_clean = [b for b in new_bullets if b != "*Price levels reference SPX, not ES"]

            # Combine and re-add asterisk
            combined = current_bullets + new_bullets_clean
            combined.append("*Price levels reference SPX, not ES")

            cursor.execute(
                "UPDATE desk_notes SET bullets_json = ? WHERE note_id = ?",
                (json.dumps(combined), existing['note_id'])
            )
            conn.commit()
            return True
        else:
            # No existing note - would need to create one
            # (User should call create_desk_note for first note)
            return False

    def create_analysis(self, symbol: str, as_of_date: str,
                       packet_path: str, skeleton_report_path: str,
                       final_report_path: Optional[str] = None) -> int:
        """Create analysis record"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO analysis
               (symbol, as_of_date, packet_path, skeleton_report_path,
                final_report_path, created_at)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(symbol, as_of_date) DO UPDATE SET
                   packet_path = excluded.packet_path,
                   skeleton_report_path = excluded.skeleton_report_path,
                   final_report_path = COALESCE(excluded.final_report_path, final_report_path)
            """,
            (symbol, as_of_date, packet_path, skeleton_report_path,
             final_report_path, datetime.now().isoformat())
        )
        conn.commit()
        return cursor.lastrowid
