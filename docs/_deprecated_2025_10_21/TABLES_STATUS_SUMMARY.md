# Database Tables Status Summary

**Generated:** 2025-10-20
**Purpose:** Quick reference - status of all 24 tables at a glance

---

## Master Tables (10 tables)

| Table | Records | Columns | Core Data | Statistics | Coordinates | Status |
|-------|---------|---------|-----------|------------|-------------|--------|
| ra_mst_courses | 101 | 8 | ✅ 100% | N/A | ❌ 0% | 🟡 Missing coords |
| ra_mst_bookmakers | 22 | 6 | ✅ 100% | N/A | N/A | ✅ Complete |
| ra_mst_regions | 14 | 3 | ✅ 100% | N/A | N/A | ✅ Complete |
| ra_mst_horses | 111,669 | 15 | 🟢 99.87% | N/A | N/A | 🟡 Gaps in age/breeder/colour_code/region |
| ra_mst_jockeys | 3,483 | 22 | ✅ 100% | 🟢 99.08% | N/A | ✅ Complete |
| ra_mst_trainers | 2,781 | 23 | ✅ 100% | 🟢 99.71% | N/A | 🟡 Location 45.85% |
| ra_mst_owners | 48,168 | 24 | ✅ 100% | 🟢 99.89% | N/A | ✅ Complete |
| ra_mst_sires | 2,143 | 47 | ✅ 99.95% | ❌ 0% | N/A | 🔴 No statistics |
| ra_mst_dams | 48,372 | 47 | ✅ 100% | ❌ 0% | N/A | 🔴 No statistics |
| ra_mst_damsires | 3,041 | 47 | 🟢 99.97% | ❌ 0% | N/A | 🔴 No statistics |

**Summary:**
- ✅ Complete: 3 tables (bookmakers, regions, jockeys/trainers/owners stats done)
- 🟡 Minor gaps: 3 tables (courses, horses, trainers)
- 🔴 Major gaps: 3 tables (sires/dams/damsires - all statistics missing)

---

## Transaction Tables (4 tables)

| Table | Records | Date Range | Core | Results | Enhanced | Status |
|-------|---------|------------|------|---------|----------|--------|
| ra_races | 136,960 | 2015-2025 (10.8y) | ✅ 100% | N/A | N/A | 🟡 Race class 78.55% |
| ra_runners | 1,326,595 | 2015-2025 (10.8y) | ✅ 100% | 🔴 8.4% | ❌ 0% | 🔴 Results/enhanced fields |
| ra_race_results | 111,479 | 2015-2025 | ✅ 100% | ✅ 100% | N/A | ✅ Complete |
| ra_horse_pedigree | 111,594 | 2025 (recent) | ✅ 99.93% | N/A | N/A | 🟡 Region 36.42% |

**Summary:**
- ✅ Complete: 1 table (ra_race_results)
- 🟡 Minor gaps: 2 tables (ra_races, ra_horse_pedigree)
- 🔴 Major gaps: 1 table (ra_runners - results and enhanced fields)

---

## Odds Tables (5 tables - Separate System)

| Table | Records | Date Range | Status | Managed By |
|-------|---------|------------|--------|------------|
| ra_odds_historical | 2,434,732 | 2015-2025 (10.8y) | 🟢 Active | Odds Workers |
| ra_odds_live | 41,024 | Current | 🟢 Active | Odds Workers |
| ra_odds_live_latest | 0 | Live snapshot | ⚪ Empty (expected) | Odds Workers |
| ra_odds_statistics | 0 | N/A | ⚪ Not implemented | Odds Workers |
| ra_runner_odds | 0 | N/A | ⚪ Not implemented | Odds Workers |

**Summary:** Managed by separate DarkHorses-Odds-Workers repository

---

## Performance Tables (5 tables - Not Implemented)

| Table | Records | Status | Purpose |
|-------|---------|--------|---------|
| ra_entity_combinations | 0 | ⚪ Not implemented | Entity pair performance |
| ra_performance_by_distance | 0 | ⚪ Not implemented | Distance-based metrics |
| ra_performance_by_venue | 0 | ⚪ Not implemented | Venue-based metrics |
| ra_runner_statistics | 0 | ⚪ Not implemented | Individual runner stats |
| ra_runner_supplementary | 0 | ⚪ Not implemented | Additional runner data |

**Summary:** Future features - no action needed unless implementing

---

## Overall Status by Category

### ✅ Production Ready (8 tables)
- ra_mst_bookmakers
- ra_mst_regions
- ra_mst_jockeys
- ra_mst_trainers (except location gaps)
- ra_mst_owners
- ra_race_results
- ra_odds_historical
- ra_odds_live

### 🟡 Minor Gaps (6 tables)
- ra_mst_courses (missing coordinates)
- ra_mst_horses (missing age/breeder/colour_code/region)
- ra_races (race_class 78.55%)
- ra_horse_pedigree (region 36.42%)
- ra_mst_trainers (location 45.85%)

### 🔴 Major Gaps (3 tables)
- ra_mst_sires (0% statistics - 39 columns empty)
- ra_mst_dams (0% statistics - 39 columns empty)
- ra_mst_damsires (0% statistics - 39 columns empty)
- ra_runners (0% enhanced fields, 8.4% results)

### ⚪ Not Implemented (7 tables)
- 5 performance tables (future features)
- 2 odds tables (odds statistics, runner odds)

---

## Critical Data Gaps Summary

### Gap 1: Pedigree Statistics (P0 - Critical)
**Tables:** ra_mst_sires, ra_mst_dams, ra_mst_damsires
**Columns:** 117 (39 per table × 3 tables)
**Impact:** 53,556 entities missing all statistics
**Cause:** Script has schema bug
**Fix:** Update populate_pedigree_statistics.py

### Gap 2: Enhanced Runner Fields (P0 - Critical)
**Table:** ra_runners
**Columns:** 7 (starting_price_decimal, finishing_time, race_comment, etc.)
**Impact:** 1.3M runners × 7 = 9.3M missing values
**Cause:** Fetchers not capturing fields
**Fix:** Update field mapping in fetchers

### Gap 3: Course Coordinates (P0 - Critical)
**Table:** ra_mst_courses
**Columns:** 2 (longitude, latitude)
**Impact:** 101 courses missing coordinates
**Cause:** Migration not applied
**Fix:** Run migration 021 + populate script

### Gap 4: Horse Metadata (P1 - High)
**Table:** ra_mst_horses
**Columns:** 4 (age, breeder, colour_code, region)
**Impact:** 111,669 horses with gaps
**Cause:** Not calculated (age), not migrated (breeder), API/mapping issue (others)
**Fix:** SQL updates + investigation

### Gap 5: Results Coverage (P1 - High)
**Table:** ra_runners
**Columns:** 5 (position, distance_beaten, prize_won, starting_price, finishing_time)
**Impact:** 1.2M runners missing results (91.6%)
**Cause:** Unknown - future races or incomplete backfill
**Fix:** Investigation needed

---

## Data Volume Summary

**Total Records:** ~4.2M (excluding odds: ~1.6M)

**By Category:**
- Master entities: 217,613 records
  - Horses: 111,669
  - Owners: 48,168
  - Dams: 48,372
  - Jockeys: 3,483
  - Trainers: 2,781
  - Sires: 2,143
  - Damsires: 3,041
  - Courses: 101
  - Bookmakers: 22
  - Regions: 14

- Transactions: 1,575,028 records
  - Runners: 1,326,595
  - Races: 136,960
  - Pedigree: 111,594 (links horses to lineage)
  - Race results: 111,479 (subset of runners with results)

- Odds: 2,475,756 records
  - Historical: 2,434,732
  - Live: 41,024

**Date Coverage:**
- Primary data: 2015-01-01 to 2025-10-19 (10.8 years)
- Pedigree: Recent only (2025-10-14 to 2025-10-20)

---

## Legend

**Status Icons:**
- ✅ Complete (100% or 95-100%)
- 🟢 Mostly complete (90-94%)
- 🟡 Minor gaps (50-89%)
- 🔴 Major gaps (1-49%)
- ❌ Empty (0%)
- ⚪ Not implemented (expected empty)

**Priority Levels:**
- **P0 (Critical):** Must fix immediately - blocking other work
- **P1 (High):** Should fix this week - important for data quality
- **P2 (Medium):** Fix this month - improves completeness
- **P3 (Low):** Fix as needed - nice to have

---

**Quick Actions:**

```bash
# 1. Check current status
psql -c "SELECT COUNT(*) FROM ra_races; SELECT MIN(date), MAX(date) FROM ra_races;"

# 2. Fix coordinates (5 min)
psql -f migrations/021_add_course_coordinates.sql
python3 scripts/update_course_coordinates.py

# 3. Fix horse metadata (1 min)
psql -c "UPDATE ra_mst_horses SET age = EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob)) WHERE dob IS NOT NULL;"
psql -c "UPDATE ra_mst_horses h SET breeder = p.breeder FROM ra_horse_pedigree p WHERE h.id = p.horse_id;"

# 4. Fix pedigree statistics (after script fix - 60 min)
python3 scripts/populate_pedigree_statistics.py
```

---

**For detailed gap analysis, see:**
- `COMPLETE_DATA_FILLING_GUIDE.md` - Comprehensive guide
- `DATABASE_AUDIT_INDEX.md` - Master index
- `COMPLETE_DATABASE_AUDIT.json` - Raw data

**Last Updated:** 2025-10-20
