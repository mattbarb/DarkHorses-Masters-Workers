-- Migration 029: Rename Race Tables to Master Convention
-- Date: 2025-10-26
-- Purpose: Align race-related tables with master table naming convention (ra_mst_*)
-- Tables: ra_races → ra_mst_races
--         ra_runners → ra_mst_runners
--         ra_race_results → ra_mst_race_results
-- Impact: All references must be updated in application code

-- ============================================================================
-- PART 1: RENAME ra_races TO ra_mst_races
-- ============================================================================

-- Step 1.1: Rename the table
ALTER TABLE ra_races RENAME TO ra_mst_races;

-- Step 1.2: Rename primary key constraint
ALTER TABLE ra_mst_races RENAME CONSTRAINT ra_races_pkey TO ra_mst_races_pkey;

-- Step 1.3: Rename any indexes (adjust based on your actual indexes)
DO $$
DECLARE
    idx_name text;
BEGIN
    FOR idx_name IN
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'ra_mst_races'
        AND indexname LIKE '%ra_races%'
    LOOP
        EXECUTE format('ALTER INDEX %I RENAME TO %I',
            idx_name,
            replace(idx_name, 'ra_races', 'ra_mst_races')
        );
    END LOOP;
END $$;

COMMENT ON TABLE ra_mst_races IS 'Master table: Race metadata from Racing API';

-- ============================================================================
-- PART 2: RENAME ra_runners TO ra_mst_runners
-- ============================================================================

-- Step 2.1: Rename the table
ALTER TABLE ra_runners RENAME TO ra_mst_runners;

-- Step 2.2: Rename primary key constraint
ALTER TABLE ra_mst_runners RENAME CONSTRAINT ra_runners_pkey TO ra_mst_runners_pkey;

-- Step 2.3: Update foreign key to ra_mst_races (now points to renamed table)
ALTER TABLE ra_mst_runners DROP CONSTRAINT IF EXISTS ra_runners_race_id_fkey;
ALTER TABLE ra_mst_runners ADD CONSTRAINT ra_mst_runners_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_mst_races(id);

-- Step 2.4: Update other foreign keys in ra_mst_runners
ALTER TABLE ra_mst_runners DROP CONSTRAINT IF EXISTS ra_runners_horse_id_fkey;
ALTER TABLE ra_mst_runners ADD CONSTRAINT ra_mst_runners_horse_id_fkey
    FOREIGN KEY (horse_id) REFERENCES ra_mst_horses(id);

ALTER TABLE ra_mst_runners DROP CONSTRAINT IF EXISTS ra_runners_jockey_id_fkey;
ALTER TABLE ra_mst_runners ADD CONSTRAINT ra_mst_runners_jockey_id_fkey
    FOREIGN KEY (jockey_id) REFERENCES ra_mst_jockeys(id);

ALTER TABLE ra_mst_runners DROP CONSTRAINT IF EXISTS ra_runners_trainer_id_fkey;
ALTER TABLE ra_mst_runners ADD CONSTRAINT ra_mst_runners_trainer_id_fkey
    FOREIGN KEY (trainer_id) REFERENCES ra_mst_trainers(id);

ALTER TABLE ra_mst_runners DROP CONSTRAINT IF EXISTS ra_runners_owner_id_fkey;
ALTER TABLE ra_mst_runners ADD CONSTRAINT ra_mst_runners_owner_id_fkey
    FOREIGN KEY (owner_id) REFERENCES ra_mst_owners(id);

-- Step 2.5: Rename any indexes
DO $$
DECLARE
    idx_name text;
BEGIN
    FOR idx_name IN
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'ra_mst_runners'
        AND indexname LIKE '%ra_runners%'
    LOOP
        EXECUTE format('ALTER INDEX %I RENAME TO %I',
            idx_name,
            replace(idx_name, 'ra_runners', 'ra_mst_runners')
        );
    END LOOP;
END $$;

COMMENT ON TABLE ra_mst_runners IS 'Master table: Race entries/runners from Racing API';

-- ============================================================================
-- PART 3: RENAME ra_race_results TO ra_mst_race_results
-- ============================================================================

-- Step 3.1: Rename the table
ALTER TABLE ra_race_results RENAME TO ra_mst_race_results;

-- Step 3.2: Rename primary key constraint
ALTER TABLE ra_mst_race_results RENAME CONSTRAINT ra_race_results_pkey TO ra_mst_race_results_pkey;

-- Step 3.3: Update foreign key to ra_mst_races
ALTER TABLE ra_mst_race_results DROP CONSTRAINT IF EXISTS ra_race_results_race_id_fkey;
ALTER TABLE ra_mst_race_results ADD CONSTRAINT ra_mst_race_results_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_mst_races(id);

-- Step 3.4: Rename any indexes
DO $$
DECLARE
    idx_name text;
BEGIN
    FOR idx_name IN
        SELECT indexname
        FROM pg_indexes
        WHERE tablename = 'ra_mst_race_results'
        AND indexname LIKE '%ra_race_results%'
    LOOP
        EXECUTE format('ALTER INDEX %I RENAME TO %I',
            idx_name,
            replace(idx_name, 'ra_race_results', 'ra_mst_race_results')
        );
    END LOOP;
END $$;

COMMENT ON TABLE ra_mst_race_results IS 'Master table: Historical race results from Racing API';

-- ============================================================================
-- PART 4: UPDATE METADATA TRACKING (OPTIONAL - SKIP IF TABLE DOESN'T EXIST)
-- ============================================================================

-- Note: Only run these if ra_metadata_tracking table exists
-- UPDATE ra_metadata_tracking SET table_name = 'ra_mst_races' WHERE table_name = 'ra_races';
-- UPDATE ra_metadata_tracking SET table_name = 'ra_mst_runners' WHERE table_name = 'ra_runners';
-- UPDATE ra_metadata_tracking SET table_name = 'ra_mst_race_results' WHERE table_name = 'ra_race_results';

-- ============================================================================
-- VERIFICATION QUERIES (Run these after migration to verify)
-- ============================================================================

-- Verify tables exist
-- SELECT COUNT(*) as races FROM ra_mst_races;
-- SELECT COUNT(*) as runners FROM ra_mst_runners;
-- SELECT COUNT(*) as results FROM ra_mst_race_results;

-- Verify metadata tracking
-- SELECT table_name FROM ra_metadata_tracking WHERE table_name LIKE 'ra_mst_%' ORDER BY table_name;

-- Verify foreign keys
-- SELECT conname, conrelid::regclass AS table, confrelid::regclass AS referenced_table
-- FROM pg_constraint
-- WHERE conrelid IN ('ra_mst_races'::regclass, 'ra_mst_runners'::regclass, 'ra_mst_race_results'::regclass)
-- ORDER BY conrelid::regclass, conname;

-- Check for any remaining old table names
-- SELECT table_name FROM information_schema.tables
-- WHERE table_schema = 'public'
-- AND table_name IN ('ra_races', 'ra_runners', 'ra_race_results');
-- -- Should return 0 rows

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================
-- Next step: Update application code to use new table names
-- - ra_races → ra_mst_races
-- - ra_runners → ra_mst_runners
-- - ra_race_results → ra_mst_race_results
