-- Migration: Drop unused tables (ra_results, om_weather_hourly_forecast)
-- Date: 2025-10-16
-- Reason: Both tables are unused by this codebase and have been superseded by other tables.

-- ============================================================================
-- TABLE 1: ra_results (0 records)
-- ============================================================================
-- Reason: Results data is stored in ra_runners table instead.
--
-- Background:
-- The Racing API /v1/results endpoint returns race records with embedded runner results.
-- Our architecture correctly stores:
--   - Race metadata → ra_races table
--   - Runner data (including position, distance_beaten, prize_won, starting_price) → ra_runners table
--
-- The ra_results table was planned but never implemented and serves no purpose.
-- See docs/RESULTS_DATA_ARCHITECTURE.md for full explanation.

DROP TABLE IF EXISTS ra_results;

-- ============================================================================
-- TABLE 2: om_weather_hourly_forecast (528 records, stale since Aug 2025)
-- ============================================================================
-- Reason: Deprecated OpenMeteo table replaced by dh_weather_* tables.
--
-- Background:
-- This was an early weather implementation using direct OpenMeteo data.
-- It has been replaced by the DarkHorses-Weather-Race-Worker system which uses:
--   - dh_weather_forecast (5,004 records, actively updated)
--   - dh_weather_history (113,036 records, actively updated)
--
-- Last updated: 2025-08-07 (2+ months stale)
-- No code in DarkHorses-Masters-Workers references this table.
-- The "om_" prefix indicates OpenMeteo, replaced by "dh_" (DarkHorses) naming convention.

DROP TABLE IF EXISTS om_weather_hourly_forecast;

-- ============================================================================
-- Summary
-- ============================================================================
-- Tables dropped: 2
-- Data loss: None (data exists in other tables or is stale/unused)
-- Code changes: insert_results() method deprecated in utils/supabase_client.py
