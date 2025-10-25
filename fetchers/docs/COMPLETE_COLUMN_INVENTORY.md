# Complete Database Column Inventory & Status

**Generated:** 2025-10-20
**Purpose:** Comprehensive view of all tables and columns with update status
**Database:** Racing API Reference Data (ra_* tables)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Total Tables** | 10 |
| **Total Columns** | 242 |
| **Columns Complete** | 75 (31%) |
| **Columns Calculated** | 54 (22%) |
| **Columns Pending** | 113 (47%) |

**Status Legend:**
- ✅ **COMPLETE** - Data populated and current
- 🟢 **CALCULATED** - Statistics populated from database (99%+ coverage)
- ⚠️ **PENDING** - Column exists but needs calculation
- 🔵 **MASTER** - Reference data (courses, bookmakers, regions)

---

## Table 1: ra_mst_jockeys (3,483 entities)

**Status:** 🟢 **99.08% STATISTICS COMPLETE**
**Update Frequency:** Daily (recent form) + Weekly (lifetime stats)
**Data Source:** Database calculation from ra_runners + ra_races

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | API | Primary key |
| name | text | ✅ COMPLETE | API | Jockey name |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |
| total_rides | integer | 🟢 CALCULATED | DB: COUNT(*) FROM ra_runners | Lifetime rides |
| total_wins | integer | 🟢 CALCULATED | DB: COUNT WHERE position=1 | Lifetime wins |
| total_places | integer | 🟢 CALCULATED | DB: COUNT WHERE position<=3 | Lifetime places |
| total_seconds | integer | 🟢 CALCULATED | DB: COUNT WHERE position=2 | Lifetime seconds |
| total_thirds | integer | 🟢 CALCULATED | DB: COUNT WHERE position=3 | Lifetime thirds |
| win_rate | decimal | 🟢 CALCULATED | DB: (wins/rides)*100 | Lifetime win % |
| place_rate | decimal | 🟢 CALCULATED | DB: (places/rides)*100 | Lifetime place % |
| recent_14d_rides | integer | 🟢 CALCULATED | DB: COUNT last 14 days | Recent form |
| recent_14d_wins | integer | 🟢 CALCULATED | DB: COUNT wins last 14d | Recent wins |
| recent_14d_win_rate | decimal | 🟢 CALCULATED | DB: 14d win % | Recent form % |
| recent_30d_rides | integer | 🟢 CALCULATED | DB: COUNT last 30 days | Recent form |
| recent_30d_wins | integer | 🟢 CALCULATED | DB: COUNT wins last 30d | Recent wins |
| recent_30d_win_rate | decimal | 🟢 CALCULATED | DB: 30d win % | Recent form % |
| last_ride_date | date | 🟢 CALCULATED | DB: MAX(race_date) | Last activity |
| last_win_date | date | 🟢 CALCULATED | DB: MAX WHERE position=1 | Last win |
| days_since_last_ride | integer | 🟢 CALCULATED | DB: CURRENT_DATE - last_ride | Activity metric |
| days_since_last_win | integer | 🟢 CALCULATED | DB: CURRENT_DATE - last_win | Performance metric |
| stats_updated_at | timestamp | 🟢 CALCULATED | System | Last calculation time |

**Total:** 19 columns | ✅ 4 master | 🟢 18 statistics

---

## Table 2: ra_mst_trainers (2,781 entities)

**Status:** 🟢 **99.71% STATISTICS COMPLETE**
**Update Frequency:** Daily (recent form) + Weekly (lifetime stats)
**Data Source:** Database calculation from ra_runners + ra_races

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | API | Primary key |
| name | text | ✅ COMPLETE | API | Trainer name |
| location | text | ✅ COMPLETE | API | Trainer location |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |
| total_runners | integer | 🟢 CALCULATED | DB: COUNT(*) FROM ra_runners | Lifetime runners |
| total_wins | integer | 🟢 CALCULATED | DB: COUNT WHERE position=1 | Lifetime wins |
| total_places | integer | 🟢 CALCULATED | DB: COUNT WHERE position<=3 | Lifetime places |
| total_seconds | integer | 🟢 CALCULATED | DB: COUNT WHERE position=2 | Lifetime seconds |
| total_thirds | integer | 🟢 CALCULATED | DB: COUNT WHERE position=3 | Lifetime thirds |
| win_rate | decimal | 🟢 CALCULATED | DB: (wins/runners)*100 | Lifetime win % |
| place_rate | decimal | 🟢 CALCULATED | DB: (places/runners)*100 | Lifetime place % |
| recent_14d_runs | integer | 🟢 CALCULATED | DB: COUNT last 14 days | Recent form |
| recent_14d_wins | integer | 🟢 CALCULATED | DB: COUNT wins last 14d | Recent wins |
| recent_14d_win_rate | decimal | 🟢 CALCULATED | DB: 14d win % | Recent form % |
| recent_30d_runs | integer | 🟢 CALCULATED | DB: COUNT last 30 days | Recent form |
| recent_30d_wins | integer | 🟢 CALCULATED | DB: COUNT wins last 30d | Recent wins |
| recent_30d_win_rate | decimal | 🟢 CALCULATED | DB: 30d win % | Recent form % |
| last_runner_date | date | 🟢 CALCULATED | DB: MAX(race_date) | Last activity |
| last_win_date | date | 🟢 CALCULATED | DB: MAX WHERE position=1 | Last win |
| days_since_last_runner | integer | 🟢 CALCULATED | DB: CURRENT_DATE - last_runner | Activity metric |
| days_since_last_win | integer | 🟢 CALCULATED | DB: CURRENT_DATE - last_win | Performance metric |
| stats_updated_at | timestamp | 🟢 CALCULATED | System | Last calculation time |

**Total:** 20 columns | ✅ 5 master | 🟢 18 statistics

---

## Table 3: ra_mst_owners (48,165 entities)

**Status:** 🟢 **99.89% STATISTICS COMPLETE**
**Update Frequency:** Daily (recent form) + Weekly (lifetime stats)
**Data Source:** Database calculation from ra_runners + ra_races

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | API | Primary key |
| name | text | ✅ COMPLETE | API | Owner name |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |
| total_horses | integer | 🟢 CALCULATED | DB: COUNT DISTINCT horse_id | Unique horses owned |
| total_runners | integer | 🟢 CALCULATED | DB: COUNT(*) FROM ra_runners | Total race entries |
| total_wins | integer | 🟢 CALCULATED | DB: COUNT WHERE position=1 | Lifetime wins |
| total_places | integer | 🟢 CALCULATED | DB: COUNT WHERE position<=3 | Lifetime places |
| total_seconds | integer | 🟢 CALCULATED | DB: COUNT WHERE position=2 | Lifetime seconds |
| total_thirds | integer | 🟢 CALCULATED | DB: COUNT WHERE position=3 | Lifetime thirds |
| win_rate | decimal | 🟢 CALCULATED | DB: (wins/runners)*100 | Lifetime win % |
| place_rate | decimal | 🟢 CALCULATED | DB: (places/runners)*100 | Lifetime place % |
| recent_14d_runs | integer | 🟢 CALCULATED | DB: COUNT last 14 days | Recent form |
| recent_14d_wins | integer | 🟢 CALCULATED | DB: COUNT wins last 14d | Recent wins |
| recent_14d_win_rate | decimal | 🟢 CALCULATED | DB: 14d win % | Recent form % |
| recent_30d_runs | integer | 🟢 CALCULATED | DB: COUNT last 30 days | Recent form |
| recent_30d_wins | integer | 🟢 CALCULATED | DB: COUNT wins last 30d | Recent wins |
| recent_30d_win_rate | decimal | 🟢 CALCULATED | DB: 30d win % | Recent form % |
| last_runner_date | date | 🟢 CALCULATED | DB: MAX(race_date) | Last activity |
| last_win_date | date | 🟢 CALCULATED | DB: MAX WHERE position=1 | Last win |
| days_since_last_runner | integer | 🟢 CALCULATED | DB: CURRENT_DATE - last_runner | Activity metric |
| days_since_last_win | integer | 🟢 CALCULATED | DB: CURRENT_DATE - last_win | Performance metric |
| active_last_30d | boolean | 🟢 CALCULATED | DB: recent_30d_runs > 0 | Activity flag |
| stats_updated_at | timestamp | 🟢 CALCULATED | System | Last calculation time |

**Total:** 21 columns | ✅ 4 master | 🟢 19 statistics

---

## Table 4: ra_mst_horses (111,669 entities)

**Status:** ✅ **99.93% PEDIGREE COMPLETE**
**Update Frequency:** Real-time (enrichment on discovery)
**Data Source:** API enrichment + pedigree denormalization

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | API | Primary key |
| name | text | ✅ COMPLETE | API | Horse name |
| sex | text | ✅ COMPLETE | API | Basic sex (M/F) |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |
| dob | date | ✅ COMPLETE | API /horses/{id}/pro | Date of birth |
| sex_code | text | ✅ COMPLETE | API /horses/{id}/pro | Full sex code |
| colour | text | ✅ COMPLETE | API /horses/{id}/pro | Coat colour |
| colour_code | text | ✅ COMPLETE | API /horses/{id}/pro | Colour code |
| region | text | ✅ COMPLETE | API /horses/{id}/pro | Breeding region |
| sire_id | text | ✅ COMPLETE | DB: Denormalized from ra_horse_pedigree | Father ID |
| dam_id | text | ✅ COMPLETE | DB: Denormalized from ra_horse_pedigree | Mother ID |
| damsire_id | text | ✅ COMPLETE | DB: Denormalized from ra_horse_pedigree | Maternal grandsire ID |
| sire_name | text | ✅ COMPLETE | API /horses/{id}/pro | Father name |
| dam_name | text | ✅ COMPLETE | API /horses/{id}/pro | Mother name |

**Total:** 15 columns | ✅ 15 complete | 🟢 0 calculated

---

## Table 5: ra_mst_sires (Estimated ~10,000 entities)

**Status:** ⚠️ **PENDING CALCULATION**
**Update Frequency:** Monthly (progeny performance)
**Data Source:** Database calculation from ra_runners + ra_races + ra_mst_horses

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | Derived | Sire ID (same as horse_id) |
| name | text | ✅ COMPLETE | From ra_mst_horses | Sire name |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |
| **career_runs** | integer | ⚠️ PENDING | DB: COUNT own races | Own racing career |
| **career_wins** | integer | ⚠️ PENDING | DB: COUNT own wins | Own wins |
| **career_places** | integer | ⚠️ PENDING | DB: COUNT own places | Own places |
| **career_prize** | decimal | ⚠️ PENDING | DB: SUM own prize_won | Total prize money |
| **best_position** | integer | ⚠️ PENDING | DB: MIN position | Best finish |
| **first_run** | date | ⚠️ PENDING | DB: MIN race_date | Career start |
| **last_run** | date | ⚠️ PENDING | DB: MAX race_date | Career end |
| **last_win** | date | ⚠️ PENDING | DB: MAX win date | Last victory |
| **progeny_count** | integer | ⚠️ PENDING | DB: COUNT DISTINCT offspring | Number of children |
| **progeny_runs** | integer | ⚠️ PENDING | DB: SUM offspring runs | Offspring total runs |
| **progeny_wins** | integer | ⚠️ PENDING | DB: SUM offspring wins | Offspring total wins |
| **progeny_places** | integer | ⚠️ PENDING | DB: SUM offspring places | Offspring total places |
| **progeny_prize** | decimal | ⚠️ PENDING | DB: SUM offspring prize | Offspring total prize |
| **avg_runs_per_horse** | decimal | ⚠️ PENDING | DB: progeny_runs / progeny_count | Progeny durability |
| **avg_wins_per_horse** | decimal | ⚠️ PENDING | DB: progeny_wins / progeny_count | Progeny quality |
| **best_distance_furlong** | integer | ⚠️ PENDING | DB: MODE offspring winning distance | Optimal distance |
| **best_class** | integer | ⚠️ PENDING | DB: MODE offspring winning class | Best class level |
| **class_1_wins** | integer | ⚠️ PENDING | DB: COUNT class 1 wins | Elite progeny |
| **class_2_wins** | integer | ⚠️ PENDING | DB: COUNT class 2 wins | High quality |
| **class_3_wins** | integer | ⚠️ PENDING | DB: COUNT class 3 wins | Good quality |
| **class_4_wins** | integer | ⚠️ PENDING | DB: COUNT class 4 wins | Moderate quality |
| **class_5_wins** | integer | ⚠️ PENDING | DB: COUNT class 5 wins | Lower quality |
| **class_6_wins** | integer | ⚠️ PENDING | DB: COUNT class 6 wins | Claiming level |
| **class_7_wins** | integer | ⚠️ PENDING | DB: COUNT class 7 wins | Selling level |
| **distance_5f_wins** | integer | ⚠️ PENDING | DB: COUNT 5f wins | Sprint prowess |
| **distance_6f_wins** | integer | ⚠️ PENDING | DB: COUNT 6f wins | Sprint |
| **distance_7f_wins** | integer | ⚠️ PENDING | DB: COUNT 7f wins | Sprint/mile |
| **distance_1m_wins** | integer | ⚠️ PENDING | DB: COUNT 1m wins | Miler |
| **distance_10f_wins** | integer | ⚠️ PENDING | DB: COUNT 10f wins | Middle distance |
| **distance_12f_wins** | integer | ⚠️ PENDING | DB: COUNT 12f wins | Middle/staying |
| **distance_14f_wins** | integer | ⚠️ PENDING | DB: COUNT 14f wins | Stayer |
| **distance_16f_wins** | integer | ⚠️ PENDING | DB: COUNT 16f+ wins | Extreme stayer |
| **ae_index** | decimal | ⚠️ PENDING | DB: Complex calculation | Aggregate Earnings Index |
| **ae_index_rank** | integer | ⚠️ PENDING | DB: RANK by AE index | Sire ranking |
| **average_winning_distance** | decimal | ⚠️ PENDING | DB: AVG winning distance | Typical distance |
| **turf_wins** | integer | ⚠️ PENDING | DB: COUNT turf wins | Turf suitability |
| **aw_wins** | integer | ⚠️ PENDING | DB: COUNT AW wins | All-weather suitability |
| **flat_wins** | integer | ⚠️ PENDING | DB: COUNT flat wins | Flat racing |
| **jump_wins** | integer | ⚠️ PENDING | DB: COUNT jump wins | National Hunt |
| **calculated_at** | timestamp | ⚠️ PENDING | System | Last calculation |

**Total:** 47 columns | ✅ 4 master | ⚠️ 38 statistics PENDING

---

## Table 6: ra_mst_dams (Estimated ~20,000 entities)

**Status:** ⚠️ **PENDING CALCULATION**
**Update Frequency:** Monthly (progeny performance)
**Structure:** Same 47 columns as ra_mst_sires (maternal lineage)

**Total:** 47 columns | ✅ 4 master | ⚠️ 38 statistics PENDING

---

## Table 7: ra_mst_damsires (Estimated ~10,000 entities)

**Status:** ⚠️ **PENDING CALCULATION**
**Update Frequency:** Monthly (grandoffspring performance)
**Structure:** Same 47 columns as ra_mst_sires (maternal grandsire lineage)

**Total:** 47 columns | ✅ 4 master | ⚠️ 38 statistics PENDING

---

## Table 8: ra_mst_courses (61 entities)

**Status:** 🔵 **MASTER REFERENCE DATA COMPLETE**
**Update Frequency:** Monthly (static reference data)
**Data Source:** API /v1/courses

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | API | Primary key |
| name | text | ✅ COMPLETE | API | Course name |
| region | text | ✅ COMPLETE | API | GB or IRE |
| latitude | decimal | ✅ COMPLETE | Manual/API | GPS coordinate |
| longitude | decimal | ✅ COMPLETE | Manual/API | GPS coordinate |
| surface_type | text | ✅ COMPLETE | API | Turf/AW |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |

**Total:** 8 columns | ✅ 8 complete

---

## Table 9: ra_mst_bookmakers (26 entities)

**Status:** 🔵 **MASTER REFERENCE DATA COMPLETE**
**Update Frequency:** Monthly (static reference data)
**Data Source:** API /v1/bookmakers

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| id | text | ✅ COMPLETE | API | Primary key |
| name | text | ✅ COMPLETE | API | Bookmaker name |
| display_order | integer | ✅ COMPLETE | API | UI sort order |
| is_premium | boolean | ✅ COMPLETE | API | Premium tier flag |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |
| updated_at | timestamp | ✅ COMPLETE | System | Auto-updated |

**Total:** 6 columns | ✅ 6 complete

---

## Table 10: ra_mst_regions (2 entities: GB, IRE)

**Status:** 🔵 **MASTER REFERENCE DATA COMPLETE**
**Update Frequency:** Static (never changes)
**Data Source:** System-defined

| Column | Type | Status | Source | Notes |
|--------|------|--------|--------|-------|
| code | text | ✅ COMPLETE | System | Primary key (GB/IRE) |
| name | text | ✅ COMPLETE | System | Full name |
| created_at | timestamp | ✅ COMPLETE | System | Auto-generated |

**Total:** 3 columns | ✅ 3 complete

---

## Summary by Status

### ✅ Complete (75 columns)
- All master reference data (horses, courses, bookmakers, regions)
- All system timestamps (created_at, updated_at)
- All primary keys and names

### 🟢 Calculated - COMPLETE (54 columns)
- Jockeys: 18 statistics (99.08% coverage)
- Trainers: 18 statistics (99.71% coverage)
- Owners: 19 statistics (99.89% coverage)

### ⚠️ Pending - NEEDS CALCULATION (113 columns)
- Sires: 38 statistics (100% pending)
- Dams: 38 statistics (100% pending)
- Damsires: 38 statistics (100% pending)

---

## Unified Update Script

**Script:** `scripts/populate_all_statistics_from_database.py`
**Purpose:** Single script to calculate ALL pending statistics from 2015-01-01 to CURRENT_DATE
**Duration:** ~45-60 minutes (all ~70,000 entities)
**Data Source:** 100% from ra_runners + ra_races (NO API calls)

**What It Will Update:**
1. ✅ **People Statistics** - ALREADY COMPLETE (jockeys, trainers, owners)
2. ⚠️ **Pedigree Statistics** - PENDING (sires, dams, damsires - 113 columns)

**Status:** Script ready - see below

---

## Next Steps

1. **Run Unified Script** to populate remaining 113 pedigree statistics columns
2. **Verify Results** with SQL queries showing coverage percentages
3. **Schedule Maintenance:**
   - Daily: Recent form updates (2-3 min)
   - Weekly: Lifetime statistics (15 min)
   - Monthly: Pedigree progeny (30-45 min)

---

**Last Updated:** 2025-10-20
**Maintained By:** Autonomous statistics calculation system
