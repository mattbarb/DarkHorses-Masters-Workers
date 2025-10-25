# Database Audit - Quick Reference Card

**Audit Date:** 2025-10-20
**Total Tables:** 24 | **Total Columns:** 625

---

## At a Glance

| Metric | Count | Percentage |
|--------|-------|------------|
| **Fully Populated (100%)** | 189 columns | 30.2% |
| **Mostly Populated (90-99%)** | 49 columns | 7.8% |
| **Partially Populated (1-89%)** | 68 columns | 10.9% |
| **Completely Empty (0%)** | 319 columns | 51.0% |

---

## Critical Issues (Fix Immediately)

### 🚨 1. Enhanced Runner Fields - 0% Populated
**Table:** `ra_runners` (1.3M records)
**Missing:** 7 critical ML fields
**Action:** Verify fetchers are populating these columns

### 🚨 2. Course Coordinates - 0% Populated
**Table:** `ra_mst_courses` (101 records)
**Missing:** longitude, latitude
**Action:** Apply migration 021 + run populate script

### ⚠️ 3. Horse Metadata Gaps
**Table:** `ra_mst_horses` (111K records)
**Issues:**
- `colour_code`: Only 24% populated (should be ~100%)
- `region`: Only 29% populated (should be higher)
- `age`: 0% populated (should calculate from DOB)
- `breeder`: 0% populated (data exists in pedigree table)

### ⚠️ 4. Results Coverage Low
**Table:** `ra_runners` (1.3M records)
**Issue:** Only 8-9% have result data (position, odds, times)
**Action:** Investigate if historical backfill needed

---

## Data by Category

### ✅ Well Populated (>95%)

**Core Entities:**
- Horses: 111,669 (pedigree 99.93% complete)
- Jockeys: 3,483 (statistics 97-100%)
- Trainers: 2,781 (statistics 95-100%)
- Owners: 48,168 (statistics 97-100%)
- Courses: 101 (except coordinates)
- Bookmakers: 22 (100% complete)

**Transactions:**
- Races: 136,960 (core fields 100%)
- Runners: 1,326,595 (pre-race data ~100%)
- Odds: 2.4M+ historical records

### ⚠️ Needs Attention (50-95%)

| Field | Table | Population | Issue |
|-------|-------|-----------|-------|
| `race_class` | ra_races | 78.55% | Should be higher |
| `ofr` | ra_runners | 74.15% | Official rating |
| `ts` | ra_runners | 79.78% | Topspeed rating |
| `headgear` | ra_runners | 37.05% | Optional field |
| `trainer.location` | ra_mst_trainers | 45.85% | API limitation? |

### ❌ Not Implemented (0%)

**Pedigree Statistics:** (39 empty columns × 3 tables)
- Sires, Dams, Damsires statistics
- Class performance breakdown
- Distance performance breakdown
- AE index calculations

**Performance Tables:** (5 empty tables)
- Entity combinations
- Performance by distance
- Performance by venue
- Runner statistics
- Runner supplementary

---

## Top 10 Missing Data by Volume

| Rank | Table.Column | Missing Records | % |
|------|--------------|-----------------|---|
| 1 | ra_odds_historical.race_name | 2,429,011 | 99.8% |
| 2-6 | ra_runners.* (optional fields) | 1,326,595 | 100% |
| 7 | ra_runners.finishing_time | 1,326,595 | 100% |
| 8 | ra_runners.starting_price_decimal | 1,326,595 | 100% |
| 9 | ra_runners.race_comment | 1,326,595 | 100% |
| 10 | ra_runners.jockey_silk_url | 1,326,595 | 100% |

---

## Data Sources

### From Racing API
- **Pre-race:** `/v1/racecards/pro` → races, runners, entities
- **Post-race:** `/v1/results` → positions, times, odds, comments
- **Enrichment:** `/v1/horses/{id}/pro` → pedigree, metadata
- **Entities:** `/v1/{entity_type}` → master data

### Calculated Locally
- **Implemented:** Jockey/trainer/owner statistics
- **Not Implemented:** Pedigree statistics, age, performance analysis

### System Generated
- Primary keys, timestamps, audit fields

### Missing/External
- Course coordinates (needs geocoding)
- Data quality scores (needs implementation)

---

## Tables by Status

### 🟢 Production Ready (8 tables)
- ra_mst_horses, ra_mst_jockeys, ra_mst_trainers, ra_mst_owners
- ra_mst_courses (except coordinates), ra_mst_bookmakers
- ra_races, ra_runners, ra_race_results
- ra_horse_pedigree

### 🟡 Partial Implementation (6 tables)
- ra_mst_sires, ra_mst_dams, ra_mst_damsires (basic data ✓, stats ✗)
- ra_odds_* tables (managed by separate system)

### 🔴 Not Implemented (5 tables)
- ra_entity_combinations (0 records)
- ra_performance_by_distance (0 records)
- ra_performance_by_venue (0 records)
- ra_runner_statistics (0 records)
- ra_runner_supplementary (0 records)

### 📊 Other (5 tables)
- ra_mst_regions (reference data, complete)
- Odds tables (separate worker system)

---

## Immediate Action Checklist

```bash
# 1. Verify enhanced fields are being populated
psql -c "SELECT COUNT(*) FROM ra_runners WHERE starting_price_decimal IS NOT NULL"

# 2. Apply course coordinates
psql -f migrations/021_add_course_coordinates.sql
python3 scripts/update_course_coordinates.py

# 3. Calculate horse ages
psql -c "UPDATE ra_mst_horses SET age = EXTRACT(YEAR FROM AGE(CURRENT_DATE, dob)) WHERE dob IS NOT NULL"

# 4. Migrate breeder
psql -c "UPDATE ra_mst_horses h SET breeder = p.breeder FROM ra_horse_pedigree p WHERE h.id = p.horse_id AND p.breeder IS NOT NULL"

# 5. Check results coverage
psql -c "SELECT COUNT(*), COUNT(position) FROM ra_runners"
```

---

## Files Generated

1. **Complete Audit:** `COMPLETE_DATABASE_AUDIT.json` (209 KB)
   - Every column analyzed with population %
   - Source classification
   - 625 columns across 24 tables

2. **Summary:** `DATABASE_AUDIT_SUMMARY.md`
   - Executive summary
   - Critical gaps analysis
   - Recommendations by priority

3. **Action Plan:** `DATA_GAPS_ACTION_PLAN.md`
   - Immediate actions (P0)
   - Short-term (P1)
   - Medium/long-term (P2/P3)
   - SQL scripts and commands

4. **Quick Ref:** This file
   - At-a-glance metrics
   - Quick decision support

---

## Key Metrics Summary

**Data Completeness:**
- Core master data: 95-100% ✅
- Pre-race runner data: 95-100% ✅
- Post-race result data: 8-9% ⚠️
- Enhanced ML fields: 0% 🚨
- Pedigree statistics: 0% ⚠️
- Course coordinates: 0% 🚨

**Overall Grade: B-**
- Strong foundation with core data
- Critical gaps in results and enhanced fields
- Many placeholder columns for future features

---

## Next Review

**Recommended Frequency:** Monthly
**Next Audit:** 2025-11-20
**Focus Areas:**
1. Enhanced runner fields population
2. Results coverage improvement
3. Pedigree statistics implementation
4. Historical backfill progress

---

**For detailed analysis, see:**
- `COMPLETE_DATABASE_AUDIT.json` - Raw data
- `DATABASE_AUDIT_SUMMARY.md` - Detailed findings
- `DATA_GAPS_ACTION_PLAN.md` - Action items
