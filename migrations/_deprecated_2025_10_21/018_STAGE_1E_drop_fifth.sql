ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;
NOTIFY pgrst, 'reload schema';
SELECT '✅ Dropped race_comment - All duplicates removed!' as status;
