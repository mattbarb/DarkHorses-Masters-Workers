-- ============================================================================
-- Migration 018 - STAGE 3: Add New Columns
-- ============================================================================
-- Run after Stage 2
-- This adds all 24 missing columns for 100% API coverage
-- ============================================================================

BEGIN;

-- Add columns in batches to avoid timeout

-- Batch 1: Horse metadata (5 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_dob DATE;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_sex_code CHAR(1);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_colour VARCHAR(100);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_region VARCHAR(10);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS breeder VARCHAR(255);

-- Batch 2: Pedigree regions (3 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS sire_region VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS dam_region VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS damsire_region VARCHAR(20);

-- Batch 3: Trainer data (3 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS trainer_location VARCHAR(255);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS trainer_14_days JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS trainer_rtf VARCHAR(50);

-- Batch 4: Equipment/Medical (3 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS headgear_run VARCHAR(50);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS wind_surgery VARCHAR(200);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS wind_surgery_run VARCHAR(50);

-- Batch 5: Last run & comment (2 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS last_run_date DATE;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS comment TEXT;

-- Batch 6: Expert analysis (4 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS spotlight TEXT;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS quotes JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS stable_tour JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS medical JSONB;

-- Batch 7: Historical & Live data (4 columns)
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS past_results_flags TEXT[];
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS prev_trainers JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS prev_owners JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS odds JSONB;

-- Reload schema
NOTIFY pgrst, 'reload schema';

SELECT '✅ Stage 3 Complete: 24 new columns added' as status;

COMMIT;
