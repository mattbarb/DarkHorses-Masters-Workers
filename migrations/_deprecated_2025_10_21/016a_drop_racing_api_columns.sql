-- Migration 016a: Drop Racing API ID Duplicates (Phase 1)
--
-- This migration removes redundant racing_api_* ID columns that duplicate
-- shorter primary *_id columns. These store identical values and can be
-- dropped immediately without data merging.
--
-- Columns to drop (6 total):
-- • fetched_at (duplicate of created_at)
-- • racing_api_race_id (duplicate of race_id)
-- • racing_api_horse_id (duplicate of horse_id)
-- • racing_api_jockey_id (duplicate of jockey_id)
-- • racing_api_trainer_id (duplicate of trainer_id)
-- • racing_api_owner_id (duplicate of owner_id)
--
-- Date: 2025-10-17
-- Phase: 1 of 2 (Phase 2 will drop data field duplicates after backfill)

BEGIN;

-- ============================================================================
-- DROP COLUMNS
-- ============================================================================

-- Drop timestamp duplicate
ALTER TABLE ra_runners DROP COLUMN IF EXISTS fetched_at;

-- Drop racing_api_* ID duplicates
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_race_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_horse_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_jockey_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_trainer_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_owner_id;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
DECLARE
    dropped_cols TEXT[] := ARRAY[
        'fetched_at',
        'racing_api_race_id', 'racing_api_horse_id', 'racing_api_jockey_id',
        'racing_api_trainer_id', 'racing_api_owner_id'
    ];
    primary_cols TEXT[] := ARRAY[
        'created_at',
        'race_id', 'horse_id', 'jockey_id', 'trainer_id', 'owner_id'
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

    RAISE NOTICE '✅ Migration 016a complete: 6 racing_api_* columns dropped successfully';
    RAISE NOTICE 'Phase 2 (data field duplicates) will run after backfill completes';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION ACTIONS
-- ============================================================================

-- 1. Update fetchers/races_fetcher.py to remove these assignments:
--    'fetched_at': datetime.utcnow().isoformat(),
--    'racing_api_race_id': race_id,
--    'racing_api_horse_id': runner.get('horse_id'),
--    'racing_api_jockey_id': runner.get('jockey_id'),
--    'racing_api_trainer_id': runner.get('trainer_id'),
--    'racing_api_owner_id': runner.get('owner_id'),
--
-- 2. Update fetchers/results_fetcher.py (if similar assignments exist)
--
-- 3. Test with: python3 main.py --test --entities races
