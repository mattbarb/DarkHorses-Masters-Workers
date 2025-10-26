# How to Run Migration 029: Rename Tables to ra_mst_* Convention

**Migration File:** `migrations/sql/029_rename_three_tables_to_mst.sql`

This migration renames three tables:
- `ra_races` → `ra_mst_races`
- `ra_runners` → `ra_mst_runners`
- `ra_race_results` → `ra_mst_race_results`

## Prerequisites

- [x] All code changes committed (already done)
- [ ] Supabase access (either CLI or dashboard)
- [ ] Database backup (recommended)

## Option 1: Supabase CLI (Recommended)

### Step 1: Install Supabase CLI (if not installed)

```bash
# macOS
brew install supabase/tap/supabase

# Or via npm
npm install -g supabase
```

### Step 2: Link to your Supabase project

```bash
# Initialize Supabase (if not already done)
supabase init

# Link to your remote project
supabase link --project-ref YOUR_PROJECT_REF
```

To get your `PROJECT_REF`:
1. Go to your Supabase dashboard
2. Settings → General → Project ID
3. Use that as YOUR_PROJECT_REF

### Step 3: Run the migration

```bash
# Run the migration directly
supabase db push --include migrations/sql/029_rename_three_tables_to_mst.sql

# OR use psql through Supabase CLI
supabase db execute < migrations/sql/029_rename_three_tables_to_mst.sql
```

### Step 4: Verify the migration

```bash
# Check that old tables don't exist
supabase db execute "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('ra_races', 'ra_runners', 'ra_race_results');"

# Should return 0 rows

# Check that new tables exist
supabase db execute "SELECT COUNT(*) as races FROM ra_mst_races; SELECT COUNT(*) as runners FROM ra_mst_runners; SELECT COUNT(*) as results FROM ra_mst_race_results;"
```

## Option 2: Direct PostgreSQL Connection

### Step 1: Get database connection string

From Supabase Dashboard:
1. Settings → Database
2. Copy the connection string (Connection pooling or Direct connection)
3. Replace `[YOUR-PASSWORD]` with your database password

### Step 2: Run migration with psql

```bash
# Set your connection details
export PGHOST="your-project.supabase.co"
export PGPORT="5432"
export PGDATABASE="postgres"
export PGUSER="postgres"
export PGPASSWORD="your-password"

# Run the migration
psql < migrations/sql/029_rename_three_tables_to_mst.sql

# OR use the connection string directly
psql "postgresql://postgres:[YOUR-PASSWORD]@your-project.supabase.co:5432/postgres" < migrations/sql/029_rename_three_tables_to_mst.sql
```

## Option 3: Supabase SQL Editor (Web UI)

### Step 1: Open SQL Editor

1. Go to https://supabase.com/dashboard
2. Select your project
3. Click "SQL Editor" in the left sidebar

### Step 2: Run the migration

1. Click "New query"
2. Copy the entire contents of `migrations/sql/029_rename_three_tables_to_mst.sql`
3. Paste into the SQL editor
4. Click "Run" or press Cmd/Ctrl + Enter

### Step 3: Verify in web UI

1. Go to "Table Editor"
2. Check that `ra_mst_races`, `ra_mst_runners`, and `ra_mst_race_results` exist
3. Check that old table names are gone

## Option 4: Using Python Script

I can create a Python script that runs the migration:

```python
#!/usr/bin/env python3
"""Run Migration 029 via Python"""

import os
from supabase import create_client
from pathlib import Path

# Load environment variables
from dotenv import load_dotenv
load_dotenv('.env.local')

# Connect to Supabase
url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')
supabase = create_client(url, key)

# Read migration file
migration_path = Path('migrations/sql/029_rename_three_tables_to_mst.sql')
with open(migration_path, 'r') as f:
    migration_sql = f.read()

# Execute migration
print("Running migration 029...")
try:
    # Note: Supabase Python SDK doesn't directly support raw SQL execution
    # You'll need to use psycopg2 or another PostgreSQL library
    import psycopg2

    conn_string = f"postgresql://postgres:{os.getenv('DB_PASSWORD')}@{url.replace('https://', '').replace('http://', '')}:5432/postgres"
    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    cursor.execute(migration_sql)
    conn.commit()

    print("✅ Migration completed successfully!")

except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
finally:
    cursor.close()
    conn.close()
```

## Verification Queries

After running the migration, verify with these queries:

```sql
-- 1. Check new tables exist and have data
SELECT
    'ra_mst_races' as table_name, COUNT(*) as row_count
FROM ra_mst_races
UNION ALL
SELECT
    'ra_mst_runners', COUNT(*)
FROM ra_mst_runners
UNION ALL
SELECT
    'ra_mst_race_results', COUNT(*)
FROM ra_mst_race_results;

-- 2. Verify old tables are gone
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('ra_races', 'ra_runners', 'ra_race_results');
-- Should return 0 rows

-- 3. Check foreign key constraints
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE conrelid IN ('ra_mst_races'::regclass, 'ra_mst_runners'::regclass, 'ra_mst_race_results'::regclass)
ORDER BY conrelid::regclass, conname;

-- 4. Verify metadata tracking updated
SELECT table_name, COUNT(*) as update_count
FROM ra_metadata_tracking
WHERE table_name IN ('ra_mst_races', 'ra_mst_runners', 'ra_mst_race_results')
GROUP BY table_name
ORDER BY table_name;

-- 5. Test a query to make sure everything works
SELECT
    r.date,
    r.course_name,
    COUNT(ru.id) as runner_count
FROM ra_mst_races r
LEFT JOIN ra_mst_runners ru ON r.race_id = ru.race_id
GROUP BY r.date, r.course_name
ORDER BY r.date DESC
LIMIT 5;
```

## Post-Migration Testing

After applying the database migration, test the application:

```bash
# Test races fetch
python3 main.py --entities races --test

# Test results fetch
python3 main.py --entities results --test

# Check metadata
python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

# Test query on new table names
races = db.client.table('ra_mst_races').select('*').limit(1).execute()
runners = db.client.table('ra_mst_runners').select('*').limit(1).execute()
results = db.client.table('ra_mst_race_results').select('*').limit(1).execute()

print(f'✅ ra_mst_races: {len(races.data)} rows')
print(f'✅ ra_mst_runners: {len(runners.data)} rows')
print(f'✅ ra_mst_race_results: {len(results.data)} rows')
"
```

## Rollback (If Needed)

If something goes wrong, you can rollback with:

```sql
-- Rollback all three tables
ALTER TABLE ra_mst_races RENAME TO ra_races;
ALTER TABLE ra_mst_races RENAME CONSTRAINT ra_mst_races_pkey TO ra_races_pkey;

ALTER TABLE ra_mst_runners RENAME TO ra_runners;
ALTER TABLE ra_mst_runners RENAME CONSTRAINT ra_mst_runners_pkey TO ra_runners_pkey;

ALTER TABLE ra_mst_race_results RENAME TO ra_race_results;
ALTER TABLE ra_mst_race_results RENAME CONSTRAINT ra_mst_race_results_pkey TO ra_race_results_pkey;

-- Fix foreign keys back
ALTER TABLE ra_runners DROP CONSTRAINT IF EXISTS ra_mst_runners_race_id_fkey;
ALTER TABLE ra_runners ADD CONSTRAINT ra_runners_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_races(race_id);

-- Update metadata
UPDATE ra_metadata_tracking SET table_name = 'ra_races' WHERE table_name = 'ra_mst_races';
UPDATE ra_metadata_tracking SET table_name = 'ra_runners' WHERE table_name = 'ra_mst_runners';
UPDATE ra_metadata_tracking SET table_name = 'ra_race_results' WHERE table_name = 'ra_mst_race_results';
```

Then revert code changes:
```bash
git revert HEAD
```

## Summary

**Recommended approach:** Option 1 (Supabase CLI) or Option 2 (Direct psql connection)

**Time required:** 1-2 minutes for migration execution

**Downtime:** None (table renames are instant in PostgreSQL)

**Risk level:** Low (non-destructive, easily reversible)

---

**After successful migration, all application code will automatically use the new table names!**
