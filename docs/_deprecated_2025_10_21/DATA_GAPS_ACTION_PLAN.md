# Data Gaps - Immediate Action Plan

**Generated:** 2025-10-20
**Based on:** Complete Database Audit of 625 columns across 24 tables

## Executive Summary

**Critical Finding:** The 6 enhanced runner fields from Migration 011 are **NOT POPULATED** despite columns existing in the database. This affects 1.3M runner records and blocks critical ML features.

**Overall Status:**
- 51% of columns (319) are completely empty
- 30% of columns (189) are fully populated
- 19% of columns (117) have partial data

---

## IMMEDIATE ACTIONS (Do Today)

### ✅ Action 1: Verify Migration 011 Status

**The enhanced runner fields exist but are 100% empty:**

```sql
-- Check if columns exist
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_runners'
AND column_name IN (
  'finishing_time',
  'starting_price_decimal',
  'race_comment',
  'jockey_silk_url',
  'overall_beaten_distance',
  'jockey_claim_lbs',
  'weight_stones_lbs'
);
```

**Current Status:** All 7 fields exist but have 0 populated records out of 1,326,595

**What to do:**
1. Verify the migration was applied (columns exist ✓)
2. Check if `results_fetcher.py` is populating these fields
3. Check if `races_fetcher.py` is populating pre-race fields (jockey_silk_url, weight_stones_lbs, jockey_claim_lbs)

**Files to check:**
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/results_fetcher.py`
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/races_fetcher.py`
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/utils/position_parser.py`

---

### ✅ Action 2: Apply Course Coordinates Migration

**Status:** Migration file exists but NOT applied to database

**Affected:** `ra_mst_courses` - 101 records missing longitude/latitude

**Commands:**
```bash
# 1. Apply migration
psql -h aws-0-eu-west-2.pooler.supabase.com \
     -p 5432 \
     -U postgres.amsjvmlaknnvppxsgpfk \
     -d postgres \
     -f /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/migrations/021_add_course_coordinates.sql

# 2. Populate coordinates
python3 /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/scripts/update_course_coordinates.py
```

**Expected Result:** 101 courses with longitude/latitude populated

---

### ✅ Action 3: Fix Horse Metadata Gaps

**Issues Found:**

| Field | Population | Missing | Issue |
|-------|-----------|---------|-------|
| `colour_code` | 24.23% | 84,613 | Should be ~100% from API |
| `region` | 28.76% | 79,553 | Should be higher from API |
| `dob`, `sex_code`, `colour` | 99.87% | 147 | Nearly complete, 147 missing |
| `age` | 0% | 111,669 | Never calculated |
| `breeder` | 0% | 111,669 | Data in pedigree table |

**Root Cause Analysis Needed:**

1. **Why is `colour_code` only 24% populated?**
   - Check API response structure from `/v1/horses/{id}/pro`
   - May be a field mapping issue in `entity_extractor.py`

2. **Why is `region` only 29% populated?**
   - Check if region is optional in API
   - Verify field mapping in enrichment

**Quick Fixes:**

```sql
-- Fix 1: Calculate age from DOB (can be done immediately)
UPDATE ra_mst_horses
SET age = EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob))
WHERE dob IS NOT NULL;

-- Fix 2: Migrate breeder from pedigree table
UPDATE ra_mst_horses h
SET breeder = p.breeder
FROM ra_horse_pedigree p
WHERE h.id = p.horse_id
AND p.breeder IS NOT NULL;
```

**Investigation Required:**
```bash
# Test enrichment for a sample horse
python3 << 'EOF'
from utils.api_client import RacingAPIClient
from config.config import get_config

config = get_config()
client = RacingAPIClient(config)

# Pick a horse with missing colour_code/region
test_horse_id = "SAMPLE_ID"  # Get from: SELECT id FROM ra_mst_horses WHERE colour_code IS NULL LIMIT 1

response = client.fetch_horse_details(test_horse_id)
print("API Response:")
print(f"  colour_code: {response.get('colour_code', 'MISSING')}")
print(f"  region: {response.get('region', 'MISSING')}")
EOF
```

---

## SHORT-TERM ACTIONS (This Week)

### ✅ Action 4: Investigate Results Fetcher Coverage

**Current State:**
- `ra_runners`: 1,326,595 total records
- Only 8-9% have result data populated:
  - `position`: 111,508 (8.41%)
  - `starting_price`: 118,097 (8.90%)
  - `distance_beaten`: 118,101 (8.90%)

**Possible Causes:**
1. Most races are future (racecards) vs past (results)
2. Results fetcher not running consistently
3. Historical data never backfilled

**Investigation Query:**
```sql
-- Check ratio of future vs past races
SELECT
  CASE
    WHEN date > CURRENT_DATE THEN 'Future'
    WHEN date = CURRENT_DATE THEN 'Today'
    ELSE 'Past'
  END as race_timing,
  COUNT(*) as race_count,
  ROUND(COUNT(*)::numeric / SUM(COUNT(*)) OVER () * 100, 2) as pct
FROM ra_races
GROUP BY 1
ORDER BY 1;

-- Check results population by year
SELECT
  EXTRACT(YEAR FROM r.date) as year,
  COUNT(DISTINCT r.race_id) as total_races,
  COUNT(DISTINCT CASE WHEN ru.position IS NOT NULL THEN r.race_id END) as races_with_results,
  ROUND(COUNT(DISTINCT CASE WHEN ru.position IS NOT NULL THEN r.race_id END)::numeric /
        COUNT(DISTINCT r.race_id)::numeric * 100, 2) as pct_with_results
FROM ra_races r
LEFT JOIN ra_runners ru ON r.race_id = ru.race_id
GROUP BY 1
ORDER BY 1 DESC;
```

**Action Items:**
1. Run investigation queries above
2. Check cron schedule for results fetcher
3. Determine if historical backfill is needed
4. Verify results_fetcher is populating enhanced fields

---

### ✅ Action 5: Implement Simple Calculations

**Easy wins that don't require API calls:**

1. **Calculate horse age** (5 minutes)
```python
# Script: scripts/calculate_horse_ages.py
from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config

config = get_config()
db = SupabaseReferenceClient(config)

# SQL to calculate age
sql = """
UPDATE ra_mst_horses
SET age = EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob)),
    updated_at = NOW()
WHERE dob IS NOT NULL
"""

result = db.execute_sql(sql)
print(f"Updated {result} horse ages")
```

2. **Migrate breeder field** (5 minutes)
```python
# Script: scripts/migrate_breeder_field.py
sql = """
UPDATE ra_mst_horses h
SET breeder = p.breeder,
    updated_at = NOW()
FROM ra_horse_pedigree p
WHERE h.id = p.horse_id
  AND p.breeder IS NOT NULL
  AND h.breeder IS NULL
"""
```

3. **Calculate pedigree win percentages** (10 minutes)
```python
# Script: scripts/calculate_pedigree_stats.py
sql = """
-- Sires
UPDATE ra_mst_sires
SET overall_win_percent = CASE
    WHEN total_runners > 0 THEN (total_wins::numeric / total_runners::numeric * 100)
    ELSE 0
  END,
  updated_at = NOW();

-- Dams
UPDATE ra_mst_dams
SET overall_win_percent = CASE
    WHEN total_runners > 0 THEN (total_wins::numeric / total_runners::numeric * 100)
    ELSE 0
  END,
  updated_at = NOW();

-- Damsires
UPDATE ra_mst_damsires
SET overall_win_percent = CASE
    WHEN total_runners > 0 THEN (total_wins::numeric / total_runners::numeric * 100)
    ELSE 0
  END,
  updated_at = NOW();
"""
```

---

## MEDIUM-TERM ACTIONS (This Month)

### ✅ Action 6: Implement Pedigree Statistics Workers

**Status:** Tables exist, statistics columns exist, but 100% empty

**Affected Tables:**
- `ra_mst_sires`: 2,143 records, 39/47 columns empty
- `ra_mst_dams`: 48,372 records, 39/47 columns empty
- `ra_mst_damsires`: 3,041 records, 39/47 columns empty

**Empty Fields (per table):**
- `overall_win_percent`, `overall_ae_index`
- `best_class`, `best_class_ae`, `best_distance`, `best_distance_ae`
- `class_1/2/3_*` fields (9 columns each)
- `distance_1/2/3_*` fields (15 columns each)
- `analysis_last_updated`, `data_quality_score`

**Implementation Pattern:**
- Follow same pattern as `scripts/statistics_workers/jockey_statistics_worker.py`
- Calculate from `ra_runners` data joined with race results
- Create 3 new workers:
  - `scripts/statistics_workers/sire_statistics_worker.py`
  - `scripts/statistics_workers/dam_statistics_worker.py`
  - `scripts/statistics_workers/damsire_statistics_worker.py`

**Estimated Effort:** 2-3 days

---

### ✅ Action 7: Populate Missing Race Metadata

**Issues:**

| Field | Population | Records Missing | Priority |
|-------|-----------|-----------------|----------|
| `race_class` | 78.55% | 29,382 | HIGH |
| `prize` | 5.23% | 129,794 | MEDIUM |
| `pattern` | 0.52% | 136,249 | LOW |
| `age_band` | 27.28% | 99,594 | MEDIUM |
| `field_size` | 27.28% | 99,594 | MEDIUM |

**Investigation Needed:**
1. Check if these fields are in API response but not being captured
2. Determine if missing data is API limitation or our mapping issue
3. Review `races_fetcher.py` field mapping

**Test Query:**
```bash
# Fetch a sample race to see what fields are available
python3 << 'EOF'
from utils.api_client import RacingAPIClient
from config.config import get_config
import json

config = get_config()
client = RacingAPIClient(config)

# Fetch today's races
import datetime
today = datetime.date.today().strftime('%Y-%m-%d')
races = client.fetch_racecards(date=today, region_codes=['gb', 'ire'])

if races:
    print(json.dumps(races[0], indent=2))
    print("\nAvailable fields:")
    print(races[0].keys())
EOF
```

---

## LONGER-TERM ACTIONS (Next Quarter)

### ✅ Action 8: Decide on Empty/Placeholder Tables

**Tables with 0 records:**
- `ra_entity_combinations` (16 columns)
- `ra_performance_by_distance` (17 columns)
- `ra_performance_by_venue` (16 columns)
- `ra_runner_statistics` (35 columns)
- `ra_runner_supplementary` (8 columns)

**Decision Needed:**
1. Implement these features? (significant dev work)
2. Remove these tables? (clean up database)
3. Keep as placeholders? (for future use)

**Recommendation:** Document the purpose and decide per table

---

### ✅ Action 9: Historical Results Backfill

**Current State:**
- Database has races from 2015-2025
- Only ~9% of runners have result data
- Most data appears to be racecards (future races)

**Considerations:**
1. How much historical data do we need for ML?
2. API rate limits (2 req/sec)
3. Storage costs
4. Processing time

**Estimate:**
- 1.3M runners × 91% missing = ~1.2M missing results
- At 2 req/sec = ~7 days of continuous fetching
- Better approach: Fetch by date range, prioritize recent history

**Proposed Approach:**
1. Start with last 12 months (highest value for ML)
2. Then backfill year by year to 2015
3. Run during off-peak hours

---

### ✅ Action 10: Implement Advanced Analytics

**Fields requiring complex calculation:**

1. **AE Index (Actual vs Expected)**
   - `overall_ae_index` for all pedigree tables
   - `best_class_ae`, `best_distance_ae`
   - Requires odds data comparison

2. **Data Quality Score**
   - `data_quality_score` for all pedigree tables
   - Measure of data completeness and reliability

3. **Performance by Distance/Venue**
   - Populate `ra_performance_by_distance`
   - Populate `ra_performance_by_venue`

**Estimated Effort:** 2-4 weeks

---

## TRACKING PROGRESS

Create a simple tracking script:

```python
# scripts/check_data_completeness.py
import psycopg2

conn = psycopg2.connect(...)
cur = conn.cursor()

checks = {
    "Enhanced runner fields": "SELECT COUNT(*) FROM ra_runners WHERE starting_price_decimal IS NOT NULL",
    "Course coordinates": "SELECT COUNT(*) FROM ra_mst_courses WHERE longitude IS NOT NULL",
    "Horse ages": "SELECT COUNT(*) FROM ra_mst_horses WHERE age IS NOT NULL",
    "Horse breeders": "SELECT COUNT(*) FROM ra_mst_horses WHERE breeder IS NOT NULL",
    "Sire win %": "SELECT COUNT(*) FROM ra_mst_sires WHERE overall_win_percent IS NOT NULL",
    "Dam win %": "SELECT COUNT(*) FROM ra_mst_dams WHERE overall_win_percent IS NOT NULL",
}

for check_name, sql in checks.items():
    cur.execute(sql)
    count = cur.fetchone()[0]
    print(f"{check_name}: {count}")
```

---

## PRIORITY MATRIX

| Action | Priority | Effort | Impact | Dependencies |
|--------|----------|--------|--------|--------------|
| Verify Migration 011 population | P0 | 1 hour | Critical | None |
| Apply course coordinates | P0 | 30 min | Medium | Migration file |
| Calculate horse ages | P1 | 5 min | Low | None |
| Migrate breeder field | P1 | 5 min | Low | None |
| Fix horse metadata gaps | P1 | 1 day | Medium | API investigation |
| Calculate pedigree win % | P2 | 1 hour | Low | None |
| Investigate results coverage | P1 | 2 hours | High | None |
| Implement pedigree workers | P2 | 3 days | Medium | Worker framework |
| Populate race metadata | P2 | 2 days | Medium | API investigation |
| Historical backfill | P3 | 2 weeks | High | Results fetcher |

**P0 = Critical, do today**
**P1 = High priority, this week**
**P2 = Medium priority, this month**
**P3 = Lower priority, this quarter**

---

## KEY QUESTIONS TO ANSWER

Before proceeding, investigate:

1. ❓ **Why are enhanced runner fields 100% empty?**
   - Are fetchers populating them?
   - Is there a bug in the mapping?

2. ❓ **Why is colour_code only 24% populated?**
   - Field mapping issue?
   - API doesn't always provide it?

3. ❓ **What % of races are future vs past?**
   - Explains why results are only 9% populated

4. ❓ **Should we backfill historical results?**
   - How far back?
   - What's the ML training data requirement?

5. ❓ **What to do with empty tables?**
   - Implement, remove, or leave as placeholders?

---

## EXPECTED OUTCOMES

After completing all Priority 0-1 actions:

- ✅ 6 enhanced runner fields populated for new data
- ✅ 101 courses with coordinates
- ✅ 111,669 horses with calculated age
- ✅ ~111,500 horses with breeder info
- ✅ Understanding of results coverage issue
- ✅ Plan for historical backfill

After Priority 2 actions:

- ✅ Pedigree statistics calculating automatically
- ✅ Better race metadata coverage
- ✅ Clear picture of what data is genuinely missing vs not yet implemented

---

## FILES REFERENCED

**Audit Files:**
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/COMPLETE_DATABASE_AUDIT.json`
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/DATABASE_AUDIT_SUMMARY.md`
- This file: `DATA_GAPS_ACTION_PLAN.md`

**Migrations:**
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/migrations/add_enhanced_statistics_columns.sql`
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/migrations/021_add_course_coordinates.sql`

**Fetchers to Review:**
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/results_fetcher.py`
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/races_fetcher.py`

**Scripts to Create:**
- `scripts/calculate_horse_ages.py`
- `scripts/migrate_breeder_field.py`
- `scripts/calculate_pedigree_stats.py`
- `scripts/check_data_completeness.py`
