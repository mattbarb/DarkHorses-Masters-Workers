-- ============================================================================
-- Migration 018: Add ALL Missing Runner Fields from Racecard Pro API
-- ============================================================================
-- Adds 23 new columns to ra_runners table to capture complete data from
-- /v1/racecards/{race_id}/pro endpoint
--
-- This migration adds:
-- - Horse metadata (dob, colour, sex_code, region)
-- - Pedigree regions (sire_region, dam_region, damsire_region)
-- - Trainer data (location, 14-day stats, RTF)
-- - Equipment/Medical (headgear_run, wind_surgery, wind_surgery_run)
-- - Expert analysis (spotlight, quotes, stable_tour, medical)
-- - Historical (prev_trainers, prev_owners, past_results_flags)
-- - Live data (last_run, odds)
-- - Breeding (breeder)
-- ============================================================================

-- Add Horse Metadata Fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS horse_dob DATE,
ADD COLUMN IF NOT EXISTS horse_sex_code CHAR(1),
ADD COLUMN IF NOT EXISTS horse_colour VARCHAR(50),
ADD COLUMN IF NOT EXISTS horse_region VARCHAR(10),
ADD COLUMN IF NOT EXISTS breeder VARCHAR(255);

-- Add Pedigree Region Fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS sire_region VARCHAR(10),
ADD COLUMN IF NOT EXISTS dam_region VARCHAR(10),
ADD COLUMN IF NOT EXISTS damsire_region VARCHAR(10);

-- Add Trainer Fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS trainer_location VARCHAR(255),
ADD COLUMN IF NOT EXISTS trainer_14_days JSONB,
ADD COLUMN IF NOT EXISTS trainer_rtf VARCHAR(20);

-- Add Equipment/Medical Fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS headgear_run VARCHAR(50),
ADD COLUMN IF NOT EXISTS wind_surgery VARCHAR(50),
ADD COLUMN IF NOT EXISTS wind_surgery_run VARCHAR(50);

-- Add Last Run Field
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS last_run_date DATE,
ADD COLUMN IF NOT EXISTS days_since_last_run INTEGER;

-- Add Expert Analysis Fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS spotlight TEXT,
ADD COLUMN IF NOT EXISTS quotes JSONB,
ADD COLUMN IF NOT EXISTS stable_tour JSONB,
ADD COLUMN IF NOT EXISTS medical JSONB;

-- Add Historical Fields
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS prev_trainers JSONB,
ADD COLUMN IF NOT EXISTS prev_owners JSONB,
ADD COLUMN IF NOT EXISTS past_results_flags JSONB;

-- Add Live Odds Field
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS odds JSONB;

-- Add comments to new columns
COMMENT ON COLUMN ra_runners.horse_dob IS 'Horse date of birth from racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_sex_code IS 'Horse sex code (M/F/G/C) from racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_colour IS 'Horse colour (e.g., Bay, Chestnut) from racecard Pro API';
COMMENT ON COLUMN ra_runners.horse_region IS 'Horse region/country of origin (GB/IRE/FR/USA) from racecard Pro API';
COMMENT ON COLUMN ra_runners.breeder IS 'Horse breeder name from racecard Pro API';
COMMENT ON COLUMN ra_runners.sire_region IS 'Sire region from racecard Pro API';
COMMENT ON COLUMN ra_runners.dam_region IS 'Dam region from racecard Pro API';
COMMENT ON COLUMN ra_runners.damsire_region IS 'Damsire region from racecard Pro API';
COMMENT ON COLUMN ra_runners.trainer_location IS 'Trainer location/yard from racecard Pro API';
COMMENT ON COLUMN ra_runners.trainer_14_days IS 'Trainer 14-day statistics object from racecard Pro API';
COMMENT ON COLUMN ra_runners.trainer_rtf IS 'Trainer recent-to-form percentage from racecard Pro API';
COMMENT ON COLUMN ra_runners.headgear_run IS 'Headgear run information (e.g., "First time") from racecard Pro API';
COMMENT ON COLUMN ra_runners.wind_surgery IS 'Wind surgery information from racecard Pro API';
COMMENT ON COLUMN ra_runners.wind_surgery_run IS 'Runs since wind surgery from racecard Pro API';
COMMENT ON COLUMN ra_runners.last_run_date IS 'Date of last run from racecard Pro API';
COMMENT ON COLUMN ra_runners.days_since_last_run IS 'Calculated: days between race_date and last_run_date';
COMMENT ON COLUMN ra_runners.spotlight IS 'Spotlight expert analysis from racecard Pro API';
COMMENT ON COLUMN ra_runners.quotes IS 'Press quotes array from racecard Pro API';
COMMENT ON COLUMN ra_runners.stable_tour IS 'Stable tour comments array from racecard Pro API';
COMMENT ON COLUMN ra_runners.medical IS 'Medical history array from racecard Pro API';
COMMENT ON COLUMN ra_runners.prev_trainers IS 'Previous trainers array from racecard Pro API';
COMMENT ON COLUMN ra_runners.prev_owners IS 'Previous owners array from racecard Pro API';
COMMENT ON COLUMN ra_runners.past_results_flags IS 'Past results flags array from racecard Pro API';
COMMENT ON COLUMN ra_runners.odds IS 'Live odds from multiple bookmakers from racecard Pro API';

-- Create indexes for commonly queried fields
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_dob ON ra_runners(horse_dob);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_region ON ra_runners(horse_region);
CREATE INDEX IF NOT EXISTS idx_ra_runners_last_run_date ON ra_runners(last_run_date);
CREATE INDEX IF NOT EXISTS idx_ra_runners_days_since_last_run ON ra_runners(days_since_last_run);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- After running this migration, verify with:
--
-- 1. Check all columns were added:
-- SELECT column_name, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'ra_runners'
-- AND column_name IN (
--     'horse_dob', 'horse_sex_code', 'horse_colour', 'horse_region',
--     'breeder', 'sire_region', 'dam_region', 'damsire_region',
--     'trainer_location', 'trainer_14_days', 'trainer_rtf',
--     'headgear_run', 'wind_surgery', 'wind_surgery_run',
--     'last_run_date', 'days_since_last_run',
--     'spotlight', 'quotes', 'stable_tour', 'medical',
--     'prev_trainers', 'prev_owners', 'past_results_flags', 'odds'
-- )
-- ORDER BY column_name;
--
-- Expected: 24 rows returned
--
-- 2. Check indexes were created:
-- SELECT indexname, indexdef
-- FROM pg_indexes
-- WHERE tablename = 'ra_runners'
-- AND indexname LIKE 'idx_ra_runners_%'
-- ORDER BY indexname;
-- ============================================================================

-- Reload schema cache
NOTIFY pgrst, 'reload schema';

-- Show summary
SELECT
    'Migration 018 Complete' as status,
    COUNT(*) as new_columns_added
FROM information_schema.columns
WHERE table_name = 'ra_runners'
AND column_name IN (
    'horse_dob', 'horse_sex_code', 'horse_colour', 'horse_region',
    'breeder', 'sire_region', 'dam_region', 'damsire_region',
    'trainer_location', 'trainer_14_days', 'trainer_rtf',
    'headgear_run', 'wind_surgery', 'wind_surgery_run',
    'last_run_date', 'days_since_last_run',
    'spotlight', 'quotes', 'stable_tour', 'medical',
    'prev_trainers', 'prev_owners', 'past_results_flags', 'odds'
);
