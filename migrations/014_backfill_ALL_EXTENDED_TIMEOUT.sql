-- ============================================================================
-- FULL BACKFILL - Single Run with Extended Timeout
-- ============================================================================
-- STRATEGY: Attempt to process all records in one transaction with 40min timeout
-- ============================================================================

-- Set extended timeout for this session (40 minutes)
SET statement_timeout = '40min';
SET lock_timeout = '40min';

BEGIN;

-- ============================================================================
-- BATCH 1: Weight fields (all records)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET weight = (api_data->>'weight_lbs')::INTEGER,
        weight_lbs = (api_data->>'weight_lbs')::INTEGER,
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'weight_lbs' IS NOT NULL
      AND api_data->>'weight_lbs' ~ '^[0-9]+$'
      AND weight IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated weight: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 2: Finishing time (all records)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET finishing_time = api_data->>'time',
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'time' IS NOT NULL
      AND api_data->>'time' != ''
      AND finishing_time IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated finishing_time: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 3: Starting price decimal (all records, skip invalid)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET starting_price_decimal = (api_data->>'sp_dec')::DECIMAL,
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'sp_dec' IS NOT NULL
      AND api_data->>'sp_dec' != '-'
      AND api_data->>'sp_dec' ~ '^[0-9]+\.?[0-9]*$'
      AND starting_price_decimal IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated starting_price_decimal: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 4: Race comment (all records)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET race_comment = api_data->>'comment',
        comment = api_data->>'comment',
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'comment' IS NOT NULL
      AND api_data->>'comment' != ''
      AND race_comment IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated race_comment: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 5: Jockey silk URL (all records)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET jockey_silk_url = api_data->>'silk_url',
        silk_url = api_data->>'silk_url',
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'silk_url' IS NOT NULL
      AND api_data->>'silk_url' != ''
      AND jockey_silk_url IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated jockey_silk_url: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 6: Overall beaten distance (all records, skip invalid)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET overall_beaten_distance = (api_data->>'ovr_btn')::DECIMAL,
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'ovr_btn' IS NOT NULL
      AND api_data->>'ovr_btn' != '-'
      AND api_data->>'ovr_btn' ~ '^[0-9]+\.?[0-9]*$'
      AND overall_beaten_distance IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated overall_beaten_distance: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 7: Jockey claim lbs (all records)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET jockey_claim_lbs = (api_data->>'jockey_claim_lbs')::INTEGER,
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'jockey_claim_lbs' IS NOT NULL
      AND api_data->>'jockey_claim_lbs' ~ '^[0-9]+$'
      AND jockey_claim_lbs IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated jockey_claim_lbs: % rows', updated_count;
END $$;

-- ============================================================================
-- BATCH 8: Weight stones/lbs (all records)
-- ============================================================================
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    UPDATE ra_runners
    SET weight_stones_lbs = api_data->>'weight',
        updated_at = NOW()
    WHERE api_data IS NOT NULL
      AND api_data->>'weight' IS NOT NULL
      AND api_data->>'weight' != ''
      AND weight_stones_lbs IS NULL;

    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated weight_stones_lbs: % rows', updated_count;
END $$;

-- ============================================================================
-- FINAL SUMMARY
-- ============================================================================
DO $$
DECLARE
    total_runners INTEGER;
    weight_populated INTEGER;
    finishing_time_populated INTEGER;
    starting_price_decimal_populated INTEGER;
    race_comment_populated INTEGER;
    jockey_silk_url_populated INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_runners FROM ra_runners;
    SELECT COUNT(*) INTO weight_populated FROM ra_runners WHERE weight IS NOT NULL;
    SELECT COUNT(*) INTO finishing_time_populated FROM ra_runners WHERE finishing_time IS NOT NULL;
    SELECT COUNT(*) INTO starting_price_decimal_populated FROM ra_runners WHERE starting_price_decimal IS NOT NULL;
    SELECT COUNT(*) INTO race_comment_populated FROM ra_runners WHERE race_comment IS NOT NULL;
    SELECT COUNT(*) INTO jockey_silk_url_populated FROM ra_runners WHERE jockey_silk_url IS NOT NULL;

    RAISE NOTICE '========================================';
    RAISE NOTICE 'BACKFILL COMPLETE';
    RAISE NOTICE '========================================';
    RAISE NOTICE 'Total runners: %', total_runners;
    RAISE NOTICE 'weight: % (%.1f%%)', weight_populated, (weight_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'finishing_time: % (%.1f%%)', finishing_time_populated, (finishing_time_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'starting_price_decimal: % (%.1f%%)', starting_price_decimal_populated, (starting_price_decimal_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'race_comment: % (%.1f%%)', race_comment_populated, (race_comment_populated::FLOAT / total_runners * 100);
    RAISE NOTICE 'jockey_silk_url: % (%.1f%%)', jockey_silk_url_populated, (jockey_silk_url_populated::FLOAT / total_runners * 100);
    RAISE NOTICE '========================================';
END $$;

COMMIT;

-- Reset timeout to default
RESET statement_timeout;
RESET lock_timeout;

-- ============================================================================
-- INSTRUCTIONS:
-- 1. Copy this entire file
-- 2. Paste in Supabase SQL Editor
-- 3. Click "Run"
-- 4. Wait up to 40 minutes (it may finish much sooner)
-- 5. Check the notices/logs for row counts
--
-- If this times out despite the 40min setting, Supabase may be enforcing
-- a hard timeout limit that cannot be overridden. In that case, you'll need
-- to use the smaller batch file (013_backfill_SMALLEST_BATCH_FIXED.sql)
-- ============================================================================
