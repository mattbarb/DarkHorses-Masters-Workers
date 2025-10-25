-- Migration: Remove redundant active_last_30d field from ra_owners
-- Date: 2025-10-19
-- Reason: Redundant with recent_30d_runs (can derive: recent_30d_runs > 0)
-- Impact: Simplifies schema, removes maintenance overhead

-- ============================================================================
-- STEP 1: Verify Data Consistency
-- ============================================================================

-- Check for inconsistencies between active_last_30d and recent_30d_runs
DO $$
DECLARE
  total_owners INTEGER;
  inconsistent_count INTEGER;
  null_count INTEGER;
BEGIN
  -- Get total count
  SELECT COUNT(*) INTO total_owners
  FROM ra_owners
  WHERE id NOT LIKE '**TEST**%';

  -- Check for inconsistencies
  SELECT COUNT(*) INTO inconsistent_count
  FROM ra_owners
  WHERE id NOT LIKE '**TEST**%'
    AND ((active_last_30d = true AND recent_30d_runs = 0)
      OR (active_last_30d = false AND recent_30d_runs > 0));

  -- Check for NULL values
  SELECT COUNT(*) INTO null_count
  FROM ra_owners
  WHERE id NOT LIKE '**TEST**%'
    AND active_last_30d IS NULL;

  RAISE NOTICE 'Total owners: %', total_owners;
  RAISE NOTICE 'Inconsistent records: %', inconsistent_count;
  RAISE NOTICE 'NULL active_last_30d: %', null_count;

  IF inconsistent_count > 0 THEN
    RAISE NOTICE 'WARNING: Found % inconsistent records (% of total)',
      inconsistent_count,
      ROUND((inconsistent_count::numeric / total_owners::numeric) * 100, 2);
    RAISE NOTICE 'These will be corrected by dropping the redundant field';
  ELSE
    RAISE NOTICE 'SUCCESS: Data is consistent - safe to drop column';
  END IF;
END $$;

-- Show sample inconsistencies (if any)
SELECT
  id,
  name,
  active_last_30d,
  recent_30d_runs,
  CASE
    WHEN active_last_30d = true AND recent_30d_runs = 0 THEN 'Active=true but no runs'
    WHEN active_last_30d = false AND recent_30d_runs > 0 THEN 'Active=false but has runs'
    ELSE 'Consistent'
  END as issue
FROM ra_owners
WHERE id NOT LIKE '**TEST**%'
  AND ((active_last_30d = true AND recent_30d_runs = 0)
    OR (active_last_30d = false AND recent_30d_runs > 0))
LIMIT 5;

-- ============================================================================
-- STEP 2: Drop the Redundant Column
-- ============================================================================

ALTER TABLE ra_owners DROP COLUMN IF EXISTS active_last_30d;

-- ============================================================================
-- STEP 3: Verify Column Removed
-- ============================================================================

-- This should return 0 rows
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_owners'
  AND column_name = 'active_last_30d';

-- ============================================================================
-- STEP 4: Update Table Comment
-- ============================================================================

COMMENT ON TABLE ra_owners IS
  'Horse racing owners reference data.
   Active status can be derived from recent_30d_runs > 0.
   Migration applied: 2025-10-19 - Removed redundant active_last_30d field';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify column is gone
\d ra_owners

-- Show current schema
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'ra_owners'
ORDER BY ordinal_position;

-- ============================================================================
-- USAGE EXAMPLES (for code updates)
-- ============================================================================

/*
BEFORE (Old code using active_last_30d):
-----------------------------------------------
SELECT * FROM ra_owners WHERE active_last_30d = true;


AFTER (New code using recent_30d_runs):
-----------------------------------------------
SELECT * FROM ra_owners WHERE recent_30d_runs > 0;


BENEFITS:
-----------------------------------------------
1. Eliminates redundant data
2. Removes synchronization overhead
3. Removes risk of data inconsistency
4. Standardizes with jockeys/trainers tables
5. Simplifies schema maintenance
*/

-- ============================================================================
-- ROLLBACK PLAN (if needed)
-- ============================================================================

/*
If you need to rollback this migration:

ALTER TABLE ra_owners ADD COLUMN active_last_30d BOOLEAN;

-- Populate based on recent_30d_runs
UPDATE ra_owners
SET active_last_30d = (recent_30d_runs > 0);

-- Verify
SELECT
  COUNT(CASE WHEN active_last_30d = true THEN 1 END) as active_count,
  COUNT(CASE WHEN recent_30d_runs > 0 THEN 1 END) as runs_count
FROM ra_owners;
*/
