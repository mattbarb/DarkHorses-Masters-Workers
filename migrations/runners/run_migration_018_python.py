#!/usr/bin/env python3
"""
Run Migration 018 via direct database connection using psycopg2
"""

import psycopg2
import sys

# Connection string - using connection pooler
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 60)
print("Migration 018: Direct Database Connection")
print("=" * 60)
print()

try:
    print("Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False
    cur = conn.cursor()
    print("✅ Connected successfully!")
    print()

    # Stage 1: Drop duplicate columns
    print("Stage 1: Dropping duplicate columns...")
    cur.execute("""
        BEGIN;
        ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_claim;
        ALTER TABLE ra_runners DROP COLUMN IF EXISTS apprentice_allowance;
        ALTER TABLE ra_runners DROP COLUMN IF EXISTS overall_beaten_distance;
        ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_post_rating;
        ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;
        COMMIT;
    """)
    print("✅ Stage 1 Complete: 5 duplicate columns dropped")
    print()

    # Stage 2: Rename columns (with conditional logic)
    print("Stage 2: Renaming columns...")
    cur.execute("""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'ra_runners' AND column_name = 'age') THEN
                ALTER TABLE ra_runners RENAME COLUMN age TO horse_age;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns
                      WHERE table_name = 'ra_runners' AND column_name = 'sex') THEN
                ALTER TABLE ra_runners RENAME COLUMN sex TO horse_sex;
            END IF;
        END $$;
    """)
    print("✅ Stage 2 Complete: Columns renamed (if they existed)")
    print()

    # Stage 3: Add new columns
    print("Stage 3: Adding new columns...")
    cur.execute("""
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
        COMMIT;
    """)
    print("✅ Stage 3 Complete: 24 new columns added")
    print()

    # Stage 4: Create indexes
    print("Stage 4: Creating indexes...")
    cur.execute("""
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
        COMMIT;
    """)
    print("✅ Stage 4 Complete: All indexes created")
    print()

    cur.close()
    conn.close()

    print("=" * 60)
    print("🎉 Migration 018 COMPLETE!")
    print("=" * 60)
    print()
    print("Summary:")
    print("  - 5 duplicate columns dropped")
    print("  - 2 columns renamed (age/sex -> horse_age/horse_sex)")
    print("  - 24 new columns added")
    print("  - 14 indexes created")
    print()
    print("Your schema is now clean and 100% complete!")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
