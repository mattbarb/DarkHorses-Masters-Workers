# RA_RUNNERS COMPLETE COLUMN INVENTORY

**Current State:** 57 columns in production database

This document provides a complete inventory of all columns currently in the `ra_runners` table, categorized by purpose and source.

---

## 📋 COLUMN CATEGORIES

### 🔑 IDENTIFIERS (7 columns)

| Column | Type | Source | Notes |
|--------|------|--------|-------|
| `runner_id` | VARCHAR(100) | Base | **PRIMARY KEY** - Composite of race_id + horse_id |
| `race_id` | VARCHAR(50) | Base | Foreign key to ra_races |
| `horse_id` | VARCHAR(50) | Base | Foreign key to ra_horses |
| `jockey_id` | VARCHAR(50) | Base | Foreign key to ra_jockeys |
| `trainer_id` | VARCHAR(50) | Base | Foreign key to ra_trainers |
| `owner_id` | VARCHAR(50) | Base | Foreign key to ra_owners |
| `is_from_api` | BOOLEAN | Base | Data source flag |

---

### 🐴 HORSE METADATA (6 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `horse_name` | VARCHAR(255) | Base | Horse name | ✅ Keep |
| `age` | INTEGER | Base | Horse age at race time | ✅ Keep |
| `sex` | VARCHAR(10) | Base | M/F/G/C | ⚠️ Less precise than sex_code |
| `dob` | DATE | Migration 003 | Date of birth | ⚠️ Migration 018 wants to add horse_dob (DUPLICATE!) |
| `colour` | VARCHAR(100) | Migration 003 | Bay, Chestnut, etc. | ⚠️ Migration 018 wants to add horse_colour (DUPLICATE!) |
| `breeder` | VARCHAR(255) | Migration 003 | Breeder name | ⚠️ Migration 018 tries to add again (DUPLICATE!) |

**Issues:**
- `sex` vs `sex_code` - `sex_code` (M/F/G/C) is more precise
- `dob` naming inconsistency - some want `horse_dob`
- `colour` naming inconsistency - some want `horse_colour`

---

### 🧬 PEDIGREE (9 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `sire_id` | VARCHAR(50) | Base | Sire (father) ID | ✅ Keep |
| `sire_name` | VARCHAR(255) | Base | Sire name | ✅ Keep |
| `dam_id` | VARCHAR(50) | Base | Dam (mother) ID | ✅ Keep |
| `dam_name` | VARCHAR(255) | Base | Dam name | ✅ Keep |
| `damsire_id` | VARCHAR(50) | Base | Damsire ID | ✅ Keep |
| `damsire_name` | VARCHAR(255) | Base | Damsire name | ✅ Keep |
| `sire_region` | VARCHAR(20) | Migration 003 | Sire region code | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `dam_region` | VARCHAR(20) | Migration 003 | Dam region code | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `damsire_region` | VARCHAR(20) | Migration 003 | Damsire region code | ⚠️ Migration 018 tries to add again (DUPLICATE!) |

---

### 👤 JOCKEY DATA (4 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `jockey_name` | VARCHAR(255) | Base | Jockey name | ✅ Keep |
| `jockey_claim` | VARCHAR(50) | Base | Claim allowance | ✅ Keep |
| `jockey_claim_lbs` | INTEGER | Migration 011 | Claim in lbs (numeric) | ⚠️ Overlaps with jockey_claim |
| `apprentice_allowance` | VARCHAR(50) | Base | Apprentice allowance | ⚠️ Overlaps with jockey_claim |

**Issue:** Three columns for jockey claims - `jockey_claim`, `jockey_claim_lbs`, `apprentice_allowance`

---

### 🏋️ TRAINER DATA (5 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `trainer_name` | VARCHAR(255) | Base | Trainer name | ✅ Keep |
| `trainer_location` | VARCHAR(255) | Migration 003 | Trainer yard location | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `trainer_rtf` | VARCHAR(50) | Migration 003 | Recent-to-form % | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `trainer_14_days_data` | JSONB | Migration 003 | 14-day stats object | ⚠️ Inconsistent naming (_data suffix) |

**Naming Issue:** `trainer_14_days_data` vs proposed `trainer_14_days` - Remove _data suffix?

---

### 👔 OWNER DATA (2 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `owner_name` | VARCHAR(255) | Base | Owner name | ✅ Keep |

---

### 🏁 RACE ENTRY DATA (5 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `number` | INTEGER | Base | Saddle cloth number | ✅ Keep |
| `draw` | INTEGER | Base | Starting stall | ✅ Keep |
| `weight_lbs` | INTEGER | Base | Weight carried (lbs) | ✅ Keep |
| `weight_stones_lbs` | VARCHAR(10) | Migration 011 | Weight in UK format (e.g., "8-13") | ⚠️ Overlaps with weight_lbs |
| `silk_url` | TEXT | Migration 011 | Jockey silk image URL | ✅ Keep (but races_fetcher uses wrong name!) |

**Issue:** races_fetcher.py still tries to use `jockey_silk_url` which was dropped!

---

### 🛡️ EQUIPMENT (5 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `headgear` | VARCHAR(100) | Base | Headgear type | ✅ Keep |
| `blinkers` | BOOLEAN | Base | Wearing blinkers? | ⚠️ Parsed from headgear_run |
| `cheekpieces` | BOOLEAN | Base | Wearing cheekpieces? | ⚠️ Parsed from headgear_run |
| `visor` | BOOLEAN | Base | Wearing visor? | ⚠️ Parsed from headgear_run |
| `tongue_tie` | BOOLEAN | Base | Wearing tongue tie? | ⚠️ Parsed from headgear_run |

**Issue:** Booleans are derived from `headgear_run` field which doesn't exist yet!

---

### 📊 FORM & CAREER (6 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `form` | VARCHAR(20) | Base | Recent form (e.g., "812") | ✅ Keep |
| `days_since_last_run` | INTEGER | Base | Days since last race | ⚠️ But last_run_date doesn't exist yet! |
| `last_run_performance` | VARCHAR(100) | Base | Last run description | ✅ Keep |
| `career_runs` | INTEGER | Base | Total career runs | ✅ Keep |
| `career_wins` | INTEGER | Base | Total career wins | ✅ Keep |
| `career_places` | INTEGER | Base | Total career places | ✅ Keep |
| `prize_money_won` | VARCHAR(100) | Base | Career prize money | ✅ Keep |

**Issue:** `days_since_last_run` exists but `last_run_date` doesn't!

---

### ⭐ RATINGS (4 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `official_rating` | INTEGER | Base | Official Rating (OR) | ✅ Keep |
| `racing_post_rating` | INTEGER | Base | Racing Post Rating | ✅ Keep |
| `rpr` | INTEGER | Base | RPR (same as racing_post_rating?) | ⚠️ Duplicate? |
| `tsr` | INTEGER | Base | Topspeed Rating | ✅ Keep |

**Issue:** `racing_post_rating` and `rpr` may be duplicates

---

### 🎯 EXPERT ANALYSIS (4 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `spotlight` | TEXT | Migration 003 | Expert spotlight analysis | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `quotes_data` | JSONB | Migration 003 | Press quotes array | ⚠️ Inconsistent naming (_data suffix) |
| `stable_tour_data` | JSONB | Migration 003 | Stable tour comments | ⚠️ Inconsistent naming (_data suffix) |
| `comment` | TEXT | Base | Race commentary | ✅ Keep (but fetcher uses wrong name!) |

**Naming Issues:**
- `quotes_data` should be `quotes`
- `stable_tour_data` should be `stable_tour`
- Fetcher uses `race_comment` which was dropped!

---

### 🏥 MEDICAL (3 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `wind_surgery` | VARCHAR(200) | Migration 003 | Wind surgery info | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `wind_surgery_run` | VARCHAR(50) | Migration 003 | Runs since wind surgery | ⚠️ Migration 018 tries to add again (DUPLICATE!) |
| `medical_data` | JSONB | Migration 003 | Medical history array | ⚠️ Inconsistent naming (_data suffix) |

**Naming Issue:** `medical_data` should be `medical`

---

### 📜 HISTORICAL (1 column)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `past_results_flags` | TEXT[] | Migration 003 | Flags like "C&D winner" | ⚠️ Migration 018 tries to add again (DUPLICATE!) |

---

### 🏆 RESULTS DATA (6 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `position` | VARCHAR(10) | Migration 005 | Finishing position | ✅ Keep |
| `distance_beaten` | DECIMAL(10,2) | Migration 005 | Distance behind winner | ✅ Keep |
| `prize_won` | DECIMAL(12,2) | Base | Prize money won | ✅ Keep |
| `starting_price` | VARCHAR(20) | Base | SP fractional (e.g., "7/2") | ✅ Keep |
| `starting_price_decimal` | DECIMAL(10,2) | Migration 011 | SP decimal (e.g., 4.50) | ⚠️ Overlaps with starting_price |
| `overall_beaten_distance` | DECIMAL(10,2) | Migration 011 | Alternative to distance_beaten | ⚠️ Overlaps with distance_beaten |

**Issues:**
- `starting_price` (fractional) vs `starting_price_decimal` (decimal) - both needed
- `distance_beaten` vs `overall_beaten_distance` - duplicates?

---

### ⏱️ TIMING (2 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `finishing_time` | VARCHAR(20) | Migration 006 | Finishing time (e.g., "1:15.23") | ✅ Keep |
| `result_updated_at` | TIMESTAMP | Base | When result was captured | ✅ Keep |

---

### 🕐 TIMESTAMPS (2 columns)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `created_at` | TIMESTAMP | Base | Record creation timestamp | ✅ Keep |
| `updated_at` | TIMESTAMP | Base | Record update timestamp | ✅ Keep |

---

### 📦 METADATA (1 column)

| Column | Type | Source | Notes | Redundancy? |
|--------|------|--------|-------|-------------|
| `api_data` | JSONB | Base | Full API response | ✅ Keep |

---

## 🔴 COLUMNS MISSING (Should Exist)

These columns are referenced in races_fetcher.py but **don't actually exist in the database**:

| Column Fetcher Uses | Actual Column Name | Fix Needed |
|---------------------|-------------------|-----------|
| `race_comment` | `comment` | ❌ Change fetcher to use `comment` |
| `jockey_silk_url` | `silk_url` | ❌ Change fetcher to use `silk_url` |

---

## ⚠️ COLUMNS THAT NEED RENAMING

To improve consistency:

| Current Name | Proposed Name | Reason |
|--------------|---------------|--------|
| `dob` | `horse_dob` (Option A)<br>OR keep `dob` (Option B) | Consistency with horse_ prefix |
| `colour` | `horse_colour` (Option A)<br>OR keep `colour` (Option B) | Consistency with horse_ prefix |
| `trainer_14_days_data` | `trainer_14_days` | Remove _data suffix |
| `quotes_data` | `quotes` | Remove _data suffix |
| `stable_tour_data` | `stable_tour` | Remove _data suffix |
| `medical_data` | `medical` | Remove _data suffix |

---

## ✅ TRULY MISSING FIELDS (Safe to Add)

These 8 fields from Racecard Pro API are genuinely missing:

| Field | Type | Purpose | API Field |
|-------|------|---------|-----------|
| `horse_sex_code` | CHAR(1) | M/F/G/C (more precise) | `sex_code` |
| `horse_region` | VARCHAR(10) | GB/IRE/FR/USA | `region` |
| `headgear_run` | VARCHAR(50) | "First time", "2nd time" | `headgear_run` |
| `last_run_date` | DATE | Date of last run | `last_run` |
| `days_since_last_run` | INTEGER | Calculated from last_run_date | Calculated |
| `prev_trainers` | JSONB | Previous trainers array | `prev_trainers` |
| `prev_owners` | JSONB | Previous owners array | `prev_owners` |
| `odds` | JSONB | Live bookmaker odds | `odds` |

---

## 📊 SUMMARY STATISTICS

```
Total columns currently in ra_runners:      57

Columns that work correctly:                41
Columns with naming inconsistencies:         6  (trainer_14_days_data, quotes_data, etc.)
Columns that overlap/duplicate:               8  (starting_price vs decimal, etc.)
Columns fetcher references incorrectly:       2  (race_comment, jockey_silk_url)

Migration 018 attempts to add:              24
  - Exact duplicates:                        10
  - Naming variant duplicates:                6
  - Truly new fields:                         8
```

---

## 🎯 CLEANUP RECOMMENDATIONS

### High Priority (Data Loss Risk)

1. **Fix races_fetcher.py immediately:**
   ```python
   # Line 322 - WRONG
   'race_comment': parse_text_field(runner.get('comment')),

   # Line 322 - CORRECT
   'comment': parse_text_field(runner.get('comment')),
   ```

2. **Fix silk_url reference:**
   ```python
   # Line 323 - WRONG
   'jockey_silk_url': runner.get('silk_url'),

   # Line 323 - CORRECT
   'silk_url': runner.get('silk_url'),
   ```

### Medium Priority (Naming Consistency)

3. **Rename JSONB columns to remove _data suffix:**
   - `trainer_14_days_data` → `trainer_14_days`
   - `quotes_data` → `quotes`
   - `stable_tour_data` → `stable_tour`
   - `medical_data` → `medical`

4. **Decide on horse_ prefix convention**
   - Either add to ALL (age → horse_age, sex → horse_sex)
   - OR remove from ALL (horse_id → id, horse_name → name)
   - OR keep current hybrid (document as intentional)

### Low Priority (Potential Duplication)

5. **Review overlapping columns:**
   - `jockey_claim` vs `jockey_claim_lbs` vs `apprentice_allowance`
   - `starting_price` vs `starting_price_decimal` (both likely needed)
   - `distance_beaten` vs `overall_beaten_distance` (check if same)
   - `racing_post_rating` vs `rpr` (likely same value)

---

## 📋 FILES TO UPDATE

After schema changes:

1. ✅ `fetchers/races_fetcher.py` - Fix column names (HIGH PRIORITY)
2. ✅ `fetchers/results_fetcher.py` - Verify column names
3. ✅ `utils/supabase_client.py` - Update DROPPED_RUNNER_COLUMNS list
4. ⚠️ `migrations/018_add_all_missing_runner_fields.sql` - **DO NOT USE**
5. ✅ Create new migration file with only 8 truly missing fields

---

**Last Updated:** 2025-10-18
**Status:** Analysis Complete - Awaiting decision on approach
