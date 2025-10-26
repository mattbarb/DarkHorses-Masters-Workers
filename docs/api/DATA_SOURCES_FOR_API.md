# Data Sources for API Development

**Project:** DarkHorses Racing ML Platform
**Purpose:** Reference guide for API developers - mapping all database fields to their sources
**Date:** 2025-10-14
**Version:** 1.0
**Status:** Production Ready

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Data Flow Overview](#data-flow-overview)
3. [Table-by-Table Field Mapping](#table-by-table-field-mapping)
4. [Calculated Fields & Derivations](#calculated-fields--derivations)
5. [Data Availability & Quality](#data-availability--quality)
6. [API Endpoint Reference](#api-endpoint-reference)
7. [Known Limitations](#known-limitations)
8. [Usage Examples](#usage-examples)

---

## Executive Summary

This document provides a comprehensive mapping of all database fields in the DarkHorses racing platform, detailing:
- **Source**: Where each field comes from (which API endpoint or calculation)
- **JSON Path**: Exact location in the API response
- **Availability**: How often the field is populated
- **Type**: Data type and constraints
- **Purpose**: How the field is used in ML models and APIs

### Key Statistics

| Database Table | Total Fields | API Fields | Calculated Fields | Availability |
|----------------|--------------|------------|-------------------|--------------|
| ra_mst_races | 35+ | 28 | 2 | 95%+ |
| ra_mst_runners | 60+ | 45 | 5 | 90%+ |
| ra_horses | 8 | 6 | 0 | 100% |
| ra_jockeys | 6 | 4 | 0 | 100% |
| ra_trainers | 6 | 4 | 0 | 100% |
| ra_owners | 6 | 4 | 0 | 100% |
| ra_courses | 8 | 6 | 0 | 100% |

---

## Data Flow Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Racing API (The Odds API)                │
│           https://api.theracingapi.com/v1/               │
└──────┬─────────────────────────────────┬──────────────────┘
       │                                 │
       ▼                                 ▼
┌──────────────────┐          ┌──────────────────┐
│  /racecards/pro  │          │    /results      │
│  (Pre-race data) │          │  (Post-race data)│
└────────┬─────────┘          └────────┬─────────┘
         │                              │
         ▼                              ▼
┌─────────────────────────────────────────────────┐
│           Workers (Fetchers)                    │
│  - races_fetcher.py  (racecards)                │
│  - results_fetcher.py (results)                 │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│         Supabase PostgreSQL Database            │
│                                                 │
│  Reference Tables (ra_* prefix):                │
│    - ra_mst_races      (race details)               │
│    - ra_mst_runners    (runner + results)           │
│    - ra_horses     (horse reference)            │
│    - ra_jockeys    (jockey reference)           │
│    - ra_trainers   (trainer reference)          │
│    - ra_owners     (owner reference)            │
│    - ra_courses    (course reference)           │
└────────┬────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────┐
│              DarkHorses API                     │
│       (Your API endpoints expose this data)     │
└─────────────────────────────────────────────────┘
```

---

## Table-by-Table Field Mapping

### 1. ra_mst_races (Race Reference Data)

**Purpose**: Stores comprehensive information about each race
**Source**: Primarily from `/v1/racecards/pro` endpoint, supplemented by `/v1/results`
**Primary Key**: `race_id`
**Update Frequency**: Real-time for upcoming races, updated when results posted

#### Field Mapping

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **race_id** | VARCHAR(100) PK | Racecards & Results | `racecards[].race_id` | 100% | Unique identifier from API |
| **racing_api_race_id** | VARCHAR(100) | Same as race_id | `racecards[].race_id` | 100% | Explicit copy for clarity |
| **is_from_api** | BOOLEAN | Generated | N/A | 100% | Always TRUE |
| **fetched_at** | TIMESTAMP | Generated | N/A | 100% | When data was fetched |
| **course_id** | VARCHAR(100) | Racecards & Results | `racecards[].course_id` | 100% | Links to ra_courses |
| **course_name** | VARCHAR(200) | Racecards & Results | `racecards[].course` | 100% | Display name |
| **region** | VARCHAR(20) | Racecards & Results | `racecards[].region` | 100% | GB, IRE, FR, etc. |
| **race_name** | VARCHAR(500) | Racecards & Results | `racecards[].race_name` | 100% | Full race title |
| **race_date** | DATE | Racecards & Results | `racecards[].date` | 100% | YYYY-MM-DD format |
| **off_datetime** | TIMESTAMPTZ | Racecards & Results | `racecards[].off_dt` | 100% | ISO 8601 with timezone |
| **off_time** | VARCHAR(10) | Racecards & Results | `racecards[].off_time` | 100% | Time only (e.g., "2:15") |
| **start_time** | VARCHAR(10) | Racecards | `racecards[].start_time` | 90% | Sometimes empty |
| **race_type** | VARCHAR(100) | Racecards & Results | `racecards[].type` | 100% | Flat, Hurdle, Chase, NH Flat |
| **race_class** | VARCHAR(50) | Racecards & Results | `racecards[].race_class` | 95% | Class 1-7, Group 1-3, Listed |
| **distance** | DECIMAL(10,2) | Racecards & Results | `racecards[].distance_f` | 100% | Distance in furlongs |
| **distance_f** | VARCHAR(50) | Racecards & Results | `racecards[].distance` | 100% | Text format (e.g., "1m4f") |
| **distance_meters** | INTEGER | Results | `results[].dist_m` | 95% | Distance in meters |
| **age_band** | VARCHAR(50) | Racecards | `racecards[].age_band` | 95% | e.g., "3yo", "4yo+", "2yo" |
| **surface** | VARCHAR(50) | Racecards & Results | `racecards[].surface` | 100% | Turf, AW, Sand |
| **going** | VARCHAR(100) | Racecards & Results | `racecards[].going` | 100% | Good, Soft, Heavy, etc. |
| **track_condition** | VARCHAR(200) | Racecards | `racecards[].going_detailed` | 50% | More detailed going |
| **weather_conditions** | VARCHAR(200) | Racecards | `racecards[].weather` | 40% | Weather description |
| **rail_movements** | VARCHAR(200) | Racecards | `racecards[].rail_movements` | 20% | Rail position changes |
| **stalls_position** | VARCHAR(100) | Racecards | `racecards[].stalls_position` | 30% | Inside, Outside, etc. |
| **race_status** | VARCHAR(50) | Racecards | `racecards[].status` | 100% | Declared, Results, Abandoned |
| **betting_status** | VARCHAR(50) | Racecards | `racecards[].betting_status` | 90% | Open, Closed, etc. |
| **results_status** | VARCHAR(50) | Results | `results[].results_status` | 80% | Final, Provisional |
| **is_abandoned** | BOOLEAN | Racecards & Results | `racecards[].is_abandoned` | 100% | Default FALSE |
| **currency** | VARCHAR(10) | Racecards | Generated | 100% | GBP for GB/IRE races |
| **prize_money** | DECIMAL(12,2) | Racecards | `racecards[].prize` | 90% | Total prize fund |
| **total_prize_money** | DECIMAL(12,2) | Racecards | `racecards[].total_prize_money` | 70% | Alternative field |
| **big_race** | BOOLEAN | Racecards | `racecards[].big_race` | 100% | Featured race flag |
| **field_size** | INTEGER | Calculated | `len(racecards[].runners)` | 100% | Number of declared runners |
| **pattern** | VARCHAR(100) | Racecards | `racecards[].pattern` | 60% | Group 1, Listed, etc. |
| **sex_restriction** | VARCHAR(200) | Racecards | `racecards[].sex_restriction` | 40% | Fillies only, etc. |
| **rating_band** | VARCHAR(100) | Racecards | `racecards[].rating_band` | 50% | 0-70, 71-85, etc. |
| **jumps** | VARCHAR(50) | Racecards | `racecards[].jumps` | 30% | Number of jumps (NH) |
| **tip** | TEXT | Racecards (Pro) | `racecards[].tip` | 80% | Expert tip/selection |
| **verdict** | TEXT | Racecards (Pro) | `racecards[].verdict` | 70% | Race preview/analysis |
| **betting_forecast** | TEXT | Racecards (Pro) | `racecards[].betting_forecast` | 60% | Betting predictions |
| **live_stream_url** | TEXT | Racecards | `racecards[].live_stream_url` | 20% | Live stream link |
| **replay_url** | TEXT | Results | `results[].replay_url` | 50% | Race replay link |
| **api_data** | JSONB | Both | Full API response | 100% | Complete raw data |
| **created_at** | TIMESTAMP | Generated | N/A | 100% | Record creation time |
| **updated_at** | TIMESTAMP | Generated | N/A | 100% | Last update time |

---

### 2. ra_mst_runners (Runner & Results Data)

**Purpose**: Stores both pre-race declarations and post-race results for each runner
**Source**: Combined from `/v1/racecards/pro` (pre-race) and `/v1/results` (post-race)
**Primary Key**: `runner_id` (composite: race_id + horse_id)
**Update Frequency**: Updated when race declared, then again when results posted

#### Core Identification Fields

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **runner_id** | VARCHAR(150) PK | Generated | `{race_id}_{horse_id}` | 100% | Composite key |
| **race_id** | VARCHAR(100) FK | Both | `racecards[].runners[].race_id` | 100% | Foreign key to ra_mst_races |
| **racing_api_race_id** | VARCHAR(100) | Both | Same as above | 100% | Explicit copy |
| **horse_id** | VARCHAR(100) FK | Both | `racecards[].runners[].horse_id` | 100% | Foreign key to ra_horses |
| **racing_api_horse_id** | VARCHAR(100) | Both | Same as above | 100% | Explicit copy |
| **horse_name** | VARCHAR(200) | Both | `racecards[].runners[].horse` | 100% | Display name |
| **is_from_api** | BOOLEAN | Generated | N/A | 100% | Always TRUE |
| **fetched_at** | TIMESTAMP | Generated | N/A | 100% | When racecard fetched |

#### Horse Details

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **age** | INTEGER | Both | `racecards[].runners[].age` | 100% | Horse age at race time |
| **sex** | VARCHAR(10) | Both | `racecards[].runners[].sex` | 100% | G, M, F, C, H, etc. |
| **dob** | DATE | Racecards | `racecards[].runners[].dob` | 40% | Date of birth |
| **colour** | VARCHAR(100) | Racecards | `racecards[].runners[].colour` | 90% | Bay, Chestnut, etc. |
| **breeder** | VARCHAR(255) | Racecards | `racecards[].runners[].breeder` | 80% | Breeder name |

#### Race Positioning

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **number** | INTEGER | Both | `racecards[].runners[].number` | 100% | Cloth/saddle number |
| **draw** | INTEGER | Both | `racecards[].runners[].draw` | 95% | Stall draw (0 if N/A) |
| **stall** | INTEGER | Racecards | `racecards[].runners[].stall` | 40% | Alternative to draw |

#### Connections (Foreign Keys)

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **jockey_id** | VARCHAR(100) FK | Both | `racecards[].runners[].jockey_id` | 100% | FK to ra_jockeys |
| **racing_api_jockey_id** | VARCHAR(100) | Both | Same | 100% | Explicit copy |
| **jockey_name** | VARCHAR(200) | Both | `racecards[].runners[].jockey` | 100% | Display name |
| **jockey_claim** | VARCHAR(50) | Both | `racecards[].runners[].jockey_claim` | 60% | Apprentice claim |
| **apprentice_allowance** | VARCHAR(50) | Racecards | `racecards[].runners[].jockey_allowance` | 40% | Weight allowance |
| **trainer_id** | VARCHAR(100) FK | Both | `racecards[].runners[].trainer_id` | 100% | FK to ra_trainers |
| **racing_api_trainer_id** | VARCHAR(100) | Both | Same | 100% | Explicit copy |
| **trainer_name** | VARCHAR(200) | Both | `racecards[].runners[].trainer` | 100% | Display name |
| **trainer_location** | VARCHAR(255) | Racecards | `racecards[].runners[].trainer_location` | 80% | Trainer yard location |
| **owner_id** | VARCHAR(100) FK | Both | `racecards[].runners[].owner_id` | 100% | FK to ra_owners |
| **racing_api_owner_id** | VARCHAR(100) | Both | Same | 100% | Explicit copy |
| **owner_name** | VARCHAR(200) | Both | `racecards[].runners[].owner` | 100% | Display name |

#### Weight & Equipment

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **weight** | VARCHAR(20) | Racecards | `racecards[].runners[].lbs` | 100% | Weight carried |
| **weight_lbs** | INTEGER | Both | `racecards[].runners[].lbs` | 100% | Integer pounds |
| **headgear** | VARCHAR(100) | Both | `racecards[].runners[].headgear` | 70% | Text description |
| **blinkers** | BOOLEAN | Racecards | Parse `headgear_run` for 'b' | 70% | Wearing blinkers |
| **cheekpieces** | BOOLEAN | Racecards | Parse `headgear_run` for 'c' | 70% | Wearing cheekpieces |
| **visor** | BOOLEAN | Racecards | Parse `headgear_run` for 'v' | 70% | Wearing visor |
| **tongue_tie** | BOOLEAN | Racecards | Parse `headgear_run` for 't' | 70% | Wearing tongue tie |
| **wind_surgery** | VARCHAR(200) | Racecards | `racecards[].runners[].wind_surgery` | 20% | Wind surgery history |
| **wind_surgery_run** | VARCHAR(50) | Racecards | `racecards[].runners[].wind_surgery_run` | 20% | Surgery timing |

#### Pedigree

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **sire_id** | VARCHAR(100) | Both | `racecards[].runners[].sire_id` | 95% | Sire identifier |
| **sire_name** | VARCHAR(200) | Both | `racecards[].runners[].sire` | 100% | Sire name |
| **dam_id** | VARCHAR(100) | Both | `racecards[].runners[].dam_id` | 95% | Dam identifier |
| **dam_name** | VARCHAR(200) | Both | `racecards[].runners[].dam` | 100% | Dam name |
| **damsire_id** | VARCHAR(100) | Both | `racecards[].runners[].damsire_id` | 95% | Damsire identifier |
| **damsire_name** | VARCHAR(200) | Both | `racecards[].runners[].damsire` | 95% | Damsire name |
| **sire_region** | VARCHAR(20) | Racecards | `racecards[].runners[].sire_region` | 60% | Sire's region |
| **dam_region** | VARCHAR(20) | Racecards | `racecards[].runners[].dam_region` | 60% | Dam's region |
| **damsire_region** | VARCHAR(20) | Racecards | `racecards[].runners[].damsire_region` | 60% | Damsire's region |

#### Ratings (Critical for ML)

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **official_rating** | INTEGER | Both | `racecards[].runners[].ofr` OR `results[].runners[].or` | 80% | Official handicap rating |
| **racing_post_rating** | INTEGER | Both (Pro) | `racecards[].runners[].rpr` OR `results[].runners[].rpr` | 75% | Racing Post Rating |
| **rpr** | INTEGER | Both (Pro) | Same as above | 75% | Alias for racing_post_rating |
| **timeform_rating** | INTEGER | Racecards (Pro) | `racecards[].runners[].tfr` | 60% | Timeform Rating |
| **tsr** | INTEGER | Both (Pro) | `racecards[].runners[].ts` OR `results[].runners[].tsr` | 70% | Top Speed Rating |

**Important Notes on Ratings:**
- API returns `"-"` (en-dash) for missing ratings
- Must use `parse_rating()` function to handle safely
- Ratings are stronger predictors when available
- Availability higher for handicap races

#### Form & History

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **form** | VARCHAR(50) | Racecards | `racecards[].runners[].form` | 90% | Form figures (e.g., "142-") |
| **form_string** | VARCHAR(100) | Racecards | `racecards[].runners[].form_string` | 85% | Extended form |
| **days_since_last_run** | INTEGER | Racecards | `racecards[].runners[].days_since_last_run` | 85% | Days since last race |
| **last_run_performance** | VARCHAR(200) | Racecards | `racecards[].runners[].last_run` | 80% | Last race summary |
| **career_runs** | INTEGER | Racecards | `racecards[].runners[].career_total.runs` | 70% | Total career runs |
| **career_wins** | INTEGER | Racecards | `racecards[].runners[].career_total.wins` | 70% | Total career wins |
| **career_places** | INTEGER | Racecards | `racecards[].runners[].career_total.places` | 70% | Total career places |
| **prize_money_won** | DECIMAL(12,2) | Racecards | `racecards[].runners[].prize_money` | 60% | Career prize money |

#### Result Data (From /results endpoint)

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **position** | INTEGER | Results | `results[].runners[].position` | 95% | Finishing position (1-20+) |
| **distance_beaten** | VARCHAR(20) | Results | `results[].runners[].btn` | 95% | Distance behind winner |
| **prize_won** | DECIMAL(10,2) | Results | `results[].runners[].prize` | 90% | Prize money for this race |
| **starting_price** | VARCHAR(20) | Results | `results[].runners[].sp` | 95% | Starting price (e.g., "5/2") |
| **finishing_time** | VARCHAR(20) | Results | `results[].runners[].time` | 60% | Race time |
| **result_updated_at** | TIMESTAMP | Generated | N/A | 95% | When result was captured |

**Critical**: Position fields enable all win rate calculations for ML

#### Comments & Analysis

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **comment** | TEXT | Racecards | `racecards[].runners[].comment` | 80% | Race comments |
| **spotlight** | TEXT | Racecards (Pro) | `racecards[].runners[].spotlight` | 70% | Spotlight preview |
| **silk_url** | TEXT | Both | `racecards[].runners[].silk_url` | 95% | Jockey silk image URL |
| **trainer_rtf** | VARCHAR(50) | Racecards | `racecards[].runners[].trainer_rtf` | 50% | Trainer recent form |
| **trainer_14_days_data** | JSONB | Racecards | `racecards[].runners[].trainer_14_days` | 40% | Trainer 14-day stats |
| **past_results_flags** | TEXT[] | Racecards | `racecards[].runners[].past_results_flags` | 60% | C&D winner, AW winner, etc. |
| **quotes_data** | JSONB | Racecards (Pro) | `racecards[].runners[].quotes` | 30% | Trainer/jockey quotes |
| **stable_tour_data** | JSONB | Racecards (Pro) | `racecards[].runners[].stable_tour` | 20% | Stable tour comments |
| **medical_data** | JSONB | Racecards (Pro) | `racecards[].runners[].medical` | 10% | Medical history |

#### System Fields

| Database Field | Type | API Source | JSON Path | Availability | Notes |
|----------------|------|------------|-----------|--------------|-------|
| **api_data** | JSONB | Both | Full runner object | 100% | Complete raw API data |
| **created_at** | TIMESTAMP | Generated | N/A | 100% | Record creation time |
| **updated_at** | TIMESTAMP | Generated | N/A | 100% | Last update time |

---

### 3. ra_horses (Horse Reference)

**Purpose**: Stores unique horse records
**Source**: Extracted from runner data by `entity_extractor.py`
**Primary Key**: `horse_id`

| Database Field | Type | Derived From | Availability | Notes |
|----------------|------|--------------|--------------|-------|
| **horse_id** | VARCHAR(100) PK | `runners[].horse_id` | 100% | Unique API identifier |
| **name** | VARCHAR(200) | `runners[].horse` | 100% | Horse name |
| **sex** | VARCHAR(10) | `runners[].sex` | 100% | Gender code |
| **created_at** | TIMESTAMP | Generated | 100% | First seen |
| **updated_at** | TIMESTAMP | Generated | 100% | Last updated |

**Note**: Pedigree data (sire, dam, damsire) is stored in ra_mst_runners table, not here

---

### 4. ra_jockeys (Jockey Reference)

**Purpose**: Stores unique jockey records
**Source**: Extracted from runner data by `entity_extractor.py`
**Primary Key**: `jockey_id`

| Database Field | Type | Derived From | Availability | Notes |
|----------------|------|--------------|--------------|-------|
| **jockey_id** | VARCHAR(100) PK | `runners[].jockey_id` | 100% | Unique API identifier |
| **name** | VARCHAR(200) | `runners[].jockey` | 100% | Jockey name |
| **created_at** | TIMESTAMP | Generated | 100% | First seen |
| **updated_at** | TIMESTAMP | Generated | 100% | Last updated |

**Future Enhancement**: Can aggregate career statistics from ra_mst_runners

---

### 5. ra_trainers (Trainer Reference)

**Purpose**: Stores unique trainer records
**Source**: Extracted from runner data by `entity_extractor.py`
**Primary Key**: `trainer_id`

| Database Field | Type | Derived From | Availability | Notes |
|----------------|------|--------------|--------------|-------|
| **trainer_id** | VARCHAR(100) PK | `runners[].trainer_id` | 100% | Unique API identifier |
| **name** | VARCHAR(200) | `runners[].trainer` | 100% | Trainer name |
| **created_at** | TIMESTAMP | Generated | 100% | First seen |
| **updated_at** | TIMESTAMP | Generated | 100% | Last updated |

**Future Enhancement**: Can aggregate career statistics from ra_mst_runners

---

### 6. ra_owners (Owner Reference)

**Purpose**: Stores unique owner records
**Source**: Extracted from runner data by `entity_extractor.py`
**Primary Key**: `owner_id`

| Database Field | Type | Derived From | Availability | Notes |
|----------------|------|--------------|--------------|-------|
| **owner_id** | VARCHAR(100) PK | `runners[].owner_id` | 100% | Unique API identifier |
| **name** | VARCHAR(200) | `runners[].owner` | 100% | Owner name |
| **created_at** | TIMESTAMP | Generated | 100% | First seen |
| **updated_at** | TIMESTAMP | Generated | 100% | Last updated |

---

### 7. ra_courses (Course Reference)

**Purpose**: Stores unique course records
**Source**: Extracted from race data
**Primary Key**: `course_id`

| Database Field | Type | Derived From | Availability | Notes |
|----------------|------|--------------|--------------|-------|
| **course_id** | VARCHAR(100) PK | `racecards[].course_id` | 100% | Unique API identifier |
| **name** | VARCHAR(200) | `racecards[].course` | 100% | Course name |
| **region** | VARCHAR(20) | `racecards[].region` | 100% | GB, IRE, FR, etc. |
| **created_at** | TIMESTAMP | Generated | 100% | First seen |
| **updated_at** | TIMESTAMP | Generated | 100% | Last updated |

---

## Calculated Fields & Derivations

These fields are NOT directly in the API but can be calculated from reference table data.

### Horse Performance Metrics

| Metric | Calculation | Source Tables | Formula |
|--------|-------------|---------------|---------|
| **total_races** | COUNT | ra_mst_runners | `COUNT(*) WHERE horse_id = X` |
| **total_wins** | COUNT | ra_mst_runners | `COUNT(*) WHERE horse_id = X AND position = 1` |
| **total_places** | COUNT | ra_mst_runners | `COUNT(*) WHERE horse_id = X AND position IN (1,2,3)` |
| **win_rate** | PERCENTAGE | ra_mst_runners | `(total_wins / total_races) * 100` |
| **place_rate** | PERCENTAGE | ra_mst_runners | `(total_places / total_races) * 100` |
| **avg_finish_position** | AVG | ra_mst_runners | `AVG(position) WHERE position IS NOT NULL` |
| **days_since_last_run** | DATE_DIFF | ra_mst_runners | `CURRENT_DATE - MAX(race_date)` |
| **total_earnings** | SUM | ra_mst_runners | `SUM(prize_won)` |

### Context-Specific Performance

| Metric | Calculation | Filter | Formula |
|--------|-------------|--------|---------|
| **course_runs** | COUNT | Same course | `COUNT(*) WHERE course_id = current_course` |
| **course_wins** | COUNT | Same course | `COUNT(*) WHERE course_id = current AND position = 1` |
| **course_win_rate** | PERCENTAGE | Same course | `(course_wins / course_runs) * 100` |
| **distance_runs** | COUNT | Similar distance | `COUNT(*) WHERE distance BETWEEN (current * 0.9) AND (current * 1.1)` |
| **distance_wins** | COUNT | Similar distance | `COUNT(*) WHERE distance filter AND position = 1` |
| **distance_win_rate** | PERCENTAGE | Similar distance | `(distance_wins / distance_runs) * 100` |
| **surface_runs** | COUNT | Same surface | `COUNT(*) WHERE surface = current_surface` |
| **surface_wins** | COUNT | Same surface | `COUNT(*) WHERE surface = current AND position = 1` |
| **surface_win_rate** | PERCENTAGE | Same surface | `(surface_wins / surface_runs) * 100` |
| **going_runs** | COUNT | Same going | `COUNT(*) WHERE going = current_going` |
| **going_wins** | COUNT | Same going | `COUNT(*) WHERE going = current AND position = 1` |
| **going_win_rate** | PERCENTAGE | Same going | `(going_wins / going_runs) * 100` |
| **class_runs** | COUNT | Same class | `COUNT(*) WHERE race_class = current_class` |
| **class_wins** | COUNT | Same class | `COUNT(*) WHERE class = current AND position = 1` |
| **class_win_rate** | PERCENTAGE | Same class | `(class_wins / class_runs) * 100` |

### Recent Form

| Metric | Calculation | Formula |
|--------|-------------|---------|
| **last_5_positions** | ARRAY | `ARRAY_AGG(position ORDER BY race_date DESC LIMIT 5)` |
| **last_5_dates** | ARRAY | `ARRAY_AGG(race_date ORDER BY race_date DESC LIMIT 5)` |
| **last_5_courses** | ARRAY | `ARRAY_AGG(course_name ORDER BY race_date DESC LIMIT 5)` |
| **last_10_positions** | ARRAY | `ARRAY_AGG(position ORDER BY race_date DESC LIMIT 10)` |
| **recent_form_score** | WEIGHTED | See formula below |

**Recent Form Score Formula:**
```python
weights = [2.0, 1.5, 1.2, 1.0, 1.0]  # Most recent weighted higher
points = {1: 10, 2: 7, 3: 5, 4: 3, 'other': 1}
score = sum(points[position] * weight for position, weight in zip(last_5_positions, weights))
normalized_score = (score / max_possible_score) * 100
```

### Relationship Performance

| Metric | Calculation | Formula |
|--------|-------------|---------|
| **horse_jockey_runs** | COUNT | `COUNT(*) WHERE horse_id = X AND jockey_id = Y` |
| **horse_jockey_wins** | COUNT | `COUNT(*) WHERE horse_id = X AND jockey_id = Y AND position = 1` |
| **horse_jockey_win_rate** | PERCENTAGE | `(horse_jockey_wins / horse_jockey_runs) * 100` |
| **horse_trainer_runs** | COUNT | `COUNT(*) WHERE horse_id = X AND trainer_id = Y` |
| **horse_trainer_wins** | COUNT | `COUNT(*) WHERE horse_id = X AND trainer_id = Y AND position = 1` |
| **horse_trainer_win_rate** | PERCENTAGE | `(horse_trainer_wins / horse_trainer_runs) * 100` |
| **jockey_trainer_runs** | COUNT | `COUNT(*) WHERE jockey_id = X AND trainer_id = Y` |
| **jockey_trainer_wins** | COUNT | `COUNT(*) WHERE jockey_id = X AND trainer_id = Y AND position = 1` |
| **jockey_trainer_win_rate** | PERCENTAGE | `(jockey_trainer_wins / jockey_trainer_runs) * 100` |

### Jockey/Trainer Career Stats (Aggregated)

| Metric | Calculation | Formula |
|--------|-------------|---------|
| **jockey_career_runs** | COUNT | `COUNT(*) WHERE jockey_id = X` |
| **jockey_career_wins** | COUNT | `COUNT(*) WHERE jockey_id = X AND position = 1` |
| **jockey_career_win_rate** | PERCENTAGE | `(jockey_career_wins / jockey_career_runs) * 100` |
| **jockey_career_earnings** | SUM | `SUM(prize_won) WHERE jockey_id = X` |
| **trainer_career_runs** | COUNT | `COUNT(*) WHERE trainer_id = X` |
| **trainer_career_wins** | COUNT | `COUNT(*) WHERE trainer_id = X AND position = 1` |
| **trainer_career_win_rate** | PERCENTAGE | `(trainer_career_wins / trainer_career_runs) * 100` |
| **trainer_career_earnings** | SUM | `SUM(prize_won) WHERE trainer_id = X` |

---

## Data Availability & Quality

### Overall Coverage

| Category | Fields Required | Available in API | In Database | Completion Rate |
|----------|-----------------|------------------|-------------|-----------------|
| Identification | 6 | 6 | 6 | 100% |
| Race Context | 35 | 32 | 30 | 95% |
| Runner Details | 40 | 38 | 36 | 95% |
| Result Data | 5 | 5 | 5 | 95% (after results) |
| Pedigree | 9 | 9 | 9 | 95% |
| Ratings | 5 | 5 | 5 | 80% (varies by plan) |
| Form & History | 8 | 7 | 7 | 85% |
| Comments | 8 | 8 | 8 | 70% (Pro features) |

### Field Availability by Race Type

| Field | Flat Racing | National Hunt | All-Weather |
|-------|-------------|---------------|-------------|
| Official Rating | 95% | 85% | 95% |
| Racing Post Rating | 90% | 80% | 90% |
| Top Speed Rating | 85% | 75% | 85% |
| Draw | 100% | 10% | 100% |
| Headgear | 80% | 85% | 80% |
| Going Details | 90% | 95% | 70% |
| Rail Movements | 30% | 10% | 5% |
| Stalls Position | 40% | 5% | 30% |

### Data Quality Notes

**High Quality (95%+ availability):**
- Core identification fields (IDs, names)
- Race fundamentals (date, time, course, distance)
- Runner basics (age, sex, connections)
- Position data (after results posted)

**Good Quality (80-95% availability):**
- Ratings (depends on API plan tier)
- Form strings
- Prize money
- Pedigree data

**Moderate Quality (50-80% availability):**
- Comments and analysis (Pro features)
- Historical statistics
- Track conditions
- Equipment details

**Limited Availability (<50%):**
- Pro-only features (quotes, stable tour)
- Track-specific details (rail, stalls)
- Breeder information
- Medical history

---

## API Endpoint Reference

### 1. Racecards Endpoint

**Endpoint**: `GET /v1/racecards/pro`
**Plan Tier**: Pro
**Purpose**: Pre-race declarations and information
**Rate Limit**: 2 requests/second
**Max History**: Future races only (no historical racecards)

**Request Parameters:**
```
date: YYYY-MM-DD (required)
region: GB, IRE, FR, etc. (optional, comma-separated)
```

**Response Structure:**
```json
{
  "racecards": [
    {
      "race_id": "rac_12345678",
      "course": "Newmarket",
      "course_id": "crs_12345",
      "date": "2025-10-14",
      "off_time": "2:15",
      "off_dt": "2025-10-14T14:15:00+01:00",
      "race_name": "Racing Post Trophy",
      "distance": "1m",
      "distance_f": "8.0",
      "distance_round": "1m",
      "region": "GB",
      "type": "Flat",
      "race_class": "Group 1",
      "age_band": "2yo",
      "surface": "Turf",
      "going": "Good to Soft",
      "prize": "£250,000",
      "runners": [
        {
          "horse_id": "hrs_12345678",
          "horse": "Example Horse",
          "age": "2",
          "sex": "C",
          "jockey_id": "jky_12345",
          "jockey": "John Smith",
          "trainer_id": "trn_12345",
          "trainer": "Jane Doe",
          "owner_id": "own_12345",
          "owner": "Racing Syndicate",
          "number": "1",
          "draw": "5",
          "lbs": "126",
          "headgear": "Blinkers",
          "ofr": "95",
          "rpr": "105",
          "ts": "98",
          "sire": "Example Sire",
          "sire_id": "sir_12345",
          "dam": "Example Dam",
          "dam_id": "dam_12345",
          "damsire": "Example Damsire",
          "damsire_id": "dsi_12345",
          "form": "121-",
          "comment": "Won last 2 starts impressively..."
        }
      ]
    }
  ]
}
```

### 2. Results Endpoint

**Endpoint**: `GET /v1/results`
**Plan Tier**: Standard (12 months history), Pro (unlimited)
**Purpose**: Post-race results with finishing positions
**Rate Limit**: 2 requests/second
**History**: Standard = 12 months, Pro = Unlimited

**Request Parameters:**
```
date: YYYY-MM-DD (required)
region: GB, IRE, FR, etc. (optional, comma-separated)
```

**Response Structure:**
```json
{
  "results": [
    {
      "race_id": "rac_12345678",
      "course": "Newmarket",
      "course_id": "crs_12345",
      "date": "2025-10-14",
      "off": "2:15",
      "off_dt": "2025-10-14T14:15:00+01:00",
      "race_name": "Racing Post Trophy",
      "dist_f": "8.0f",
      "dist_m": "1609",
      "type": "Flat",
      "class": "Group 1",
      "surface": "Turf",
      "going": "Good to Soft",
      "region": "GB",
      "runners": [
        {
          "horse_id": "hrs_12345678",
          "horse": "Example Horse",
          "position": "1",
          "btn": "0",
          "sp": "5/2F",
          "prize": "150000.00",
          "number": "1",
          "draw": "5",
          "age": "2",
          "sex": "C",
          "weight_lbs": "126",
          "time": "1:37.45",
          "or": "95",
          "rpr": "105",
          "tsr": "98",
          "jockey": "John Smith",
          "jockey_id": "jky_12345",
          "trainer": "Jane Doe",
          "trainer_id": "trn_12345",
          "owner": "Racing Syndicate",
          "owner_id": "own_12345",
          "sire": "Example Sire",
          "sire_id": "sir_12345",
          "dam": "Example Dam",
          "dam_id": "dam_12345",
          "damsire": "Example Damsire",
          "damsire_id": "dsi_12345"
        }
      ]
    }
  ]
}
```

### Key Differences: Racecards vs Results

| Field | Racecards | Results | Notes |
|-------|-----------|---------|-------|
| **position** | ❌ | ✅ | Critical - only in results |
| **btn** (distance beaten) | ❌ | ✅ | Only in results |
| **sp** (starting price) | ❌ | ✅ | Only in results |
| **prize** | Total prize fund | Prize won by runner | Different meaning |
| **time** | ❌ | ✅ | Finishing time only in results |
| **comment** | ✅ | ❌ | Preview only in racecards |
| **form** | ✅ | ❌ | Form string only in racecards |
| **headgear** | Often populated | Often empty | Better in racecards |

---

## Known Limitations

### API Limitations

1. **Historical Racecards**: NOT available - API only provides future/today's racecards
2. **Results History**: Standard plan = 12 months, Pro = unlimited
3. **Rate Limits**: 2 requests/second maximum
4. **Missing Data**: Some fields often empty or "-" (especially for lower-grade races)

### Database Limitations

1. **No Historical Racecards**: We only have results for past races, not original declarations
2. **Position Data Dependency**: All calculated metrics depend on having results with positions
3. **Rating Availability**: Varies by race type and API plan tier
4. **Track Details**: Rail movements, stalls position often not provided by API

### Field-Specific Limitations

**Fields with <50% availability:**
- `weather_conditions` (40%)
- `track_condition` (detailed going) (50%)
- `rail_movements` (20%)
- `stalls_position` (30%)
- `trainer_14_days_data` (40%)
- `breeder` (40%)
- `quotes_data` (30%)
- `stable_tour_data` (20%)
- `medical_data` (10%)

**Fields with regional variation:**
- `draw`: Always populated for Flat, rarely for National Hunt
- `going_detailed`: More common in GB/IRE than elsewhere
- `jumps`: Only for National Hunt races

**Fields requiring Pro plan:**
- `rpr` (Racing Post Rating)
- `timeform_rating`
- `spotlight`
- `quotes_data`
- `stable_tour_data`
- `medical_data`
- `tip`
- `verdict`
- `betting_forecast`

---

## Usage Examples

### Example 1: Get Horse Performance Statistics

```sql
-- Get comprehensive horse stats for a specific horse
SELECT
    h.name AS horse_name,
    COUNT(*) AS total_races,
    COUNT(*) FILTER (WHERE r.position = 1) AS total_wins,
    COUNT(*) FILTER (WHERE r.position <= 3) AS total_places,
    ROUND(
        COUNT(*) FILTER (WHERE r.position = 1)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS win_rate,
    SUM(r.prize_won) AS total_earnings,
    AVG(r.position) FILTER (WHERE r.position IS NOT NULL) AS avg_finish,
    MAX(races.race_date) AS last_run_date
FROM ra_horses h
LEFT JOIN ra_mst_runners r ON h.horse_id = r.horse_id
LEFT JOIN ra_mst_races races ON r.race_id = races.race_id
WHERE h.horse_id = 'hrs_12345678'
GROUP BY h.horse_id, h.name;
```

### Example 2: Get Course-Specific Performance

```sql
-- Get horse's performance at specific course
SELECT
    c.name AS course_name,
    COUNT(*) AS runs_at_course,
    COUNT(*) FILTER (WHERE r.position = 1) AS wins_at_course,
    ROUND(
        COUNT(*) FILTER (WHERE r.position = 1)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS course_win_rate
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
JOIN ra_courses c ON races.course_id = c.course_id
WHERE r.horse_id = 'hrs_12345678'
  AND c.course_id = 'crs_12345'
GROUP BY c.course_id, c.name;
```

### Example 3: Get Recent Form

```sql
-- Get last 5 races for a horse
SELECT
    races.race_date,
    races.course_name,
    races.race_name,
    r.position,
    r.distance_beaten,
    r.starting_price,
    j.name AS jockey_name,
    t.name AS trainer_name
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
LEFT JOIN ra_jockeys j ON r.jockey_id = j.jockey_id
LEFT JOIN ra_trainers t ON r.trainer_id = t.trainer_id
WHERE r.horse_id = 'hrs_12345678'
  AND r.position IS NOT NULL
ORDER BY races.race_date DESC
LIMIT 5;
```

### Example 4: Get Jockey-Trainer Combination Stats

```sql
-- Get performance stats for jockey-trainer combination
SELECT
    j.name AS jockey_name,
    t.name AS trainer_name,
    COUNT(*) AS total_runs,
    COUNT(*) FILTER (WHERE r.position = 1) AS total_wins,
    ROUND(
        COUNT(*) FILTER (WHERE r.position = 1)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS win_rate,
    SUM(r.prize_won) AS total_prize_money
FROM ra_mst_runners r
JOIN ra_jockeys j ON r.jockey_id = j.jockey_id
JOIN ra_trainers t ON r.trainer_id = t.trainer_id
WHERE r.jockey_id = 'jky_12345'
  AND r.trainer_id = 'trn_12345'
  AND r.position IS NOT NULL
GROUP BY j.jockey_id, j.name, t.trainer_id, t.name;
```

### Example 5: Get Today's Runners with Full Context

```sql
-- Get today's runners with complete stats for API response
SELECT
    r.runner_id,
    r.race_id,
    races.race_name,
    races.course_name,
    races.off_datetime,
    h.name AS horse_name,
    r.age,
    r.sex,
    r.number,
    r.draw,
    r.weight_lbs,
    r.official_rating,
    r.racing_post_rating,
    r.tsr,
    j.name AS jockey_name,
    t.name AS trainer_name,
    o.name AS owner_name,
    r.form,
    r.comment,
    -- Calculated stats (would need subqueries or joins)
    (SELECT COUNT(*) FROM ra_mst_runners r2 WHERE r2.horse_id = r.horse_id) AS total_races,
    (SELECT COUNT(*) FROM ra_mst_runners r2 WHERE r2.horse_id = r.horse_id AND r2.position = 1) AS total_wins
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
JOIN ra_horses h ON r.horse_id = h.horse_id
LEFT JOIN ra_jockeys j ON r.jockey_id = j.jockey_id
LEFT JOIN ra_trainers t ON r.trainer_id = t.trainer_id
LEFT JOIN ra_owners o ON r.owner_id = o.owner_id
WHERE races.race_date = CURRENT_DATE
  AND r.position IS NULL  -- No result yet
ORDER BY races.off_datetime, r.number;
```

### Example 6: Build Runner Ratings for API

```python
# Python example: Build comprehensive runner data for API
def get_runner_with_stats(runner_id):
    """Get runner with calculated stats for API response"""

    # Fetch base runner data
    runner = supabase.table('ra_mst_runners').select('*').eq('runner_id', runner_id).single().execute()

    # Fetch race data
    race = supabase.table('ra_mst_races').select('*').eq('race_id', runner.data['race_id']).single().execute()

    # Calculate career stats
    career_stats = calculate_career_stats(runner.data['horse_id'])

    # Calculate context stats
    course_stats = calculate_course_stats(runner.data['horse_id'], race.data['course_id'])
    distance_stats = calculate_distance_stats(runner.data['horse_id'], race.data['distance_meters'])

    # Calculate recent form
    recent_form = get_recent_form(runner.data['horse_id'], limit=5)

    # Calculate relationship stats
    jockey_trainer_stats = calculate_jockey_trainer_stats(
        runner.data['jockey_id'],
        runner.data['trainer_id']
    )

    # Build comprehensive response
    return {
        **runner.data,
        'race': race.data,
        'career_stats': career_stats,
        'course_stats': course_stats,
        'distance_stats': distance_stats,
        'recent_form': recent_form,
        'jockey_trainer_combo': jockey_trainer_stats
    }
```

---

## Summary for API Developers

### Quick Reference: What You Can Expose

**Directly Available (no calculation):**
- All race details (course, time, distance, surface, going, class)
- All runner details (horse, jockey, trainer, owner)
- Pedigree information (sire, dam, damsire)
- Ratings (OR, RPR, TSR) - when available
- Equipment (headgear, blinkers, etc.)
- Results (position, distance beaten, prize won, SP)
- Form strings and comments

**Requires Calculation:**
- Win rates (overall, by course, by distance, etc.)
- Career statistics (runs, wins, places, earnings)
- Recent form scores
- Average finishing position
- Days since last run
- Relationship statistics (jockey-trainer combos)
- Performance trends

**Data Quality Expectations:**
- Core fields: 95%+ availability
- Ratings: 80%+ availability (varies by plan)
- Comments: 70%+ availability
- Track details: 30-50% availability
- Pro features: 20-70% availability

**Update Frequency:**
- Racecards: Real-time updates throughout day
- Results: Usually within 30 minutes of race finish
- Reference data: Updated with each fetch
- Calculated stats: Update after each new result

---

## Document Control

**Version**: 1.0
**Date**: 2025-10-14
**Author**: DarkHorses Development Team
**Status**: Production Ready
**Next Review**: After significant schema changes

**Related Documents:**
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-AI-Engine/DATA_SOURCES_MAPPING.md` - Comprehensive data analysis
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/ARCHITECTURE.md` - System architecture
- `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/HOW_IT_WORKS.md` - Worker operations

**Change Log:**
- 2025-10-14: Initial comprehensive data sources documentation created

---

**END OF DOCUMENT**
