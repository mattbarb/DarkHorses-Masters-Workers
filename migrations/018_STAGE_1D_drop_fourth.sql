ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_post_rating;
NOTIFY pgrst, 'reload schema';
SELECT '✅ Dropped racing_post_rating' as status;
