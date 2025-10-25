-- ============================================================================
-- Migration 018 REVISED: Standardize Schema and Add Missing Fields
-- ============================================================================
-- This migration replaces the original 018_add_all_missing_runner_fields.sql
-- which would have created 16 duplicate columns.
--
-- This revised version:
-- 1. Renames existing columns for consistency (remove _data suffix)
-- 2. Adds ONLY the 8 truly missing fields from Racecard Pro API
-- 3. Does NOT create duplicate columns
--
-- Date: 2025-10-18
-- Supersedes: 018_add_all_missing_runner_fields.sql (DO NOT RUN THAT FILE!)
-- Related: RA_RUNNERS_SCHEMA_ANALYSIS.md, SCHEMA_CLEANUP_EXECUTIVE_SUMMARY.md
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: RENAME EXISTING COLUMNS FOR CONSISTENCY
-- ============================================================================

-- Remove _data suffix from JSONB columns for cleaner naming
ALTER TABLE ra_runners
  RENAME COLUMN trainer_14_days_data TO trainer_14_days;

ALTER TABLE ra_runners
  RENAME COLUMN quotes_data TO quotes;

ALTER TABLE ra_runners
  RENAME COLUMN stable_tour_data TO stable_tour;

ALTER TABLE ra_runners
  RENAME COLUMN medical_data TO medical;

-- Standardize horse field naming with horse_ prefix
ALTER TABLE ra_runners
  RENAME COLUMN dob TO horse_dob;

ALTER TABLE ra_runners
  RENAME COLUMN colour TO horse_colour;

ALTER TABLE ra_runners
  RENAME COLUMN age TO horse_age;

ALTER TABLE ra_runners
  RENAME COLUMN sex TO horse_sex;

-- ============================================================================
-- SECTION 2: ADD TRULY MISSING FIELDS (8 new columns)
-- ============================================================================

-- Horse metadata (2 new fields)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS horse_sex_code CHAR(1),
  ADD COLUMN IF NOT EXISTS horse_region VARCHAR(10);

-- Equipment/Medical (1 new field)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS headgear_run VARCHAR(50);

-- Last run data (2 new fields)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS last_run_date DATE,
  ADD COLUMN IF NOT EXISTS days_since_last_run INTEGER;

-- Historical data (2 new fields)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS prev_trainers JSONB,
  ADD COLUMN IF NOT EXISTS prev_owners JSONB;

-- Live data (1 new field)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS odds JSONB;

-- ============================================================================
-- SECTION 3: ADD COMMENTS TO NEW COLUMNS
-- ============================================================================

COMMENT ON COLUMN ra_runners.horse_sex_code IS 'Horse sex code (M/F/G/C) - more precise than horse_sex from Racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_region IS 'Horse region/country of origin (GB/IRE/FR/USA) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.headgear_run IS 'Headgear run information (e.g., "First time", "2nd time") from Racecard Pro API';
COMMENT ON COLUMN ra_runners.last_run_date IS 'Date of last run from Racecard Pro API';
COMMENT ON COLUMN ra_runners.days_since_last_run IS 'Calculated: days between race_date and last_run_date';
COMMENT ON COLUMN ra_runners.prev_trainers IS 'Previous trainers array (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.prev_owners IS 'Previous owners array (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.odds IS 'Live odds from multiple bookmakers (JSONB array) from Racecard Pro API';

-- Update comments on renamed columns
COMMENT ON COLUMN ra_runners.trainer_14_days IS 'Trainer 14-day statistics object (JSONB) from Racecard Pro API (renamed from trainer_14_days_data)';
COMMENT ON COLUMN ra_runners.quotes IS 'Press quotes array (JSONB) from Racecard Pro API (renamed from quotes_data)';
COMMENT ON COLUMN ra_runners.stable_tour IS 'Stable tour comments array (JSONB) from Racecard Pro API (renamed from stable_tour_data)';
COMMENT ON COLUMN ra_runners.medical IS 'Medical history array (JSONB) from Racecard Pro API (renamed from medical_data)';
COMMENT ON COLUMN ra_runners.horse_dob IS 'Horse date of birth from Racecard Pro API (renamed from dob for consistency)';
COMMENT ON COLUMN ra_runners.horse_colour IS 'Horse colour (e.g., Bay, Chestnut) from Racecard Pro API (renamed from colour for consistency)';
COMMENT ON COLUMN ra_runners.horse_age IS 'Horse age at race time (renamed from age for consistency)';
COMMENT ON COLUMN ra_runners.horse_sex IS 'Horse sex (M/F/G) - basic version (renamed from sex for consistency)';

-- ============================================================================
-- SECTION 4: CREATE INDEXES FOR NEW FIELDS
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_sex_code ON ra_runners(horse_sex_code);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_region ON ra_runners(horse_region);
CREATE INDEX IF NOT EXISTS idx_ra_runners_last_run_date ON ra_runners(last_run_date);
CREATE INDEX IF NOT EXISTS idx_ra_runners_days_since_last_run ON ra_runners(days_since_last_run);

-- GIN indexes for new JSONB columns
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_trainers_gin ON ra_runners USING GIN (prev_trainers);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_owners_gin ON ra_runners USING GIN (prev_owners);
CREATE INDEX IF NOT EXISTS idx_ra_runners_odds_gin ON ra_runners USING GIN (odds);

-- Update existing GIN indexes to use new column names (drop old, create new)
DROP INDEX IF EXISTS idx_runners_trainer_14_days_gin;
DROP INDEX IF EXISTS idx_runners_quotes_gin;
DROP INDEX IF EXISTS idx_runners_stable_tour_gin;
DROP INDEX IF EXISTS idx_runners_medical_gin;

CREATE INDEX IF NOT EXISTS idx_ra_runners_trainer_14_days_gin ON ra_runners USING GIN (trainer_14_days);
CREATE INDEX IF NOT EXISTS idx_ra_runners_quotes_gin ON ra_runners USING GIN (quotes);
CREATE INDEX IF NOT EXISTS idx_ra_runners_stable_tour_gin ON ra_runners USING GIN (stable_tour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_medical_gin ON ra_runners USING GIN (medical);

-- Update existing indexes for renamed horse fields (drop old, create new)
DROP INDEX IF EXISTS idx_runners_dob;
DROP INDEX IF EXISTS idx_runners_colour;

CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_dob ON ra_runners(horse_dob);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_colour ON ra_runners(horse_colour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_age ON ra_runners(horse_age);

-- ============================================================================
-- SECTION 5: VERIFICATION
-- ============================================================================

-- Verify renamed columns exist
DO $$
DECLARE
    renamed_cols TEXT[] := ARRAY[
        'trainer_14_days', 'quotes', 'stable_tour', 'medical',
        'horse_dob', 'horse_colour', 'horse_age', 'horse_sex'
    ];
    col TEXT;
BEGIN
    FOREACH col IN ARRAY renamed_cols
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'ra_runners' AND column_name = col
        ) THEN
            RAISE EXCEPTION 'Renamed column % is missing!', col;
        END IF;
    END LOOP;
    RAISE NOTICE '✅ All 8 renamed columns verified';
END $$;

-- Verify old column names are gone
DO $$
DECLARE
    old_cols TEXT[] := ARRAY[
        'trainer_14_days_data', 'quotes_data', 'stable_tour_data', 'medical_data',
        'dob', 'colour', 'age', 'sex'
    ];
    col TEXT;
BEGIN
    FOREACH col IN ARRAY old_cols
    LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'ra_runners' AND column_name = col
        ) THEN
            RAISE EXCEPTION 'Old column name % still exists!', col;
        END IF;
    END LOOP;
    RAISE NOTICE '✅ All 8 old column names removed';
END $$;

-- Verify new columns were added
DO $$
DECLARE
    new_cols TEXT[] := ARRAY[
        'horse_sex_code', 'horse_region', 'headgear_run',
        'last_run_date', 'days_since_last_run',
        'prev_trainers', 'prev_owners', 'odds'
    ];
    col TEXT;
BEGIN
    FOREACH col IN ARRAY new_cols
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'ra_runners' AND column_name = col
        ) THEN
            RAISE EXCEPTION 'New column % was not added!', col;
        END IF;
    END LOOP;
    RAISE NOTICE '✅ All 8 new columns added successfully';
END $$;

-- ============================================================================
-- SECTION 6: RELOAD SCHEMA CACHE
-- ============================================================================

NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- SECTION 7: SUMMARY REPORT
-- ============================================================================

SELECT
    '✅ Migration 018 REVISED Complete' as status,
    '8 columns renamed, 8 new columns added' as changes,
    NOW() as completed_at;

-- List renamed columns
SELECT 'Renamed columns (old → new):' AS info;
SELECT
    'trainer_14_days_data → trainer_14_days' AS rename_1
UNION ALL SELECT 'quotes_data → quotes'
UNION ALL SELECT 'stable_tour_data → stable_tour'
UNION ALL SELECT 'medical_data → medical'
UNION ALL SELECT 'dob → horse_dob'
UNION ALL SELECT 'colour → horse_colour'
UNION ALL SELECT 'age → horse_age'
UNION ALL SELECT 'sex → horse_sex';

-- List new columns added
SELECT 'New columns added:' AS info;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN (
      'horse_sex_code', 'horse_region', 'headgear_run',
      'last_run_date', 'days_since_last_run',
      'prev_trainers', 'prev_owners', 'odds'
  )
ORDER BY column_name;

-- Show total column count
SELECT
    'Total columns in ra_runners:' AS info,
    COUNT(*) as column_count
FROM information_schema.columns
WHERE table_name = 'ra_runners';

COMMIT;

-- ============================================================================
-- MIGRATION 018 REVISED COMPLETE
-- ============================================================================

-- Next steps:
-- 1. Update fetchers/races_fetcher.py to use new column names
-- 2. Update fetchers/results_fetcher.py if needed
-- 3. Test with: python3 main.py --entities races --test
-- 4. Run full data capture to populate new fields
--
-- For rollback:
-- BEGIN;
-- -- Rename columns back
-- ALTER TABLE ra_runners
--   RENAME COLUMN trainer_14_days TO trainer_14_days_data,
--   RENAME COLUMN quotes TO quotes_data,
--   RENAME COLUMN stable_tour TO stable_tour_data,
--   RENAME COLUMN medical TO medical_data,
--   RENAME COLUMN horse_dob TO dob,
--   RENAME COLUMN horse_colour TO colour,
--   RENAME COLUMN horse_age TO age,
--   RENAME COLUMN horse_sex TO sex;
-- -- Drop new columns
-- ALTER TABLE ra_runners
--   DROP COLUMN horse_sex_code,
--   DROP COLUMN horse_region,
--   DROP COLUMN headgear_run,
--   DROP COLUMN last_run_date,
--   DROP COLUMN days_since_last_run,
--   DROP COLUMN prev_trainers,
--   DROP COLUMN prev_owners,
--   DROP COLUMN odds;
-- COMMIT;
-- ============================================================================
