-- Migration: Add region column to ra_horse_pedigree
-- Date: 2025-10-15
-- Reason: Denormalize region for better ML query performance

-- Step 1: Add region column
ALTER TABLE ra_horse_pedigree
ADD COLUMN IF NOT EXISTS region VARCHAR(10);

-- Step 2: Backfill region from ra_horses for existing records
UPDATE ra_horse_pedigree p
SET region = h.region
FROM ra_horses h
WHERE p.horse_id = h.horse_id
  AND p.region IS NULL;

-- Step 3: Add index on region for better query performance
CREATE INDEX IF NOT EXISTS idx_horse_pedigree_region ON ra_horse_pedigree(region);

-- Step 4: Verify the update (run this separately to see results)
SELECT
    COUNT(*) as total_records,
    COUNT(region) as records_with_region,
    COUNT(*) - COUNT(region) as null_region_count,
    ROUND(100.0 * COUNT(region) / COUNT(*), 1) as percentage_populated
FROM ra_horse_pedigree;
