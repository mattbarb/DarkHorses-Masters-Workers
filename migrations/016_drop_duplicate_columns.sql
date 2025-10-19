-- Migration 016: Drop Duplicate and Redundant Columns from ra_runners
--
-- This migration removes duplicate columns that store identical data:
--
-- TIMESTAMP DUPLICATES:
-- • fetched_at (duplicate of created_at)
--
-- RACING API ID DUPLICATES:
-- • racing_api_race_id (duplicate of race_id)
-- • racing_api_horse_id (duplicate of horse_id)
-- • racing_api_jockey_id (duplicate of jockey_id)
-- • racing_api_trainer_id (duplicate of trainer_id)
-- • racing_api_owner_id (duplicate of owner_id)
--
-- DATA FIELD DUPLICATES:
-- • weight (duplicate of weight_lbs)
-- • race_comment (duplicate of comment)
-- • jockey_silk_url (duplicate of silk_url)
--
-- Total columns to drop: 9
--
-- ⚠️ IMPORTANT: Run scripts/merge_duplicate_columns.py BEFORE executing this migration
--              to ensure no data is lost.
--
-- Date: 2025-10-17
-- Related: docs/DUPLICATE_COLUMN_CLEANUP_PLAN.md

-- ============================================================================
-- SAFETY CHECKS (Optional - Comment out if you want to run without checks)
-- ============================================================================

-- Verify no data will be lost (this will error if there's data that would be lost)
DO $$
DECLARE
    weight_orphans INTEGER;
    comment_orphans INTEGER;
    silk_orphans INTEGER;
BEGIN
    -- Check for records where duplicate has data but primary is NULL
    SELECT COUNT(*) INTO weight_orphans
    FROM ra_runners
    WHERE weight IS NOT NULL AND weight_lbs IS NULL;

    SELECT COUNT(*) INTO comment_orphans
    FROM ra_runners
    WHERE race_comment IS NOT NULL AND comment IS NULL;

    SELECT COUNT(*) INTO silk_orphans
    FROM ra_runners
    WHERE jockey_silk_url IS NOT NULL AND silk_url IS NULL;

    -- Raise error if any orphans found
    IF weight_orphans > 0 THEN
        RAISE EXCEPTION 'Cannot drop weight: % records would lose data. Run merge script first.', weight_orphans;
    END IF;

    IF comment_orphans > 0 THEN
        RAISE EXCEPTION 'Cannot drop race_comment: % records would lose data. Run merge script first.', comment_orphans;
    END IF;

    IF silk_orphans > 0 THEN
        RAISE EXCEPTION 'Cannot drop jockey_silk_url: % records would lose data. Run merge script first.', silk_orphans;
    END IF;

    RAISE NOTICE 'Safety checks passed. No data will be lost.';
END $$;

-- ============================================================================
-- DROP DUPLICATE COLUMNS
-- ============================================================================

-- Drop timestamp duplicate
ALTER TABLE ra_runners DROP COLUMN IF EXISTS fetched_at;

-- Drop racing_api_* ID duplicates
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_race_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_horse_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_jockey_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_trainer_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_owner_id;

-- Drop data field duplicates
ALTER TABLE ra_runners DROP COLUMN IF EXISTS weight;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_silk_url;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify all duplicate columns are dropped
DO $$
DECLARE
    dropped_cols TEXT[] := ARRAY[
        'fetched_at',
        'racing_api_race_id', 'racing_api_horse_id', 'racing_api_jockey_id',
        'racing_api_trainer_id', 'racing_api_owner_id',
        'weight', 'race_comment', 'jockey_silk_url'
    ];
    primary_cols TEXT[] := ARRAY[
        'created_at',
        'race_id', 'horse_id', 'jockey_id', 'trainer_id', 'owner_id',
        'weight_lbs', 'comment', 'silk_url'
    ];
    col TEXT;
BEGIN
    -- Check that duplicate columns no longer exist
    FOREACH col IN ARRAY dropped_cols
    LOOP
        IF EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'ra_runners' AND column_name = col
        ) THEN
            RAISE EXCEPTION 'Column % still exists!', col;
        END IF;
    END LOOP;

    -- Check that primary columns still exist
    FOREACH col IN ARRAY primary_cols
    LOOP
        IF NOT EXISTS (
            SELECT 1 FROM information_schema.columns
            WHERE table_name = 'ra_runners' AND column_name = col
        ) THEN
            RAISE EXCEPTION 'Primary column % is missing!', col;
        END IF;
    END LOOP;

    RAISE NOTICE '✅ Migration 016 complete: 9 duplicate columns dropped successfully';
END $$;

-- ============================================================================
-- POST-MIGRATION NOTES
-- ============================================================================

-- After running this migration, you MUST update fetchers to remove duplicate field assignments:
--
-- 1. Update fetchers/races_fetcher.py (lines ~276-310):
--    REMOVE these duplicate assignments:
--      'fetched_at': datetime.utcnow().isoformat(),
--      'racing_api_race_id': race_id,
--      'racing_api_horse_id': runner.get('horse_id'),
--      'racing_api_jockey_id': runner.get('jockey_id'),
--      'racing_api_trainer_id': runner.get('trainer_id'),
--      'racing_api_owner_id': runner.get('owner_id'),
--      'weight': runner.get('weight_lbs'),
--      'race_comment': parse_text_field(runner.get('comment')),
--      'jockey_silk_url': parse_text_field(runner.get('silk_url')),
--
--    KEEP these primary assignments:
--      'created_at': datetime.utcnow().isoformat(),
--      'race_id': race_id,
--      'horse_id': runner.get('horse_id'),
--      'jockey_id': runner.get('jockey_id'),
--      'trainer_id': runner.get('trainer_id'),
--      'owner_id': runner.get('owner_id'),
--      'weight_lbs': runner.get('weight_lbs'),
--      'comment': runner.get('comment'),
--      'silk_url': runner.get('silk_url'),
--
-- 2. Update fetchers/results_fetcher.py (if similar duplicates exist)
--
-- 3. Update scripts/backfill_runners_optimized.py field mappings:
--    Change:
--      {'db_field': 'weight', ...}  →  {'db_field': 'weight_lbs', ...}
--      {'db_field': 'race_comment', ...}  →  {'db_field': 'comment', ...}
--      {'db_field': 'jockey_silk_url', ...}  →  {'db_field': 'silk_url', ...}
--
-- 4. Test with a small fetch to verify only primary columns are populated:
--    python3 main.py --test --entities races
