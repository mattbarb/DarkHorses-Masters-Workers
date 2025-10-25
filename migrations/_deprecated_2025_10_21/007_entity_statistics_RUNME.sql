-- ============================================================================
-- MIGRATION 007: Entity Statistics (Simplified for Manual Execution)
-- ============================================================================
-- Run this in Supabase SQL Editor to add statistics to jockeys/trainers/owners
-- ============================================================================

BEGIN;

-- ============================================================================
-- JOCKEYS: Add Statistics Columns
-- ============================================================================

ALTER TABLE ra_jockeys
ADD COLUMN IF NOT EXISTS total_rides INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_wins INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_places INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_seconds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS total_thirds INTEGER DEFAULT NULL,
ADD COLUMN IF NOT EXISTS win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS place_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN IF NOT EXISTS stats_updated_at TIMESTAMP DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_jockeys_win_rate ON ra_jockeys(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jockeys_total_rides ON ra_jockeys(total_rides) WHERE total_rides IS NOT NULL;

-- ============================================================================
-- TRAINERS: Add Statistics Columns
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_trainers_win_rate ON ra_trainers(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_trainers_total_runners ON ra_trainers(total_runners) WHERE total_runners IS NOT NULL;

-- ============================================================================
-- OWNERS: Add Statistics Columns
-- ============================================================================

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

CREATE INDEX IF NOT EXISTS idx_owners_win_rate ON ra_owners(win_rate) WHERE win_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_owners_total_runners ON ra_owners(total_runners) WHERE total_runners IS NOT NULL;

-- ============================================================================
-- CREATE STATISTICS VIEWS
-- ============================================================================

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
    COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' THEN r.runner_id END) as calculated_recent_14d_runs,
    COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1 THEN 1 END) as calculated_recent_14d_wins,
    ROUND(100.0 * COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1 THEN 1 END) /
          NULLIF(COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' THEN r.runner_id END), 0), 2) as calculated_recent_14d_win_rate
FROM ra_trainers t
LEFT JOIN ra_runners r ON r.trainer_id = t.trainer_id AND r.position IS NOT NULL
LEFT JOIN ra_races rc ON rc.race_id = r.race_id
GROUP BY t.trainer_id, t.name;

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
    BOOL_OR(rc.race_date >= CURRENT_DATE - INTERVAL '30 days') as calculated_active_last_30d
FROM ra_owners o
LEFT JOIN ra_runners r ON r.owner_id = o.owner_id AND r.position IS NOT NULL
LEFT JOIN ra_races rc ON rc.race_id = r.race_id
GROUP BY o.owner_id, o.name;

-- ============================================================================
-- CREATE UPDATE FUNCTION
-- ============================================================================

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

COMMIT;

-- ============================================================================
-- DONE! Now run: python3 scripts/calculate_entity_statistics.py
-- ============================================================================
