-- Migration 008: Add Missing Pedigree and Horse Fields
-- Date: 2025-10-14
-- Purpose: Add breeder field to ra_horse_pedigree and colour_code to ra_horses
-- Related: REMAINING_TABLES_AUDIT.md, API_CROSS_REFERENCE_ADDENDUM.md

-- ============================================================================
-- PART 1: Add breeder field to ra_horse_pedigree
-- ============================================================================

DO $$
BEGIN
    -- Check if breeder column exists
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'ra_horse_pedigree'
        AND column_name = 'breeder'
    ) THEN
        ALTER TABLE ra_horse_pedigree
        ADD COLUMN breeder VARCHAR(100);

        RAISE NOTICE 'Added breeder column to ra_horse_pedigree';
    ELSE
        RAISE NOTICE 'breeder column already exists in ra_horse_pedigree';
    END IF;
END $$;

-- Add index for breeder lookups (optional but recommended)
CREATE INDEX IF NOT EXISTS idx_ra_horse_pedigree_breeder
ON ra_horse_pedigree(breeder)
WHERE breeder IS NOT NULL;

COMMENT ON COLUMN ra_horse_pedigree.breeder IS 'Name of breeder who bred this horse (from Racing API HorsePro endpoint)';

-- ============================================================================
-- PART 2: Add colour_code field to ra_horses (if not exists)
-- ============================================================================

DO $$
BEGIN
    -- Check if colour_code column exists
    IF NOT EXISTS (
        SELECT 1
        FROM information_schema.columns
        WHERE table_name = 'ra_horses'
        AND column_name = 'colour_code'
    ) THEN
        ALTER TABLE ra_horses
        ADD COLUMN colour_code VARCHAR(10);

        RAISE NOTICE 'Added colour_code column to ra_horses';
    ELSE
        RAISE NOTICE 'colour_code column already exists in ra_horses';
    END IF;
END $$;

-- Add index for colour_code lookups (optional)
CREATE INDEX IF NOT EXISTS idx_ra_horses_colour_code
ON ra_horses(colour_code)
WHERE colour_code IS NOT NULL;

COMMENT ON COLUMN ra_horses.colour_code IS 'Colour code from Racing API (e.g., "B" for Bay, "CH" for Chestnut)';

-- ============================================================================
-- PART 3: Verify existing fields in ra_horses
-- ============================================================================

-- Verify that these fields already exist (they should from previous migrations)
DO $$
BEGIN
    -- Check dob
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_horses' AND column_name = 'dob'
    ) THEN
        ALTER TABLE ra_horses ADD COLUMN dob DATE;
        RAISE NOTICE 'Added dob column to ra_horses';
    END IF;

    -- Check sex_code
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_horses' AND column_name = 'sex_code'
    ) THEN
        ALTER TABLE ra_horses ADD COLUMN sex_code VARCHAR(1);
        RAISE NOTICE 'Added sex_code column to ra_horses';
    END IF;

    -- Check colour
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_horses' AND column_name = 'colour'
    ) THEN
        ALTER TABLE ra_horses ADD COLUMN colour VARCHAR(20);
        RAISE NOTICE 'Added colour column to ra_horses';
    END IF;

    -- Check region
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_name = 'ra_horses' AND column_name = 'region'
    ) THEN
        ALTER TABLE ra_horses ADD COLUMN region VARCHAR(10);
        RAISE NOTICE 'Added region column to ra_horses';
    END IF;
END $$;

-- ============================================================================
-- PART 4: Validation Queries
-- ============================================================================

-- Report current state
DO $$
DECLARE
    pedigree_count INTEGER;
    horses_with_dob INTEGER;
    horses_with_colour INTEGER;
    horses_with_breeder INTEGER;
BEGIN
    -- Count pedigree records
    SELECT COUNT(*) INTO pedigree_count FROM ra_horse_pedigree;

    -- Count horses with dob
    SELECT COUNT(*) INTO horses_with_dob FROM ra_horses WHERE dob IS NOT NULL;

    -- Count horses with colour
    SELECT COUNT(*) INTO horses_with_colour FROM ra_horses WHERE colour IS NOT NULL;

    -- Count pedigree records with breeder
    SELECT COUNT(*) INTO horses_with_breeder FROM ra_horse_pedigree WHERE breeder IS NOT NULL;

    RAISE NOTICE '============================================';
    RAISE NOTICE 'MIGRATION 008 VALIDATION';
    RAISE NOTICE '============================================';
    RAISE NOTICE 'Pedigree records: %', pedigree_count;
    RAISE NOTICE 'Horses with DOB: %', horses_with_dob;
    RAISE NOTICE 'Horses with colour: %', horses_with_colour;
    RAISE NOTICE 'Pedigree records with breeder: %', horses_with_breeder;
    RAISE NOTICE '============================================';

    IF pedigree_count = 0 THEN
        RAISE NOTICE 'NOTE: ra_horse_pedigree is empty. Run backfill script to populate.';
    END IF;

    IF horses_with_dob = 0 THEN
        RAISE NOTICE 'NOTE: No horses have DOB data. Run backfill script to populate.';
    END IF;
END $$;

-- ============================================================================
-- ROLLBACK (If Needed)
-- ============================================================================

-- To rollback this migration (NOT RECOMMENDED unless testing):
-- ALTER TABLE ra_horse_pedigree DROP COLUMN IF EXISTS breeder;
-- ALTER TABLE ra_horses DROP COLUMN IF EXISTS colour_code;
-- DROP INDEX IF EXISTS idx_ra_horse_pedigree_breeder;
-- DROP INDEX IF EXISTS idx_ra_horses_colour_code;

-- ============================================================================
-- NOTES
-- ============================================================================

/*
This migration adds support for capturing additional fields from the Racing API
HorsePro endpoint that were discovered during the comprehensive API audit.

Fields Added:
1. ra_horse_pedigree.breeder - Name of the breeder (NEW field discovered)
2. ra_horses.colour_code - Colour code in addition to colour string (NEW field)

Fields Verified (should already exist from previous migrations):
3. ra_horses.dob - Date of birth
4. ra_horses.sex_code - Sex code (G/C/F/M)
5. ra_horses.colour - Colour name (e.g., "Bay", "Chestnut")
6. ra_horses.region - Region code (e.g., "gb", "ire")

Next Steps:
1. Run this migration
2. Update horses_fetcher.py to capture these fields
3. Create and run backfill script (scripts/backfill_horse_pedigree.py)
4. Expected time: 15.5 hours (111,325 horses × 0.5s per API call)

API Endpoint Used:
- GET /v1/horses/{horse_id}/pro (Pro plan required)

Related Documents:
- docs/REMAINING_TABLES_AUDIT.md
- docs/API_CROSS_REFERENCE_ADDENDUM.md
- WORKER_FIXES_COMPLETED.md
*/
