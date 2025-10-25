# Fetchers - Racing API Data Collection System

## Overview

This directory contains ALL fetchers for collecting data from The Racing API. Each fetcher is responsible for populating specific tables in the database.

**Master Controller:** `master_fetcher_controller.py` - Orchestrates all fetching operations

## 📚 Documentation

**Complete documentation is in the `/fetchers/docs/` subdirectory:**

- **[CONTROLLER_QUICK_START.md](docs/CONTROLLER_QUICK_START.md)** - Master controller usage guide
- **[FETCHERS_INDEX.md](docs/FETCHERS_INDEX.md)** - Quick navigation and data flow
- **[TABLE_TO_SCRIPT_MAPPING.md](docs/TABLE_TO_SCRIPT_MAPPING.md)** - Definitive table-to-script reference
- **[COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md](docs/COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md)** - Complete implementation guide
- **[TABLE_COLUMN_MAPPING.json](docs/TABLE_COLUMN_MAPPING.json)** - Detailed column-level mapping
- **[COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json](docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json)** - All 625+ columns with data sources
- **[COMPLETE_COLUMN_INVENTORY.md](docs/COMPLETE_COLUMN_INVENTORY.md)** - Column inventory in markdown format

## Quick Start

```bash
# Daily sync (for 1am cron)
python3 fetchers/master_fetcher_controller.py --mode daily

# Backfill from 2015
python3 fetchers/master_fetcher_controller.py --mode backfill

# Manual - specific table
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races --start-date 2024-01-01

# List all tables
python3 fetchers/master_fetcher_controller.py --list
```

## Fetcher Modes

### 1. BACKFILL Mode
**Purpose:** Initial data population from 2015-01-01 to present
**When to use:** First-time setup, data recovery, historical gaps
**Time:** ~4-6 hours for complete backfill

```bash
# Backfill all tables
python3 fetchers/master_fetcher_controller.py --mode backfill

# Backfill specific tables
python3 fetchers/master_fetcher_controller.py --mode backfill --tables ra_races ra_runners
```

### 2. DAILY Mode
**Purpose:** Daily updates at 1am UK time
**Fetches:** Last 3 days + current reference data
**Time:** ~5-10 minutes

```bash
# Daily sync (add to cron)
python3 fetchers/master_fetcher_controller.py --mode daily

# Test daily sync
python3 fetchers/master_fetcher_controller.py --mode daily --test
```

### 3. MANUAL Mode
**Purpose:** Ad-hoc fetching with custom parameters
**Use cases:** Specific date ranges, testing, data fixes

```bash
# Fetch specific date range
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races \
    --start-date 2024-01-01 --end-date 2024-01-31

# Fetch last N days
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races --days-back 7
```

## Table-to-Fetcher Mapping

### Master Tables (Reference Data)

| Table | Fetcher | Type | API Endpoint | Update Frequency |
|-------|---------|------|--------------|------------------|
| `ra_mst_courses` | `courses_fetcher.py` | Bulk | `/v1/courses` | Monthly |
| `ra_mst_bookmakers` | `bookmakers_fetcher.py` | Bulk | `/v1/bookmakers` | Monthly |
| `ra_mst_jockeys` | `jockeys_fetcher.py` | Bulk | `/v1/jockeys` | Weekly |
| `ra_mst_trainers` | `trainers_fetcher.py` | Bulk | `/v1/trainers` | Weekly |
| `ra_mst_owners` | `owners_fetcher.py` | Bulk | `/v1/owners` | Weekly |

**Bulk Type:** Always fetches current/active data. No date range needed.

### Transaction Tables (Date-Based)

| Table | Fetcher | Type | API Endpoint | Update Frequency |
|-------|---------|------|--------------|------------------|
| `ra_races` | `races_fetcher.py` | Date Range | `/v1/racecards/pro` | Daily |
| `ra_runners` | `races_fetcher.py` | Date Range | `/v1/racecards/pro` | Daily |
| `ra_mst_horses` | `races_fetcher.py` | Extracted | `/v1/racecards/pro` + enrichment | Daily |
| `ra_horse_pedigree` | `races_fetcher.py` | Extracted | `/v1/horses/{id}/pro` | Daily |
| `ra_race_results` | `results_fetcher.py` | Date Range | `/v1/results` | Daily |

**Date Range Type:** Requires start/end dates or days_back parameter.
**Extracted Type:** Data is extracted during another fetcher's operation.

## Column Details by Table

### ra_mst_courses (15 columns)
**Source:** `/v1/courses`
**Fetcher:** `courses_fetcher.py`

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | course.id | Unique course ID |
| name | varchar(255) | course.name | Course name |
| code | varchar(20) | course.code | Short code |
| region | varchar(50) | course.region | Region (GB/IRE) |
| country | varchar(50) | course.country | Country name |
| type | varchar(50) | course.type | Flat/Jump |
| surface | varchar(50) | course.surface | Turf/All-weather |
| latitude | numeric | course.latitude | GPS latitude |
| longitude | numeric | course.longitude | GPS longitude |
| ... | ... | ... | (15 total) |

### ra_mst_bookmakers (10 columns)
**Source:** `/v1/bookmakers`
**Fetcher:** `bookmakers_fetcher.py`

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | bookmaker.id | Unique bookmaker ID |
| name | varchar(255) | bookmaker.name | Bookmaker name |
| url | text | bookmaker.url | Website URL |
| ... | ... | ... | (10 total) |

### ra_mst_jockeys (25+ columns)
**Source:** `/v1/jockeys`
**Fetcher:** `jockeys_fetcher.py`
**Filter:** region_codes = ['gb', 'ire']

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | jockey.id | Unique jockey ID |
| name | varchar(255) | jockey.name | Jockey name |
| region | varchar(50) | jockey.region | GB/IRE |
| nationality | varchar(100) | jockey.nationality | Nationality |
| dob | date | jockey.dob | Date of birth |
| statistics columns | ... | jockey.statistics.* | Performance stats |
| ... | ... | ... | (25+ total) |

### ra_mst_trainers (25+ columns)
**Source:** `/v1/trainers`
**Fetcher:** `trainers_fetcher.py`
**Filter:** region_codes = ['gb', 'ire']

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | trainer.id | Unique trainer ID |
| name | varchar(255) | trainer.name | Trainer name |
| region | varchar(50) | trainer.region | GB/IRE |
| location | varchar(255) | trainer.location | Training yard location |
| statistics columns | ... | trainer.statistics.* | Performance stats |
| ... | ... | ... | (25+ total) |

### ra_mst_owners (20+ columns)
**Source:** `/v1/owners`
**Fetcher:** `owners_fetcher.py`
**Filter:** region_codes = ['gb', 'ire']

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | owner.id | Unique owner ID |
| name | varchar(255) | owner.name | Owner name |
| region | varchar(50) | owner.region | GB/IRE |
| statistics columns | ... | owner.statistics.* | Performance stats |
| ... | ... | ... | (20+ total) |

### ra_mst_horses (25+ columns)
**Source:** `/v1/racecards/pro` (discovery) + `/v1/horses/{id}/pro` (enrichment)
**Fetcher:** `races_fetcher.py` (EntityExtractor with hybrid enrichment)

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | runner.horse.id | Unique horse ID |
| name | varchar(255) | runner.horse.name | Horse name |
| sex | varchar(10) | horse_pro.sex | Sex (discovery) |
| sex_code | varchar(10) | horse_pro.sex_code | M/F/G/C (enrichment) |
| dob | date | horse_pro.dob | Date of birth (enrichment) |
| colour | varchar(50) | horse_pro.colour | Colour (enrichment) |
| colour_code | varchar(20) | horse_pro.colour_code | Colour code (enrichment) |
| region | varchar(50) | horse_pro.region | GB/IRE (enrichment) |
| sire_id | varchar(50) | horse_pro.pedigree.sire_id | Sire ID (enrichment) |
| dam_id | varchar(50) | horse_pro.pedigree.dam_id | Dam ID (enrichment) |
| damsire_id | varchar(50) | horse_pro.pedigree.damsire_id | Damsire ID (enrichment) |
| ... | ... | ... | (25+ total) |

**Enrichment:** NEW horses automatically enriched with Pro endpoint for complete metadata + pedigree.

### ra_horse_pedigree (10 columns)
**Source:** `/v1/horses/{id}/pro`
**Fetcher:** `races_fetcher.py` (during horse enrichment)

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| horse_id | varchar(50) | horse.id | Horse ID (FK) |
| sire | varchar(255) | pedigree.sire | Sire name |
| sire_id | varchar(50) | pedigree.sire_id | Sire ID (FK) |
| dam | varchar(255) | pedigree.dam | Dam name |
| dam_id | varchar(50) | pedigree.dam_id | Dam ID (FK) |
| damsire | varchar(255) | pedigree.damsire | Damsire name |
| damsire_id | varchar(50) | pedigree.damsire_id | Damsire ID (FK) |
| breeder | varchar(255) | pedigree.breeder | Breeder name |
| breeder_location | varchar(255) | pedigree.breeder_location | Breeder location |
| ... | ... | ... | (10 total) |

### ra_races (30+ columns)
**Source:** `/v1/racecards/pro`
**Fetcher:** `races_fetcher.py`

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | race.id | Unique race ID |
| date | date | race.date | Race date |
| time | time | race.time | Race time |
| course_id | varchar(50) | race.course.id | Course ID (FK) |
| course_name | varchar(255) | race.course.name | Course name |
| race_class | varchar(20) | race.class | Race class |
| distance | varchar(50) | race.distance | Distance (text) |
| distance_f | varchar(20) | race.distance_f | Distance (furlongs) |
| distance_m | integer | race.distance_m | Distance (meters) |
| going | varchar(50) | race.going | Going description |
| prize_money | integer | race.prize | Prize money |
| race_type | varchar(50) | race.type | Flat/Jump/etc |
| age_band | varchar(50) | race.age_band | Age restrictions |
| ... | ... | ... | (30+ total) |

### ra_runners (40+ columns)
**Source:** `/v1/racecards/pro`
**Fetcher:** `races_fetcher.py`

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| id | varchar(50) | runner.id | Unique runner ID |
| race_id | varchar(50) | race.id | Race ID (FK) |
| horse_id | varchar(50) | runner.horse.id | Horse ID (FK) |
| jockey_id | varchar(50) | runner.jockey.id | Jockey ID (FK) |
| trainer_id | varchar(50) | runner.trainer.id | Trainer ID (FK) |
| owner_id | varchar(50) | runner.owner.id | Owner ID (FK) |
| draw | integer | runner.draw | Starting stall |
| weight | varchar(20) | runner.weight | Weight carried |
| age | integer | runner.age | Horse age |
| form | varchar(50) | runner.form | Recent form |
| official_rating | integer | runner.official_rating | OR |
| ... | ... | ... | (40+ total) |

**Enhanced Fields (from results):**
- position, distance_beaten, prize_won
- starting_price, starting_price_decimal
- finishing_time, race_comment
- jockey_silk_url, overall_beaten_distance
- jockey_claim_lbs, weight_stones_lbs

### ra_race_results (35+ columns)
**Source:** `/v1/results`
**Fetcher:** `results_fetcher.py`
**Updates:** ra_runners table with position data

| Column | Type | Source Field | Description |
|--------|------|--------------|-------------|
| race_id | varchar(50) | race.id | Race ID (FK) |
| runner_id | varchar(50) | runner.id | Runner ID (FK) |
| position | integer | runner.position | Finishing position |
| distance_beaten | numeric | runner.distance_beaten | Distance behind winner |
| finishing_time | varchar(20) | runner.time | Race time |
| starting_price | varchar(20) | runner.sp | SP (fractional) |
| starting_price_decimal | numeric | runner.sp_decimal | SP (decimal) |
| race_comment | text | runner.comment | Race commentary |
| ... | ... | ... | (35+ total) |

## Execution Order

### Backfill Order (Recommended)

1. **Master Tables** (reference data - can run parallel)
   - ra_mst_courses
   - ra_mst_bookmakers
   - ra_mst_jockeys
   - ra_mst_trainers
   - ra_mst_owners

2. **Races** (creates horses, pedigree, runners - run sequentially)
   - ra_races
   - ra_runners
   - ra_mst_horses (extracted)
   - ra_horse_pedigree (extracted)

3. **Results** (updates runners - run after races)
   - ra_race_results

### Daily Order (Same as backfill)

Same order but with smaller date ranges (last 3 days).

## Scheduling

### Cron Configuration (1am UK time)

```bash
# Daily sync at 1am UK time (adjust for BST/GMT)
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/daily_fetch.log 2>&1

# Weekly master table refresh (Sundays at 2am)
0 2 * * 0 cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners >> logs/weekly_fetch.log 2>&1
```

### Systemd Timer (Alternative)

Create `/etc/systemd/system/darkhorses-daily-fetch.timer`:
```ini
[Unit]
Description=DarkHorses Daily Fetch Timer

[Timer]
OnCalendar=01:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Create `/etc/systemd/system/darkhorses-daily-fetch.service`:
```ini
[Unit]
Description=DarkHorses Daily Fetch

[Service]
Type=oneshot
WorkingDirectory=/path/to/DarkHorses-Masters-Workers
ExecStart=/usr/bin/python3 fetchers/master_fetcher_controller.py --mode daily
```

Enable:
```bash
sudo systemctl enable darkhorses-daily-fetch.timer
sudo systemctl start darkhorses-daily-fetch.timer
```

## Error Handling

All fetchers implement:
- Automatic retry with exponential backoff
- Rate limiting (2 requests/second)
- Error logging
- Graceful degradation
- Transaction rollback on failure

## Monitoring

### Check Last Run

```bash
# View latest results
ls -lt logs/fetcher_*.json | head -1 | xargs cat | jq

# Check for errors
grep "ERROR" logs/daily_fetch.log | tail -20
```

### Database Verification

```bash
# Check data freshness
psql -c "SELECT table_name, MAX(updated_at) as last_update
         FROM information_schema.tables
         WHERE table_name LIKE 'ra_%'
         GROUP BY table_name;"

# Check row counts
psql -c "SELECT 'ra_races' as table, COUNT(*) FROM ra_races
         UNION ALL SELECT 'ra_runners', COUNT(*) FROM ra_runners
         UNION ALL SELECT 'ra_mst_horses', COUNT(*) FROM ra_mst_horses;"
```

## Regional Filtering

**All fetchers filter to GB & IRE only:**
- Courses: UK & Ireland
- Jockeys/Trainers/Owners: `region_codes=['gb', 'ire']`
- Races/Results: `region_codes=['gb', 'ire']`

## Performance

### Backfill (2015-present, ~10 years)

| Table | Rows | Time | Rate |
|-------|------|------|------|
| ra_mst_courses | ~100 | 30s | N/A |
| ra_mst_bookmakers | ~50 | 30s | N/A |
| ra_mst_jockeys | ~5,000 | 2m | N/A |
| ra_mst_trainers | ~3,000 | 2m | N/A |
| ra_mst_owners | ~10,000 | 3m | N/A |
| ra_races | ~150,000 | 2h | ~2,000/min |
| ra_runners | ~2,000,000 | 2h | Included |
| ra_mst_horses | ~200,000 | 2h | Included |
| ra_race_results | ~150,000 | 2h | ~2,000/min |

**Total Backfill Time:** ~6-8 hours

### Daily Sync (last 3 days)

| Table | Time |
|-------|------|
| Master tables | 5m |
| Races/Runners | 2m |
| Results | 2m |

**Total Daily Time:** ~10 minutes

## Testing

```bash
# Test daily mode
python3 fetchers/master_fetcher_controller.py --mode daily --test

# Test specific fetcher
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_races --days-back 1 --test

# Dry run (no database writes)
# Add --dry-run flag to fetchers (if implemented)
```

## Calculated Tables (Phase 2)

In addition to fetching data from Racing API, this directory includes scripts for calculating derived statistics:

### Master Script
```bash
# Run all calculated tables (daily)
python3 fetchers/populate_all_calculated_tables.py

# With custom thresholds (weekly)
python3 fetchers/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5
```

### Tables Updated by Calculations
1. **ra_entity_combinations** - Jockey-trainer partnerships
2. **ra_runner_odds** - Aggregated odds summaries
3. **ra_runner_statistics** - 60 performance metrics per runner
4. **ra_performance_by_distance** - Distance-based performance
5. **ra_performance_by_venue** - Course specialist identification

### Individual Calculation Scripts
- `populate_entity_combinations_from_runners.py` - Partnerships
- `populate_runner_odds.py` - Odds aggregation
- `populate_runner_statistics.py` - Runner metrics
- `populate_performance_by_distance.py` - Distance analysis
- `populate_performance_by_venue.py` - Venue analysis
- `populate_calculated_tables.py` - Phase 1 master
- `populate_phase2_analytics.py` - Phase 2 master
- `populate_all_calculated_tables.py` - Complete master

### Schedule Configuration
See `/fetchers/schedules/` for:
- `calculated_tables_schedule.yaml` - Complete schedule config
- `README.md` - Schedule documentation

**Recommended Schedule:**
```bash
# Add to crontab:
30 2 * * * cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1
```

---

## Documentation Files

- **This README** - Complete fetcher system overview
- **TABLE_COLUMN_MAPPING.json** - Detailed column-to-API field mapping
- **Individual fetchers** - See docstrings in each fetcher file
- **`/fetchers/docs/`** - Complete documentation library
- **`/fetchers/schedules/`** - Schedule configurations
- **`/docs/CALCULATED_TABLES_IMPLEMENTATION.md`** - Calculation implementation guide
- **`/docs/CALCULATED_TABLES_SCHEDULING.md`** - Production scheduling guide

---

**Last Updated:** 2025-10-22
**Version:** 2.1 (+ Calculated Tables)
**Status:** Production Ready
