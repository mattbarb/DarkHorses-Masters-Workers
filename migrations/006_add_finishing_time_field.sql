-- ============================================================================
-- DATABASE MIGRATION: Add Finishing Time Field
-- ============================================================================
-- Purpose: Add finishing_time field to ra_runners (was in migration 005 but may be missing)
-- Date: 2025-10-14
-- Related: DATA_SOURCES_FOR_API.md
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: ADD FINISHING TIME IF NOT EXISTS
-- ============================================================================

-- Add finishing_time if it doesn't exist
-- (Migration 005 added this but we want to be safe)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_runners' AND column_name = 'finishing_time'
    ) THEN
        ALTER TABLE ra_runners ADD COLUMN finishing_time VARCHAR(20);
        RAISE NOTICE 'Added finishing_time column';
    ELSE
        RAISE NOTICE 'finishing_time column already exists';
    END IF;
END $$;

-- Document column
COMMENT ON COLUMN ra_runners.finishing_time IS 'Race finishing time (e.g., "1:48.55") from results API';

-- ============================================================================
-- SECTION 2: VALIDATION
-- ============================================================================

-- Verify all position/result fields exist
DO $$
DECLARE
    missing_columns INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('position'),
        ('distance_beaten'),
        ('prize_won'),
        ('starting_price'),
        ('finishing_time'),
        ('result_updated_at')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_runners'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % result columns in ra_runners', missing_columns;
    END IF;

    RAISE NOTICE 'All result columns verified in ra_runners';
END $$;

-- ============================================================================
-- SECTION 3: SUMMARY REPORT
-- ============================================================================

SELECT
    '✓ Migration 006 Complete - Result Fields Verified' AS status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_runners') AS ra_runners_column_count,
    NOW() AS completed_at;

-- List all result-related columns
SELECT 'Result-related ra_runners columns:' AS info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN ('position', 'distance_beaten', 'prize_won', 'starting_price', 'finishing_time', 'result_updated_at')
ORDER BY column_name;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Expected result: All result fields present and documented

-- For rollback (if needed):
-- ALTER TABLE ra_runners DROP COLUMN IF EXISTS finishing_time;

-- ============================================================================
