-- Riley Project - Cycles Watch Schema
-- Migration: 002
-- Created: 2025-12-19
-- Phase 1: Instruments, Trading Calendars, Cycle Specs, Projections, Desk Notes, Scans

-- Drop old instruments table if exists
DROP TABLE IF EXISTS instruments;

-- Instruments with canonical + alias support
CREATE TABLE IF NOT EXISTS instruments (
    instrument_id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    name TEXT,
    role TEXT NOT NULL CHECK(role IN ('CANONICAL','ALIAS')),
    canonical_symbol TEXT NOT NULL,
    alias_of_instrument_id INTEGER NULL REFERENCES instruments(instrument_id),
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    CHECK (
        (role = 'CANONICAL' AND alias_of_instrument_id IS NULL AND canonical_symbol = symbol)
        OR
        (role = 'ALIAS' AND alias_of_instrument_id IS NOT NULL AND canonical_symbol != symbol)
    )
);

-- Daily trading calendar
CREATE TABLE IF NOT EXISTS trading_calendar_daily (
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    td_index INTEGER NOT NULL,
    trading_date_label TEXT NOT NULL,
    PRIMARY KEY (instrument_id, td_index),
    UNIQUE (instrument_id, trading_date_label)
);

-- Weekly trading calendar
CREATE TABLE IF NOT EXISTS trading_calendar_weekly (
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    tw_index INTEGER NOT NULL,
    week_end_label TEXT NOT NULL,
    PRIMARY KEY (instrument_id, tw_index),
    UNIQUE (instrument_id, week_end_label)
);

-- Cycle specifications (versioned)
CREATE TABLE IF NOT EXISTS cycle_specs (
    cycle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL CHECK(timeframe IN ('DAILY','WEEKLY')),
    anchor_input_date_label TEXT NOT NULL,
    snap_rule TEXT NOT NULL DEFAULT 'NEXT_TRADING_DAY',
    cycle_length_bars INTEGER NOT NULL,
    window_minus_bars INTEGER NOT NULL,
    window_plus_bars INTEGER NOT NULL,
    prewindow_lead_bars INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE','SUPERSEDED')),
    source TEXT,
    confidence INTEGER,
    notes TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_cycle_specs_active
    ON cycle_specs(instrument_id, timeframe, status, version);

-- Cycle projections (k forward/backward)
CREATE TABLE IF NOT EXISTS cycle_projections (
    projection_id INTEGER PRIMARY KEY AUTOINCREMENT,
    cycle_id INTEGER NOT NULL REFERENCES cycle_specs(cycle_id),
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    timeframe TEXT NOT NULL CHECK(timeframe IN ('DAILY','WEEKLY')),
    version INTEGER NOT NULL,
    anchor_index INTEGER NOT NULL,
    anchor_label TEXT NOT NULL,
    k INTEGER NOT NULL,
    median_index INTEGER NOT NULL,
    median_label TEXT NOT NULL,
    core_start_index INTEGER NOT NULL,
    core_end_index INTEGER NOT NULL,
    prewindow_start_index INTEGER NOT NULL,
    prewindow_end_index INTEGER NOT NULL,
    computed_at TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    notes TEXT,
    CHECK (core_start_index <= median_index),
    CHECK (median_index <= core_end_index),
    CHECK (prewindow_start_index <= prewindow_end_index),
    CHECK (prewindow_end_index < core_start_index)
);

CREATE INDEX IF NOT EXISTS idx_projections_active
    ON cycle_projections(instrument_id, timeframe, active);
CREATE INDEX IF NOT EXISTS idx_projections_cycle
    ON cycle_projections(cycle_id, version, active);

-- Desk notes (bullet journal + structured zones)
CREATE TABLE IF NOT EXISTS desk_notes (
    note_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    asof_td_label TEXT NOT NULL,
    author TEXT NOT NULL,
    source TEXT,
    timeframe_scope TEXT NOT NULL CHECK(timeframe_scope IN ('DAILY','WEEKLY','BOTH')),
    note_type TEXT NOT NULL CHECK(note_type IN ('NARRATIVE','LEVELS','CYCLES','RISK','SUMMARY')),
    price_reference TEXT NOT NULL CHECK(price_reference IN ('ES','SPX','SPY','OTHER')),
    bullets_json TEXT NOT NULL,
    tags_json TEXT,
    range_state TEXT CHECK(range_state IN ('RANGE','TREND_UP','TREND_DOWN','UNKNOWN')),
    cycle_trough_start_label TEXT,
    cycle_trough_end_label TEXT,
    downside_zone_low REAL,
    downside_zone_high REAL,
    invalidation_rule TEXT,
    notes TEXT,
    created_at TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_desk_notes
    ON desk_notes(instrument_id, asof_td_label);

-- Daily scan runs
CREATE TABLE IF NOT EXISTS daily_scan_runs (
    scan_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_td_label TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Daily scan rows
CREATE TABLE IF NOT EXISTS daily_scan_rows (
    scan_row_id INTEGER PRIMARY KEY AUTOINCREMENT,
    scan_id INTEGER NOT NULL REFERENCES daily_scan_runs(scan_id),
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    daily_status TEXT NOT NULL CHECK(daily_status IN ('NONE','PREWINDOW','IN_WINDOW','POST')),
    weekly_status TEXT NOT NULL CHECK(weekly_status IN ('NONE','PREWINDOW','IN_WINDOW','POST')),
    days_to_daily_core_start INTEGER,
    weeks_to_weekly_core_start INTEGER,
    overlap_flag INTEGER NOT NULL DEFAULT 0,
    priority_score INTEGER NOT NULL DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_scan_rows_priority
    ON daily_scan_rows(scan_id, priority_score);
