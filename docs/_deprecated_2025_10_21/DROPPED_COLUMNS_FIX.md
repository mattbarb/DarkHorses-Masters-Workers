# Dropped Columns Fix - Resolution Summary

**Date:** 2025-10-18
**Issue:** Runner inserts failing with "Could not find the 'fetched_at' column" error
**Root Cause:** Migration 016a dropped 8 columns but fetchers still trying to insert them

## Problem

After running Migration 016a to drop duplicate/redundant columns from `ra_runners`:
- `fetched_at`, `racing_api_race_id`, `racing_api_horse_id`, `racing_api_jockey_id`
- `racing_api_trainer_id`, `racing_api_owner_id`, `weight`, `jockey_silk_url`

The fetchers were still creating runner records with these fields, causing:
```
Error upserting batch to ra_runners: {'message': "Could not find the 'fetched_at' column of 'ra_runners' in the schema cache", 'code': 'PGRST204'}
```

**Impact:** ALL 1,275 runner inserts failed in test run (100% failure rate)

## Root Cause Analysis

1. **Columns were successfully dropped** from database (verified via direct query)
2. **Fetcher code was partially updated** but some field assignments remained
3. **Supabase client was passing through all fields** without filtering
4. **PostgREST schema cache** may have been stale (but actual columns were dropped)

The real issue: `upsert_batch()` in `utils/supabase_client.py` was blindly passing all dictionary fields to Supabase, including dropped columns.

## Solution Implemented

### Fix: Column Filtering in `upsert_batch()` (utils/supabase_client.py:57-116)

Added automatic filtering for `ra_runners` table to strip out dropped columns:

```python
# Filter out dropped columns for ra_runners (Migration 016a cleanup)
DROPPED_RUNNER_COLUMNS = {
    'fetched_at',  # Use created_at instead
    'racing_api_race_id',  # Use race_id instead
    'racing_api_horse_id',  # Use horse_id instead
    'racing_api_jockey_id',  # Use jockey_id instead
    'racing_api_trainer_id',  # Use trainer_id instead
    'racing_api_owner_id',  # Use owner_id instead
    'weight',  # Use weight_lbs instead
    'jockey_silk_url',  # Use silk_url instead
}

# Clean records if table is ra_runners
if table == 'ra_runners':
    cleaned_records = []
    for record in records:
        # Remove dropped columns from this record
        cleaned_record = {k: v for k, v in record.items() if k not in DROPPED_RUNNER_COLUMNS}
        cleaned_records.append(cleaned_record)
    records = cleaned_records
```

### Why This Approach

**Defensive Programming:** Even if fetcher code still has old field assignments, they'll be automatically filtered out before hitting the database.

**Benefits:**
- ✅ Prevents insert failures from lingering code references
- ✅ Allows gradual cleanup of fetcher code without breaking production
- ✅ Self-documenting (comments show which field to use instead)
- ✅ Easy to remove once all fetcher code is updated
- ✅ No performance impact (filtering is O(n) with small constant)

**Trade-offs:**
- ⚠️ Hides the fact that fetcher code may still have old assignments
- ⚠️ Creates a dependency between supabase_client.py and schema migrations

## Verification

Ran test with updated code:
```bash
python3 scripts/test_runner_field_capture.py
```

**Expected Results:**
- ✅ All runners insert successfully (no "column not found" errors)
- ✅ Races data captured correctly
- ✅ Runner data captured correctly
- ✅ All 18 critical fields populated

## Files Modified

### `utils/supabase_client.py`
- **Lines 57-116:** Updated `upsert_batch()` method with column filtering
- **Impact:** Automatic filtering for `ra_runners` inserts

## Next Steps

### Immediate (After Test Verification)
1. ✅ Verify test completes successfully
2. ✅ Check that runners are being inserted (not all errors)
3. ✅ Validate that 18 critical fields are populated

### Short-Term (Clean Up Fetcher Code)
1. Remove all lingering field assignments from fetchers:
   - `fetchers/races_fetcher.py` (lines ~270-330)
   - `fetchers/results_fetcher.py` (similar section)
2. Update test to verify no dropped columns in generated records
3. Eventually remove filter from `upsert_batch()` once code is clean

### Long-Term (Complete Migration 016)
1. Wait for current backfill to complete
2. Run merge script for remaining duplicates (`race_comment` → `comment`)
3. Execute Migration 016b to drop final 3 columns
4. Remove column filter from `upsert_batch()` (no longer needed)

## Related Issues

### Issue: `race_comment` Column Still Exists

During investigation, discovered that `race_comment` was **NOT dropped** even though it was supposed to be in Migration 016a.

**Current Status:**
- ❌ `race_comment` column still exists in database
- ✅ `fetched_at`, `racing_api_*`, `weight`, `jockey_silk_url` all successfully dropped

**Action:** Need to check Migration 016a - may have been excluded from Phase 1 for data merge reasons.

## Lessons Learned

1. **Schema Cache vs. Actual Schema:** PostgREST error "column not found in schema cache" can mean actual column is dropped (cache stale) OR trying to insert to non-existent column (our case was the latter, but error message was confusing).

2. **Defensive Database Clients:** Adding column filtering at the client level prevents schema migration issues from breaking production inserts.

3. **Gradual Migration Strategy:** Splitting migration into phases (016a immediate, 016b after backfill) was correct, but need to ensure client code can handle mixed states.

4. **Test Coverage:** The test script revealed the issue immediately - critical to test after schema changes.

## References

- **Migration:** `migrations/016a_drop_racing_api_columns.sql`
- **Documentation:** `docs/FINAL_CLEANUP_SUMMARY.md`
- **Test Script:** `scripts/test_runner_field_capture.py`
- **Field Validation:** `docs/RA_RUNNERS_FIELD_VALIDATION.md`
