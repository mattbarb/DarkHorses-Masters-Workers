# Visual Data Validation Guide

**Purpose:** Insert **TEST** markers into all database columns to visually verify that every field is being updated correctly.

**Status:** ✅ Production-Ready System
**Location:** `tests/test_schema_auto.py`
**Controller Integration:** `fetchers/master_fetcher_controller.py`

---

## Overview

This system provides **schema-aware test data insertion** that:
1. Reads the actual database schema from `docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json`
2. Generates appropriate test values for each column type
3. Inserts test rows with `**TEST**` markers
4. Allows visual verification that every column is populated
5. Provides automated cleanup to remove all test data

**Key Feature:** Uses REAL database schema, not hardcoded assumptions.

---

## Quick Start

### Insert Test Data (All Tables)

```bash
# Via controller (recommended - interactive mode)
python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive

# Via direct script
python3 tests/test_schema_auto.py
```

### Insert Test Data (Specific Tables)

```bash
# Via controller
python3 fetchers/master_fetcher_controller.py --mode test-auto --tables ra_mst_races ra_mst_runners --interactive

# Via direct script
python3 tests/test_schema_auto.py --tables ra_mst_horses ra_mst_races
```

### Cleanup Test Data

```bash
# Via controller
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive

# Via direct script
python3 tests/test_schema_auto.py --cleanup
```

### Complete Workflow (Insert → Verify → Cleanup)

```bash
# Full test workflow via controller
python3 fetchers/master_fetcher_controller.py --mode test-full --interactive
```

---

## How It Works

### 1. Schema-Aware Data Generation

The system reads column metadata and generates appropriate test values:

| Column Type | Test Value Generated | Example |
|-------------|---------------------|---------|
| Text/VARCHAR | `**TEST**` | `**TEST**` |
| Integer/BIGINT | `9999` | `9999` |
| Decimal/NUMERIC | `99.99` | `99.99` |
| Boolean | `True` | `true` |
| Date | `2099-12-31` | `2099-12-31` |
| Timestamp | `2099-12-31T23:59:59` | `2099-12-31T23:59:59` |
| JSON | `{"test": "**TEST**"}` | `{"test": "**TEST**"}` |

### 2. Smart Column Detection

The system detects column purpose by name and adjusts values:

- **ID columns** (`*_id`): `**TEST**_columnname_abc123`
- **Name columns** (`*_name`): `**TEST** Column Name`
- **Code columns** (`*_code`): `**TE**`
- **Timestamp columns**: `2099-12-31T23:59:59`

### 3. Test Marker

All string values include `**TEST**` making them:
- ✅ Easy to identify visually
- ✅ Easy to cleanup programmatically
- ✅ Distinguishable from real data

---

## Visual Verification Process

### Step 1: Insert Test Data

```bash
python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive
```

**Expected Output:**
```
================================================================================
SCHEMA-AWARE TEST DATA INSERTION
================================================================================

Inserting test data into: ra_mst_courses
  Generated test row with 15 columns
✅ Successfully inserted test row into ra_mst_courses

Inserting test data into: ra_mst_horses
  Generated test row with 23 columns
✅ Successfully inserted test row into ra_mst_horses

...

================================================================================
SCHEMA-AWARE TEST DATA INSERT SUMMARY
================================================================================

Tables Processed: 22
Successful: 22
Failed: 0
Total Columns Populated: 625

✅ Successful Insertions:
  - ra_mst_courses: 15 columns
  - ra_mst_horses: 23 columns
  - ra_mst_races: 45 columns
  - ra_mst_runners: 57 columns
  ...
```

### Step 2: Visual Verification in Supabase

**Open Supabase Table Editor:**
1. Go to your Supabase dashboard
2. Navigate to Table Editor
3. Select each table (e.g., `ra_mst_races`, `ra_mst_runners`)
4. Look for rows with `**TEST**` markers

**What to Look For:**
- ✅ **TEST** markers appear in text columns
- ✅ `9999` or `99.99` appear in numeric columns
- ✅ Future dates (`2099-12-31`) appear in date columns
- ✅ All columns have values (no NULLs unless column allows NULL)
- ❌ Any column that's empty indicates it's NOT being populated

### Step 3: Verify Column Coverage

**Run query to check all tables have test data:**
```sql
-- Check which tables have test data
SELECT
    table_name,
    (SELECT COUNT(*)
     FROM information_schema.columns c
     WHERE c.table_name = t.table_name) as total_columns,
    'Has test data' as status
FROM information_schema.tables t
WHERE table_schema = 'public'
  AND table_name LIKE 'ra_%'
ORDER BY table_name;
```

**Check specific table for test data:**
```sql
-- Example: Check ra_mst_runners for test data
SELECT * FROM ra_mst_runners
WHERE horse_name LIKE '%**TEST**%'
   OR jockey_name LIKE '%**TEST**%'
LIMIT 1;
```

### Step 4: Cleanup Test Data

```bash
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

**Expected Output:**
```
================================================================================
CLEANING TEST DATA FROM 22 TABLES
================================================================================

Cleaning test data from: ra_mst_courses
  Deleted 1 rows by course_name column

Cleaning test data from: ra_mst_horses
  Deleted 1 rows by horse_name column

...

================================================================================
SCHEMA-AWARE TEST DATA CLEANUP SUMMARY
================================================================================

Tables Processed: 22
Successful: 22
Failed: 0
Total Rows Deleted: 22
```

---

## Controller Modes

The `master_fetcher_controller.py` provides several test modes:

### 1. `test-auto` - Schema-Aware Insert

```bash
python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive
```

**What it does:**
- Reads database schema from JSON
- Generates appropriate test data for each column type
- Inserts one test row per table
- Shows summary of columns populated

**Use when:** You want to quickly verify all columns are being populated

---

### 2. `test-cleanup` - Remove Test Data

```bash
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

**What it does:**
- Searches all text columns for `**TEST**` markers
- Deletes matching rows from all tables
- Shows count of rows deleted per table

**Use when:** Cleaning up after visual verification

---

### 3. `test-full` - Complete Workflow

```bash
python3 fetchers/master_fetcher_controller.py --mode test-full --interactive
```

**What it does:**
1. Inserts test data into all tables
2. Analyzes table structure and data
3. Waits for manual verification
4. Cleans up all test data

**Use when:** Running comprehensive validation workflow

---

## Column Inventory Schema

The system uses `docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json` which contains:

```json
{
  "total_tables": 22,
  "total_columns": 625,
  "columns": [
    {
      "table": "ra_mst_races",
      "column": "race_id",
      "type": "character varying",
      "nullable": false,
      "source": "Racing API",
      "fetcher": "RacesFetcher",
      "endpoint": "/v1/racecards/pro"
    },
    ...
  ]
}
```

**Benefits:**
- ✅ Always uses CURRENT schema
- ✅ No hardcoded assumptions
- ✅ Automatically adapts to schema changes
- ✅ Knows exact data types for each column

---

## Verification Checklist

Use this checklist when visually reviewing test data:

### Master Tables

- [ ] `ra_mst_courses` - All 15 columns populated
- [ ] `ra_mst_bookmakers` - All columns populated
- [ ] `ra_mst_regions` - All columns populated
- [ ] `ra_mst_jockeys` - All person fields populated
- [ ] `ra_mst_trainers` - All person fields populated
- [ ] `ra_mst_owners` - All person fields populated
- [ ] `ra_mst_horses` - All 23 columns including pedigree IDs
- [ ] `ra_mst_sires` - All 47 statistics columns
- [ ] `ra_mst_dams` - All 47 statistics columns
- [ ] `ra_mst_damsires` - All 47 statistics columns

### Transaction Tables

- [ ] `ra_mst_races` - All 45 race metadata columns
- [ ] `ra_mst_runners` - All 57 runner columns including enhanced fields
- [ ] `ra_mst_race_results` - All 38 result columns
- [ ] `ra_horse_pedigree` - All lineage columns (sire, dam, damsire, breeder with IDs)

### Calculated Tables

- [ ] `ra_entity_combinations` - All combination fields
- [ ] `ra_runner_statistics` - All statistics columns
- [ ] `ra_performance_by_distance` - All distance performance fields
- [ ] `ra_performance_by_venue` - All venue performance fields

---

## Common Issues and Solutions

### Issue: "No schema data available"

**Cause:** Column inventory JSON file not found

**Solution:**
```bash
# Check if file exists
ls -la docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json

# If missing, generate it (if you have the generator script)
python3 scripts/analysis/generate_column_inventory.py
```

---

### Issue: "Insert succeeded but no data returned"

**Cause:** Supabase RLS policies may prevent reading after insert

**Solution:** This is just a warning - data was inserted. Verify in Supabase dashboard.

---

### Issue: Foreign key constraint violations

**Cause:** Test data for child tables references non-existent parent records

**Solution:** Insert test data in dependency order:
```bash
# First: Master tables
python3 tests/test_schema_auto.py --tables ra_mst_courses ra_mst_bookmakers ra_mst_jockeys ra_mst_trainers ra_mst_owners ra_mst_horses

# Then: Transaction tables
python3 tests/test_schema_auto.py --tables ra_mst_races ra_mst_runners ra_mst_race_results

# Finally: Calculated tables
python3 tests/test_schema_auto.py --tables ra_runner_statistics ra_performance_by_distance
```

---

### Issue: Some columns still NULL after test insert

**Cause:** Columns may have database-level DEFAULT values or be auto-generated

**Action:** This is expected for:
- Auto-increment `id` columns
- `created_at`/`updated_at` with database defaults
- Columns with `DEFAULT` constraints

---

## Advanced Usage

### Test Specific Column Coverage

```python
# Custom script to test specific columns
from tests.test_schema_auto import SchemaAwareTestInserter

inserter = SchemaAwareTestInserter()

# Create custom test row
test_row = inserter.create_test_row('ra_mst_runners')
print(f"Generated {len(test_row)} columns for ra_mst_runners")
print(test_row)

# Verify all required columns are present
required_columns = ['race_id', 'horse_id', 'position', 'starting_price_decimal', 'race_comment']
missing = [col for col in required_columns if col not in test_row]
if missing:
    print(f"Missing required columns: {missing}")
```

### Generate Test Data Report

```bash
# Insert test data and generate report
python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive > test_data_report.txt

# Review report
cat test_data_report.txt | grep "Successfully inserted"
```

### Verify Cleanup Was Complete

```sql
-- After cleanup, check for any remaining test data
SELECT table_name, COUNT(*) as test_rows
FROM (
    SELECT 'ra_mst_races' as table_name FROM ra_mst_races WHERE race_title LIKE '%**TEST**%'
    UNION ALL
    SELECT 'ra_mst_runners' FROM ra_mst_runners WHERE horse_name LIKE '%**TEST**%'
    UNION ALL
    SELECT 'ra_mst_horses' FROM ra_mst_horses WHERE horse_name LIKE '%**TEST**%'
    -- Add more tables as needed
) combined
GROUP BY table_name
HAVING COUNT(*) > 0;

-- Should return 0 rows if cleanup was successful
```

---

## Integration with Fetchers

### Before Running Fetchers

```bash
# 1. Insert test data
python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive

# 2. Run fetcher in test mode
python3 main.py --test --entities races

# 3. Verify test data was NOT overwritten
# Check that **TEST** markers still exist alongside real data

# 4. Cleanup
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

### After Schema Changes

```bash
# 1. Update column inventory (if generator exists)
python3 scripts/analysis/generate_column_inventory.py

# 2. Run test insertion to verify new columns
python3 tests/test_schema_auto.py

# 3. Check for any new columns that failed to populate
# Review summary output for failed insertions
```

---

## Best Practices

### DO ✅

- **Run test-auto before major deployments** to verify all columns populate
- **Visual review in Supabase** - automated checks can't catch everything
- **Test specific tables** after schema changes: `--tables ra_new_table`
- **Cleanup after verification** to avoid polluting database
- **Use interactive mode** for clearer output: `--interactive`

### DON'T ❌

- **Don't run in production** without cleanup immediately after
- **Don't assume test passed** if you didn't visually verify
- **Don't skip cleanup** - test data can interfere with real data
- **Don't modify test marker** - `**TEST**` is used for cleanup detection

---

## File Locations (After Reorganization)

```
tests/
├── test_schema_auto.py ← Main test insertion script
├── insert_test_data.py ← Legacy hardcoded test data
├── cleanup_test_data.py ← Test data cleanup utility
└── test_api_source.py ← API-based test data insertion

docs/
└── COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json ← Schema definition (625 columns)

fetchers/
└── master_fetcher_controller.py ← Integrated test modes
```

---

## Summary

This visual validation system provides a **reliable, schema-aware way** to verify that every database column is being populated correctly by:

1. ✅ Using REAL database schema (not assumptions)
2. ✅ Generating type-appropriate test values
3. ✅ Inserting visible `**TEST**` markers
4. ✅ Allowing manual visual verification
5. ✅ Providing automated cleanup

**Recommended workflow:**
```bash
# 1. Insert test data
python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive

# 2. Open Supabase dashboard and visually verify each table

# 3. Cleanup when done
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

This approach catches issues that automated tests might miss, like:
- Column mapping errors (right value, wrong column)
- Data type mismatches (strings in numeric fields)
- Truncation or formatting issues
- Null values in required fields

---

**Last Updated:** 2025-10-23
**Status:** Production-Ready
**Import Paths:** Updated for reorganized structure
**Column Inventory:** 625 columns across 22 tables
