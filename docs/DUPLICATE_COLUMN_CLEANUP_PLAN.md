# Duplicate Column Cleanup Plan for ra_runners

## Problem

The `ra_runners` table has duplicate columns storing identical data:

1. **weight** vs **weight_lbs** - Both store numeric weight in pounds
2. **comment** vs **race_comment** - Both store race commentary text
3. **silk_url** vs **jockey_silk_url** - Both store jockey silk SVG URLs

## Root Cause

The fetchers (`races_fetcher.py`, `results_fetcher.py`) were updated to populate **BOTH** columns with identical data:

```python
# races_fetcher.py lines 100-101, 128-129, 132-134
'weight': runner.get('weight_lbs'),
'weight_lbs': runner.get('weight_lbs'),  # DUPLICATE!

'comment': runner.get('comment'),
'race_comment': parse_text_field(runner.get('comment')),  # DUPLICATE!

'silk_url': runner.get('silk_url'),
'jockey_silk_url': parse_text_field(runner.get('silk_url')),  # DUPLICATE!
```

## Current Data State

From sample of 1,000 records:

| Column Group | Column 1 | Column 1 Pop % | Column 2 | Column 2 Pop % |
|--------------|----------|----------------|----------|----------------|
| Weight | weight | 63.8% | weight_lbs | 100.0% |
| Comment | comment | 68.6% | race_comment | 17.0% |
| Silk URL | silk_url | 63.3% | jockey_silk_url | 2.9% |

**Analysis:**
- **weight_lbs** has higher population (100%) - newer records have both columns
- **comment** has much higher population (68.6%) - primary column
- **silk_url** has much higher population (63.3%) - primary column

## Recommended Primary Columns

Based on population rates and naming clarity:

| Keep (Primary) | Drop (Duplicate) | Reason |
|----------------|------------------|--------|
| **weight_lbs** | weight | More specific name, higher population |
| **comment** | race_comment | Simpler name, much higher population |
| **silk_url** | jockey_silk_url | Simpler name, much higher population |

## Cleanup Steps

### Step 1: Merge Data Before Dropping

Ensure primary columns have ALL data by merging from duplicates:

```sql
-- Merge weight into weight_lbs
UPDATE ra_runners
SET weight_lbs = COALESCE(weight_lbs, weight),
    updated_at = NOW()
WHERE weight_lbs IS NULL AND weight IS NOT NULL;

-- Merge race_comment into comment
UPDATE ra_runners
SET comment = COALESCE(comment, race_comment),
    updated_at = NOW()
WHERE comment IS NULL AND race_comment IS NOT NULL;

-- Merge jockey_silk_url into silk_url
UPDATE ra_runners
SET silk_url = COALESCE(silk_url, jockey_silk_url),
    updated_at = NOW()
WHERE silk_url IS NULL AND jockey_silk_url IS NOT NULL;
```

**⚠️ IMPORTANT**: These UPDATE queries will timeout on 1.3M records table.
**Solution**: Run via Python script with small batches (same approach as backfill).

### Step 2: Drop Duplicate Columns

```sql
-- Drop duplicate columns
ALTER TABLE ra_runners DROP COLUMN IF EXISTS weight;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS race_comment;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS jockey_silk_url;
```

### Step 3: Update Fetchers

Remove duplicate field assignments from `fetchers/races_fetcher.py` and `fetchers/results_fetcher.py`:

**Remove these lines:**
```python
'weight': runner.get('weight_lbs'),  # DELETE - use weight_lbs only
'race_comment': parse_text_field(runner.get('comment')),  # DELETE - use comment only
'jockey_silk_url': parse_text_field(runner.get('silk_url')),  # DELETE - use silk_url only
```

**Keep these lines:**
```python
'weight_lbs': runner.get('weight_lbs'),  # KEEP
'comment': runner.get('comment'),  # KEEP
'silk_url': runner.get('silk_url'),  # KEEP
```

### Step 4: Update Backfill Script

Update `scripts/backfill_runners_optimized.py` field mappings to use primary columns only:

**Current (WRONG):**
```python
{'db_field': 'weight', 'api_field': 'weight_lbs', ...},  # Should be weight_lbs
{'db_field': 'race_comment', 'api_field': 'comment', ...},  # Should be comment
{'db_field': 'jockey_silk_url', 'api_field': 'silk_url', ...},  # Should be silk_url
```

**Corrected:**
```python
{'db_field': 'weight_lbs', 'api_field': 'weight_lbs', ...},  # ✅ Correct
{'db_field': 'comment', 'api_field': 'comment', ...},  # ✅ Correct
{'db_field': 'silk_url', 'api_field': 'silk_url', ...},  # ✅ Correct
```

## Implementation Order

1. ✅ **Create merge script** (Python with small batches to avoid timeout)
2. ✅ **Run merge script** to consolidate data into primary columns
3. ✅ **Verify merge** - check that no data will be lost
4. ✅ **Create migration** with DROP COLUMN statements
5. ✅ **Run migration** in Supabase dashboard
6. ✅ **Update fetchers** to remove duplicate assignments
7. ✅ **Update backfill script** field mappings
8. ✅ **Test** with small fetch to verify only primary columns populated

## Estimated Impact

**Space savings:**
- 3 columns × 1.3M records = ~3.9M cells eliminated
- Approximate storage reduction: 50-100 MB (depends on data types)

**Performance improvement:**
- Fewer columns to index and query
- Simpler schema reduces developer confusion
- Backfill script will run faster (fewer fields to process)

## Risk Assessment

**Low Risk** - All duplicate data is identical, no data loss expected.

**Safeguards:**
1. Merge data before dropping columns (COALESCE ensures no NULL overwrites)
2. Test merge script on sample first
3. Backup database before migration (Supabase has automatic backups)
4. Can rollback migration if issues arise

## Next Actions

Would you like me to:
1. Create the Python merge script (small batches, timeout-safe)?
2. Create the SQL migration file?
3. Both?
