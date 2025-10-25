-- ============================================================================
-- DATABASE MIGRATION 007: Entity Table Enhancements
-- ============================================================================
-- Purpose: Add calculated statistics fields to entity tables
-- Date: 2025-10-14
-- Related: DATABASE_SCHEMA_AUDIT_DETAILED.md
-- ============================================================================
--
-- WHAT THIS MIGRATION DOES:
-- 1. Adds career statistics fields to ra_jockeys
-- 2. Adds career statistics fields to ra_trainers
-- 3. Adds career statistics fields to ra_owners
-- 4. Creates indexes for performance
-- 5. Adds helper functions for statistics calculation
--
-- IMPORTANT NOTES:
-- - Statistics fields will be NULL initially
-- - Use statistics calculation script to populate
-- - Fields should be updated daily/weekly
-- - win_rate is percentage (0-100), stored as DECIMAL(5,2)
--
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: ADD STATISTICS FIELDS TO ra_jockeys
-- ============================================================================

-- Add career statistics fields
ALTER TABLE ra_jockeys
ADD COLUMN IF NOT EXISTS total_rides INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_wins INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_places INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_seconds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_thirds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS place_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS stats_updated_at TIMESTAMP DEFAULT NULL;

-- Add comments
COMMENT ON COLUMN ra_jockeys.total_rides IS 'Total number of rides (calculated from ra_runners)';
COMMENT ON COLUMN ra_jockeys.total_wins IS 'Total number of wins (position = 1)';
COMMENT ON COLUMN ra_jockeys.total_places IS 'Total number of places (position <= 3)';
COMMENT ON COLUMN ra_jockeys.total_seconds IS 'Total number of 2nd place finishes';
COMMENT ON COLUMN ra_jockeys.total_thirds IS 'Total number of 3rd place finishes';
COMMENT ON COLUMN ra_jockeys.win_rate IS 'Win percentage (0-100), calculated as (wins/rides)*100';
COMMENT ON COLUMN ra_jockeys.place_rate IS 'Place percentage (0-100), calculated as (places/rides)*100';
COMMENT ON COLUMN ra_jockeys.stats_updated_at IS 'When statistics were last calculated';

-- Create indexes for jockey statistics queries
CREATE INDEX IF NOT EXISTS idx_jockeys_win_rate ON ra_jockeys(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jockeys_total_rides ON ra_jockeys(total_rides) WHERE total_rides IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jockeys_stats_updated ON ra_jockeys(stats_updated_at);

-- ============================================================================
-- SECTION 2: ADD STATISTICS FIELDS TO ra_trainers
-- ============================================================================

-- Add career statistics fields
ALTER TABLE ra_trainers
ADD COLUMN IF NOT EXISTS total_runners INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_wins INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_places INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_seconds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_thirds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS place_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS recent_14d_runs INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS recent_14d_wins INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS recent_14d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS stats_updated_at TIMESTAMP DEFAULT NULL;

-- Add comments
COMMENT ON COLUMN ra_trainers.total_runners IS 'Total number of runners (calculated from ra_runners)';
COMMENT ON COLUMN ra_trainers.total_wins IS 'Total number of wins (position = 1)';
COMMENT ON COLUMN ra_trainers.total_places IS 'Total number of places (position <= 3)';
COMMENT ON COLUMN ra_trainers.total_seconds IS 'Total number of 2nd place finishes';
COMMENT ON COLUMN ra_trainers.total_thirds IS 'Total number of 3rd place finishes';
COMMENT ON COLUMN ra_trainers.win_rate IS 'Win percentage (0-100), calculated as (wins/runners)*100';
COMMENT ON COLUMN ra_trainers.place_rate IS 'Place percentage (0-100), calculated as (places/runners)*100';
COMMENT ON COLUMN ra_trainers.recent_14d_runs IS 'Number of runners in last 14 days';
COMMENT ON COLUMN ra_trainers.recent_14d_wins IS 'Number of wins in last 14 days';
COMMENT ON COLUMN ra_trainers.recent_14d_win_rate IS 'Win percentage in last 14 days';
COMMENT ON COLUMN ra_trainers.stats_updated_at IS 'When statistics were last calculated';

-- Create indexes for trainer statistics queries
CREATE INDEX IF NOT EXISTS idx_trainers_win_rate ON ra_trainers(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trainers_total_runners ON ra_trainers(total_runners) WHERE total_runners IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trainers_recent_win_rate ON ra_trainers(recent_14d_win_rate) WHERE recent_14d_win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trainers_stats_updated ON ra_trainers(stats_updated_at);

-- ============================================================================
-- SECTION 3: ADD STATISTICS FIELDS TO ra_owners
-- ============================================================================

-- Add career statistics fields
ALTER TABLE ra_owners
ADD COLUMN IF NOT EXISTS total_horses INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_runners INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_wins INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_places INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_seconds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_thirds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS place_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS active_last_30d BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS stats_updated_at TIMESTAMP DEFAULT NULL;

-- Add comments
COMMENT ON COLUMN ra_owners.total_horses IS 'Total number of unique horses owned (calculated from ra_runners)';
COMMENT ON COLUMN ra_owners.total_runners IS 'Total number of runners (calculated from ra_runners)';
COMMENT ON COLUMN ra_owners.total_wins IS 'Total number of wins (position = 1)';
COMMENT ON COLUMN ra_owners.total_places IS 'Total number of places (position <= 3)';
COMMENT ON COLUMN ra_owners.total_seconds IS 'Total number of 2nd place finishes';
COMMENT ON COLUMN ra_owners.total_thirds IS 'Total number of 3rd place finishes';
COMMENT ON COLUMN ra_owners.win_rate IS 'Win percentage (0-100), calculated as (wins/runners)*100';
COMMENT ON COLUMN ra_owners.place_rate IS 'Place percentage (0-100), calculated as (places/runners)*100';
COMMENT ON COLUMN ra_owners.active_last_30d IS 'TRUE if owner had runners in last 30 days';
COMMENT ON COLUMN ra_owners.stats_updated_at IS 'When statistics were last calculated';

-- Create indexes for owner statistics queries
CREATE INDEX IF NOT EXISTS idx_owners_win_rate ON ra_owners(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_owners_total_runners ON ra_owners(total_runners) WHERE total_runners IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_owners_active ON ra_owners(active_last_30d) WHERE active_last_30d = TRUE;
CREATE INDEX IF NOT EXISTS idx_owners_stats_updated ON ra_owners(stats_updated_at);

-- ============================================================================
-- SECTION 4: CREATE HELPER VIEWS FOR STATISTICS CALCULATION
-- ============================================================================

-- View: Jockey statistics from ra_runners
CREATE OR REPLACE VIEW jockey_statistics AS
SELECT
    j.jockey_id,
    j.name,
    COUNT(r.runner_id) as calculated_total_rides,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as calculated_total_wins,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as calculated_total_places,
    COUNT(CASE WHEN r.position = 2 THEN 1 END) as calculated_total_seconds,
    COUNT(CASE WHEN r.position = 3 THEN 1 END) as calculated_total_thirds,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_win_rate,
    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_place_rate
FROM ra_jockeys j
LEFT JOIN ra_runners r ON r.jockey_id = j.jockey_id AND r.position IS NOT NULL
GROUP BY j.jockey_id, j.name;

COMMENT ON VIEW jockey_statistics IS 'Calculated jockey statistics from ra_runners (use to update ra_jockeys)';

-- View: Trainer statistics from ra_runners
CREATE OR REPLACE VIEW trainer_statistics AS
SELECT
    t.trainer_id,
    t.name,
    COUNT(r.runner_id) as calculated_total_runners,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as calculated_total_wins,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as calculated_total_places,
    COUNT(CASE WHEN r.position = 2 THEN 1 END) as calculated_total_seconds,
    COUNT(CASE WHEN r.position = 3 THEN 1 END) as calculated_total_thirds,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_win_rate,
    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_place_rate,
    -- Recent 14 days stats
    COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' THEN r.runner_id END) as calculated_recent_14d_runs,
    COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1 THEN 1 END) as calculated_recent_14d_wins,
    ROUND(100.0 * COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1 THEN 1 END) /
          NULLIF(COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' THEN r.runner_id END), 0), 2) as calculated_recent_14d_win_rate
FROM ra_trainers t
LEFT JOIN ra_runners r ON r.trainer_id = t.trainer_id AND r.position IS NOT NULL
LEFT JOIN ra_races rc ON rc.race_id = r.race_id
GROUP BY t.trainer_id, t.name;

COMMENT ON VIEW trainer_statistics IS 'Calculated trainer statistics from ra_runners (use to update ra_trainers)';

-- View: Owner statistics from ra_runners
CREATE OR REPLACE VIEW owner_statistics AS
SELECT
    o.owner_id,
    o.name,
    COUNT(DISTINCT r.horse_id) as calculated_total_horses,
    COUNT(r.runner_id) as calculated_total_runners,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as calculated_total_wins,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as calculated_total_places,
    COUNT(CASE WHEN r.position = 2 THEN 1 END) as calculated_total_seconds,
    COUNT(CASE WHEN r.position = 3 THEN 1 END) as calculated_total_thirds,
    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_win_rate,
    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as calculated_place_rate,
    -- Active in last 30 days
    BOOL_OR(rc.race_date >= CURRENT_DATE - INTERVAL '30 days') as calculated_active_last_30d
FROM ra_owners o
LEFT JOIN ra_runners r ON r.owner_id = o.owner_id AND r.position IS NOT NULL
LEFT JOIN ra_races rc ON rc.race_id = r.race_id
GROUP BY o.owner_id, o.name;

COMMENT ON VIEW owner_statistics IS 'Calculated owner statistics from ra_runners (use to update ra_owners)';

-- ============================================================================
-- SECTION 5: CREATE STATISTICS UPDATE FUNCTION
-- ============================================================================

-- Function to update all entity statistics
CREATE OR REPLACE FUNCTION update_entity_statistics()
RETURNS TABLE(
    jockeys_updated INTEGER,
    trainers_updated INTEGER,
    owners_updated INTEGER
) AS $$
DECLARE
    jockey_count INTEGER;
    trainer_count INTEGER;
    owner_count INTEGER;
BEGIN
    -- Update jockey statistics
    UPDATE ra_jockeys j
    SET
        total_rides = s.calculated_total_rides,
        total_wins = s.calculated_total_wins,
        total_places = s.calculated_total_places,
        total_seconds = s.calculated_total_seconds,
        total_thirds = s.calculated_total_thirds,
        win_rate = s.calculated_win_rate,
        place_rate = s.calculated_place_rate,
        stats_updated_at = NOW()
    FROM jockey_statistics s
    WHERE j.jockey_id = s.jockey_id;

    GET DIAGNOSTICS jockey_count = ROW_COUNT;

    -- Update trainer statistics
    UPDATE ra_trainers t
    SET
        total_runners = s.calculated_total_runners,
        total_wins = s.calculated_total_wins,
        total_places = s.calculated_total_places,
        total_seconds = s.calculated_total_seconds,
        total_thirds = s.calculated_total_thirds,
        win_rate = s.calculated_win_rate,
        place_rate = s.calculated_place_rate,
        recent_14d_runs = s.calculated_recent_14d_runs,
        recent_14d_wins = s.calculated_recent_14d_wins,
        recent_14d_win_rate = s.calculated_recent_14d_win_rate,
        stats_updated_at = NOW()
    FROM trainer_statistics s
    WHERE t.trainer_id = s.trainer_id;

    GET DIAGNOSTICS trainer_count = ROW_COUNT;

    -- Update owner statistics
    UPDATE ra_owners o
    SET
        total_horses = s.calculated_total_horses,
        total_runners = s.calculated_total_runners,
        total_wins = s.calculated_total_wins,
        total_places = s.calculated_total_places,
        total_seconds = s.calculated_total_seconds,
        total_thirds = s.calculated_total_thirds,
        win_rate = s.calculated_win_rate,
        place_rate = s.calculated_place_rate,
        active_last_30d = s.calculated_active_last_30d,
        stats_updated_at = NOW()
    FROM owner_statistics s
    WHERE o.owner_id = s.owner_id;

    GET DIAGNOSTICS owner_count = ROW_COUNT;

    -- Return counts
    RETURN QUERY SELECT jockey_count, trainer_count, owner_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION update_entity_statistics() IS 'Updates all entity statistics from ra_runners data. Run daily/weekly.';

-- ============================================================================
-- SECTION 6: VALIDATION
-- ============================================================================

-- Verify all columns were added
DO $$
DECLARE
    missing_columns INTEGER;
BEGIN
    -- Check ra_jockeys columns
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('total_rides'),
        ('total_wins'),
        ('win_rate'),
        ('stats_updated_at')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_jockeys'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_jockeys', missing_columns;
    END IF;

    -- Check ra_trainers columns
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('total_runners'),
        ('total_wins'),
        ('win_rate'),
        ('recent_14d_runs'),
        ('stats_updated_at')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_trainers'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_trainers', missing_columns;
    END IF;

    -- Check ra_owners columns
    SELECT COUNT(*) INTO missing_columns
    FROM (VALUES
        ('total_horses'),
        ('total_runners'),
        ('total_wins'),
        ('win_rate'),
        ('active_last_30d'),
        ('stats_updated_at')
    ) AS expected(column_name)
    WHERE NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_owners'
        AND information_schema.columns.column_name = expected.column_name
    );

    IF missing_columns > 0 THEN
        RAISE EXCEPTION 'Missing % columns in ra_owners', missing_columns;
    END IF;

    RAISE NOTICE '✓ All columns added successfully';
END $$;

-- Verify views were created
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'jockey_statistics') THEN
        RAISE EXCEPTION 'View jockey_statistics not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'trainer_statistics') THEN
        RAISE EXCEPTION 'View trainer_statistics not created';
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.views WHERE table_name = 'owner_statistics') THEN
        RAISE EXCEPTION 'View owner_statistics not created';
    END IF;

    RAISE NOTICE '✓ All views created successfully';
END $$;

-- Verify function was created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public' AND p.proname = 'update_entity_statistics'
    ) THEN
        RAISE EXCEPTION 'Function update_entity_statistics not created';
    END IF;

    RAISE NOTICE '✓ Update function created successfully';
END $$;

-- ============================================================================
-- SECTION 7: SUMMARY REPORT
-- ============================================================================

SELECT
    '✓ Migration 007 Complete - Entity Table Enhancements' AS status,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_jockeys') AS ra_jockeys_column_count,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_trainers') AS ra_trainers_column_count,
    (SELECT COUNT(*) FROM information_schema.columns WHERE table_name = 'ra_owners') AS ra_owners_column_count,
    NOW() AS completed_at;

-- List new columns added to each table
SELECT 'New ra_jockeys columns:' AS info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_jockeys'
  AND column_name IN (
      'total_rides', 'total_wins', 'total_places', 'total_seconds', 'total_thirds',
      'win_rate', 'place_rate', 'stats_updated_at'
  )
ORDER BY column_name;

SELECT 'New ra_trainers columns:' AS info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_trainers'
  AND column_name IN (
      'total_runners', 'total_wins', 'total_places', 'total_seconds', 'total_thirds',
      'win_rate', 'place_rate', 'recent_14d_runs', 'recent_14d_wins', 'recent_14d_win_rate',
      'stats_updated_at'
  )
ORDER BY column_name;

SELECT 'New ra_owners columns:' AS info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_owners'
  AND column_name IN (
      'total_horses', 'total_runners', 'total_wins', 'total_places', 'total_seconds', 'total_thirds',
      'win_rate', 'place_rate', 'active_last_30d', 'stats_updated_at'
  )
ORDER BY column_name;

-- List new indexes created
SELECT 'New indexes:' AS info;
SELECT indexname, tablename
FROM pg_indexes
WHERE schemaname = 'public'
  AND tablename IN ('ra_jockeys', 'ra_trainers', 'ra_owners')
  AND (indexname LIKE 'idx_jockeys_%' OR indexname LIKE 'idx_trainers_%' OR indexname LIKE 'idx_owners_%')
ORDER BY tablename, indexname;

-- List new views created
SELECT 'New views:' AS info;
SELECT table_name as view_name
FROM information_schema.views
WHERE table_schema = 'public'
  AND table_name IN ('jockey_statistics', 'trainer_statistics', 'owner_statistics')
ORDER BY table_name;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- USAGE INSTRUCTIONS:
--
-- 1. Run this migration:
--    psql $SUPABASE_URL -f migrations/007_add_entity_table_enhancements.sql
--
-- 2. After position data is populated in ra_runners, update statistics:
--    psql $SUPABASE_URL -c "SELECT * FROM update_entity_statistics();"
--
-- 3. Schedule daily statistics updates:
--    Add cron job or scheduled task to run:
--    SELECT * FROM update_entity_statistics();
--
-- 4. Query statistics:
--    SELECT * FROM jockey_statistics WHERE calculated_win_rate > 15;
--    SELECT * FROM trainer_statistics ORDER BY calculated_win_rate DESC LIMIT 10;
--    SELECT * FROM owner_statistics WHERE calculated_active_last_30d = TRUE;
--
-- NOTES:
-- - Statistics will be NULL until update_entity_statistics() is called
-- - Position data must be populated in ra_runners first
-- - Run statistics update after backfilling position data
-- - Schedule regular updates (daily or weekly recommended)
--
-- ROLLBACK:
-- If you need to rollback this migration:
--
-- DROP FUNCTION IF EXISTS update_entity_statistics();
-- DROP VIEW IF EXISTS jockey_statistics;
-- DROP VIEW IF EXISTS trainer_statistics;
-- DROP VIEW IF EXISTS owner_statistics;
--
-- DROP INDEX IF EXISTS idx_jockeys_win_rate;
-- DROP INDEX IF EXISTS idx_jockeys_total_rides;
-- DROP INDEX IF EXISTS idx_jockeys_stats_updated;
-- DROP INDEX IF EXISTS idx_trainers_win_rate;
-- DROP INDEX IF EXISTS idx_trainers_total_runners;
-- DROP INDEX IF EXISTS idx_trainers_recent_win_rate;
-- DROP INDEX IF EXISTS idx_trainers_stats_updated;
-- DROP INDEX IF EXISTS idx_owners_win_rate;
-- DROP INDEX IF EXISTS idx_owners_total_runners;
-- DROP INDEX IF EXISTS idx_owners_active;
-- DROP INDEX IF EXISTS idx_owners_stats_updated;
--
-- ALTER TABLE ra_jockeys
--   DROP COLUMN total_rides,
--   DROP COLUMN total_wins,
--   DROP COLUMN total_places,
--   DROP COLUMN total_seconds,
--   DROP COLUMN total_thirds,
--   DROP COLUMN win_rate,
--   DROP COLUMN place_rate,
--   DROP COLUMN stats_updated_at;
--
-- ALTER TABLE ra_trainers
--   DROP COLUMN total_runners,
--   DROP COLUMN total_wins,
--   DROP COLUMN total_places,
--   DROP COLUMN total_seconds,
--   DROP COLUMN total_thirds,
--   DROP COLUMN win_rate,
--   DROP COLUMN place_rate,
--   DROP COLUMN recent_14d_runs,
--   DROP COLUMN recent_14d_wins,
--   DROP COLUMN recent_14d_win_rate,
--   DROP COLUMN stats_updated_at;
--
-- ALTER TABLE ra_owners
--   DROP COLUMN total_horses,
--   DROP COLUMN total_runners,
--   DROP COLUMN total_wins,
--   DROP COLUMN total_places,
--   DROP COLUMN total_seconds,
--   DROP COLUMN total_thirds,
--   DROP COLUMN win_rate,
--   DROP COLUMN place_rate,
--   DROP COLUMN active_last_30d,
--   DROP COLUMN stats_updated_at;
--
-- ============================================================================
