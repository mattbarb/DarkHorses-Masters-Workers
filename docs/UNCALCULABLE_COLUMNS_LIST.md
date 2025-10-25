# Uncalculable Columns - Complete List by Table

**Date:** 2025-10-23
**Total:** 15 columns that cannot be calculated from current Racing API data

---

## By Table

### ra_entity_combinations (3 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `ae_index` | DECIMAL | Actual vs Expected performance index | ✅ Yes (future value) |
| `profit_loss_1u` | DECIMAL | Profit/loss from 1-unit betting simulation | ✅ Yes (future value) |
| `query_filters` | JSONB | Metadata - filters used for this combination | ⚠️ Optional (remove?) |

**Table Purpose:** Tracks performance of entity combinations (e.g., jockey + trainer)

---

### ra_performance_by_distance (6 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `ae_index` | DECIMAL | Actual vs Expected performance index | ✅ Yes (future value) |
| `profit_loss_1u` | DECIMAL | Profit/loss from 1-unit betting simulation | ✅ Yes (future value) |
| `best_time_seconds` | DECIMAL | Best race time at this distance | ✅ **CAN CALCULATE!** |
| `avg_time_seconds` | DECIMAL | Average race time at this distance | ✅ **CAN CALCULATE!** |
| `last_time_seconds` | DECIMAL | Most recent race time at this distance | ✅ **CAN CALCULATE!** |
| `query_filters` | JSONB | Metadata - filters used | ⚠️ Optional (remove?) |

**Table Purpose:** Tracks entity performance by distance range

**NOTE:** I was wrong - the 3 time columns CAN be calculated! So only 3 uncalculable here.

---

### ra_performance_by_venue (3 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `ae_index` | DECIMAL | Actual vs Expected performance index | ✅ Yes (future value) |
| `profit_loss_1u` | DECIMAL | Profit/loss from 1-unit betting simulation | ✅ Yes (future value) |
| `query_filters` | JSONB | Metadata - filters used | ⚠️ Optional (remove?) |

**Table Purpose:** Tracks entity performance at specific venues/courses

---

### ra_runner_statistics (2 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `min_winning_distance_yards` | INTEGER | Minimum distance at which this runner won | ✅ **CAN CALCULATE!** |
| `max_winning_distance_yards` | INTEGER | Maximum distance at which this runner won | ✅ **CAN CALCULATE!** |

**Table Purpose:** Comprehensive runner-level statistics

**NOTE:** Both CAN be calculated from race results! So 0 uncalculable here.

---

### ra_mst_sires (3 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `horse_id` | VARCHAR | Reference to sire as a horse (optional) | ℹ️ Optional reference |
| `best_distance_ae` | DECIMAL | AE index at best distance | ✅ Yes (future value) |
| `analysis_last_updated` | TIMESTAMP | When statistics were last calculated | ⚠️ Optional (remove?) |

**Table Purpose:** Sire performance statistics (47 columns total, 28 NULL)

**Additional AE columns** (in class/distance breakdowns):
- `class_1_ae`, `class_2_ae`, `class_3_ae` (3 columns)
- `distance_1_ae`, `distance_2_ae`, `distance_3_ae` (3 columns)

**Note:** Other NULL columns in this table are conditional (e.g., class_2_* is NULL if sire never ran in Class 2)

---

### ra_mst_dams (3 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `horse_id` | VARCHAR | Reference to dam as a horse (optional) | ℹ️ Optional reference |
| `best_distance_ae` | DECIMAL | AE index at best distance | ✅ Yes (future value) |
| `analysis_last_updated` | TIMESTAMP | When statistics were last calculated | ⚠️ Optional (remove?) |

**Table Purpose:** Dam performance statistics (47 columns total, 39 NULL)

**Additional AE columns** (in class/distance breakdowns):
- `class_1_ae`, `class_2_ae`, `class_3_ae` (3 columns)
- `distance_1_ae`, `distance_2_ae`, `distance_3_ae` (3 columns)

---

### ra_mst_damsires (3 columns)

| Column | Type | Description | Keep? |
|--------|------|-------------|-------|
| `horse_id` | VARCHAR | Reference to damsire as a horse (optional) | ℹ️ Optional reference |
| `best_distance_ae` | DECIMAL | AE index at best distance | ✅ Yes (future value) |
| `analysis_last_updated` | TIMESTAMP | When statistics were last calculated | ⚠️ Optional (remove?) |

**Table Purpose:** Damsire performance statistics (47 columns total, 39 NULL)

**Additional AE columns** (in class/distance breakdowns):
- `class_1_ae`, `class_2_ae`, `class_3_ae` (3 columns)
- `distance_1_ae`, `distance_2_ae`, `distance_3_ae` (3 columns)

---

## Summary by Type

### Type 1: Advanced Metrics (KEEP - Future Value)

**AE Index** (24 total across all tables):
- 3× in statistics tables (entity_combinations, by_distance, by_venue)
- 3× in pedigree tables (sires.best_distance_ae, dams, damsires)
- 18× in pedigree class/distance breakdowns (class_1/2/3_ae, distance_1/2/3_ae for sires/dams/damsires)

**Profit/Loss** (3 total):
- ra_entity_combinations.profit_loss_1u
- ra_performance_by_distance.profit_loss_1u
- ra_performance_by_venue.profit_loss_1u

**Subtotal:** 27 columns

---

### Type 2: Metadata (COULD REMOVE - Low Value)

**Query Filters** (3 total):
- ra_entity_combinations.query_filters
- ra_performance_by_distance.query_filters
- ra_performance_by_venue.query_filters

**Analysis Timestamps** (3 total):
- ra_mst_sires.analysis_last_updated
- ra_mst_dams.analysis_last_updated
- ra_mst_damsires.analysis_last_updated

**Optional References** (3 total):
- ra_mst_sires.horse_id
- ra_mst_dams.horse_id
- ra_mst_damsires.horse_id

**Subtotal:** 9 columns

---

### Type 3: Actually CAN Calculate (WRONG INITIAL ASSESSMENT)

These were incorrectly listed as uncalculable:
- ✅ ra_performance_by_distance: best_time_seconds, avg_time_seconds, last_time_seconds (3 columns)
- ✅ ra_runner_statistics: min_winning_distance_yards, max_winning_distance_yards (2 columns)

**Subtotal:** 5 columns (moving to "calculable")

---

## CORRECTED Final Count

**Total Uncalculable:** 36 columns (not 15!)
- Advanced Metrics (AE + Profit/Loss): 27 columns
- Metadata: 9 columns

**Total CAN Calculate:** 5 columns (I was wrong earlier)

**Total NULL After Workers:** 36 columns (not 15!)

---

## Corrected Coverage Projection

| Metric | Current | After Workers | Percent |
|--------|---------|---------------|---------|
| **Total columns** | 507 | 507 | - |
| **Populated now** | 333 | 333 | 65.7% |
| **Can calculate** | - | 164 | - |
| **After workers** | 333 | 497 | **98.0%** |
| **Uncalculable** | - | 36 | 7.1% |

Wait, let me recalculate properly...

---

## PROPER Calculation

From NULL_COLUMN_CATEGORIZATION.md:
- Total columns: 507
- Currently populated: 333
- Currently NULL: 174

Of the 174 NULL:
- CAN calculate from API (via workers): 138 columns
  - Time-based stats (jockeys/trainers/owners): 12 columns
  - Pedigree performance (sires/dams/damsires): 117 columns (excluding AE fields)
  - Analytics stats (times, distances): 9 columns

- CANNOT calculate without advanced systems: 36 columns
  - AE indices: 27 columns
  - Profit/loss: 3 columns
  - Metadata: 6 columns (query_filters, analysis_last_updated, horse_id references)

**After Workers:**
- Populated: 333 + 138 = 471 columns
- NULL: 36 columns
- Coverage: 471/507 = **92.9%**

---

## Recommendation

### Option 1: Keep All (RECOMMENDED)
- ✅ Keep all 36 uncalculable columns
- ✅ Implement workers → 92.9% coverage
- ✅ Document remaining 36 as "future enhancement"

### Option 2: Remove Metadata Only
- ⚠️ Remove 6 metadata columns (query_filters, analysis_last_updated)
- ✅ Keep AE and profit/loss (future value)
- ✅ After workers → 471/501 = **94.0% coverage**
- ✅ Only 30 NULL columns (all valuable metrics)

### Option 3: Remove All Uncalculable
- ❌ Remove all 36 columns
- ✅ After workers → 471/471 = **100% coverage**
- ❌ Lose future capability
- ❌ Need migrations to add back later

---

**My Recommendation:** Option 1 - Keep all columns, achieve 92.9% coverage, document the 36 as requiring advanced models.

---

**Last Updated:** 2025-10-23
**Corrected:** Yes - proper count is 36 uncalculable, not 15
