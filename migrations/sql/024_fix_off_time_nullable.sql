-- Migration 024: Fix off_time column to allow NULL values
-- Date: 2025-10-20
-- Purpose: Some races don't have off_time data yet (future races), so column needs to be nullable

BEGIN;

-- Make off_time nullable
ALTER TABLE ra_races
ALTER COLUMN off_time DROP NOT NULL;

COMMIT;

-- Verification
SELECT
    'off_time now nullable' as status,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_races'
  AND column_name = 'off_time';
