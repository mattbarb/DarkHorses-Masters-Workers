-- ============================================================================
-- Migration 027: Drop ra_runner_odds Table
-- ============================================================================
-- Date: 2025-10-22
-- Reason: Table is redundant with existing ra_odds_live and ra_odds_historical tables
--
-- Background:
-- The ra_runner_odds table was designed as an aggregated/cached view of odds data,
-- combining data from ra_odds_live (224K records) and ra_odds_historical (2.4M records).
-- However:
-- 1. The table has remained empty (0 records) in production
-- 2. The populate script (populate_runner_odds.py) is missing from the codebase
-- 3. All population attempts fail with 100% error rate
-- 4. Raw odds data is already available in two comprehensive tables
-- 5. Modern database queries can aggregate odds data on-demand efficiently
--
-- Impact:
-- - No data loss (table is empty)
-- - Removes maintenance burden of a calculated table that never worked
-- - Simplifies the calculated tables architecture (Phase 1 now has only 1 table)
-- - Queries should use ra_odds_live and ra_odds_historical directly
--
-- Code Cleanup Required:
-- - Remove from scripts/populate_all_calculated_tables.py
-- - Remove from fetchers/populate_all_calculated_tables.py
-- - Update fetchers/schedules/calculated_tables_schedule.yaml
-- - Update docs/CALCULATED_TABLES_IMPLEMENTATION.md
-- ============================================================================

-- Verify table is empty before dropping (safety check)
DO $$
DECLARE
    record_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO record_count FROM ra_runner_odds;

    IF record_count > 0 THEN
        RAISE NOTICE 'WARNING: ra_runner_odds contains % records', record_count;
        RAISE NOTICE 'Migration aborted - table is not empty!';
        RAISE EXCEPTION 'Cannot drop non-empty table ra_runner_odds';
    ELSE
        RAISE NOTICE 'Table ra_runner_odds is empty (% records), safe to drop', record_count;
    END IF;
END $$;

-- Drop the table
DROP TABLE IF EXISTS ra_runner_odds CASCADE;

-- Add comment documenting the removal
COMMENT ON SCHEMA public IS
'ra_runner_odds table removed 2025-10-22 - use ra_odds_live and ra_odds_historical instead';

-- ============================================================================
-- VERIFICATION
-- ============================================================================
-- After running this migration, verify:
--
-- 1. Table is gone:
-- SELECT table_name FROM information_schema.tables
-- WHERE table_name = 'ra_runner_odds';
-- (should return 0 rows)
--
-- 2. Odds data is still available:
-- SELECT COUNT(*) FROM ra_odds_live;      -- Should show ~224K records
-- SELECT COUNT(*) FROM ra_odds_historical; -- Should show ~2.4M records
--
-- 3. Check for any dependent views or functions:
-- SELECT dependent_ns.nspname AS schema, dependent_view.relname AS name
-- FROM pg_depend
-- JOIN pg_rewrite ON pg_depend.objid = pg_rewrite.oid
-- JOIN pg_class AS dependent_view ON pg_rewrite.ev_class = dependent_view.oid
-- JOIN pg_namespace dependent_ns ON dependent_ns.oid = dependent_view.relnamespace
-- WHERE pg_depend.refobjid = 'ra_runner_odds'::regclass;
-- (should return 0 rows after CASCADE drop)
-- ============================================================================

-- ============================================================================
-- ALTERNATIVE QUERIES FOR ODDS DATA
-- ============================================================================
-- Instead of ra_runner_odds, use these queries:
--
-- Get latest odds for a runner:
-- SELECT * FROM ra_odds_live
-- WHERE race_id = 'rac_XXXXX' AND horse_id = 'hrs_XXXXX'
-- ORDER BY odds_updated_at DESC LIMIT 1;
--
-- Get all bookmaker odds for a race:
-- SELECT horse_id, horse_name, bookmaker_id, decimal_odds, fractional_odds
-- FROM ra_odds_live
-- WHERE race_id = 'rac_XXXXX'
-- ORDER BY horse_name, bookmaker_id;
--
-- Get historical SP (starting price) data:
-- SELECT horse_name, decimal_final_odds, fractional_final_odds
-- FROM ra_odds_historical
-- WHERE date_of_race = '2025-10-21' AND track = 'Newcastle'
-- ORDER BY race_time, horse_name;
-- ============================================================================
