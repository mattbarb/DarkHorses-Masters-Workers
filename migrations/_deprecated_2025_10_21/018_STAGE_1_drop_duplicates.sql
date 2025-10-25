-- ============================================================================
-- Migration 018 - STAGE 1: Drop Duplicate Columns
-- ============================================================================
-- Run this first, then Stage 2, then Stage 3
-- ============================================================================

BEGIN;

-- Drop duplicate columns (fast, won't timeout)
ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_claim;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS apprentice_allowance;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS overall_beaten_distance;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_post_rating;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;

-- Reload schema
NOTIFY pgrst, 'reload schema';

SELECT '✅ Stage 1 Complete: 5 duplicate columns dropped' as status;

COMMIT;
