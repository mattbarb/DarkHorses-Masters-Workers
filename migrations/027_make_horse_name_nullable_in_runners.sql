-- Migration 027: Make horse_name nullable in ra_runners
-- Date: 2025-10-23
-- Purpose: Allow results updates when API doesn't return horse name (we have horse_id for joins)

-- Make horse_name nullable
ALTER TABLE ra_runners
ALTER COLUMN horse_name DROP NOT NULL;

-- Add comment explaining why
COMMENT ON COLUMN ra_runners.horse_name IS 'Horse name - nullable because we can join via horse_id to ra_mst_horses. May be NULL in historical results data.';
