-- Migration 026: Populate Pedigree Names from ra_horse_pedigree
-- Date: 2025-10-20
-- Purpose: Copy sire/dam/damsire names from ra_horse_pedigree to ra_mst_sires/dams/damsires tables
--          This fills the missing name data for 48,366 dams and 3,040 damsires

BEGIN;

-- ====================================================================================
-- STEP 1: Populate ra_mst_sires names (if any are missing)
-- ====================================================================================

INSERT INTO ra_mst_sires (id, name, created_at, updated_at)
SELECT DISTINCT
    p.sire_id,
    p.sire,
    NOW(),
    NOW()
FROM ra_horse_pedigree p
WHERE p.sire_id IS NOT NULL
  AND p.sire IS NOT NULL
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    updated_at = NOW()
WHERE ra_mst_sires.name IS NULL OR ra_mst_sires.name = '';

-- ====================================================================================
-- STEP 2: Populate ra_mst_dams names (CRITICAL - 48,366 missing names)
-- ====================================================================================

INSERT INTO ra_mst_dams (id, name, created_at, updated_at)
SELECT DISTINCT
    p.dam_id,
    p.dam,
    NOW(),
    NOW()
FROM ra_horse_pedigree p
WHERE p.dam_id IS NOT NULL
  AND p.dam IS NOT NULL
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    updated_at = NOW()
WHERE ra_mst_dams.name IS NULL OR ra_mst_dams.name = '';

-- ====================================================================================
-- STEP 3: Populate ra_mst_damsires names (CRITICAL - 3,040 missing names)
-- ====================================================================================

INSERT INTO ra_mst_damsires (id, name, created_at, updated_at)
SELECT DISTINCT
    p.damsire_id,
    p.damsire,
    NOW(),
    NOW()
FROM ra_horse_pedigree p
WHERE p.damsire_id IS NOT NULL
  AND p.damsire IS NOT NULL
ON CONFLICT (id) DO UPDATE
SET
    name = EXCLUDED.name,
    updated_at = NOW()
WHERE ra_mst_damsires.name IS NULL OR ra_mst_damsires.name = '';

COMMIT;

-- ====================================================================================
-- VERIFICATION QUERIES
-- ====================================================================================

-- Verify sires
SELECT
    'Sires' as entity,
    COUNT(*) as total,
    COUNT(name) FILTER (WHERE name IS NOT NULL AND name != '') as with_names,
    ROUND(COUNT(name) FILTER (WHERE name IS NOT NULL AND name != '')::numeric / COUNT(*)::numeric * 100, 2) as name_coverage_pct
FROM ra_mst_sires

UNION ALL

-- Verify dams
SELECT
    'Dams' as entity,
    COUNT(*) as total,
    COUNT(name) FILTER (WHERE name IS NOT NULL AND name != '') as with_names,
    ROUND(COUNT(name) FILTER (WHERE name IS NOT NULL AND name != '')::numeric / COUNT(*)::numeric * 100, 2) as name_coverage_pct
FROM ra_mst_dams

UNION ALL

-- Verify damsires
SELECT
    'Damsires' as entity,
    COUNT(*) as total,
    COUNT(name) FILTER (WHERE name IS NOT NULL AND name != '') as with_names,
    ROUND(COUNT(name) FILTER (WHERE name IS NOT NULL AND name != '')::numeric / COUNT(*)::numeric * 100, 2) as name_coverage_pct
FROM ra_mst_damsires

ORDER BY entity;
