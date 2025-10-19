-- ============================================================================
-- BACKFILL USING POSTGRESQL FUNCTIONS (RPC Approach)
-- ============================================================================
-- STRATEGY: Create PostgreSQL functions that can be called via Supabase RPC
-- Each function processes one field completely in batches
-- ============================================================================

-- FUNCTION 1: Backfill weight field
CREATE OR REPLACE FUNCTION backfill_weight_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET weight = (api_data->>'weight_lbs')::INTEGER,
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'weight_lbs' IS NOT NULL
              AND api_data->>'weight_lbs' ~ '^[0-9]+$'
              AND weight IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'weight',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 2: Backfill finishing_time field
CREATE OR REPLACE FUNCTION backfill_finishing_time_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET finishing_time = api_data->>'time',
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'time' IS NOT NULL
              AND api_data->>'time' != ''
              AND finishing_time IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'finishing_time',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 3: Backfill starting_price_decimal field
CREATE OR REPLACE FUNCTION backfill_starting_price_decimal_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET starting_price_decimal = (api_data->>'sp_dec')::DECIMAL,
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'sp_dec' IS NOT NULL
              AND api_data->>'sp_dec' != '-'
              AND api_data->>'sp_dec' ~ '^[0-9]+\.?[0-9]*$'
              AND starting_price_decimal IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'starting_price_decimal',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 4: Backfill overall_beaten_distance field
CREATE OR REPLACE FUNCTION backfill_overall_beaten_distance_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET overall_beaten_distance = (api_data->>'ovr_btn')::DECIMAL,
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'ovr_btn' IS NOT NULL
              AND api_data->>'ovr_btn' != '-'
              AND api_data->>'ovr_btn' ~ '^[0-9]+\.?[0-9]*$'
              AND overall_beaten_distance IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'overall_beaten_distance',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 5: Backfill jockey_claim_lbs field
CREATE OR REPLACE FUNCTION backfill_jockey_claim_lbs_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET jockey_claim_lbs = (api_data->>'jockey_claim_lbs')::INTEGER,
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'jockey_claim_lbs' IS NOT NULL
              AND api_data->>'jockey_claim_lbs' ~ '^[0-9]+$'
              AND jockey_claim_lbs IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'jockey_claim_lbs',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 6: Backfill weight_stones_lbs field
CREATE OR REPLACE FUNCTION backfill_weight_stones_lbs_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET weight_stones_lbs = api_data->>'weight',
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'weight' IS NOT NULL
              AND api_data->>'weight' != ''
              AND weight_stones_lbs IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'weight_stones_lbs',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 7: Backfill race_comment field
CREATE OR REPLACE FUNCTION backfill_race_comment_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET race_comment = api_data->>'comment',
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'comment' IS NOT NULL
              AND api_data->>'comment' != ''
              AND race_comment IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'race_comment',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- FUNCTION 8: Backfill jockey_silk_url field
CREATE OR REPLACE FUNCTION backfill_jockey_silk_url_field(batch_limit INTEGER DEFAULT 5000)
RETURNS JSON AS $$
DECLARE
    rows_updated INTEGER := 0;
    total_updated INTEGER := 0;
    batch_count INTEGER := 0;
BEGIN
    LOOP
        batch_count := batch_count + 1;

        UPDATE ra_runners
        SET jockey_silk_url = api_data->>'silk_url',
            updated_at = NOW()
        WHERE runner_id IN (
            SELECT runner_id FROM ra_runners
            WHERE api_data IS NOT NULL
              AND api_data->>'silk_url' IS NOT NULL
              AND api_data->>'silk_url' != ''
              AND jockey_silk_url IS NULL
            LIMIT batch_limit
        );

        GET DIAGNOSTICS rows_updated = ROW_COUNT;
        total_updated := total_updated + rows_updated;

        EXIT WHEN rows_updated = 0;
    END LOOP;

    RETURN json_build_object(
        'field', 'jockey_silk_url',
        'batches', batch_count,
        'updated', total_updated
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- INSTRUCTIONS:
-- 1. Run this migration in Supabase SQL Editor to create the functions
-- 2. Then use the Python script backfill_runners_rpc.py to call these functions
-- 3. Each function runs entirely server-side and avoids timeout issues
-- ============================================================================
