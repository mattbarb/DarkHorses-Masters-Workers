-- ============================================================================
-- Migration 018 - STAGE 4: Add Indexes
-- ============================================================================
-- Run after Stage 3
-- Adds indexes for performance on new columns
-- ============================================================================

BEGIN;

-- Simple indexes
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_age ON ra_runners(horse_age);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_sex_code ON ra_runners(horse_sex_code);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_region ON ra_runners(horse_region);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_dob ON ra_runners(horse_dob);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_colour ON ra_runners(horse_colour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_last_run_date ON ra_runners(last_run_date);

-- GIN indexes for JSONB columns
CREATE INDEX IF NOT EXISTS idx_ra_runners_trainer_14_days_gin ON ra_runners USING GIN (trainer_14_days);
CREATE INDEX IF NOT EXISTS idx_ra_runners_quotes_gin ON ra_runners USING GIN (quotes);
CREATE INDEX IF NOT EXISTS idx_ra_runners_stable_tour_gin ON ra_runners USING GIN (stable_tour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_medical_gin ON ra_runners USING GIN (medical);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_trainers_gin ON ra_runners USING GIN (prev_trainers);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_owners_gin ON ra_runners USING GIN (prev_owners);
CREATE INDEX IF NOT EXISTS idx_ra_runners_odds_gin ON ra_runners USING GIN (odds);

-- GIN index for array column
CREATE INDEX IF NOT EXISTS idx_ra_runners_past_results_flags_gin ON ra_runners USING GIN (past_results_flags);

-- Reload schema
NOTIFY pgrst, 'reload schema';

SELECT '✅ Stage 4 Complete: All indexes created' as status;
SELECT '🎉 Migration 018 FULLY COMPLETE!' as final_status;

COMMIT;
