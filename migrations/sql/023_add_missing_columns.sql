-- Migration 023: Add missing columns identified during backfill
-- Date: 2025-10-20
-- Purpose: Add columns that code expects but don't exist in database

BEGIN;

-- Add trainer_location to ra_runners
-- This column stores the trainer's location/region
ALTER TABLE ra_runners
ADD COLUMN IF NOT EXISTS trainer_location CHARACTER VARYING;

-- Add 'time' column to ra_races as alias/copy of off_time
-- The code expects 'time' but database has 'off_time'
-- We'll add 'time' and keep both for compatibility
ALTER TABLE ra_races
ADD COLUMN IF NOT EXISTS time TIME WITHOUT TIME ZONE;

-- Copy existing off_time data to time column (if any exists)
UPDATE ra_races
SET time = off_time
WHERE time IS NULL AND off_time IS NOT NULL;

COMMIT;

-- Verification
SELECT 'trainer_location added to ra_runners' as status,
       EXISTS(
           SELECT 1 FROM information_schema.columns
           WHERE table_name = 'ra_runners'
           AND column_name = 'trainer_location'
       ) as column_exists;

SELECT 'time added to ra_races' as status,
       EXISTS(
           SELECT 1 FROM information_schema.columns
           WHERE table_name = 'ra_races'
           AND column_name = 'time'
       ) as column_exists;
