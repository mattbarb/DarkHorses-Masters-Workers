# Complete Data Strategy: 2015 to Current + Ongoing Sync

**Date:** 2025-10-23
**Purpose:** Master strategy for achieving complete historical data from 2015-01-01 and maintaining current data with scheduled syncs

---

## 🎯 Objective

**Ensure we have ALL racing data from January 1, 2015 onwards and keep it continuously updated.**

This requires a two-phase approach:
1. **Phase 1:** Historical backfill (one-time operation)
2. **Phase 2:** Scheduled ongoing sync (continuous operations)

---

## 📊 Current State

Based on system analysis, we have:

| Component | Status |
|-----------|--------|
| **Backfill scripts** | ✅ Production-ready (`scripts/backfill/`) |
| **Sync schedules** | ✅ Documented (`COMPLETE_18_TABLES_SCHEDULE.md`) |
| **Master controller** | ✅ Built-in (`master_fetcher_controller.py`) |
| **API coverage** | ✅ Pro plan with historical data from 2015+ |

---

## 🔄 Phase 1: Historical Backfill (One-Time)

### What Needs Backfilling?

**Master Tables (Reference Data):**
- `ra_mst_courses` - ✅ Already complete (static data)
- `ra_mst_bookmakers` - ✅ Already complete (static data)
- `ra_mst_regions` - ✅ Already complete (static data)
- `ra_mst_jockeys` - ⚠️ Current active jockeys only
- `ra_mst_trainers` - ⚠️ Current active trainers only
- `ra_mst_owners` - ⚠️ Current active owners only
- `ra_mst_horses` - ⚠️ Needs all horses from 2015+ races
- `ra_mst_sires` - ✅ Auto-extracted from runners
- `ra_mst_dams` - ✅ Auto-extracted from runners
- `ra_mst_damsires` - ✅ Auto-extracted from runners

**Transaction Tables (Historical Data):**
- `ra_races` - ⚠️ Need all races 2015-01-01 to present
- `ra_runners` - ⚠️ **CRITICAL GAP** - Need all runners 2015-2024
- `ra_race_results` - ⚠️ Need all results 2015-01-01 to present
- `ra_horse_pedigree` - ⚠️ Need all pedigrees for historical horses

**Statistics Tables:**
- `ra_entity_combinations` - ℹ️ Calculated after backfill completes
- `ra_performance_by_distance` - ℹ️ Calculated after backfill completes
- `ra_performance_by_venue` - ℹ️ Calculated after backfill completes
- `ra_runner_statistics` - ℹ️ Calculated after backfill completes

---

### Backfill Strategy: Two-Step Process

#### Step 1: Races & Runners Backfill (CRITICAL)

**What:** Fetch all racecards from 2015-01-01 to present
**Why:** This populates races AND fills the critical runner data gap
**Script:** `master_fetcher_controller.py --mode backfill`

```bash
# Full backfill from 2015 (interactive with progress)
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

# OR non-interactive for background execution
nohup python3 fetchers/master_fetcher_controller.py --mode backfill > logs/backfill_2015_full.log 2>&1 &
```

**What this does:**
1. Fetches all racecards from `/v1/racecards/pro` (2015-01-01 to today)
2. Stores race metadata → `ra_races`
3. Stores runner entries → `ra_runners` (fills the gap!)
4. Extracts entities:
   - Jockeys → `ra_mst_jockeys`
   - Trainers → `ra_mst_trainers`
   - Owners → `ra_mst_owners`
   - Horses → `ra_mst_horses`
5. Auto-enriches new horses:
   - Fetches `/v1/horses/{id}/pro` for complete metadata
   - Stores pedigree → `ra_horse_pedigree`
   - Extracts pedigree entities → `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires`

**Estimated Time:** 20-24 hours (for ~3,900 days from 2015)
**API Calls:** ~145,000 total (within Pro plan limits)
**Storage:** ~1.5 GB additional data

**Features:**
- ✅ Checkpoint-based resume (can restart if interrupted)
- ✅ Rate-limited (2 req/sec to respect API limits)
- ✅ UPSERT-safe (no duplicates if re-run)
- ✅ Progress tracking with ETA
- ✅ Error logging and recovery

#### Step 2: Results Backfill

**What:** Fetch all race results from 2015-01-01 to present
**Why:** Updates runner positions, times, and outcomes
**Script:** Same controller, results fetcher

```bash
# Backfill results (can run concurrently with Step 1 or after)
python3 fetchers/master_fetcher_controller.py --mode backfill --tables ra_race_results --interactive
```

**What this does:**
1. Fetches all results from `/v1/results/pro` (2015-01-01 to today)
2. Updates `ra_runners` with finishing positions, times, SP
3. Updates `ra_race_results` with complete result data

**Estimated Time:** 10-12 hours
**API Calls:** ~3,900 (1 per day)

**Note:** Results can be backfilled in parallel with races (different endpoint) or sequentially after races complete.

---

### Incremental Backfill Strategy (Recommended)

For better control and validation, backfill by year in reverse order:

```bash
# 2024 (most recent, most valuable)
python3 fetchers/master_fetcher_controller.py \
  --mode manual \
  --table ra_races \
  --start-date 2024-01-01 \
  --end-date 2024-12-31 \
  --interactive

# 2023
python3 fetchers/master_fetcher_controller.py \
  --mode manual \
  --table ra_races \
  --start-date 2023-01-01 \
  --end-date 2023-12-31 \
  --interactive

# Continue backwards: 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015
```

**Benefits:**
- ✅ Can validate data quality year by year
- ✅ Can pause and resume at year boundaries
- ✅ Recent data is prioritized (most important for ML)
- ✅ Lower risk than one massive 10-year backfill

---

## 🕐 Phase 2: Ongoing Scheduled Sync

Once historical backfill is complete, maintain currency with scheduled syncs.

### Master Tables Schedule

**Static Data (Monthly) - 1st of month at 1PM UK:**
```bash
# Cron: 0 13 1 * *
0 13 1 * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses ra_mst_bookmakers ra_mst_regions >> logs/cron_static.log 2>&1
```

**People Data (Weekly) - Sunday at 1PM UK:**
```bash
# Cron: 0 13 * * 0
0 13 * * 0 cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners >> logs/cron_people.log 2>&1
```

**Horse Data (Daily) - Every day at 1PM UK:**
```bash
# Cron: 0 13 * * *
0 13 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_horses >> logs/cron_horses.log 2>&1
```

### Transaction Tables Schedule

**Races, Runners, Results - Every 4 hours starting 6AM UK:**
```bash
# Cron: 0 6,10,14,18,22 * * *
0 6,10,14,18,22 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_races ra_runners ra_race_results ra_horse_pedigree >> logs/cron_transactions.log 2>&1
```

**Why every 4 hours?**
- **06:00** - Morning sync (overnight results)
- **10:00** - Mid-morning (morning racecards)
- **14:00** - Afternoon (prime UK racing time)
- **18:00** - Evening (catch day's results)
- **22:00** - Night (evening meetings + Irish racing)

### Statistics Tables Schedule

**Daily Calculation - 2:30AM UK:**
```bash
# Cron: 30 2 * * *
30 2 * * * cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1
```

**Weekly High-Quality Recalculation - Sunday 3:30AM UK:**
```bash
# Cron: 30 3 * * 0
30 3 * * 0 cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10 >> logs/cron_calculated_weekly.log 2>&1
```

---

## 📋 Complete Implementation Checklist

### Pre-Backfill

- [ ] Verify API credentials are configured (Pro plan)
- [ ] Check database has sufficient storage (~2GB free)
- [ ] Review `BACKFILL_START_DATE` in `master_fetcher_controller.py` (set to 2015-01-01)
- [ ] Test with small date range first

### Backfill Execution

- [ ] **Option A:** Run full backfill (20-24 hours)
  ```bash
  python3 fetchers/master_fetcher_controller.py --mode backfill --interactive
  ```

- [ ] **Option B:** Run incremental by year (recommended)
  ```bash
  # 2024, 2023, 2022... down to 2015
  ```

- [ ] Monitor progress in logs:
  ```bash
  tail -f logs/fetcher_backfill_*.json
  ```

- [ ] Verify checkpoint files are created (resume capability):
  ```bash
  ls -lh logs/backfill_*_checkpoint.json
  ```

### Post-Backfill Validation

- [ ] Check record counts match expected volumes:
  ```sql
  SELECT 'ra_races' as table, COUNT(*) as records FROM ra_races
  UNION ALL
  SELECT 'ra_runners', COUNT(*) FROM ra_runners
  UNION ALL
  SELECT 'ra_race_results', COUNT(*) FROM ra_race_results
  UNION ALL
  SELECT 'ra_mst_horses', COUNT(*) FROM ra_mst_horses
  UNION ALL
  SELECT 'ra_horse_pedigree', COUNT(*) FROM ra_horse_pedigree;
  ```

- [ ] Verify coverage by year:
  ```sql
  SELECT
    EXTRACT(YEAR FROM date) as year,
    COUNT(*) as races,
    COUNT(DISTINCT course_id) as courses
  FROM ra_races
  GROUP BY EXTRACT(YEAR FROM date)
  ORDER BY year DESC;
  ```

- [ ] Check runner-to-race ratio (should be ~10):
  ```sql
  SELECT
    COUNT(*) as total_races,
    (SELECT COUNT(*) FROM ra_runners) as total_runners,
    ROUND((SELECT COUNT(*) FROM ra_runners)::numeric / COUNT(*)::numeric, 2) as runners_per_race
  FROM ra_races;
  ```

### Schedule Setup

- [ ] Install cron jobs for ongoing sync
  ```bash
  crontab -e
  # Add schedules from Phase 2 above
  ```

- [ ] Verify cron jobs installed:
  ```bash
  crontab -l
  ```

- [ ] Test manual execution first:
  ```bash
  python3 fetchers/master_fetcher_controller.py --mode daily --interactive
  ```

- [ ] Monitor first week of scheduled runs:
  ```bash
  tail -f logs/cron_*.log
  ```

---

## 🔍 Monitoring and Maintenance

### Daily Checks

```bash
# Check if cron jobs ran
grep "CRON" /var/log/system.log | tail -20  # macOS
grep "CRON" /var/log/syslog | tail -20      # Linux

# Check for errors in logs
grep -i "error\|failed" logs/cron_*.log | tail -20

# Verify data freshness
```

```sql
-- Last update times
SELECT
  'ra_races' as table,
  MAX(updated_at) as last_update,
  COUNT(*) as total_records
FROM ra_races
UNION ALL
SELECT 'ra_runners', MAX(updated_at), COUNT(*) FROM ra_runners
UNION ALL
SELECT 'ra_race_results', MAX(updated_at), COUNT(*) FROM ra_race_results;
```

### Weekly Checks

- [ ] Review weekly stats calculation success
- [ ] Check storage usage trends
- [ ] Verify no checkpoint files are stale (backfill should be complete)

### Monthly Checks

- [ ] Audit data quality (missing fields, NULL rates)
- [ ] Review API usage vs limits
- [ ] Verify all 18 tables are updating as scheduled

---

## ⚠️ Important Notes

### 1. Backfill is Safe to Re-Run

All operations use **UPSERT** (insert or update on conflict). You can:
- Re-run backfill if interrupted (uses checkpoints)
- Re-run for specific date ranges (won't create duplicates)
- Run backfill while daily sync is active (UPSERT prevents conflicts)

### 2. Entity Extraction is Automatic

When backfilling races:
- **Jockeys, trainers, owners** are extracted from runners automatically
- **Sires, dams, damsires** are extracted from horse pedigrees automatically
- **Horse enrichment** happens automatically for new horses discovered

No separate entity backfill needed!

### 3. Statistics Require Source Data First

The 4 statistics tables (`ra_entity_combinations`, `ra_performance_by_*`, `ra_runner_statistics`) are **calculated from source data**:

1. ✅ Run backfill first (fills `ra_race_results`)
2. ✅ Then run statistics calculation:
   ```bash
   python3 fetchers/populate_all_calculated_tables.py
   ```

Statistics workers (from `STATISTICS_WORKERS_PLAN.md`) populate time-based and performance metrics.

### 4. Racing API Pro Plan Coverage

The Racing API **Pro plan provides**:
- ✅ Complete historical data from 2015+
- ✅ All race types (flat, jump, all-weather)
- ✅ UK & Ireland regions (GB, IRE)
- ✅ Complete runner data with pedigrees
- ✅ Results with positions, times, SP

**NOT limited to 12 months** - that's Standard plan limitation.

---

## 📚 Related Documentation

### Backfill Details
- `/docs/backfill/COMPREHENSIVE_BACKFILL_2015_2025.md` - Full backfill strategy
- `/docs/backfill/BACKFILL_EXECUTION_SUMMARY.md` - Execution report

### Schedule Configuration
- `/fetchers/schedules/COMPLETE_18_TABLES_SCHEDULE.md` - Detailed schedules
- `/fetchers/schedules/README.md` - Schedule overview

### Statistics Workers
- `/docs/STATISTICS_WORKERS_PLAN.md` - Worker implementation plan
- `/docs/UNCALCULABLE_COLUMNS_LIST.md` - Columns requiring advanced models

### Coverage Analysis
- `/fetchers/docs/*_COMPLETE_COVERAGE_AND_STATISTICS_GUIDE.md` - Master coverage guide
- `/docs/100_PERCENT_COVERAGE_ACHIEVEMENT.md` - Coverage metrics

---

## 🚀 Quick Start Commands

### 1. Analyze Current State
```bash
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive
```

### 2. Test Backfill (7 days)
```bash
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races --days-back 7 --interactive
```

### 3. Run Full Backfill
```bash
# Interactive (see progress)
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

# Background (for server)
nohup python3 fetchers/master_fetcher_controller.py --mode backfill > logs/backfill_2015_full.log 2>&1 &
```

### 4. Monitor Progress
```bash
# Watch logs
tail -f logs/fetcher_backfill_*.json

# Check process
ps aux | grep master_fetcher

# Check database
psql "$SUPABASE_URL" -c "SELECT COUNT(*) FROM ra_runners;"
```

### 5. Install Scheduled Syncs
```bash
# Edit crontab
crontab -e

# Add the 3 main cron jobs from Phase 2 above
```

---

## ✅ Success Criteria

You'll know the system is working correctly when:

1. **Historical backfill complete:**
   - `ra_runners` has ~10 runners per race (not ~2.7)
   - All years 2015-2025 represented in `ra_races`
   - `ra_horse_pedigree` has records for all horses

2. **Scheduled sync working:**
   - Cron logs show successful daily runs
   - Latest races appear within 4 hours
   - Master tables update on schedule

3. **Statistics calculating:**
   - All 4 statistics tables have recent `created_at` timestamps
   - Runner statistics cover historical horses

4. **Data quality high:**
   - 100% actual coverage (no unexpected NULLs)
   - Entity relationships intact (FK constraints)
   - No duplicate records

---

## 📊 Expected Final State

After complete backfill and ongoing sync:

| Table | Expected Records | Coverage | Update Frequency |
|-------|-----------------|----------|------------------|
| **ra_races** | ~150,000+ | 2015-current | Every 4 hours |
| **ra_runners** | ~1,500,000+ | 2015-current | Every 4 hours |
| **ra_race_results** | ~150,000+ | 2015-current | Every 4 hours |
| **ra_mst_horses** | ~200,000+ | All discovered | Every 4 hours |
| **ra_horse_pedigree** | ~200,000+ | All enriched | Every 4 hours |
| **ra_mst_jockeys** | ~5,000+ | All active | Weekly |
| **ra_mst_trainers** | ~3,500+ | All active | Weekly |
| **ra_mst_owners** | ~60,000+ | All active | Weekly |
| **ra_mst_sires** | ~15,000+ | Auto-extracted | Continuous |
| **ra_mst_dams** | ~100,000+ | Auto-extracted | Continuous |
| **ra_mst_damsires** | ~20,000+ | Auto-extracted | Continuous |
| **ra_mst_courses** | ~100 | Static | Monthly |
| **ra_mst_bookmakers** | ~30 | Static | Monthly |
| **ra_mst_regions** | ~10 | Static | Quarterly |
| **ra_entity_combinations** | ~50,000+ | Calculated | Daily |
| **ra_performance_by_distance** | ~100,000+ | Calculated | Daily |
| **ra_performance_by_venue** | ~150,000+ | Calculated | Daily |
| **ra_runner_statistics** | ~1,500,000+ | Calculated | Daily |

**Total Records:** ~3.8 million+
**Total Storage:** ~3-4 GB
**Data Currency:** Within 4 hours of real-time
**Historical Depth:** 10+ years (2015-current)

---

**Last Updated:** 2025-10-23
**Status:** ✅ Ready to Execute
**Next Action:** Run backfill from 2015-01-01

