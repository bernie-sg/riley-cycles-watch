-- Riley Project - Price Bars Daily Table
-- Migration: 006
-- Created: 2025-12-26
-- Purpose: Store daily OHLCV price data for market instruments (feeds RRG)

CREATE TABLE IF NOT EXISTS price_bars_daily (
    symbol TEXT NOT NULL,
    date TEXT NOT NULL,
    open REAL NOT NULL,
    high REAL NOT NULL,
    low REAL NOT NULL,
    close REAL NOT NULL,
    adj_close REAL,
    volume INTEGER,
    source TEXT DEFAULT 'yfinance',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (symbol, date)
);

CREATE INDEX IF NOT EXISTS idx_price_bars_date ON price_bars_daily(date);
CREATE INDEX IF NOT EXISTS idx_price_bars_symbol ON price_bars_daily(symbol);
CREATE INDEX IF NOT EXISTS idx_price_bars_symbol_date ON price_bars_daily(symbol, date);
