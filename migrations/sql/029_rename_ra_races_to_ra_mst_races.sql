-- Migration 029: Rename ra_races to ra_mst_races
-- Date: 2025-10-26
-- Purpose: Align races table with master table naming convention (ra_mst_*)
-- Impact: All references to ra_races must be updated in application code

-- Step 1: Rename the table
ALTER TABLE ra_races RENAME TO ra_mst_races;

-- Step 2: Rename associated constraints and indexes
-- Primary key constraint
ALTER TABLE ra_mst_races RENAME CONSTRAINT ra_races_pkey TO ra_mst_races_pkey;

-- Indexes (if any exist, rename them)
-- Note: Check existing indexes with:
-- SELECT indexname FROM pg_indexes WHERE tablename = 'ra_mst_races';

-- Step 3: Update foreign key references in other tables
-- ra_runners references ra_races(race_id)
ALTER TABLE ra_runners DROP CONSTRAINT IF EXISTS ra_runners_race_id_fkey;
ALTER TABLE ra_runners ADD CONSTRAINT ra_runners_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_mst_races(race_id);

-- ra_race_results might reference ra_races if FK exists
ALTER TABLE ra_race_results DROP CONSTRAINT IF EXISTS ra_race_results_race_id_fkey;
ALTER TABLE ra_race_results ADD CONSTRAINT ra_race_results_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_mst_races(race_id);

-- Step 4: Update metadata tracking references
UPDATE ra_metadata_tracking
SET table_name = 'ra_mst_races'
WHERE table_name = 'ra_races';

-- Verification queries (commented out - run manually to verify)
-- SELECT COUNT(*) FROM ra_mst_races;
-- SELECT table_name FROM ra_metadata_tracking WHERE table_name = 'ra_mst_races';
-- SELECT conname FROM pg_constraint WHERE conrelid = 'ra_mst_races'::regclass;

COMMENT ON TABLE ra_mst_races IS 'Master table: Race metadata from Racing API';
