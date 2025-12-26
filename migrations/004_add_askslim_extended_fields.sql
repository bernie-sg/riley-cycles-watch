-- Migration: Add extended askSlim fields
-- Adds support for directional bias, key levels, and video analysis

-- Add support and resistance levels to cycle_specs
ALTER TABLE cycle_specs ADD COLUMN support_level REAL;
ALTER TABLE cycle_specs ADD COLUMN resistance_level REAL;

-- Create table for instrument-level analysis data
CREATE TABLE IF NOT EXISTS instrument_analysis (
    analysis_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL REFERENCES instruments(instrument_id),
    directional_bias TEXT CHECK(directional_bias IN ('Bullish', 'Bearish', 'Neutral', NULL)),
    video_url TEXT,
    source TEXT NOT NULL DEFAULT 'askSlim',
    version INTEGER NOT NULL DEFAULT 1,
    status TEXT NOT NULL DEFAULT 'ACTIVE' CHECK(status IN ('ACTIVE', 'SUPERSEDED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_instrument_analysis_active
    ON instrument_analysis(instrument_id, status, version);
