-- Migration 003: Add astro events support

CREATE TABLE IF NOT EXISTS astro_events (
    astro_id INTEGER PRIMARY KEY AUTOINCREMENT,
    instrument_id INTEGER NOT NULL,
    event_label TEXT NOT NULL,           -- YYYY-MM-DD (display)
    td_index INTEGER NOT NULL,            -- resolved trading-day index
    role TEXT NOT NULL CHECK(role IN ('PRIMARY','BACKUP')),
    name TEXT,
    category TEXT,                        -- REVERSAL / RISK / VOL / LIQUIDITY / OTHER
    confidence INTEGER,
    source TEXT,
    notes TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY (instrument_id) REFERENCES instruments(instrument_id),
    UNIQUE(instrument_id, td_index, role)
);

CREATE INDEX idx_astro_instrument_td ON astro_events(instrument_id, td_index);
CREATE INDEX idx_astro_instrument_role ON astro_events(instrument_id, role);
