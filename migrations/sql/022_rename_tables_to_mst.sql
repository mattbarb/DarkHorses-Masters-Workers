-- Migration 022: Rename tables to ra_mst_ prefix for master/reference data
-- Date: 2025-10-19
-- Purpose: Reorganize database with clear naming convention
--   - ra_mst_* = Master/reference data (slow-changing)
--   - ra_* = Event/transaction data (fast-changing)
--   - ra_analytics_* = Derived analytics
--   - ra_rel_* = Relationship tables

-- ============================================================================
-- PART 1: RENAME MASTER TABLES
-- ============================================================================

-- Master/Reference Data (10 tables)
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
-- PART 2: RENAME ANALYTICS TABLES
-- ============================================================================

BEGIN;

ALTER TABLE ra_entity_combinations RENAME TO ra_analytics_combinations;
ALTER TABLE ra_performance_by_distance RENAME TO ra_analytics_by_distance;
ALTER TABLE ra_performance_by_venue RENAME TO ra_analytics_by_venue;

COMMIT;

-- ============================================================================
-- PART 3: RENAME RELATIONSHIP TABLES
-- ============================================================================

BEGIN;

ALTER TABLE ra_horse_pedigree RENAME TO ra_rel_pedigree;

COMMIT;

-- ============================================================================
-- PART 4: RENAME SUPPLEMENTARY TABLES
-- ============================================================================

BEGIN;

ALTER TABLE ra_runner_supplementary RENAME TO ra_sup_runner;

COMMIT;

-- ============================================================================
-- PART 5: VERIFICATION QUERIES
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

-- Verify foreign keys still work (check ra_runners)
SELECT
    tc.table_name AS from_table,
    kcu.column_name AS from_column,
    ccu.table_name AS to_table,
    ccu.column_name AS to_column,
    tc.constraint_name
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
ORDER BY tc.constraint_name;

-- ============================================================================
-- ROLLBACK SCRIPT (If needed)
-- ============================================================================

-- UNCOMMENT BELOW TO ROLLBACK

-- BEGIN;

-- -- Rollback master tables
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

-- -- Rollback analytics tables
-- ALTER TABLE ra_analytics_combinations RENAME TO ra_entity_combinations;
-- ALTER TABLE ra_analytics_by_distance RENAME TO ra_performance_by_distance;
-- ALTER TABLE ra_analytics_by_venue RENAME TO ra_performance_by_venue;

-- -- Rollback relationship tables
-- ALTER TABLE ra_rel_pedigree RENAME TO ra_horse_pedigree;

-- -- Rollback supplementary tables
-- ALTER TABLE ra_sup_runner RENAME TO ra_runner_supplementary;

-- COMMIT;

-- ============================================================================
-- FINAL TABLE STRUCTURE
-- ============================================================================

/*
AFTER MIGRATION:

Masters (ra_mst_*) - 10 tables:
  - ra_mst_bookmakers
  - ra_mst_courses
  - ra_mst_dams
  - ra_mst_damsires
  - ra_mst_horses
  - ra_mst_jockeys
  - ra_mst_owners
  - ra_mst_regions
  - ra_mst_sires
  - ra_mst_trainers

Events (ra_*) - 5 tables:
  - ra_races
  - ra_runners
  - ra_runner_odds
  - ra_runner_statistics
  - ra_race_results (DEPRECATED - consider dropping)

Analytics (ra_analytics_*) - 3 tables:
  - ra_analytics_combinations
  - ra_analytics_by_distance
  - ra_analytics_by_venue

Relationships (ra_rel_*) - 1 table:
  - ra_rel_pedigree

Supplementary (ra_sup_*) - 1 table:
  - ra_sup_runner

Odds (ra_odds_*) - 3 tables (NO CHANGES):
  - ra_odds_historical
  - ra_odds_live
  - ra_odds_statistics
*/
