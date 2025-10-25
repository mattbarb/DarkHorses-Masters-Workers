# API-Source Test Data Guide

**Script:** `fetchers/test_api_source.py`
**Controller Modes:** `--mode test-api` and `--mode test-api-cleanup`
**Purpose:** Insert REAL data from Racing API marked as TEST to verify all columns are being captured

---

## Overview

The API-Source Test system fetches **REAL data** from the Racing API endpoints, marks it with **TEST** identifiers, and inserts it into the database. This is the **CORRECT** way to verify that fetchers are capturing ALL columns from actual API responses.

**Key Difference from Other Test Modes:**
- `test-insert`: Uses hardcoded synthetic data (❌ Wrong - doesn't match actual schema)
- `test-auto`: Generates synthetic data based on schema (⚠️ Better - but not real API data)
- **`test-api`**: Fetches REAL API data and marks as TEST (✅ **RECOMMENDED** - tests actual pipeline)

---

## Why Use Real API Data?

1. **Validates Actual Column Capture:** Ensures fetchers extract ALL fields from real API responses
2. **Tests Real Data Types:** Verifies data types match what API actually returns
3. **Validates Transformations:** Confirms field mappings work with real data structure
4. **Catches API Changes:** Detects if API response format has changed
5. **Production-Like Testing:** Uses the same data pipeline as production

---

## Quick Start

### Insert Real API Test Data

```bash
# Insert test data from Racing API (from controller)
python3 fetchers/master_fetcher_controller.py --mode test-api --interactive

# Insert into specific tables
python3 fetchers/master_fetcher_controller.py --mode test-api --tables ra_mst_horses ra_races --interactive

# Standalone (all supported tables)
python3 fetchers/test_api_source.py

# Standalone (specific tables)
python3 fetchers/test_api_source.py --tables ra_mst_courses ra_mst_jockeys
```

### Clean Up API-Source Test Data

```bash
# Clean up test data from all tables (from controller)
python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --interactive

# Clean up specific tables
python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --tables ra_races ra_runners --interactive

# Standalone
python3 fetchers/test_api_source.py --cleanup
```

---

## What It Does

### Data Sourcing Strategy

**For Each Table:**

1. **ra_mst_courses:** Fetches from `/v1/courses` endpoint (region_codes=['gb'])
2. **ra_mst_jockeys:** Extracts from `/v1/racecards/pro` (yesterday's racecards)
3. **ra_mst_trainers:** Extracts from `/v1/racecards/pro` (yesterday's racecards)
4. **ra_mst_owners:** Extracts from `/v1/racecards/pro` (yesterday's racecards)
5. **ra_mst_horses:** Extracts from `/v1/racecards/pro` + enriches with `/v1/horses/{id}/pro`
6. **ra_races:** Fetches from `/v1/racecards/pro` (complete race data)
7. **ra_runners:** Extracted from race runners (nested in racecards)
8. **ra_mst_bookmakers:** Uses hardcoded bookmaker (no API endpoint available)

### Marking Strategy

**All fetched data is marked as TEST:**
- **IDs:** Prefixed with `**TEST**_test_{unique_id}_`
- **Names:** Prefixed with `**TEST** ` + original name
- **Pedigree IDs:** Also prefixed (sire_id, dam_id, damsire_id)

**Example Marked Data:**
```json
{
  "id": "**TEST**_test_abc12345_course",
  "name": "**TEST** Ascot",
  "region_code": "gb",
  "region": "Great Britain"
}
```

### Database Insertion

**Uses Same Pipeline as Production:**
1. Fetches from Racing API (REAL responses)
2. Marks data with TEST identifiers
3. Transforms using SAME logic as production fetchers
4. Inserts via SupabaseReferenceClient (UPSERT)
5. Reports success/failure

---

## Supported Tables

**Currently Supported (7 tables):**

1. ✅ `ra_mst_courses` - Course reference data
2. ✅ `ra_mst_jockeys` - Jockey entities from racecards
3. ✅ `ra_mst_trainers` - Trainer entities from racecards
4. ✅ `ra_mst_owners` - Owner entities from racecards
5. ✅ `ra_mst_horses` - Horse data with Pro enrichment
6. ✅ `ra_races` - Race data from racecards
7. ✅ `ra_mst_bookmakers` - Bookmaker reference (hardcoded)

**Future Expansion:**
- `ra_runners` - Runner data from race entries
- `ra_race_results` - Results data from completed races
- `ra_horse_pedigree` - Pedigree data from enrichment

---

## Use Cases

### 1. Verify Column Capture After Fetcher Updates

**Scenario:** You updated races_fetcher.py to capture new fields

**Workflow:**
```bash
# 1. Insert real API test data
python3 fetchers/master_fetcher_controller.py --mode test-api --tables ra_races --interactive

# 2. Run analysis to check column population
python3 fetchers/master_fetcher_controller.py --mode analyze --tables ra_races --interactive

# 3. Verify new columns are populated
# Check analysis output for columns with >0% population

# 4. Clean up
python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --tables ra_races --interactive
```

### 2. Test Complete Data Pipeline

**Scenario:** Verify end-to-end data flow from API to database

**Workflow:**
```bash
# Insert real API data
python3 fetchers/test_api_source.py

# Check database directly
psql -h ... -c "SELECT * FROM ra_mst_courses WHERE id LIKE '%**TEST**%';"

# Verify all expected columns populated

# Clean up
python3 fetchers/test_api_source.py --cleanup
```

### 3. Validate API Response Format

**Scenario:** Racing API may have changed response structure

**Workflow:**
```bash
# Insert real API data
python3 fetchers/test_api_source.py --tables ra_mst_horses

# Check logs for any transformation errors
# Review what fields were captured vs expected

# Clean up
python3 fetchers/test_api_source.py --cleanup --tables ra_mst_horses
```

### 4. Pre-Deployment Validation

**Scenario:** Before deploying fetcher changes to production

**Workflow:**
```bash
# Complete test workflow
python3 fetchers/master_fetcher_controller.py --mode test-api --interactive && \
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive && \
python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --interactive
```

---

## Output

### Insert Summary

```
================================================================================
API-SOURCE TEST DATA INSERT SUMMARY
================================================================================

Tables Processed: 7
Successful: 7
Failed: 0
Total API Fields Captured: 156

✅ Successful Insertions:
  - ra_mst_courses: 5 API fields captured
  - ra_mst_jockeys: 8 API fields captured
  - ra_mst_trainers: 7 API fields captured
  - ra_mst_owners: 6 API fields captured
  - ra_mst_horses: 15 API fields captured (with Pro enrichment)
  - ra_races: 45 API fields captured
  - ra_mst_bookmakers: 3 fields captured

================================================================================
```

### Cleanup Summary

```
================================================================================
API-SOURCE TEST DATA CLEANUP SUMMARY
================================================================================

Tables Processed: 7
Successful: 7
Failed: 0
Total Rows Deleted: 8

(1 row per table + 1 for runners nested in race)

================================================================================
```

---

## How It Works

### Fetching Real Data

**1. Courses:**
```python
# Fetch from /v1/courses
response = api_client.get_courses(region_codes=['gb'])
course = response['courses'][0]  # Take first course
```

**2. Entities (Jockeys/Trainers/Owners/Horses):**
```python
# Fetch yesterday's racecards (has real data)
yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
response = api_client.get_racecards_pro(
    date_from=yesterday,
    date_to=yesterday,
    region_codes=['gb']
)

# Extract entity from first runner
race = response['racecards'][0]
runner = race['runners'][0]
jockey = runner['jockey']  # Real jockey data
trainer = runner['trainer']  # Real trainer data
owner = runner['owner']  # Real owner data
horse = runner['horse']  # Real horse data
```

**3. Horses (with Pro Enrichment):**
```python
# Get basic horse data from racecard
horse = runner['horse']

# Enrich with Pro endpoint
pro_data = api_client.get_horse_details(horse['id'], tier='pro')
horse.update(pro_data['horse'])  # Merge complete pedigree data
```

### Marking as TEST

**All IDs and names are marked:**
```python
test_course = course.copy()
test_course['id'] = f"**TEST**_{unique_id}_course"
test_course['name'] = f"**TEST** {course['name']}"
```

**Ensures:**
- Test data easily identifiable
- Won't conflict with production data (unique IDs)
- Can be cleaned up by pattern matching (`LIKE '%**TEST**%'`)

### Transformation and Insertion

**Uses SAME transformation logic as production fetchers:**
```python
# Same as courses_fetcher.py
db_record = {
    'id': test_course.get('id'),
    'name': test_course.get('course') or test_course.get('name'),
    'region_code': test_course.get('region_code'),
    'region': test_course.get('region'),
    'latitude': test_course.get('latitude'),
    'longitude': test_course.get('longitude'),
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}

# Insert via database client (UPSERT)
result = db_client.insert_courses([db_record])
```

---

## Safety Features

### Insert Safety

✅ **Real API Data** - Tests actual production data pipeline
✅ **Unique Test IDs** - Won't conflict with production data
✅ **Clear Markers** - **TEST** prefix makes it obvious
✅ **No Production Impact** - Uses test-specific IDs
✅ **Same as Production** - Uses actual fetcher transformation logic

### Cleanup Safety

✅ **Pattern Matching** - Only deletes rows with **TEST** markers
✅ **Multiple Checks** - Checks both `id` and `name` fields
✅ **Safe Wildcards** - `LIKE '%**TEST**%'` won't match production data
✅ **Reports Deleted** - Shows exactly how many rows removed

---

## Comparison with Other Test Modes

### test-insert (Hardcoded Synthetic Data)

**Approach:** Hardcoded column names and values

**Problems:**
- ❌ Column names may not match actual schema
- ❌ Doesn't reflect real API response structure
- ❌ Data types may be wrong
- ❌ Fails when schema changes

**When to Use:** Never (deprecated)

### test-auto (Schema-Aware Synthetic Data)

**Approach:** Reads actual schema, generates appropriate test values

**Pros:**
- ✅ Column names match actual schema
- ✅ Data types appropriate for columns

**Cons:**
- ⚠️ Still synthetic data, not real API responses
- ⚠️ Doesn't test actual fetcher transformation logic
- ⚠️ May not catch API response format changes

**When to Use:** When API not available or for rapid schema testing

### test-api (Real API-Source Data) - **RECOMMENDED**

**Approach:** Fetches REAL data from Racing API, marks as TEST

**Pros:**
- ✅ Uses REAL API responses
- ✅ Tests actual fetcher transformation logic
- ✅ Validates production pipeline
- ✅ Catches API format changes
- ✅ Verifies all columns captured from real data

**Cons:**
- ⚠️ Requires API access
- ⚠️ Slightly slower (makes real API calls)

**When to Use:** Always (except when API unavailable)

---

## Common Issues & Solutions

### Issue: "No data from API"

**Cause:** API endpoint returned no data or wrong format

**Solutions:**
1. Check Racing API credentials in .env.local
2. Verify API subscription (Pro plan for racecards/horses)
3. Try different date (yesterday may have no races)
4. Check API status/rate limits

### Issue: Cleanup doesn't remove all test rows

**Cause:** Test data doesn't match cleanup patterns

**Solutions:**
1. Ensure test data was inserted with **TEST** markers
2. Check if IDs were modified after insertion
3. Manual cleanup: `DELETE FROM table WHERE id LIKE '%**TEST**%';`

### Issue: Transformation errors

**Cause:** API response structure changed or field missing

**Solutions:**
1. Check API documentation for endpoint changes
2. Update fetcher transformation logic
3. Review logs for specific field errors
4. Add null checks for optional fields

---

## Integration with Analysis

**Combined Workflow:**

```bash
# Complete validation workflow
python3 fetchers/master_fetcher_controller.py --mode test-api --interactive && \
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive && \
python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --interactive
```

**What This Tests:**

1. **API Data Fetch:** Verifies Racing API connectivity and data retrieval
2. **Column Capture:** Analysis shows which columns populated from real API data
3. **Data Pipeline:** Confirms entire fetch → transform → insert flow works
4. **Column Completeness:** Identifies any columns NOT being captured

**Expected Results:**

- All tables show successful insertion
- Analysis shows populated columns from API
- Any 0% columns indicate fields NOT captured from API
- Can compare with COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json

---

## Best Practices

### DO

✅ Run before major deployments to production
✅ Use after updating fetcher transformation logic
✅ Combine with analysis mode for comprehensive validation
✅ Clean up test data after testing
✅ Keep test data short-lived (hours, not days)
✅ Use this as primary test method (real API data)

### DON'T

❌ Leave test data in production for extended periods
❌ Rely on test data for production queries
❌ Modify test data after insertion (breaks cleanup)
❌ Use **TEST** markers in production data
❌ Skip cleanup step

---

## Troubleshooting

### Error: "RacingAPIClient authentication failed"

**Cause:** Invalid API credentials

**Solution:**
```bash
# Check .env.local has correct credentials
grep -E "RACING_API_(USERNAME|PASSWORD)" .env.local
```

### Error: "No racecards found for yesterday"

**Cause:** No races scheduled on that date

**Solution:** Script uses yesterday's date. If no races, try day before:
```python
# In test_api_source.py, temporarily change:
yesterday = (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d')
```

### Warning: "Could not enrich horse with Pro endpoint"

**Cause:** Horse Pro enrichment failed (non-critical)

**Solution:** Basic horse data still inserted. Check:
1. API Pro plan subscription active
2. Horse ID valid
3. Rate limits not exceeded

---

## Related Documentation

- **[COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json](COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json)** - All columns with API sources
- **[TABLE_ANALYSIS_GUIDE.md](TABLE_ANALYSIS_GUIDE.md)** - Comprehensive table analysis
- **[CONTROLLER_QUICK_START.md](CONTROLLER_QUICK_START.md)** - Master controller usage
- **[TEST_DATA_GUIDE.md](TEST_DATA_GUIDE.md)** - Other test modes (synthetic data)

---

## Examples

### Example 1: Test Horses Table with Real API Data

```bash
# Insert real API horse data (with Pro enrichment)
python3 fetchers/test_api_source.py --tables ra_mst_horses

# Check what was inserted
psql -h ... -c "SELECT * FROM ra_mst_horses WHERE id LIKE '%**TEST**%';"

# Verify pedigree fields populated (from Pro endpoint)
python3 fetchers/analyze_tables.py --tables ra_mst_horses

# Clean up
python3 fetchers/test_api_source.py --cleanup --tables ra_mst_horses
```

### Example 2: Validate Complete Race Pipeline

```bash
# Insert real race data (race + runners)
python3 fetchers/test_api_source.py --tables ra_races

# Verify race and runners both inserted
psql -h ... -c "
SELECT r.race_title, COUNT(run.id) as runner_count
FROM ra_races r
LEFT JOIN ra_runners run ON r.race_id = run.race_id
WHERE r.race_id LIKE '%**TEST**%'
GROUP BY r.race_title;
"

# Clean up both race and runners
python3 fetchers/test_api_source.py --cleanup --tables ra_races ra_runners
```

### Example 3: Pre-Deployment Full Validation

```bash
# Complete validation before production deployment
python3 fetchers/master_fetcher_controller.py --mode test-api --interactive
# Review: All tables should succeed

python3 fetchers/master_fetcher_controller.py --mode analyze --interactive
# Review: Check column population percentages

python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --interactive
# Review: All test data removed
```

---

## Summary

**The API-source test system provides:**

✅ Validation with REAL Racing API data
✅ Tests actual production data pipeline
✅ Verifies ALL columns captured from API responses
✅ Catches API format changes early
✅ Safe insertion and cleanup
✅ Controller integration for easy use
✅ Combined with analysis for comprehensive validation

**Use it for:**
- Pre-deployment validation
- Fetcher update verification
- API response format validation
- Production pipeline testing
- Column capture completeness checks

---

**Last Updated:** 2025-10-21
**Version:** v1.0
**Maintainer:** DarkHorses-Masters-Workers Team
