# Migration 029: Rename ra_races to ra_mst_races

**Date:** 2025-10-26
**Purpose:** Align races table with master table naming convention
**Impact:** Table rename + 100+ code files updated

## Summary

The `ra_races` table has been renamed to `ra_mst_races` to align with the master table naming convention used for reference data (ra_mst_*). This change classifies races as master reference data alongside courses, bookmakers, horses, jockeys, trainers, and owners.

## Database Changes

### SQL Migration
- **File:** `migrations/sql/029_rename_ra_races_to_ra_mst_races.sql`
- **Changes:**
  - Renamed table: `ra_races` → `ra_mst_races`
  - Renamed primary key constraint: `ra_races_pkey` → `ra_mst_races_pkey`
  - Updated foreign key constraints in `ra_mst_runners` and `ra_mst_race_results`
  - Updated metadata tracking table references

### To Apply Migration

Run the migration in Supabase SQL editor:

```bash
psql -h <host> -U <user> -d <database> -f migrations/sql/029_rename_ra_races_to_ra_mst_races.sql
```

Or via Supabase dashboard:
1. Go to SQL Editor
2. Paste contents of `migrations/sql/029_rename_ra_races_to_ra_mst_races.sql`
3. Execute

## Code Changes

### Files Updated: 102 files

#### Core Python Files (21 files)
- `utils/supabase_client.py` - Updated `insert_races()` method
- `utils/metadata_tracker.py` - Updated table list
- `workers/statistics/*.py` (8 files) - Updated race date queries
- `workers/pedigree/pedigree_statistics_agent.py` - Updated race queries
- `workers/orchestrators/master_populate_all_ra_tables.py` - Updated table configuration
- `scripts/population/*.py` (5 files) - Updated aggregation queries
- `scripts/backfill/*.py` (2 files) - Updated race queries
- `scripts/diagnostics/*.py` (1 file) - Updated test queries
- `scripts/maintenance/*.py` (1 file) - Updated maintenance queries
- `scripts/validation/*.py` (1 file) - Updated validation queries

#### Shell Scripts (2 files)
- `monitor_backfill.sh` - Updated database queries
- `scripts/maintenance/backfill_distance_m_loop.sh` - Updated queries

#### Documentation Files (80 files)
- `CLAUDE.md` - Updated project documentation
- `README.md` - Updated system overview
- `docs/**/*.md` (54 files) - Updated all references
- `docs/**/*.json` (8 files) - Updated JSON inventory files
- `fetchers/docs/*.md` (10 files) - Updated fetcher documentation
- `fetchers/docs/*.json` (3 files) - Updated column mappings
- `fetchers/schedules/*.yaml` (1 file) - Updated schedule dependencies
- `QUICK_START_BACKFILL_AND_SYNC.md` - Updated quick start guide
- `DATA_SOURCE_STRATEGY.md` - Updated data source documentation

### Change Pattern

All occurrences were replaced using these patterns:

```python
# Python code
.table('ra_races')          → .table('ra_mst_races')
.from_('ra_races')          → .from_('ra_mst_races')

# Documentation
ra_races                    → ra_mst_races
```

## Testing Checklist

Before deploying to production, verify:

- [ ] Migration SQL runs without errors
- [ ] All foreign key constraints are properly updated
- [ ] `ra_mst_runners.race_id` still references the renamed table
- [ ] `ra_mst_race_results.race_id` still references the renamed table
- [ ] Test basic race fetch: `python3 main.py --entities races --test`
- [ ] Test results fetch: `python3 main.py --entities results --test`
- [ ] Test statistics calculation: Verify workers can query race dates
- [ ] Verify metadata tracking updates correctly
- [ ] Check that no code still references `ra_races`

## Verification Queries

After migration, run these queries to verify:

```sql
-- Verify table exists
SELECT COUNT(*) FROM ra_mst_races;

-- Verify foreign keys
SELECT
    conname AS constraint_name,
    conrelid::regclass AS table_name,
    confrelid::regclass AS referenced_table
FROM pg_constraint
WHERE confrelid = 'ra_mst_races'::regclass;

-- Verify metadata tracking
SELECT * FROM ra_metadata_tracking
WHERE table_name = 'ra_mst_races';

-- Verify no references to old name remain
SELECT * FROM ra_metadata_tracking
WHERE table_name = 'ra_races';  -- Should return 0 rows
```

## Rollback Plan

If issues arise, rollback with:

```sql
-- Rollback migration
ALTER TABLE ra_mst_races RENAME TO ra_races;
ALTER TABLE ra_mst_races RENAME CONSTRAINT ra_mst_races_pkey TO ra_races_pkey;

-- Restore foreign keys
ALTER TABLE ra_mst_runners DROP CONSTRAINT IF EXISTS ra_mst_runners_race_id_fkey;
ALTER TABLE ra_mst_runners ADD CONSTRAINT ra_mst_runners_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_races(race_id);

ALTER TABLE ra_mst_race_results DROP CONSTRAINT IF EXISTS ra_mst_race_results_race_id_fkey;
ALTER TABLE ra_mst_race_results ADD CONSTRAINT ra_mst_race_results_race_id_fkey
    FOREIGN KEY (race_id) REFERENCES ra_races(race_id);

-- Restore metadata
UPDATE ra_metadata_tracking
SET table_name = 'ra_races'
WHERE table_name = 'ra_mst_races';
```

Then revert all code changes via git:
```bash
git revert <commit-hash>
```

## Impact Assessment

### Low Risk Areas
- Documentation files (no runtime impact)
- JSON inventory files (reference only)
- Schedule YAML files (documentation)

### Medium Risk Areas
- Statistics workers (may fail to calculate if migration not applied)
- Population scripts (may fail to find table)
- Validation scripts (may fail test queries)

### High Risk Areas
- `utils/supabase_client.py` - Core database operations
- Active fetchers (races_fetcher.py, results_fetcher.py) - Production data flow

### Zero Risk
- Files in `_deprecated/` directory were NOT updated (intentionally)

## Post-Migration Steps

1. **Apply migration** to Supabase database
2. **Deploy code changes** to production
3. **Run smoke tests:**
   ```bash
   python3 main.py --entities races --test
   python3 main.py --entities results --test
   ```
4. **Monitor logs** for any references to old table name
5. **Update any external documentation** or API references

## Notes

- Migration maintains all data (no data loss)
- Table structure unchanged (column-compatible)
- Foreign key relationships preserved
- Indexes and constraints renamed consistently
- No changes to `_deprecated/` directory files (intentional)

## Classification Change

**Before:** ra_races was categorized as a transaction table
**After:** ra_mst_races is now categorized as a master reference table

This aligns with the table's purpose: storing race metadata that serves as reference data for runners and results.

**Updated Master Tables (11 total):**
- ra_mst_bookmakers
- ra_mst_courses
- ra_mst_dams
- ra_mst_damsires
- ra_mst_horses
- ra_mst_jockeys
- ra_mst_owners
- ra_mst_races ← NEW
- ra_mst_regions
- ra_mst_sires
- ra_mst_trainers

## References

- **Migration File:** `migrations/sql/029_rename_ra_races_to_ra_mst_races.sql`
- **Previous Migration:** `028_drop_ra_runner_supplementary.sql`
- **Next Migration:** TBD
- **Related Documentation:** `CLAUDE.md`, `fetchers/docs/*MASTER_DATABASE_TABLES_AND_DATA_SOURCES.md`
