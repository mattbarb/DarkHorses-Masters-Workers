# Statistics Workers - Quick Start Guide

## What Are These Workers?

Three production-ready scripts that populate enhanced statistics fields in your database tables:

- **ra_jockeys** - 10 statistics fields (rides, wins, win rates)
- **ra_trainers** - 10 statistics fields (runners, wins, win rates)
- **ra_owners** - 10 statistics fields (runners, wins, win rates)

## Quick Start

### 1. Test First (Recommended)

Test with a small sample (10 entities per table):

```bash
python3 scripts/statistics_workers/run_all_statistics_workers.py --limit 10
```

This should complete in under 1 minute.

### 2. Run Full Update

Process all entities in the database:

```bash
python3 scripts/statistics_workers/run_all_statistics_workers.py
```

**Expected duration:** 2-3.5 hours for ~8,500 entities

### 3. Verify Results

Check the database:

```python
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

# Check jockeys
result = db.client.table('ra_jockeys')\
    .select('name, last_ride_date, recent_14d_rides, recent_14d_win_rate')\
    .not_.is_('stats_updated_at', 'null')\
    .limit(10)\
    .execute()

for row in result.data:
    print(f"{row['name']}: {row['recent_14d_rides']} rides, {row['recent_14d_win_rate']}% win rate")
```

### 4. Schedule Weekly Updates

Add to cron (runs every Sunday at 2am):

```bash
0 2 * * 0 cd /path/to/DarkHorses-Masters-Workers && python3 scripts/statistics_workers/run_all_statistics_workers.py
```

## Individual Workers

Run workers separately if needed:

```bash
# Jockeys only
python3 scripts/statistics_workers/jockeys_statistics_worker.py

# Trainers only
python3 scripts/statistics_workers/trainers_statistics_worker.py

# Owners only
python3 scripts/statistics_workers/owners_statistics_worker.py
```

## What Gets Updated?

### Every Entity Gets:
- **Last activity date** - When they last rode/ran
- **Last win date** - When they last won
- **Days since** - Days since last activity/win
- **Recent 14-day form** - Rides/runs and wins in last 14 days
- **Recent 30-day form** - Rides/runs and wins in last 30 days
- **Win rates** - Percentage win rates for 14d and 30d windows

### Example Output:

```
Mr C J Shine(7) (jky_286434)
  Last ride: 2025-10-16, Days since: 3
  Last win: 2024-12-29, Days since: 294
  Recent 14d: 2 rides, 0 wins, 0.0% win rate
  Recent 30d: 6 rides, 0 wins, 0.0% win rate
```

## Troubleshooting

### Workers Running Slow?
- Normal! API has rate limit of 2 requests/second
- Active entities (with many results) take longer
- Expected: 2-3.5 hours for full run

### Seeing Rate Limit Warnings?
- Normal! Workers automatically retry
- No action needed, just wait

### Some Entities Not Updated?
- Check if entity is active (had races in last 365 days)
- Inactive entities may have NULL statistics

### Database Errors?
- Verify Supabase connection
- Check service key has write permissions
- Ensure statistics columns exist in tables

## File Locations

```
scripts/statistics_workers/
├── README.md                          # Detailed documentation
├── __init__.py                        # Package init
├── jockeys_statistics_worker.py       # Jockeys worker
├── trainers_statistics_worker.py      # Trainers worker
├── owners_statistics_worker.py        # Owners worker
└── run_all_statistics_workers.py      # Master script (recommended)
```

## Statistics Fields

Each table gets these 10 fields:

| Field Name | Type | Description |
|-----------|------|-------------|
| last_ride_date / last_runner_date | DATE | Last activity date |
| last_win_date | DATE | Last win date |
| days_since_last_ride / days_since_last_runner | INTEGER | Days since last activity |
| days_since_last_win | INTEGER | Days since last win |
| recent_14d_rides / recent_14d_runs | INTEGER | Count in last 14 days |
| recent_14d_wins | INTEGER | Wins in last 14 days |
| recent_14d_win_rate | DECIMAL | Win rate in last 14 days (%) |
| recent_30d_rides / recent_30d_runs | INTEGER | Count in last 30 days |
| recent_30d_wins | INTEGER | Wins in last 30 days |
| recent_30d_win_rate | DECIMAL | Win rate in last 30 days (%) |

## Full Documentation

For detailed information:
- **Complete docs:** `scripts/statistics_workers/README.md`
- **Implementation:** `STATISTICS_WORKERS_IMPLEMENTATION.md`
- **Reference:** `scripts/test_statistics_endpoints.py`

## Need Help?

1. Check logs for error details
2. Test with `--limit 10` first
3. Verify database connection and permissions
4. Review README.md for troubleshooting section

## Summary

**To update all statistics:**
```bash
python3 scripts/statistics_workers/run_all_statistics_workers.py
```

**To test first:**
```bash
python3 scripts/statistics_workers/run_all_statistics_workers.py --limit 10
```

**To schedule weekly:**
```bash
0 2 * * 0 cd /path/to/project && python3 scripts/statistics_workers/run_all_statistics_workers.py
```

That's it! Your entity statistics will be automatically calculated and kept up to date.
