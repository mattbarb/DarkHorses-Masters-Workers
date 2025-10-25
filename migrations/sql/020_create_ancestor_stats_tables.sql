-- Migration 020: Create ancestor statistics tables
-- Date: 2025-10-18
-- Purpose: Track sire/dam/damsire own race results and progeny/grandoffspring statistics

-- =============================================================================
-- STAGE 1: Create ra_sire_stats table
-- =============================================================================

CREATE TABLE IF NOT EXISTS ra_sire_stats (
    -- Primary key
    sire_id VARCHAR PRIMARY KEY,
    sire_name VARCHAR NOT NULL,
    sire_region VARCHAR,

    -- Sire's own racing career
    own_race_runs INT DEFAULT 0,
    own_race_wins INT DEFAULT 0,
    own_race_places INT DEFAULT 0,  -- Positions 1-3
    own_total_prize DECIMAL(12,2) DEFAULT 0,
    own_best_position INT,
    own_avg_position DECIMAL(5,2),
    own_career_start DATE,
    own_career_end DATE,

    -- Progeny statistics (offspring performance)
    total_progeny INT DEFAULT 0,              -- Unique horses
    progeny_total_runs INT DEFAULT 0,
    progeny_wins INT DEFAULT 0,
    progeny_places INT DEFAULT 0,
    progeny_total_prize DECIMAL(15,2) DEFAULT 0,
    progeny_win_rate DECIMAL(5,2),            -- wins / total_runs
    progeny_place_rate DECIMAL(5,2),          -- places / total_runs
    progeny_avg_position DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Indexes will be created in Stage 4
    CONSTRAINT check_own_runs CHECK (own_race_runs >= 0),
    CONSTRAINT check_progeny_count CHECK (total_progeny >= 0)
);

COMMENT ON TABLE ra_sire_stats IS 'Sire racing statistics: own career results + progeny performance';

-- =============================================================================
-- STAGE 2: Create ra_dam_stats table
-- =============================================================================

CREATE TABLE IF NOT EXISTS ra_dam_stats (
    -- Primary key
    dam_id VARCHAR PRIMARY KEY,
    dam_name VARCHAR NOT NULL,
    dam_region VARCHAR,

    -- Dam's own racing career
    own_race_runs INT DEFAULT 0,
    own_race_wins INT DEFAULT 0,
    own_race_places INT DEFAULT 0,
    own_total_prize DECIMAL(12,2) DEFAULT 0,
    own_best_position INT,
    own_avg_position DECIMAL(5,2),
    own_career_start DATE,
    own_career_end DATE,

    -- Progeny statistics (offspring performance)
    total_progeny INT DEFAULT 0,
    progeny_total_runs INT DEFAULT 0,
    progeny_wins INT DEFAULT 0,
    progeny_places INT DEFAULT 0,
    progeny_total_prize DECIMAL(15,2) DEFAULT 0,
    progeny_win_rate DECIMAL(5,2),
    progeny_place_rate DECIMAL(5,2),
    progeny_avg_position DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT check_own_runs_dam CHECK (own_race_runs >= 0),
    CONSTRAINT check_progeny_count_dam CHECK (total_progeny >= 0)
);

COMMENT ON TABLE ra_dam_stats IS 'Dam racing statistics: own career results + progeny performance';

-- =============================================================================
-- STAGE 3: Create ra_damsire_stats table
-- =============================================================================

CREATE TABLE IF NOT EXISTS ra_damsire_stats (
    -- Primary key
    damsire_id VARCHAR PRIMARY KEY,
    damsire_name VARCHAR NOT NULL,
    damsire_region VARCHAR,

    -- Damsire's own racing career
    own_race_runs INT DEFAULT 0,
    own_race_wins INT DEFAULT 0,
    own_race_places INT DEFAULT 0,
    own_total_prize DECIMAL(12,2) DEFAULT 0,
    own_best_position INT,
    own_avg_position DECIMAL(5,2),
    own_career_start DATE,
    own_career_end DATE,

    -- Grandoffspring statistics (maternal grandchildren performance)
    total_grandoffspring INT DEFAULT 0,       -- Unique horses with this damsire
    grandoffspring_total_runs INT DEFAULT 0,
    grandoffspring_wins INT DEFAULT 0,
    grandoffspring_places INT DEFAULT 0,
    grandoffspring_total_prize DECIMAL(15,2) DEFAULT 0,
    grandoffspring_win_rate DECIMAL(5,2),
    grandoffspring_place_rate DECIMAL(5,2),
    grandoffspring_avg_position DECIMAL(5,2),

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    CONSTRAINT check_own_runs_damsire CHECK (own_race_runs >= 0),
    CONSTRAINT check_grandoffspring_count CHECK (total_grandoffspring >= 0)
);

COMMENT ON TABLE ra_damsire_stats IS 'Damsire racing statistics: own career results + grandoffspring performance';

-- =============================================================================
-- STAGE 4: Create indexes for performance
-- =============================================================================

-- ra_sire_stats indexes
CREATE INDEX IF NOT EXISTS idx_sire_stats_name ON ra_sire_stats(sire_name);
CREATE INDEX IF NOT EXISTS idx_sire_stats_progeny_wins ON ra_sire_stats(progeny_wins DESC);
CREATE INDEX IF NOT EXISTS idx_sire_stats_progeny_count ON ra_sire_stats(total_progeny DESC);
CREATE INDEX IF NOT EXISTS idx_sire_stats_win_rate ON ra_sire_stats(progeny_win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_sire_stats_own_wins ON ra_sire_stats(own_race_wins DESC);

-- ra_dam_stats indexes
CREATE INDEX IF NOT EXISTS idx_dam_stats_name ON ra_dam_stats(dam_name);
CREATE INDEX IF NOT EXISTS idx_dam_stats_progeny_wins ON ra_dam_stats(progeny_wins DESC);
CREATE INDEX IF NOT EXISTS idx_dam_stats_progeny_count ON ra_dam_stats(total_progeny DESC);
CREATE INDEX IF NOT EXISTS idx_dam_stats_win_rate ON ra_dam_stats(progeny_win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_dam_stats_own_wins ON ra_dam_stats(own_race_wins DESC);

-- ra_damsire_stats indexes
CREATE INDEX IF NOT EXISTS idx_damsire_stats_name ON ra_damsire_stats(damsire_name);
CREATE INDEX IF NOT EXISTS idx_damsire_stats_grandoffspring_wins ON ra_damsire_stats(grandoffspring_wins DESC);
CREATE INDEX IF NOT EXISTS idx_damsire_stats_grandoffspring_count ON ra_damsire_stats(total_grandoffspring DESC);
CREATE INDEX IF NOT EXISTS idx_damsire_stats_win_rate ON ra_damsire_stats(grandoffspring_win_rate DESC);
CREATE INDEX IF NOT EXISTS idx_damsire_stats_own_wins ON ra_damsire_stats(own_race_wins DESC);

-- =============================================================================
-- NOTES
-- =============================================================================
--
-- These tables store:
-- 1. Ancestor's OWN racing career statistics
--    - Calculated from ra_runners where horse_id = sire_id/dam_id/damsire_id
--    - Shows how successful the ancestor was as a racehorse
--
-- 2. Progeny/Grandoffspring performance statistics
--    - Calculated from ra_lineage + ra_runners
--    - Shows breeding success (how well offspring perform)
--
-- Population strategy:
-- 1. For each unique ancestor in ra_lineage
-- 2. Find their own racing career (if they raced)
--    - Query ra_runners WHERE horse_id = ancestor_id
-- 3. Calculate progeny/grandoffspring stats
--    - Query ra_lineage + ra_runners for offspring performance
--
-- Update frequency:
-- - Can be refreshed periodically (weekly/monthly)
-- - Or updated incrementally as new results come in
--
-- Example queries enabled:
-- - Best sires by progeny win rate
-- - Dams who were great racers and great producers
-- - Damsires with most successful grandoffspring
-- - Compare ancestor's own success vs breeding success
--
-- =============================================================================
