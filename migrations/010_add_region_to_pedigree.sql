-- Migration: Add region column to ra_horse_pedigree
-- Date: 2025-10-15
-- Reason: Denormalize region for better ML query performance

-- Add region column to ra_horse_pedigree
ALTER TABLE ra_horse_pedigree
ADD COLUMN IF NOT EXISTS region VARCHAR(10);

-- Backfill region from ra_horses for existing records
UPDATE ra_horse_pedigree p
SET region = h.region
FROM ra_horses h
WHERE p.horse_id = h.horse_id
  AND p.region IS NULL;

-- Add index on region for better query performance
CREATE INDEX IF NOT EXISTS idx_horse_pedigree_region ON ra_horse_pedigree(region);

-- Verify the update
DO $$
DECLARE
    total_records INTEGER;
    records_with_region INTEGER;
    null_region_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO total_records FROM ra_horse_pedigree;
    SELECT COUNT(*) INTO records_with_region FROM ra_horse_pedigree WHERE region IS NOT NULL;
    SELECT COUNT(*) INTO null_region_count FROM ra_horse_pedigree WHERE region IS NULL;

    RAISE NOTICE 'Migration complete:';
    RAISE NOTICE '  Total pedigree records: %', total_records;
    RAISE NOTICE '  Records with region: % (%.1f%%)', records_with_region,
                 CASE WHEN total_records > 0 THEN (records_with_region::float / total_records * 100) ELSE 0 END;
    RAISE NOTICE '  Records with NULL region: % (%.1f%%)', null_region_count,
                 CASE WHEN total_records > 0 THEN (null_region_count::float / total_records * 100) ELSE 0 END;
END $$;
