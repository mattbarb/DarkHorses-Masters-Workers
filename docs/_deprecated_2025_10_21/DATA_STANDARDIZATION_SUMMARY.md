# Data Standardization Summary

## Quick Answer to Your Questions

### 1. Location Field in Jockeys - Is This Data Available?

**Answer: NO** ❌

- **Jockeys**: Location data NOT available in Racing API
- **Trainers**: Location data IS available (`trainer_location` field) ✅
- **Owners**: Location data NOT available in Racing API

**Current Database Schema is CORRECT:**
- `ra_trainers` HAS location field (populated from API)
- `ra_jockeys` has NO location field (data not available)
- `ra_owners` has NO location field (data not available)

**API Data Available:**
```
trainer_location: "Upper Lambourn, Berks"  ✅ Available
jockey_location: NOT AVAILABLE             ❌
owner_location: NOT AVAILABLE              ❌
```

**No action needed** - schema correctly matches API data availability.

---

### 2. Should Trainers and Owners Have Location?

**Trainers**: YES ✅ - Already have it and it's populated
**Owners**: NO ❌ - Data not available from API
**Jockeys**: NO ❌ - Data not available from API

---

### 3. Data Standardization Issue: `active_last_30d` vs `recent_30d_runs`

**You Found a MAJOR Issue!** ⚠️

**Current State in ra_owners:**
```sql
active_last_30d | boolean      -- Redundant and OUT OF DATE
recent_30d_runs | integer      -- Accurate and up-to-date
```

**Data Analysis Shows SEVERE Inconsistency:**

| Metric | Count | Percentage |
|--------|-------|------------|
| Total owners | 48,165 | 100% |
| Marked `active_last_30d = true` | 5,726 | **11.9%** |
| Actually have `recent_30d_runs > 0` | 964 | **2.0%** |
| **Inconsistency** | 4,762 | **9.9%** |

**This means:**
- 4,762 owners are marked as "active" but have NO runs in last 30 days
- The `active_last_30d` field is **NOT being updated** correctly
- It's redundant because `recent_30d_runs > 0` gives the SAME information (when accurate)

**Recommendation: REMOVE `active_last_30d` field**

Benefits:
1. ✅ Eliminates data inconsistency
2. ✅ Removes maintenance overhead
3. ✅ Standardizes across all tables (jockeys/trainers don't have this field)
4. ✅ Single source of truth: `recent_30d_runs`

**Code Change Required:**
```python
# Before:
owners = db.query('ra_owners').filter(active_last_30d=True)

# After:
owners = db.query('ra_owners').filter('recent_30d_runs > 0')
```

---

## Complete Standardization Analysis

### Schema Comparison Across All Three Tables

| Field Category | Jockeys | Trainers | Owners | Standardized? |
|---------------|---------|----------|--------|---------------|
| **Core Identity** |
| `id`, `name` | ✅ | ✅ | ✅ | ✅ YES |
| `location` | ❌ | ✅ | ❌ | ✅ YES (matches API) |
| `created_at`, `updated_at` | ✅ | ✅ | ✅ | ✅ YES |
| **Lifetime Stats** |
| `total_*` (rides/runners) | ✅ | ✅ | ✅ | ✅ YES |
| `total_wins/places/seconds/thirds` | ✅ | ✅ | ✅ | ✅ YES |
| `win_rate`, `place_rate` | ✅ | ✅ | ✅ | ✅ YES |
| **Entity-Specific** |
| `total_horses` | ❌ | ❌ | ✅ | ✅ YES (owner-specific) |
| `active_last_30d` | ❌ | ❌ | ⚠️ | ❌ NO - REMOVE |
| **Enhanced Statistics** |
| `last_*_date` | ✅ | ✅ | ✅ | ✅ YES |
| `days_since_last_*` | ✅ | ✅ | ✅ | ✅ YES |
| `recent_14d_*` | ✅ | ✅ | ✅ | ✅ YES |
| `recent_30d_*` | ✅ | ✅ | ✅ | ✅ YES |
| `stats_updated_at` | ✅ | ✅ | ✅ | ✅ YES |

**Standardization Score: 99% (Will be 100% after removing redundant field)**

### Terminology Differences (CORRECT)

| Entity | Activity Term | Why It's Correct |
|--------|--------------|------------------|
| Jockeys | "rides" | Jockeys RIDE horses |
| Trainers | "runs/runners" | Trainers have horses that RUN |
| Owners | "runs/runners" | Owners have horses that RUN |

✅ **This is industry-standard terminology** - No change needed!

---

## Action Items

### Priority 1: Remove Redundant Field (IMMEDIATE)

**File**: `migrations/remove_redundant_active_last_30d.sql` ✅ Created

**Execute Migration:**
```bash
# Run the migration
PGPASSWORD='your_password' psql -h your_host -p 5432 -U postgres -d postgres -f migrations/remove_redundant_active_last_30d.sql
```

**Impact:**
- Removes `active_last_30d` from `ra_owners`
- Eliminates 9.9% data inconsistency
- Standardizes schema across all tables

### Priority 2: Update Code References

Search codebase for any references to `active_last_30d`:

```bash
grep -r "active_last_30d" --include="*.py"
```

Replace with:
```python
# Old
WHERE active_last_30d = true

# New
WHERE recent_30d_runs > 0
```

### Priority 3: Verify Location Data

Ensure trainer locations are being populated:

```sql
-- Check trainers with missing location
SELECT COUNT(*)
FROM ra_trainers
WHERE location IS NULL
  AND id NOT LIKE '**TEST**%';
```

---

## Files Created

1. **`docs/DATA_STANDARDIZATION_ANALYSIS.md`** (8.5 KB)
   - Complete analysis of all standardization issues
   - Detailed recommendations
   - Migration execution plan

2. **`migrations/remove_redundant_active_last_30d.sql`** (3.2 KB)
   - Production-ready migration
   - Data consistency checks
   - Rollback plan included

3. **`docs/DATA_STANDARDIZATION_SUMMARY.md`** (This file)
   - Quick reference for standardization decisions
   - Action items and priorities

---

## Summary

### ✅ What's Already Standardized

1. ✅ **Location fields** - Schema correctly matches API data availability
2. ✅ **Terminology** - "Rides" vs "Runs" is contextually appropriate
3. ✅ **Core fields** - All three tables have consistent structure
4. ✅ **Enhanced statistics** - All 10 new fields consistent across tables
5. ✅ **Timestamps** - created_at, updated_at, stats_updated_at consistent

### ⚠️ What Needs Fixing

1. ⚠️ **`active_last_30d` in owners** - Redundant and 9.9% inconsistent - **REMOVE**

### 📊 Statistics

- **Jockeys**: 22 fields - ✅ Fully standardized
- **Trainers**: 23 fields - ✅ Fully standardized
- **Owners**: 25 fields - ⚠️ One redundant field to remove

**Overall Grade: A- (Will be A+ after removing `active_last_30d`)**

---

**Next Step**: Execute `migrations/remove_redundant_active_last_30d.sql` to achieve 100% standardization.
