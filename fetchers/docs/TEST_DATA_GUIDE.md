# Test Data Guide

**Script:** `fetchers/insert_test_data.py`
**Controller Modes:** `--mode test-insert` and `--mode test-cleanup`
**Purpose:** Insert test rows with **TEST** markers to verify all columns are being captured

---

## Overview

The Test Data system allows you to insert one test row into each of the 23 ra_ tables with **TEST** markers in every field. This is useful for:

1. **Verifying column capture** - Ensure all columns are accessible
2. **Testing fetchers** - Confirm fetchers are capturing all fields
3. **Data type validation** - Verify data types are correct
4. **Schema verification** - Check that no columns are being missed
5. **Integration testing** - Test end-to-end data flow

---

## Quick Start

### Insert Test Data

```bash
# Insert test data into all 23 tables (from controller)
python3 fetchers/master_fetcher_controller.py --mode test-insert --interactive

# Insert into specific tables
python3 fetchers/master_fetcher_controller.py --mode test-insert --tables ra_races ra_runners --interactive

# Standalone (all tables)
python3 fetchers/insert_test_data.py

# Standalone (specific tables)
python3 fetchers/insert_test_data.py --tables ra_mst_horses ra_horse_pedigree
```

### Clean Up Test Data

```bash
# Clean up test data from all tables (from controller)
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive

# Clean up specific tables
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --tables ra_races ra_runners --interactive

# Standalone
python3 fetchers/insert_test_data.py --cleanup
```

---

## What It Does

### Test Row Structure

**Each test row contains:**
- **TEST** markers in all text fields
- Test values (9999, 99.99, etc.) in numeric fields
- Future dates (2099-12-31) for date fields
- Unique IDs with `test_` prefix
- Easily identifiable patterns

**Example Test Row (ra_mst_horses):**
```json
{
  "horse_id": "test_abc12345_horse",
  "name": "**TEST** Horse Name test_abc12345",
  "sex": "**TEST**",
  "sex_code": "T",
  "dob": "2099-12-31",
  "colour": "**TEST**",
  "colour_code": "T",
  "region": "**TEST**",
  "sire_id": "test_abc12345_sire",
  "dam_id": "test_abc12345_dam",
  "damsire_id": "test_abc12345_damsire",
  "sire_name": "**TEST** Sire",
  "dam_name": "**TEST** Dam",
  "damsire_name": "**TEST** Damsire",
  "created_at": "2099-12-31T23:59:59",
  "updated_at": "2099-12-31T23:59:59"
}
```

### Tables Covered

**All 23 ra_ tables:**

**Master/Reference Tables (11):**
1. ra_mst_courses
2. ra_mst_bookmakers
3. ra_mst_regions
4. ra_mst_jockeys
5. ra_mst_trainers
6. ra_mst_owners
7. ra_mst_horses
8. ra_mst_sires
9. ra_mst_dams
10. ra_mst_damsires
11. ra_horse_pedigree

**Transaction Tables (3):**
12. ra_races
13. ra_runners
14. ra_race_results

**Future/Partial Tables (9):**
15. ra_entity_combinations
16. ra_performance_by_distance
17. ra_performance_by_venue
18. ra_runner_statistics
19. ra_runner_supplementary
20. ra_odds_live
21. ra_odds_historical
22. ra_odds_statistics
23. ra_runner_odds

---

## Use Cases

### 1. Verify All Columns Are Captured

**Scenario:** After updating a fetcher, verify it captures all columns

**Workflow:**
```bash
# 1. Insert test data
python3 fetchers/master_fetcher_controller.py --mode test-insert --interactive

# 2. Run analysis to see which columns are populated
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive

# 3. Check for any empty columns
# Review analysis output for columns with 0% population

# 4. Clean up
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

### 2. Test Schema Changes

**Scenario:** After adding new columns, verify they're accessible

**Workflow:**
```bash
# 1. Insert test data into affected table
python3 fetchers/insert_test_data.py --tables ra_runners

# 2. Query to verify new columns
# Check database directly or use analysis

# 3. Clean up
python3 fetchers/insert_test_data.py --cleanup --tables ra_runners
```

### 3. Integration Testing

**Scenario:** Test end-to-end data flow

**Workflow:**
```bash
# 1. Insert test data
python3 fetchers/master_fetcher_controller.py --mode test-insert

# 2. Run fetchers (they should not overwrite test data)
python3 fetchers/master_fetcher_controller.py --mode daily --test

# 3. Verify test data still exists
# Query for rows with **TEST** markers

# 4. Clean up
python3 fetchers/master_fetcher_controller.py --mode test-cleanup
```

### 4. Column Mapping Verification

**Scenario:** Verify column mappings in COMPLETE_COLUMN_INVENTORY

**Workflow:**
```bash
# 1. Insert test data
python3 fetchers/master_fetcher_controller.py --mode test-insert

# 2. Check which columns got populated
python3 fetchers/master_fetcher_controller.py --mode analyze

# 3. Compare with COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json
# Verify all columns listed in inventory are accessible

# 4. Update inventory if needed

# 5. Clean up
python3 fetchers/master_fetcher_controller.py --mode test-cleanup
```

---

## Output

### Insert Summary

```
================================================================================
TEST DATA INSERT SUMMARY
================================================================================

Tables Processed: 23
Successful: 21
Failed: 2

❌ Failed Tables:
  - ra_odds_live: relation "ra_odds_live" does not exist
  - ra_odds_historical: relation "ra_odds_historical" does not exist

================================================================================
```

### Cleanup Summary

```
================================================================================
TEST DATA CLEANUP SUMMARY
================================================================================

Tables Processed: 23
Successful: 23
Failed: 0
Total Rows Deleted: 23

================================================================================
```

---

## How It Works

### Insertion Logic

**For Each Table:**
1. Generate test data specific to that table's schema
2. Include **TEST** markers in all text/varchar fields
3. Use test values (9999, 99.99) for numeric fields
4. Use future dates (2099-12-31) for date fields
5. Use unique IDs with `test_` prefix
6. Insert via Supabase client
7. Report success/failure

**Test Data Templates:**
- Each table has a custom test data template
- Templates match the actual column structure
- All required fields are populated
- Optional fields are populated where possible

### Cleanup Logic

**For Each Table:**
1. Delete rows where `name` contains `**TEST**`
2. Delete rows where `id` contains `**TEST**`
3. Delete rows where ID fields contain `test_`
4. Delete rows where common ID fields match test pattern
5. Report total rows deleted

**Cleanup Patterns:**
- `name LIKE '%**TEST**%'`
- `id LIKE '%**TEST**%'`
- `horse_id LIKE '%test_%'`
- `race_id LIKE '%test_%'`
- And other common ID fields

---

## Safety Features

### Insert Safety

✅ **Unique IDs** - Test IDs are unique and don't conflict with real data
✅ **Future Dates** - Uses 2099 dates so won't interfere with temporal queries
✅ **Clear Markers** - **TEST** markers make it obvious these are test rows
✅ **No Overwrites** - Inserts new rows, doesn't update existing data

### Cleanup Safety

✅ **Pattern Matching** - Only deletes rows matching test patterns
✅ **Multiple Checks** - Checks multiple fields to ensure it's test data
✅ **No Wildcards** - Doesn't use broad wildcards that could match real data
✅ **Reports Deleted** - Shows exactly how many rows were deleted

---

## Common Issues & Solutions

### Issue: Insert Fails for Some Tables

**Possible Causes:**
1. Table doesn't exist yet (future/TBD tables)
2. Missing required columns
3. Data type mismatch
4. Foreign key constraints

**Solutions:**
1. Check table exists: `\dt ra_*` in psql
2. Review table schema
3. Update test data template for that table
4. Disable constraints temporarily (not recommended)

### Issue: Cleanup Doesn't Remove All Test Rows

**Possible Causes:**
1. Test data doesn't match cleanup patterns
2. Column names different from expected
3. Test rows modified after insertion

**Solutions:**
1. Check test row structure
2. Add additional cleanup patterns for that table
3. Manual cleanup via SQL: `DELETE FROM table WHERE name LIKE '%**TEST**%'`

### Issue: Test Data Interferes with Fetchers

**Problem:** Fetchers try to update test rows

**Solution:**
- Fetchers use UPSERT with primary keys
- Test rows have unique IDs that won't match API data
- No interference should occur
- Clean up test data if needed

---

## Integration with Analysis

**Combined Workflow:**

```bash
# 1. Insert test data to all tables
python3 fetchers/master_fetcher_controller.py --mode test-insert --interactive

# 2. Run comprehensive analysis
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive

# 3. Review results:
#    - Check if all columns show at least 1 row populated
#    - Identify any columns with 0% population
#    - These are columns NOT being captured

# 4. Clean up test data
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

**What To Look For:**
- Columns with 0% population after test insert → NOT captured
- Columns with very low % → Rarely populated (check if expected)
- Columns with 100% → Fully captured (good!)

---

## Best Practices

### DO

✅ Insert test data before major deployments
✅ Clean up test data after testing
✅ Use test data to verify schema changes
✅ Combine with analysis for comprehensive checks
✅ Keep test data short-lived (hours, not days)

### DON'T

❌ Leave test data in production for extended periods
❌ Rely on test data for production queries
❌ Modify test data after insertion (breaks cleanup)
❌ Use test data patterns in real data (**TEST** markers)
❌ Run test insert on production without cleanup plan

---

## Automation

### Pre-Deployment Check

```bash
#!/bin/bash
# Pre-deployment verification script

echo "Inserting test data..."
python3 fetchers/master_fetcher_controller.py --mode test-insert

echo "Running analysis..."
python3 fetchers/master_fetcher_controller.py --mode analyze

echo "Checking for empty columns..."
# Parse JSON to find columns with 0% population

echo "Cleaning up..."
python3 fetchers/master_fetcher_controller.py --mode test-cleanup

echo "Pre-deployment check complete!"
```

### Scheduled Verification

```bash
# Weekly schema verification (Sundays at 4am)
0 4 * * 0 cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode test-insert && python3 fetchers/master_fetcher_controller.py --mode analyze && python3 fetchers/master_fetcher_controller.py --mode test-cleanup >> logs/weekly_test.log 2>&1
```

---

## Troubleshooting

### Error: "relation does not exist"

**Cause:** Table hasn't been created yet

**Solution:**
- Skip that table (it's a future/TBD table)
- Create the table if needed
- Remove from test list if not implemented

### Error: "duplicate key value violates unique constraint"

**Cause:** Test row with same ID already exists

**Solution:**
- Run cleanup first: `--mode test-cleanup`
- IDs include random UUID, so shouldn't happen often
- Delete manually if needed

### Warning: "No data returned after insert"

**Cause:** Insert succeeded but no data in response

**Solution:**
- Usually harmless (Supabase behavior)
- Check database to verify row exists
- If row exists, it's successful

---

## Related Documentation

- **[TABLE_ANALYSIS_GUIDE.md](TABLE_ANALYSIS_GUIDE.md)** - Comprehensive table analysis
- **[COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json](COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json)** - All columns with sources
- **[TABLE_TO_SCRIPT_MAPPING.md](TABLE_TO_SCRIPT_MAPPING.md)** - Which fetcher populates which table

---

## Examples

### Example 1: Verify Horses Table

```bash
# Insert test data into horses table
python3 fetchers/insert_test_data.py --tables ra_mst_horses

# Check what was inserted
psql -h ... -c "SELECT * FROM ra_mst_horses WHERE name LIKE '%**TEST**%';"

# Verify all columns populated
python3 fetchers/analyze_tables.py --tables ra_mst_horses

# Clean up
python3 fetchers/insert_test_data.py --cleanup --tables ra_mst_horses
```

### Example 2: Full System Test

```bash
# Full workflow
python3 fetchers/master_fetcher_controller.py --mode test-insert --interactive && \
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive && \
python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive
```

### Example 3: Check Specific Columns

```bash
# Insert test data
python3 fetchers/insert_test_data.py --tables ra_runners

# Query specific columns
psql -h ... -c "
SELECT
  race_comment,
  starting_price_decimal,
  jockey_silk_url,
  weight_stones_lbs
FROM ra_runners
WHERE horse_name LIKE '%**TEST**%';
"

# Clean up
python3 fetchers/insert_test_data.py --cleanup --tables ra_runners
```

---

## Summary

**The test data system provides:**

✅ Quick verification that all columns are accessible
✅ Easy schema change validation
✅ Integration testing capabilities
✅ Column mapping verification
✅ Safe insertion and cleanup
✅ Controller integration for easy use

**Use it for:**
- Pre-deployment checks
- Schema change verification
- Column capture validation
- Integration testing
- Documentation validation

---

**Last Updated:** 2025-10-21
**Version:** v1.0
**Maintainer:** DarkHorses-Masters-Workers Team
