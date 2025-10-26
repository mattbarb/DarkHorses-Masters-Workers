# Calculated Tables - Production Scheduling Guide

**Created:** 2025-10-22
**Purpose:** Complete guide for scheduling all calculation tasks in production

## Overview

Your system now has **5 automated calculation tables** that derive statistics from the Racing API data:

**Phase 1 - Database Calculations:**
1. ra_entity_combinations (jockey-trainer partnerships)
2. ra_runner_odds (aggregated odds)

**Phase 2 - Analytics:**
3. ra_runner_statistics (runner performance metrics)
4. ra_performance_by_distance (distance-based analysis)
5. ra_performance_by_venue (course specialists)

These run AFTER Racing API data is fetched (via master_fetcher_controller.py).

---

## Master Script

### populate_all_calculated_tables.py

**Location:** `/scripts/populate_all_calculated_tables.py`

Single script that runs ALL calculations in the correct order.

**Usage:**
```bash
# Production run (default settings)
python3 scripts/populate_all_calculated_tables.py

# Custom thresholds
python3 scripts/populate_all_calculated_tables.py \
  --min-runs 10 \
  --min-runs-runner 5 \
  --min-runs-distance 10 \
  --min-runs-venue 10

# Skip specific phases
python3 scripts/populate_all_calculated_tables.py --skip-phase1
python3 scripts/populate_all_calculated_tables.py --skip-phase2
```

---

## Production Cron Schedule

### Recommended Setup

Add to your crontab (`crontab -e`):

```bash
# ============================================================================
# DarkHorses Masters Workers - Production Schedule
# ============================================================================

# 1. RACING API DATA FETCH (Primary Data Source)
# Runs hourly, checks schedule internally, fetches new races/results
0 * * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1

# 2. CALCULATED TABLES (Derived Statistics)
# Runs daily at 2:30 AM (after Racing API fetches complete)
30 2 * * * cd /path/to/project && python3 scripts/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1

# 3. WEEKLY FULL RECALCULATION
# Runs Sunday at 3:30 AM with higher thresholds
30 3 * * 0 cd /path/to/project && python3 scripts/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10 >> logs/cron_calculated_weekly.log 2>&1
```

### Execution Timeline

```
Daily Schedule:
00:00 AM - System idle
01:00 AM - Racing API daily fetch (races, results) [master_fetcher_controller --mode scheduled]
01:15 AM - Fetches complete
02:00 AM - Racing API weekly fetch (people) [master_fetcher_controller --mode scheduled]
02:15 AM - Fetches complete
02:30 AM - Calculate ALL derived statistics [populate_all_calculated_tables.py]
02:45 AM - Calculations complete
03:00 AM - Racing API monthly fetch (courses, bookmakers) [master_fetcher_controller --mode scheduled]

Weekly (Sunday):
03:30 AM - Full recalculation with strict thresholds [populate_all_calculated_tables.py]
04:00 AM - All operations complete
```

---

## Alternative: Render.com Cron Jobs

If deploying on Render.com, configure via dashboard:

### Job 1: Scheduled Data Fetch
- **Name:** `racing-api-scheduled-fetch`
- **Command:** `python3 fetchers/master_fetcher_controller.py --mode scheduled`
- **Schedule:** `0 * * * *` (hourly)
- **Region:** Same as main service

### Job 2: Daily Calculations
- **Name:** `calculated-tables-daily`
- **Command:** `python3 scripts/populate_all_calculated_tables.py`
- **Schedule:** `30 2 * * *` (2:30 AM daily)
- **Region:** Same as main service

### Job 3: Weekly Recalculation
- **Name:** `calculated-tables-weekly`
- **Command:** `python3 scripts/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10`
- **Schedule:** `30 3 * * 0` (3:30 AM Sunday)
- **Region:** Same as main service

---

## Monitoring

### Check Logs

```bash
# View latest calculated tables run
tail -50 logs/cron_calculated_tables.log

# Check for errors
grep -i error logs/cron_calculated_tables.log

# View weekly recalculation results
tail -100 logs/cron_calculated_weekly.log
```

### Verify Table Populations

```sql
-- Check last update times
SELECT 'entity_combinations' as table_name,
       MAX(created_at) as last_update,
       COUNT(*) as records
FROM ra_entity_combinations
UNION ALL
SELECT 'runner_statistics',
       MAX(updated_at),
       COUNT(*)
FROM ra_runner_statistics
UNION ALL
SELECT 'performance_by_distance',
       MAX(calculated_at),
       COUNT(*)
FROM ra_performance_by_distance
UNION ALL
SELECT 'performance_by_venue',
       MAX(calculated_at),
       COUNT(*)
FROM ra_performance_by_venue;
```

### Expected Record Counts

Based on 1.3M+ runners in production:

| Table | Expected Records | Test (1K runners) |
|-------|------------------|-------------------|
| ra_entity_combinations | 200-500 partnerships | 19 |
| ra_runner_odds | Varies (days_back × races) | N/A |
| ra_runner_statistics | 50K-100K runners | 117 |
| ra_performance_by_distance | 5K-15K records | 408 |
| ra_performance_by_venue | 3K-10K records | 286 |

---

## Performance Expectations

### Daily Run (Default Thresholds)

**Phase 1:**
- Entity combinations: 2-5 minutes
- Runner odds (7 days): 30-60 seconds
- **Subtotal: 3-6 minutes**

**Phase 2:**
- Runner statistics: 5-8 minutes
- Performance by distance: 5-8 minutes
- Performance by venue: 5-8 minutes
- **Subtotal: 15-25 minutes**

**Total Daily: 18-31 minutes**

### Weekly Full Recalculation (Strict Thresholds)

**With higher thresholds:**
- Fewer records to calculate
- Faster processing
- **Total: 10-20 minutes**

---

## Customization Options

### Adjust Thresholds

Lower thresholds = more records, longer runtime:
```bash
python3 scripts/populate_all_calculated_tables.py \
  --min-runs 3 \
  --min-runs-runner 2 \
  --min-runs-distance 3 \
  --min-runs-venue 3
```

Higher thresholds = fewer records, faster runtime, more statistically significant:
```bash
python3 scripts/populate_all_calculated_tables.py \
  --min-runs 15 \
  --min-runs-runner 10 \
  --min-runs-distance 15 \
  --min-runs-venue 15
```

### Skip Specific Calculations

```bash
# Skip Phase 1 entirely (keep only Phase 2 analytics)
python3 scripts/populate_all_calculated_tables.py --skip-phase1

# Skip Phase 2 entirely (keep only Phase 1 calculations)
python3 scripts/populate_all_calculated_tables.py --skip-phase2

# Skip individual tables
python3 scripts/populate_all_calculated_tables.py --skip-runner-odds --skip-venue
```

### Run Phases Separately

```bash
# Run only Phase 1
python3 scripts/populate_all_calculated_tables.py --skip-phase2

# Run only Phase 2
python3 scripts/populate_all_calculated_tables.py --skip-phase1
```

---

## Troubleshooting

### Issue: Calculations Take Too Long

**Solution 1:** Increase thresholds
```bash
--min-runs 20 --min-runs-distance 20 --min-runs-venue 20
```

**Solution 2:** Run phases at different times
```bash
# 2:30 AM - Phase 1 only
30 2 * * * cd /path && python3 scripts/populate_all_calculated_tables.py --skip-phase2

# 3:00 AM - Phase 2 only
0 3 * * * cd /path && python3 scripts/populate_all_calculated_tables.py --skip-phase1
```

**Solution 3:** Run full recalc less frequently
```bash
# Change weekly to monthly
30 3 1 * * cd /path && python3 scripts/populate_all_calculated_tables.py ...
```

### Issue: Errors in Specific Table

**Check logs for the specific table:**
```bash
grep "ra_runner_statistics" logs/cron_calculated_tables.log
```

**Run that table individually:**
```bash
# Test runner statistics alone
python3 scripts/populate_runner_statistics.py --min-runs 3
```

### Issue: No Data Calculated

**Verify Racing API data exists:**
```sql
SELECT COUNT(*) FROM ra_mst_runners WHERE position IS NOT NULL;
```

If count is 0, Racing API fetch hasn't run or completed.

**Check Racing API fetch schedule:**
```bash
python3 fetchers/master_fetcher_controller.py --show-schedule
```

---

## Success Checklist

After deploying to production:

- [ ] Cron jobs or Render scheduled tasks configured
- [ ] First daily run completed successfully
- [ ] Logs show successful table populations
- [ ] Database queries confirm records exist
- [ ] Weekly recalculation scheduled
- [ ] Monitoring alerts set up (optional)
- [ ] Backup/recovery process documented

---

## Quick Reference

### Check If Scheduled Tasks Are Running

```bash
# View cron jobs
crontab -l

# Check for running Python processes
ps aux | grep populate_all_calculated_tables

# Check recent log activity
ls -lht logs/ | head -10
```

### Manual Test Run

```bash
# Test with production data, see real-time output
python3 scripts/populate_all_calculated_tables.py 2>&1 | tee logs/manual_test_$(date +%Y%m%d_%H%M%S).log
```

### Emergency: Stop All Calculations

```bash
# Find and kill running calculation processes
pkill -f populate_all_calculated_tables
pkill -f populate_runner_statistics
pkill -f populate_performance_by
```

---

**Status:** Production-ready
**Deployment:** Ready for cron/Render scheduling
**Maintenance:** Weekly log review recommended
**Last Updated:** 2025-10-22
