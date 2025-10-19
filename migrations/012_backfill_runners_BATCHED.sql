-- ============================================================================
-- DATABASE MIGRATION 012: Backfill ra_runners Fields (BATCHED VERSION)
-- ============================================================================
-- Purpose: Extract field values from api_data JSONB in smaller batches
-- Date: 2025-10-17
-- ============================================================================
--
-- STRATEGY: Process 10,000 records at a time to avoid timeouts
-- RUN THIS MULTIPLE TIMES until no more rows are updated
--
-- ============================================================================

-- BATCH 1: Weight fields (limit 10,000 rows per run)
UPDATE ra_runners
SET
    weight = (api_data->>'weight_lbs')::INTEGER,
    weight_lbs = (api_data->>'weight_lbs')::INTEGER,
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'weight_lbs' IS NOT NULL
      AND weight IS NULL
    LIMIT 10000
);

-- Check how many rows were updated
SELECT 'Weight fields updated: ' || COUNT(*) as result
FROM ra_runners
WHERE weight IS NOT NULL;

-- ============================================================================
-- BATCH 2: Finishing time (limit 10,000 rows per run)
UPDATE ra_runners
SET
    finishing_time = api_data->>'time',
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'time' IS NOT NULL
      AND finishing_time IS NULL
    LIMIT 10000
);

SELECT 'Finishing time updated: ' || COUNT(*) as result
FROM ra_runners
WHERE finishing_time IS NOT NULL;

-- ============================================================================
-- BATCH 3: Starting price decimal (limit 10,000 rows per run)
UPDATE ra_runners
SET
    starting_price_decimal = (api_data->>'sp_dec')::DECIMAL,
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'sp_dec' IS NOT NULL
      AND starting_price_decimal IS NULL
    LIMIT 10000
);

SELECT 'Starting price decimal updated: ' || COUNT(*) as result
FROM ra_runners
WHERE starting_price_decimal IS NOT NULL;

-- ============================================================================
-- BATCH 4: Overall beaten distance (limit 10,000 rows per run)
UPDATE ra_runners
SET
    overall_beaten_distance = (api_data->>'ovr_btn')::DECIMAL,
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'ovr_btn' IS NOT NULL
      AND overall_beaten_distance IS NULL
    LIMIT 10000
);

SELECT 'Overall beaten distance updated: ' || COUNT(*) as result
FROM ra_runners
WHERE overall_beaten_distance IS NOT NULL;

-- ============================================================================
-- BATCH 5: Race comment (limit 10,000 rows per run)
UPDATE ra_runners
SET
    race_comment = api_data->>'comment',
    comment = api_data->>'comment',
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'comment' IS NOT NULL
      AND race_comment IS NULL
    LIMIT 10000
);

SELECT 'Race comment updated: ' || COUNT(*) as result
FROM ra_runners
WHERE race_comment IS NOT NULL;

-- ============================================================================
-- BATCH 6: Jockey silk URL (limit 10,000 rows per run)
UPDATE ra_runners
SET
    jockey_silk_url = api_data->>'silk_url',
    silk_url = api_data->>'silk_url',
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'silk_url' IS NOT NULL
      AND jockey_silk_url IS NULL
    LIMIT 10000
);

SELECT 'Jockey silk URL updated: ' || COUNT(*) as result
FROM ra_runners
WHERE jockey_silk_url IS NOT NULL;

-- ============================================================================
-- BATCH 7: Jockey claim lbs (limit 10,000 rows per run)
UPDATE ra_runners
SET
    jockey_claim_lbs = (api_data->>'jockey_claim_lbs')::INTEGER,
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'jockey_claim_lbs' IS NOT NULL
      AND jockey_claim_lbs IS NULL
    LIMIT 10000
);

SELECT 'Jockey claim lbs updated: ' || COUNT(*) as result
FROM ra_runners
WHERE jockey_claim_lbs IS NOT NULL;

-- ============================================================================
-- BATCH 8: Weight stones/lbs (limit 10,000 rows per run)
UPDATE ra_runners
SET
    weight_stones_lbs = api_data->>'weight',
    updated_at = NOW()
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'weight' IS NOT NULL
      AND weight_stones_lbs IS NULL
    LIMIT 10000
);

SELECT 'Weight stones/lbs updated: ' || COUNT(*) as result
FROM ra_runners
WHERE weight_stones_lbs IS NOT NULL;

-- ============================================================================
-- BATCH 9: Prize money (limit 10,000 rows per run)
-- Clean currency symbols
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
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data IS NOT NULL
      AND api_data->>'prize' IS NOT NULL
      AND api_data->>'prize' != ''
      AND prize_money_won IS NULL
      AND api_data->>'prize' ~ '^[£€$]?[0-9,]+\.?[0-9]*$'
    LIMIT 10000
);

SELECT 'Prize money won updated: ' || COUNT(*) as result
FROM ra_runners
WHERE prize_money_won IS NOT NULL;

-- ============================================================================
-- FINAL SUMMARY
-- ============================================================================
SELECT
    'SUMMARY: ' ||
    COUNT(CASE WHEN weight IS NOT NULL THEN 1 END) || ' have weight, ' ||
    COUNT(CASE WHEN finishing_time IS NOT NULL THEN 1 END) || ' have finishing_time, ' ||
    COUNT(CASE WHEN starting_price_decimal IS NOT NULL THEN 1 END) || ' have starting_price_decimal'
    as result
FROM ra_runners;

-- ============================================================================
-- INSTRUCTIONS:
-- 1. Run this script repeatedly (10-20 times) until no more rows are updated
-- 2. Each run processes 10,000 records per field (90,000 total updates)
-- 3. Takes ~1-2 minutes per run
-- 4. Total time: ~20-40 minutes for full 1.3M backfill
--
-- To check remaining work:
-- SELECT COUNT(*) FROM ra_runners WHERE weight IS NULL AND api_data->>'weight_lbs' IS NOT NULL;
-- ============================================================================
