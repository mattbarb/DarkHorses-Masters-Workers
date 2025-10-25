# ra_results Table - Quick Fixes

## Issues Found

1. ❌ **dist_f column type error**: Database expected INTEGER but API returns strings like "8f", "11f"
2. ⚠️ **weight column error**: Schema cache issue with ra_runners table

## Fix #1: Update dist_f Column Type

**Run in Supabase SQL Editor:**

```sql
ALTER TABLE ra_results
ALTER COLUMN dist_f TYPE VARCHAR(20);
```

**Verify:**
```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_results'
AND column_name = 'dist_f';
```

Expected: `dist_f | character varying`

## Fix #2: Reload Supabase Schema Cache

The "Could not find 'weight' column" error is a schema cache issue.

**Option A: Restart PostgREST (Recommended)**

In Supabase Dashboard:
1. Go to Settings → API
2. Click "Restart API" or "Reload Schema Cache"

**Option B: Run NOTIFY Command**

```sql
NOTIFY pgrst, 'reload schema';
```

## Test After Fixes

```bash
# Test with 3 days of results
python3 scripts/test_results_table.py
```

**Expected output:**
```
Results inserted: {'inserted': 176, 'updated': 0, 'errors': 0} ⭐ NEW TABLE
Runners inserted: {'inserted': 1630, 'updated': 0, 'errors': 0}
```

## Verification Queries

After successful test:

```sql
-- Check results were inserted
SELECT COUNT(*) as total_results FROM ra_results;

-- Check tote data
SELECT
  race_id,
  course_name,
  tote_win,
  tote_ex,
  winning_time_detail
FROM ra_results
WHERE tote_win IS NOT NULL
LIMIT 10;

-- Check runners
SELECT COUNT(*) as total_runners FROM ra_runners;
```

## Root Cause

- **dist_f**: Migration 017 initially created as INTEGER, but API returns formatted strings
- **weight**: Old schema used `weight` field, but we migrated to `weight_lbs` - PostgREST cache wasn't updated

## Prevention

For future migrations:
1. Check API response data types before creating columns
2. Always reload schema cache after DDL changes
3. Test with real data before large imports

---

**Status:** Fixes ready to apply
**Time to fix:** < 2 minutes
**Risk:** Very low - simple type changes
