-- ============================================================================
-- DATABASE MIGRATION 012: Backfill ra_runners Fields from api_data
-- ============================================================================
-- Purpose: Extract field values from api_data JSONB to populate NULL columns
-- Date: 2025-10-17
-- Related: FIELD_MAPPING_FIXES_SUMMARY.md
-- ============================================================================
--
-- WHAT THIS MIGRATION DOES:
-- Extracts correctly mapped field values from the api_data JSONB column
-- and populates the dedicated columns that were previously NULL due to
-- incorrect field name mappings in the fetchers.
--
-- IMPORTANT NOTES:
-- - This is a one-time backfill for historical data
-- - Future data will be captured correctly by updated fetchers
-- - Run this migration during off-peak hours (may take 10-20 minutes)
-- - Safe to run multiple times (idempotent - only updates NULL fields)
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: BACKFILL WEIGHT FIELDS
-- ============================================================================

-- Update weight and weight_lbs from api_data->>'weight_lbs'
UPDATE ra_runners
SET
    weight = (api_data->>'weight_lbs')::INTEGER,
    weight_lbs = (api_data->>'weight_lbs')::INTEGER,
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'weight_lbs' IS NOT NULL
    AND weight IS NULL;

-- Log progress
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated weight fields: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 2: BACKFILL FORM FIELDS
-- ============================================================================

-- Update form and form_string from api_data->>'form_string'
-- Note: Many records won't have this field (API doesn't always provide)
UPDATE ra_runners
SET
    form = api_data->>'form_string',
    form_string = api_data->>'form_string',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'form_string' IS NOT NULL
    AND form IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated form fields: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 3: BACKFILL PRIZE MONEY
-- ============================================================================

-- Update prize_money_won from api_data->>'prize'
-- Clean currency symbols (£, €, $) before converting to numeric
UPDATE ra_runners
SET
    prize_money_won = (
        REPLACE(
            REPLACE(
                REPLACE(
                    REPLACE(api_data->>'prize', '£', ''),
                    '€', ''
                ),
                '$', ''
            ),
            ',', ''
        )
    )::NUMERIC,
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'prize' IS NOT NULL
    AND api_data->>'prize' != ''
    AND prize_money_won IS NULL
    AND api_data->>'prize' ~ '^[£€$]?[0-9,]+\.?[0-9]*$';  -- Only update if valid numeric format

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated prize_money_won: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 4: BACKFILL COMMENT AND SILK FIELDS
-- ============================================================================

-- Update comment from api_data->>'comment'
UPDATE ra_runners
SET
    comment = api_data->>'comment',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'comment' IS NOT NULL
    AND comment IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated comment: % rows', updated_count;
END $$;

-- Update silk_url from api_data->>'silk_url'
UPDATE ra_runners
SET
    silk_url = api_data->>'silk_url',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'silk_url' IS NOT NULL
    AND silk_url IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated silk_url: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 5: BACKFILL MIGRATION 011 FIELDS - FINISHING TIME
-- ============================================================================

-- Update finishing_time from api_data->>'time'
UPDATE ra_runners
SET
    finishing_time = api_data->>'time',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'time' IS NOT NULL
    AND finishing_time IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated finishing_time: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 6: BACKFILL MIGRATION 011 FIELDS - STARTING PRICE DECIMAL
-- ============================================================================

-- Update starting_price_decimal from api_data->>'sp_dec'
UPDATE ra_runners
SET
    starting_price_decimal = (api_data->>'sp_dec')::DECIMAL,
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'sp_dec' IS NOT NULL
    AND starting_price_decimal IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated starting_price_decimal: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 7: BACKFILL MIGRATION 011 FIELDS - BEATEN DISTANCE
-- ============================================================================

-- Update overall_beaten_distance from api_data->>'ovr_btn'
UPDATE ra_runners
SET
    overall_beaten_distance = (api_data->>'ovr_btn')::DECIMAL,
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'ovr_btn' IS NOT NULL
    AND overall_beaten_distance IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated overall_beaten_distance: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 8: BACKFILL MIGRATION 011 FIELDS - JOCKEY CLAIM
-- ============================================================================

-- Update jockey_claim_lbs from api_data->>'jockey_claim_lbs'
UPDATE ra_runners
SET
    jockey_claim_lbs = (api_data->>'jockey_claim_lbs')::INTEGER,
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'jockey_claim_lbs' IS NOT NULL
    AND jockey_claim_lbs IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated jockey_claim_lbs: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 9: BACKFILL MIGRATION 011 FIELDS - WEIGHT STONES/LBS
-- ============================================================================

-- Update weight_stones_lbs from api_data->>'weight' (format: "9-8")
UPDATE ra_runners
SET
    weight_stones_lbs = api_data->>'weight',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'weight' IS NOT NULL
    AND weight_stones_lbs IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated weight_stones_lbs: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 10: BACKFILL MIGRATION 011 FIELDS - RACE COMMENT
-- ============================================================================

-- Update race_comment from api_data->>'comment' (same as comment field)
UPDATE ra_runners
SET
    race_comment = api_data->>'comment',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'comment' IS NOT NULL
    AND race_comment IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated race_comment: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 11: BACKFILL MIGRATION 011 FIELDS - JOCKEY SILK URL
-- ============================================================================

-- Update jockey_silk_url from api_data->>'silk_url' (same as silk_url field)
UPDATE ra_runners
SET
    jockey_silk_url = api_data->>'silk_url',
    updated_at = NOW()
WHERE
    api_data IS NOT NULL
    AND api_data->>'silk_url' IS NOT NULL
    AND jockey_silk_url IS NULL;

DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated jockey_silk_url: % rows', updated_count;
END $$;

-- ============================================================================
-- SECTION 12: VERIFY BACKFILL RESULTS
-- ============================================================================

-- Generate summary report
DO $$
DECLARE
    total_runners INTEGER;
    weight_populated INTEGER;
    form_populated INTEGER;
    finishing_time_populated INTEGER;
    starting_price_decimal_populated INTEGER;
    race_comment_populated INTEGER;
    jockey_silk_url_populated INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_runners FROM ra_runners;
    SELECT COUNT(*) INTO weight_populated FROM ra_runners WHERE weight IS NOT NULL;
    SELECT COUNT(*) INTO form_populated FROM ra_runners WHERE form IS NOT NULL;
    SELECT COUNT(*) INTO finishing_time_populated FROM ra_runners WHERE finishing_time IS NOT NULL;
    SELECT COUNT(*) INTO starting_price_decimal_populated FROM ra_runners WHERE starting_price_decimal IS NOT NULL;
    SELECT COUNT(*) INTO race_comment_populated FROM ra_runners WHERE race_comment IS NOT NULL;
    SELECT COUNT(*) INTO jockey_silk_url_populated FROM ra_runners WHERE jockey_silk_url IS NOT NULL;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'BACKFILL COMPLETE - SUMMARY';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total runners: %', total_runners;
    RAISE NOTICE 'weight populated: % (%.1f%%)', weight_populated, (weight_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'form populated: % (%.1f%%)', form_populated, (form_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'finishing_time populated: % (%.1f%%)', finishing_time_populated, (finishing_time_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'starting_price_decimal populated: % (%.1f%%)', starting_price_decimal_populated, (starting_price_decimal_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'race_comment populated: % (%.1f%%)', race_comment_populated, (race_comment_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'jockey_silk_url populated: % (%.1f%%)', jockey_silk_url_populated, (jockey_silk_url_populated::FLOAT / total_runners * 100);
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next steps:
-- 1. Verify field population with: SELECT COUNT(*) FROM ra_runners WHERE weight IS NOT NULL;
-- 2. Test ML models with newly populated fields
-- 3. Schedule future fetches to use updated fetcher code
-- ============================================================================
