-- ============================================================================
-- DATABASE MIGRATION: Add Missing Fields
-- ============================================================================
-- Purpose: Add fields identified in database audit as missing but available in API
-- Date: 2025-10-08
-- Related: DATA_UPDATE_MASTER_PLAN.md
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: ADD NEW COLUMNS TO ra_runners
-- ============================================================================

-- Add horse detail fields from API
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS dob DATE,
ADD COLUMN IF NOT EXISTS colour VARCHAR(100),
ADD COLUMN IF NOT EXISTS breeder VARCHAR(255),
ADD COLUMN IF NOT EXISTS dam_region VARCHAR(20),
ADD COLUMN IF NOT EXISTS sire_region VARCHAR(20),
ADD COLUMN IF NOT EXISTS damsire_region VARCHAR(20);

-- Add trainer fields from API
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS trainer_location VARCHAR(255),
ADD COLUMN IF NOT EXISTS trainer_rtf VARCHAR(50),
ADD COLUMN IF NOT EXISTS trainer_14_days_data JSONB;

-- Add premium content fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS spotlight TEXT;

-- Add medical/surgery fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS wind_surgery VARCHAR(200),
ADD COLUMN IF NOT EXISTS wind_surgery_run VARCHAR(50);

-- Add array fields for historical data
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS past_results_flags TEXT[],
ADD COLUMN IF NOT EXISTS quotes_data JSONB,
ADD COLUMN IF NOT EXISTS stable_tour_data JSONB,
ADD COLUMN IF NOT EXISTS medical_data JSONB;

-- Document columns
COMMENT ON COLUMN ra_runners.dob IS 'Horse date of birth (from runner data in API)';
COMMENT ON COLUMN ra_runners.colour IS 'Horse colour (Bay, Chestnut, etc.)';
COMMENT ON COLUMN ra_runners.breeder IS 'Horse breeder name';
COMMENT ON COLUMN ra_runners.dam_region IS 'Dam region code (gb, ire, etc.)';
COMMENT ON COLUMN ra_runners.sire_region IS 'Sire region code (gb, ire, etc.)';
COMMENT ON COLUMN ra_runners.damsire_region IS 'Damsire region code (gb, ire, etc.)';
COMMENT ON COLUMN ra_runners.trainer_location IS 'Trainer location/yard';
COMMENT ON COLUMN ra_runners.trainer_rtf IS 'Trainer recent form (e.g., 14-day stats)';
COMMENT ON COLUMN ra_runners.trainer_14_days_data IS 'Trainer 14-day statistics (JSONB object)';
COMMENT ON COLUMN ra_runners.spotlight IS 'Spotlight/preview comment from experts';
COMMENT ON COLUMN ra_runners.wind_surgery IS 'Wind surgery information';
COMMENT ON COLUMN ra_runners.wind_surgery_run IS 'Wind surgery run indicator';
COMMENT ON COLUMN ra_runners.past_results_flags IS 'Flags like "C&D winner", "AW winner" (array)';
COMMENT ON COLUMN ra_runners.quotes_data IS 'Trainer/jockey quotes (JSONB array)';
COMMENT ON COLUMN ra_runners.stable_tour_data IS 'Stable tour comments (JSONB array)';
COMMENT ON COLUMN ra_runners.medical_data IS 'Medical history (JSONB array)';


-- ============================================================================
-- SECTION 2: ADD NEW COLUMNS TO ra_races
-- ============================================================================

-- Add race classification fields
ALTER TABLE ra_races
ADD COLUMN IF NOT EXISTS pattern VARCHAR(100),
ADD COLUMN IF NOT EXISTS sex_restriction VARCHAR(200),
ADD COLUMN IF NOT EXISTS rating_band VARCHAR(100);

-- Add race detail fields
ALTER TABLE ra_races
ADD COLUMN IF NOT EXISTS jumps VARCHAR(50);

-- Add preview/analysis fields
ALTER TABLE ra_races
ADD COLUMN IF NOT EXISTS tip TEXT,
ADD COLUMN IF NOT EXISTS verdict TEXT,
ADD COLUMN IF NOT EXISTS betting_forecast TEXT;

-- Note: stalls field may already exist as stalls_position
-- Check and add only if doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_races' AND column_name = 'stalls'
    ) THEN
        ALTER TABLE ra_races ADD COLUMN stalls VARCHAR(200);
    END IF;
END $$;

-- Document columns
COMMENT ON COLUMN ra_races.pattern IS 'Race pattern (Group 1, Group 2, Listed, etc.)';
COMMENT ON COLUMN ra_races.sex_restriction IS 'Sex restriction (Fillies only, Colts & Geldings, etc.)';
COMMENT ON COLUMN ra_races.rating_band IS 'Rating band restriction (0-75, 76-90, etc.)';
COMMENT ON COLUMN ra_races.jumps IS 'Number of jumps (for National Hunt races)';
COMMENT ON COLUMN ra_races.tip IS 'Expert tip/selection for the race';
COMMENT ON COLUMN ra_races.verdict IS 'Race verdict/preview/analysis';
COMMENT ON COLUMN ra_races.betting_forecast IS 'Betting forecast for the race';


-- ============================================================================
-- SECTION 3: ADD INDEXES FOR NEW COLUMNS
-- ============================================================================

-- Indexes on ra_runners for common queries
CREATE INDEX IF NOT EXISTS idx_runners_dob ON ra_runners(dob);
CREATE INDEX IF NOT EXISTS idx_runners_colour ON ra_runners(colour);
CREATE INDEX IF NOT EXISTS idx_runners_breeder ON ra_runners(breeder);
CREATE INDEX IF NOT EXISTS idx_runners_trainer_location ON ra_runners(trainer_location);

-- GIN indexes for JSONB columns (for advanced queries)
CREATE INDEX IF NOT EXISTS idx_runners_trainer_14_days_gin ON ra_runners USING GIN (trainer_14_days_data);
CREATE INDEX IF NOT EXISTS idx_runners_quotes_gin ON ra_runners USING GIN (quotes_data);
CREATE INDEX IF NOT EXISTS idx_runners_stable_tour_gin ON ra_runners USING GIN (stable_tour_data);
CREATE INDEX IF NOT EXISTS idx_runners_medical_gin ON ra_runners USING GIN (medical_data);

-- GIN index for array column
CREATE INDEX IF NOT EXISTS idx_runners_past_results_flags_gin ON ra_runners USING GIN (past_results_flags);

-- Indexes on ra_races for filtering
CREATE INDEX IF NOT EXISTS idx_races_pattern ON ra_races(pattern);
CREATE INDEX IF NOT EXISTS idx_races_sex_restriction ON ra_races(sex_restriction);
CREATE INDEX IF NOT EXISTS idx_races_rating_band ON ra_races(rating_band);


-- ============================================================================
-- SECTION 4: VALIDATION
-- ============================================================================

-- Verify columns were added
DO $$
DECLARE
    missing_columns INTEGER;
BEGIN
    -- Check ra_runners columns
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('dob'),
        ('colour'),
        ('breeder'),
        ('trainer_location'),
        ('spotlight'),
        ('wind_surgery'),
        ('past_results_flags'),
        ('trainer_14_days_data')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_runners'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_runners', missing_columns;
    END IF;

    -- Check ra_races columns
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('pattern'),
        ('sex_restriction'),
        ('rating_band'),
        ('tip'),
        ('verdict'),
        ('betting_forecast')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_races'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_races', missing_columns;
    END IF;

    RAISE NOTICE 'All columns added successfully';
END $$;


-- ============================================================================
-- SECTION 5: SUMMARY REPORT
-- ============================================================================

SELECT
    '✓ Migration 003 Complete' AS status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_runners') AS ra_runners_column_count,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_races') AS ra_races_column_count,
    NOW() AS completed_at;

-- List new columns added
SELECT 'New ra_runners columns:' AS info;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN (
      'dob', 'colour', 'breeder', 'dam_region', 'sire_region', 'damsire_region',
      'trainer_location', 'trainer_rtf', 'trainer_14_days_data',
      'spotlight', 'wind_surgery', 'wind_surgery_run',
      'past_results_flags', 'quotes_data', 'stable_tour_data', 'medical_data'
  )
ORDER BY column_name;

SELECT 'New ra_races columns:' AS info;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_races'
  AND column_name IN (
      'pattern', 'sex_restriction', 'rating_band', 'jumps',
      'tip', 'verdict', 'betting_forecast', 'stalls'
  )
ORDER BY column_name;

-- List new indexes created
SELECT 'New indexes:' AS info;
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('ra_runners', 'ra_races')
  AND indexname LIKE 'idx_runners_%' OR indexname LIKE 'idx_races_%'
ORDER BY tablename, indexname;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Next steps:
-- 1. Update fetchers/horses_fetcher.py to add fetch_and_store_detailed() method
-- 2. Update fetchers/races_fetcher.py to extract new fields
-- 3. Run pedigree backfill job
-- 4. Monitor data population

-- For rollback:
-- ALTER TABLE ra_runners DROP COLUMN dob, DROP COLUMN colour, ...
-- (See EXECUTION_CHECKLIST.md for complete rollback procedure)

-- ============================================================================
