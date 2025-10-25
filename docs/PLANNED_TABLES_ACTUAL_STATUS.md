# Planned Tables - Actual Status Report

**Generated:** 2025-10-22
**Purpose:** Correct the master document based on actual database inspection

## Executive Summary

The master tables documentation classified 11 tables as "planned but not implemented." However, actual database inspection reveals a very different picture:

**Actually Implemented:**
- ✅ **6 tables are ALREADY POPULATED** with significant data
- ✅ **5 tables exist but are empty** (ready for population)

## Detailed Findings

### ✅ Tables Already Populated (Contrary to Documentation)

#### 1. ra_mst_regions
- **Documented Status:** ⚠️ NOT IMPLEMENTED (0 rows)
- **Actual Status:** ✅ POPULATED (14 rows)
- **Schema:**
  - `code` (VARCHAR, primary key) - Region code (e.g., 'gb', 'ire', 'fr')
  - `name` (VARCHAR) - Region name (e.g., 'Great Britain', 'Ireland')
  - `created_at` (TIMESTAMP)
- **Sample Data:**
  - gb: Great Britain
  - ire: Ireland
  - fr: France
  - uae: United Arab Emirates
  - aus: Australia
  - usa: United States
  - (plus 8 more)
- **Data Source:** Extracted from ra_mst_courses
- **Action Needed:** ✅ Update documentation only - table is operational

---

#### 2. ra_odds_live
- **Documented Status:** ⚠️ NOT IMPLEMENTED - Requires External Provider
- **Actual Status:** ✅ POPULATED (213,707 rows!)
- **Schema:** 32 columns including:
  - race_id, horse_id, bookmaker_id
  - odds_decimal, odds_fractional
  - race_date, off_dt, course, race_name
  - jockey, trainer, draw, form
  - bookmaker_name, bookmaker_type, market_type
  - market_status, in_play
  - odds_timestamp, fetched_at, updated_at
- **Sample Data:** Real betting odds from Bet365 and other bookmakers
- **Data Source:** External odds provider (already integrated!)
- **Action Needed:** ✅ Document existing integration - system is operational

---

#### 3. ra_odds_live_latest
- **Documented Status:** ⚠️ NOT IMPLEMENTED - Requires External Provider
- **Actual Status:** ✅ POPULATED (213,707 rows)
- **Schema:** 13 columns (snapshot table)
  - race_id, race_date, race_time, off_dt
  - course, race_name, runners
  - horse_name, horse_number
  - odds_decimal, odds_fractional
  - bookmaker_name, fetched_at
- **Purpose:** Latest odds only (faster queries than ra_odds_live)
- **Data Source:** External odds provider
- **Action Needed:** ✅ Document existing integration

---

#### 4. ra_odds_historical
- **Documented Status:** ⚠️ NOT IMPLEMENTED - Requires External Provider
- **Actual Status:** ✅ POPULATED (2,435,424 rows!!)
- **Schema:** 36 columns including:
  - racing_bet_data_id, date_of_race
  - country, track, race_time, going, race_type
  - distance, race_class, runners_count
  - horse_name, official_rating, age, weight
  - jockey, trainer, headgear, stall_number
  - sp_favorite_position, industry_sp
  - finishing_position, winning_distance
  - ip_min, ip_max, pre_race_min, pre_race_max
  - forecasted_odds
  - sp_win_return, ew_return, place_return
  - data_source, file_source
- **Sample Data:** Historical odds from 2017+ (Excel files imported)
- **Data Source:** Racing Bet Data Excel files + External provider
- **Reserved Space:** 1.3 GB (document was correct about size!)
- **Action Needed:** ✅ Document existing backfill - 2.4M historical records operational

---

#### 5. ra_odds_statistics
- **Documented Status:** ⚠️ NOT IMPLEMENTED - Requires ra_odds_* tables first
- **Actual Status:** ✅ POPULATED (8,701 rows)
- **Schema:** 11 columns including:
  - id, fetch_timestamp
  - race_id, races_count, horses_count
  - bookmakers_found, total_odds_fetched
  - bookmaker_list
  - fetch_duration_ms, errors_count
  - created_at
- **Purpose:** Tracks odds fetching operations and statistics
- **Data Source:** Calculated from odds fetching operations
- **Action Needed:** ✅ Document existing calculation logic

---

### 📋 Tables Exist But Are Empty (Need Population)

#### 6. ra_entity_combinations
- **Status:** ⚠️ EMPTY (0 rows) - Ready for population
- **Schema:** 16 columns
  - `id` (BIGINT, auto-generated primary key)
  - `entity1_type`, `entity1_id` (VARCHAR) - First entity in pair
  - `entity2_type`, `entity2_id` (VARCHAR) - Second entity in pair
  - `total_runs` (INTEGER) - Number of times this pair ran together
  - `wins`, `places_2nd`, `places_3rd` (INTEGER) - Performance stats
  - `win_percent`, `place_percent` (NUMERIC) - Success rates
  - `ae_index` (NUMERIC) - Actual vs Expected index
  - `profit_loss_1u` (NUMERIC) - Profit/loss per unit stake
  - `query_filters` (JSONB) - Optional filter conditions
  - `calculated_at`, `created_at` (TIMESTAMP)
- **Purpose:** Track entity pair combinations (jockey-horse, trainer-horse, etc.)
- **Constraint:** `chk_entity_comb_canonical_order` - Requires entity types in canonical order
- **Data Source:** Analysis of ra_runners
- **Script Created:** ✅ `scripts/populate_entity_combinations_v2.py`
- **Issue:** Need to resolve canonical order constraint (likely alphabetical)
- **Action Needed:** 🔧 Fix constraint handling, then populate

---

#### 7. ra_runner_supplementary
- **Status:** ⚠️ EMPTY (0 rows)
- **Columns:** Schema exists but cannot determine without data
- **Purpose:** Additional runner metadata
- **Data Source:** TBD - needs requirements definition
- **Action Needed:** 📝 Define what supplementary data is needed

---

#### 8. ra_runner_statistics
- **Status:** ⚠️ EMPTY (0 rows)
- **Purpose:** Individual runner performance metrics
- **Data Source:** Database calculation from ra_runners + ra_races
- **Action Needed:** 📊 Implement statistics calculation (Phase 2)

---

#### 9. ra_performance_by_distance
- **Status:** ⚠️ EMPTY (0 rows)
- **Purpose:** Distance-based performance analysis
- **Data Source:** Database calculation
- **Action Needed:** 📊 Implement distance analysis (Phase 2)

---

#### 10. ra_performance_by_venue
- **Status:** ⚠️ EMPTY (0 rows)
- **Purpose:** Venue-based performance analysis
- **Data Source:** Database calculation
- **Action Needed:** 📊 Implement venue analysis (Phase 2)

---

#### 11. ra_runner_odds
- **Status:** ⚠️ EMPTY (0 rows)
- **Purpose:** Runner-specific odds summaries
- **Data Source:** Aggregated from ra_odds_live/ra_odds_historical
- **Action Needed:** 📊 Implement odds aggregation (can be done now!)

---

## Scripts Created (This Session)

### ✅ Working Scripts

1. **populate_regions.py**
   - ✅ Successfully tested
   - ✅ Updates ra_mst_regions from ra_mst_courses
   - ✅ Handles existing data (upsert)
   - Can be run periodically to add new regions

### 🔧 Needs Fix

2. **populate_entity_combinations_v2.py**
   - ⚠️ Constraint error: `chk_entity_comb_canonical_order`
   - Issue: Entity types must be in specific order
   - Likely solution: Sort entity types alphabetically before insert
   - Example: ('jockey', 'horse') should be ('horse', 'jockey') if 'h' < 'j'

3. **populate_phase1_tables.py**
   - Master script to run all Phase 1 populations
   - Needs update based on actual table status

---

## Revised Implementation Priorities

### Already Operational (Document Only)
1. ✅ ra_mst_regions - Populated (14 regions)
2. ✅ ra_odds_live - Populated (213K rows)
3. ✅ ra_odds_live_latest - Populated (213K rows)
4. ✅ ra_odds_historical - Populated (2.4M rows)
5. ✅ ra_odds_statistics - Populated (8.7K rows)

### Phase 1 - Quick Wins (Ready to Implement)
6. 🔧 ra_entity_combinations - Fix constraint, then populate
7. 📝 ra_runner_supplementary - Define requirements first
8. 📊 ra_runner_odds - Aggregate from existing odds tables

### Phase 2 - Performance Analytics
9. 📊 ra_runner_statistics - Complex calculation
10. 📊 ra_performance_by_distance - Analysis script needed
11. 📊 ra_performance_by_venue - Analysis script needed

---

## Key Discoveries

### Discovery 1: Odds Integration Already Exists!
The documentation stated odds tables required external provider and were "NOT IMPLEMENTED."
**Reality:** External provider is ALREADY INTEGRATED with 2.4 million historical records!

**Questions for investigation:**
- What external provider is being used?
- Where is the odds fetching code? (likely in DarkHorses-Odds-Workers repo)
- How is the integration configured?
- What is the update schedule?

### Discovery 2: Table Schema Differs from Assumptions
The ra_entity_combinations table uses a flexible entity pair design (entity1/entity2)
rather than specific jockey/trainer/owner/horse columns. This is more powerful but requires
understanding the canonical order constraint.

### Discovery 3: ra_runner_supplementary Purpose Unclear
This table exists but its intended use is not clear. Need to determine what "supplementary"
data should be stored vs. what already exists in ra_runners (which has 57 columns).

---

## Recommended Next Steps

### Immediate (Documentation)
1. ✅ Update master document with actual table status
2. ✅ Document existing odds integration
3. ✅ Document ra_mst_regions is operational

### Short Term (Fix & Populate)
1. 🔧 Fix ra_entity_combinations canonical order constraint
2. 🔧 Test and populate ra_entity_combinations
3. 📊 Implement ra_runner_odds aggregation (data source ready)

### Medium Term (Analytics)
1. 📊 Implement ra_runner_statistics calculation
2. 📊 Implement ra_performance_by_distance analysis
3. 📊 Implement ra_performance_by_venue analysis

### Long Term (Investigation)
1. 🔍 Document existing odds provider integration
2. 🔍 Define ra_runner_supplementary requirements
3. 🔍 Consider whether ra_runner_supplementary is still needed

---

## Files Created This Session

1. `/scripts/populate_regions.py` - ✅ Working
2. `/scripts/populate_entity_combinations.py` - ⚠️ Old version (wrong schema)
3. `/scripts/populate_entity_combinations_v2.py` - 🔧 Needs constraint fix
4. `/scripts/populate_phase1_tables.py` - 🔧 Needs update
5. `/docs/PLANNED_TABLES_ACTUAL_STATUS.md` - 📋 This document

---

**Status as of 2025-10-22:** Major discrepancy found between documentation and reality.
**Impact:** HIGH - 5 of 11 "planned" tables are already operational with millions of rows.
**Priority:** Update master document immediately to reflect actual system state.
