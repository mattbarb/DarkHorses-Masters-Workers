-- Migration 029: Make all historical result fields nullable in ra_runners
-- Date: 2025-10-23
-- Purpose: Historical results API doesn't always provide all pre-race fields
--          These fields are available in racecards but may be NULL when updating from results

-- Make all potentially missing result fields nullable
ALTER TABLE ra_runners
ALTER COLUMN draw DROP NOT NULL,
ALTER COLUMN weight_lbs DROP NOT NULL,
ALTER COLUMN jockey_name DROP NOT NULL,
ALTER COLUMN trainer_name DROP NOT NULL,
ALTER COLUMN owner_name DROP NOT NULL;

-- Add comments
COMMENT ON COLUMN ra_runners.draw IS 'Starting draw position - nullable in historical results, available in racecards';
COMMENT ON COLUMN ra_runners.weight_lbs IS 'Carried weight in lbs - nullable in historical results, available in racecards';
COMMENT ON COLUMN ra_runners.jockey_name IS 'Jockey name - nullable in results (can join via jockey_id to ra_mst_jockeys)';
COMMENT ON COLUMN ra_runners.trainer_name IS 'Trainer name - nullable in results (can join via trainer_id to ra_mst_trainers)';
COMMENT ON COLUMN ra_runners.owner_name IS 'Owner name - nullable in results (can join via owner_id to ra_mst_owners)';
