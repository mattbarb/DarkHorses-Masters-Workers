# Region Field Addition to ra_horse_pedigree

**Date:** 2025-10-15
**Status:** Migration ready, workers updated

## Summary

Added `region` column to `ra_horse_pedigree` table for better ML query performance and data organization.

## Background

The `ra_horse_pedigree` table was missing the `region` field, which made it:
1. Impossible to filter pedigrees by region without joining to `ra_horses`
2. Inefficient for ML queries that need region-specific pedigree data
3. Inconsistent with other reference tables that include region

## Changes Made

### 1. Database Migration

**File:** `migrations/010_add_region_to_pedigree.sql`

**Actions:**
- Adds `region VARCHAR(10)` column to `ra_horse_pedigree`
- Backfills existing records with region from `ra_horses` table
- Creates index `idx_horse_pedigree_region` for query performance
- Includes verification reporting

**To Execute:**
```sql
-- Run via Supabase SQL Editor
-- Path: migrations/010_add_region_to_pedigree.sql
```

### 2. Backfill Script Update

**File:** `scripts/backfill_horse_pedigree_enhanced.py`

**Changes:**
- Line 237: Added `'region': horse_data.get('region')` to pedigree_record dictionary

**Before:**
```python
pedigree_record = {
    'horse_id': horse_id,
    'sire_id': horse_data.get('sire_id'),
    ...
    'breeder': horse_data.get('breeder'),
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}
```

**After:**
```python
pedigree_record = {
    'horse_id': horse_id,
    'sire_id': horse_data.get('sire_id'),
    ...
    'breeder': horse_data.get('breeder'),
    'region': horse_data.get('region'),  # Added
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}
```

### 3. Horses Fetcher Update

**File:** `fetchers/horses_fetcher.py`

**Changes:**
- Line 198: Added `'region': horse_pro.get('region')` to pedigree_record dictionary

**Impact:**
- All new horses discovered via hybrid enrichment will have region set in pedigree table
- Ensures consistency between `ra_horses` and `ra_horse_pedigree`

## Benefits

### For ML Queries

**Before (required join):**
```sql
SELECT p.*
FROM ra_horse_pedigree p
JOIN ra_horses h ON p.horse_id = h.horse_id
WHERE h.region IN ('gb', 'ire');
```

**After (direct filter):**
```sql
SELECT *
FROM ra_horse_pedigree
WHERE region IN ('gb', 'ire');
```

### Performance Improvements

1. **Faster queries** - No join required for region filtering
2. **Better indexing** - Direct index on region column
3. **Simplified queries** - Cleaner SQL for ML feature extraction

### Data Consistency

1. Region stored in both `ra_horses` and `ra_horse_pedigree`
2. All new pedigrees automatically include region
3. Existing pedigrees backfilled from `ra_horses`

## Data Quality

### Current State (Pre-Migration)

- **Total pedigree records:** ~72,266
- **Records with region:** 0 (0%)
- **Records without region:** 72,266 (100%)

### Expected State (Post-Migration)

- **Total pedigree records:** ~72,266
- **Records with region:** ~72,266 (100%) - backfilled from ra_horses
- **Records without region:** 0 (0%)

**Note:** Some records may have NULL region if:
- The parent horse record also has NULL region
- The horse hasn't been enriched yet with Pro API data

## ML API Impact

### Updated Documentation

The following ML API documentation should be updated to reflect the new field:

**Files to update:**
1. `/Users/matthewbarber/Documents/GitHub/DarkHorses-API/docs/AI ML Documentation/MASTERS_DATABASE_SCHEMA_ML_API_REFERENCE.md`
   - Add `region` to ra_horse_pedigree table schema
   - Update example queries to show direct region filtering

2. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/api_reference/DATABASE_SCHEMA_ML_API_REFERENCE.md`
   - Add `region` to ra_horse_pedigree table schema
   - Note: This is the source document

### Example Query Update

**For sire analysis by region:**
```sql
SELECT
    sire_id,
    sire,
    region,
    COUNT(*) as offspring_count,
    AVG(win_rate) as avg_offspring_win_rate
FROM ra_horse_pedigree p
JOIN ra_runners r ON r.horse_id = p.horse_id
WHERE p.region IN ('gb', 'ire')
  AND p.sire_id IS NOT NULL
GROUP BY sire_id, sire, region
ORDER BY offspring_count DESC
LIMIT 100;
```

## Deployment Steps

1. **Run Migration**
   ```bash
   # Execute via Supabase SQL Editor
   # File: migrations/010_add_region_to_pedigree.sql
   ```

2. **Verify Migration**
   ```sql
   -- Check column exists
   SELECT column_name, data_type
   FROM information_schema.columns
   WHERE table_name = 'ra_horse_pedigree'
     AND column_name = 'region';

   -- Check data population
   SELECT
       COUNT(*) as total,
       COUNT(region) as with_region,
       COUNT(*) - COUNT(region) as without_region
   FROM ra_horse_pedigree;

   -- Check region distribution
   SELECT region, COUNT(*) as count
   FROM ra_horse_pedigree
   GROUP BY region
   ORDER BY count DESC;
   ```

3. **Worker Updates**
   - Workers already updated (backfill script, horses fetcher)
   - No restart required - changes take effect on next fetch
   - Currently running backfill will use NEW code (includes region)

## Rollback Plan

If issues arise:

```sql
-- Remove index
DROP INDEX IF EXISTS idx_horse_pedigree_region;

-- Remove column
ALTER TABLE ra_horse_pedigree DROP COLUMN IF EXISTS region;
```

**Note:** This is a non-destructive addition. Rollback is safe.

## Testing

### Pre-Migration Test
```sql
-- Verify column doesn't exist
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'ra_horse_pedigree'
  AND column_name = 'region';
-- Expected: No results
```

### Post-Migration Test
```sql
-- Verify column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_horse_pedigree'
  AND column_name = 'region';
-- Expected: region | character varying

-- Verify data populated
SELECT
    COUNT(*) as total,
    COUNT(DISTINCT region) as unique_regions,
    COUNT(region) as populated
FROM ra_horse_pedigree;
-- Expected: total > 0, unique_regions >= 2 (gb, ire), populated > 0

-- Verify index exists
SELECT indexname
FROM pg_indexes
WHERE tablename = 'ra_horse_pedigree'
  AND indexname = 'idx_horse_pedigree_region';
-- Expected: idx_horse_pedigree_region
```

## Related Changes

This change is part of a larger effort to improve ML API data quality:

1. **ML Runner History Cleanup** - Removed pre-calculated ML table (deprecated)
2. **Region Field Addition** - This change
3. **API-Based ML Features** - Moving to on-demand feature calculation

## Notes

- The running backfill process (if active) will automatically use the new code
- New horses discovered via hybrid enrichment will have region set immediately
- Existing pedigrees backfilled via migration
- No impact on existing functionality - purely additive change

---

**Migration Status:** Ready to execute
**Worker Status:** Updated and deployed
**Documentation Status:** Needs update in ML API docs
