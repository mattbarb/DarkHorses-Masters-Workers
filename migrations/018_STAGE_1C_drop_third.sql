ALTER TABLE ra_runners DROP COLUMN IF EXISTS overall_beaten_distance;
NOTIFY pgrst, 'reload schema';
SELECT '✅ Dropped overall_beaten_distance' as status;
