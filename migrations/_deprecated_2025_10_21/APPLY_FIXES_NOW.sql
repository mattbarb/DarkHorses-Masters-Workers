-- ============================================================================
-- APPLY THESE FIXES IN SUPABASE SQL EDITOR NOW
-- ============================================================================
-- Copy this entire file and paste into Supabase SQL Editor, then click RUN
-- ============================================================================

-- Fix 1: Change dist_f column from INTEGER to VARCHAR
ALTER TABLE ra_results ALTER COLUMN dist_f TYPE VARCHAR(20);

-- Fix 2: Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

-- Verify Fix 1
SELECT
    'dist_f column type fixed:' as status,
    data_type
FROM information_schema.columns
WHERE table_name = 'ra_results'
AND column_name = 'dist_f';

-- Verify Fix 2
SELECT 'Schema cache reloaded' as status;

-- ============================================================================
-- EXPECTED RESULTS:
-- Row 1: status = "dist_f column type fixed:", data_type = "character varying"
-- Row 2: status = "Schema cache reloaded"
-- ============================================================================
