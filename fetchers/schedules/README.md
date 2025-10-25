# Fetchers Schedules

This directory contains schedule configuration files for all automated fetching and calculation tasks.

## Files

### calculated_tables_schedule.yaml
Complete schedule configuration for all calculated/derived tables:
- Daily and weekly calculation schedules
- Table definitions and dependencies
- Cron job configurations
- Monitoring settings

## Schedule Overview

### Racing API Data Fetch
- **Frequency:** Hourly (checks internal schedule)
- **Script:** `fetchers/master_fetcher_controller.py --mode scheduled`
- **Tables:** ra_races, ra_runners, ra_mst_*, etc.
- **Cron:** `0 * * * *`

### Calculated Tables (Daily)
- **Frequency:** Daily at 2:30 AM
- **Script:** `fetchers/populate_all_calculated_tables.py`
- **Tables:** 4 derived/analytics tables
- **Cron:** `30 2 * * *`

### Calculated Tables (Weekly Full Recalc)
- **Frequency:** Sunday at 3:30 AM
- **Script:** `fetchers/populate_all_calculated_tables.py` (with strict thresholds)
- **Tables:** Same 4 tables, higher quality thresholds
- **Cron:** `30 3 * * 0`

## Quick Start

### View Schedule Configuration
```bash
cat fetchers/schedules/calculated_tables_schedule.yaml
```

### Install Cron Jobs
```bash
# Edit crontab
crontab -e

# Add these lines:
0 * * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1
30 2 * * * cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1
30 3 * * 0 cd /path/to/project && python3 fetchers/populate_all_calculated_tables.py --min-runs 10 --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10 >> logs/cron_calculated_weekly.log 2>&1
```

### Manual Run
```bash
# Run all calculated tables now
python3 fetchers/populate_all_calculated_tables.py

# Run with custom parameters
python3 fetchers/populate_all_calculated_tables.py --min-runs 10
```

## Tables Updated

When `populate_all_calculated_tables.py` runs:

**Phase 1:**
1. `ra_entity_combinations` - Jockey-trainer partnerships

**Phase 2:**
2. `ra_runner_statistics` - 60 performance metrics per runner
3. `ra_performance_by_distance` - Distance-based performance
4. `ra_performance_by_venue` - Course specialist identification

**Total: 4 tables** (cleared and rebuilt each run)

**Note:** Odds data is queried directly from `ra_odds_live` and `ra_odds_historical` (no aggregation table needed)

## Dependencies

```
Racing API Fetch (hourly)
    ↓
Source Tables Populated
    ├── ra_runners
    ├── ra_races
    └── ra_odds_live
    ↓
Calculated Tables (daily 2:30 AM)
    ├── Phase 1 (2-5 minutes)
    │   └── ra_entity_combinations
    └── Phase 2 (15-25 minutes)
        ├── ra_runner_statistics
        ├── ra_performance_by_distance
        └── ra_performance_by_venue
```

## Monitoring

### Check Last Run
```bash
tail -50 logs/cron_calculated_tables.log
```

### Check for Errors
```bash
grep -i "error\|failed" logs/cron_calculated_tables.log
```

### Verify Tables
```sql
-- Check update times and record counts
SELECT 'entity_combinations' as table_name,
       MAX(created_at) as last_update,
       COUNT(*) as records
FROM ra_entity_combinations
UNION ALL
SELECT 'runner_statistics',
       MAX(updated_at),
       COUNT(*)
FROM ra_runner_statistics;
```

## Customization

### Adjust Thresholds

Edit parameters in cron command:
```bash
# Higher thresholds = fewer records, faster runtime
--min-runs 20 --min-runs-runner 10 --min-runs-distance 20 --min-runs-venue 20

# Lower thresholds = more records, longer runtime
--min-runs 2 --min-runs-runner 1 --min-runs-distance 2 --min-runs-venue 2
```

### Skip Specific Phases
```bash
# Only Phase 1
python3 fetchers/populate_all_calculated_tables.py --skip-phase2

# Only Phase 2
python3 fetchers/populate_all_calculated_tables.py --skip-phase1
```

## Related Documentation

- `/docs/CALCULATED_TABLES_IMPLEMENTATION.md` - Implementation details
- `/docs/CALCULATED_TABLES_SCHEDULING.md` - Full scheduling guide
- `/fetchers/CONTROLLER_QUICK_START.md` - Master controller guide

---

**Last Updated:** 2025-10-22
**Maintained By:** Development Team
