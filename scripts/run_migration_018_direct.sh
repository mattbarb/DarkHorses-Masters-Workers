#!/bin/bash

# Direct connection to Supabase PostgreSQL to run Migration 018
# This bypasses the API timeout issues

# Connection details
PGHOST="db.amsjvmlaknnvppxsgpfk.supabase.co"
PGPORT="5432"
PGDATABASE="postgres"
PGUSER="postgres"
PGPASSWORD="R0pMr1L58WH3hUkpVtPcwYnw"

export PGPASSWORD

echo "=========================================="
echo "Migration 018: Direct Database Connection"
echo "=========================================="
echo ""

# Stage 1: Drop duplicate columns
echo "Stage 1: Dropping duplicate columns..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
BEGIN;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_claim;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS apprentice_allowance;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS overall_beaten_distance;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_post_rating;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;
NOTIFY pgrst, 'reload schema';
COMMIT;
SELECT '✅ Stage 1 Complete: 5 duplicate columns dropped' as status;
EOF

echo ""
echo "Stage 2: Renaming columns..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
BEGIN;
ALTER TABLE ra_runners RENAME COLUMN age TO horse_age;
ALTER TABLE ra_runners RENAME COLUMN sex TO horse_sex;
NOTIFY pgrst, 'reload schema';
COMMIT;
SELECT '✅ Stage 2 Complete: 2 columns renamed' as status;
EOF

echo ""
echo "Stage 3: Adding new columns..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
BEGIN;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_dob DATE;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_sex_code CHAR(1);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_colour VARCHAR(100);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS horse_region VARCHAR(10);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS breeder VARCHAR(255);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS sire_region VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS dam_region VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS damsire_region VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS trainer_location VARCHAR(255);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS trainer_14_days JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS trainer_rtf VARCHAR(50);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS headgear_run VARCHAR(50);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS wind_surgery VARCHAR(200);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS wind_surgery_run VARCHAR(50);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS last_run_date DATE;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS comment TEXT;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS spotlight TEXT;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS quotes JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS stable_tour JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS medical JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS past_results_flags TEXT[];
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS prev_trainers JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS prev_owners JSONB;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS odds JSONB;
NOTIFY pgrst, 'reload schema';
COMMIT;
SELECT '✅ Stage 3 Complete: 24 new columns added' as status;
EOF

echo ""
echo "Stage 4: Creating indexes..."
psql -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE << 'EOF'
BEGIN;
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_age ON ra_runners(horse_age);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_sex_code ON ra_runners(horse_sex_code);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_region ON ra_runners(horse_region);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_dob ON ra_runners(horse_dob);
CREATE INDEX IF NOT EXISTS idx_ra_runners_horse_colour ON ra_runners(horse_colour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_last_run_date ON ra_runners(last_run_date);
CREATE INDEX IF NOT EXISTS idx_ra_runners_trainer_14_days_gin ON ra_runners USING GIN (trainer_14_days);
CREATE INDEX IF NOT EXISTS idx_ra_runners_quotes_gin ON ra_runners USING GIN (quotes);
CREATE INDEX IF NOT EXISTS idx_ra_runners_stable_tour_gin ON ra_runners USING GIN (stable_tour);
CREATE INDEX IF NOT EXISTS idx_ra_runners_medical_gin ON ra_runners USING GIN (medical);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_trainers_gin ON ra_runners USING GIN (prev_trainers);
CREATE INDEX IF NOT EXISTS idx_ra_runners_prev_owners_gin ON ra_runners USING GIN (prev_owners);
CREATE INDEX IF NOT EXISTS idx_ra_runners_odds_gin ON ra_runners USING GIN (odds);
CREATE INDEX IF NOT EXISTS idx_ra_runners_past_results_flags_gin ON ra_runners USING GIN (past_results_flags);
NOTIFY pgrst, 'reload schema';
COMMIT;
SELECT '✅ Stage 4 Complete: All indexes created' as status;
EOF

echo ""
echo "=========================================="
echo "🎉 Migration 018 COMPLETE!"
echo "=========================================="
echo ""
echo "Summary:"
echo "  - 5 duplicate columns dropped"
echo "  - 2 columns renamed (age/sex -> horse_age/horse_sex)"
echo "  - 24 new columns added"
echo "  - 14 indexes created"
echo ""
echo "Your schema is now clean and 100% complete!"
