# Autonomous Validation Agent Guide

**Purpose:** Fully automated end-to-end validation of the complete data pipeline with comprehensive reporting.

**Status:** ✅ Production-Ready
**Location:** `tests/autonomous_validation_agent.py`

---

## What It Does

The autonomous agent performs **complete end-to-end validation** automatically:

### Phase 1: Fetch Live Data
- Fetches REAL races from Racing API (yesterday's date)
- Uses production RacesFetcher code
- Adds `**TEST**` markers to every single field
- Inserts marked data to database
- Reports: races marked, runners marked, total records

### Phase 2: Verify All Tables
- Queries EVERY table in the database
- Checks EVERY column for `**TEST**` markers
- Calculates coverage percentage per table
- Identifies columns missing `**TEST**`
- Generates detailed verification report

### Phase 3: Cleanup
- Removes all test data from database
- Deletes rows with `**TEST**` markers
- Verifies cleanup was successful
- Reports: tables cleaned, total rows deleted

### Phase 4: Report Generation
- Creates JSON report (machine-readable)
- Creates Markdown report (human-readable)
- Saves to `logs/validation_report_TIMESTAMP.{json,md}`

---

## Quick Start

### Run Complete Validation

```bash
python3 tests/autonomous_validation_agent.py
```

**What happens:**
1. 3-second countdown (can cancel with Ctrl+C)
2. Fetches live data from Racing API
3. Adds **TEST** markers
4. Verifies all 14+ tables
5. Generates reports
6. Cleans up test data
7. Shows summary

**Expected output:**
```
================================================================================
AUTONOMOUS VALIDATION AGENT - STARTING
================================================================================

Workflow:
1. Fetch REAL data from Racing API
2. Add **TEST** markers to all fields
3. Insert to database
4. Verify EVERY table and column
5. Generate comprehensive report
6. Cleanup test data
================================================================================

Press Ctrl+C to cancel, or wait 3 seconds to continue...
================================================================================

================================================================================
PHASE 1: FETCHING LIVE DATA WITH **TEST** MARKERS
================================================================================

Fetching races for date: 2025-10-22
✅ Fetched 127 races from Racing API

Adding **TEST** markers to fetched data...
  ✅ Marked race: 12345 - **TEST** 3:45 Cheltenham
  ✅ Marked race: 12346 - **TEST** 4:20 Newmarket
  ...

✅ Phase 1 complete:
   Races marked: 5
   Runners marked: 67
   Total records marked: 72

================================================================================
PHASE 2: VERIFYING ALL TABLES AND COLUMNS
================================================================================

Verifying ra_races...
  ✅ ra_races: All 45 columns have **TEST**

Verifying ra_runners...
  ✅ ra_runners: All 57 columns have **TEST**

Verifying ra_race_results...
  ⚠️  ra_race_results: No test data found

Verifying ra_mst_jockeys...
  ✅ ra_mst_jockeys: All 12 columns have **TEST**

...

================================================================================
PHASE 2 SUMMARY:
================================================================================
Tables checked: 14
Tables with test data: 12
Tables missing test data: 2

Total columns checked: 625
Columns with **TEST**: 598
Overall coverage: 95.68%

✅ All tables have **TEST** marker coverage!

================================================================================
PHASE 3: CLEANING UP TEST DATA
================================================================================

Cleaning ra_runners...
  ✅ Deleted 67 rows from ra_runners
Cleaning ra_races...
  ✅ Deleted 5 rows from ra_races
...

✅ Phase 3 complete: 144 rows deleted

📄 Reports saved:
   JSON: logs/validation_report_20251023_092534.json
   Markdown: logs/validation_report_20251023_092534.md

================================================================================
AUTONOMOUS VALIDATION COMPLETE
================================================================================

✅ VALIDATION SUCCESSFUL
   Coverage: 95.68%

📄 Check detailed reports in logs/
================================================================================
```

---

## Understanding the Reports

### JSON Report (validation_report_TIMESTAMP.json)

**Machine-readable format** for automated processing:

```json
{
  "timestamp": "2025-10-23T09:25:34",
  "phase_1_fetch": {
    "success": true,
    "races_marked": 5,
    "runners_marked": 67,
    "total_marked": 72
  },
  "phase_2_verification": {
    "tables_checked": 14,
    "tables_with_test_data": 12,
    "total_columns_checked": 625,
    "total_columns_with_test": 598,
    "overall_coverage_percent": 95.68,
    "details": [...]
  },
  "phase_3_cleanup": {
    "success": true,
    "total_deleted": 144
  },
  "overall_success": true
}
```

### Markdown Report (validation_report_TIMESTAMP.md)

**Human-readable format** for review:

```markdown
# Autonomous Validation Report

**Generated:** 2025-10-23T09:25:34

---

## Phase 1: Fetch Live Data

✅ **Success**

- Races marked: 5
- Runners marked: 67
- Total marked: 72

## Phase 2: Verification Results

**Overall Coverage:** 95.68%

- Tables checked: 14
- Tables with test data: 12
- Total columns checked: 625
- Columns with **TEST**: 598

### Per-Table Results

✅ **ra_races** - 100.0% (45/45 columns)
✅ **ra_runners** - 100.0% (57/57 columns)
❌ **ra_race_results** - No test data found
✅ **ra_mst_jockeys** - 100.0% (12/12 columns)
⚠️ **ra_mst_horses** - 87.5% (21/24 columns)

   Missing **TEST** in:
   - `dob` (date)
   - `sex_code` (character varying)
   - `breeder` (character varying)

...

## Phase 3: Cleanup

✅ **Success:** 144 rows deleted

---

## Overall Result

✅ **VALIDATION SUCCESSFUL**
```

---

## What Gets Verified

### Tables Verified (14 tables)

**Transaction Tables:**
- `ra_races` - 45 columns
- `ra_runners` - 57 columns
- `ra_race_results` - 38 columns

**Master Tables - People:**
- `ra_mst_jockeys` - 12 columns
- `ra_mst_trainers` - 12 columns
- `ra_mst_owners` - 12 columns

**Master Tables - Horses:**
- `ra_mst_horses` - 24 columns
- `ra_horse_pedigree` - 8 columns

**Master Tables - Reference:**
- `ra_mst_courses` - 15 columns
- `ra_mst_bookmakers` - 5 columns
- `ra_mst_regions` - 3 columns

**Pedigree Statistics:**
- `ra_mst_sires` - 47 columns
- `ra_mst_dams` - 47 columns
- `ra_mst_damsires` - 47 columns

**Total:** 625+ columns across 14 tables

### Verification Criteria

For each table, the agent checks:
1. ✅ Does table have any test data?
2. ✅ How many columns exist?
3. ✅ How many columns have `**TEST**` markers?
4. ✅ Which columns are missing `**TEST**`?
5. ✅ What is the coverage percentage?

**Pass criteria:**
- Overall coverage > 50%
- Critical tables (ra_races, ra_runners) have 100%
- Cleanup successful

---

## Interpreting Results

### ✅ 100% Coverage

```
✅ ra_races - 100.0% (45/45 columns)
```

**Meaning:** ALL columns in ra_races have `**TEST**` markers
**Action:** None - perfect!

### ⚠️ Partial Coverage

```
⚠️ ra_mst_horses - 87.5% (21/24 columns)

   Missing **TEST** in:
   - dob (date)
   - sex_code (character varying)
   - breeder (character varying)
```

**Meaning:** 3 columns don't have `**TEST**` markers
**Possible causes:**
1. Columns not populated by fetcher (bug)
2. Columns populated later by different process (expected)
3. Auto-generated columns (expected)

**Action:** Review each missing column to determine if it's a bug or expected

### ❌ No Test Data

```
❌ ra_race_results - No test data found
```

**Meaning:** Table has no rows with `**TEST**` markers
**Possible causes:**
1. Fetcher doesn't populate this table (need to extend test)
2. Table populated by different process (expected)
3. No data available for test date (expected)

**Action:** Determine if table should have test data

---

## Common Scenarios

### Scenario 1: First-Time Validation

**Goal:** Verify entire system works end-to-end

```bash
python3 tests/autonomous_validation_agent.py
```

**Expected:**
- Phase 1: Success (data fetched and marked)
- Phase 2: 70-100% coverage (some tables may not have test data yet)
- Phase 3: Success (cleanup works)

**Review:** Check markdown report for any critical tables missing data

---

### Scenario 2: After Code Changes

**Goal:** Verify changes didn't break anything

```bash
# Make code changes to fetchers/races_fetcher.py

# Run validation
python3 tests/autonomous_validation_agent.py

# Check report - did coverage change?
cat logs/validation_report_*.md | tail -50
```

**Expected:**
- Coverage should remain the same or improve
- No new missing columns

**If coverage decreased:** Your changes broke something - review the diff

---

### Scenario 3: After Schema Changes

**Goal:** Verify new columns are being populated

```bash
# Add new column to database
# Update fetcher to populate new column

# Run validation
python3 tests/autonomous_validation_agent.py

# Check if new column has **TEST**
grep "new_column_name" logs/validation_report_*.md
```

**Expected:**
- New column should appear in column list
- New column should have `**TEST**` marker

---

## Integration with CI/CD

### GitHub Actions Example

```yaml
name: Validate Data Pipeline

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run Autonomous Validation
        env:
          RACING_API_USERNAME: ${{ secrets.RACING_API_USERNAME }}
          RACING_API_PASSWORD: ${{ secrets.RACING_API_PASSWORD }}
          SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
          SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
        run: python3 tests/autonomous_validation_agent.py

      - name: Check Coverage
        run: |
          COVERAGE=$(cat logs/validation_report_*.json | jq '.phase_2_verification.overall_coverage_percent')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage too low: $COVERAGE%"
            exit 1
          fi

      - name: Upload Reports
        uses: actions/upload-artifact@v2
        with:
          name: validation-reports
          path: logs/validation_report_*
```

---

## Advanced Usage

### Custom Table List

Modify the agent to verify specific tables:

```python
# In autonomous_validation_agent.py, modify:
self.tables_to_verify = [
    'ra_races',
    'ra_runners',
    'your_custom_table',
]
```

### Coverage Threshold

Modify pass criteria:

```python
# Change threshold from 50% to 80%
results['overall_success'] = (
    fetch_results.get('success') and
    cleanup_results.get('success') and
    overall_coverage > 80  # Stricter threshold
)
```

### Quiet Mode

Run without interactive output (CI/CD):

```python
# Modify main() to skip countdown
# time.sleep(3)  # Comment out
```

---

## Troubleshooting

### Issue: "No test data found in {table}"

**Cause:** Table wasn't populated during Phase 1

**Solutions:**
1. Check if table is populated by races fetcher (might need different entity type)
2. Extend test to fetch other entity types (results, courses, etc.)
3. Expected if table is populated by different process

---

### Issue: "Overall coverage < 50%"

**Cause:** Many columns missing `**TEST**` markers

**Investigation:**
1. Review markdown report - which tables have low coverage?
2. Check fetcher code - are those columns being populated?
3. Check API response - are those fields present?
4. Check transformation logic - are fields mapped correctly?

---

### Issue: "Cleanup failed"

**Cause:** Error deleting test data

**Solutions:**
1. Check database permissions
2. Check foreign key constraints (delete child tables first)
3. Manual cleanup: Run test_live_data_with_markers.py --cleanup

---

## Best Practices

### DO ✅

- **Run before deployments** - Catch issues early
- **Review reports** - Don't just check pass/fail
- **Track coverage trends** - Should improve over time
- **Investigate low coverage** - Find and fix root causes
- **Run after schema changes** - Verify new columns populate

### DON'T ❌

- **Don't ignore warnings** - Partial coverage indicates issues
- **Don't assume pass = perfect** - Review actual coverage numbers
- **Don't skip cleanup** - Agent does it automatically, but verify
- **Don't run in production** during business hours - Uses real API

---

## Summary

The Autonomous Validation Agent provides **comprehensive, automated end-to-end validation**:

1. ✅ **Fetches real data** from Racing API
2. ✅ **Tests production code** (not mocks)
3. ✅ **Verifies all tables** and columns
4. ✅ **Generates reports** for review
5. ✅ **Cleans up automatically**
6. ✅ **CI/CD ready** - machine-readable output

**Use it:**
- Before every deployment
- After code changes
- After schema changes
- In CI/CD pipelines
- For periodic health checks

**Command:**
```bash
python3 tests/autonomous_validation_agent.py
```

**Reports:**
- `logs/validation_report_TIMESTAMP.json` - Machine-readable
- `logs/validation_report_TIMESTAMP.md` - Human-readable

---

**Last Updated:** 2025-10-23
**Status:** Production-Ready
**Automated:** 100%
**Coverage Target:** >80%
