# Complete Data Filling Guide

**Generated:** 2025-10-20
**Database:** Racing API Masters Workers
**Coverage:** ALL 625 columns across 24 tables

---

## Executive Summary

This guide provides a complete inventory of ALL missing data across the entire database with specific instructions on how to fill each gap.

**Data Status:**
- **189 columns (30.2%)** - Fully populated ✅
- **436 columns (69.8%)** - Have gaps that need attention

**Data Coverage Timeline:**
- **Core race data:** 2015-01-01 to 2025-10-19 (10.8 years)
- **Odds historical:** 2015-01-01 to 2025-10-19 (10.8 years)
- **Pedigree data:** 2025-10-14 to 2025-10-20 (recent only)

---

## Data Sources Breakdown

### 1. Calculated from Database (208 columns, 169 with gaps)

**What it is:** Statistics calculated from historical race/runner records

**Tables affected:**
- `ra_mst_jockeys` - Win rates, recent form (14d/30d)
- `ra_mst_trainers` - Win rates, recent form (14d/30d)
- `ra_mst_owners` - Win rates, recent form (14d/30d)
- `ra_mst_sires` - Progeny performance statistics (117 columns at 0%)
- `ra_mst_dams` - Progeny performance statistics (117 columns at 0%)
- `ra_mst_damsires` - Grandoffspring performance statistics (117 columns at 0%)

**Status:**
- ✅ Jockeys: 99.08% complete (win_rate populated)
- ✅ Trainers: 99.71% complete (win_rate populated)
- ✅ Owners: 99.89% complete (win_rate populated)
- ❌ **Pedigree (sires/dams/damsires): 0% complete** - ALL 117 statistics columns empty

**How to fill:**
```bash
# People statistics (already mostly done)
python3 scripts/statistics_workers/populate_all_statistics.py --all

# Pedigree statistics (CRITICAL - needs fixing first)
# ISSUE: Script has schema errors (sire_name column doesn't exist)
# FIX: Update script to use ra_mst_sires.name instead of ra_mst_horses.sire_name
# THEN:
python3 scripts/populate_pedigree_statistics.py
```

**Duration:** 30-60 minutes for pedigree statistics

**Gap Details - Pedigree Statistics (ALL at 0%):**

For each of sires (2,143), dams (48,372), damsires (3,041):
- `overall_win_percent` - Win rate across all offspring
- `overall_ae_index` - Actual vs Expected index
- `best_class` - Best performing class name
- `best_class_ae` - AE index for best class
- `best_distance` - Best performing distance
- `best_distance_ae` - AE index for best distance
- `analysis_last_updated` - Timestamp of last calculation
- `data_quality_score` - Quality metric
- `class_1_name` through `class_3_name` - Top 3 classes
- `class_1_runners` through `class_3_runners` - Runner counts per class
- `class_1_wins` through `class_3_wins` - Win counts per class
- `class_1_win_percent` through `class_3_win_percent` - Win rates per class
- `class_1_ae` through `class_3_ae` - AE indices per class
- `distance_1_name` through `distance_3_name` - Top 3 distances
- `distance_1_runners` through `distance_3_runners` - Runner counts per distance
- `distance_1_wins` through `distance_3_wins` - Win counts per distance
- `distance_1_win_percent` through `distance_3_win_percent` - Win rates per distance
- `distance_1_ae` through `distance_3_ae` - AE indices per distance

**Total Empty:** 39 columns × 3 tables = 117 critical statistics columns

---

### 2. Racing API - Racecards/Results (125 columns, 99 with gaps)

**What it is:** Data from `/v1/racecards/pro` and `/v1/results` endpoints

**Tables affected:**
- `ra_races` - Race metadata
- `ra_runners` - Runner entries with result data
- `ra_mst_trainers` - Trainer locations

**Status:**
- ✅ Core race fields: 100% (id, course_id, date, time, etc.)
- ⚠️ Race class: 78.55% (should be higher)
- ⚠️ Result fields: Only 8-9% populated (may be expected if mostly future races)

**Critical Gaps - ra_runners (1,326,595 records):**

**Result-only fields (9 fields at 0%):**
- `starting_price_decimal` - Decimal odds format (0%)
- `finishing_time` - Race completion time (0%)
- `race_comment` - Race commentary/notes (0%)
- `overall_beaten_distance` - Alternative distance metric (0%)

**Pre/Post-race fields (partial):**
- `jockey_silk_url` - SVG URL (0%)
- `weight_stones_lbs` - UK format weight (0%)
- `jockey_claim_lbs` - Weight allowance (0%)

**Race results (low coverage - 8-9%):**
- `position` - Finishing position (111,479 / 1,326,595 = 8.4%)
- `distance_beaten` - Distance behind winner (115,813 / 1,326,595 = 8.73%)
- `prize_won` - Prize money (114,688 / 1,326,595 = 8.65%)
- `starting_price` - Fractional odds (106,449 / 1,326,595 = 8.03%)

**Other partial fields:**
- `ofr` - Official rating (74.15%)
- `ts` - Topspeed rating (79.78%)
- `headgear` - Headgear worn (37.05%)

**How to fill:**

1. **Verify enhanced runner fields are being captured:**
```python
# Check fetchers/results_fetcher.py and fetchers/races_fetcher.py
# Ensure they extract: starting_price_decimal, finishing_time, race_comment, etc.
# These fields were added in migration 011 but may not be mapped in fetchers
```

2. **Run historical backfill if needed:**
```bash
# If result coverage is low because of incomplete backfill
python3 scripts/backfill_events.py --start-date 2015-01-01 --end-date 2025-10-19
```

**Investigate First:**
- Why are enhanced runner fields 0% if migration exists?
- Is low results coverage due to future races or incomplete backfill?
- Check field mapping in `utils/entity_extractor.py` and fetcher transform functions

---

### 3. Racing API - Enrichment (18 columns, 11 with gaps)

**What it is:** Horse pedigree and metadata from `/v1/horses/{id}/pro`

**Tables affected:**
- `ra_mst_horses` - Horse metadata
- `ra_horse_pedigree` - Complete lineage

**Status:**
- ✅ Pedigree coverage: 99.93% (sire_id, dam_id, damsire_id populated)
- ✅ Pedigree names: 100% (sire, dam, damsire populated)
- ⚠️ Horse metadata has gaps:

**Gap Details - ra_mst_horses (111,669 records):**
- `age` - 0% (0 / 111,669) - **Should be calculated from DOB**
- `breeder` - 0% (0 / 111,669) - **Data exists in ra_horse_pedigree**
- `colour_code` - 24.23% (27,056 / 111,669) - **Should be ~100%**
- `region` - 28.76% (32,116 / 111,669) - **Should be higher**

**How to fill:**

1. **Calculate age from DOB:**
```sql
UPDATE ra_mst_horses
SET age = EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob)),
    updated_at = NOW()
WHERE dob IS NOT NULL;
```

2. **Migrate breeder from pedigree table:**
```sql
UPDATE ra_mst_horses h
SET breeder = p.breeder,
    updated_at = NOW()
FROM ra_horse_pedigree p
WHERE h.id = p.horse_id
  AND p.breeder IS NOT NULL
  AND h.breeder IS NULL;
```

3. **Investigate colour_code and region gaps:**
```bash
# Check if API response includes these fields
# Review entity_extractor.py field mapping
# May need to re-run enrichment for affected horses
```

**Gap in ra_horse_pedigree:**
- `region` - 36.42% (40,639 / 111,594) - Lower than expected

---

### 4. External - Geocoding Required (2 columns, 2 with gaps)

**What it is:** Geographic coordinates from external geocoding service

**Table:** `ra_mst_courses` (101 records)

**Status:**
- ❌ `longitude` - 0% (0 / 101)
- ❌ `latitude` - 0% (0 / 101)

**How to fill:**

1. **Apply migration:**
```bash
psql -f migrations/021_add_course_coordinates.sql
```

2. **Run populate script:**
```bash
python3 scripts/update_course_coordinates.py
```

**Duration:** < 5 minutes

---

### 5. Not Implemented - Future Features (93 columns, 93 with gaps)

**What it is:** Tables/columns for features not yet built

**Tables (all at 0 records):**
- `ra_entity_combinations` (16 columns) - Performance analysis for entity pairs
- `ra_performance_by_distance` (17 columns) - Distance-based performance metrics
- `ra_performance_by_venue` (17 columns) - Venue-based performance metrics
- `ra_runner_statistics` (21 columns) - Individual runner statistics
- `ra_runner_supplementary` (22 columns) - Additional runner data

**Status:** ❌ Not implemented - all empty

**How to fill:**
These are placeholder tables for future ML features. No action needed unless implementing these features.

---

### 6. Odds Worker System (93 columns, 30 with gaps)

**What it is:** Separate odds collection system (not part of this codebase)

**Tables:**
- `ra_odds_historical` (2.4M records, 10.8 years)
- `ra_odds_live` (41K records)
- `ra_odds_live_latest` (0 records - live snapshot)
- `ra_odds_statistics` (0 records - calculated)
- `ra_runner_odds` (0 records - runner-level odds)

**Status:** Managed by DarkHorses-Odds-Workers repository

**Action:** None needed - separate system

---

### 7. System-Generated (56 columns, 17 with gaps)

**What it is:** Auto-generated IDs and timestamps

**Columns:** `id`, `created_at`, `updated_at`

**Status:** ✅ Mostly complete (timestamps may be NULL for system inserts)

**Action:** None needed - handled automatically

---

### 8. Extracted from Races/Results (6 columns, 2 with gaps)

**What it is:** Entity IDs and names discovered during race extraction

**Tables:**
- `ra_mst_jockeys` - id, name (100%)
- `ra_mst_trainers` - id, name (100%)
- `ra_mst_owners` - id, name (100%)
- `ra_mst_sires` - id, name (99.95%)
- `ra_mst_dams` - id, name (100%)
- `ra_mst_damsires` - id, name (99.97%)

**Status:** ✅ Complete (names populated via migration 026)

**Action:** None needed

---

### 9. Unknown Source - Investigate (3 columns, 3 with gaps)

**What it is:** Columns where data source is unclear

**Gaps:**
- `ra_mst_sires.horse_id` - 0% (0 / 2,143) - Not clear if this should map to ra_mst_horses.id
- `ra_mst_dams.horse_id` - 0% (0 / 48,372) - Same question
- `ra_mst_damsires.horse_id` - 0% (0 / 3,041) - Same question

**Investigation needed:**
- Determine if these should reference actual horse records
- May be for sires/dams/damsires that are also racehorses
- Check API response structure for pedigree entities

**Action:** Research API documentation and schema design intent

---

### 10. Racing API - Reference Data (9 columns, 0 with gaps)

**What it is:** Static reference tables from API

**Tables:**
- `ra_mst_courses` - Course details (101 records, 100% except coordinates)
- `ra_mst_bookmakers` - Bookmaker list (22 records, 100%)
- `ra_mst_regions` - Region codes (14 records, 100%)

**Status:** ✅ Complete

**Action:** None needed

---

## Priority Action Plan

### Priority 0 - CRITICAL (Do Today)

1. **Fix pedigree statistics script schema issue**
   - Error: References `ra_mst_horses.sire_name` column that doesn't exist
   - Fix: Update to use `ra_mst_sires.name` with proper JOIN
   - Impact: Blocks 117 critical statistics columns

2. **Investigate enhanced runner fields (0% populated)**
   - 7 fields added in migration 011 but not being captured
   - Check fetchers/results_fetcher.py:333 field mapping
   - Impact: 9.1M missing data points (7 fields × 1.3M runners)

3. **Apply course coordinates**
   - Run migration 021
   - Execute populate script
   - Impact: 202 missing values (2 fields × 101 courses)

### Priority 1 - HIGH (This Week)

4. **Calculate horse ages from DOB**
   - Simple SQL UPDATE
   - Impact: 111,669 empty `age` values

5. **Migrate breeder from pedigree table**
   - Simple SQL UPDATE with JOIN
   - Impact: 111,669 empty `breeder` values

6. **Run pedigree statistics calculation**
   - After fixing script schema issues
   - Duration: 30-60 minutes
   - Impact: 117 empty statistics columns

7. **Investigate results coverage**
   - Determine if 8-9% is expected (future races) or incomplete backfill
   - May need historical results backfill
   - Impact: Potentially 1.2M missing result records

### Priority 2 - MEDIUM (This Month)

8. **Investigate colour_code gap (24% vs expected 100%)**
   - Check API response and field mapping
   - May need re-enrichment for affected horses

9. **Investigate region gaps**
   - ra_mst_horses.region: 28.76%
   - ra_horse_pedigree.region: 36.42%
   - Determine if API limitation or mapping issue

10. **Investigate race_class gap (78.55%)**
    - Should be higher coverage
    - Check if API data issue or mapping problem

### Priority 3 - LOW (As Needed)

11. **Research horse_id in pedigree master tables**
    - Determine design intent
    - Decide if should populate or remove columns

12. **Consider implementing future feature tables**
    - ra_entity_combinations
    - ra_performance_by_* tables
    - ra_runner_statistics/supplementary
    - Only if ML features require them

---

## Data Completeness by Table

### ✅ Complete (100% core data)

- `ra_mst_bookmakers` (22 records)
- `ra_mst_regions` (14 records)
- `ra_mst_courses` (101 records) - except coordinates

### 🟢 Mostly Complete (95-99%)

- `ra_mst_horses` (111,669 records) - 99.87% core, gaps in age/breeder/colour_code/region
- `ra_mst_jockeys` (3,483 records) - 99.08% statistics
- `ra_mst_trainers` (2,781 records) - 99.71% statistics (45.85% have location)
- `ra_mst_owners` (48,168 records) - 99.89% statistics
- `ra_horse_pedigree` (111,594 records) - 99.93% complete (36.42% have region)

### 🟡 Partial Implementation (50-94%)

- `ra_races` (136,960 records) - 100% core, 78.55% have race_class
- `ra_runners` (1,326,595 records) - 100% pre-race, 8-9% results, 0% enhanced fields
- `ra_odds_historical` (2.4M records) - Various gaps in optional fields

### 🔴 Empty / Not Implemented (0%)

- `ra_mst_sires` (2,143 records) - Names 99.95%, ALL statistics 0%
- `ra_mst_dams` (48,372 records) - Names 100%, ALL statistics 0%
- `ra_mst_damsires` (3,041 records) - Names 99.97%, ALL statistics 0%
- `ra_entity_combinations` (0 records) - Not implemented
- `ra_performance_by_distance` (0 records) - Not implemented
- `ra_performance_by_venue` (0 records) - Not implemented
- `ra_runner_statistics` (0 records) - Not implemented
- `ra_runner_supplementary` (0 records) - Not implemented
- `ra_odds_live_latest` (0 records) - Live snapshot (expected empty)
- `ra_odds_statistics` (0 records) - Not implemented
- `ra_runner_odds` (0 records) - Not implemented

---

## Verification Queries

### Check Overall Data Completeness
```sql
-- Summary across all key tables
SELECT
    'Races' as entity,
    COUNT(*) as total,
    MIN(date) as earliest,
    MAX(date) as latest
FROM ra_races
UNION ALL
SELECT 'Runners', COUNT(*),
    (SELECT MIN(r.date) FROM ra_races r JOIN ra_runners ru ON r.id = ru.race_id),
    (SELECT MAX(r.date) FROM ra_races r JOIN ra_runners ru ON r.id = ru.race_id)
FROM ra_runners
UNION ALL
SELECT 'Horses', COUNT(*), NULL, NULL FROM ra_mst_horses
UNION ALL
SELECT 'Jockeys', COUNT(*), NULL, NULL FROM ra_mst_jockeys
UNION ALL
SELECT 'Trainers', COUNT(*), NULL, NULL FROM ra_mst_trainers
UNION ALL
SELECT 'Owners', COUNT(*), NULL, NULL FROM ra_mst_owners;
```

### Check Pedigree Statistics Status
```sql
SELECT
    'Sires' as entity,
    COUNT(*) as total,
    COUNT(overall_win_percent) as with_stats,
    ROUND(COUNT(overall_win_percent)::numeric / COUNT(*)::numeric * 100, 2) as stats_pct
FROM ra_mst_sires
UNION ALL
SELECT 'Dams', COUNT(*), COUNT(overall_win_percent),
    ROUND(COUNT(overall_win_percent)::numeric / COUNT(*)::numeric * 100, 2)
FROM ra_mst_dams
UNION ALL
SELECT 'Damsires', COUNT(*), COUNT(overall_win_percent),
    ROUND(COUNT(overall_win_percent)::numeric / COUNT(*)::numeric * 100, 2)
FROM ra_mst_damsires;
```

### Check Enhanced Runner Fields
```sql
SELECT
    COUNT(*) as total_runners,
    COUNT(starting_price_decimal) as with_decimal_odds,
    COUNT(finishing_time) as with_time,
    COUNT(race_comment) as with_comment,
    COUNT(jockey_silk_url) as with_silk,
    ROUND(COUNT(starting_price_decimal)::numeric / COUNT(*)::numeric * 100, 2) as decimal_odds_pct,
    ROUND(COUNT(finishing_time)::numeric / COUNT(*)::numeric * 100, 2) as time_pct
FROM ra_runners;
```

### Check Results Coverage
```sql
SELECT
    COUNT(*) as total_runners,
    COUNT(position) as with_position,
    COUNT(starting_price) as with_sp,
    ROUND(COUNT(position)::numeric / COUNT(*)::numeric * 100, 2) as results_pct,
    -- Breakdown by date range
    COUNT(*) FILTER (WHERE race_id IN (SELECT id FROM ra_races WHERE date < CURRENT_DATE)) as past_races,
    COUNT(position) FILTER (WHERE race_id IN (SELECT id FROM ra_races WHERE date < CURRENT_DATE)) as past_with_results
FROM ra_runners;
```

---

## Summary Statistics

**Database Size:**
- 24 tables
- 625 columns total
- ~4.2M total records (excluding odds)

**Data Completeness:**
- 189 columns (30.2%) fully populated ✅
- 247 columns (39.5%) with minor gaps (90-99%) 🟢
- 69 columns (11.0%) with significant gaps (1-89%) 🟡
- 120 columns (19.2%) completely empty ❌

**Critical Issues:**
1. Pedigree statistics: 117 columns at 0% (script has schema bug)
2. Enhanced runner fields: 7 columns at 0% (not being captured)
3. Course coordinates: 2 columns at 0% (migration not applied)
4. Horse metadata: 4 columns with gaps (age, breeder, colour_code, region)

**Data Timeline:**
- Race/runner data: 2015-01-01 to 2025-10-19 (10.8 years)
- Odds data: 2015-01-01 to 2025-10-19 (10.8 years)
- Pedigree data: Recent only (2025-10-14 to 2025-10-20)

---

**Next Steps:**
1. Fix pedigree statistics script
2. Investigate enhanced runner field mapping
3. Apply course coordinates migration
4. Run Priority 0 and Priority 1 tasks
5. Monitor data quality with verification queries

**Last Updated:** 2025-10-20
**Audit Source:** `docs/COMPLETE_DATABASE_AUDIT.json`
