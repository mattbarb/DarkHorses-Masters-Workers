-- ============================================================================
-- SMALLEST POSSIBLE BATCH - Run this 100+ times
-- ============================================================================
-- STRATEGY: Update only 1000 records per run to avoid ANY timeout
-- Copy this entire file, paste in Supabase SQL Editor, run repeatedly
-- ============================================================================

-- Update 1000 weight records
UPDATE ra_runners
SET weight = (api_data->>'weight_lbs')::INTEGER,
    weight_lbs = (api_data->>'weight_lbs')::INTEGER
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'weight_lbs' IS NOT NULL
      AND weight IS NULL
    LIMIT 1000
);

-- Update 1000 finishing_time records
UPDATE ra_runners
SET finishing_time = api_data->>'time'
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'time' IS NOT NULL
      AND finishing_time IS NULL
    LIMIT 1000
);

-- Update 1000 starting_price_decimal records
UPDATE ra_runners
SET starting_price_decimal = (api_data->>'sp_dec')::DECIMAL
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'sp_dec' IS NOT NULL
      AND starting_price_decimal IS NULL
    LIMIT 1000
);

-- Update 1000 race_comment records
UPDATE ra_runners
SET race_comment = api_data->>'comment',
    comment = api_data->>'comment'
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'comment' IS NOT NULL
      AND race_comment IS NULL
    LIMIT 1000
);

-- Update 1000 jockey_silk_url records
UPDATE ra_runners
SET jockey_silk_url = api_data->>'silk_url',
    silk_url = api_data->>'silk_url'
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'silk_url' IS NOT NULL
      AND jockey_silk_url IS NULL
    LIMIT 1000
);

-- Update 1000 overall_beaten_distance records
UPDATE ra_runners
SET overall_beaten_distance = (api_data->>'ovr_btn')::DECIMAL
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'ovr_btn' IS NOT NULL
      AND overall_beaten_distance IS NULL
    LIMIT 1000
);

-- Update 1000 jockey_claim_lbs records
UPDATE ra_runners
SET jockey_claim_lbs = (api_data->>'jockey_claim_lbs')::INTEGER
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'jockey_claim_lbs' IS NOT NULL
      AND jockey_claim_lbs IS NULL
    LIMIT 1000
);

-- Update 1000 weight_stones_lbs records
UPDATE ra_runners
SET weight_stones_lbs = api_data->>'weight'
WHERE runner_id IN (
    SELECT runner_id FROM ra_runners
    WHERE api_data->>'weight' IS NOT NULL
      AND weight_stones_lbs IS NULL
    LIMIT 1000
);

-- Show progress
SELECT
    'Progress: ' ||
    COUNT(CASE WHEN weight IS NOT NULL THEN 1 END) || ' weight, ' ||
    COUNT(CASE WHEN finishing_time IS NOT NULL THEN 1 END) || ' time, ' ||
    COUNT(CASE WHEN starting_price_decimal IS NOT NULL THEN 1 END) || ' sp_dec'
    as result
FROM ra_runners;

-- ============================================================================
-- INSTRUCTIONS:
-- 1. Copy this entire file
-- 2. Paste in Supabase SQL Editor
-- 3. Click "Run"
-- 4. Wait 10-20 seconds
-- 5. Repeat 100-150 times (or until progress stops increasing)
--
-- Each run updates 8000 records (1000 per field × 8 fields)
-- Total runs needed: ~150 to complete 1.2M records
-- Can run in background while working on other tasks
--
-- To check remaining:
-- SELECT COUNT(*) FROM ra_runners WHERE weight IS NULL AND api_data->>'weight_lbs' IS NOT NULL;
-- ============================================================================
