-- Migration 028: Make number (saddle cloth) nullable in ra_runners
-- Date: 2025-10-23
-- Purpose: Allow results updates when API doesn't return saddle cloth number for historical races

-- Make number nullable
ALTER TABLE ra_runners
ALTER COLUMN number DROP NOT NULL;

-- Add comment explaining why
COMMENT ON COLUMN ra_runners.number IS 'Saddle cloth number - nullable because not always available in historical race results.';
