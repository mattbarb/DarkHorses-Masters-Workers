# Table to Script Mapping - Complete Reference

**Date:** 2025-10-21
**Purpose:** Definitive mapping of every ra_* table to its population script
**Location:** `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/`

---

## Quick Reference

| Table | Primary Script | Type | Mode | API Endpoint |
|-------|---------------|------|------|--------------|
| ra_mst_courses | `master_fetcher_controller.py` (courses_fetcher.py) | Fetcher | Backfill/Daily | /v1/courses |
| ra_mst_bookmakers | `master_fetcher_controller.py` (bookmakers_fetcher.py) | Fetcher | Backfill/Daily | /v1/bookmakers |
| ra_mst_jockeys | `master_fetcher_controller.py` (jockeys_fetcher.py) | Fetcher | Backfill/Daily | /v1/jockeys |
| ra_mst_trainers | `master_fetcher_controller.py` (trainers_fetcher.py) | Fetcher | Backfill/Daily | /v1/trainers |
| ra_mst_owners | `master_fetcher_controller.py` (owners_fetcher.py) | Fetcher | Backfill/Daily | /v1/owners |
| ra_mst_horses | `master_fetcher_controller.py` (races_fetcher.py) | Fetcher | Backfill/Daily | /v1/racecards/pro + /v1/horses/{id}/pro |
| ra_horse_pedigree | `master_fetcher_controller.py` (races_fetcher.py) | Fetcher | Backfill/Daily | /v1/horses/{id}/pro |
| ra_races | `master_fetcher_controller.py` (races_fetcher.py) | Fetcher | Backfill/Daily | /v1/racecards/pro |
| ra_runners | `master_fetcher_controller.py` (races_fetcher.py) | Fetcher | Backfill/Daily | /v1/racecards/pro |
| ra_race_results | `master_fetcher_controller.py` (results_fetcher.py) | Fetcher | Backfill/Daily | /v1/results |
| ra_mst_sires | `../scripts/population_workers/pedigree_statistics_agent.py` | Calculator | Weekly | Database calculation |
| ra_mst_dams | `../scripts/population_workers/pedigree_statistics_agent.py` | Calculator | Weekly | Database calculation |
| ra_mst_damsires | `../scripts/population_workers/pedigree_statistics_agent.py` | Calculator | Weekly | Database calculation |
| ra_mst_jockeys (stats) | `../scripts/statistics_workers/calculate_jockey_statistics.py` | Calculator | Weekly | Database calculation |
| ra_mst_trainers (stats) | `../scripts/statistics_workers/calculate_trainer_statistics.py` | Calculator | Weekly | Database calculation |
| ra_mst_owners (stats) | `../scripts/statistics_workers/calculate_owner_statistics.py` | Calculator | Weekly | Database calculation |

---

## Detailed Table Information

### ra_mst_courses

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `courses_fetcher.py`
**Data Source:** Racing API `/v1/courses`
**Update Frequency:** Monthly

**Columns Populated (15):**
- Core: id, name, code, region, country
- Details: type, surface, latitude, longitude
- Metadata: created_at, updated_at

**How to Run:**
```bash
# Via master controller (recommended)
python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses

# Direct fetcher (legacy)
python3 -c "from fetchers.courses_fetcher import CoursesFetcher; CoursesFetcher().fetch_and_store()"
```

**Backfill:** Bulk fetch (all current courses)
**Daily:** Bulk fetch (updates current courses)

---

### ra_mst_bookmakers

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `bookmakers_fetcher.py`
**Data Source:** Racing API `/v1/bookmakers`
**Update Frequency:** Monthly

**Columns Populated (10):**
- Core: id, name, url
- Metadata: created_at, updated_at

**How to Run:**
```bash
# Via master controller (recommended)
python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_bookmakers

# Direct fetcher (legacy)
python3 -c "from fetchers.bookmakers_fetcher import BookmakersFetcher; BookmakersFetcher().fetch_and_store()"
```

**Backfill:** Bulk fetch (all current bookmakers)
**Daily:** Bulk fetch (updates current bookmakers)

---

### ra_mst_jockeys

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `jockeys_fetcher.py`
**Data Source:** Racing API `/v1/jockeys` (region_codes=['gb', 'ire'])
**Update Frequency:** Weekly

**Columns Populated (25+):**
- Core: id, name, region, nationality, dob
- Statistics: From API statistics object
- Metadata: created_at, updated_at

**Additional Statistics Script:** `../scripts/statistics_workers/calculate_jockey_statistics.py`
**Statistics Source:** Database calculation from ra_runners + ra_races

**How to Run:**
```bash
# Fetch from API (weekly)
python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys

# Calculate additional statistics (weekly)
python3 scripts/statistics_workers/calculate_jockey_statistics.py
```

**Backfill:** Bulk fetch (all active jockeys)
**Daily:** Bulk fetch (updates all jockeys)

---

### ra_mst_trainers

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `trainers_fetcher.py`
**Data Source:** Racing API `/v1/trainers` (region_codes=['gb', 'ire'])
**Update Frequency:** Weekly

**Columns Populated (25+):**
- Core: id, name, region, location
- Statistics: From API statistics object
- Metadata: created_at, updated_at

**Additional Statistics Script:** `../scripts/statistics_workers/calculate_trainer_statistics.py`
**Statistics Source:** Database calculation from ra_runners + ra_races

**How to Run:**
```bash
# Fetch from API (weekly)
python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_trainers

# Calculate additional statistics (weekly)
python3 scripts/statistics_workers/calculate_trainer_statistics.py
```

**Backfill:** Bulk fetch (all active trainers)
**Daily:** Bulk fetch (updates all trainers)

---

### ra_mst_owners

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `owners_fetcher.py`
**Data Source:** Racing API `/v1/owners` (region_codes=['gb', 'ire'])
**Update Frequency:** Weekly

**Columns Populated (20+):**
- Core: id, name, region
- Statistics: From API statistics object
- Metadata: created_at, updated_at

**Additional Statistics Script:** `../scripts/statistics_workers/calculate_owner_statistics.py`
**Statistics Source:** Database calculation from ra_runners + ra_races

**How to Run:**
```bash
# Fetch from API (weekly)
python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_owners

# Calculate additional statistics (weekly)
python3 scripts/statistics_workers/calculate_owner_statistics.py
```

**Backfill:** Bulk fetch (all active owners)
**Daily:** Bulk fetch (updates all owners)

---

### ra_mst_horses

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `races_fetcher.py` (hybrid enrichment)
**Data Source:**
- Discovery: `/v1/racecards/pro` (runner.horse)
- Enrichment: `/v1/horses/{id}/pro` (NEW horses only)
**Update Frequency:** Daily

**Columns Populated (25+):**
- Discovery (all horses): id, name, sex
- Enrichment (NEW only): sex_code, dob, colour, colour_code, region, sire_id, dam_id, damsire_id
- Metadata: created_at, updated_at

**How to Run:**
```bash
# Via master controller (recommended) - includes enrichment
python3 fetchers/master_fetcher_controller.py --mode daily

# Races fetcher automatically discovers and enriches horses
# NOTE: Uses hybrid strategy - only enriches NEW horses
```

**Backfill:** Extracted from racecards 2015-present + enrichment
**Daily:** Extracted from racecards last 3 days + enrichment for NEW horses

**Special Notes:**
- Hybrid enrichment: 50-100 new horses/day enriched automatically
- Pedigree data captured during enrichment
- NO need for separate horses fetch (included in races fetch)

---

### ra_horse_pedigree

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `races_fetcher.py` (during horse enrichment)
**Data Source:** `/v1/horses/{id}/pro` (pedigree object)
**Update Frequency:** Daily

**Columns Populated (10):**
- horse_id, sire, sire_id, dam, dam_id
- damsire, damsire_id, breeder, breeder_location
- Metadata: created_at

**How to Run:**
```bash
# Automatically populated during horse enrichment
python3 fetchers/master_fetcher_controller.py --mode daily

# Pedigree is extracted when NEW horse is enriched
```

**Backfill:** Captured during horse backfill
**Daily:** Captured when NEW horses are enriched

**Special Notes:**
- Automatically populated - no separate fetch needed
- Only populated for horses that get enriched
- Source for ra_mst_sires/dams/damsires names

---

### ra_races

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `races_fetcher.py`
**Data Source:** Racing API `/v1/racecards/pro`
**Update Frequency:** Daily

**Columns Populated (30+):**
- Core: id, date, time, course_id, course_name
- Details: race_class, distance, distance_f, distance_m
- Conditions: going, prize_money, race_type, age_band
- Metadata: created_at, updated_at

**How to Run:**
```bash
# Via master controller (recommended)
python3 fetchers/master_fetcher_controller.py --mode daily

# Specific date range (manual)
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_races --start-date 2024-01-01 --end-date 2024-01-31
```

**Backfill:** Date range 2015-01-01 to present (~150,000 races)
**Daily:** Last 3 days (~300 races)

**Special Notes:**
- Also creates runners, horses, and pedigree records
- Primary entry point for race data

---

### ra_runners

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `races_fetcher.py` (pre-race) + `results_fetcher.py` (post-race)
**Data Source:**
- Pre-race: `/v1/racecards/pro`
- Post-race: `/v1/results` (updates with position data)
**Update Frequency:** Daily

**Columns Populated (40+):**
- Core: id, race_id, horse_id, jockey_id, trainer_id, owner_id
- Pedigree: sire_id, dam_id, damsire_id
- Pre-race: draw, weight, age, form, official_rating
- Post-race: position, distance_beaten, finishing_time, starting_price
- Enhanced: starting_price_decimal, race_comment, jockey_silk_url
- Metadata: created_at, updated_at

**How to Run:**
```bash
# Create runners (pre-race data)
python3 fetchers/master_fetcher_controller.py --mode daily

# Update with results (post-race data)
# Automatically runs as part of daily sync
```

**Backfill:**
- Runners created from racecards 2015-present (~2,000,000 runners)
- Updated with results data

**Daily:** Last 3 days runners + results updates

**Special Notes:**
- Created during races fetch
- Updated by results fetch with position data
- 6 enhanced fields added in migration 011

---

### ra_race_results

**Primary Script:** `master_fetcher_controller.py`
**Underlying Fetcher:** `results_fetcher.py`
**Data Source:** Racing API `/v1/results`
**Update Frequency:** Daily

**Columns Populated (35+):**
- Core: race_id, runner_id
- Position: position, distance_beaten
- Time: finishing_time
- Odds: starting_price, starting_price_decimal
- Commentary: race_comment
- Enhanced: overall_beaten_distance, jockey_claim_lbs, weight_stones_lbs
- Metadata: created_at, updated_at

**How to Run:**
```bash
# Via master controller (recommended)
python3 fetchers/master_fetcher_controller.py --mode daily

# Specific date range (manual)
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_race_results --start-date 2024-01-01 --end-date 2024-01-31
```

**Backfill:** Date range 2015-01-01 to present (~150,000 results)
**Daily:** Last 3 days (~300 results)

**Special Notes:**
- Updates ra_runners table with position data
- Populates 6 enhanced fields
- Critical for statistics calculations

---

### ra_mst_sires

**Primary Script:** `../scripts/population_workers/pedigree_statistics_agent.py`
**Data Source:** Database calculation (ra_mst_horses + ra_runners + ra_races)
**Update Frequency:** Weekly

**Columns Populated (47):**
- Names: Populated by migration 026 from ra_horse_pedigree
- Statistics (42): Calculated by pedigree agent
  - Basic: total_runners, total_wins, total_places_2nd/3rd, overall_win_percent
  - AE indices: overall_ae_index, best_class_ae, best_distance_ae
  - Class breakdown: class_1/2/3 (name, runners, wins, win_percent, ae)
  - Distance breakdown: distance_1/2/3 (name, runners, wins, win_percent, ae)
  - Metadata: analysis_last_updated, data_quality_score

**How to Run:**
```bash
# Full calculation
python3 scripts/population_workers/pedigree_statistics_agent.py --table sires

# Test (10 entities)
python3 scripts/population_workers/pedigree_statistics_agent.py --table sires --test
```

**Backfill:** Calculate from all historical data (2,143 sires)
**Weekly:** Re-calculate to update statistics

**Special Notes:**
- NO API calls - all from database
- Names populated first by migration
- Statistics calculated from progeny performance

---

### ra_mst_dams

**Primary Script:** `../scripts/population_workers/pedigree_statistics_agent.py`
**Data Source:** Database calculation (ra_mst_horses + ra_runners + ra_races)
**Update Frequency:** Weekly

**Columns Populated (47):**
- Names: Populated by migration 026 from ra_horse_pedigree
- Statistics (42): Calculated by pedigree agent (same as sires)

**How to Run:**
```bash
# Full calculation
python3 scripts/population_workers/pedigree_statistics_agent.py --table dams

# Test (10 entities)
python3 scripts/population_workers/pedigree_statistics_agent.py --table dams --test
```

**Backfill:** Calculate from all historical data (48,372 dams)
**Weekly:** Re-calculate to update statistics

**Duration:** ~2-3 hours for full calculation

**Special Notes:**
- Largest pedigree table (48k entities)
- Same column structure as sires/damsires
- All data from database (no API)

---

### ra_mst_damsires

**Primary Script:** `../scripts/population_workers/pedigree_statistics_agent.py`
**Data Source:** Database calculation (ra_mst_horses + ra_runners + ra_races)
**Update Frequency:** Weekly

**Columns Populated (47):**
- Names: Populated by migration 026 from ra_horse_pedigree
- Statistics (42): Calculated by pedigree agent (same as sires)

**How to Run:**
```bash
# Full calculation
python3 scripts/population_workers/pedigree_statistics_agent.py --table damsires

# Test (10 entities)
python3 scripts/population_workers/pedigree_statistics_agent.py --table damsires --test
```

**Backfill:** Calculate from all historical data (3,041 damsires)
**Weekly:** Re-calculate to update statistics

**Special Notes:**
- Damsire = maternal grandsire
- Same column structure as sires/dams
- All data from database (no API)

---

## Execution Order

### Initial Backfill

**Step 1: Racing API Data (Fetchers)**
```bash
# Run ALL fetchers (6-8 hours)
python3 fetchers/master_fetcher_controller.py --mode backfill
```

This populates (in order):
1. ra_mst_courses
2. ra_mst_bookmakers
3. ra_mst_jockeys
4. ra_mst_trainers
5. ra_mst_owners
6. ra_races (+ ra_runners, ra_mst_horses, ra_horse_pedigree)
7. ra_race_results (updates ra_runners)

**Step 2: Pedigree Statistics (Database Calculation)**
```bash
# Calculate pedigree statistics (3-4 hours)
python3 scripts/population_workers/pedigree_statistics_agent.py
```

This populates:
1. ra_mst_sires (2,143 entities)
2. ra_mst_dams (48,372 entities)
3. ra_mst_damsires (3,041 entities)

**Step 3: Entity Statistics (Database Calculation)**
```bash
# Calculate entity statistics (15 minutes)
python3 scripts/statistics_workers/run_all_statistics_workers.py
```

This updates:
1. ra_mst_jockeys (additional statistics)
2. ra_mst_trainers (additional statistics)
3. ra_mst_owners (additional statistics)

**Total Time:** ~10-12 hours

---

### Daily Sync

**1am UK Time (Automated)**
```bash
# Cron job
0 1 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1
```

**Duration:** ~10 minutes

**What it does:**
- Fetches last 3 days of races/results
- Updates current master tables
- Enriches NEW horses
- Updates runner positions

---

### Weekly Refresh

**Sunday 2am UK Time (Automated)**
```bash
# Cron job
0 2 * * 0 cd /path/to/project && python3 scripts/population_workers/pedigree_statistics_agent.py >> logs/cron_weekly.log 2>&1
```

**Duration:** ~3-4 hours

**What it does:**
- Re-calculates all pedigree statistics
- Updates with latest race results
- Refreshes AE indices

---

## Script Locations

### Fetchers (All in this directory)
```
fetchers/
├── master_fetcher_controller.py    ⭐ Master orchestrator
├── courses_fetcher.py
├── bookmakers_fetcher.py
├── jockeys_fetcher.py
├── trainers_fetcher.py
├── owners_fetcher.py
├── races_fetcher.py                (also handles horses, pedigree, runners)
└── results_fetcher.py
```

### Population Workers (Statistics)
```
scripts/population_workers/
├── pedigree_statistics_agent.py    ⭐ Pedigree statistics
└── master_populate_all_ra_tables.py

scripts/statistics_workers/
├── calculate_jockey_statistics.py
├── calculate_trainer_statistics.py
├── calculate_owner_statistics.py
└── run_all_statistics_workers.py
```

---

## Quick Command Reference

```bash
# BACKFILL (First Time - 6-8 hours)
python3 fetchers/master_fetcher_controller.py --mode backfill

# DAILY SYNC (~10 minutes)
python3 fetchers/master_fetcher_controller.py --mode daily

# PEDIGREE STATISTICS (3-4 hours)
python3 scripts/population_workers/pedigree_statistics_agent.py

# SPECIFIC TABLE
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races --start-date 2024-01-01

# TEST MODE
python3 fetchers/master_fetcher_controller.py --mode daily --test

# LIST TABLES
python3 fetchers/master_fetcher_controller.py --list
```

---

**Last Updated:** 2025-10-21
**Location:** `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/`
**Related:** See TABLE_COLUMN_MAPPING.json for field-level details
