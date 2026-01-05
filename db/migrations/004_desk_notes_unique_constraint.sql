-- Migration 004: Enforce unique desk note per instrument/date

-- Drop existing desk_notes table and recreate with UNIQUE constraint
-- (Safe because we only have 1 note currently)

DROP TABLE IF EXISTS desk_notes;

CREATE TABLE desk_notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL,
    asof_td_label TEXT NOT NULL,
    author TEXT NOT NULL,
    source TEXT,
    timeframe_scope TEXT CHECK(timeframe_scope IN ('DAILY','WEEKLY','BOTH')),
    note_type TEXT CHECK(note_type IN ('NARRATIVE','LEVELS','CYCLES','RISK','SUMMARY')),
    price_reference TEXT CHECK(price_reference IN ('ES','SPX','SPY','OTHER')),
    bullets_json TEXT NOT NULL,
    tags_json TEXT,
    range_state TEXT CHECK(range_state IN ('RANGE','TREND_UP','TREND_DOWN','UNKNOWN')),
    cycle_trough_start_label TEXT,
    cycle_trough_end_label TEXT,
    downside_zone_low REAL,
    downside_zone_high REAL,
    invalidation_rule TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT,
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id),
    UNIQUE(instrument_id, asof_td_label)  -- ONE NOTE PER DATE
);

CREATE INDEX IF NOT EXISTS idx_desk_notes_instrument_asof ON desk_notes(instrument_id, asof_td_label);
