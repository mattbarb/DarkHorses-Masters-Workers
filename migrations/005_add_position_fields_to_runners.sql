-- ============================================================================
-- DATABASE MIGRATION: Add Position and Result Fields to ra_runners
-- ============================================================================
-- Purpose: Enable ML model to learn win patterns by capturing finishing positions
-- Date: 2025-10-14
-- Critical: Without this data, ML model cannot calculate win rates (currently 0%)
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: ADD POSITION AND RESULT COLUMNS TO ra_runners
-- ============================================================================

-- Add position and result fields
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS position INTEGER;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS distance_beaten VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS prize_won DECIMAL(10,2);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS starting_price VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS result_updated_at TIMESTAMP;

-- Document columns
COMMENT ON COLUMN ra_runners.position IS 'Finishing position (1st, 2nd, 3rd, etc.). NULL for special cases like fell (F), unseated (U), pulled up (PU)';
COMMENT ON COLUMN ra_runners.distance_beaten IS 'Distance behind winner (e.g., "2.5L", "nk", "hd", "sht-hd")';
COMMENT ON COLUMN ra_runners.prize_won IS 'Prize money won in this race';
COMMENT ON COLUMN ra_runners.starting_price IS 'Starting price/odds (e.g., "5/1", "7/2", "evens")';
COMMENT ON COLUMN ra_runners.result_updated_at IS 'Timestamp when result data was last updated';

-- ============================================================================
-- SECTION 2: ADD INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index for position queries (filter out NULL values for efficiency)
CREATE INDEX IF NOT EXISTS idx_runners_position ON ra_runners(position) WHERE position IS NOT NULL;

-- Index for result_updated_at (helps identify which records have results)
CREATE INDEX IF NOT EXISTS idx_runners_result_updated ON ra_runners(result_updated_at) WHERE result_updated_at IS NOT NULL;

-- Composite index for analyzing winners
CREATE INDEX IF NOT EXISTS idx_runners_position_horse ON ra_runners(horse_id, position) WHERE position = 1;

-- ============================================================================
-- SECTION 3: VALIDATION
-- ============================================================================

-- Verify columns were added
DO $$
DECLARE
    missing_columns INTEGER;
BEGIN
    -- Check ra_runners columns
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('position'),
        ('distance_beaten'),
        ('prize_won'),
        ('starting_price'),
        ('result_updated_at')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_runners'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_runners', missing_columns;
    END IF;

    RAISE NOTICE 'All position columns added successfully to ra_runners';
END $$;

-- ============================================================================
-- SECTION 4: SUMMARY REPORT
-- ============================================================================

SELECT
    '✓ Migration 005 Complete - Position Fields Added' AS status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_runners') AS ra_runners_column_count,
    NOW() AS completed_at;

-- List new columns added
SELECT 'New ra_runners position columns:' AS info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN ('position', 'distance_beaten', 'prize_won', 'starting_price', 'result_updated_at')
ORDER BY column_name;

-- List new indexes created
SELECT 'New position indexes:' AS info;
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'ra_runners'
  AND indexname IN ('idx_runners_position', 'idx_runners_result_updated', 'idx_runners_position_horse')
ORDER BY indexname;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Next steps:
-- 1. Update fetchers/results_fetcher.py to extract position data from API
-- 2. Update utils/entity_extractor.py to include position fields in runner inserts
-- 3. Run results fetcher to populate position data
-- 4. Verify ML compilation can now calculate win rates
-- 5. Monitor that win rates are no longer all 0%

-- Expected impact:
-- - Enables 43% of ML schema fields (position-dependent calculations)
-- - Unlocks win_rate, place_rate, form_score calculations
-- - Allows ML model to learn which horses actually win races

-- For rollback (if needed):
-- DROP INDEX IF EXISTS idx_runners_position;
-- DROP INDEX IF EXISTS idx_runners_result_updated;
-- DROP INDEX IF EXISTS idx_runners_position_horse;
-- ALTER TABLE ra_runners
--   DROP COLUMN position,
--   DROP COLUMN distance_beaten,
--   DROP COLUMN prize_won,
--   DROP COLUMN starting_price,
--   DROP COLUMN result_updated_at;

-- ============================================================================
