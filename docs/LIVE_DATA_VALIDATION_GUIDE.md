# Live Data Validation with **TEST** Markers

**Purpose:** Fetch REAL data from Racing API, add `**TEST**` markers, and verify the complete pipeline works end-to-end.

**Status:** ✅ Production-Ready
**Location:** `tests/test_live_data_with_markers.py`

---

## Why This Approach?

Unlike schema-based test insertion (which uses hardcoded values), this approach:

1. ✅ **Fetches REAL data** from Racing API
2. ✅ **Uses REAL transformation logic** from fetchers
3. ✅ **Tests COMPLETE pipeline** (API → Transform → Database)
4. ✅ **Adds visual markers** (`**TEST**`) to every field
5. ✅ **Verifies end-to-end** that all columns are populated correctly
6. ✅ **Easy cleanup** - delete all rows with `**TEST**`

**This tests the ACTUAL production code path**, not fake/mock data.

---

## Quick Start

### 1. Fetch Live Data with TEST Markers

```bash
# Fetch yesterday's races and add **TEST** markers
python3 tests/test_live_data_with_markers.py
```

**What happens:**
- Fetches REAL races from Racing API (yesterday's date)
- Uses production RacesFetcher code
- Extracts entities (horses, jockeys, trainers, owners)
- Inserts into database
- Adds `**TEST**` marker to every single field
- Shows summary of what was marked

**Expected output:**
```
================================================================================
FETCHING REAL RACES DATA WITH **TEST** MARKERS
================================================================================

Fetching races for date: 2025-10-22

✅ Fetched 127 races from Racing API

Adding **TEST** markers to fetched data...
  ✅ Marked race: 12345 - **TEST** 3:45 Cheltenham 2m Hurdle
  ✅ Marked race: 12346 - **TEST** 4:20 Newmarket 1m Maiden
  ...

================================================================================
SUMMARY:
================================================================================
Races marked with **TEST**: 5
Runners marked with **TEST**: 67
Total marked: 72

Now open Supabase and verify:
1. Check ra_races table - look for **TEST** in all columns
2. Check ra_runners table - look for **TEST** in all columns
3. Every column should show **TEST** marker
================================================================================
```

### 2. Visual Verification in Supabase

**Open Supabase Table Editor:**
1. Navigate to `ra_races` table
2. Find rows with `**TEST**` in race_title
3. Click to view details
4. **Verify EVERY column shows `**TEST**` marker**

**Example row you'll see:**
```
race_id:              "**TEST** 12345"
race_title:           "**TEST** 3:45 Cheltenham 2m Hurdle"
course_name:          "**TEST** Cheltenham"
race_class:           "**TEST** 2"
distance_yards:       "**TEST** 4400"
going:                "**TEST** Good to Soft"
prize_money:          "**TEST** 15000.00"
number_of_runners:    "**TEST** 14"
race_type:            "**TEST** Hurdle"
age_band:             "**TEST** 4yo+"
... (all 45 columns show **TEST**)
```

### 3. Check Runners Table

**Navigate to `ra_runners` table:**
```
horse_name:             "**TEST** Dancing King"
jockey_name:            "**TEST** A P McCoy"
trainer_name:           "**TEST** W P Mullins"
weight:                 "**TEST** 11.7"
position:               "**TEST** 1"
starting_price_decimal: "**TEST** 7.5"
race_comment:           "**TEST** tracked leaders, led 2 out, ran on"
... (all 57 columns show **TEST**)
```

### 4. Cleanup When Done

```bash
# Remove all **TEST** data
python3 tests/test_live_data_with_markers.py --cleanup
```

**Expected output:**
```
================================================================================
CLEANING UP **TEST** DATA
================================================================================

Cleaning ra_runners...
  ✅ Deleted 67 rows from ra_runners
Cleaning ra_race_results...
  ℹ️  No test data found in ra_race_results
Cleaning ra_races...
  ✅ Deleted 5 rows from ra_races
Cleaning ra_mst_horses...
  ✅ Deleted 67 rows from ra_mst_horses
...

================================================================================
CLEANUP SUMMARY:
================================================================================
Tables cleaned: 4
Total rows deleted: 144
================================================================================
```

---

## How It Works

### Step 1: Fetch Real Data

```python
# Uses production RacesFetcher
races_fetcher = RacesFetcher()

# Fetch yesterday's races (guaranteed data)
result = races_fetcher.fetch_and_store(
    region_codes=['gb', 'ire'],
    days_back=1,
    max_days=1
)

# This uses:
# - Real Racing API endpoint (/v1/racecards/pro)
# - Real transformation logic
# - Real entity extraction
# - Real database insertion
```

### Step 2: Add TEST Markers

```python
def add_test_markers_to_value(value, field_name):
    """Add **TEST** marker to any value type"""

    if isinstance(value, str):
        return f"**TEST** {value}"

    elif isinstance(value, (int, float)):
        return f"**TEST** {value}"

    elif isinstance(value, bool):
        return f"**TEST** {value}"

    # ... handles all types
```

### Step 3: Update Database

```python
# Add markers to race
marked_race = add_test_markers_to_record(race)

# Update in database
db.table('ra_races').update(marked_race).eq('race_id', race_id).execute()

# Same for runners, entities, etc.
```

### Step 4: Visual Verification

**Open Supabase → See `**TEST**` in EVERY column**

If any column is missing `**TEST**`:
- ❌ That column is NOT being populated by the fetcher
- ❌ There's a bug in the transformation logic
- ❌ The field might be missing from the API response

---

## What This Tests

### ✅ Complete Production Pipeline

1. **API Fetch** - Tests actual Racing API endpoint
2. **Response Parsing** - Tests JSON parsing logic
3. **Data Transformation** - Tests field mapping
4. **Entity Extraction** - Tests automatic entity discovery
5. **Database Insertion** - Tests Supabase insertion
6. **All Columns** - Tests every single field is populated

### ✅ Real Data Scenarios

- Real race titles (not "Test Race")
- Real horse names (not "Test Horse")
- Real numeric values (not just 9999)
- Real dates (not just 2099-12-31)
- Real API response structure

### ✅ Edge Cases

- Null/missing fields in API response
- Different data types
- Optional vs required fields
- Foreign key relationships
- Complex nested data

---

## Advanced Usage

### Test Specific Date

```bash
# Test data from 3 days ago
python3 tests/test_live_data_with_markers.py --days-back 3
```

### Test Different Entities

The script can be extended to test other entities:

```python
# Add methods for:
# - fetch_and_insert_results()
# - fetch_and_insert_courses()
# - fetch_and_insert_horses()
```

### Verify Specific Tables

```sql
-- Check which tables have test data
SELECT
    'ra_races' as table_name,
    COUNT(*) as test_rows
FROM ra_races
WHERE race_title LIKE '%**TEST**%'

UNION ALL

SELECT
    'ra_runners',
    COUNT(*)
FROM ra_runners
WHERE horse_name LIKE '%**TEST**%'

UNION ALL

SELECT
    'ra_mst_horses',
    COUNT(*)
FROM ra_mst_horses
WHERE horse_name LIKE '%**TEST**%';
```

---

## Comparison: Live vs Schema-Based Testing

| Aspect | Live Data Test | Schema-Based Test |
|--------|----------------|-------------------|
| **Data Source** | Real Racing API | Hardcoded values |
| **Tests Production Code** | ✅ Yes | ⚠️ Partial |
| **Tests API Integration** | ✅ Yes | ❌ No |
| **Tests Transformations** | ✅ Yes | ❌ No |
| **Tests All Columns** | ✅ Yes | ✅ Yes |
| **Requires API Access** | ✅ Yes | ❌ No |
| **Speed** | Slower (API call) | Faster (no API) |
| **Use Case** | End-to-end validation | Schema verification |

**Recommendation:** Use BOTH
1. **Live Data Test** - Before deployment, verify production pipeline
2. **Schema-Based Test** - Quick verification after schema changes

---

## Best Practices

### DO ✅

- **Run before major deployments** to verify complete pipeline
- **Use yesterday's data** (--days-back 1) - guaranteed to have results
- **Visual verification** in Supabase - automated checks can't see everything
- **Cleanup immediately** after verification
- **Test all entity types** (races, results, horses, etc.)

### DON'T ❌

- **Don't run in production** without cleanup
- **Don't use today's date** - races might not have run yet
- **Don't skip visual check** - that's the whole point!
- **Don't assume test passed** just because it ran without errors
- **Don't leave test data** - cleanup after every test

---

## Troubleshooting

### Issue: "No races found in database to mark"

**Cause:** Fetcher didn't insert any races

**Solutions:**
1. Check API credentials are valid
2. Verify date has races (use --days-back 1 for yesterday)
3. Check fetcher logs for errors
4. Verify region codes are correct (['gb', 'ire'])

---

### Issue: Some columns don't show **TEST**

**Cause:** Those columns aren't being populated by the fetcher

**Investigation:**
1. Check API response - is field present?
2. Check transformation logic - is field mapped?
3. Check column name - does it match database?
4. Check fetcher code - is field included in insert?

---

### Issue: Cleanup doesn't remove all rows

**Cause:** Table not included in cleanup list

**Solution:**
Add table to `tables_to_clean` in cleanup method:
```python
tables_to_clean = [
    ('ra_runners', 'horse_name'),
    ('ra_races', 'race_title'),
    ('your_new_table', 'some_text_column'),  # Add here
]
```

---

## Integration with Controller

**Future Enhancement:** Add to master_fetcher_controller.py

```bash
# Add new mode: test-live
python3 fetchers/master_fetcher_controller.py --mode test-live --interactive

# What it would do:
# 1. Fetch live data
# 2. Add TEST markers
# 3. Show summary
# 4. Wait for user verification
# 5. Cleanup
```

---

## Example Workflow

### Pre-Deployment Validation

```bash
# 1. Fetch live data with markers
python3 tests/test_live_data_with_markers.py

# Output:
# ✅ Fetched 127 races from Racing API
# ✅ Races marked with **TEST**: 5
# ✅ Runners marked with **TEST**: 67

# 2. Open Supabase
# - Check ra_races table
# - Find rows with **TEST** in race_title
# - Verify ALL 45 columns show **TEST**

# 3. Check ra_runners table
# - Find rows with **TEST** in horse_name
# - Verify ALL 57 columns show **TEST**

# 4. If everything looks good, cleanup
python3 tests/test_live_data_with_markers.py --cleanup

# Output:
# ✅ Cleanup complete: 144 rows deleted

# 5. Deploy with confidence!
```

### After Code Changes

```bash
# Made changes to RacesFetcher transformation logic

# 1. Test with live data
python3 tests/test_live_data_with_markers.py

# 2. Verify new/changed columns show **TEST**

# 3. Cleanup
python3 tests/test_live_data_with_markers.py --cleanup
```

---

## What You'll See in Supabase

### ra_races Table (45 columns)

```
✅ race_id:              "**TEST** 67890"
✅ race_title:           "**TEST** 3:45 Cheltenham 2m Hurdle"
✅ race_date:            "**TEST** 2025-10-22"
✅ race_time:            "**TEST** 15:45"
✅ course_id:            "**TEST** 39"
✅ course_name:          "**TEST** Cheltenham"
✅ race_class:           "**TEST** 2"
✅ distance_yards:       "**TEST** 4400"
✅ distance_furlongs:    "**TEST** 22"
✅ going:                "**TEST** Good to Soft"
✅ prize_money:          "**TEST** 15000.00"
✅ race_type:            "**TEST** Hurdle"
✅ age_band:             "**TEST** 4yo+"
... (all 45 columns)
```

### ra_runners Table (57 columns)

```
✅ race_id:              "**TEST** 67890"
✅ horse_id:             "**TEST** 123456"
✅ horse_name:           "**TEST** Dancing King"
✅ jockey_id:            "**TEST** 789"
✅ jockey_name:          "**TEST** A P McCoy"
✅ trainer_id:           "**TEST** 456"
✅ trainer_name:         "**TEST** W P Mullins"
✅ weight:               "**TEST** 11.7"
✅ draw:                 "**TEST** 5"
✅ position:             "**TEST** 1"
✅ starting_price:       "**TEST** 7/2"
✅ starting_price_decimal: "**TEST** 4.5"
✅ race_comment:         "**TEST** tracked leaders, led 2 out, ran on"
✅ jockey_silk_url:      "**TEST** https://..."
... (all 57 columns)
```

**Every. Single. Column. Shows. **TEST****

If any column is blank or missing **TEST** → That column has a problem!

---

## Summary

This live data validation approach provides the **most comprehensive end-to-end testing** possible:

1. ✅ **Real API data** - Not fake/mock data
2. ✅ **Real code path** - Production fetchers, transformers, inserters
3. ✅ **Visual verification** - See every column populated
4. ✅ **Easy identification** - **TEST** marker in all fields
5. ✅ **Easy cleanup** - One command removes all test data

**Recommended Usage:**
- Run before every major deployment
- Run after code changes to fetchers
- Run after schema changes
- Run periodically to verify data quality

**Command:**
```bash
python3 tests/test_live_data_with_markers.py
```

**Then:** Open Supabase and verify every column shows `**TEST**`

**Finally:**
```bash
python3 tests/test_live_data_with_markers.py --cleanup
```

---

**Last Updated:** 2025-10-23
**Status:** Production-Ready
**Tests:** Complete pipeline (API → Database)
**Visual Markers:** `**TEST**` in all columns
