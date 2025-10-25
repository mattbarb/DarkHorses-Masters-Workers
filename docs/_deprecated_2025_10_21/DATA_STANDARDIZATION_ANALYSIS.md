# Data Standardization Analysis & Recommendations

**Date**: 2025-10-19
**Status**: Analysis Complete - Ready for Migration Planning

## Executive Summary

This document analyzes data inconsistencies across the three entity tables (jockeys, trainers, owners) and provides recommendations for standardization to improve data quality, consistency, and maintainability.

---

## 1. Location Field Inconsistency

### Current State

| Table | Has Location Field | Location Data Available in API | Status |
|-------|-------------------|-------------------------------|--------|
| **ra_jockeys** | ❌ NO | ❌ NO | Missing field, no source |
| **ra_trainers** | ✅ YES | ✅ YES (`trainer_location`) | ✅ Correct |
| **ra_owners** | ❌ NO | ❌ NO | Missing field, no source |

### API Data Available

**Trainers Only:**
- Field: `trainer_location`
- Example: "Upper Lambourn, Berks"
- Format: "{Town}, {County}" or "{Town}"
- Availability: 100% of trainers in racecards
- **Status**: ✅ Available and currently being captured

**Jockeys:**
- ❌ No location field in API
- Only `jockey` (name) and `jockey_id` available

**Owners:**
- ❌ No location field in API
- Only `owner` (name) and `owner_id` available

### Recommendation

**NO ACTION NEEDED** - Current schema is correct:
- ✅ Trainers have location (data available from API)
- ✅ Jockeys don't have location (data not available)
- ✅ Owners don't have location (data not available)

**Database schema matches API data availability perfectly.**

---

## 2. Redundant Field: `active_last_30d` in Owners

### Current State

**Owners table has redundant field:**
```sql
active_last_30d | boolean | NULL
recent_30d_runs | integer | 0
```

### Problem

`active_last_30d` is **redundant** because:
- Can be derived from: `recent_30d_runs > 0`
- Adds maintenance overhead (must keep synchronized)
- Creates potential for data inconsistency
- Not present in jockeys or trainers tables

### Recommendation

**REMOVE `active_last_30d` field from ra_owners table**

**Migration Plan:**

```sql
-- Step 1: Verify redundancy (check if data is consistent)
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN active_last_30d = true AND recent_30d_runs > 0 THEN 1 END) as consistent_true,
  COUNT(CASE WHEN active_last_30d = false AND recent_30d_runs = 0 THEN 1 END) as consistent_false,
  COUNT(CASE WHEN (active_last_30d = true AND recent_30d_runs = 0)
              OR (active_last_30d = false AND recent_30d_runs > 0) THEN 1 END) as inconsistent
FROM ra_owners;

-- Step 2: Drop the redundant column
ALTER TABLE ra_owners DROP COLUMN active_last_30d;

-- Step 3: Update any queries/code that reference this field
-- Replace: WHERE active_last_30d = true
-- With: WHERE recent_30d_runs > 0
```

**Impact:**
- ✅ Simplifies schema
- ✅ Removes maintenance overhead
- ✅ Eliminates risk of data inconsistency
- ✅ Standardizes across all three tables
- ⚠️ Requires updating any queries using `active_last_30d`

**Priority:** HIGH - Should be done before production deployment

---

## 3. Naming Consistency Analysis

### Terminology Differences

#### "Rides" vs "Runs"

| Table | Terminology | Fields |
|-------|------------|--------|
| **Jockeys** | "rides" | `total_rides`, `recent_14d_rides`, `recent_30d_rides` |
| **Trainers** | "runs" | `total_runners`, `recent_14d_runs`, `recent_30d_runs` |
| **Owners** | "runs" | `total_runners`, `recent_14d_runs`, `recent_30d_runs` |

**Analysis:**
- ✅ **This is CORRECT and contextually appropriate**
- Jockeys "ride" horses → "rides"
- Trainers/Owners have horses that "run" → "runs"/"runners"
- Common industry terminology

**Recommendation:** **NO CHANGE** - Keep terminology as-is (industry standard)

#### "Last Ride" vs "Last Runner"

| Table | Field Name | Meaning |
|-------|-----------|---------|
| **Jockeys** | `last_ride_date` | Last time jockey rode |
| **Trainers** | `last_runner_date` | Last time trainer had a runner |
| **Owners** | `last_runner_date` | Last time owner had a runner |

**Analysis:**
- ✅ **This is CORRECT and contextually appropriate**
- Consistent with "rides" vs "runs" terminology

**Recommendation:** **NO CHANGE** - Keep as-is

---

## 4. Field Inventory Comparison

### Complete Schema Comparison

| Field | Jockeys | Trainers | Owners | Notes |
|-------|---------|----------|--------|-------|
| **Core Fields** |
| `id` | ✅ | ✅ | ✅ | Primary key |
| `name` | ✅ | ✅ | ✅ | Entity name |
| `location` | ❌ | ✅ | ❌ | Only trainers (API data available) |
| `created_at` | ✅ | ✅ | ✅ | Timestamp |
| `updated_at` | ✅ | ✅ | ✅ | Timestamp |
| **Total Statistics (Legacy)** |
| `total_rides` / `total_runners` | ✅ | ✅ | ✅ | Lifetime totals |
| `total_wins` | ✅ | ✅ | ✅ | Lifetime wins |
| `total_places` | ✅ | ✅ | ✅ | Lifetime places (1st-3rd) |
| `total_seconds` | ✅ | ✅ | ✅ | Lifetime 2nd place |
| `total_thirds` | ✅ | ✅ | ✅ | Lifetime 3rd place |
| `win_rate` | ✅ | ✅ | ✅ | Lifetime win % |
| `place_rate` | ✅ | ✅ | ✅ | Lifetime place % |
| **Owner-Specific** |
| `total_horses` | ❌ | ❌ | ✅ | Unique horses owned |
| `active_last_30d` | ❌ | ❌ | ⚠️ | **REDUNDANT - REMOVE** |
| **Enhanced Statistics (NEW)** |
| `last_ride_date` / `last_runner_date` | ✅ | ✅ | ✅ | Most recent activity |
| `last_win_date` | ✅ | ✅ | ✅ | Most recent win |
| `days_since_last_ride` / `days_since_last_runner` | ✅ | ✅ | ✅ | Days since activity |
| `days_since_last_win` | ✅ | ✅ | ✅ | Days since win |
| `recent_14d_rides` / `recent_14d_runs` | ✅ | ✅ | ✅ | 14-day activity |
| `recent_14d_wins` | ✅ | ✅ | ✅ | 14-day wins |
| `recent_14d_win_rate` | ✅ | ✅ | ✅ | 14-day win % |
| `recent_30d_rides` / `recent_30d_runs` | ✅ | ✅ | ✅ | 30-day activity |
| `recent_30d_wins` | ✅ | ✅ | ✅ | 30-day wins |
| `recent_30d_win_rate` | ✅ | ✅ | ✅ | 30-day win % |
| `stats_updated_at` | ✅ | ✅ | ✅ | Last stats update |

### Summary

**Jockeys**: 22 fields
**Trainers**: 23 fields (+ location)
**Owners**: 25 fields (+ location missing, + total_horses, + active_last_30d redundant)

---

## 5. Legacy vs Enhanced Statistics

### Overlap Analysis

| Legacy Field | Enhanced Equivalent | Status |
|-------------|-------------------|--------|
| `total_rides` / `total_runners` | - | ✅ Keep (lifetime total) |
| `total_wins` | - | ✅ Keep (lifetime total) |
| `total_places` | - | ✅ Keep (lifetime total) |
| `win_rate` | `recent_14d_win_rate` / `recent_30d_win_rate` | ⚠️ Different time periods |
| `place_rate` | - | ✅ Keep (not in enhanced) |

**Recommendation:** **KEEP BOTH**
- Legacy fields: Lifetime totals (all-time career statistics)
- Enhanced fields: Recent form (14-day and 30-day windows)
- Both serve different analytical purposes
- No redundancy - different time periods

---

## 6. Recommended Migrations

### Priority 1: Remove Redundant Field (Immediate)

**Target:** Remove `active_last_30d` from `ra_owners`

**Migration File:** `migrations/remove_redundant_active_last_30d.sql`

```sql
-- Migration: Remove redundant active_last_30d field from ra_owners
-- Date: 2025-10-19
-- Reason: Redundant with recent_30d_runs (can derive: recent_30d_runs > 0)

-- Step 1: Verify data consistency (optional check)
DO $$
DECLARE
  inconsistent_count INTEGER;
BEGIN
  SELECT COUNT(*) INTO inconsistent_count
  FROM ra_owners
  WHERE (active_last_30d = true AND recent_30d_runs = 0)
     OR (active_last_30d = false AND recent_30d_runs > 0);

  IF inconsistent_count > 0 THEN
    RAISE NOTICE 'Warning: Found % inconsistent records', inconsistent_count;
  ELSE
    RAISE NOTICE 'Data is consistent - safe to drop column';
  END IF;
END $$;

-- Step 2: Drop the redundant column
ALTER TABLE ra_owners DROP COLUMN IF EXISTS active_last_30d;

-- Step 3: Verify column removed
SELECT column_name
FROM information_schema.columns
WHERE table_name = 'ra_owners'
  AND column_name = 'active_last_30d';
-- Should return 0 rows

COMMENT ON TABLE ra_owners IS
  'Horse racing owners reference data.
   Active status can be derived from recent_30d_runs > 0';
```

**Code Updates Needed:**
```python
# Before:
owners = db.query('ra_owners').filter(active_last_30d=True)

# After:
owners = db.query('ra_owners').filter('recent_30d_runs > 0')
```

---

## 7. Data Quality Checks

### Recommended Validation Queries

**Check for NULL statistics after population:**
```sql
-- Jockeys with no statistics populated
SELECT COUNT(*)
FROM ra_jockeys
WHERE last_ride_date IS NULL
  AND id NOT LIKE '**TEST**%';

-- Trainers with no statistics populated
SELECT COUNT(*)
FROM ra_trainers
WHERE last_runner_date IS NULL
  AND id NOT LIKE '**TEST**%';

-- Owners with no statistics populated
SELECT COUNT(*)
FROM ra_owners
WHERE last_runner_date IS NULL
  AND id NOT LIKE '**TEST**%';
```

**Verify location data for trainers:**
```sql
-- Trainers with missing location (should be populated from API)
SELECT id, name, location
FROM ra_trainers
WHERE location IS NULL
  AND id NOT LIKE '**TEST**%'
LIMIT 10;
```

**Check active_last_30d consistency (before removal):**
```sql
-- Find inconsistent active_last_30d values
SELECT
  id,
  name,
  active_last_30d,
  recent_30d_runs,
  CASE
    WHEN active_last_30d = true AND recent_30d_runs = 0 THEN 'Inconsistent: Active but no runs'
    WHEN active_last_30d = false AND recent_30d_runs > 0 THEN 'Inconsistent: Inactive but has runs'
    ELSE 'Consistent'
  END as status
FROM ra_owners
WHERE (active_last_30d = true AND recent_30d_runs = 0)
   OR (active_last_30d = false AND recent_30d_runs > 0);
```

---

## 8. Final Recommendations Summary

### ✅ NO CHANGE NEEDED

1. **Location fields** - Current schema correctly matches API data availability
2. **"Rides" vs "Runs" terminology** - Contextually appropriate, industry standard
3. **Legacy statistics fields** - Serve different purpose than enhanced statistics

### ⚠️ ACTION REQUIRED

1. **Remove `active_last_30d` from ra_owners** (Priority: HIGH)
   - Redundant field causing maintenance overhead
   - Can be derived from `recent_30d_runs > 0`
   - Should be removed before production deployment

### 📋 DOCUMENTATION UPDATES

1. Update entity extractor documentation to clarify:
   - Trainers: location data IS captured from API
   - Jockeys/Owners: location data NOT available in API

2. Update statistics worker documentation to clarify:
   - Legacy fields: Lifetime career totals
   - Enhanced fields: Recent form (14/30 day windows)
   - Different analytical purposes, not redundant

---

## 9. Migration Execution Plan

### Phase 1: Data Validation (Week 1)

1. Run consistency check on `active_last_30d`
2. Document any inconsistencies found
3. Verify all trainers have location populated

### Phase 2: Migration (Week 1)

1. Create backup of ra_owners table
2. Run migration to remove `active_last_30d`
3. Update all code references
4. Deploy updated code

### Phase 3: Verification (Week 1)

1. Confirm column removed from schema
2. Verify all queries still work correctly
3. Validate no performance degradation

---

## 10. Schema Standardization Scorecard

| Category | Status | Notes |
|----------|--------|-------|
| **Field Naming** | ✅ EXCELLENT | Contextually appropriate terminology |
| **Data Availability** | ✅ EXCELLENT | Schema matches API capabilities |
| **Consistency** | ⚠️ GOOD | One redundant field to remove |
| **Documentation** | ✅ GOOD | Clear field purposes |
| **Maintainability** | ⚠️ GOOD | Will be excellent after redundant field removed |

**Overall Grade: A- (Will be A+ after removing redundant field)**

---

**Document Status**: Ready for review and migration planning
**Next Steps**: Execute Phase 1 (Data Validation)
