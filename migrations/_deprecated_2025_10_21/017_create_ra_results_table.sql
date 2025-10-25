-- ============================================================================
-- Migration 017: Create ra_results Table
-- ============================================================================
-- Creates a dedicated results table to capture race-level result data
-- including tote pools, winning time, comments, and non-runners
--
-- This separates result-specific data from the ra_races table which stores
-- race metadata. Runner-level results remain in ra_runners.
-- ============================================================================

-- Create ra_results table
CREATE TABLE IF NOT EXISTS ra_results (
    -- Primary key
    race_id VARCHAR(50) PRIMARY KEY,

    -- Race identification (duplicated from ra_races for convenience)
    course_id VARCHAR(50),
    course_name VARCHAR(255),
    race_name VARCHAR(255),
    race_date DATE,
    off_time VARCHAR(20),
    off_datetime TIMESTAMP,
    region VARCHAR(10),

    -- Race classification
    type VARCHAR(50),          -- Race type (e.g., 'Flat', 'NH Flat', 'Hurdle', 'Chase')
    class VARCHAR(50),         -- Race class
    pattern VARCHAR(50),       -- Pattern race indicator
    rating_band VARCHAR(50),   -- Rating band
    age_band VARCHAR(50),      -- Age band restriction
    sex_rest VARCHAR(50),      -- Sex restriction

    -- Distance
    dist VARCHAR(20),          -- Distance string (e.g., "1m 2f")
    dist_y INTEGER,            -- Distance in yards
    dist_m INTEGER,            -- Distance in meters
    dist_f VARCHAR(20),        -- Distance in furlongs (can be "8f", "11f", etc.)

    -- Going and surface
    going VARCHAR(50),         -- Going description
    surface VARCHAR(50),       -- Surface type
    jumps VARCHAR(50),         -- Jumps information (for NH races)

    -- Result-specific data
    winning_time_detail TEXT,  -- Winning time with details
    comments TEXT,             -- Race comments/notes

    -- Non-runners information
    non_runners TEXT,          -- Non-runners data (JSON or text)

    -- Tote pools (UK/IRE betting pools)
    tote_win VARCHAR(50),      -- Tote win dividend
    tote_pl VARCHAR(255),      -- Tote place dividends (can be multiple)
    tote_ex VARCHAR(50),       -- Tote exacta
    tote_csf VARCHAR(50),      -- Tote CSF (Computer Straight Forecast)
    tote_tricast VARCHAR(50),  -- Tote tricast
    tote_trifecta VARCHAR(50), -- Tote trifecta

    -- Metadata
    api_data JSONB,            -- Full API response for debugging
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    -- Foreign key to ra_races table
    CONSTRAINT fk_ra_results_race_id FOREIGN KEY (race_id) REFERENCES ra_races(race_id) ON DELETE CASCADE
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_ra_results_race_date ON ra_results(race_date);
CREATE INDEX IF NOT EXISTS idx_ra_results_course_id ON ra_results(course_id);
CREATE INDEX IF NOT EXISTS idx_ra_results_region ON ra_results(region);
CREATE INDEX IF NOT EXISTS idx_ra_results_type ON ra_results(type);
CREATE INDEX IF NOT EXISTS idx_ra_results_class ON ra_results(class);

-- Add comment to table
COMMENT ON TABLE ra_results IS 'Race results data including tote pools, winning time, and race-level result information';

-- Add comments to key columns
COMMENT ON COLUMN ra_results.race_id IS 'Primary key - unique race identifier from Racing API';
COMMENT ON COLUMN ra_results.winning_time_detail IS 'Winning time with additional details (e.g., "1:48.55 (slow by 3.25s)")';
COMMENT ON COLUMN ra_results.comments IS 'Race comments and notes from stewards/officials';
COMMENT ON COLUMN ra_results.non_runners IS 'Information about non-runners (horses that did not start)';
COMMENT ON COLUMN ra_results.tote_win IS 'Tote win dividend (e.g., "£4.50")';
COMMENT ON COLUMN ra_results.tote_pl IS 'Tote place dividends (comma-separated for multiple places)';
COMMENT ON COLUMN ra_results.tote_ex IS 'Tote exacta dividend (1st and 2nd in correct order)';
COMMENT ON COLUMN ra_results.tote_csf IS 'Computer Straight Forecast dividend';
COMMENT ON COLUMN ra_results.tote_tricast IS 'Tote tricast dividend (1st, 2nd, 3rd in correct order)';
COMMENT ON COLUMN ra_results.tote_trifecta IS 'Tote trifecta dividend (1st, 2nd, 3rd in any order)';

-- ============================================================================
-- VERIFICATION QUERY
-- ============================================================================
-- After running this migration, verify with:
--
-- SELECT COUNT(*) FROM ra_results;
-- SELECT * FROM ra_results LIMIT 5;
--
-- Check that foreign key relationship exists:
-- SELECT
--     tc.constraint_name,
--     tc.table_name,
--     kcu.column_name,
--     ccu.table_name AS foreign_table_name,
--     ccu.column_name AS foreign_column_name
-- FROM
--     information_schema.table_constraints AS tc
--     JOIN information_schema.key_column_usage AS kcu
--       ON tc.constraint_name = kcu.constraint_name
--       AND tc.table_schema = kcu.table_schema
--     JOIN information_schema.constraint_column_usage AS ccu
--       ON ccu.constraint_name = tc.constraint_name
--       AND ccu.table_schema = tc.table_schema
-- WHERE tc.constraint_type = 'FOREIGN KEY'
--   AND tc.table_name = 'ra_results';
-- ============================================================================
