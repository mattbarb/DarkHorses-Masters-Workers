-- Drop columns ONE AT A TIME to avoid timeout
-- Run this first

ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_claim;
NOTIFY pgrst, 'reload schema';
SELECT '✅ Dropped jockey_claim' as status;
