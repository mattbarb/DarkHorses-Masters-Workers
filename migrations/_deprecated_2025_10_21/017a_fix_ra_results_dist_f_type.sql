-- ============================================================================
-- Migration 017a: Fix ra_results dist_f Column Type
-- ============================================================================
-- Changes dist_f from INTEGER to VARCHAR to handle values like "8f", "11f"
-- ============================================================================

-- Modify dist_f column to VARCHAR
ALTER TABLE ra_results
ALTER COLUMN dist_f TYPE VARCHAR(20);

-- Verify the change
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_results'
AND column_name = 'dist_f';

-- Expected result: dist_f | character varying
