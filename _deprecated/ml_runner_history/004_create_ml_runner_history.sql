-- ============================================================================
-- DATABASE MIGRATION: Create ML Runner History Table
-- ============================================================================
-- Purpose: Create denormalized table for ML predictions with complete runner history
-- Date: 2025-10-13
-- Related: ML prediction system for upcoming races
-- ============================================================================

BEGIN;

-- ============================================================================
-- SECTION 1: CREATE MAIN TABLE
-- ============================================================================

CREATE TABLE IF NOT EXISTS dh_ml_runner_history (
    -- Primary identification
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    race_id TEXT NOT NULL,
    runner_id TEXT NOT NULL,
    horse_id TEXT NOT NULL,
    horse_name TEXT NOT NULL,
    compilation_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),

    -- Race context (upcoming race details)
    race_date DATE NOT NULL,
    off_datetime TIMESTAMP WITH TIME ZONE,
    course_id TEXT,
    course_name TEXT,
    region TEXT,
    distance_meters INTEGER,
    distance_f NUMERIC,
    surface TEXT,
    going TEXT,
    race_type TEXT,
    race_class TEXT,
    age_band TEXT,
    prize_money NUMERIC,
    field_size INTEGER,

    -- Current runner details
    current_weight_lbs INTEGER,
    current_draw INTEGER,
    current_number INTEGER,
    headgear TEXT,
    blinkers BOOLEAN DEFAULT FALSE,
    cheekpieces BOOLEAN DEFAULT FALSE,
    visor BOOLEAN DEFAULT FALSE,
    tongue_tie BOOLEAN DEFAULT FALSE,

    -- Current entities
    jockey_id TEXT,
    jockey_name TEXT,
    trainer_id TEXT,
    trainer_name TEXT,
    owner_id TEXT,
    owner_name TEXT,
    official_rating INTEGER,
    racing_post_rating INTEGER,
    timeform_rating INTEGER,

    -- Career statistics (all-time)
    total_races INTEGER DEFAULT 0,
    total_wins INTEGER DEFAULT 0,
    total_places INTEGER DEFAULT 0,
    total_seconds INTEGER DEFAULT 0,
    total_thirds INTEGER DEFAULT 0,
    win_rate NUMERIC(5,2),
    place_rate NUMERIC(5,2),
    avg_finish_position NUMERIC(5,2),
    total_earnings NUMERIC(12,2),
    days_since_last_run INTEGER,

    -- Context-specific performance
    course_runs INTEGER DEFAULT 0,
    course_wins INTEGER DEFAULT 0,
    course_places INTEGER DEFAULT 0,
    course_win_rate NUMERIC(5,2),

    distance_runs INTEGER DEFAULT 0,
    distance_wins INTEGER DEFAULT 0,
    distance_places INTEGER DEFAULT 0,
    distance_win_rate NUMERIC(5,2),

    surface_runs INTEGER DEFAULT 0,
    surface_wins INTEGER DEFAULT 0,
    surface_places INTEGER DEFAULT 0,
    surface_win_rate NUMERIC(5,2),

    going_runs INTEGER DEFAULT 0,
    going_wins INTEGER DEFAULT 0,
    going_places INTEGER DEFAULT 0,
    going_win_rate NUMERIC(5,2),

    class_runs INTEGER DEFAULT 0,
    class_wins INTEGER DEFAULT 0,
    class_places INTEGER DEFAULT 0,
    class_win_rate NUMERIC(5,2),

    -- Recent form (last 5-10 races)
    last_5_positions INTEGER[],
    last_5_dates DATE[],
    last_5_courses TEXT[],
    last_5_distances INTEGER[],
    last_5_classes TEXT[],
    last_10_positions INTEGER[],
    recent_form_score NUMERIC(5,2),

    -- Relationship statistics
    horse_jockey_runs INTEGER DEFAULT 0,
    horse_jockey_wins INTEGER DEFAULT 0,
    horse_jockey_win_rate NUMERIC(5,2),

    horse_trainer_runs INTEGER DEFAULT 0,
    horse_trainer_wins INTEGER DEFAULT 0,
    horse_trainer_win_rate NUMERIC(5,2),

    jockey_trainer_runs INTEGER DEFAULT 0,
    jockey_trainer_wins INTEGER DEFAULT 0,
    jockey_trainer_win_rate NUMERIC(5,2),

    -- Trainer/Jockey career stats (JSONB)
    jockey_career_stats JSONB,
    trainer_career_stats JSONB,

    -- Pedigree information
    sire_id TEXT,
    sire_name TEXT,
    dam_id TEXT,
    dam_name TEXT,
    damsire_id TEXT,
    damsire_name TEXT,
    horse_age INTEGER,
    horse_sex TEXT,
    horse_dob DATE,
    pedigree_data JSONB,

    -- Historical races (complete array)
    historical_races JSONB,
    historical_races_count INTEGER DEFAULT 0,

    -- Odds and betting data
    current_odds JSONB,
    historical_odds_average NUMERIC(8,2),

    -- Status flags
    is_scratched BOOLEAN DEFAULT FALSE,
    is_non_runner BOOLEAN DEFAULT FALSE,
    has_form BOOLEAN DEFAULT FALSE,

    -- Metadata
    ml_features_version TEXT DEFAULT '1.0',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================================================
-- SECTION 2: CREATE INDEXES
-- ============================================================================

-- Primary lookup indexes
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_race_id
    ON dh_ml_runner_history(race_id);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_horse_id
    ON dh_ml_runner_history(horse_id);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_runner_id
    ON dh_ml_runner_history(runner_id);

-- Date-based indexes for cleanup and queries
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_race_date
    ON dh_ml_runner_history(race_date);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_compilation_date
    ON dh_ml_runner_history(compilation_date DESC);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_race_date_course
    ON dh_ml_runner_history(race_date, course_id);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_region_date
    ON dh_ml_runner_history(region, race_date);

-- Entity indexes
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_jockey_id
    ON dh_ml_runner_history(jockey_id);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_trainer_id
    ON dh_ml_runner_history(trainer_id);

-- Status indexes
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_is_scratched
    ON dh_ml_runner_history(is_scratched) WHERE is_scratched = FALSE;

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_has_form
    ON dh_ml_runner_history(has_form) WHERE has_form = TRUE;

-- JSONB indexes for deep queries
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_historical_races_gin
    ON dh_ml_runner_history USING GIN (historical_races);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_jockey_stats_gin
    ON dh_ml_runner_history USING GIN (jockey_career_stats);

CREATE INDEX IF NOT EXISTS idx_ml_runner_history_trainer_stats_gin
    ON dh_ml_runner_history USING GIN (trainer_career_stats);

-- Unique constraint to prevent duplicates
-- Note: We allow multiple compilations per runner (tracked by compilation_date)
-- Cleanup old compilations via the cleanup function
CREATE INDEX IF NOT EXISTS idx_ml_runner_history_runner_compilation
    ON dh_ml_runner_history(runner_id, compilation_date DESC);

-- ============================================================================
-- SECTION 3: ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE dh_ml_runner_history IS
'Denormalized ML-ready table containing complete runner history for upcoming races';

-- Identification columns
COMMENT ON COLUMN dh_ml_runner_history.race_id IS
'ID of the upcoming race this runner is entered in';

COMMENT ON COLUMN dh_ml_runner_history.compilation_date IS
'When this data was compiled (for versioning and cleanup)';

-- Career statistics
COMMENT ON COLUMN dh_ml_runner_history.total_races IS
'Total career races for this horse';

COMMENT ON COLUMN dh_ml_runner_history.win_rate IS
'Career win percentage (wins/races * 100)';

COMMENT ON COLUMN dh_ml_runner_history.place_rate IS
'Career place percentage (places/races * 100, where place = top 3)';

-- Context-specific performance
COMMENT ON COLUMN dh_ml_runner_history.course_runs IS
'Number of previous runs at this specific course';

COMMENT ON COLUMN dh_ml_runner_history.distance_runs IS
'Number of previous runs at similar distance (±10%)';

COMMENT ON COLUMN dh_ml_runner_history.going_runs IS
'Number of previous runs on similar going conditions';

-- Recent form
COMMENT ON COLUMN dh_ml_runner_history.last_5_positions IS
'Array of last 5 finishing positions (most recent first)';

COMMENT ON COLUMN dh_ml_runner_history.recent_form_score IS
'Calculated form score based on recent performances (0-100)';

-- Relationship statistics
COMMENT ON COLUMN dh_ml_runner_history.horse_jockey_runs IS
'Number of races this horse has run with this jockey';

COMMENT ON COLUMN dh_ml_runner_history.horse_trainer_runs IS
'Number of races this horse has run with this trainer';

-- Historical data
COMMENT ON COLUMN dh_ml_runner_history.historical_races IS
'Complete array of all past races for this horse (JSONB)';

COMMENT ON COLUMN dh_ml_runner_history.jockey_career_stats IS
'Jockey overall career statistics (JSONB)';

COMMENT ON COLUMN dh_ml_runner_history.trainer_career_stats IS
'Trainer overall career statistics (JSONB)';

-- Status flags
COMMENT ON COLUMN dh_ml_runner_history.has_form IS
'TRUE if horse has at least 1 previous race on record';

COMMENT ON COLUMN dh_ml_runner_history.ml_features_version IS
'Schema version for ML features (for backward compatibility)';

-- ============================================================================
-- SECTION 4: CREATE HELPER VIEWS
-- ============================================================================

-- View for upcoming races with ML data
CREATE OR REPLACE VIEW v_ml_upcoming_races AS
SELECT
    race_date,
    race_id,
    course_name,
    region,
    race_class,
    distance_meters,
    COUNT(*) as runners_count,
    AVG(win_rate) as avg_win_rate,
    AVG(recent_form_score) as avg_form_score,
    MAX(compilation_date) as last_compiled
FROM dh_ml_runner_history
WHERE race_date >= CURRENT_DATE
  AND is_scratched = FALSE
GROUP BY race_date, race_id, course_name, region, race_class, distance_meters
ORDER BY race_date, race_id;

COMMENT ON VIEW v_ml_upcoming_races IS
'Summary view of upcoming races with ML data compiled';

-- View for ML data quality monitoring
CREATE OR REPLACE VIEW v_ml_data_quality AS
SELECT
    race_date,
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE has_form = TRUE) as runners_with_form,
    COUNT(*) FILTER (WHERE historical_races_count > 0) as runners_with_history,
    COUNT(*) FILTER (WHERE historical_races_count >= 5) as runners_with_5plus_races,
    AVG(historical_races_count) as avg_races_per_horse,
    COUNT(*) FILTER (WHERE course_runs > 0) as runners_with_course_experience,
    COUNT(*) FILTER (WHERE distance_runs > 0) as runners_with_distance_experience,
    MAX(compilation_date) as last_updated
FROM dh_ml_runner_history
WHERE race_date >= CURRENT_DATE
  AND is_scratched = FALSE
GROUP BY race_date
ORDER BY race_date;

COMMENT ON VIEW v_ml_data_quality IS
'Data quality metrics for ML runner history table';

-- ============================================================================
-- SECTION 5: CREATE CLEANUP FUNCTION
-- ============================================================================

-- Function to clean up old race data
CREATE OR REPLACE FUNCTION cleanup_old_ml_data(days_to_keep INTEGER DEFAULT 30)
RETURNS TABLE(deleted_count BIGINT) AS $$
DECLARE
    cutoff_date DATE;
    rows_deleted BIGINT;
BEGIN
    -- Calculate cutoff date
    cutoff_date := CURRENT_DATE - days_to_keep;

    -- Delete old records
    DELETE FROM dh_ml_runner_history
    WHERE race_date < cutoff_date;

    GET DIAGNOSTICS rows_deleted = ROW_COUNT;

    RETURN QUERY SELECT rows_deleted;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION cleanup_old_ml_data IS
'Removes ML runner history data for races older than specified days (default: 30)';

-- ============================================================================
-- SECTION 6: VALIDATION
-- ============================================================================

-- Verify table was created
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.tables
        WHERE table_name = 'dh_ml_runner_history'
    ) THEN
        RAISE EXCEPTION 'Table dh_ml_runner_history was not created';
    END IF;

    RAISE NOTICE 'Table dh_ml_runner_history created successfully';
END $$;

-- Count indexes
DO $$
DECLARE
    index_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO index_count
    FROM pg_indexes
    WHERE tablename = 'dh_ml_runner_history';

    RAISE NOTICE 'Created % indexes on dh_ml_runner_history', index_count;
END $$;

-- ============================================================================
-- SECTION 7: SUMMARY REPORT
-- ============================================================================

SELECT
    '✓ Migration 004 Complete' AS status,
    (SELECT COUNT(*) FROM information_schema.columns
     WHERE table_name = 'dh_ml_runner_history') AS column_count,
    (SELECT COUNT(*) FROM pg_indexes
     WHERE tablename = 'dh_ml_runner_history') AS index_count,
    NOW() AS completed_at;

-- List all columns
SELECT 'Columns created:' AS info;
SELECT
    column_name,
    data_type,
    CASE
        WHEN is_nullable = 'NO' THEN 'NOT NULL'
        ELSE 'NULLABLE'
    END as nullable
FROM information_schema.columns
WHERE table_name = 'dh_ml_runner_history'
ORDER BY ordinal_position;

COMMIT;

-- ============================================================================
-- MIGRATION COMPLETE
-- ============================================================================

-- Next steps:
-- 1. Run this migration: psql -f migrations/004_create_ml_runner_history.sql
-- 2. Implement scripts/compile_ml_data.py
-- 3. Add to scheduler configuration
-- 4. Create monitoring dashboard

-- For rollback:
-- DROP TABLE IF EXISTS dh_ml_runner_history CASCADE;
-- DROP VIEW IF EXISTS v_ml_upcoming_races CASCADE;
-- DROP VIEW IF EXISTS v_ml_data_quality CASCADE;
-- DROP FUNCTION IF EXISTS cleanup_old_ml_data CASCADE;

-- ============================================================================
