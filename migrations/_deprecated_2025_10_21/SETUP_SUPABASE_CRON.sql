-- ============================================================================
-- SUPABASE CRON JOB SETUP - Entity Statistics Auto-Update
-- ============================================================================
-- Run this in Supabase SQL Editor to set up automatic daily statistics updates
-- Requires: Supabase Pro plan (includes pg_cron extension)
-- ============================================================================

-- Step 1: Enable the pg_cron extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Step 2: Create the cron job
-- This will run daily at 3:00 AM UTC
-- Adjust the time to match your needs (uses cron syntax: minute hour day month weekday)
SELECT cron.schedule(
    'update-entity-statistics-daily',  -- Job name
    '0 3 * * *',                        -- Schedule: 3:00 AM UTC every day
    $$ SELECT * FROM update_entity_statistics(); $$  -- SQL to execute
);

-- ============================================================================
-- CRON SCHEDULE EXAMPLES (if you want different timing):
-- ============================================================================
-- '0 2 * * *'     = 2:00 AM daily
-- '0 3 * * *'     = 3:00 AM daily (recommended - after nightly data loads)
-- '0 */6 * * *'   = Every 6 hours
-- '0 0 * * 0'     = Midnight every Sunday
-- '30 1 * * *'    = 1:30 AM daily
-- ============================================================================

-- Step 3: Verify the cron job was created
SELECT jobid, schedule, command, nodename, active
FROM cron.job
WHERE jobname = 'update-entity-statistics-daily';

-- ============================================================================
-- EXPECTED OUTPUT:
-- You should see your cron job listed with active = true
-- ============================================================================

-- ============================================================================
-- MANAGEMENT COMMANDS (for future reference)
-- ============================================================================

-- View all cron jobs:
-- SELECT * FROM cron.job;

-- Manually trigger the job now (for testing):
-- SELECT cron.schedule_in_database('update-entity-statistics-daily', '1 second', $$ SELECT * FROM update_entity_statistics(); $$, 'postgres');

-- Unschedule/delete a job:
-- SELECT cron.unschedule('update-entity-statistics-daily');

-- View job run history:
-- SELECT * FROM cron.job_run_details WHERE jobid = (SELECT jobid FROM cron.job WHERE jobname = 'update-entity-statistics-daily') ORDER BY start_time DESC LIMIT 10;

-- ============================================================================
-- INITIAL RUN (run statistics NOW before waiting for cron)
-- ============================================================================

-- Run this once now to populate initial statistics:
SET statement_timeout = '300s';
SELECT * FROM update_entity_statistics();
RESET statement_timeout;

-- ============================================================================
-- SETUP COMPLETE!
-- ============================================================================
-- The cron job will now run automatically every day at 3:00 AM UTC
-- Statistics will be updated for all jockeys, trainers, and owners
-- No manual intervention required
-- ============================================================================
