-- ============================================================================
-- Migration 018 SAFE: Complete Schema Based on Current State
-- ============================================================================
-- This migration handles the ACTUAL current state of the database
-- Only renames columns that exist and adds columns that are missing
--
-- Date: 2025-10-18
-- Supersedes: All previous versions of Migration 018
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: RENAME EXISTING COLUMNS (only if they exist)
-- ============================================================================

-- Rename age -> horse_age (exists in current schema)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ra_runners' AND column_name = 'age') THEN
        ALTER TABLE ra_runners RENAME COLUMN age TO horse_age;
        RAISE NOTICE 'Renamed age -> horse_age';
    ELSE
        RAISE NOTICE 'Column age does not exist, skipping rename';
    END IF;
END $$;

-- Rename sex -> horse_sex (exists in current schema)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ra_runners' AND column_name = 'sex') THEN
        ALTER TABLE ra_runners RENAME COLUMN sex TO horse_sex;
        RAISE NOTICE 'Renamed sex -> horse_sex';
    ELSE
        RAISE NOTICE 'Column sex does not exist, skipping rename';
    END IF;
END $$;

-- ============================================================================
-- SECTION 2: ADD MISSING COLUMNS
-- ============================================================================

-- Add horse_sex_code (NEW)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS horse_sex_code CHAR(1);

-- Add horse_region (NEW)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS horse_region VARCHAR(10);

-- Add horse_dob (if missing - Migration 003 may not have run)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS horse_dob DATE;

-- Add horse_colour (if missing - Migration 003 may not have run)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS horse_colour VARCHAR(100);

-- Add breeder (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS breeder VARCHAR(255);

-- Add pedigree regions (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS sire_region VARCHAR(20);

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS dam_region VARCHAR(20);

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS damsire_region VARCHAR(20);

-- Add trainer fields (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS trainer_location VARCHAR(255);

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS trainer_14_days JSONB;

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS trainer_rtf VARCHAR(50);

-- Add equipment/medical fields (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS headgear_run VARCHAR(50);

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS wind_surgery VARCHAR(200);

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS wind_surgery_run VARCHAR(50);

-- Add last run fields (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS last_run_date DATE;

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS days_since_last_run INTEGER;

-- Add expert analysis fields (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS spotlight TEXT;

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS quotes JSONB;

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS stable_tour JSONB;

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS medical JSONB;

-- Add historical fields (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS past_results_flags TEXT[];

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS prev_trainers JSONB;

ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS prev_owners JSONB;

-- Add live odds field (if missing)
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS odds JSONB;

-- ============================================================================
-- SECTION 3: ADD COMMENTS
-- ============================================================================

COMMENT ON COLUMN ra_runners.horse_age IS 'Horse age at race time (renamed from age for consistency)';
COMMENT ON COLUMN ra_runners.horse_sex IS 'Horse sex (M/F/G) - basic version (renamed from sex for consistency)';
COMMENT ON COLUMN ra_runners.horse_sex_code IS 'Horse sex code (M/F/G/C) - more precise than horse_sex from Racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_region IS 'Horse region/country of origin (GB/IRE/FR/USA) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_dob IS 'Horse date of birth from Racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_colour IS 'Horse colour (e.g., Bay, Chestnut) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.breeder IS 'Horse breeder name from Racecard Pro API';
COMMENT ON COLUMN ra_runners.sire_region IS 'Sire region from Racecard Pro API';
COMMENT ON COLUMN ra_runners.dam_region IS 'Dam region from Racecard Pro API';
COMMENT ON COLUMN ra_runners.damsire_region IS 'Damsire region from Racecard Pro API';
COMMENT ON COLUMN ra_runners.trainer_location IS 'Trainer location/yard from Racecard Pro API';
COMMENT ON COLUMN ra_runners.trainer_14_days IS 'Trainer 14-day statistics (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.trainer_rtf IS 'Trainer recent-to-form percentage from Racecard Pro API';
COMMENT ON COLUMN ra_runners.headgear_run IS 'Headgear run information (e.g., "First time", "2nd time") from Racecard Pro API';
COMMENT ON COLUMN ra_runners.wind_surgery IS 'Wind surgery information from Racecard Pro API';
COMMENT ON COLUMN ra_runners.wind_surgery_run IS 'Runs since wind surgery from Racecard Pro API';
COMMENT ON COLUMN ra_runners.last_run_date IS 'Date of last run from Racecard Pro API';
COMMENT ON COLUMN ra_runners.days_since_last_run IS 'Calculated: days between race_date and last_run_date';
COMMENT ON COLUMN ra_runners.spotlight IS 'Spotlight expert analysis from Racecard Pro API';
COMMENT ON COLUMN ra_runners.quotes IS 'Press quotes (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.stable_tour IS 'Stable tour comments (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.medical IS 'Medical history (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.past_results_flags IS 'Past results flags from Racecard Pro API';
COMMENT ON COLUMN ra_runners.prev_trainers IS 'Previous trainers (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.prev_owners IS 'Previous owners (JSONB) from Racecard Pro API';
COMMENT ON COLUMN ra_runners.odds IS 'Live odds from multiple bookmakers (JSONB) from Racecard Pro API';

-- ============================================================================
-- SECTION 4: CREATE INDEXES
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_age ON ra_runners(horse_age);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_sex_code ON ra_runners(horse_sex_code);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_region ON ra_runners(horse_region);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_dob ON ra_runners(horse_dob);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_colour ON ra_runners(horse_colour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_last_run_date ON ra_runners(last_run_date);
CREATE INDEX IF NOT EXISTS idx_ra_runners_days_since_last_run ON ra_runners(days_since_last_run);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_ra_runners_trainer_14_days_gin ON ra_runners USING GIN (trainer_14_days);
CREATE INDEX IF NOT EXISTS idx_ra_runners_quotes_gin ON ra_runners USING GIN (quotes);
CREATE INDEX IF NOT EXISTS idx_ra_runners_stable_tour_gin ON ra_runners USING GIN (stable_tour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_medical_gin ON ra_runners USING GIN (medical);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_trainers_gin ON ra_runners USING GIN (prev_trainers);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_owners_gin ON ra_runners USING GIN (prev_owners);
CREATE INDEX IF NOT EXISTS idx_ra_runners_odds_gin ON ra_runners USING GIN (odds);

-- GIN index for array column
CREATE INDEX IF NOT EXISTS idx_ra_runners_past_results_flags_gin ON ra_runners USING GIN (past_results_flags);

-- ============================================================================
-- SECTION 5: RELOAD SCHEMA CACHE
-- ============================================================================

NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- SECTION 6: SUMMARY
-- ============================================================================

SELECT
    '✅ Migration 018 SAFE Complete' as status,
    '2 columns renamed, 24 columns ensured to exist' as changes,
    NOW() as completed_at;

-- List columns that were added or already existed
SELECT 'All required columns now exist:' AS info;
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_runners'
  AND column_name IN (
      'horse_age', 'horse_sex', 'horse_sex_code', 'horse_region',
      'horse_dob', 'horse_colour', 'breeder',
      'sire_region', 'dam_region', 'damsire_region',
      'trainer_location', 'trainer_14_days', 'trainer_rtf',
      'headgear_run', 'wind_surgery', 'wind_surgery_run',
      'last_run_date', 'days_since_last_run',
      'spotlight', 'quotes', 'stable_tour', 'medical',
      'past_results_flags', 'prev_trainers', 'prev_owners', 'odds'
  )
ORDER BY column_name;

COMMIT;

-- ============================================================================
-- MIGRATION 018 SAFE COMPLETE
-- ============================================================================
