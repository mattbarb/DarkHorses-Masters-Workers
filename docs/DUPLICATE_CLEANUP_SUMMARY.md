# Duplicate Column Cleanup - Complete Summary

## Overview

Analysis revealed 3 duplicate column pairs in `ra_runners` table storing identical data, wasting space and causing confusion.

## Duplicate Columns Identified

| Primary Column (Keep) | Duplicate Column (Drop) | Data Type | Sample Population |
|-----------------------|-------------------------|-----------|-------------------|
| **weight_lbs** | weight | INTEGER | 100% vs 63.8% |
| **comment** | race_comment | TEXT | 68.6% vs 17.0% |
| **silk_url** | jockey_silk_url | TEXT | 63.3% vs 2.9% |

**Total to drop:** 3 columns (weight, race_comment, jockey_silk_url)

## Root Cause

Fetchers (`races_fetcher.py:100-134`) were updated to populate **both** columns with identical data:

```python
# Redundant assignments
'weight': runner.get('weight_lbs'),
'weight_lbs': runner.get('weight_lbs'),  # DUPLICATE!

'comment': runner.get('comment'),
'race_comment': parse_text_field(runner.get('comment')),  # DUPLICATE!

'silk_url': runner.get('silk_url'),
'jockey_silk_url': parse_text_field(runner.get('silk_url')),  # DUPLICATE!
```

## Files Created

### 1. Analysis & Planning
- **`docs/DUPLICATE_COLUMN_CLEANUP_PLAN.md`** - Detailed cleanup strategy
- **`scripts/analyze_duplicate_columns.py`** - Column usage analysis (timed out on 1.3M records)
- **`scripts/sample_duplicate_columns.py`** - Sample-based analysis (successful)

### 2. Implementation Scripts
- **`scripts/merge_duplicate_columns.py`** - Merge data before dropping columns
  - Uses 25-record batches to avoid timeouts
  - Checkpoint/resume capability
  - Processes: weight → weight_lbs, race_comment → comment, jockey_silk_url → silk_url

### 3. Database Migration
- **`migrations/016_drop_duplicate_columns.sql`** - Drop duplicate columns
  - Includes safety checks (prevents data loss)
  - Verification step
  - Post-migration instructions

## Implementation Steps

### ✅ Step 1: WAIT for Backfill to Complete (IN PROGRESS)

**Current Status:** `scripts/backfill_runners_optimized.py` is running in background

```bash
# Monitor progress
tail -f logs/backfill_optimized_run.log

# Check process
ps -p $(cat logs/backfill_optimized_pid.txt)
```

**Why wait?** The backfill script is populating the WRONG columns:
- Currently populating: `weight`, `race_comment`, `jockey_silk_url` (duplicates to be dropped)
- Should populate: `weight_lbs`, `comment`, `silk_url` (primary columns)

**⚠️ CRITICAL:** Stop backfill once complete and update field mappings before restarting!

### Step 2: Update Backfill Script Field Mappings

**File:** `scripts/backfill_runners_optimized.py`

**Change field mappings from:**
```python
FIELD_MAPPINGS = [
    {'db_field': 'weight', 'api_field': 'weight_lbs', ...},  # WRONG
    {'db_field': 'race_comment', 'api_field': 'comment', ...},  # WRONG
    {'db_field': 'jockey_silk_url', 'api_field': 'silk_url', ...},  # WRONG
    ...
]
```

**To:**
```python
FIELD_MAPPINGS = [
    {'db_field': 'weight_lbs', 'api_field': 'weight_lbs', ...},  # CORRECT
    {'db_field': 'comment', 'api_field': 'comment', ...},  # CORRECT
    {'db_field': 'silk_url', 'api_field': 'silk_url', ...},  # CORRECT
    ...
]
```

### Step 3: Run Merge Script

Consolidate any data from duplicate columns into primary columns:

```bash
python3 scripts/merge_duplicate_columns.py --batch-size 25
```

**Expected output:**
- Merges weight → weight_lbs (for any NULL weight_lbs)
- Merges race_comment → comment (for any NULL comment)
- Merges jockey_silk_url → silk_url (for any NULL silk_url)

**Duration:** ~2-4 hours (depending on how many records need merging)

### Step 4: Run Migration to Drop Columns

```bash
# In Supabase SQL Editor, run:
migrations/016_drop_duplicate_columns.sql
```

**What it does:**
- Safety checks (errors if data would be lost)
- Drops: weight, race_comment, jockey_silk_url
- Verification (confirms columns dropped)

**Expected result:** 3 columns removed, ~50-100 MB storage saved

### Step 5: Update Fetchers

**File:** `fetchers/races_fetcher.py` (lines 100-134)

**Remove these duplicate assignments:**
```python
'weight': runner.get('weight_lbs'),  # DELETE
'race_comment': parse_text_field(runner.get('comment')),  # DELETE
'jockey_silk_url': parse_text_field(runner.get('silk_url')),  # DELETE
```

**Keep these primary assignments:**
```python
'weight_lbs': runner.get('weight_lbs'),  # KEEP
'comment': runner.get('comment'),  # KEEP
'silk_url': runner.get('silk_url'),  # KEEP
```

**Also check:** `fetchers/results_fetcher.py` for similar duplicates

### Step 6: Test

```bash
# Fetch small sample to verify only primary columns populated
python3 main.py --test --entities races
```

**Verify in database:**
- `weight_lbs`, `comment`, `silk_url` have data ✅
- `weight`, `race_comment`, `jockey_silk_url` columns don't exist ✅

## Expected Benefits

### Storage Savings
- **Columns eliminated:** 3
- **Cells eliminated:** ~3.9M (3 columns × 1.3M records)
- **Storage saved:** ~50-100 MB

### Performance Improvements
- Fewer columns to index and query
- Simpler schema reduces confusion
- Backfill scripts run faster

### Code Clarity
- Eliminates redundant field assignments in fetchers
- Clear naming convention (one column per field)
- Easier for developers to understand schema

## Current Status

- ✅ Analysis complete
- ✅ Scripts created (merge + migration)
- 🔄 **WAITING:** Backfill running (populating wrong columns)
- ⏸️ **PAUSED:** Cleanup until backfill completes and field mappings updated

## Risk Assessment

**Risk Level:** LOW

**Safeguards:**
1. Merge script runs BEFORE dropping columns (no data loss)
2. Migration has safety checks (errors if data would be lost)
3. Checkpoint/resume capability (can interrupt and restart)
4. Supabase automatic backups (can rollback if needed)

## Timeline

| Step | Duration | Status |
|------|----------|--------|
| 1. Analysis | 1 hour | ✅ Complete |
| 2. Script creation | 1 hour | ✅ Complete |
| 3. Wait for backfill | 4-6 hours | 🔄 In progress |
| 4. Update backfill mappings | 5 minutes | ⏸️ Waiting |
| 5. Run merge script | 2-4 hours | ⏸️ Waiting |
| 6. Run migration | 1 minute | ⏸️ Waiting |
| 7. Update fetchers | 10 minutes | ⏸️ Waiting |
| 8. Testing | 15 minutes | ⏸️ Waiting |
| **Total** | **8-12 hours** | **~20% complete** |

## Next Action

**WAIT** for current backfill to complete, then update field mappings in `scripts/backfill_runners_optimized.py` before proceeding with merge.

Monitor backfill progress:
```bash
tail -f logs/backfill_optimized_run.log
```
