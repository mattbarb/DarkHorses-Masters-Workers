-- ============================================================================
-- DARKHORSES DATABASE FIX SCRIPT
-- ============================================================================
-- Purpose: Apply critical fixes identified in database audit
-- Date: 2025-10-07
-- Execute in order - each section depends on previous ones
-- ============================================================================

-- ============================================================================
-- SECTION 1: ADD MISSING COLUMNS
-- ============================================================================

-- Add missing entry_id column to ra_runners
-- User reported: "entry_id in ra_runners is totally missing"
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS entry_id TEXT;

-- Populate entry_id with runner_id as default
-- Adjust this logic if entry_id should be something different
UPDATE ra_runners
SET entry_id = runner_id
WHERE entry_id IS NULL;

-- Add index for entry_id
CREATE INDEX IF NOT EXISTS idx_runners_entry_id ON ra_runners(entry_id);

-- Document the column
COMMENT ON COLUMN ra_runners.entry_id IS
'Entry ID for the runner (unique identifier per race entry)';


-- ============================================================================
-- SECTION 2: REMOVE ALWAYS-NULL COLUMNS
-- ============================================================================

-- Remove latitude/longitude from ra_courses (not provided by API)
ALTER TABLE ra_courses DROP COLUMN IF EXISTS latitude;
ALTER TABLE ra_courses DROP COLUMN IF EXISTS longitude;


-- ============================================================================
-- SECTION 3: REMOVE DUPLICATE COLUMNS
-- ============================================================================

-- Remove duplicate columns from ra_runners
-- Keep the more descriptive name in each case

-- Keep weight_lbs, remove weight
ALTER TABLE ra_runners DROP COLUMN IF EXISTS weight;

-- Keep racing_post_rating, remove rpr
ALTER TABLE ra_runners DROP COLUMN IF EXISTS rpr;

-- Keep draw, remove stall (they're the same thing)
ALTER TABLE ra_runners DROP COLUMN IF EXISTS stall;

-- Optional: Remove racing_api_* duplicates if you prefer
-- (Keeping them for now as they may be useful for audit trail)
-- ALTER TABLE ra_races DROP COLUMN IF EXISTS racing_api_race_id;
-- ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_race_id;
-- ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_horse_id;
-- ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_jockey_id;
-- ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_trainer_id;
-- ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_owner_id;


-- ============================================================================
-- SECTION 4: ADD NOT NULL CONSTRAINTS
-- ============================================================================

-- IMPORTANT: Only run this section AFTER verifying no NULLs exist
-- Check first:
--   SELECT COUNT(*) FROM ra_races WHERE race_name IS NULL;
--   SELECT COUNT(*) FROM ra_races WHERE race_date IS NULL;
--   SELECT COUNT(*) FROM ra_runners WHERE race_id IS NULL;
--   SELECT COUNT(*) FROM ra_runners WHERE horse_id IS NULL;
--   SELECT COUNT(*) FROM ra_horses WHERE name IS NULL;

-- If all counts are 0, proceed:

-- Critical fields in ra_races
ALTER TABLE ra_races ALTER COLUMN race_name SET NOT NULL;
ALTER TABLE ra_races ALTER COLUMN race_date SET NOT NULL;
ALTER TABLE ra_races ALTER COLUMN race_id SET NOT NULL;

-- Critical fields in ra_runners
ALTER TABLE ra_runners ALTER COLUMN runner_id SET NOT NULL;
ALTER TABLE ra_runners ALTER COLUMN race_id SET NOT NULL;
ALTER TABLE ra_runners ALTER COLUMN horse_id SET NOT NULL;

-- Critical fields in ra_horses
ALTER TABLE ra_horses ALTER COLUMN horse_id SET NOT NULL;
ALTER TABLE ra_horses ALTER COLUMN name SET NOT NULL;

-- Critical fields in other entity tables
ALTER TABLE ra_jockeys ALTER COLUMN jockey_id SET NOT NULL;
ALTER TABLE ra_jockeys ALTER COLUMN name SET NOT NULL;

ALTER TABLE ra_trainers ALTER COLUMN trainer_id SET NOT NULL;
ALTER TABLE ra_trainers ALTER COLUMN name SET NOT NULL;

ALTER TABLE ra_owners ALTER COLUMN owner_id SET NOT NULL;
ALTER TABLE ra_owners ALTER COLUMN name SET NOT NULL;

ALTER TABLE ra_courses ALTER COLUMN course_id SET NOT NULL;
ALTER TABLE ra_courses ALTER COLUMN name SET NOT NULL;


-- ============================================================================
-- SECTION 5: ADD FOREIGN KEY CONSTRAINTS
-- ============================================================================

-- IMPORTANT: These will fail if referential integrity is violated
-- Check for orphaned records first:
--   SELECT COUNT(*) FROM ra_races r
--   LEFT JOIN ra_courses c ON c.course_id = r.course_id
--   WHERE c.course_id IS NULL AND r.course_id IS NOT NULL;

-- Add FK from ra_races to ra_courses
ALTER TABLE ra_races
DROP CONSTRAINT IF EXISTS fk_races_course;

ALTER TABLE ra_races
ADD CONSTRAINT fk_races_course
FOREIGN KEY (course_id) REFERENCES ra_courses(course_id)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- Add FK from ra_runners to ra_races
ALTER TABLE ra_runners
DROP CONSTRAINT IF EXISTS fk_runners_race;

ALTER TABLE ra_runners
ADD CONSTRAINT fk_runners_race
FOREIGN KEY (race_id) REFERENCES ra_races(race_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- Add FK from ra_runners to ra_horses
ALTER TABLE ra_runners
DROP CONSTRAINT IF EXISTS fk_runners_horse;

ALTER TABLE ra_runners
ADD CONSTRAINT fk_runners_horse
FOREIGN KEY (horse_id) REFERENCES ra_horses(horse_id)
ON DELETE RESTRICT
ON UPDATE CASCADE;

-- Add FK from ra_runners to ra_jockeys (nullable)
ALTER TABLE ra_runners
DROP CONSTRAINT IF EXISTS fk_runners_jockey;

ALTER TABLE ra_runners
ADD CONSTRAINT fk_runners_jockey
FOREIGN KEY (jockey_id) REFERENCES ra_jockeys(jockey_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Add FK from ra_runners to ra_trainers (nullable)
ALTER TABLE ra_runners
DROP CONSTRAINT IF EXISTS fk_runners_trainer;

ALTER TABLE ra_runners
ADD CONSTRAINT fk_runners_trainer
FOREIGN KEY (trainer_id) REFERENCES ra_trainers(trainer_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Add FK from ra_runners to ra_owners (nullable)
ALTER TABLE ra_runners
DROP CONSTRAINT IF EXISTS fk_runners_owner;

ALTER TABLE ra_runners
ADD CONSTRAINT fk_runners_owner
FOREIGN KEY (owner_id) REFERENCES ra_owners(owner_id)
ON DELETE SET NULL
ON UPDATE CASCADE;

-- Add FK from ra_horse_pedigree to ra_horses
ALTER TABLE ra_horse_pedigree
DROP CONSTRAINT IF EXISTS fk_pedigree_horse;

ALTER TABLE ra_horse_pedigree
ADD CONSTRAINT fk_pedigree_horse
FOREIGN KEY (horse_id) REFERENCES ra_horses(horse_id)
ON DELETE CASCADE
ON UPDATE CASCADE;

-- Add FK from ra_results to ra_races (if race_id exists in ra_results)
ALTER TABLE ra_results
DROP CONSTRAINT IF EXISTS fk_results_race;

ALTER TABLE ra_results
ADD CONSTRAINT fk_results_race
FOREIGN KEY (race_id) REFERENCES ra_races(race_id)
ON DELETE CASCADE
ON UPDATE CASCADE;


-- ============================================================================
-- SECTION 6: ADD PERFORMANCE INDEXES
-- ============================================================================

-- Indexes for ra_races (most queried table)
CREATE INDEX IF NOT EXISTS idx_races_race_date ON ra_races(race_date DESC);
CREATE INDEX IF NOT EXISTS idx_races_course_date ON ra_races(course_id, race_date DESC);
CREATE INDEX IF NOT EXISTS idx_races_region_date ON ra_races(region, race_date DESC);
CREATE INDEX IF NOT EXISTS idx_races_region ON ra_races(region);
CREATE INDEX IF NOT EXISTS idx_races_race_type ON ra_races(race_type);
CREATE INDEX IF NOT EXISTS idx_races_race_class ON ra_races(race_class);

-- Indexes for ra_runners (large table, many joins)
CREATE INDEX IF NOT EXISTS idx_runners_race_id ON ra_runners(race_id);
CREATE INDEX IF NOT EXISTS idx_runners_horse_id ON ra_runners(horse_id);
CREATE INDEX IF NOT EXISTS idx_runners_jockey_id ON ra_runners(jockey_id);
CREATE INDEX IF NOT EXISTS idx_runners_trainer_id ON ra_runners(trainer_id);
CREATE INDEX IF NOT EXISTS idx_runners_owner_id ON ra_runners(owner_id);
CREATE INDEX IF NOT EXISTS idx_runners_horse_race ON ra_runners(horse_id, race_id);

-- Indexes for ra_horses
CREATE INDEX IF NOT EXISTS idx_horses_region ON ra_horses(region);
CREATE INDEX IF NOT EXISTS idx_horses_name ON ra_horses(name);
CREATE INDEX IF NOT EXISTS idx_horses_sex ON ra_horses(sex);

-- Indexes for ra_jockeys
CREATE INDEX IF NOT EXISTS idx_jockeys_name ON ra_jockeys(name);

-- Indexes for ra_trainers
CREATE INDEX IF NOT EXISTS idx_trainers_name ON ra_trainers(name);

-- Indexes for ra_owners
CREATE INDEX IF NOT EXISTS idx_owners_name ON ra_owners(name);

-- Indexes for ra_courses
CREATE INDEX IF NOT EXISTS idx_courses_region ON ra_courses(region);
CREATE INDEX IF NOT EXISTS idx_courses_name ON ra_courses(name);

-- JSONB indexes for api_data columns (GIN indexes)
CREATE INDEX IF NOT EXISTS idx_races_api_data_gin ON ra_races USING GIN (api_data);
CREATE INDEX IF NOT EXISTS idx_runners_api_data_gin ON ra_runners USING GIN (api_data);
CREATE INDEX IF NOT EXISTS idx_results_api_data_gin ON ra_results USING GIN (api_data);

-- Indexes for ra_collection_metadata (already exist from migration, but adding for completeness)
CREATE INDEX IF NOT EXISTS idx_metadata_table_name ON ra_collection_metadata(table_name);
CREATE INDEX IF NOT EXISTS idx_metadata_created_at ON ra_collection_metadata(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_metadata_status ON ra_collection_metadata(status);
CREATE INDEX IF NOT EXISTS idx_metadata_operation ON ra_collection_metadata(operation);
CREATE INDEX IF NOT EXISTS idx_metadata_table_created ON ra_collection_metadata(table_name, created_at DESC);


-- ============================================================================
-- SECTION 7: ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

-- Table comments
COMMENT ON TABLE ra_races IS 'Race metadata including course, date, type, conditions, and prize money';
COMMENT ON TABLE ra_runners IS 'Individual race entries linking horses, jockeys, trainers with race details';
COMMENT ON TABLE ra_horses IS 'Horse profiles with basic identification and pedigree references';
COMMENT ON TABLE ra_horse_pedigree IS 'Horse pedigree information (sire, dam, damsire)';
COMMENT ON TABLE ra_jockeys IS 'Jockey profiles';
COMMENT ON TABLE ra_trainers IS 'Trainer profiles';
COMMENT ON TABLE ra_owners IS 'Owner profiles';
COMMENT ON TABLE ra_courses IS 'Racing course/track information';
COMMENT ON TABLE ra_results IS 'Race results (purpose TBD - may overlap with ra_races)';
COMMENT ON TABLE ra_bookmakers IS 'Bookmaker reference data';

-- Key column comments for ra_races
COMMENT ON COLUMN ra_races.race_id IS 'Unique identifier for race (from Racing API)';
COMMENT ON COLUMN ra_races.race_date IS 'Date the race is scheduled (NOT NULL)';
COMMENT ON COLUMN ra_races.off_datetime IS 'Scheduled start date/time of race';
COMMENT ON COLUMN ra_races.race_type IS 'Type of race (flat, hurdle, chase, etc.)';
COMMENT ON COLUMN ra_races.race_class IS 'Class of race (1-7, Listed, Group 1-3)';
COMMENT ON COLUMN ra_races.distance_meters IS 'Race distance in meters (calculated)';
COMMENT ON COLUMN ra_races.going IS 'Track going description (good, soft, heavy, etc.)';
COMMENT ON COLUMN ra_races.api_data IS 'Full API response stored as JSONB for reference';

-- Key column comments for ra_runners
COMMENT ON COLUMN ra_runners.runner_id IS 'Unique identifier for runner (format: race_id_horse_id)';
COMMENT ON COLUMN ra_runners.race_id IS 'Foreign key to ra_races';
COMMENT ON COLUMN ra_runners.horse_id IS 'Foreign key to ra_horses';
COMMENT ON COLUMN ra_runners.weight_lbs IS 'Weight carried by horse in pounds';
COMMENT ON COLUMN ra_runners.official_rating IS 'Official handicap rating';
COMMENT ON COLUMN ra_runners.racing_post_rating IS 'Racing Post Rating (RPR)';
COMMENT ON COLUMN ra_runners.api_data IS 'Full API runner data stored as JSONB';


-- ============================================================================
-- SECTION 8: VALIDATION QUERIES
-- ============================================================================

-- Run these queries to verify the fixes were applied successfully

-- Check entry_id was added and populated
SELECT
    'entry_id column check' AS test,
    COUNT(*) AS total_rows,
    COUNT(entry_id) AS populated_rows,
    COUNT(*) - COUNT(entry_id) AS null_rows
FROM ra_runners;

-- Check duplicate columns were removed
SELECT
    'Duplicate columns removed' AS test,
    COUNT(*) FILTER (WHERE column_name IN ('weight', 'rpr', 'stall', 'latitude', 'longitude')) AS should_be_zero
FROM information_schema.columns
WHERE table_name IN ('ra_runners', 'ra_courses');

-- Check foreign keys were added
SELECT
    'Foreign key constraints' AS test,
    COUNT(*) AS fk_count
FROM information_schema.table_constraints
WHERE constraint_type = 'FOREIGN KEY'
AND table_schema = 'public'
AND table_name LIKE 'ra_%';

-- Check indexes were created
SELECT
    'Performance indexes' AS test,
    COUNT(*) AS index_count
FROM pg_indexes
WHERE schemaname = 'public'
AND tablename LIKE 'ra_%';

-- Check NOT NULL constraints
SELECT
    'NOT NULL constraints' AS test,
    COUNT(*) AS not_null_count
FROM information_schema.columns
WHERE table_schema = 'public'
AND table_name IN ('ra_races', 'ra_runners', 'ra_horses')
AND is_nullable = 'NO'
AND column_name IN ('race_id', 'race_name', 'race_date', 'runner_id', 'horse_id', 'name');


-- ============================================================================
-- SECTION 9: DATA QUALITY CHECKS
-- ============================================================================

-- Check for NULL values in critical fields
SELECT
    'ra_races NULL check' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE race_name IS NULL) AS null_race_name,
    COUNT(*) FILTER (WHERE race_date IS NULL) AS null_race_date,
    COUNT(*) FILTER (WHERE course_id IS NULL) AS null_course_id
FROM ra_races;

SELECT
    'ra_runners NULL check' AS table_name,
    COUNT(*) AS total_rows,
    COUNT(*) FILTER (WHERE race_id IS NULL) AS null_race_id,
    COUNT(*) FILTER (WHERE horse_id IS NULL) AS null_horse_id,
    COUNT(*) FILTER (WHERE entry_id IS NULL) AS null_entry_id
FROM ra_runners;

-- Check for orphaned records (after FK constraints)
SELECT
    'Orphaned records check' AS test,
    COUNT(*) AS should_be_zero
FROM ra_runners r
LEFT JOIN ra_races rc ON rc.race_id = r.race_id
WHERE rc.race_id IS NULL;

-- Check date range coverage
SELECT
    'Date range coverage' AS test,
    MIN(race_date) AS earliest_race,
    MAX(race_date) AS latest_race,
    COUNT(DISTINCT race_date) AS unique_dates,
    COUNT(*) AS total_races
FROM ra_races;


-- ============================================================================
-- COMPLETION MESSAGE
-- ============================================================================

-- If you've reached this point without errors, fixes are complete!
SELECT
    '✓ Database fixes applied successfully!' AS status,
    NOW() AS completed_at;


-- ============================================================================
-- NOTES & RECOMMENDATIONS
-- ============================================================================

/*
1. PEDIGREE DATA DUPLICATION:
   - Pedigree fields exist in BOTH ra_runners AND ra_horse_pedigree
   - Decide which location is source of truth
   - Consider removing pedigree columns from ra_runners:
     ALTER TABLE ra_runners DROP COLUMN sire_id;
     ALTER TABLE ra_runners DROP COLUMN sire_name;
     ALTER TABLE ra_runners DROP COLUMN dam_id;
     ALTER TABLE ra_runners DROP COLUMN dam_name;
     ALTER TABLE ra_runners DROP COLUMN damsire_id;
     ALTER TABLE ra_runners DROP COLUMN damsire_name;

2. RA_RESULTS TABLE PURPOSE:
   - Overlaps significantly with ra_races
   - Consider merging into ra_races OR
   - Create separate ra_runner_results for finishing positions

3. ENTITY TABLES (jockeys, trainers, owners):
   - Currently very minimal (just ID and name)
   - Consider adding: region, statistics, metadata

4. MONITOR DATA QUALITY:
   - Use ra_collection_metadata table to track updates
   - Regularly check for NULL percentages in critical columns
   - Monitor foreign key constraint violations

5. BACKUP BEFORE RUNNING:
   - Always backup database before applying schema changes
   - Test in development environment first
   - Run in transaction if possible (BEGIN; ... COMMIT; or ROLLBACK;)

6. INCREMENTAL EXECUTION:
   - You can run sections individually
   - Comment out sections you don't want to run yet
   - Validate after each section before proceeding
*/

-- ============================================================================
-- END OF FIX SCRIPT
-- ============================================================================
