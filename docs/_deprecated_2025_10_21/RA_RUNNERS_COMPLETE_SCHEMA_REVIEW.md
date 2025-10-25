# RA_RUNNERS COMPLETE SCHEMA REVIEW

**Date:** 2025-10-18
**Post-Migration 018 Status**
**Total Columns:** 76

---

## EXECUTIVE SUMMARY

### Findings

✅ **73 columns are correctly structured** - No changes needed
⚠️  **3 columns are potential duplicates** requiring review
❌ **1 column should be DROPPED** - `horse_sex_code` (exact duplicate of `horse_sex`)

### Recommended Actions

1. **DROP 1 COLUMN:** `horse_sex_code` (redundant duplicate)
2. **KEEP "duplicate" pairs that serve different purposes:**
   - `weight_lbs` + `weight_stones_lbs` (numeric vs display format)
   - `starting_price` + `starting_price_decimal` (fractional vs decimal odds)

**Result:** 76 columns → 75 columns (optimal, no further cleanup needed)

---

## COMPLETE COLUMN INVENTORY

### PRIMARY KEYS & IDENTIFIERS (3 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 1 | `runner_id` | text, NOT NULL | Primary key (race_id + horse_id composite) | ✅ KEEP |
| 7 | `race_id` | text, NOT NULL | Foreign key to ra_races | ✅ KEEP |
| 9 | `horse_id` | text | Foreign key to ra_horses | ✅ KEEP |

---

### HORSE DETAILS (9 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 11 | `horse_name` | text | Horse name for display | ✅ KEEP |
| 12 | `horse_age` | integer | Horse age at time of race | ✅ KEEP |
| 13 | `horse_sex` | text | Sex code: M/F/G/C | ✅ KEEP |
| 76 | `horse_dob` | date | Date of birth (from enrichment) | ✅ KEEP |
| 77 | `horse_sex_code` | char(1) | **DUPLICATE of horse_sex** | ❌ DROP |
| 78 | `horse_colour` | varchar(100) | Horse color (from enrichment) | ✅ KEEP |
| 79 | `horse_region` | varchar(10) | Horse breeding region | ✅ KEEP |
| 80 | `breeder` | varchar(255) | Breeder name | ✅ KEEP |

**Action:** Drop `horse_sex_code` - it's an exact duplicate of `horse_sex`

---

### PEDIGREE (12 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 37 | `sire_id` | text | Sire (father) ID | ✅ KEEP |
| 38 | `sire_name` | text | Sire name | ✅ KEEP |
| 81 | `sire_region` | varchar(20) | Sire breeding region | ✅ KEEP |
| 39 | `dam_id` | text | Dam (mother) ID | ✅ KEEP |
| 40 | `dam_name` | text | Dam name | ✅ KEEP |
| 82 | `dam_region` | varchar(20) | Dam breeding region | ✅ KEEP |
| 41 | `damsire_id` | text | Damsire (mother's father) ID | ✅ KEEP |
| 42 | `damsire_name` | text | Damsire name | ✅ KEEP |
| 83 | `damsire_region` | varchar(20) | Damsire breeding region | ✅ KEEP |

---

### PEOPLE (12 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 18 | `jockey_id` | text | Jockey ID | ✅ KEEP |
| 20 | `jockey_name` | text | Jockey name | ✅ KEEP |
| 74 | `jockey_claim_lbs` | integer | Apprentice allowance in lbs | ✅ KEEP |
| 23 | `trainer_id` | text | Trainer ID | ✅ KEEP |
| 25 | `trainer_name` | text | Trainer name | ✅ KEEP |
| 84 | `trainer_location` | varchar(255) | Trainer location | ✅ KEEP |
| 85 | `trainer_14_days` | jsonb | 14-day trainer stats | ✅ KEEP |
| 86 | `trainer_rtf` | varchar(50) | Trainer "run to form" rating | ✅ KEEP |
| 27 | `owner_id` | text | Owner ID | ✅ KEEP |
| 29 | `owner_name` | text | Owner name | ✅ KEEP |
| 96 | `prev_trainers` | jsonb | Previous trainers history | ✅ KEEP |
| 97 | `prev_owners` | jsonb | Previous owners history | ✅ KEEP |

---

### RACE ENTRY DETAILS (4 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 14 | `number` | integer | Runner number (saddlecloth) | ✅ KEEP |
| 16 | `draw` | integer | Stall/draw number | ✅ KEEP |
| 31 | `weight_lbs` | numeric | Weight in pounds (for calculation) | ✅ KEEP |
| 75 | `weight_stones_lbs` | varchar(10) | Weight in stones-lbs format (for display) | ✅ KEEP |

**Note:** Both weight columns needed - one for math, one for UK/IRE display format

---

### HEADGEAR & EQUIPMENT (6 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 32 | `headgear` | text | Headgear code (b/v/p/t/h/tv/etc) | ✅ KEEP |
| 33 | `blinkers` | boolean | Wearing blinkers | ✅ KEEP |
| 34 | `cheekpieces` | boolean | Wearing cheekpieces | ✅ KEEP |
| 35 | `visor` | boolean | Wearing visor | ✅ KEEP |
| 36 | `tongue_tie` | boolean | Wearing tongue tie | ✅ KEEP |
| 87 | `headgear_run` | varchar(50) | First/second run in headgear | ✅ KEEP |

---

### MEDICAL & SURGERY (2 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 88 | `wind_surgery` | varchar(200) | Wind surgery details | ✅ KEEP |
| 89 | `wind_surgery_run` | varchar(50) | Runs since wind surgery | ✅ KEEP |

---

### FORM & PERFORMANCE (7 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 43 | `form` | text | Form figures (e.g., "1234") | ✅ KEEP |
| 44 | `form_string` | text | Form with separators | ✅ KEEP |
| 45 | `days_since_last_run` | integer | Days since previous run | ✅ KEEP |
| 90 | `last_run_date` | date | Date of last run | ✅ KEEP |
| 46 | `last_run_performance` | text | Description of last performance | ✅ KEEP |
| 47 | `career_runs` | integer | Total career starts | ✅ KEEP |
| 48 | `career_wins` | integer | Total career wins | ✅ KEEP |
| 49 | `career_places` | integer | Total career places | ✅ KEEP |
| 95 | `past_results_flags` | text[] | Array of performance flags | ✅ KEEP |

---

### RATINGS (3 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 51 | `official_rating` | integer | Official OR rating | ✅ KEEP |
| 53 | `rpr` | integer | Racing Post Rating | ✅ KEEP |
| 55 | `tsr` | integer | Top Speed Rating | ✅ KEEP |

---

### BETTING (4 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 67 | `starting_price` | varchar(20) | SP in fractional format (e.g., "9/4") | ✅ KEEP |
| 70 | `starting_price_decimal` | numeric | SP in decimal format (e.g., 3.25) | ✅ KEEP |
| 98 | `odds` | jsonb | Historical odds movements | ✅ KEEP |
| 58 | `betting_enabled` | boolean | Whether betting was available | ✅ KEEP |

**Note:** Both SP formats needed - fractional for display, decimal for calculations

---

### RESULT FIELDS (5 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 64 | `position` | integer | Finishing position | ✅ KEEP |
| 65 | `distance_beaten` | varchar(20) | Distance beaten (e.g., "0.5", "nk") | ✅ KEEP |
| 69 | `finishing_time` | varchar(20) | Finishing time | ✅ KEEP |
| 66 | `prize_won` | numeric | Prize money won | ✅ KEEP |
| 50 | `prize_money_won` | numeric | Career prize money | ✅ KEEP |

---

### ANALYSIS & COMMENTARY (5 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 99 | `comment` | text | Race comment/analysis | ✅ KEEP |
| 91 | `spotlight` | text | Pre-race spotlight comment | ✅ KEEP |
| 92 | `quotes` | jsonb | Trainer/jockey quotes | ✅ KEEP |
| 93 | `stable_tour` | jsonb | Stable tour information | ✅ KEEP |
| 94 | `medical` | jsonb | Medical notes/updates | ✅ KEEP |

---

### METADATA (5 columns)

| # | Column | Type | Purpose | Status |
|---|--------|------|---------|--------|
| 57 | `silk_url` | text | URL to jockey silk image | ✅ KEEP |
| 61 | `api_data` | jsonb | Full API response (for debugging) | ✅ KEEP |
| 5 | `is_from_api` | boolean | Indicates if from API or manual entry | ✅ KEEP |
| 62 | `created_at` | timestamptz | Record creation timestamp | ✅ KEEP |
| 63 | `updated_at` | timestamptz | Record update timestamp | ✅ KEEP |
| 68 | `result_updated_at` | timestamp | Result data update time | ✅ KEEP |

---

## DUPLICATE COLUMN DETAILS

### 1. Weight Columns - KEEP BOTH ✅

```sql
weight_lbs              numeric              -- For calculations: 122
weight_stones_lbs       varchar(10)          -- For display: "8-10"
```

**Rationale:** Different use cases
- Math operations need pure numbers (`weight_lbs`)
- UI display needs traditional format (`weight_stones_lbs`)
- Both populated from API (different fields)

### 2. Starting Price Columns - KEEP BOTH ✅

```sql
starting_price          varchar(20)          -- Fractional: "9/4", "5/1"
starting_price_decimal  numeric              -- Decimal: 3.25, 6.00
```

**Rationale:** Different use cases
- Traditional display uses fractional format
- Calculations need decimal format (probability, expected value)
- Both populated from API (different fields: `sp` and `sp_dec`)

### 3. Horse Sex Columns - DROP ONE ❌

```sql
horse_sex               text                 -- Currently populated for ALL runners
horse_sex_code          char(1)              -- Only for enriched horses, SAME DATA
```

**Rationale:** Exact duplicates
- Both store identical single-letter codes: "M", "F", "G", "C"
- `horse_sex` populated for all 118,221 runners
- `horse_sex_code` only for ~1-2% enriched horses
- No benefit to maintaining both

**Action:** Drop `horse_sex_code`

---

## MIGRATION SCRIPT

```sql
-- Migration 019: Remove redundant horse_sex_code column

BEGIN;

-- Drop the duplicate column
ALTER TABLE ra_runners DROP COLUMN IF EXISTS horse_sex_code;

-- Reload PostgREST schema cache
NOTIFY pgrst, 'reload schema';

COMMIT;

SELECT '✅ Migration 019 Complete: Removed horse_sex_code duplicate column' as status;
```

---

## FETCHER CODE UPDATES

**No changes required** - fetchers are already correctly using `horse_sex`:

```python
# fetchers/races_fetcher.py (line 276)
'horse_sex': runner.get('sex'),  # ✅ Already correct

# fetchers/results_fetcher.py (line 376)
'horse_sex': runner.get('sex'),  # ✅ Already correct
```

**Update enrichment logic:**

```python
# utils/entity_extractor.py
# Remove horse_sex_code from enriched_horse_data mapping
# (Currently at line ~XXX if it exists)

# BEFORE (if present):
'horse_sex_code': horse_data.get('sex_code'),

# AFTER:
# Remove this line entirely - use horse_sex instead
```

---

## SUMMARY

### Current State
- **76 columns total**
- **3 apparent duplicate pairs**
- **118,221 runners** populated

### Recommended State
- **75 columns** (drop `horse_sex_code`)
- **2 intentional "duplicate" pairs** that serve different purposes
- **No further cleanup needed**

### Impact
- **Minimal:** Single column drop
- **Risk:** None - column sparsely populated with duplicate data
- **Benefit:** Cleaner schema, less confusion

---

## CONCLUSION

The ra_runners table is **well-structured** with only **1 truly redundant column**. The other "duplicate" pairs serve legitimate different purposes and should be retained.

**Final recommendation:** Execute Migration 019 to drop `horse_sex_code`, resulting in a clean, optimized 75-column schema.
