# Database Schema Reference for ML API

**Project:** DarkHorses Racing ML Platform
**Purpose:** Comprehensive schema reference for ML API development
**Status:** Production (Post-Enrichment Implementation)
**Last Updated:** 2025-10-15
**Database:** Supabase PostgreSQL

---

## Table of Contents

1. [Overview](#overview)
2. [Quick Reference Tables](#quick-reference-tables)
3. [Source Tables (ra_* prefix)](#source-tables-ra-prefix)
   - [ra_horses](#ra_horses)
   - [ra_horse_pedigree](#ra_horse_pedigree)
   - [ra_jockeys](#ra_jockeys)
   - [ra_trainers](#ra_trainers)
   - [ra_owners](#ra_owners)
   - [ra_courses](#ra_courses)
   - [ra_mst_races](#ra_mst_races)
   - [ra_mst_runners](#ra_mst_runners)
   - [ra_results](#ra_results)
4. [ML Output Table](#ml-output-table)
5. [API Usage Guide](#api-usage-guide)
6. [Data Quality & Coverage](#data-quality--coverage)
7. [Field Reference Index](#field-reference-index)

---

## Overview

### Database Architecture

The DarkHorses database consists of:

**Source Tables (`ra_*`)** - Raw reference/master data from The Racing API
- Entity tables: horses, jockeys, trainers, owners, courses
- Transaction tables: races, runners, results
- **Total Records:** ~680,000+

**ML API** (External Project) - Data access via API
- ML features calculated on-demand via API
- Historical performance aggregated in real-time
- See separate DarkHorses-AI-Engine project

### Enrichment Status

**Hybrid Enrichment** (Implemented 2025-10-14):
- All NEW horses automatically enriched with complete pedigree data
- Uses `/v1/horses/{id}/pro` endpoint
- Captures 9 additional fields: dob, sex_code, colour, colour_code, region, sire, dam, damsire, breeder (with IDs)
- Historical backfill: Running (111,185 horses)

### Regional Scope

**All data filtered to:** UK (GB) and Ireland (IRE) only

---

## Quick Reference Tables

### Table Summary

| Table | Records | Purpose | ML Relevance | Enriched |
|-------|---------|---------|--------------|----------|
| `ra_horses` | 111,430 | Horse entity data | HIGH | ✅ YES |
| `ra_horse_pedigree` | 111,185+ | Complete pedigree lineage | HIGH | ✅ YES |
| `ra_jockeys` | 3,480 | Jockey entity data | MEDIUM | Partial |
| `ra_trainers` | 2,780 | Trainer entity data | MEDIUM | Partial |
| `ra_owners` | 48,092 | Owner entity data | LOW | No |
| `ra_courses` | 101 | Course reference data | MEDIUM | Complete |
| `ra_mst_races` | 136,648 | Race metadata | HIGH | Complete |
| `ra_mst_runners` | 379,422 | Runner entries & results | **CRITICAL** | Complete |
| `ra_results` | Variable | Historical results | HIGH | Complete |
| `dh_ml_runner_history` | Dynamic | ML-ready runner data | **CRITICAL** | N/A (computed) |

### Data Source Mapping

| API Endpoint | Tables Updated | Frequency |
|--------------|----------------|-----------|
| `/v1/racecards/pro` | ra_mst_races, ra_mst_runners, ra_horses, ra_jockeys, ra_trainers, ra_owners | Daily |
| `/v1/horses/{id}/pro` | ra_horses, ra_horse_pedigree | On discovery (NEW horses only) |
| `/v1/results` | ra_mst_races, ra_mst_runners | Daily |
| `/v1/courses` | ra_courses | Monthly |
| `/v1/bookmakers` | ra_bookmakers | Monthly |

---

## Source Tables (ra_* prefix)

---

### ra_horses

**Purpose:** Horse entity table with complete metadata
**Records:** 111,430 horses
**Primary Key:** `horse_id` (varchar, Racing API ID)
**Enrichment Status:** ✅ Complete (dob, sex_code, colour, region captured via hybrid enrichment)

#### Schema

| Column | Type | Nullable | Populated | API Source | ML Relevance |
|--------|------|----------|-----------|------------|--------------|
| `id` | integer | NO | 100% | Auto-increment | LOW |
| `horse_id` | varchar(100) | NO | 100% | API (racecards/results) | **HIGH** |
| `racing_api_horse_id` | varchar(100) | YES | 100% | API (racecards/results) | LOW (duplicate) |
| `name` | varchar(255) | NO | 100% | API (racecards/results) | MEDIUM |
| `sex` | varchar(20) | YES | ~95% | API (racecards/results) | MEDIUM |
| `dob` | date | YES | **~95%** | `/v1/horses/{id}/pro` | **HIGH** |
| `sex_code` | varchar(10) | YES | **~95%** | `/v1/horses/{id}/pro` | MEDIUM |
| `colour` | varchar(100) | YES | **~95%** | `/v1/horses/{id}/pro` | LOW |
| `colour_code` | varchar(10) | YES | **~95%** | `/v1/horses/{id}/pro` | LOW |
| `region` | varchar(20) | YES | **~95%** | `/v1/horses/{id}/pro` | MEDIUM |
| `created_at` | timestamp | YES | 100% | System | LOW |
| `updated_at` | timestamp | YES | 100% | System | LOW |

#### Enriched Fields (NEW - Hybrid Enrichment)

**Fields added via Pro endpoint:**
- `dob` - Date of birth (used for age calculations, form analysis)
- `sex_code` - Standardized sex code (C/F/G/H/M)
- `colour` - Horse colour (bay, chestnut, etc.)
- `colour_code` - Colour code abbreviation
- `region` - Country/region of origin

**ML Usage:**
- `horse_id` - Primary identifier for joining
- `dob` - Calculate current age, age at race time
- `sex_code` - Sex-based performance analysis
- `region` - Regional performance patterns

#### Example Query

```sql
-- Get horse with enriched data
SELECT
    h.horse_id,
    h.name,
    h.dob,
    h.sex_code,
    h.colour,
    h.region,
    p.sire,
    p.dam,
    p.damsire
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id
WHERE h.horse_id = 'hor_1234567';
```

---

### ra_horse_pedigree

**Purpose:** Complete pedigree lineage for ML genetic analysis
**Records:** 111,185+ (growing)
**Primary Key:** `horse_id` (varchar, Racing API ID)
**Enrichment Status:** ✅ Complete (captured via hybrid enrichment)

#### Schema

| Column | Type | Nullable | Populated | API Source | ML Relevance |
|--------|------|----------|-----------|------------|--------------|
| `id` | integer | NO | 100% | Auto-increment | LOW |
| `horse_id` | varchar(100) | NO | 100% | Foreign key | **HIGH** |
| `sire_id` | varchar(100) | YES | ~100% | `/v1/horses/{id}/pro` | **HIGH** |
| `sire` | varchar(255) | YES | ~100% | `/v1/horses/{id}/pro` | MEDIUM |
| `dam_id` | varchar(100) | YES | ~100% | `/v1/horses/{id}/pro` | **HIGH** |
| `dam` | varchar(255) | YES | ~100% | `/v1/horses/{id}/pro` | MEDIUM |
| `damsire_id` | varchar(100) | YES | ~100% | `/v1/horses/{id}/pro` | **HIGH** |
| `damsire` | varchar(255) | YES | ~100% | `/v1/horses/{id}/pro` | MEDIUM |
| `breeder` | varchar(255) | YES | ~80% | `/v1/horses/{id}/pro` | LOW |
| `created_at` | timestamp | YES | 100% | System | LOW |
| `updated_at` | timestamp | YES | 100% | System | LOW |

#### ML Usage

**Pedigree Analysis:**
- `sire_id`, `dam_id`, `damsire_id` - Lineage-based performance prediction
- Use IDs to build family trees and analyze genetic patterns
- Calculate sire/damsire performance statistics

**Example:** Horses by Dubawi (sire) have 18% win rate vs 12% average

#### Example Query

```sql
-- Get all horses by a specific sire
SELECT
    h.name as horse_name,
    p.sire as sire_name,
    COUNT(r.runner_id) as total_races,
    SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) as wins
FROM ra_horse_pedigree p
JOIN ra_horses h ON p.horse_id = h.horse_id
LEFT JOIN ra_mst_runners r ON h.horse_id = r.horse_id
WHERE p.sire_id = 'sir_1234567'
GROUP BY h.name, p.sire;
```

---

### ra_jockeys

**Purpose:** Jockey entity table
**Records:** 3,480 jockeys
**Primary Key:** `jockey_id` (varchar, Racing API ID)
**Enrichment Status:** Partial (name only, statistics calculated from results)

#### Schema

| Column | Type | Nullable | Populated | API Source | ML Relevance |
|--------|------|----------|-----------|------------|--------------|
| `id` | integer | NO | 100% | Auto-increment | LOW |
| `jockey_id` | varchar(100) | NO | 100% | API (racecards/results) | **HIGH** |
| `name` | varchar(255) | NO | 100% | API (racecards/results) | MEDIUM |
| `created_at` | timestamp | YES | 100% | System | LOW |
| `updated_at` | timestamp | YES | 100% | System | LOW |

#### Calculated Statistics (Computed)

Calculate from `ra_mst_runners` table:
- Total rides
- Total wins
- Win rate
- Place rate
- Course-specific win rates
- Trainer combination statistics

#### ML Usage

**Jockey Performance:**
- `jockey_id` - Join with runners to calculate statistics
- Calculate win rates per course, distance, surface
- Analyze jockey-trainer combinations
- Recent form (last 14 days, last 30 days)

#### Example Query

```sql
-- Calculate jockey statistics
SELECT
    j.jockey_id,
    j.name,
    COUNT(r.runner_id) as total_rides,
    SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) / COUNT(r.runner_id), 2) as win_rate
FROM ra_jockeys j
LEFT JOIN ra_mst_runners r ON j.jockey_id = r.jockey_id
WHERE r.position IS NOT NULL
GROUP BY j.jockey_id, j.name;
```

---

### ra_trainers

**Purpose:** Trainer entity table
**Records:** 2,780 trainers
**Primary Key:** `trainer_id` (varchar, Racing API ID)
**Enrichment Status:** Partial (location captured from runners)

#### Schema

| Column | Type | Nullable | Populated | API Source | ML Relevance |
|--------|------|----------|-----------|------------|--------------|
| `id` | integer | NO | 100% | Auto-increment | LOW |
| `trainer_id` | varchar(100) | NO | 100% | API (racecards/results) | **HIGH** |
| `name` | varchar(255) | NO | 100% | API (racecards/results) | MEDIUM |
| `location` | varchar(255) | YES | ~80% | API (racecards Pro - trainer_location) | MEDIUM |
| `created_at` | timestamp | YES | 100% | System | LOW |
| `updated_at` | timestamp | YES | 100% | System | LOW |

#### Calculated Statistics (Computed)

Calculate from `ra_mst_runners` table:
- Total runners
- Total wins
- Win rate
- Course-specific win rates
- Recent form (14-day stats available in runner data)

#### ML Usage

**Trainer Performance:**
- `trainer_id` - Join with runners to calculate statistics
- `location` - Regional performance analysis
- Trainer-jockey combinations
- Trainer-course combinations
- Recent form trends

#### Example Query

```sql
-- Calculate trainer statistics with location
SELECT
    t.trainer_id,
    t.name,
    t.location,
    COUNT(r.runner_id) as total_runners,
    SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) / COUNT(r.runner_id), 2) as win_rate
FROM ra_trainers t
LEFT JOIN ra_mst_runners r ON t.trainer_id = r.trainer_id
WHERE r.position IS NOT NULL
GROUP BY t.trainer_id, t.name, t.location;
```

---

### ra_owners

**Purpose:** Owner entity table
**Records:** 48,092 owners
**Primary Key:** `owner_id` (varchar, Racing API ID)
**Enrichment Status:** Complete (minimal data available)

#### Schema

| Column | Type | Nullable | Populated | API Source | ML Relevance |
|--------|------|----------|-----------|------------|--------------|
| `id` | integer | NO | 100% | Auto-increment | LOW |
| `owner_id` | varchar(100) | NO | 100% | API (racecards/results) | LOW |
| `name` | varchar(255) | NO | 100% | API (racecards/results) | LOW |
| `created_at` | timestamp | YES | 100% | System | LOW |
| `updated_at` | timestamp | YES | 100% | System | LOW |

#### ML Usage

**Limited ML Value:**
- Mainly used for reference/joining
- Can calculate owner win rates, but low predictive value
- More useful for portfolio analysis than individual race prediction

---

### ra_courses

**Purpose:** Course/track reference data
**Records:** 101 courses
**Primary Key:** `course_id` (varchar, Racing API ID)
**Enrichment Status:** ✅ Complete

#### Schema

| Column | Type | Nullable | Populated | API Source | ML Relevance |
|--------|------|----------|-----------|------------|--------------|
| `id` | integer | NO | 100% | Auto-increment | LOW |
| `course_id` | varchar(100) | NO | 100% | `/v1/courses` | **HIGH** |
| `name` | varchar(255) | NO | 100% | `/v1/courses` | MEDIUM |
| `region` | varchar(50) | YES | 100% | `/v1/courses` | MEDIUM |
| `latitude` | decimal | YES | 100% | `/v1/courses` | LOW |
| `longitude` | decimal | YES | 100% | `/v1/courses` | LOW |
| `created_at` | timestamp | YES | 100% | System | LOW |
| `updated_at` | timestamp | YES | 100% | System | LOW |

#### ML Usage

**Course Characteristics:**
- `course_id` - Join with races for course-specific statistics
- `region` - Regional performance patterns
- Course-specific win rates for horses/jockeys/trainers
- Track biases (draw bias, pace bias)

---

### ra_mst_races

**Purpose:** Race metadata and conditions
**Records:** 136,648 races
**Primary Key:** `race_id` (varchar, Racing API ID)
**Enrichment Status:** ✅ Complete

#### Schema (45 columns)

**Core Fields:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `race_id` | varchar(100) | 100% | API | **CRITICAL** |
| `racing_api_race_id` | varchar(100) | 100% | API | LOW (duplicate) |
| `course_id` | varchar(100) | 100% | API | **HIGH** |
| `course_name` | varchar(255) | 100% | API | MEDIUM |
| `region` | varchar(50) | 100% | API | MEDIUM |
| `race_name` | varchar(255) | 100% | API | LOW |
| `race_date` | date | 100% | API | **HIGH** |
| `off_time` | varchar(50) | 100% | API | MEDIUM |
| `off_datetime` | timestamp | 100% | API | **HIGH** |
| `start_time` | varchar(50) | 100% | API | LOW |
| `race_type` | varchar(50) | 100% | API | **HIGH** |
| `race_class` | varchar(50) | ~95% | API | **HIGH** |
| `pattern` | varchar(50) | ~60% | API (Pro) | MEDIUM |
| `sex_restriction` | varchar(50) | ~30% | API (Pro) | MEDIUM |
| `rating_band` | varchar(100) | ~70% | API (Pro) | MEDIUM |

**Distance Fields:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `distance` | decimal | 100% | API (furlongs) | **HIGH** |
| `distance_f` | varchar(50) | 100% | API (display) | LOW |
| `distance_meters` | integer | ~90% | API (`dist_m`) | **HIGH** |

**Conditions:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `surface` | varchar(50) | 100% | API | **HIGH** |
| `going` | varchar(100) | ~95% | API | **HIGH** |
| `track_condition` | varchar(255) | ~40% | API (`going_detailed`) | MEDIUM |
| `weather_conditions` | varchar(255) | ~30% | API (`weather`) | MEDIUM |
| `rail_movements` | varchar(255) | ~20% | API | LOW |
| `stalls_position` | varchar(50) | ~30% | API (`stalls`) | MEDIUM |

**Race Status:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `is_abandoned` | boolean | 100% | API | HIGH (filter) |
| `big_race` | boolean | 100% | API | MEDIUM |

**Financial:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `currency` | varchar(10) | 100% | Default (GBP) | LOW |
| `prize_money` | decimal | ~90% | API (`prize`) | MEDIUM |
| `total_prize_money` | decimal | ~70% | API | MEDIUM |

**Pro Content:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `tip` | text | ~60% | API (Pro) | LOW |
| `verdict` | text | ~60% | API (Pro) | LOW |
| `betting_forecast` | text | ~60% | API (Pro) | LOW |

**Field Size:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `field_size` | integer | 100% | Calculated | **HIGH** |

#### ML Usage

**Critical Race Context:**
- `race_id` - Primary identifier
- `race_date`, `off_datetime` - Temporal features
- `course_id` - Course-specific performance
- `race_class` - Class-based performance
- `distance_meters` - Distance suitability
- `surface` - Surface-specific performance (flat vs jump)
- `going` - Ground condition performance
- `field_size` - Competition level

---

### ra_mst_runners

**Purpose:** Runner entries and results (MOST CRITICAL TABLE FOR ML)
**Records:** 379,422 runners
**Primary Key:** `runner_id` (varchar, Generated: race_id + horse_id)
**Enrichment Status:** ✅ Complete

#### Schema (69 columns)

**Identification:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `runner_id` | varchar(200) | 100% | Generated | **CRITICAL** |
| `race_id` | varchar(100) | 100% | API | **CRITICAL** |
| `racing_api_race_id` | varchar(100) | 100% | API | LOW |
| `horse_id` | varchar(100) | 100% | API | **CRITICAL** |
| `racing_api_horse_id` | varchar(100) | 100% | API | LOW |
| `horse_name` | varchar(255) | 100% | API | LOW |

**Race Entry Details:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `number` | integer | 100% | API | MEDIUM |
| `draw` | integer | ~95% | API | **HIGH** |
| `stall` | integer | ~30% | API | MEDIUM |
| `age` | integer | 100% | API | **HIGH** |
| `sex` | varchar(20) | 100% | API | MEDIUM |

**Connections:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `jockey_id` | varchar(100) | 100% | API | **HIGH** |
| `racing_api_jockey_id` | varchar(100) | 100% | API | LOW |
| `jockey_name` | varchar(255) | 100% | API | LOW |
| `jockey_claim` | varchar(10) | ~30% | API | MEDIUM |
| `apprentice_allowance` | integer | ~20% | API | MEDIUM |
| `trainer_id` | varchar(100) | 100% | API | **HIGH** |
| `racing_api_trainer_id` | varchar(100) | 100% | API | LOW |
| `trainer_name` | varchar(255) | 100% | API | LOW |
| `owner_id` | varchar(100) | 100% | API | LOW |
| `racing_api_owner_id` | varchar(100) | 100% | API | LOW |
| `owner_name` | varchar(255) | 100% | API | LOW |

**Weight:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `weight` | integer | 100% | API (`lbs`) | **HIGH** |
| `weight_lbs` | integer | 100% | API (`lbs`) | **HIGH** |

**Equipment:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `headgear` | varchar(100) | ~60% | API | MEDIUM |
| `blinkers` | boolean | 100% | Derived from `headgear_run` | **HIGH** |
| `cheekpieces` | boolean | 100% | Derived from `headgear_run` | MEDIUM |
| `visor` | boolean | 100% | Derived from `headgear_run` | MEDIUM |
| `tongue_tie` | boolean | 100% | Derived from `headgear_run` | MEDIUM |

**Pedigree (stored in runners for convenience):**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `sire_id` | varchar(100) | 100% | API | **HIGH** |
| `sire_name` | varchar(255) | 100% | API | LOW |
| `dam_id` | varchar(100) | 100% | API | **HIGH** |
| `dam_name` | varchar(255) | 100% | API | LOW |
| `damsire_id` | varchar(100) | 100% | API | **HIGH** |
| `damsire_name` | varchar(255) | 100% | API | LOW |

**Ratings:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `official_rating` | integer | ~85% | API (`ofr`) | **HIGH** |
| `racing_post_rating` | integer | ~70% | API (`rpr`) | **HIGH** |
| `rpr` | integer | ~70% | API (`rpr`) | **HIGH** |
| `timeform_rating` | integer | ~70% | API (`tfr`) | **HIGH** |
| `tsr` | integer | ~70% | API (`ts`) | **HIGH** |

**Form:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `form` | varchar(50) | ~90% | API | **HIGH** |
| `form_string` | varchar(100) | ~85% | API | **HIGH** |
| `days_since_last_run` | integer | ~80% | API (`last_run`) | **HIGH** |
| `last_run_performance` | varchar(100) | ~80% | API (`last_run`) | MEDIUM |

**Career Stats (from API):**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `career_runs` | integer | ~70% | API (`career_total.runs`) | **HIGH** |
| `career_wins` | integer | ~70% | API (`career_total.wins`) | **HIGH** |
| `career_places` | integer | ~70% | API (`career_total.places`) | **HIGH** |
| `prize_money_won` | decimal | ~60% | API (`prize_money`) | MEDIUM |

**Results (CRITICAL - populated after race):**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| **`position`** | integer | ~90% | Results API (`position`) | **CRITICAL** |
| **`distance_beaten`** | decimal | ~85% | Results API (`btn`) | **HIGH** |
| **`prize_won`** | decimal | ~80% | Results API (`prize`) | MEDIUM |
| **`starting_price`** | varchar(20) | ~85% | Results API (`sp`) | **HIGH** |
| **`sp_decimal`** | decimal | ~85% | Results API (`sp_dec`) | **HIGH** |
| **`finishing_time`** | varchar(50) | ~60% | Results API (`time`) | MEDIUM |
| `result_updated_at` | timestamp | ~90% | System | LOW |

**Other:**

| Column | Type | Populated | API Source | ML Relevance |
|--------|------|-----------|------------|--------------|
| `comment` | text | ~80% | API (`comment`) | LOW |
| `silk_url` | varchar(500) | 100% | API | N/A |
| `api_data` | jsonb | 100% | API (full response) | LOW |
| `is_from_api` | boolean | 100% | System | LOW |
| `fetched_at` | timestamp | 100% | System | LOW |
| `created_at` | timestamp | 100% | System | LOW |
| `updated_at` | timestamp | 100% | System | LOW |

#### ML Usage

**CRITICAL TABLE** - Contains:
1. **Pre-race data** - Entry details, connections, ratings, form
2. **Results data** - Position, distances, prices
3. **Complete historical** - All past races for each horse

**Key ML Features:**
- Historical positions → Career win rate, place rate
- Ratings → Ability assessment
- Form → Recent performance
- Days since last run → Fitness indicator
- Blinkers/equipment → Performance changes
- Draw → Track bias analysis
- Weight → Performance under conditions
- Jockey/trainer IDs → Relationship statistics

#### Example Query

```sql
-- Get complete runner history for a horse
SELECT
    races.race_date,
    races.course_name,
    races.distance_meters,
    races.going,
    runners.position,
    runners.distance_beaten,
    runners.official_rating,
    runners.weight_lbs,
    runners.jockey_name,
    runners.starting_price
FROM ra_mst_runners runners
JOIN ra_mst_races races ON runners.race_id = races.race_id
WHERE runners.horse_id = 'hor_1234567'
  AND runners.position IS NOT NULL
ORDER BY races.race_date DESC;
```

---

### ra_results

**Purpose:** Historical race results (subset of ra_mst_runners)
**Records:** Variable (subset of runners with results)
**Primary Key:** Composite (race_id + horse_id)
**Enrichment Status:** ✅ Complete

**Note:** Results data is merged into `ra_mst_runners` table. The `ra_results` table may be deprecated in favor of using `ra_mst_runners` where `position IS NOT NULL`.

---

## ML API Access

### ML Feature Calculation via API

**Approach:** ML features are calculated on-demand via a separate API project (DarkHorses-AI-Engine)

**Why API Instead of Pre-Calculated Table:**
- More flexible - features can be customized per model
- Real-time calculations ensure fresh data
- Reduces database storage requirements
- Easier to version and update feature definitions
- Better separation of concerns (data storage vs ML logic)

### ML Feature Categories

The ML API calculates these features on-demand from the source tables:

**Career Statistics:**
- Calculated from `ra_mst_runners` WHERE `position IS NOT NULL`
- `total_races`, `total_wins`, `total_places`
- `win_rate`, `place_rate`, `avg_finish_position`

**Context-Specific Performance:**
- Course performance: Filter by `course_id`
- Distance performance: Filter by `distance_meters` (±10%)
- Surface performance: Filter by `surface`
- Going performance: Filter by `going`
- Class performance: Filter by `race_class`

**Recent Form:**
- Last N positions: Order by `race_date DESC LIMIT N`
- Form score: Weighted calculation from recent positions
- Days since last run: `CURRENT_DATE - MAX(race_date)`

**Relationship Statistics:**
- Horse + Jockey: Filter by `horse_id` AND `jockey_id`
- Horse + Trainer: Filter by `horse_id` AND `trainer_id`
- Jockey + Trainer: Filter by `jockey_id` AND `trainer_id`

### Example API Calculation (SQL)

```sql
-- Calculate career statistics for a horse
SELECT
    horse_id,
    COUNT(*) as total_races,
    SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as wins,
    SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) as places,
    ROUND(100.0 * SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate,
    ROUND(AVG(position::numeric), 2) as avg_position
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
WHERE r.horse_id = :horse_id
  AND r.position IS NOT NULL
  AND races.race_date < :current_race_date;

-- Calculate course-specific win rate
SELECT
    horse_id,
    COUNT(*) as course_runs,
    SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) as course_wins,
    ROUND(100.0 * SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as course_win_rate
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
WHERE r.horse_id = :horse_id
  AND races.course_id = :course_id
  AND r.position IS NOT NULL
  AND races.race_date < :current_race_date;

-- Get last 5 positions
SELECT position
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
WHERE r.horse_id = :horse_id
  AND r.position IS NOT NULL
  AND races.race_date < :current_race_date
ORDER BY races.race_date DESC
LIMIT 5;
```

### ML API Project

**Location:** DarkHorses-AI-Engine repository

**Responsibilities:**
- Feature calculation and caching
- Model training and versioning
- Prediction endpoints
- Performance optimization

**This Project (Masters-Workers):**
- Data collection and storage
- Data quality and enrichment
- Raw data API access

---

## API Usage Guide

### Example API Endpoints (Conceptual)

#### 1. Get ML Data for Upcoming Races

**Endpoint:** `GET /api/ml/upcoming-races`

**Query Parameters:**
- `date` - Race date (YYYY-MM-DD, default: tomorrow)
- `region` - Filter by region (gb, ire)
- `course_id` - Filter by specific course

**Response:**
```json
{
  "race_date": "2025-10-16",
  "total_races": 45,
  "total_runners": 389,
  "races": [
    {
      "race_id": "rac_12345",
      "course_name": "Ascot",
      "off_time": "14:30",
      "distance_meters": 1600,
      "going": "Good",
      "field_size": 12,
      "runners": [
        {
          "runner_id": "run_12345_67890",
          "horse_name": "Starlight Express",
          "draw": 5,
          "jockey_name": "R Moore",
          "trainer_name": "A O'Brien",
          "current_weight_lbs": 130,
          "official_rating": 95,
          "win_rate": 18.5,
          "course_win_rate": 25.0,
          "distance_win_rate": 22.3,
          "recent_form_score": 78,
          "last_5_positions": [1, 2, 3, 1, 2],
          "days_since_last_run": 21,
          "has_blinkers": false,
          "historical_races": [...]
        }
      ]
    }
  ]
}
```

**SQL Query:**
```sql
SELECT
    ml.*,
    races.off_time,
    races.race_name
FROM dh_ml_runner_history ml
JOIN ra_mst_races races ON ml.race_id = races.race_id
WHERE ml.race_date = :date
  AND ml.is_scratched = FALSE
ORDER BY races.off_datetime, ml.current_draw;
```

#### 2. Get Horse Complete History

**Endpoint:** `GET /api/horses/{horse_id}/history`

**Response:**
```json
{
  "horse_id": "hor_1234567",
  "name": "Starlight Express",
  "dob": "2019-02-15",
  "sex_code": "G",
  "region": "GB",
  "pedigree": {
    "sire": "Galileo (IRE)",
    "sire_id": "sir_123",
    "dam": "Moonlight Mare (GB)",
    "dam_id": "dam_456",
    "damsire": "Dubawi (IRE)",
    "damsire_id": "dsi_789"
  },
  "career_stats": {
    "total_races": 15,
    "wins": 3,
    "places": 8,
    "win_rate": 20.0,
    "place_rate": 53.3
  },
  "races": [
    {
      "race_date": "2025-10-01",
      "course": "Ascot",
      "distance_meters": 1600,
      "going": "Good",
      "position": 1,
      "distance_beaten": 0.0,
      "weight_lbs": 128,
      "jockey": "R Moore",
      "trainer": "A O'Brien",
      "starting_price": "5/2"
    }
  ]
}
```

**SQL Query:**
```sql
-- Get horse with complete history
SELECT
    h.*,
    p.*,
    json_agg(
        json_build_object(
            'race_date', races.race_date,
            'course_name', races.course_name,
            'distance_meters', races.distance_meters,
            'going', races.going,
            'position', r.position,
            'distance_beaten', r.distance_beaten,
            'weight_lbs', r.weight_lbs,
            'jockey_name', r.jockey_name,
            'trainer_name', r.trainer_name,
            'starting_price', r.starting_price
        ) ORDER BY races.race_date DESC
    ) as races
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id
LEFT JOIN ra_mst_runners r ON h.horse_id = r.horse_id
LEFT JOIN ra_mst_races races ON r.race_id = races.race_id
WHERE h.horse_id = :horse_id
  AND r.position IS NOT NULL
GROUP BY h.horse_id, p.id;
```

#### 3. Get Predictions Features

**Endpoint:** `POST /api/ml/predict`

**Request Body:**
```json
{
  "runner_ids": ["run_12345_67890", "run_12345_67891"],
  "features": ["career", "context", "form", "relationships"]
}
```

**Response:** Returns ML-ready feature vectors for each runner

**SQL Query:**
```sql
-- Get feature vectors for prediction
SELECT
    runner_id,
    horse_id,

    -- Career features
    total_races, win_rate, place_rate, avg_finish_position,
    days_since_last_run,

    -- Context features
    course_win_rate, distance_win_rate, surface_win_rate,
    going_win_rate, class_win_rate,

    -- Form features
    last_5_positions, recent_form_score,

    -- Relationship features
    horse_jockey_win_rate, horse_trainer_win_rate,

    -- Current entry features
    current_weight_lbs, current_draw, current_official_rating,
    current_rpr, current_tsr, has_blinkers,

    -- Race context
    distance_meters, race_class, field_size, going, surface

FROM dh_ml_runner_history
WHERE runner_id = ANY(:runner_ids);
```

### Performance Optimization

**Indexes (already created):**
- `ra_horses` - (horse_id)
- `ra_horse_pedigree` - (horse_id)
- `ra_jockeys` - (jockey_id)
- `ra_trainers` - (trainer_id)
- `ra_mst_races` - (race_id), (race_date), (course_id, race_date)
- `ra_mst_runners` - (runner_id), (race_id), (horse_id), (position)
- `dh_ml_runner_history` - (runner_id, compilation_date), (race_date), (race_id)

**Query Tips:**
1. Always filter by date range first
2. Use indexes on race_id, horse_id, jockey_id, trainer_id
3. For historical queries, use LIMIT to paginate
4. Prefer `dh_ml_runner_history` for ML features (pre-calculated)

---

## Data Quality & Coverage

### Enrichment Coverage

**Current Status (Post-Backfill):**

| Field Category | Coverage | Status |
|----------------|----------|--------|
| Horse metadata (dob, sex_code, colour, region) | ~95% | ✅ Excellent |
| Pedigree data (sire, dam, damsire, breeder) | ~95% | ✅ Excellent |
| Position results | ~90% | ✅ Good |
| Ratings (OR, RPR, TSR) | ~75% | ✅ Good |
| Form data | ~85% | ✅ Good |
| Equipment (blinkers, etc.) | ~95% | ✅ Excellent |
| Trainer location | ~80% | ✅ Good |

### Data Freshness

**Update Schedule:**
- **Daily:** Racecards (upcoming 7 days), results (last 24 hours)
- **Daily:** ML compilation (6:00 AM UTC)
- **Weekly:** Jockeys, trainers, owners (entity refresh)
- **Monthly:** Courses, bookmakers

**Staleness Checks:**
```sql
-- Check data freshness
SELECT
    MAX(race_date) as latest_race,
    MAX(created_at) as latest_fetch,
    NOW() - MAX(created_at) as staleness
FROM ra_mst_races
WHERE race_date >= CURRENT_DATE;
```

### Validation Queries

**Check ML Data Quality:**
```sql
-- ML data completeness
SELECT
    race_date,
    COUNT(*) as total_runners,
    COUNT(total_races) as has_career_stats,
    COUNT(recent_form_score) as has_form_score,
    COUNT(last_5_positions) as has_last_5
FROM dh_ml_runner_history
WHERE race_date >= CURRENT_DATE
GROUP BY race_date
ORDER BY race_date;
```

**Check Enrichment Coverage:**
```sql
-- Horse enrichment coverage
SELECT
    COUNT(*) as total_horses,
    COUNT(dob) as has_dob,
    COUNT(colour) as has_colour,
    COUNT(p.horse_id) as has_pedigree,
    ROUND(100.0 * COUNT(dob) / COUNT(*), 2) as dob_pct,
    ROUND(100.0 * COUNT(p.horse_id) / COUNT(*), 2) as pedigree_pct
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id;
```

---

## Field Reference Index

### By Category

**Identification Fields:**
- `horse_id`, `jockey_id`, `trainer_id`, `owner_id`, `course_id`, `race_id`, `runner_id`

**Temporal Fields:**
- `race_date`, `off_datetime`, `dob`, `days_since_last_run`

**Performance Fields:**
- `position`, `distance_beaten`, `finishing_time`, `starting_price`
- `win_rate`, `place_rate`, `course_win_rate`, `distance_win_rate`

**Rating Fields:**
- `official_rating`, `racing_post_rating`, `rpr`, `timeform_rating`, `tsr`

**Form Fields:**
- `form`, `form_string`, `last_5_positions`, `recent_form_score`

**Equipment Fields:**
- `blinkers`, `cheekpieces`, `visor`, `tongue_tie`, `headgear`

**Pedigree Fields:**
- `sire_id`, `dam_id`, `damsire_id`, `breeder`

**Race Context Fields:**
- `distance_meters`, `race_class`, `surface`, `going`, `field_size`, `race_type`

**Weight Fields:**
- `weight_lbs`, `jockey_claim`, `apprentice_allowance`

### By ML Importance

**CRITICAL (Essential for predictions):**
- `position`, `horse_id`, `race_id`, `runner_id`
- `official_rating`, `rpr`, `tsr`
- `win_rate`, `place_rate`, `course_win_rate`, `distance_win_rate`
- `last_5_positions`, `recent_form_score`
- `distance_meters`, `race_class`, `going`, `draw`
- `days_since_last_run`

**HIGH (Important features):**
- `jockey_id`, `trainer_id`, `sire_id`, `dam_id`, `damsire_id`
- `starting_price`, `distance_beaten`
- `weight_lbs`, `age`, `blinkers`
- `race_date`, `field_size`, `surface`

**MEDIUM (Supporting features):**
- `course_id`, `sex`, `trainer_location`
- `career_runs`, `career_wins`
- `form`, `form_string`

**LOW (Reference/informational):**
- Names (horse_name, jockey_name, trainer_name, course_name)
- `silk_url`, `comment`, `tip`, `verdict`

### Field-to-Table Mapping

Quick lookup for which table contains each field:

| Field | Primary Table | Also Available In |
|-------|---------------|-------------------|
| `horse_id` | ra_horses | ra_mst_runners, dh_ml_runner_history |
| `dob` | ra_horses | dh_ml_runner_history |
| `sire_id` | ra_horse_pedigree | ra_mst_runners (denormalized) |
| `position` | ra_mst_runners | dh_ml_runner_history.historical_races |
| `official_rating` | ra_mst_runners | dh_ml_runner_history |
| `win_rate` | dh_ml_runner_history | (calculated from ra_mst_runners) |
| `race_class` | ra_mst_races | dh_ml_runner_history |

---

## Related Documentation

- **Main README:** `docs/README.md`
- **Enrichment Details:** `docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`
- **ML Pipeline:** `docs/architecture/ML_DATA_PIPELINE.md`
- **Database Audit:** `docs/audit/DATABASE_SCHEMA_AUDIT_DETAILED.md`
- **API Testing:** `docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md`

---

## Change Log

- **2025-10-15**: Created comprehensive ML API reference (post-enrichment)
- **2025-10-14**: Hybrid enrichment implemented
- **2025-10-13**: ML runner history pipeline deployed

---

**Document Version:** 1.0
**Status:** Production Ready
**Maintainer:** DarkHorses Development Team
**For Support:** See main README.md

