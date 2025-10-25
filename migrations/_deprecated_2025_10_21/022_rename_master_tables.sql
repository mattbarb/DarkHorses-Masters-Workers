-- Migration 022: Rename master/reference tables to ra_mst_ prefix
-- Date: 2025-10-19
-- Purpose: Add ra_mst_ prefix to master/reference data tables
--   - ra_mst_* = Master/reference data (slow-changing)
--   - ra_* = Event/transaction data (fast-changing, no changes)
--   - ra_odds_* = Odds data (managed by other tool, no changes)

-- ============================================================================
-- RENAME MASTER TABLES (10 tables)
-- ============================================================================
-- PostgreSQL automatically updates foreign key references when renaming tables!

BEGIN;

-- People (3 tables)
ALTER TABLE ra_jockeys RENAME TO ra_mst_jockeys;
ALTER TABLE ra_trainers RENAME TO ra_mst_trainers;
ALTER TABLE ra_owners RENAME TO ra_mst_owners;

-- Horses (1 table)
ALTER TABLE ra_horses RENAME TO ra_mst_horses;

-- Pedigree (3 tables)
ALTER TABLE ra_sires RENAME TO ra_mst_sires;
ALTER TABLE ra_dams RENAME TO ra_mst_dams;
ALTER TABLE ra_damsires RENAME TO ra_mst_damsires;

-- Reference Data (3 tables)
ALTER TABLE ra_bookmakers RENAME TO ra_mst_bookmakers;
ALTER TABLE ra_courses RENAME TO ra_mst_courses;
ALTER TABLE ra_regions RENAME TO ra_mst_regions;

COMMIT;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Verify all tables renamed correctly
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size('public.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
  AND tablename LIKE 'ra_%'
  AND tablename NOT LIKE '%backup%'
ORDER BY tablename;

-- Expected output should show:
-- ra_mst_bookmakers
-- ra_mst_courses
-- ra_mst_dams
-- ra_mst_damsires
-- ra_mst_horses
-- ra_mst_jockeys
-- ra_mst_owners
-- ra_mst_regions
-- ra_mst_sires
-- ra_mst_trainers
-- (plus all other ra_* tables unchanged)

-- Verify foreign keys still work (check ra_runners)
SELECT
    tc.table_name AS from_table,
    kcu.column_name AS from_column,
    ccu.table_name AS to_table,
    ccu.column_name AS to_column
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
    AND tc.table_name = 'ra_runners'
ORDER BY kcu.column_name;

-- Expected: All foreign keys should now point to ra_mst_* tables

-- ============================================================================
-- ROLLBACK SCRIPT (If needed)
-- ============================================================================

-- UNCOMMENT BELOW TO ROLLBACK

-- BEGIN;
-- ALTER TABLE ra_mst_jockeys RENAME TO ra_jockeys;
-- ALTER TABLE ra_mst_trainers RENAME TO ra_trainers;
-- ALTER TABLE ra_mst_owners RENAME TO ra_owners;
-- ALTER TABLE ra_mst_horses RENAME TO ra_horses;
-- ALTER TABLE ra_mst_sires RENAME TO ra_sires;
-- ALTER TABLE ra_mst_dams RENAME TO ra_dams;
-- ALTER TABLE ra_mst_damsires RENAME TO ra_damsires;
-- ALTER TABLE ra_mst_bookmakers RENAME TO ra_bookmakers;
-- ALTER TABLE ra_mst_courses RENAME TO ra_courses;
-- ALTER TABLE ra_mst_regions RENAME TO ra_regions;
-- COMMIT;

-- ============================================================================
-- FINAL TABLE STRUCTURE
-- ============================================================================

/*
AFTER MIGRATION:

Masters (ra_mst_*) - 10 tables (RENAMED):
  ✅ ra_mst_bookmakers      (was ra_bookmakers)
  ✅ ra_mst_courses          (was ra_courses)
  ✅ ra_mst_dams             (was ra_dams)
  ✅ ra_mst_damsires         (was ra_damsires)
  ✅ ra_mst_horses           (was ra_horses)
  ✅ ra_mst_jockeys          (was ra_jockeys)
  ✅ ra_mst_owners           (was ra_owners)
  ✅ ra_mst_regions          (was ra_regions)
  ✅ ra_mst_sires            (was ra_sires)
  ✅ ra_mst_trainers         (was ra_trainers)

Events (ra_*) - NO CHANGES:
  ✅ ra_entity_combinations
  ✅ ra_horse_pedigree
  ✅ ra_performance_by_distance
  ✅ ra_performance_by_venue
  ✅ ra_race_results
  ✅ ra_races
  ✅ ra_runner_odds
  ✅ ra_runner_statistics
  ✅ ra_runner_supplementary
  ✅ ra_runners

Odds (ra_odds_*) - NO CHANGES (managed by other tool):
  ✅ ra_odds_historical
  ✅ ra_odds_live
  ✅ ra_odds_statistics
*/
