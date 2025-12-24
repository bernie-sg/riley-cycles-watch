-- Migration 005: Add taxonomy fields to instruments table
-- Purpose: Enable UI sorting/grouping by instrument type, sector, and custom groups

-- Add taxonomy columns
ALTER TABLE instruments ADD COLUMN instrument_type TEXT DEFAULT 'FUTURES';
ALTER TABLE instruments ADD COLUMN sector TEXT DEFAULT 'UNCLASSIFIED';
ALTER TABLE instruments ADD COLUMN group_name TEXT DEFAULT 'FUTURES';
ALTER TABLE instruments ADD COLUMN sort_key INTEGER DEFAULT 1000;

-- Create index for efficient sorting
CREATE INDEX IF NOT EXISTS idx_instruments_taxonomy
ON instruments(group_name, sector, sort_key, symbol);

-- Backfill common futures symbols
UPDATE instruments SET
    group_name = 'FUTURES',
    instrument_type = 'FUTURES',
    sort_key = 100
WHERE symbol IN ('ES', 'NQ', 'YM', 'RTY');

UPDATE instruments SET
    group_name = 'FUTURES',
    instrument_type = 'FUTURES',
    sector = 'ENERGY',
    sort_key = 200
WHERE symbol IN ('CL', 'NG', 'XLE');

UPDATE instruments SET
    group_name = 'FUTURES',
    instrument_type = 'FUTURES',
    sector = 'METALS',
    sort_key = 300
WHERE symbol IN ('GC', 'SI', 'PL', 'HG');

UPDATE instruments SET
    group_name = 'FUTURES',
    instrument_type = 'FUTURES',
    sector = 'AGRICULTURE',
    sort_key = 400
WHERE symbol IN ('ZC', 'ZS', 'ZW');

UPDATE instruments SET
    group_name = 'FUTURES',
    instrument_type = 'FUTURES',
    sector = 'FIXED_INCOME',
    sort_key = 500
WHERE symbol IN ('ZB', 'ZN', 'ZF', 'ZT');

UPDATE instruments SET
    group_name = 'FX',
    instrument_type = 'FX',
    sector = 'CURRENCIES',
    sort_key = 600
WHERE symbol IN ('DXY', 'EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD', 'USDCAD', '6E', '6J', '6B');

UPDATE instruments SET
    group_name = 'CRYPTO',
    instrument_type = 'CRYPTO',
    sector = 'DIGITAL_ASSETS',
    sort_key = 700
WHERE symbol IN ('BTC');

UPDATE instruments SET
    group_name = 'EQUITY',
    instrument_type = 'EQUITY',
    sector = 'TECH',
    sort_key = 800
WHERE symbol IN ('NVDA');
