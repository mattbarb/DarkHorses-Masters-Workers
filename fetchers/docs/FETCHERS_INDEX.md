# Fetchers Directory - Complete Index

**Location:** `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/`
**Last Updated:** 2025-10-21
**Status:** ✅ Production Ready

---

## 📁 Directory Contents

### Master Controller (⭐ START HERE)
```
master_fetcher_controller.py    - MASTER orchestrator for all fetchers
```

**Single command for everything:**
```bash
python3 fetchers/master_fetcher_controller.py --mode daily
```

### Individual Fetchers (11 files)

| File | Tables Populated | API Endpoint | Type |
|------|------------------|--------------|------|
| `courses_fetcher.py` | ra_mst_courses | /v1/courses | Bulk |
| `bookmakers_fetcher.py` | ra_mst_bookmakers | /v1/bookmakers | Bulk |
| `jockeys_fetcher.py` | ra_mst_jockeys | /v1/jockeys | Bulk |
| `trainers_fetcher.py` | ra_mst_trainers | /v1/trainers | Bulk |
| `owners_fetcher.py` | ra_mst_owners | /v1/owners | Bulk |
| `horses_fetcher.py` | ra_mst_horses | /v1/horses | Bulk |
| `races_fetcher.py` | ra_mst_races, ra_mst_runners, ra_mst_horses*, ra_horse_pedigree* | /v1/racecards/pro | Date Range |
| `results_fetcher.py` | ra_mst_race_results (updates ra_mst_runners) | /v1/results | Date Range |
| `events_fetcher.py` | (Future use) | /v1/events | - |
| `masters_fetcher.py` | (Legacy - use master_fetcher_controller.py) | - | - |
| `statistics_fetcher.py` | (Deprecated - use population_workers) | - | - |

**Note:** *extracted during races fetch

### Documentation (3 files)

| File | Description | Use Case |
|------|-------------|----------|
| `README.md` | **Complete fetcher guide** | Learn how system works |
| `TABLE_COLUMN_MAPPING.json` | **Detailed column mapping** | Reference API fields |
| `FETCHERS_INDEX.md` | **This file** | Quick navigation |

### Support Files
```
__init__.py    - Python package initialization
```

---

## 🎯 Quick Commands

### Daily Operations

```bash
# Daily sync (for 1am cron)
python3 fetchers/master_fetcher_controller.py --mode daily

# Test daily sync
python3 fetchers/master_fetcher_controller.py --mode daily --test

# List all available tables
python3 fetchers/master_fetcher_controller.py --list
```

### Initial Setup

```bash
# Backfill from 2015
python3 fetchers/master_fetcher_controller.py --mode backfill

# Backfill specific tables
python3 fetchers/master_fetcher_controller.py --mode backfill --tables ra_mst_courses ra_mst_bookmakers
```

### Manual Operations

```bash
# Fetch specific date range
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_mst_races --start-date 2024-01-01 --end-date 2024-01-31

# Fetch last 7 days
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_mst_races --days-back 7
```

---

## 📊 Tables Managed (10 Total)

### Master Tables (5)
1. **ra_mst_courses** - Racing courses (GB & IRE)
2. **ra_mst_bookmakers** - Bookmakers list
3. **ra_mst_jockeys** - Active jockeys
4. **ra_mst_trainers** - Active trainers
5. **ra_mst_owners** - Active owners

### Transaction Tables (5)
6. **ra_mst_races** - Race metadata
7. **ra_mst_runners** - Race entries/runners
8. **ra_mst_horses** - Horses (with pedigree enrichment)
9. **ra_horse_pedigree** - Horse pedigree data
10. **ra_mst_race_results** - Historical results

**Total Columns:** 300+ from Racing API

---

## 🔄 Fetcher Modes

### 1. BACKFILL Mode
**Purpose:** Initial population from 2015-01-01
**Time:** 6-8 hours
**Data:** ~10 years of historical data

```bash
python3 fetchers/master_fetcher_controller.py --mode backfill
```

### 2. DAILY Mode
**Purpose:** Daily sync at 1am UK
**Time:** ~10 minutes
**Data:** Last 3 days + current references

```bash
python3 fetchers/master_fetcher_controller.py --mode daily
```

### 3. MANUAL Mode
**Purpose:** Custom date ranges, testing
**Time:** Varies
**Data:** User-specified

```bash
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_mst_races --days-back 7
```

---

## 📖 Documentation Structure

```
fetchers/
├── FETCHERS_INDEX.md (THIS FILE)        - Quick reference
├── README.md                            - Complete guide
│   ├── All fetchers explained
│   ├── Table-to-fetcher mapping
│   ├── Column details
│   ├── Execution order
│   ├── Performance metrics
│   └── Scheduling instructions
│
├── TABLE_COLUMN_MAPPING.json           - Detailed mapping
│   ├── Every table documented
│   ├── API endpoint for each
│   ├── Column-to-field mapping
│   ├── Data types
│   └── Execution order
│
└── master_fetcher_controller.py        - The orchestrator
    ├── 3 modes (backfill/daily/manual)
    ├── Error handling
    ├── Logging
    └── JSON results
```

---

## 📚 Related Documentation

### In `/docs` directory:
- `FETCHER_SCHEDULING_GUIDE.md` - Cron/systemd setup
- `COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json` - Master inventory (625+ columns)

### In root directory:
- `FETCHER_SYSTEM_SUMMARY.md` - Complete system overview
- `COMPLETE_POPULATION_SYSTEM_SUMMARY.md` - Full integration guide
- `QUICK_START_GUIDE.md` - Quick reference

---

## 🔍 How to Find Information

### "Which fetcher populates table X?"
→ Check `TABLE_COLUMN_MAPPING.json` or run:
```bash
python3 fetchers/master_fetcher_controller.py --list
```

### "What columns come from the API?"
→ See `TABLE_COLUMN_MAPPING.json` → `tables` → `{table_name}` → `columns`

### "How do I schedule daily runs?"
→ See `README.md` → "Scheduling" section
→ Or `/docs/FETCHER_SCHEDULING_GUIDE.md`

### "What's the execution order?"
→ See `TABLE_COLUMN_MAPPING.json` → `fetcher_execution_order`

### "How do I backfill historical data?"
→ See `README.md` → "Backfill Mode"
→ Or run: `python3 fetchers/master_fetcher_controller.py --mode backfill`

---

## 🛠️ File Purposes

### Active Production Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `master_fetcher_controller.py` | **Run all fetchers** | Daily sync, backfill, manual ops |
| `courses_fetcher.py` | Fetch courses | Called by master controller |
| `bookmakers_fetcher.py` | Fetch bookmakers | Called by master controller |
| `jockeys_fetcher.py` | Fetch jockeys | Called by master controller |
| `trainers_fetcher.py` | Fetch trainers | Called by master controller |
| `owners_fetcher.py` | Fetch owners | Called by master controller |
| `races_fetcher.py` | Fetch races/runners/horses | Called by master controller |
| `results_fetcher.py` | Fetch results | Called by master controller |

### Documentation Files

| File | Purpose | When to Read |
|------|---------|--------------|
| `README.md` | Complete guide | Learning the system |
| `TABLE_COLUMN_MAPPING.json` | Column details | Looking up API fields |
| `FETCHERS_INDEX.md` | This file | Quick navigation |

### Legacy/Deprecated Files

| File | Status | Notes |
|------|--------|-------|
| `horses_fetcher.py` | Legacy | Use races_fetcher.py instead (hybrid enrichment) |
| `masters_fetcher.py` | Deprecated | Use master_fetcher_controller.py |
| `statistics_fetcher.py` | Deprecated | Use scripts/population_workers/ |
| `events_fetcher.py` | Future | Not currently used |

---

## 🎯 Common Tasks

### Check What Tables Are Available
```bash
python3 fetchers/master_fetcher_controller.py --list
```

### Run Daily Sync
```bash
python3 fetchers/master_fetcher_controller.py --mode daily
```

### Initial Setup (First Time)
```bash
# 1. Backfill all data
python3 fetchers/master_fetcher_controller.py --mode backfill

# 2. Schedule daily sync
crontab -e
# Add: 0 1 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1
```

### Test Before Scheduling
```bash
# Test with limited data
python3 fetchers/master_fetcher_controller.py --mode daily --test
```

### Fetch Specific Date Range
```bash
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_mst_races --start-date 2024-01-01 --end-date 2024-01-31
```

---

## 📊 Complete Data Flow (All 23 Tables)

### Phase 1: Racing API Fetchers → Database (10 tables)

```
Racing API
    ↓
master_fetcher_controller.py (orchestrator)
    ↓
Individual Fetchers (8 fetcher scripts)
    │
    ├── courses_fetcher.py
    │   └── ra_mst_courses (101 courses)
    │
    ├── bookmakers_fetcher.py
    │   └── ra_mst_bookmakers (22 bookmakers)
    │
    ├── jockeys_fetcher.py
    │   └── ra_mst_jockeys (3,483 active jockeys)
    │
    ├── trainers_fetcher.py
    │   └── ra_mst_trainers (2,781 active trainers)
    │
    ├── owners_fetcher.py
    │   └── ra_mst_owners (48,168 active owners)
    │
    ├── races_fetcher.py (also extracts from racecards)
    │   ├── ra_mst_races (~850,000 races)
    │   ├── ra_mst_runners (~12M race entries)
    │   ├── ra_mst_horses (111,669 horses with hybrid enrichment)
    │   ├── ra_horse_pedigree (~90,000 pedigree records)
    │   └── ra_mst_regions (2 regions: GB, IRE - extracted from courses)
    │
    └── results_fetcher.py
        └── ra_mst_race_results (~850,000 results - updates ra_mst_runners)
```

**Tables Populated from Racing API: 10**
- Master/Reference: `ra_mst_courses`, `ra_mst_bookmakers`, `ra_mst_regions`, `ra_mst_jockeys`, `ra_mst_trainers`, `ra_mst_owners`
- Horses/Pedigree: `ra_mst_horses`, `ra_horse_pedigree`
- Transaction: `ra_mst_races`, `ra_mst_runners`, `ra_mst_race_results`

---

### Phase 2: Database Calculations → Statistics Tables (3 tables)

```
Database (10 tables with Racing API data)
    ├── ra_mst_horses (with sire_id, dam_id, damsire_id)
    ├── ra_mst_runners (with race results)
    └── ra_mst_races (with race metadata)
    ↓
Population Workers
    └── scripts/populate_pedigree_statistics.py
    ↓
Statistics Tables (calculated from progeny performance)
    ├── ra_mst_sires (2,143 sires - 47 calculated columns)
    ├── ra_mst_dams (48,372 dams - 47 calculated columns)
    └── ra_mst_damsires (3,041 damsires - 47 calculated columns)
```

**Tables Calculated from Database: 3**
- `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires`

---

### Phase 3: Future/External Data Sources (10 tables - TBD)

```
External Data Sources
    ↓
Future Workers/Fetchers (to be implemented)
    ↓
Additional Tables (planned/partial)
    ├── ra_entity_combinations (entity pattern tracking)
    ├── ra_performance_by_distance (distance performance aggregates)
    ├── ra_performance_by_venue (venue performance aggregates)
    ├── ra_runner_statistics (individual runner stats)
    ├── ra_runner_supplementary (additional runner metadata)
    ├── ra_odds_live (live betting odds - requires odds provider)
    ├── ra_odds_historical (historical odds - requires odds provider)
    ├── ra_odds_statistics (odds aggregates - calculated from odds)
    ├── ra_runner_odds (runner-specific odds - requires odds provider)
    └── [Additional tables as needed]
```

**Tables Not Yet Implemented: 10**
- Performance Metrics: `ra_performance_by_distance`, `ra_performance_by_venue`, `ra_runner_statistics`, `ra_runner_supplementary`
- Odds (require external provider): `ra_odds_live`, `ra_odds_historical`, `ra_odds_statistics`, `ra_runner_odds`
- Tracking: `ra_entity_combinations`

---

## 📈 Complete Table Inventory (23 Tables Total)

### ✅ Fully Populated (13 tables)

**From Racing API (10 tables):**
1. `ra_mst_courses` - Courses/venues (101)
2. `ra_mst_bookmakers` - Bookmakers (22)
3. `ra_mst_regions` - Region codes (2: GB, IRE)
4. `ra_mst_jockeys` - Active jockeys (3,483)
5. `ra_mst_trainers` - Active trainers (2,781)
6. `ra_mst_owners` - Active owners (48,168)
7. `ra_mst_horses` - Horses with pedigree (111,669)
8. `ra_horse_pedigree` - Horse lineage (~90,000)
9. `ra_mst_races` - Race metadata (~850,000)
10. `ra_mst_runners` - Race entries (~12M)

**Calculated from Database (3 tables):**
11. `ra_mst_sires` - Sire statistics (2,143)
12. `ra_mst_dams` - Dam statistics (48,372)
13. `ra_mst_damsires` - Damsire statistics (3,041)

### ⏳ Partially Implemented / TBD (10 tables)

**Performance Metrics (4 tables):**
14. `ra_performance_by_distance` - Distance performance aggregates
15. `ra_performance_by_venue` - Venue performance aggregates
16. `ra_runner_statistics` - Individual runner statistics
17. `ra_runner_supplementary` - Additional runner metadata

**Odds Data - Requires External Provider (4 tables):**
18. `ra_odds_live` - Live betting odds
19. `ra_odds_historical` - Historical betting odds
20. `ra_odds_statistics` - Odds aggregates/trends
21. `ra_runner_odds` - Runner-specific odds

**Tracking/Analysis (2 tables):**
22. `ra_entity_combinations` - Entity combination patterns
23. `ra_mst_race_results` - Historical results table (~850,000)

**Note:** Racing API does NOT provide odds data - requires separate odds provider.

---

## 🎯 Summary: What Populates What

**Phase 1 - Racing API Fetchers:**
- `master_fetcher_controller.py` orchestrates 8 individual fetchers
- Populates 10 tables directly from Racing API
- Duration: 6-8 hours (backfill), ~10 minutes (daily)

**Phase 2 - Database Calculations:**
- `scripts/populate_pedigree_statistics.py` calculates statistics
- Populates 3 statistics tables from existing data
- Duration: 30-60 minutes (full calculation)

**Phase 3 - Future Implementation:**
- 10 tables planned or partially implemented
- Requires external data sources (odds) or additional workers
- Status: TBD

---

## ⚙️ Configuration

All fetchers use:
- **Config:** `config/config.py`
- **Environment:** `.env.local`
- **API Client:** `utils/api_client.py`
- **DB Client:** `utils/supabase_client.py`

Required environment variables:
```bash
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

---

## 📝 Logs

All fetchers log to:
- **Console:** Real-time progress
- **JSON Results:** `logs/fetcher_{mode}_{timestamp}.json`
- **Cron Logs:** `logs/cron_daily.log` (if scheduled)

View latest results:
```bash
ls -lt logs/fetcher_*.json | head -1 | xargs cat | jq
```

---

## ✅ Quick Checklist

**Daily Operations:**
- [ ] Fetcher runs at 1am UK (cron)
- [ ] Logs are being created
- [ ] No errors in logs
- [ ] Data is up to date

**First Time Setup:**
- [ ] Environment variables configured
- [ ] Backfill completed
- [ ] Daily cron scheduled
- [ ] Logs directory exists
- [ ] Database access verified

**Maintenance:**
- [ ] Review logs weekly
- [ ] Check data freshness
- [ ] Monitor disk space (logs)
- [ ] Update documentation as needed

---

## 🚀 Next Steps

1. **Read:** `README.md` for complete understanding
2. **Test:** `python3 fetchers/master_fetcher_controller.py --mode daily --test`
3. **Backfill:** `python3 fetchers/master_fetcher_controller.py --mode backfill` (if first time)
4. **Schedule:** Add cron job for daily sync
5. **Monitor:** Check logs regularly

---

**Need Help?**
- **Quick Reference:** This file (FETCHERS_INDEX.md)
- **Complete Guide:** README.md
- **Column Details:** TABLE_COLUMN_MAPPING.json
- **Scheduling:** /docs/FETCHER_SCHEDULING_GUIDE.md
- **System Overview:** /FETCHER_SYSTEM_SUMMARY.md

**Status:** ✅ All fetchers operational and documented
**Location:** `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/`
