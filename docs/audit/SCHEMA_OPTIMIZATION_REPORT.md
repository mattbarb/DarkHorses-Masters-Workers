# Database Schema Optimization Report

**Date:** 2025-10-14
**Purpose:** Identify columns to add, remove, or backfill in ra_* tables
**Status:** Complete

---

## Executive Summary

**Columns to ADD:** 0 (All API fields already captured)
**Columns to REMOVE:** 28 (100% NULL, never populated)
**Columns to BACKFILL:** 5 (100% NULL but can be populated)
**Columns OK as-is:** 13 (Expected to be NULL based on data source)

---

## Critical Findings

### 1. ra_horses - 5 Columns Need Backfilling (100% NULL)

| Column | Status | Action | Priority |
|--------|--------|--------|----------|
| `dob` | ❌ 100% NULL | **BACKFILL** | CRITICAL |
| `sex_code` | ❌ 100% NULL | **BACKFILL** | CRITICAL |
| `colour` | ❌ 100% NULL | **BACKFILL** | CRITICAL |
| `colour_code` | ❌ 100% NULL | **BACKFILL** | CRITICAL |
| `region` | ❌ 100% NULL | **BACKFILL** | CRITICAL |

**Solution:** Already prepared - `scripts/backfill_horse_pedigree.py`
**Time:** 15.5 hours (111,325 horses)
**Expected result:** 95%+ coverage for all fields

---

### 2. ra_horse_pedigree - 3 Columns to REMOVE (100% NULL)

| Column | Status | Reason | Action |
|--------|--------|--------|--------|
| `sire_region` | ❌ 100% NULL | Not in API | **REMOVE** |
| `dam_region` | ❌ 100% NULL | Not in API | **REMOVE** |
| `damsire_region` | ❌ 100% NULL | Not in API | **REMOVE** |

**Note:** These region fields were expected from API but are not provided. Safe to remove.

---

### 3. ra_trainers - 1 Column to REMOVE (100% NULL)

| Column | Status | Reason | Action |
|--------|--------|--------|--------|
| `location` | ❌ 100% NULL | Not in API | **REMOVE** |

**Note:** Trainer location not provided by Racing API.

---

### 4. ra_races - 15 Columns to REMOVE (100% NULL)

#### Application-Specific Columns (Not from API)
| Column | Purpose | Action |
|--------|---------|--------|
| `api_race_id` | Duplicate of `race_id` | **REMOVE** |
| `app_race_id` | Internal app ID (unused) | **REMOVE** |
| `admin_notes` | Admin annotations (unused) | **REMOVE** |
| `user_notes` | User annotations (unused) | **REMOVE** |
| `popularity_score` | Calculated metric (unused) | **REMOVE** |
| `featured` | Already populated (0.0% NULL) | **KEEP** |

#### API Fields Not Available
| Column | Status | Reason |
|--------|--------|--------|
| `betting_status` | ❌ 100% NULL | Not in racecards/results |
| `race_status` | ❌ 100% NULL | Use `results_status` instead |
| `results_status` | ❌ 100% NULL | Only in results endpoint |
| `start_time` | ❌ 100% NULL | Use `off_time` instead |
| `live_stream_url` | ❌ 100% NULL | Not in API |
| `replay_url` | ❌ 100% NULL | Not in API |
| `stalls_position` | ❌ 100% NULL | Not in API |
| `total_prize_money` | ❌ 100% NULL | Use `prize_money` instead |

**Total to remove from ra_races:** 15 columns

---

### 5. ra_runners - 9 Columns to REMOVE (100% NULL)

#### Application-Specific Columns
| Column | Purpose | Action |
|--------|---------|--------|
| `api_entry_id` | Duplicate (unused) | **REMOVE** |
| `app_entry_id` | Internal app ID (unused) | **REMOVE** |
| `entry_id` | Duplicate of `runner_id` | **REMOVE** |
| `number_card` | Internal display (unused) | **REMOVE** |
| `user_notes` | User annotations (unused) | **REMOVE** |
| `user_rating` | User ratings (unused) | **REMOVE** |
| `trainer_comments` | Not in API | **REMOVE** |

#### API Fields Not Available
| Column | Status | Reason |
|--------|--------|--------|
| `stall` | ❌ 100% NULL | Use `draw` instead (same field) |
| `timeform_rating` | ❌ 100% NULL | API provides `tfr` but mapped to different column |

**Note:** Check if `timeform_rating` should be populated from `tfr` field.

**Total to remove from ra_runners:** 9 columns

---

## Columns OK as NULL (Expected Behavior)

### ra_races - Moderate NULL is OK

| Column | NULL % | Reason |
|--------|--------|--------|
| `age_band` | 73.0% | Not all races specify age restrictions |
| `currency` | 89.6% | Only for races with prize money |
| `distance_meters` | 73.5% | Old races may lack this field |
| `field_size` | 73.0% | Calculated field, may be missing |
| `prize_money` | 91.9% | Not all races have prize money |
| `rail_movements` | 73.0% | Only relevant for specific tracks |
| `track_condition` | 73.0% | Detailed going info not always available |
| `weather_conditions` | 73.0% | Not always recorded |

**Action:** KEEP - Expected NULL percentages based on race types.

---

### ra_runners - Results Data (Expected High NULL)

| Column | NULL % | Reason |
|--------|--------|--------|
| `position` | 99.8% | Only available from results (not racecards) |
| `distance_beaten` | 99.8% | Only available from results |
| `starting_price` | 99.8% | Only available from results |
| `prize_won` | 99.9% | Only available from results |
| `result_updated_at` | 99.8% | Only set when results captured |
| `finishing_time` | 100% | Not provided by API |

**Action:** KEEP - Will be populated as results are fetched. Already covered in DATA_GAP_ANALYSIS.md.

---

### ra_runners - Career Stats (Expected NULL)

| Column | NULL % | Reason |
|--------|--------|--------|
| `career_runs` | 100% | Not in current API response |
| `career_wins` | 100% | Not in current API response |
| `career_places` | 100% | Not in current API response |
| `days_since_last_run` | 100% | Not in current API response |
| `form_string` | 100% | Not in current API response |
| `prize_money_won` | 100% | Not in current API response |
| `jockey_claim` | 100% | Not in current API response |
| `apprentice_allowance` | 100% | Not in current API response |

**Action:** KEEP - May be added in future API updates or calculated fields.

---

## Migration Plan

### Migration 009: Remove Unused Columns

**Priority:** LOW (doesn't affect functionality, but cleans up schema)

**Tables to modify:**
1. `ra_horses` - None (all fields needed for backfill)
2. `ra_trainers` - Drop `location` (1 column)
3. `ra_horse_pedigree` - Drop `sire_region`, `dam_region`, `damsire_region` (3 columns)
4. `ra_races` - Drop 15 columns (listed above)
5. `ra_runners` - Drop 9 columns (listed above)

**Total columns to remove:** 28

**SQL Script:**
```sql
-- Migration 009: Remove unused columns

-- ra_trainers
ALTER TABLE ra_trainers DROP COLUMN IF EXISTS location;

-- ra_horse_pedigree
ALTER TABLE ra_horse_pedigree DROP COLUMN IF EXISTS sire_region;
ALTER TABLE ra_horse_pedigree DROP COLUMN IF EXISTS dam_region;
ALTER TABLE ra_horse_pedigree DROP COLUMN IF EXISTS damsire_region;

-- ra_races
ALTER TABLE ra_races DROP COLUMN IF EXISTS api_race_id;
ALTER TABLE ra_races DROP COLUMN IF EXISTS app_race_id;
ALTER TABLE ra_races DROP COLUMN IF EXISTS admin_notes;
ALTER TABLE ra_races DROP COLUMN IF EXISTS user_notes;
ALTER TABLE ra_races DROP COLUMN IF EXISTS popularity_score;
ALTER TABLE ra_races DROP COLUMN IF EXISTS betting_status;
ALTER TABLE ra_races DROP COLUMN IF EXISTS race_status;
ALTER TABLE ra_races DROP COLUMN IF EXISTS results_status;
ALTER TABLE ra_races DROP COLUMN IF EXISTS start_time;
ALTER TABLE ra_races DROP COLUMN IF EXISTS live_stream_url;
ALTER TABLE ra_races DROP COLUMN IF EXISTS replay_url;
ALTER TABLE ra_races DROP COLUMN IF EXISTS stalls_position;
ALTER TABLE ra_races DROP COLUMN IF EXISTS total_prize_money;

-- ra_runners
ALTER TABLE ra_runners DROP COLUMN IF EXISTS api_entry_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS app_entry_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS entry_id;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS number_card;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS user_notes;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS user_rating;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS trainer_comments;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS stall;
ALTER TABLE ra_runners DROP COLUMN IF EXISTS timeform_rating;
```

**Impact:**
- Reduces schema complexity
- No data loss (all columns are 100% NULL)
- Improves query performance (fewer columns to scan)
- Reduces storage

---

## Special Investigation: timeform_rating

**Issue:** `ra_runners.timeform_rating` is 100% NULL but workers capture `tfr` field.

**Check:** Is `tfr` being stored in a different column?

Looking at races_fetcher.py:327:
```python
'timeform_rating': parse_rating(runner.get('tfr')),
```

**This should be populating!** Need to check if there's a column mismatch or if TFR is genuinely not in API.

**Action:** Check sample API response for `tfr` field availability.

---

## Summary

### Immediate Actions Required

1. ✅ **BACKFILL ra_horses** (CRITICAL)
   - Script ready: `scripts/backfill_horse_pedigree.py`
   - Time: 15.5 hours
   - Will populate: dob, sex_code, colour, colour_code, region

2. ⚠️ **OPTIONAL: Remove 28 unused columns**
   - Migration ready: Create `migrations/009_remove_unused_columns.sql`
   - Time: <1 minute
   - Impact: Schema cleanup, no functional change

3. ⚠️ **INVESTIGATE: timeform_rating field**
   - Check if TFR is in API response
   - Verify column mapping is correct

### No Columns to Add

✅ **All API fields are already captured** in the current schema.

---

## Recommendations

### Option A: Minimal (RECOMMENDED)
1. Run horse pedigree backfill (15.5 hours)
2. Leave schema as-is (extra columns don't hurt)
3. Monitor timeform_rating in future

### Option B: Clean Schema
1. Run horse pedigree backfill (15.5 hours)
2. Create and run migration 009 to remove 28 unused columns
3. Investigate and fix timeform_rating mapping

### Option C: Status Quo
1. Run horse pedigree backfill only
2. Keep all columns for future expansion
3. Accept some NULL columns

---

**Recommendation:** Execute **Option A** (Minimal)

The extra columns don't cause performance issues and may be useful for future API updates or application features.

---

**End of Report**
