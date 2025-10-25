-- Migration 028: Drop ra_runner_supplementary table
-- Date: 2025-10-22
-- Reason: Redundant table with unclear purpose and 0 records
-- Impact: None - table never populated
-- Related: RA_RUNNER_SUPPLEMENTARY_REMOVAL_SUMMARY.md

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Check current state
SELECT
    'ra_runner_supplementary' as table_name,
    COUNT(*) as record_count
FROM ra_runner_supplementary;

-- Expected: 0 records (table never populated)

-- ============================================================================
-- DROP TABLE
-- ============================================================================

-- Drop table (CASCADE to handle any dependencies)
DROP TABLE IF EXISTS ra_runner_supplementary CASCADE;

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- Verify table no longer exists
SELECT
    table_name,
    table_type
FROM information_schema.tables
WHERE table_name = 'ra_runner_supplementary';

-- Expected: 0 rows (table dropped)

-- ============================================================================
-- NOTES
-- ============================================================================

-- RATIONALE:
-- 1. Table has 0 records in production
-- 2. No populate script exists
-- 3. Purpose was never clearly defined
-- 4. ra_runners table (57 columns) already captures all runner data
-- 5. Adding ~16 supplementary columns to ra_runners would be more efficient than separate table

-- REPLACEMENT:
-- If additional runner fields are needed in the future:
-- - Add columns directly to ra_runners table
-- - OR create specific analytical tables (ra_runner_statistics, etc.)

-- IMPACT:
-- - None - table was empty and never used
-- - Simplifies schema
-- - Reduces maintenance burden

-- ROLLBACK (if needed):
-- To recreate the table, check migration history or schema backups
-- Note: Since table was never populated, rollback is not recommended

-- ============================================================================
-- RELATED DOCUMENTATION
-- ============================================================================

-- See: RA_RUNNER_SUPPLEMENTARY_REMOVAL_SUMMARY.md
-- See: FETCHER_AUDIT_REPORT.md (Section on unpopulated tables)
