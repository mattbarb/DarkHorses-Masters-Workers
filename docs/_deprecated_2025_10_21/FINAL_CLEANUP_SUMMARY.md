# Final Duplicate Column Cleanup Summary

## Total Columns to Drop: 9

### 1. Timestamp Duplicate (1 column)
- **DROP:** `fetched_at` → **KEEP:** `created_at`
- Both track when record was created
- `created_at` is standard across all tables

### 2. Racing API ID Duplicates (5 columns)
- **DROP:** `racing_api_race_id` → **KEEP:** `race_id`
- **DROP:** `racing_api_horse_id` → **KEEP:** `horse_id`
- **DROP:** `racing_api_jockey_id` → **KEEP:** `jockey_id`
- **DROP:** `racing_api_trainer_id` → **KEEP:** `trainer_id`
- **DROP:** `racing_api_owner_id` → **KEEP:** `owner_id`
- All store identical IDs from Racing API
- Primary columns (`*_id`) are cleaner, shorter names

### 3. Data Field Duplicates (3 columns)
- **DROP:** `weight` → **KEEP:** `weight_lbs`
- **DROP:** `race_comment` → **KEEP:** `comment`
- **DROP:** `jockey_silk_url` → **KEEP:** `silk_url`
- All store identical data from API responses
- Primary columns are more specific/standard names

## Storage Impact

**Before:** 1,325,718 records × 9 duplicate columns = ~11.9M redundant cells
**After:** 9 columns eliminated
**Estimated savings:** 150-200 MB

## Execution Plan

### ✅ Phase 1: IMMEDIATE - Drop Racing API ID Columns (No data merge needed)

These columns store identical data, no merging required:
- fetched_at
- racing_api_race_id, racing_api_horse_id, racing_api_jockey_id
- racing_api_trainer_id, racing_api_owner_id

**Action:** Run migration NOW for these 6 columns

### ⏸️ Phase 2: WAIT - Drop Data Field Columns (After backfill completes)

These columns need data consolidation first:
- weight → weight_lbs
- race_comment → comment
- jockey_silk_url → silk_url

**Action:** Wait for current backfill to finish, then run merge script

## Implementation Steps

### Step 1: Run Partial Migration (NOW)

Create and run simplified migration for racing_api_* fields:

```sql
-- migrations/016a_drop_racing_api_columns.sql
ALTER TABLE ra_runners DROP COLUMN IF EXISTS fetched_at;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_race_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_horse_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_jockey_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_trainer_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS racing_api_owner_id;
```

**Duration:** ~10 seconds

### Step 2: Update Fetchers (NOW)

Remove assignments for dropped columns in `fetchers/races_fetcher.py`:

```python
# REMOVE these lines:
'fetched_at': datetime.utcnow().isoformat(),
'racing_api_race_id': race_id,
'racing_api_horse_id': runner.get('horse_id'),
'racing_api_jockey_id': runner.get('jockey_id'),
'racing_api_trainer_id': runner.get('trainer_id'),
'racing_api_owner_id': runner.get('owner_id'),
```

### Step 3: Wait for Backfill to Complete

Current backfill is populating wrong columns (weight, race_comment, jockey_silk_url).
Monitor: `tail -f logs/backfill_optimized_run.log`

### Step 4: Update Backfill Field Mappings

Change `scripts/backfill_runners_optimized.py`:
```python
{'db_field': 'weight_lbs', 'api_field': 'weight_lbs', ...},  # Not 'weight'
{'db_field': 'comment', 'api_field': 'comment', ...},  # Not 'race_comment'
{'db_field': 'silk_url', 'api_field': 'silk_url', ...},  # Not 'jockey_silk_url'
```

### Step 5: Run Merge Script (After backfill)

```bash
python3 scripts/merge_duplicate_columns.py --batch-size 25
```

**Duration:** ~2-4 hours

### Step 6: Drop Remaining Columns

```sql
-- migrations/016b_drop_data_field_duplicates.sql
ALTER TABLE ra_runners DROP COLUMN IF EXISTS weight;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_silk_url;
```

### Step 7: Update Fetchers (Final)

Remove remaining duplicate assignments:
```python
# REMOVE:
'weight': runner.get('weight_lbs'),
'race_comment': parse_text_field(runner.get('comment')),
'jockey_silk_url': parse_text_field(runner.get('silk_url')),
```

## Files Created

1. **`migrations/016_drop_duplicate_columns.sql`** - Complete migration (all 9 columns)
2. **`migrations/016a_drop_racing_api_columns.sql`** - Phase 1 only (6 columns) - CREATE THIS
3. **`migrations/016b_drop_data_field_duplicates.sql`** - Phase 2 only (3 columns) - CREATE THIS
4. **`scripts/merge_duplicate_columns.py`** - Data consolidation (already created)
5. **`docs/DUPLICATE_CLEANUP_SUMMARY.md`** - Original plan
6. **`docs/FINAL_CLEANUP_SUMMARY.md`** - This document

## Benefits

### Immediate (Phase 1)
- 6 columns eliminated
- ~100 MB storage freed
- Cleaner schema (no racing_api_* prefix noise)
- Fetchers simplified

### After Phase 2
- 9 total columns eliminated
- ~200 MB total storage freed
- All duplicate data removed
- Simplified backfill operations

## Next Actions

1. ✅ **NOW:** Create and run `migrations/016a_drop_racing_api_columns.sql`
2. ✅ **NOW:** Update `fetchers/races_fetcher.py` to remove racing_api_* assignments
3. ⏸️ **LATER:** Complete Phase 2 after backfill finishes
