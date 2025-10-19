# RA_RUNNERS SCHEMA CLEANUP - FINAL REPORT

**Date:** 2025-10-18
**Status:** ✅ COMPLETE

---

## Executive Summary

Successfully completed comprehensive schema review and cleanup of the `ra_runners` table following Migration 018.

**Result:**
- Analyzed all 76 columns
- Identified 1 redundant column
- Dropped `horse_sex_code` (exact duplicate)
- **Final schema: 75 columns - optimized and clean**

---

## Actions Taken

### 1. Comprehensive Schema Analysis

**Scripts Created:**
- `scripts/analyze_current_schema.py` - Full column inventory
- `scripts/analyze_duplicate_usage.py` - Data population analysis

**Documentation Created:**
- `docs/RA_RUNNERS_DUPLICATE_COLUMN_ANALYSIS.md` - Duplicate column analysis
- `docs/RA_RUNNERS_COMPLETE_SCHEMA_REVIEW.md` - Complete 76-column inventory
- `docs/SCHEMA_CLEANUP_FINAL_REPORT.md` - This report

### 2. Duplicate Analysis Results

Found **3 sets of potential duplicates:**

#### ✅ KEPT: Weight Columns (Serve Different Purposes)
```sql
weight_lbs              numeric       -- For calculations (131, 122)
weight_stones_lbs       varchar(10)   -- For display ("9-5", "8-10")
```
- **Population:** 99.9% vs 9.0%
- **Reason:** Different formats for different use cases
- **Status:** Both retained

#### ✅ KEPT: Starting Price Columns (Serve Different Purposes)
```sql
starting_price          varchar(20)   -- Fractional odds ("5/2F", "9/4")
starting_price_decimal  numeric       -- Decimal odds (3.25, 6.00)
```
- **Population:** 95.9% vs 9.0%
- **Reason:** Traditional display vs mathematical operations
- **Status:** Both retained

#### ❌ DROPPED: Horse Sex Columns (Exact Duplicates)
```sql
horse_sex               text          -- Populated: 100% (1,326,334 runners)
horse_sex_code          char(1)       -- Populated: 0% (never used)
```
- **Population:** 100% vs 0%
- **Reason:** Exact duplicate, never populated, redundant
- **Status:** `horse_sex_code` DROPPED

### 3. Manual Migration Executed

**Column dropped via Supabase SQL Editor:**
```sql
ALTER TABLE ra_runners DROP COLUMN horse_sex_code;
```

**Verification:**
```
Total Columns: 75 ✅
horse_sex: Present ✅
horse_sex_code: Removed ✅
```

---

## Data Quality Findings

### Database Statistics
- **Total runners:** 1,326,334
- **Recent update:** 118,221 new runners (from results fetch)

### Column Population Rates

**Consistently High (>95%):**
- `horse_sex`: 100%
- `weight_lbs`: 99.9%
- `starting_price`: 95.9%

**Historical/Recent Split (9-10%):**
- `weight_stones_lbs`: 9.0% (only populated post-Migration 018)
- `starting_price_decimal`: 9.0% (only populated post-Migration 018)

**Never Populated (0%):**
- `horse_sex_code`: 0% (added but never used)

### Insights
1. Migration 018 added new fields that are only populated for new data
2. Historical data (1.2M+ runners) doesn't have newer fields
3. `horse_sex_code` was added by mistake - duplicate of existing `horse_sex`

---

## Schema Design Validation

### ✅ Validated Patterns

**1. Dual-Format Columns Are Intentional:**
- Weight in both numeric and display format
- Odds in both fractional and decimal format
- These support different use cases (calculation vs presentation)

**2. Entity Naming Is Consistent:**
- All horse-related fields use `horse_` prefix
- All pedigree fields properly named (`sire_`, `dam_`, `damsire_`)
- All people properly separated (`jockey_`, `trainer_`, `owner_`)

**3. JSONB Used Appropriately:**
- Complex nested data: `trainer_14_days`, `quotes`, `medical`
- Historical arrays: `past_results_flags`, `prev_trainers`, `prev_owners`
- Full API response: `api_data` (for debugging)

**4. Indexes Properly Created:**
- B-tree indexes on frequently queried fields
- GIN indexes on JSONB columns
- All from Migration 018

---

## Remaining Schema Analysis

### No Further Issues Found

**Entity ID Columns (7):** ✅ All different entities, not duplicates
- `horse_id`, `jockey_id`, `trainer_id`, `owner_id`, `sire_id`, `dam_id`, `damsire_id`

**Entity Name Columns (7):** ✅ All different entities, not duplicates
- `horse_name`, `jockey_name`, `trainer_name`, `owner_name`, `sire_name`, `dam_name`, `damsire_name`

**Region Columns (4):** ✅ All different entities, track breeding origins
- `horse_region`, `sire_region`, `dam_region`, `damsire_region`

---

## Final Schema Summary

### Column Breakdown by Category

| Category | Columns | Purpose |
|----------|---------|---------|
| **Primary Keys & IDs** | 3 | runner_id, race_id, horse_id |
| **Horse Details** | 8 | Name, age, sex, DOB, colour, region, breeder |
| **Pedigree** | 9 | Sire, dam, damsire (IDs, names, regions) |
| **People** | 10 | Jockey, trainer, owner (IDs, names, details) |
| **Race Entry** | 4 | Number, draw, weight (2 formats) |
| **Headgear** | 6 | Equipment flags and details |
| **Medical** | 2 | Wind surgery details |
| **Form & Performance** | 9 | Form, career stats, last run |
| **Ratings** | 3 | OR, RPR, TSR |
| **Betting** | 4 | SP (2 formats), odds, betting_enabled |
| **Results** | 5 | Position, distance, time, prize |
| **Analysis** | 5 | Comments, spotlight, quotes, medical, stable tour |
| **Metadata** | 6 | Timestamps, silk URL, API data, flags |
| **TOTAL** | **75** | **Optimized and complete** |

---

## Recommendations for Future

### ✅ Best Practices Established

1. **Maintain dual-format columns** when they serve different purposes
2. **Use consistent naming conventions** (prefixes like `horse_`, `jockey_`)
3. **Leverage JSONB** for complex/nested API data
4. **Always verify column usage** before adding (check if already exists)
5. **Document schema changes** thoroughly

### 🔄 Data Backfill Considerations

**Historical data gaps identified:**
- `weight_stones_lbs`: Only 9% populated (new data only)
- `starting_price_decimal`: Only 9% populated (new data only)

**Options:**
1. **Leave as-is:** Historical data has `weight_lbs` and `starting_price` (sufficient)
2. **Backfill:** Convert historical data to populate new formats
3. **Hybrid:** Compute display formats on-the-fly when needed

**Recommendation:** Leave as-is - historical data is complete in original formats.

---

## Migration History

### Successfully Completed Migrations

**Migration 018 (2025-10-18):**
- Dropped 5 duplicate columns
- Renamed 2 columns (age → horse_age, sex → horse_sex)
- Added 24 new columns for complete API coverage
- Created 14 indexes
- Status: ✅ Complete

**Migration 019 (2025-10-18):**
- Dropped 1 redundant column (`horse_sex_code`)
- Status: ✅ Complete

### Schema State

**Before Migration 018:** ~51 columns (estimated)
**After Migration 018:** 76 columns
**After Migration 019:** 75 columns ✅

---

## Conclusion

The `ra_runners` table is now in **optimal condition**:

✅ **Clean schema** - No redundant columns
✅ **Complete coverage** - All API fields captured
✅ **Well-indexed** - Performance optimized
✅ **Properly documented** - Full inventory and analysis
✅ **Production-ready** - Successfully processing 1.3M+ runners

**No further schema cleanup required.**

---

## Files Generated

### Scripts
- `scripts/analyze_current_schema.py`
- `scripts/analyze_duplicate_usage.py`

### Documentation
- `docs/RA_RUNNERS_DUPLICATE_COLUMN_ANALYSIS.md`
- `docs/RA_RUNNERS_COMPLETE_SCHEMA_REVIEW.md`
- `docs/SCHEMA_CLEANUP_FINAL_REPORT.md` (this file)

### Migrations
- `migrations/018_FINAL_consolidate_and_complete.sql`
- Migration 019: Manual DROP COLUMN via SQL Editor

---

**Status:** ✅ COMPLETE - Schema cleanup finished, no further action required.
