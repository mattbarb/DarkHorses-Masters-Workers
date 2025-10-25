-- Migration: Add Enhanced Statistics Columns
-- Date: 2025-10-19
-- Purpose: Add recent form and "days since" statistics to jockeys, trainers, owners tables

-- ============================================================================
-- 1. ra_jockeys - Add 10 new columns
-- ============================================================================

ALTER TABLE ra_jockeys
ADD COLUMN IF NOT EXISTS last_ride_date DATE,
ADD COLUMN IF NOT EXISTS last_win_date DATE,
ADD COLUMN IF NOT EXISTS days_since_last_ride INTEGER,
ADD COLUMN IF NOT EXISTS days_since_last_win INTEGER,
ADD COLUMN IF NOT EXISTS recent_14d_rides INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_14d_wins INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_14d_win_rate NUMERIC(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS recent_30d_rides INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_30d_wins INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_30d_win_rate NUMERIC(5,2) DEFAULT 0.00;

COMMENT ON COLUMN ra_jockeys.last_ride_date IS 'Date of most recent ride';
COMMENT ON COLUMN ra_jockeys.last_win_date IS 'Date of most recent win';
COMMENT ON COLUMN ra_jockeys.days_since_last_ride IS 'Days since last ride (calculated from last_ride_date)';
COMMENT ON COLUMN ra_jockeys.days_since_last_win IS 'Days since last win (calculated from last_win_date)';
COMMENT ON COLUMN ra_jockeys.recent_14d_rides IS 'Number of rides in last 14 days';
COMMENT ON COLUMN ra_jockeys.recent_14d_wins IS 'Number of wins in last 14 days';
COMMENT ON COLUMN ra_jockeys.recent_14d_win_rate IS 'Win percentage in last 14 days';
COMMENT ON COLUMN ra_jockeys.recent_30d_rides IS 'Number of rides in last 30 days';
COMMENT ON COLUMN ra_jockeys.recent_30d_wins IS 'Number of wins in last 30 days';
COMMENT ON COLUMN ra_jockeys.recent_30d_win_rate IS 'Win percentage in last 30 days';

-- ============================================================================
-- 2. ra_trainers - Add 10 new columns (for consistency with jockeys and owners)
-- ============================================================================

ALTER TABLE ra_trainers
ADD COLUMN IF NOT EXISTS last_runner_date DATE,
ADD COLUMN IF NOT EXISTS last_win_date DATE,
ADD COLUMN IF NOT EXISTS days_since_last_runner INTEGER,
ADD COLUMN IF NOT EXISTS days_since_last_win INTEGER,
ADD COLUMN IF NOT EXISTS recent_14d_runs INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_14d_wins INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_14d_win_rate NUMERIC(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS recent_30d_runs INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_30d_wins INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_30d_win_rate NUMERIC(5,2) DEFAULT 0.00;

COMMENT ON COLUMN ra_trainers.last_runner_date IS 'Date of most recent runner';
COMMENT ON COLUMN ra_trainers.last_win_date IS 'Date of most recent win';
COMMENT ON COLUMN ra_trainers.days_since_last_runner IS 'Days since last runner (calculated from last_runner_date)';
COMMENT ON COLUMN ra_trainers.days_since_last_win IS 'Days since last win (calculated from last_win_date)';
COMMENT ON COLUMN ra_trainers.recent_14d_runs IS 'Number of runners in last 14 days';
COMMENT ON COLUMN ra_trainers.recent_14d_wins IS 'Number of wins in last 14 days';
COMMENT ON COLUMN ra_trainers.recent_14d_win_rate IS 'Win percentage in last 14 days';
COMMENT ON COLUMN ra_trainers.recent_30d_runs IS 'Number of runners in last 30 days';
COMMENT ON COLUMN ra_trainers.recent_30d_wins IS 'Number of wins in last 30 days';
COMMENT ON COLUMN ra_trainers.recent_30d_win_rate IS 'Win percentage in last 30 days';

-- ============================================================================
-- 3. ra_owners - Add 10 new columns
-- ============================================================================

ALTER TABLE ra_owners
ADD COLUMN IF NOT EXISTS last_runner_date DATE,
ADD COLUMN IF NOT EXISTS last_win_date DATE,
ADD COLUMN IF NOT EXISTS days_since_last_runner INTEGER,
ADD COLUMN IF NOT EXISTS days_since_last_win INTEGER,
ADD COLUMN IF NOT EXISTS recent_14d_runs INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_14d_wins INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_14d_win_rate NUMERIC(5,2) DEFAULT 0.00,
ADD COLUMN IF NOT EXISTS recent_30d_runs INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_30d_wins INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS recent_30d_win_rate NUMERIC(5,2) DEFAULT 0.00;

COMMENT ON COLUMN ra_owners.last_runner_date IS 'Date of most recent runner';
COMMENT ON COLUMN ra_owners.last_win_date IS 'Date of most recent win';
COMMENT ON COLUMN ra_owners.days_since_last_runner IS 'Days since last runner (calculated from last_runner_date)';
COMMENT ON COLUMN ra_owners.days_since_last_win IS 'Days since last win (calculated from last_win_date)';
COMMENT ON COLUMN ra_owners.recent_14d_runs IS 'Number of runners in last 14 days';
COMMENT ON COLUMN ra_owners.recent_14d_wins IS 'Number of wins in last 14 days';
COMMENT ON COLUMN ra_owners.recent_14d_win_rate IS 'Win percentage in last 14 days';
COMMENT ON COLUMN ra_owners.recent_30d_runs IS 'Number of runners in last 30 days';
COMMENT ON COLUMN ra_owners.recent_30d_wins IS 'Number of wins in last 30 days';
COMMENT ON COLUMN ra_owners.recent_30d_win_rate IS 'Win percentage in last 30 days';

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check new columns were added
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'ra_jockeys'
  AND column_name IN (
    'last_ride_date', 'last_win_date', 'days_since_last_ride', 'days_since_last_win',
    'recent_14d_rides', 'recent_14d_wins', 'recent_14d_win_rate',
    'recent_30d_rides', 'recent_30d_wins', 'recent_30d_win_rate'
  )
ORDER BY column_name;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'ra_trainers'
  AND column_name IN (
    'last_runner_date', 'last_win_date', 'days_since_last_runner', 'days_since_last_win',
    'recent_14d_runs', 'recent_14d_wins', 'recent_14d_win_rate',
    'recent_30d_runs', 'recent_30d_wins', 'recent_30d_win_rate'
  )
ORDER BY column_name;

SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'ra_owners'
  AND column_name IN (
    'last_runner_date', 'last_win_date', 'days_since_last_runner', 'days_since_last_win',
    'recent_14d_runs', 'recent_14d_wins', 'recent_14d_win_rate',
    'recent_30d_runs', 'recent_30d_wins', 'recent_30d_win_rate'
  )
ORDER BY column_name;

-- ============================================================================
-- Summary
-- ============================================================================

/*
COLUMNS ADDED (CONSISTENT ACROSS ALL 3 TABLES):

ra_jockeys: 10 new columns
  - last_ride_date, last_win_date
  - days_since_last_ride, days_since_last_win
  - recent_14d_rides, recent_14d_wins, recent_14d_win_rate
  - recent_30d_rides, recent_30d_wins, recent_30d_win_rate

ra_trainers: 10 new columns (CONSISTENT with jockeys/owners)
  - last_runner_date, last_win_date
  - days_since_last_runner, days_since_last_win
  - recent_14d_runs, recent_14d_wins, recent_14d_win_rate
  - recent_30d_runs, recent_30d_wins, recent_30d_win_rate

ra_owners: 10 new columns (CONSISTENT with jockeys/trainers)
  - last_runner_date, last_win_date
  - days_since_last_runner, days_since_last_win
  - recent_14d_runs, recent_14d_wins, recent_14d_win_rate
  - recent_30d_runs, recent_30d_wins, recent_30d_win_rate

TOTAL: 30 new columns across 3 tables (10 per table for consistency)

All columns are nullable and will be populated by statistics workers.
*/
