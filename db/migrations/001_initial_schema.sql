-- Riley Project Initial Schema
-- Migration: 001
-- Created: 2025-12-18

CREATE TABLE IF NOT EXISTS runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    as_of_date TEXT NOT NULL,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    UNIQUE(as_of_date)
);

CREATE TABLE IF NOT EXISTS instruments (
    symbol TEXT PRIMARY KEY,
    type TEXT,
    source_preference TEXT
);

CREATE TABLE IF NOT EXISTS analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    as_of_date TEXT NOT NULL,
    packet_path TEXT NOT NULL,
    skeleton_report_path TEXT NOT NULL,
    final_report_path TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(symbol, as_of_date),
    FOREIGN KEY (symbol) REFERENCES instruments(symbol)
);

CREATE INDEX IF NOT EXISTS idx_runs_date ON runs(as_of_date);
CREATE INDEX IF NOT EXISTS idx_analysis_symbol_date ON analysis(symbol, as_of_date);
