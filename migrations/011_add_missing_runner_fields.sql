-- ============================================================================
-- DATABASE MIGRATION: Add Missing Runner Fields from Racing API
-- ============================================================================
-- Purpose: Capture 6 additional valuable fields from Racing API results
-- Date: 2025-10-17
-- Related: API Comprehensive Test Results, Field Analysis
-- ============================================================================
-- Fields being added:
--   1. sp_dec - Starting price in decimal format (e.g., 4.50) - CRITICAL for ML
--   2. comment - Race commentary/running notes - Valuable for qualitative analysis
--   3. silk_url - Jockey silk image URL - UI/display enhancement
--   4. ovr_btn - Overall beaten distance (alternative to btn) - ML feature
--   5. jockey_claim_lbs - Jockey weight allowance - Race conditions data
--   6. weight_stones_lbs - Weight in stones-lbs format (e.g., "8-13") - Display format
--
-- Note: finishing_time (from 'time' field) already exists from migration 006
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: ADD NEW FIELDS TO ra_runners
-- ============================================================================

-- Add starting price in decimal format (CRITICAL for ML odds analysis)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS starting_price_decimal DECIMAL(10,2);
COMMENT ON COLUMN ra_runners.starting_price_decimal IS 'Starting price in decimal format (e.g., 4.50 for 7/2). Easier for numerical analysis than fractional format.';

-- Add race commentary (VALUABLE for qualitative analysis)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS race_comment TEXT;
COMMENT ON COLUMN ra_runners.race_comment IS 'Race commentary/running notes describing how the horse ran (e.g., "Led, ridden 2f out, kept on well")';

-- Add jockey silk image URL (UI/display enhancement)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS jockey_silk_url TEXT;
COMMENT ON COLUMN ra_runners.jockey_silk_url IS 'URL to jockey silk image (SVG format from Racing Post assets)';

-- Add overall beaten distance (ML feature - alternative to btn)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS overall_beaten_distance DECIMAL(10,2);
COMMENT ON COLUMN ra_runners.overall_beaten_distance IS 'Overall beaten distance in lengths (e.g., 2.5). Alternative representation to distance_beaten field.';

-- Add jockey claim weight allowance (race conditions data)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS jockey_claim_lbs INTEGER;
COMMENT ON COLUMN ra_runners.jockey_claim_lbs IS 'Jockey weight allowance in pounds (e.g., 3, 5, 7). Zero if no claim.';

-- Add weight in stones-lbs format (display format for UK racing)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS weight_stones_lbs VARCHAR(10);
COMMENT ON COLUMN ra_runners.weight_stones_lbs IS 'Weight in stones-lbs format (e.g., "8-13" for 8 stone 13 pounds). UK/IRE display format.';

-- ============================================================================
-- SECTION 2: ADD INDEXES FOR PERFORMANCE
-- ============================================================================

-- Index on starting_price_decimal for odds analysis queries
CREATE INDEX IF NOT EXISTS idx_runners_sp_decimal
  ON ra_runners(starting_price_decimal)
  WHERE starting_price_decimal IS NOT NULL;

-- Index on overall_beaten_distance for performance analysis
CREATE INDEX IF NOT EXISTS idx_runners_ovr_btn
  ON ra_runners(overall_beaten_distance)
  WHERE overall_beaten_distance IS NOT NULL;

-- Index on jockey_claim_lbs for apprentice/conditional jockey analysis
CREATE INDEX IF NOT EXISTS idx_runners_jockey_claim
  ON ra_runners(jockey_claim_lbs)
  WHERE jockey_claim_lbs > 0;

-- ============================================================================
-- SECTION 3: VALIDATION
-- ============================================================================

-- Verify all new columns were added
DO $$
DECLARE
    missing_columns INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('starting_price_decimal'),
        ('race_comment'),
        ('jockey_silk_url'),
        ('overall_beaten_distance'),
        ('jockey_claim_lbs'),
        ('weight_stones_lbs')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_runners'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_runners', missing_columns;
    END IF;

    RAISE NOTICE 'All 6 new columns added successfully to ra_runners';
END $$;

-- ============================================================================
-- SECTION 4: SUMMARY REPORT
-- ============================================================================

SELECT
    '✓ Migration 011 Complete - Missing Runner Fields Added' AS status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_runners') AS ra_runners_total_columns,
    NOW() AS completed_at;

-- List newly added columns
SELECT 'Newly added ra_runners columns:' AS info;
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN (
    'starting_price_decimal',
    'race_comment',
    'jockey_silk_url',
    'overall_beaten_distance',
    'jockey_claim_lbs',
    'weight_stones_lbs'
  )
ORDER BY column_name;

-- List newly created indexes
SELECT 'New indexes created:' AS info;
SELECT indexname, tablename, indexdef
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename = 'ra_runners'
  AND indexname IN (
    'idx_runners_sp_decimal',
    'idx_runners_ovr_btn',
    'idx_runners_jockey_claim'
  )
ORDER BY indexname;

-- Display summary of all result-related columns
SELECT 'Summary: All result-related columns in ra_runners:' AS info;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN (
    -- Existing result fields
    'position',
    'distance_beaten',
    'prize_won',
    'starting_price',
    'finishing_time',
    'result_updated_at',
    -- Newly added fields
    'starting_price_decimal',
    'race_comment',
    'jockey_silk_url',
    'overall_beaten_distance',
    'jockey_claim_lbs',
    'weight_stones_lbs'
  )
ORDER BY column_name;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Next steps:
-- 1. Update fetchers/results_fetcher.py to capture new fields
-- 2. Update fetchers/races_fetcher.py to capture new fields (where available)
-- 3. Add helper methods for parsing decimal and integer values
-- 4. Run test script to verify field capture
-- 5. Execute backfill to populate historical data

-- Expected impact:
-- - sp_dec enables more accurate ML odds analysis (decimal format easier than fractions)
-- - comment provides qualitative data for future text analysis
-- - silk_url enhances UI/display capabilities
-- - ovr_btn provides alternative distance metric for ML features
-- - jockey_claim_lbs adds important race conditions data
-- - weight_stones_lbs provides proper UK/IRE display format

-- Field population rates (from API testing):
-- - sp_dec: 100% (all finished runners)
-- - comment: 100% (all finished runners)
-- - silk_url: 100% (all runners)
-- - ovr_btn: 100% (all finished runners)
-- - jockey_claim_lbs: 100% (0 if no claim)
-- - weight: 100% (all runners)

-- For rollback (if needed):
-- BEGIN;
-- DROP INDEX IF EXISTS idx_runners_sp_decimal;
-- DROP INDEX IF EXISTS idx_runners_ovr_btn;
-- DROP INDEX IF EXISTS idx_runners_jockey_claim;
-- ALTER TABLE ra_runners
--   DROP COLUMN IF EXISTS starting_price_decimal,
--   DROP COLUMN IF EXISTS race_comment,
--   DROP COLUMN IF EXISTS jockey_silk_url,
--   DROP COLUMN IF EXISTS overall_beaten_distance,
--   DROP COLUMN IF EXISTS jockey_claim_lbs,
--   DROP COLUMN IF EXISTS weight_stones_lbs;
-- COMMIT;

-- ============================================================================
