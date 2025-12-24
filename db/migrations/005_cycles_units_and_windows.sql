-- Migration 005: Cycles Units and Windows
-- Separate DAILY (TD) and WEEKLY (TW) indices to prevent calendar mixing

BEGIN TRANSACTION;

-- =============================================================================
-- 0. DELETE ALL CORRUPTED PROJECTIONS (fresh start)
-- =============================================================================

DELETE FROM cycle_projections;

-- =============================================================================
-- 1. CYCLE_PROJECTIONS: Add unit-specific index columns
-- =============================================================================

-- DAILY index fields (TD = trading day)
ALTER TABLE cycle_projections ADD COLUMN median_td_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN core_start_td_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN core_end_td_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN prewindow_start_td_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN prewindow_end_td_index INTEGER;

-- WEEKLY index fields (TW = trading week)
ALTER TABLE cycle_projections ADD COLUMN median_tw_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN core_start_tw_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN core_end_tw_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN prewindow_start_tw_index INTEGER;
ALTER TABLE cycle_projections ADD COLUMN prewindow_end_tw_index INTEGER;

-- Resolved label fields (for display)
ALTER TABLE cycle_projections ADD COLUMN core_start_label TEXT;
ALTER TABLE cycle_projections ADD COLUMN core_end_label TEXT;
ALTER TABLE cycle_projections ADD COLUMN prewindow_start_label TEXT;
ALTER TABLE cycle_projections ADD COLUMN prewindow_end_label TEXT;

-- =============================================================================
-- 2. UNIQUENESS CONSTRAINT (prevents duplicates forever)
-- =============================================================================

CREATE UNIQUE INDEX IF NOT EXISTS uq_cycle_proj
ON cycle_projections(instrument_id, timeframe, version, k);

-- =============================================================================
-- 3. PERFORMANCE INDEXES
-- =============================================================================

CREATE INDEX IF NOT EXISTS idx_cycle_specs_active
ON cycle_specs(instrument_id, timeframe, status);

CREATE INDEX IF NOT EXISTS idx_tcd_lookup
ON trading_calendar_daily(td_index);

CREATE INDEX IF NOT EXISTS idx_tcw_lookup
ON trading_calendar_weekly(tw_index);

COMMIT;
