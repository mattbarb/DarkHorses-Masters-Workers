-- ============================================================================
-- RUN THIS IN SUPABASE SQL EDITOR TO UPDATE ALL ENTITY STATISTICS
-- ============================================================================
-- This will calculate jockey/trainer/owner statistics from race results
-- May take 30-90 seconds depending on data volume
-- ============================================================================

-- Increase timeout for this query
SET statement_timeout = '300s';

-- Run the statistics update function
SELECT * FROM update_entity_statistics();

-- Reset timeout
RESET statement_timeout;

-- ============================================================================
-- EXPECTED RESULT:
-- Should return a single row showing counts of entities updated:
--   jockeys_updated | trainers_updated | owners_updated
--   1000           | 1200             | 2500
-- ============================================================================
