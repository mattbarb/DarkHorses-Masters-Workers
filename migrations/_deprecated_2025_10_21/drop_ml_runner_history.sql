-- Migration: Drop ML Runner History Table
-- Date: 2025-10-15
-- Reason: Moved to API-based approach for ML feature calculation
-- See: _deprecated/ml_runner_history/README.md

-- Drop the ML runner history table if it exists
DROP TABLE IF EXISTS dh_ml_runner_history CASCADE;

-- Drop any related indexes (if they weren't CASCADE deleted)
DROP INDEX IF EXISTS idx_ml_runner_history_race_id;
DROP INDEX IF EXISTS idx_ml_runner_history_horse_id;
DROP INDEX IF EXISTS idx_ml_runner_history_race_date;
DROP INDEX IF EXISTS idx_ml_runner_history_course_id;
DROP INDEX IF EXISTS idx_ml_runner_history_jockey_id;
DROP INDEX IF EXISTS idx_ml_runner_history_trainer_id;

-- Drop any related views (if they exist)
DROP VIEW IF EXISTS v_ml_runner_history_latest;
DROP VIEW IF EXISTS v_ml_runner_history_upcoming;

-- Verify cleanup
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name = 'dh_ml_runner_history'
    ) THEN
        RAISE EXCEPTION 'Table dh_ml_runner_history still exists after drop attempt';
    ELSE
        RAISE NOTICE 'Table dh_ml_runner_history successfully dropped';
    END IF;
END $$;
