# Complete 18 Tables Sync Schedule

**Date:** 2025-10-23
**Purpose:** Comprehensive schedule for all 18 database tables with UK-time synchronization

---

## 📊 All 18 Tables Coverage

### Master/Reference Tables (10)
1. ✅ `ra_mst_bookmakers` - Bookmaker reference data
2. ✅ `ra_mst_courses` - Course/venue reference data
3. ✅ `ra_mst_dams` - Dam (mother horse) pedigree data
4. ✅ `ra_mst_damsires` - Damsire (mother's father) pedigree data
5. ✅ `ra_mst_horses` - Horse master data with enrichment
6. ✅ `ra_mst_jockeys` - Jockey reference data
7. ✅ `ra_mst_owners` - Owner reference data
8. ✅ `ra_mst_regions` - Region codes (GB, IRE, etc.)
9. ✅ `ra_mst_sires` - Sire (father horse) pedigree data
10. ✅ `ra_mst_trainers` - Trainer reference data

### Transaction Tables (4)
11. ✅ `ra_races` - Race metadata and details
12. ✅ `ra_mst_runners` - Runner entries in races
13. ✅ `ra_mst_race_results` - Historical race results
14. ✅ `ra_horse_pedigree` - Complete horse pedigree (enrichment)

### Statistics/Analytics Tables (4)
15. ✅ `ra_entity_combinations` - Performance by entity combos
16. ✅ `ra_performance_by_distance` - Distance-based performance
17. ✅ `ra_performance_by_venue` - Venue specialist identification
18. ✅ `ra_runner_statistics` - Comprehensive runner metrics

---

## 🕐 Sync Schedule (UK Time)

### 13:00 (1:00 PM) - Master Table Sync
**Frequency:** Daily
**Tables:** All 10 master/reference tables
**Script:** `master_fetcher_controller.py --mode daily`
**Rationale:** Static reference data changes infrequently

```bash
# Cron: Daily at 1:00 PM UK time
0 13 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_bookmakers ra_mst_courses ra_mst_dams ra_mst_damsires ra_mst_horses ra_mst_jockeys ra_mst_owners ra_mst_regions ra_mst_sires ra_mst_trainers >> logs/cron_master_tables.log 2>&1
```

**What syncs:**
1. `ra_mst_courses` - Monthly (1st of month) - RARELY CHANGES
2. `ra_mst_bookmakers` - Monthly (1st of month) - RARELY CHANGES
3. `ra_mst_jockeys` - Weekly (Sunday) - CHANGES OCCASIONALLY
4. `ra_mst_trainers` - Weekly (Sunday) - CHANGES OCCASIONALLY
5. `ra_mst_owners` - Weekly (Sunday) - CHANGES OCCASIONALLY
6. `ra_mst_horses` - Daily (with enrichment) - NEW HORSES DAILY
7. `ra_mst_regions` - Quarterly - STATIC
8. `ra_mst_sires` - Extracted from runners (automatic)
9. `ra_mst_dams` - Extracted from runners (automatic)
10. `ra_mst_damsires` - Extracted from runners (automatic)

---

### Multiple Times Daily - Transaction Tables
**Frequency:** Every 4 hours (to catch race updates)
**Tables:** Races, runners, results, pedigree
**Script:** `master_fetcher_controller.py --mode daily`

```bash
# Cron: Every 4 hours starting at 6:00 AM UK time
0 6,10,14,18,22 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_races ra_mst_runners ra_mst_race_results ra_horse_pedigree >> logs/cron_transactions.log 2>&1
```

**What syncs:**
1. `ra_races` - Racecards for upcoming races
2. `ra_mst_runners` - Runner entries for races
3. `ra_mst_race_results` - Results as races complete
4. `ra_horse_pedigree` - Pedigree for new horses (enrichment)

**Schedule breakdown:**
- **06:00** - Morning update (catch overnight results)
- **10:00** - Mid-morning (catch morning race cards)
- **14:00 (2:00 PM)** - Afternoon (prime UK racing time)
- **18:00 (6:00 PM)** - Evening (catch day's results)
- **22:00 (10:00 PM)** - Night (catch evening racing, Irish meetings)

---

### 02:30 AM - Statistics Tables (Calculated)
**Frequency:** Daily
**Tables:** All 4 statistics/analytics tables
**Script:** `populate_all_calculated_tables.py`

```bash
# Cron: Daily at 2:30 AM UK time
30 2 * * * cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1
```

**What calculates:**
1. `ra_entity_combinations` - Jockey-trainer partnerships
2. `ra_performance_by_distance` - Distance specialists
3. `ra_performance_by_venue` - Course specialists
4. `ra_runner_statistics` - 60 performance metrics per runner

**Runtime:** 15-25 minutes

---

### 03:30 AM Sunday - Weekly Full Recalculation
**Frequency:** Weekly (Sunday)
**Tables:** Same 4 statistics tables (with stricter thresholds)
**Script:** `populate_all_calculated_tables.py` (with quality filters)

```bash
# Cron: Sunday at 3:30 AM UK time
30 3 * * 0 cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10 >> logs/cron_calculated_weekly.log 2>&1
```

**Purpose:** Higher quality thresholds = better statistics accuracy

---

## 📋 Complete Schedule Table

| Table | Frequency | UK Time | Script | Notes |
|-------|-----------|---------|--------|-------|
| **ra_mst_bookmakers** | Monthly | 13:00 (1st) | master_fetcher | Static data |
| **ra_mst_courses** | Monthly | 13:00 (1st) | master_fetcher | Static data |
| **ra_mst_regions** | Quarterly | 13:00 (1st) | master_fetcher | Static data |
| **ra_mst_jockeys** | Weekly | 13:00 (Sun) | master_fetcher | People data |
| **ra_mst_trainers** | Weekly | 13:00 (Sun) | master_fetcher | People data |
| **ra_mst_owners** | Weekly | 13:00 (Sun) | master_fetcher | People data |
| **ra_mst_horses** | Daily | 6,10,14,18,22 | master_fetcher | With enrichment |
| **ra_mst_sires** | Automatic | - | entity_extractor | From runners |
| **ra_mst_dams** | Automatic | - | entity_extractor | From runners |
| **ra_mst_damsires** | Automatic | - | entity_extractor | From runners |
| **ra_races** | Every 4h | 6,10,14,18,22 | races_fetcher | Racecards |
| **ra_mst_runners** | Every 4h | 6,10,14,18,22 | races_fetcher | Runner entries |
| **ra_mst_race_results** | Every 4h | 6,10,14,18,22 | results_fetcher | Race results |
| **ra_horse_pedigree** | Every 4h | 6,10,14,18,22 | entity_extractor | Enrichment |
| **ra_entity_combinations** | Daily | 02:30 | calculated_tables | Statistics |
| **ra_performance_by_distance** | Daily | 02:30 | calculated_tables | Statistics |
| **ra_performance_by_venue** | Daily | 02:30 | calculated_tables | Statistics |
| **ra_runner_statistics** | Daily | 02:30 | calculated_tables | Statistics |

---

## 🚀 Recommended Cron Setup

### Option 1: Simple (3 Cron Jobs)

```bash
# 1. Transaction tables (every 4 hours)
0 6,10,14,18,22 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_transactions.log 2>&1

# 2. Master tables (daily at 1pm)
0 13 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1

# 3. Calculated tables (daily at 2:30am)
30 2 * * * cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1
```

---

### Option 2: Comprehensive (6 Cron Jobs)

```bash
# 1. Transaction tables (races, runners, results) - Every 4 hours
0 6,10,14,18,22 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_races ra_mst_runners ra_mst_race_results ra_horse_pedigree >> logs/cron_transactions.log 2>&1

# 2. Static master tables (courses, bookmakers) - Monthly 1st at 1pm
0 13 1 * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses ra_mst_bookmakers ra_mst_regions >> logs/cron_static.log 2>&1

# 3. People master tables (jockeys, trainers, owners) - Weekly Sunday at 1pm
0 13 * * 0 cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners >> logs/cron_people.log 2>&1

# 4. Horse master table (with enrichment) - Daily at 1pm
0 13 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_horses >> logs/cron_horses.log 2>&1

# 5. Calculated tables - Daily at 2:30am
30 2 * * * cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1

# 6. Calculated tables (high quality) - Weekly Sunday at 3:30am
30 3 * * 0 cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10 >> logs/cron_calculated_weekly.log 2>&1
```

---

## 📊 Data Flow

```
06:00 - Morning Transaction Sync
    ├── Fetch overnight results
    ├── Fetch morning racecards
    └── Extract new entities (horses, jockeys, etc.)

10:00 - Mid-Morning Sync
    ├── Fetch updated racecards
    └── Catch new runner entries

13:00 - Master Tables Sync (1:00 PM)
    ├── Monthly: Courses, Bookmakers, Regions
    ├── Weekly: Jockeys, Trainers, Owners
    └── Daily: Horses (with enrichment)

14:00 - Afternoon Racing Sync (2:00 PM)
    ├── Fetch active race cards
    ├── Fetch live updates
    └── Peak UK racing time

18:00 - Evening Results Sync (6:00 PM)
    ├── Fetch day's results
    └── Update runner positions/times

22:00 - Night Sync (10:00 PM)
    ├── Fetch evening race results
    ├── Catch Irish evening meetings
    └── Final daily update

02:30 - Statistics Calculation
    ├── Clear statistics tables
    ├── Recalculate from source data
    └── 15-25 minute runtime
```

---

## ⚠️ Important Notes

### 1. Entity Extraction is Automatic
**Tables auto-populated from runners:**
- `ra_mst_sires`
- `ra_mst_dams`
- `ra_mst_damsires`

These are extracted automatically when races/runners sync via `entity_extractor.py`. No separate schedule needed!

### 2. Enrichment Happens On-The-Fly
**Table populated during sync:**
- `ra_horse_pedigree`

When new horses are discovered in races, the enrichment happens automatically via `/v1/horses/{id}/pro` API endpoint.

### 3. Statistics are Derived
**Tables calculated from source data:**
- `ra_entity_combinations`
- `ra_performance_by_distance`
- `ra_performance_by_venue`
- `ra_runner_statistics`

These are NEVER fetched from API - they're calculated daily from `ra_mst_race_results`.

### 4. Regions are Static
**Table rarely changes:**
- `ra_mst_regions`

Only needs quarterly update or when new racing jurisdictions are added.

---

## 🔍 Monitoring

### Check What's Running
```bash
# View cron jobs
crontab -l

# Check process
ps aux | grep master_fetcher

# Check logs
tail -f logs/cron_transactions.log
tail -f logs/cron_calculated_tables.log
```

### Verify Last Update Times
```sql
-- Check last update per table
SELECT 'ra_races' as table_name, MAX(updated_at) as last_update, COUNT(*) as records FROM ra_races
UNION ALL
SELECT 'ra_mst_jockeys', MAX(updated_at), COUNT(*) FROM ra_mst_jockeys
UNION ALL
SELECT 'ra_entity_combinations', MAX(created_at), COUNT(*) FROM ra_entity_combinations;
```

### Check for Missed Syncs
```bash
# Find errors in logs
grep -i "error\|failed" logs/cron_*.log

# Check if cron ran
grep "CRON" /var/log/syslog  # Linux
grep "cron" /var/log/system.log  # macOS
```

---

## 🎯 Quick Start

### 1. Install Cron Jobs
```bash
# Edit crontab
crontab -e

# Add Option 1 (Simple - 3 jobs) or Option 2 (Comprehensive - 6 jobs)
```

### 2. Verify Setup
```bash
# Test transaction sync manually
python3 fetchers/master_fetcher_controller.py --mode daily --interactive

# Test calculated tables manually
python3 fetchers/populate_all_calculated_tables.py
```

### 3. Monitor First Week
```bash
# Check logs daily for first week
tail -100 logs/cron_*.log

# Verify data is updating
# (Use SQL queries above)
```

---

## 📚 Related Documentation

- `fetchers/schedules/README.md` - Schedule overview
- `fetchers/schedules/calculated_tables_schedule.yaml` - Detailed config
- `fetchers/master_fetcher_controller.py` - Main controller script
- `fetchers/populate_all_calculated_tables.py` - Statistics calculator
- `docs/COMPLETE_COVERAGE_AND_STATISTICS_GUIDE.md` - Coverage reference

---

## ✅ Coverage Confirmation

**ALL 18 TABLES HAVE SCHEDULES:**
- ✅ 10 Master tables (monthly/weekly/daily/automatic)
- ✅ 4 Transaction tables (every 4 hours)
- ✅ 4 Statistics tables (daily calculation)

**No table is left behind!**

---

**Last Updated:** 2025-10-23
**Timezone:** All times are UK (Europe/London)
**Status:** ✅ Complete coverage for all 18 tables
