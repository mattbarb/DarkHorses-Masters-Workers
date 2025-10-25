-- Migration 025: Denormalize Pedigree IDs from ra_horse_pedigree to ra_mst_horses
-- Date: 2025-10-20
-- Purpose: Copy pedigree IDs (sire_id, dam_id, damsire_id) from ra_horse_pedigree to ra_mst_horses
--          This eliminates the need for joins when querying horse pedigree data.
--          CRITICAL for query performance and ML feature generation.

BEGIN;

-- Update ra_mst_horses with pedigree IDs from ra_horse_pedigree
UPDATE ra_mst_horses h
SET
    sire_id = p.sire_id,
    dam_id = p.dam_id,
    damsire_id = p.damsire_id,
    updated_at = NOW()
FROM ra_horse_pedigree p
WHERE h.id = p.horse_id
  AND (h.sire_id IS NULL OR h.dam_id IS NULL OR h.damsire_id IS NULL);

COMMIT;

-- Verification
SELECT
    'Pedigree IDs denormalized' as status,
    COUNT(*) as total_horses,
    COUNT(sire_id) as horses_with_sire,
    COUNT(dam_id) as horses_with_dam,
    COUNT(damsire_id) as horses_with_damsire,
    ROUND(COUNT(sire_id)::numeric / COUNT(*)::numeric * 100, 2) as sire_coverage_pct,
    ROUND(COUNT(dam_id)::numeric / COUNT(*)::numeric * 100, 2) as dam_coverage_pct
FROM ra_mst_horses;
