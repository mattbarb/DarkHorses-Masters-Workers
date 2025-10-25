-- Migration 021: Add Latitude and Longitude to ra_courses
--
-- This migration adds geographical coordinates to the ra_courses table
-- to enable location-based features and mapping functionality.
--
-- Columns to add:
-- • latitude (DECIMAL) - Course latitude in decimal degrees
-- • longitude (DECIMAL) - Course longitude in decimal degrees
--
-- Data source: DarkHorses-Course-Cordinates-Fetcher/ra_courses_final_validated.json
-- All coordinates are validated and precise (hyper-precise validation method)
--
-- Date: 2025-10-19
-- Related: scripts/update_course_coordinates.py

BEGIN;

-- ============================================================================
-- ADD COORDINATE COLUMNS
-- ============================================================================

-- Add latitude column (decimal degrees, range -90 to +90)
ALTER TABLE ra_courses
ADD COLUMN IF NOT EXISTS latitude DECIMAL(10, 8);

-- Add longitude column (decimal degrees, range -180 to +180)
ALTER TABLE ra_courses
ADD COLUMN IF NOT EXISTS longitude DECIMAL(11, 8);

-- ============================================================================
-- ADD COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON COLUMN ra_courses.latitude IS 'Course latitude in decimal degrees (WGS84)';
COMMENT ON COLUMN ra_courses.longitude IS 'Course longitude in decimal degrees (WGS84)';

-- ============================================================================
-- CREATE INDEX FOR GEOSPATIAL QUERIES
-- ============================================================================

-- Create composite index for efficient location-based queries
CREATE INDEX IF NOT EXISTS idx_ra_courses_coordinates
ON ra_courses(latitude, longitude)
WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

DO $$
BEGIN
    -- Check that columns were added
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_courses' AND column_name = 'latitude'
    ) THEN
        RAISE EXCEPTION 'latitude column was not added!';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_courses' AND column_name = 'longitude'
    ) THEN
        RAISE EXCEPTION 'longitude column was not added!';
    END IF;

    -- Check that index was created
    IF NOT EXISTS (
        SELECT 1 FROM pg_indexes
        WHERE tablename = 'ra_courses' AND indexname = 'idx_ra_courses_coordinates'
    ) THEN
        RAISE EXCEPTION 'idx_ra_courses_coordinates index was not created!';
    END IF;

    RAISE NOTICE '✅ Migration 021 complete: latitude and longitude columns added successfully';
    RAISE NOTICE 'Next step: Run scripts/update_course_coordinates.py to populate coordinates';
END $$;

COMMIT;

-- ============================================================================
-- POST-MIGRATION ACTIONS
-- ============================================================================

-- 1. Run the update script to populate coordinates:
--    python3 scripts/update_course_coordinates.py
--
-- 2. Verify coordinate population:
--    SELECT COUNT(*) as total_courses,
--           COUNT(latitude) as with_coordinates,
--           ROUND(COUNT(latitude)::numeric / COUNT(*)::numeric * 100, 2) as coverage_pct
--    FROM ra_courses;
--
-- 3. (Optional) Update courses_fetcher.py to capture coordinates from API if available
