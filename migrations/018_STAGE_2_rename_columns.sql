-- ============================================================================
-- Migration 018 - STAGE 2: Rename Columns
-- ============================================================================
-- Run after Stage 1
-- ============================================================================

BEGIN;

-- Rename age -> horse_age
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ra_runners' AND column_name = 'age') THEN
        ALTER TABLE ra_runners RENAME COLUMN age TO horse_age;
        RAISE NOTICE 'Renamed age -> horse_age';
    ELSE
        RAISE NOTICE 'Column age does not exist, already renamed';
    END IF;
END $$;

-- Rename sex -> horse_sex
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'ra_runners' AND column_name = 'sex') THEN
        ALTER TABLE ra_runners RENAME COLUMN sex TO horse_sex;
        RAISE NOTICE 'Renamed sex -> horse_sex';
    ELSE
        RAISE NOTICE 'Column sex does not exist, already renamed';
    END IF;
END $$;

-- Reload schema
NOTIFY pgrst, 'reload schema';

SELECT '✅ Stage 2 Complete: 2 columns renamed' as status;

COMMIT;
