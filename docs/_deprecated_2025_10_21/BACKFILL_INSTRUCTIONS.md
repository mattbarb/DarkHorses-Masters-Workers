# Backfill Instructions - Fix NULL Fields in ra_runners

**Purpose:** Extract correct field values from `api_data` JSONB column to populate NULL fields in `ra_runners` table

**Affected Records:** ~1,325,718 runners
**Fields to Fix:** 13 fields (weight, form, finishing_time, starting_price_decimal, etc.)

---

## Quick Start

### 1. Test First (DRY RUN - Recommended)
```bash
# Test with 100 records to verify the script works
python3 scripts/backfill_runners_field_mapping.py --test --dry-run
```

This will:
- Process only 100 records
- Show what WOULD be updated without actually updating
- Give you a preview of the changes

### 2. Small Test (Actual Updates)
```bash
# Update 100 records for real
python3 scripts/backfill_runners_field_mapping.py --test
```

### 3. Verify Test Results
```sql
-- Check if fields are now populated for test records
SELECT
  runner_id,
  weight,
  form,
  finishing_time,
  starting_price_decimal,
  race_comment
FROM ra_runners
WHERE weight IS NOT NULL
LIMIT 10;
```

### 4. Full Backfill (1.3M Records)
```bash
# Process all records (will take ~20-30 minutes)
python3 scripts/backfill_runners_field_mapping.py --batch-size 1000
```

---

## Command Options

```bash
python3 scripts/backfill_runners_field_mapping.py [OPTIONS]

Options:
  --batch-size N    Process N records per batch (default: 1000)
  --limit N         Limit total records to process (default: None = all)
  --dry-run         Show what would be updated without updating
  --test            Test mode: limit to 100 records
  -h, --help        Show help message
```

### Examples:

```bash
# Dry run first 1000 records
python3 scripts/backfill_runners_field_mapping.py --limit 1000 --dry-run

# Update first 5000 records
python3 scripts/backfill_runners_field_mapping.py --limit 5000

# Full backfill with larger batch size (faster but more memory)
python3 scripts/backfill_runners_field_mapping.py --batch-size 5000

# Full backfill (all 1.3M records, default batch size)
python3 scripts/backfill_runners_field_mapping.py
```

---

## What Gets Updated

The script extracts data from `api_data` JSONB and populates these fields:

| Field | Source in api_data | Example Value |
|-------|-------------------|---------------|
| `weight` | `weight_lbs` | 134 |
| `weight_lbs` | `weight_lbs` | 134 |
| `form` | `form_string` | "225470" |
| `form_string` | `form_string` | "225470" |
| `prize_money_won` | `prize` | "28012.50" |
| `comment` | `comment` | "Led - ridden clear..." |
| `silk_url` | `silk_url` | "https://..." |
| **Migration 011 Fields:** | | |
| `finishing_time` | `time` | "1:15.23" |
| `starting_price_decimal` | `sp_dec` | 4.50 |
| `overall_beaten_distance` | `ovr_btn` | 3.75 |
| `jockey_claim_lbs` | `jockey_claim_lbs` | 0 or 7 |
| `weight_stones_lbs` | `weight` | "9-8" |
| `race_comment` | `comment` | "Led - ridden clear..." |
| `jockey_silk_url` | `silk_url` | "https://..." |

---

## Performance Estimates

| Records | Batch Size | Estimated Time |
|---------|-----------|----------------|
| 100 | 100 | < 1 minute |
| 1,000 | 1000 | 1-2 minutes |
| 10,000 | 1000 | 10-15 minutes |
| 1,325,718 | 1000 | 20-30 minutes |
| 1,325,718 | 5000 | 10-15 minutes |

**Note:** Times depend on network latency to Supabase and API rate limits.

---

## Monitoring Progress

The script outputs real-time progress:

```
Processing batch 1: records 0 to 1,000
Fetched 1000 runners
Updating 997 runners...
Batch complete. Processed: 1,000, Updated: 997, Skipped: 3

Processing batch 2: records 1,000 to 2,000
...
```

### Output Files

Results are saved to `logs/backfill_runners_field_mapping_TIMESTAMP.json`:

```json
{
  "total_processed": 1325718,
  "total_updated": 1320450,
  "total_skipped": 5268,
  "fields_updated": {
    "weight": 1320450,
    "form": 950320,
    "finishing_time": 1320450,
    "starting_price_decimal": 1320450,
    ...
  },
  "errors": []
}
```

---

## Verification After Backfill

### Check Field Population Rates
```sql
SELECT
  COUNT(*) as total_rows,
  COUNT(weight) as weight_populated,
  COUNT(form) as form_populated,
  COUNT(finishing_time) as finishing_time_populated,
  COUNT(starting_price_decimal) as starting_price_decimal_populated,
  ROUND(COUNT(weight)::numeric / COUNT(*)::numeric * 100, 2) as weight_pct,
  ROUND(COUNT(form)::numeric / COUNT(*)::numeric * 100, 2) as form_pct,
  ROUND(COUNT(finishing_time)::numeric / COUNT(*)::numeric * 100, 2) as finishing_time_pct,
  ROUND(COUNT(starting_price_decimal)::numeric / COUNT(*)::numeric * 100, 2) as starting_price_decimal_pct
FROM ra_runners;
```

**Expected Results:**
- `weight`: ~99% (only NULL if API didn't provide)
- `form`: ~70% (not always available in API)
- `finishing_time`: ~99% (results only)
- `starting_price_decimal`: ~99%
- All Migration 011 fields: ~90-99%

### Sample Data Check
```sql
-- View sample of updated data
SELECT
  runner_id,
  horse_name,
  weight,
  form,
  finishing_time,
  starting_price_decimal,
  race_comment,
  jockey_silk_url
FROM ra_runners
WHERE weight IS NOT NULL
ORDER BY created_at DESC
LIMIT 10;
```

---

## Troubleshooting

### Issue: Script times out
**Solution:** Reduce batch size:
```bash
python3 scripts/backfill_runners_field_mapping.py --batch-size 500
```

### Issue: Some fields still NULL after backfill
**Cause:** API didn't provide that data for those specific runners
**Solution:** This is expected. Check api_data directly:
```sql
SELECT runner_id, api_data FROM ra_runners WHERE weight IS NULL LIMIT 5;
```

### Issue: Errors during update
**Cause:** Network issues, database timeouts, or invalid data
**Solution:** Check error log in output JSON file, re-run backfill (it will update any remaining NULL fields)

---

## Safety Features

✅ **Read-only for api_data:** Original API data is never modified
✅ **Idempotent:** Safe to run multiple times (will only update NULL fields)
✅ **Dry-run mode:** Test before making changes
✅ **Batch processing:** Prevents memory issues with large dataset
✅ **Error logging:** All errors captured and logged
✅ **Statistics tracking:** Complete audit trail of all changes

---

## Re-running After Errors

If the backfill stops or errors occur, you can safely re-run:

```bash
# Re-run will only update fields that are still NULL
python3 scripts/backfill_runners_field_mapping.py
```

The script will:
- Skip records already updated
- Only process remaining NULL fields
- Continue from where it left off

---

## After Successful Backfill

1. ✅ Verify field population rates (see SQL above)
2. ✅ Test ML models with new data
3. ✅ Update CLAUDE.md with backfill completion date
4. ✅ Schedule future fetches to use updated fetchers
5. ✅ Consider Migration 012 to remove duplicate columns

---

## Questions?

Review these files:
- `FIELD_MAPPING_FIXES_SUMMARY.md` - Complete technical details
- `scripts/backfill_runners_field_mapping.py` - The backfill script source
- `logs/backfill_runners_field_mapping_*.json` - Execution results

---

**Ready to start?**

```bash
# Step 1: Dry run test
python3 scripts/backfill_runners_field_mapping.py --test --dry-run

# Step 2: Real test
python3 scripts/backfill_runners_field_mapping.py --test

# Step 3: Full backfill
python3 scripts/backfill_runners_field_mapping.py
```

🎉 Good luck!
