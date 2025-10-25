# Data Source Strategy - DEFINITIVE GUIDE

**Date:** 2025-10-21
**Purpose:** Define what data comes from Racing API vs database calculations
**Status:** ✅ CANONICAL REFERENCE

---

## Core Principle

**ALWAYS get data from Racing API FIRST, then calculate statistics from database.**

---

## Table-by-Table Data Source Map

### 1. Racing API Data (PRIMARY SOURCE)

These tables get ALL their data from The Racing API:

#### Master/Reference Tables (Bulk Fetchers)
| Table | API Endpoint | Fetcher Script | Data Type |
|-------|--------------|----------------|-----------|
| `ra_mst_courses` | `/v1/courses` | `courses_fetcher.py` | Course/venue reference |
| `ra_mst_bookmakers` | `/v1/bookmakers` | `bookmakers_fetcher.py` | Bookmaker list |
| `ra_mst_jockeys` | `/v1/jockeys` | `jockeys_fetcher.py` | Active jockeys |
| `ra_mst_trainers` | `/v1/trainers` | `trainers_fetcher.py` | Active trainers |
| `ra_mst_owners` | `/v1/owners` | `owners_fetcher.py` | Active owners |
| `ra_mst_regions` | `/v1/courses` (extracted) | `courses_fetcher.py` | Region codes |

#### Transaction Tables (Date Range Fetchers)
| Table | API Endpoint | Fetcher Script | Data Type |
|-------|--------------|----------------|-----------|
| `ra_races` | `/v1/racecards/pro` | `races_fetcher.py` | Race metadata |
| `ra_runners` | `/v1/racecards/pro` | `races_fetcher.py` | Race entries/runners |
| `ra_race_results` | `/v1/results` | `results_fetcher.py` | Historical results |

#### Enriched Tables (Hybrid: API + Enrichment)
| Table | Primary API | Enrichment API | Fetcher Script | Data Type |
|-------|-------------|----------------|----------------|-----------|
| `ra_mst_horses` | `/v1/racecards/pro` (discovery) | `/v1/horses/{id}/pro` (NEW horses only) | `races_fetcher.py` | Horse data with pedigree |
| `ra_horse_pedigree` | N/A | `/v1/horses/{id}/pro` (during enrichment) | `races_fetcher.py` | Lineage data |

**IMPORTANT:** Only NEW horses discovered in racecards are enriched with Pro endpoint.

---

### 2. Database Calculated Data (SECONDARY SOURCE)

These tables are calculated FROM existing Racing API data:

#### Pedigree Statistics (Calculated from Progeny Performance)
| Table | Data Source | Calculation Script | Calculation Type |
|-------|-------------|-------------------|------------------|
| `ra_mst_sires` | `ra_runners` + `ra_races` + `ra_mst_horses` | `scripts/populate_pedigree_statistics.py` | Aggregate progeny stats |
| `ra_mst_dams` | `ra_runners` + `ra_races` + `ra_mst_horses` | `scripts/populate_pedigree_statistics.py` | Aggregate progeny stats |
| `ra_mst_damsires` | `ra_runners` + `ra_races` + `ra_mst_horses` | `scripts/populate_pedigree_statistics.py` | Aggregate grandprogeny stats |

**Columns Calculated (47 per table):**
- Total runners, wins, places
- Win percentages
- Performance by class (1-7)
- Performance by distance
- AE (Actual vs Expected) index
- Quality score
- Best performing classes/distances

#### Performance Metrics (Calculated from Race Results)
| Table | Data Source | Calculation Script | Calculation Type |
|-------|-------------|-------------------|------------------|
| `ra_performance_by_distance` | `ra_runners` + `ra_races` | TBD | Distance performance aggregates |
| `ra_performance_by_venue` | `ra_runners` + `ra_races` | TBD | Venue performance aggregates |
| `ra_runner_statistics` | `ra_runners` + `ra_races` | TBD | Individual runner stats |

#### Supplementary Tables
| Table | Data Source | Population Method | Data Type |
|-------|-------------|-------------------|-----------|
| `ra_runner_supplementary` | `ra_runners` (extracted) | Direct extraction | Additional runner metadata |
| `ra_entity_combinations` | `ra_runners` (patterns) | Pattern analysis | Entity combination tracking |

---

### 3. External Data (TERTIARY SOURCE)

These tables get data from external sources (NOT Racing API):

| Table | Data Source | Population Method | Purpose |
|-------|-------------|-------------------|---------|
| `ra_odds_live` | Live Odds API/Service | TBD | Real-time betting odds |
| `ra_odds_historical` | Historical Odds API/Service | TBD | Historical betting odds |
| `ra_odds_statistics` | `ra_odds_*` tables | Calculation | Odds aggregates/trends |
| `ra_runner_odds` | Odds API/Service | TBD | Runner-specific odds |

**Note:** Odds data is NOT available from Racing API - requires separate odds provider.

---

## Data Flow Architecture

### Phase 1: Racing API Data Collection (FIRST)

```
Racing API
    ↓
Master Fetcher Controller
    ↓
Individual Fetchers
    ├── Bulk Fetchers (courses, bookmakers, people)
    ├── Date Range Fetchers (races, runners, results)
    └── Hybrid Enrichment (horses with pedigree)
    ↓
Database (ra_* tables populated)
```

**Script:** `fetchers/master_fetcher_controller.py`
**Modes:** backfill, daily, scheduled
**Duration:**
- Backfill: 6-8 hours (2015-present)
- Daily: ~10 minutes (last 3 days)

### Phase 2: Database Calculations (SECOND)

```
Database (ra_* tables with API data)
    ↓
Population Workers
    ├── Pedigree Statistics Worker (sires/dams/damsires)
    ├── Performance Metrics Workers (TBD)
    └── Supplementary Data Extractors (TBD)
    ↓
Statistics Tables Populated
```

**Script:** `scripts/populate_pedigree_statistics.py` (currently implemented)
**Duration:** ~30-60 minutes (53,556 entities)

### Phase 3: External Data Integration (THIRD)

```
External Odds Provider
    ↓
Odds Fetchers (TBD)
    ↓
Odds Tables Populated
```

**Status:** Not yet implemented

---

## Correct Execution Order

### Initial Setup (First Time)

```bash
# Step 1: Backfill ALL Racing API data (MUST DO FIRST)
python3 fetchers/master_fetcher_controller.py --mode backfill

# Step 2: Calculate pedigree statistics from collected data
python3 scripts/populate_pedigree_statistics.py

# Step 3: Schedule automated updates
crontab -e
# Add: 0 1 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily
# Add: 0 4 * * 0 cd /path/to/project && python3 scripts/populate_pedigree_statistics.py
```

### Daily Operations (Automated)

```bash
# 1am UK: Fetch latest Racing API data
python3 fetchers/master_fetcher_controller.py --mode daily

# 4am UK (Sunday): Recalculate statistics
python3 scripts/populate_pedigree_statistics.py
```

---

## Common Misconceptions to AVOID

### ❌ WRONG: "Get statistics from Racing API"
**Reality:** Racing API does NOT provide aggregate statistics. We must calculate them.

### ❌ WRONG: "Calculate statistics before fetching data"
**Reality:** You MUST fetch Race API data FIRST. Statistics are calculated FROM that data.

### ❌ WRONG: "Horses table populated from /v1/horses endpoint"
**Reality:** Horses are discovered from racecards, then enriched individually for NEW horses only.

### ❌ WRONG: "Odds data comes from Racing API"
**Reality:** Racing API does NOT provide odds. Requires separate odds provider.

### ❌ WRONG: "All data should be fetched together"
**Reality:** Two-phase approach: (1) Racing API fetch, (2) Database calculations

---

## What Data is Available from Racing API

### ✅ Available (Use Racing API)

**Master/Reference Data:**
- Courses (venues)
- Bookmakers
- Jockeys (active)
- Trainers (active)
- Owners (active)
- Horses (individual profile via Pro endpoint)

**Transaction Data:**
- Racecards (upcoming/past races)
- Race metadata (date, time, class, distance, going, etc.)
- Runners (horse entries with jockey, trainer, weight, etc.)
- Results (finishing positions, times, distances beaten)

**Enrichment Data (Pro endpoints):**
- Horse pedigree (sire, dam, damsire, breeder)
- Horse metadata (DOB, sex, colour, region)

### ❌ NOT Available (Must Calculate or Get Elsewhere)

**Aggregate Statistics:**
- Sire/dam/damsire performance stats (calculate from progeny)
- Trainer/jockey/owner performance stats by class/distance
- Venue-specific performance metrics
- Distance-specific performance trends

**Odds Data:**
- Live odds
- Historical odds
- Odds movements
- Market information

**Derived Metrics:**
- AE indices
- Quality scores
- Performance ratings
- Trend analysis

---

## Table Population Status

### ✅ Fully Implemented

| Table | Method | Status |
|-------|--------|--------|
| `ra_mst_courses` | Racing API | ✅ Production |
| `ra_mst_bookmakers` | Racing API | ✅ Production |
| `ra_mst_jockeys` | Racing API | ✅ Production |
| `ra_mst_trainers` | Racing API | ✅ Production |
| `ra_mst_owners` | Racing API | ✅ Production |
| `ra_mst_horses` | Racing API (hybrid) | ✅ Production |
| `ra_horse_pedigree` | Racing API (enrichment) | ✅ Production |
| `ra_races` | Racing API | ✅ Production |
| `ra_runners` | Racing API | ✅ Production |
| `ra_race_results` | Racing API | ✅ Production |
| `ra_mst_regions` | Extracted from courses | ✅ Production |
| `ra_mst_sires` | Database calculation | ✅ Production |
| `ra_mst_dams` | Database calculation | ✅ Production |
| `ra_mst_damsires` | Database calculation | ✅ Production |

### 🟡 Partially Implemented / TBD

| Table | Method | Status |
|-------|--------|--------|
| `ra_performance_by_distance` | Database calculation | ⏳ TBD |
| `ra_performance_by_venue` | Database calculation | ⏳ TBD |
| `ra_runner_statistics` | Database calculation | ⏳ TBD |
| `ra_runner_supplementary` | Extracted from runners | ⏳ TBD |
| `ra_entity_combinations` | Pattern analysis | ⏳ TBD |

### ⚠️ Requires External Source

| Table | Method | Status |
|-------|--------|--------|
| `ra_odds_live` | External API | ⚠️ Need odds provider |
| `ra_odds_historical` | External API | ⚠️ Need odds provider |
| `ra_odds_statistics` | Calculation from odds | ⚠️ Need odds provider |
| `ra_runner_odds` | External API | ⚠️ Need odds provider |

---

## Key Takeaways

1. **Racing API is PRIMARY** - Always fetch from Racing API first
2. **Statistics are CALCULATED** - Never expect statistics from Racing API
3. **Two-Phase Approach** - (1) API fetch, (2) Database calculations
4. **Hybrid Enrichment** - Horses discovered in racecards, enriched individually for NEW horses
5. **Odds Separate** - Racing API does NOT provide odds data
6. **Correct Order Matters** - Can't calculate statistics before having the base data

---

## References

**Fetcher Documentation:**
- `/fetchers/README.md` - Complete fetcher guide
- `/fetchers/TABLE_TO_SCRIPT_MAPPING.md` - Table-to-script reference
- `/fetchers/CONTROLLER_QUICK_START.md` - Controller usage guide

**Calculation Documentation:**
- `/docs/COMPLETE_DATA_FILLING_SUMMARY.md` - Statistics population guide
- `/scripts/populate_pedigree_statistics.py` - Pedigree calculator

**API Documentation:**
- `/docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md` - API endpoint testing
- `/docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json` - Master column inventory

---

**Version:** 1.0
**Status:** ✅ CANONICAL - This is the definitive data source strategy
**Last Updated:** 2025-10-21
