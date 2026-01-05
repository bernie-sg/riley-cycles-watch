-- Migration 005: Media Management System
-- Creates media_files table to track all charts/images with categorization
-- Enables separate handling of auto-scraped (askslim) vs manual uploads (tradingview/other)

CREATE TABLE IF NOT EXISTS media_files (
    media_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL,
    category TEXT NOT NULL CHECK(category IN ('askslim', 'tradingview', 'other')),
    timeframe TEXT CHECK(timeframe IN ('DAILY', 'WEEKLY', NULL)),
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    upload_date TEXT NOT NULL,
    source TEXT CHECK(source IN ('scraper', 'manual')),
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id) ON DELETE CASCADE,
    UNIQUE(instrument_id, category, timeframe, file_name)
);

-- Index for fast lookups by instrument and category
CREATE INDEX IF NOT EXISTS idx_media_instrument_category
ON media_files(instrument_id, category);

-- Index for date-based queries
CREATE INDEX IF NOT EXISTS idx_media_upload_date
ON media_files(upload_date DESC);
