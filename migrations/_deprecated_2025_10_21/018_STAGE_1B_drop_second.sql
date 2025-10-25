ALTER TABLE ra_runners DROP COLUMN IF EXISTS apprentice_allowance;
NOTIFY pgrst, 'reload schema';
SELECT '✅ Dropped apprentice_allowance' as status;
