# Complete Database Audit Summary

**Audit Date:** 2025-10-20
**Database:** DarkHorses Masters Workers Production
**Total Tables:** 24
**Total Columns:** 625

## Executive Summary

This comprehensive audit analyzed all 625 columns across 24 tables in the database to identify data completeness, sources, and gaps.

### Key Findings

- **30.2% of columns (189)** are 100% populated
- **51.0% of columns (319)** are completely empty (0% populated)
- **9.0% of columns (56)** have partial data (1-49% populated)
- **8 core transaction tables** contain the primary racing data
- **12 master/reference tables** contain entity data
- **4 odds tables** managed by separate odds workers

### Population Distribution

| Range | Count | Percentage |
|-------|-------|------------|
| 100% populated | 189 | 30.2% |
| 95-99% populated | 44 | 7.0% |
| 90-94% populated | 5 | 0.8% |
| 50-89% populated | 12 | 1.9% |
| 1-49% populated | 56 | 9.0% |
| 0% populated | 319 | 51.0% |

## Critical Data Gaps Requiring Immediate Attention

### 1. Enhanced Runner Fields (Migration 011) - NOT POPULATED

**Status:** Migration created but NOT applied to database

**Affected Table:** `ra_runners` (1.3M records)

**Missing Fields (0% populated):**
- `finishing_time` - Race finishing time (critical for ML)
- `starting_price_decimal` - Decimal odds format (critical for ML)
- `race_comment` - Race commentary/running notes
- `jockey_silk_url` - Jockey silk image URL
- `overall_beaten_distance` - Alternative distance metric
- `jockey_claim_lbs` - Jockey weight allowance
- `weight_stones_lbs` - Weight in UK format

**Action Required:**
1. Apply migration `migrations/add_enhanced_statistics_columns.sql`
2. Backfill data from existing results using `/results` API
3. Update `results_fetcher.py` to populate these fields going forward

**Impact:** These fields are critical for ML model features and UI enhancements. Currently 100% missing.

---

### 2. Course Coordinates - 0% Populated

**Status:** Migration 021 created but NOT applied

**Affected Table:** `ra_mst_courses` (101 records)

**Missing Fields:**
- `longitude` (0% populated, 101 NULL)
- `latitude` (0% populated, 101 NULL)

**Action Required:**
1. Apply migration `migrations/021_add_course_coordinates.sql`
2. Run script `scripts/update_course_coordinates.py` to populate
3. Source: Can be fetched from Racing API or external geocoding service

**Impact:** Required for geographical analysis and distance calculations.

---

### 3. Pedigree Statistics - 100% Unpopulated

**Affected Tables:**
- `ra_mst_sires` (2,143 records) - 39 empty columns
- `ra_mst_dams` (48,372 records) - 39 empty columns
- `ra_mst_damsires` (3,041 records) - 39 empty columns

**Empty Statistics Fields (per table):**
- `overall_win_percent`, `overall_ae_index`
- `best_class`, `best_class_ae`
- `best_distance`, `best_distance_ae`
- `analysis_last_updated`, `data_quality_score`
- All `class_1/2/3_*` fields (9 columns each)
- All `distance_1/2/3_*` fields (15 columns each)

**Action Required:**
1. Implement pedigree statistics workers (similar to jockey/trainer/owner workers)
2. Calculate statistics from `ra_runners` data
3. Schedule periodic updates

**Impact:** Pedigree performance analysis is completely unavailable. These are advanced analytics fields.

---

### 4. Horse Metadata Gaps

**Table:** `ra_mst_horses` (111,669 records)

**Partial Population:**
- `colour_code`: 24.23% populated (27,056 / 111,669) - 84,613 NULL
- `region`: 28.76% populated (32,116 / 111,669) - 79,553 NULL
- `dob`: 99.87% populated (147 missing)
- `sex_code`: 99.87% populated (147 missing)
- `colour`: 99.87% populated (147 missing)

**Completely Empty:**
- `age`: 0% populated (should be calculated from DOB)
- `breeder`: 0% populated (should migrate from `ra_horse_pedigree.breeder`)

**Action Required:**
1. Investigate why `colour_code` and `region` are only ~25-30% populated
2. Implement `age` calculation from `dob` (simple calculation)
3. Migrate `breeder` from `ra_horse_pedigree` table (99.93% available there)
4. Re-enrich the 147 horses missing `dob`, `sex_code`, `colour`

**Impact:** Basic horse metadata incomplete for ML features.

---

### 5. Result Data Population - Only 8-9% of Runners

**Table:** `ra_runners` (1,326,595 records)

**Result Fields (should populate after race completion):**
- `position`: 8.41% populated (111,508 / 1,326,595) - 91.59% missing
- `distance_beaten`: 8.90% populated (118,101) - 91.10% missing
- `starting_price`: 8.90% populated (118,097) - 91.10% missing
- `weight_st_lbs`: 9.11% populated (120,897) - 90.89% missing
- `comment`: 8.91% populated (118,146) - 91.09% missing

**Analysis:**
- Only ~9% of runners have result data populated
- Suggests either:
  - Most races in database are future races (racecards)
  - Results fetcher not running consistently
  - Historical backfill incomplete

**Action Required:**
1. Check ratio of future vs past races in `ra_races`
2. Verify results fetcher is running daily
3. Consider historical results backfill for 2015-2025

**Impact:** Limited historical result data reduces ML training dataset size.

---

### 6. Race Metadata Gaps

**Table:** `ra_races` (136,960 records)

**Low Population Fields:**
- `race_class`: 78.55% populated (107,578) - 29,382 missing (21.45%)
- `prize`: 5.23% populated (7,166) - 129,794 missing
- `pattern`: 0.52% populated (711) - 136,249 missing
- `betting_forecast`: 0.24% populated (327)
- `verdict`: 0.24% populated (327)
- `tip`: 0.23% populated (319)

**Completely Empty:**
- `race_number`, `going_detailed`, `stalls`, `rail_movements`, `weather`, `meet_id`

**Analysis:**
- `race_class` missing for 21% of races (should be higher)
- `prize` only available for 5% of races (may be API limitation)
- Editorial fields (`tip`, `verdict`, `betting_forecast`) only for ~0.2% (premium content)

**Action Required:**
1. Investigate why `race_class` is missing for 21% of races
2. Determine if `prize`, `pattern` are available from API
3. Document which fields are optional/premium content

**Impact:** Some ML features may be unavailable for races without class/prize data.

---

## Data Sources Classification

### A. API Sources (Racing API)

**Primary Race Data:**
- `/v1/racecards/pro` - Race and runner metadata (pre-race)
- `/v1/results` - Result data (post-race)
- `/v1/horses/{id}/pro` - Complete horse data with pedigree (enrichment)

**Entity Data:**
- `/v1/jockeys` - Jockey master data
- `/v1/trainers` - Trainer master data
- `/v1/owners` - Owner master data
- `/v1/courses` - Course master data
- `/v1/bookmakers` - Bookmaker master data

### B. Calculated Fields (Workers)

**Statistics Workers (Implemented):**
- Jockey statistics (win rate, recent form)
- Trainer statistics (win rate, recent form)
- Owner statistics (win rate, recent form)

**Statistics Workers (NOT Implemented):**
- Pedigree statistics (sires, dams, damsires)
- Horse performance by distance/venue
- Entity combination statistics

**Simple Calculations (NOT Implemented):**
- Horse age (from DOB)
- Win percentages for pedigree tables

### C. System-Generated

- `id` (primary keys)
- `created_at`, `updated_at` (timestamps)
- Auto-incremented sequences

### D. External/Manual Sources

- Course coordinates (requires geocoding or manual entry)
- Data quality scores (requires implementation)

---

## Recommendations by Priority

### Priority 1: Critical - Apply Existing Migrations

1. **Apply Enhanced Runner Fields Migration**
   - File: `migrations/add_enhanced_statistics_columns.sql`
   - Impact: Unlocks 6 critical ML features
   - Effort: Low (migration exists)

2. **Apply Course Coordinates Migration**
   - File: `migrations/021_add_course_coordinates.sql`
   - Run: `scripts/update_course_coordinates.py`
   - Impact: Enables geographical analysis
   - Effort: Low (migration + script exist)

### Priority 2: High - Fix Data Quality Issues

3. **Investigate Horse Metadata Gaps**
   - Why is `colour_code` only 24% populated?
   - Why is `region` only 29% populated?
   - Re-enrich 147 horses missing basic metadata

4. **Implement Simple Calculations**
   - Calculate `age` from `dob` in `ra_mst_horses`
   - Migrate `breeder` from `ra_horse_pedigree` to `ra_mst_horses`
   - Calculate `overall_win_percent` for pedigree tables

5. **Verify Results Fetcher Coverage**
   - Only 8-9% of runners have result data
   - Check if historical backfill is needed
   - Ensure daily results fetcher is running

### Priority 3: Medium - Implement Missing Workers

6. **Implement Pedigree Statistics Workers**
   - Sire statistics calculation
   - Dam statistics calculation
   - Damsire statistics calculation
   - Similar pattern to existing jockey/trainer workers

7. **Implement Performance Analysis**
   - Horse performance by distance
   - Horse performance by venue
   - Entity combination statistics

### Priority 4: Low - Optional/Premium Features

8. **Document Optional Fields**
   - Identify fields that are legitimately optional
   - Document premium/editorial content fields
   - Mark fields that are API limitations vs implementation gaps

9. **Clean Up Empty Tables**
   - `ra_entity_combinations` (0 records)
   - `ra_performance_by_distance` (0 records)
   - `ra_performance_by_venue` (0 records)
   - Decide: implement or remove

---

## Tables Summary

### Core Transaction Tables (High Importance)

| Table | Records | Columns | 100% Pop | 0% Pop | Notes |
|-------|---------|---------|----------|--------|-------|
| `ra_races` | 136,960 | 34 | 20 | 6 | Race metadata, some gaps |
| `ra_runners` | 1,326,595 | 42 | 21 | 14 | Runner data, result fields low |
| `ra_race_results` | 1,278,821 | 4 | 4 | 0 | Minimal table, fully populated |

### Master/Reference Tables (Medium Importance)

| Table | Records | Columns | 100% Pop | 0% Pop | Notes |
|-------|---------|---------|----------|--------|-------|
| `ra_mst_horses` | 111,669 | 15 | 7 | 2 | Some metadata gaps |
| `ra_mst_jockeys` | 3,483 | 22 | 12 | 0 | Well populated |
| `ra_mst_trainers` | 2,781 | 23 | 13 | 0 | Well populated |
| `ra_mst_owners` | 48,168 | 24 | 15 | 0 | Well populated |
| `ra_mst_courses` | 101 | 8 | 6 | 2 | Missing coordinates |
| `ra_mst_bookmakers` | 22 | 6 | 6 | 0 | Fully populated |
| `ra_horse_pedigree` | 111,594 | 11 | 8 | 0 | Well populated |

### Pedigree Tables (Low Importance - Statistics Not Implemented)

| Table | Records | Columns | 100% Pop | 0% Pop | Notes |
|-------|---------|---------|----------|--------|-------|
| `ra_mst_sires` | 2,143 | 47 | 5 | 39 | Statistics unpopulated |
| `ra_mst_dams` | 48,372 | 47 | 5 | 39 | Statistics unpopulated |
| `ra_mst_damsires` | 3,041 | 47 | 5 | 39 | Statistics unpopulated |

### Odds Tables (Separate System)

| Table | Records | Columns | 100% Pop | 0% Pop | Notes |
|-------|---------|---------|----------|--------|-------|
| `ra_odds_historical` | 2,434,732 | 36 | 21 | 0 | Managed by odds workers |
| `ra_odds_live` | 203,430 | 33 | 22 | 1 | Managed by odds workers |
| `ra_odds_live_latest` | 13,166 | 28 | 28 | 0 | Managed by odds workers |
| `ra_runner_odds` | 13,166 | 9 | 9 | 0 | Managed by odds workers |
| `ra_odds_statistics` | 7,935 | 27 | 26 | 1 | Managed by odds workers |

### Empty/Placeholder Tables

| Table | Records | Columns | Notes |
|-------|---------|---------|-------|
| `ra_entity_combinations` | 0 | 16 | Not yet implemented |
| `ra_performance_by_distance` | 0 | 17 | Not yet implemented |
| `ra_performance_by_venue` | 0 | 16 | Not yet implemented |
| `ra_runner_statistics` | 0 | 35 | Not yet implemented |
| `ra_runner_supplementary` | 0 | 8 | Not yet implemented |

---

## Next Steps

1. **Immediate Actions (This Week):**
   - Apply `add_enhanced_statistics_columns.sql` migration
   - Apply `021_add_course_coordinates.sql` migration
   - Run course coordinates population script
   - Verify results fetcher is running daily

2. **Short-term (This Month):**
   - Investigate horse metadata gaps (colour_code, region)
   - Implement age calculation from DOB
   - Migrate breeder field from pedigree table
   - Document which empty fields are intentional vs gaps

3. **Medium-term (Next Quarter):**
   - Implement pedigree statistics workers
   - Implement performance analysis tables
   - Consider historical results backfill for 2015-2025
   - Optimize data collection for fields with low population

4. **Long-term (Future):**
   - Evaluate unused tables (entity_combinations, performance_by_*)
   - Implement advanced analytics (data_quality_score, AE index)
   - Consider additional API endpoints for missing fields

---

## Files Generated

- **Full Audit:** `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/COMPLETE_DATABASE_AUDIT.json`
- **Summary:** This file

## Methodology

This audit was performed by:
1. Connecting to production Supabase database
2. Querying all `ra_*` tables from `information_schema`
3. For each column: checking NULL count, empty string count, population percentage
4. Analyzing patterns to determine likely data sources
5. Identifying critical gaps and recommendations

**Total Analysis Time:** ~45 seconds
**Database Connection:** Direct SQL queries via psycopg2
**Coverage:** 100% of tables and columns
