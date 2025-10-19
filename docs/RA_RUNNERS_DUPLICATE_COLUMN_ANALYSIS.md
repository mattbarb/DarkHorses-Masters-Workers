# RA_RUNNERS DUPLICATE COLUMN ANALYSIS

**Date:** 2025-10-18
**Status:** Post-Migration 018
**Total Columns:** 76

## Executive Summary

After reviewing the ra_runners table following Migration 018, there are **3 sets of duplicate/related columns** that need decisions:

1. **Weight Columns** - 2 columns storing same data in different formats
2. **Starting Price Columns** - 2 columns storing same data in different formats
3. **Horse Sex Columns** - 2 columns storing related but different data

**Recommendation:** Keep BOTH columns in each set - they serve different query purposes.

---

## Analysis by Column Group

### 1. WEIGHT COLUMNS

```
weight_lbs              numeric              # Pure number: 122
weight_stones_lbs       varchar(10)          # Display format: "8-10"
```

**API Provides:**
```json
{
  "weight": "8-10",        → weight_stones_lbs
  "weight_lbs": "122"      → weight_lbs
}
```

**Usage:**
- `weight_lbs` - For calculations, comparisons, sorting
- `weight_stones_lbs` - For display to users (UK/IRE format)

**Recommendation:** ✅ **KEEP BOTH**
**Reason:** Different purposes - one for computation, one for display

---

### 2. STARTING PRICE COLUMNS

```
starting_price          varchar(20)          # Fractional odds: "9/4", "5/1"
starting_price_decimal  numeric              # Decimal odds: 3.25, 6.00
```

**API Provides:**
```json
{
  "sp": "9/4",           → starting_price
  "sp_dec": "3.25"       → starting_price_decimal
}
```

**Usage:**
- `starting_price` - Display format (traditional UK/IRE odds)
- `starting_price_decimal` - For calculations, probability, EV computations

**Recommendation:** ✅ **KEEP BOTH**
**Reason:** Different use cases - traditional display vs mathematical operations

---

### 3. HORSE SEX COLUMNS

```
horse_sex               text                 # Full description: "M", "F", "G", "C"
horse_sex_code          char(1)              # Same single-letter code: "M", "F", "G", "C"
```

**API Provides:**
```json
{
  "sex": "M"             → horse_sex (currently)
                         → horse_sex_code (from enrichment)
}
```

**Current State:**
- `horse_sex` - Populated from racecards/results (ALL runners)
- `horse_sex_code` - Only populated for enriched horses (NEW horses only)

**Analysis:**
Looking at the API, `sex` and `sex_code` appear to be the SAME VALUE. However:

1. **From /v1/racecards/pro:** Only provides `sex` (e.g., "M", "F", "G", "C")
2. **From /v1/horses/{id}/pro:** Provides `sex_code` (likely same format)

**Issue:** We currently have BOTH columns but they likely contain identical data.

**Options:**

**Option A: Keep Both (Current State)**
- Pro: No code changes needed
- Con: Redundant data, confusion about which to use
- Storage: Minimal cost (1 char vs text)

**Option B: Consolidate to `horse_sex_code`**
- Pro: Single source of truth, more specific name
- Con: Requires updating fetchers to populate this column instead
- Con: Name less intuitive ("sex" vs "sex_code")

**Option C: Consolidate to `horse_sex`**
- Pro: Simpler name, already populated everywhere
- Con: Drop newly added column from Migration 018
- Con: Less specific (could be confused with full names like "gelding")

**Recommendation:** 🔄 **CONSOLIDATE - Keep `horse_sex`, Drop `horse_sex_code`**

**Reason:**
- The API uses `sex` not `sex_code` in racecards
- `horse_sex` is already populated for ALL 118,221 runners
- `horse_sex_code` is only populated for enriched horses
- They store identical single-letter codes ("M", "F", "G", "C")
- No value in maintaining both when they're duplicates

**Migration Required:**
```sql
-- Drop the redundant column
ALTER TABLE ra_runners DROP COLUMN IF EXISTS horse_sex_code;
```

**Code Changes Required:**
```python
# fetchers/races_fetcher.py - NO CHANGE (already using horse_sex)
'horse_sex': runner.get('sex'),  # ✅ Already correct

# utils/entity_extractor.py - Update enrichment logic
# Remove horse_sex_code from enriched horse data
```

---

## "FALSE POSITIVE" DUPLICATE GROUPS

These groups were flagged by pattern matching but are NOT duplicates:

### Entity ID Columns (7 columns)
```
horse_id, jockey_id, trainer_id, owner_id, sire_id, dam_id, damsire_id
```
**Status:** ✅ **KEEP ALL** - Different entities, not duplicates

### Entity Name Columns (7 columns)
```
horse_name, jockey_name, trainer_name, owner_name, sire_name, dam_name, damsire_name
```
**Status:** ✅ **KEEP ALL** - Different entities, not duplicates

### Pedigree Region Columns (4 columns)
```
horse_region, sire_region, dam_region, damsire_region
```
**Status:** ✅ **KEEP ALL** - Different entities, tracks breeding origins

---

## FINAL RECOMMENDATIONS

### Actions Required

**1. Drop Redundant Column:**
```sql
ALTER TABLE ra_runners DROP COLUMN IF EXISTS horse_sex_code;
```

**2. Update Entity Extractor:**
Remove `horse_sex_code` from enrichment mapping in `utils/entity_extractor.py`

**3. Keep All Other "Duplicate" Columns:**
- `weight_lbs` + `weight_stones_lbs` - Serve different purposes
- `starting_price` + `starting_price_decimal` - Serve different purposes

### Summary Table

| Column Set | Columns | Action | Reason |
|------------|---------|--------|---------|
| Weight | `weight_lbs`<br>`weight_stones_lbs` | ✅ KEEP BOTH | Different formats for different uses |
| Starting Price | `starting_price`<br>`starting_price_decimal` | ✅ KEEP BOTH | Traditional vs decimal odds |
| Horse Sex | `horse_sex`<br>`horse_sex_code` | ❌ DROP `horse_sex_code` | Exact duplicates, redundant |
| Entity IDs | 7 columns | ✅ KEEP ALL | Different entities |
| Entity Names | 7 columns | ✅ KEEP ALL | Different entities |
| Regions | 4 columns | ✅ KEEP ALL | Different breeding origins |

---

## Column Count Impact

**Current:** 76 columns
**After dropping `horse_sex_code`:** 75 columns

---

## Data Quality Notes

### Current Population Rates (118,221 runners)

Based on the schema analysis:

**Weight Columns:**
- Both should be ~100% populated (from API racecards/results)

**Starting Price Columns:**
- Both should be ~100% populated for races with results
- Empty for future races (no SP yet)

**Sex Columns:**
- `horse_sex` - ~100% populated (from all racecards)
- `horse_sex_code` - Only for enriched horses (~1-2% of runners)

This confirms `horse_sex_code` is redundant and should be dropped.

---

## API Field Mapping Reference

From `/v1/racecards/pro` and `/v1/results/pro`:

```json
{
  "weight": "8-10",              → weight_stones_lbs
  "weight_lbs": "122",           → weight_lbs
  "sp": "9/4",                   → starting_price
  "sp_dec": "3.25",              → starting_price_decimal
  "sex": "M"                     → horse_sex
}
```

From `/v1/horses/{id}/pro` (enrichment):

```json
{
  "sex": "M",                    → Currently mapped to horse_sex
  "sex_code": "M"                → Currently mapped to horse_sex_code (REDUNDANT)
}
```

**Note:** The enrichment endpoint likely provides the same value in both `sex` and `sex_code`.

---

## Conclusion

**Final Action:** Drop `horse_sex_code` column only. All other "duplicates" are actually serving different purposes and should be retained.

**Impact:** Minimal - reduces column count by 1, removes redundant data, simplifies schema.

**Risk:** None - the column is sparsely populated and contains duplicate data.
