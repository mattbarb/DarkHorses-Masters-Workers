# Master Fetcher Controller - Quick Start Guide

**Version:** 2.0 (Enhanced with Scheduling & Progress Monitoring)
**Date:** 2025-10-21
**Status:** Production Ready

---

## What's New in Version 2.0

### ✨ Key Features

1. **Built-in Scheduling** - Schedule configuration built into controller
2. **Interactive Mode** - Real-time progress monitoring for local runs
3. **Automated Mode** - JSON logging for server/cron runs
4. **Scheduled Mode** - Automatically checks schedule and runs appropriate tasks
5. **Progress Tracking** - Real-time stats and progress display

---

## Quick Command Reference

### Local Development (Interactive)

```bash
# Backfill with progress monitoring
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

# Daily sync with progress
python3 fetchers/master_fetcher_controller.py --mode daily --interactive

# Test with limited data
python3 fetchers/master_fetcher_controller.py --mode daily --test --interactive

# Manual run with progress
python3 fetchers/master_fetcher_controller.py --mode manual --table ra_mst_races --days-back 7 --interactive
```

### Production/Server (Automated)

```bash
# Daily sync (automated - for cron)
python3 fetchers/master_fetcher_controller.py --mode daily

# Scheduled mode (checks schedule, runs appropriate tasks)
python3 fetchers/master_fetcher_controller.py --mode scheduled

# Backfill (no interaction needed)
python3 fetchers/master_fetcher_controller.py --mode backfill
```

### Information Commands

```bash
# Show built-in schedule configuration
python3 fetchers/master_fetcher_controller.py --show-schedule

# List all available tables
python3 fetchers/master_fetcher_controller.py --list

# Show help
python3 fetchers/master_fetcher_controller.py --help
```

---

## Built-in Schedule Configuration

The controller includes built-in scheduling logic:

### Daily Schedule
- **When:** Every day at 1:00 AM UK time
- **Tables:** `ra_mst_races`, `ra_mst_race_results`
- **Purpose:** Sync race data and results
- **Duration:** ~10 minutes

### Weekly Schedule
- **When:** Sunday at 2:00 AM UK time
- **Tables:** `ra_mst_jockeys`, `ra_mst_trainers`, `ra_mst_owners`
- **Purpose:** Refresh people data
- **Duration:** ~5 minutes

### Monthly Schedule
- **When:** 1st of month at 3:00 AM UK time
- **Tables:** `ra_mst_courses`, `ra_mst_bookmakers`
- **Purpose:** Refresh reference data
- **Duration:** ~2 minutes

---

## Interactive vs Automated Mode

### Interactive Mode (`--interactive`)

**Use for:** Local development, testing, manual runs

**Features:**
- Real-time progress display
- Emoji indicators (🔄 ✅ ❌ 📊 ⏱️ 💾)
- Progress summaries after each table
- Detailed final summary
- Visual feedback

**Example Output:**
```
================================================================================
FETCHER CONTROLLER - DAILY MODE
================================================================================
Tables to process: 10
  1. ra_mst_courses
  2. ra_mst_bookmakers
  ...

Start time: 2025-10-21 09:00:00
================================================================================

🔄 Fetching ra_mst_courses...
   Type: bulk
   Mode: daily
   Starting: 09:00:01

✅ Success: ra_mst_courses
   Duration: 0:00:05
   Fetched: 101
   Inserted: 2

📊 Progress: 1/10 (10.0%)
   ✅ Successful: 1
   ❌ Failed: 0
```

### Automated Mode (default, no `--interactive`)

**Use for:** Production, cron jobs, server runs

**Features:**
- Standard logging to files
- JSON result output
- No terminal formatting
- Suitable for automated parsing
- Cron-friendly

---

## Cron Configuration

### Option 1: Scheduled Mode (Recommended)

**Single cron entry** - Controller checks schedule automatically:

```bash
# Add to crontab (crontab -e)
0 * * * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1
```

**How it works:**
- Runs every hour
- Controller checks current date/time
- Automatically runs appropriate tasks based on schedule
- Daily tasks run at 1am, weekly on Sunday at 2am, monthly on 1st at 3am

### Option 2: Explicit Schedules

**Separate cron entries** for each schedule:

```bash
# Daily (1am)
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1

# Weekly (Sunday 2am)
0 2 * * 0 cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners >> logs/cron_weekly.log 2>&1

# Monthly (1st of month 3am)
0 3 1 * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses ra_mst_bookmakers >> logs/cron_monthly.log 2>&1
```

---

## Common Use Cases

### 1. Initial Setup (First Time)

```bash
# Step 1: Backfill all historical data (with progress monitoring)
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

# Step 2: Verify results
ls -lt logs/fetcher_backfill_*.json | head -1 | xargs cat | jq

# Step 3: Schedule automated runs (add to crontab)
crontab -e
# Add: 0 * * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1
```

**Duration:** 6-8 hours for backfill

### 2. Daily Local Testing

```bash
# Test with limited data and see progress
python3 fetchers/master_fetcher_controller.py --mode daily --test --interactive
```

**Duration:** ~2 minutes (limited data)

### 3. Manual Data Recovery

```bash
# Recover specific date range
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_mst_races \
    --start-date 2024-01-01 \
    --end-date 2024-01-31 \
    --interactive
```

### 4. Check What Will Run Today

```bash
# Show schedule (see what's configured)
python3 fetchers/master_fetcher_controller.py --show-schedule

# Test scheduled mode without running (dry run)
python3 fetchers/master_fetcher_controller.py --mode scheduled --interactive --test
```

### 5. Production Monitoring

```bash
# View latest run results
ls -lt logs/fetcher_*.json | head -1 | xargs cat | jq

# Check for failures
grep -i "success.*false" logs/fetcher_*.json

# View automated logs
tail -f logs/cron_scheduled.log
```

---

## Progress Monitoring Details

### Real-time Stats Tracked

```python
{
    'total_tables': 10,
    'successful': 8,
    'failed': 2,
    'start_time': datetime,
    'end_time': datetime
}
```

### Per-Table Metrics

- Duration
- Records fetched from API
- Records inserted to database
- Success/failure status
- Error messages (if failed)

### Final Summary (Interactive Mode)

```
================================================================================
FINAL SUMMARY - DAILY MODE
================================================================================

📊 Overall Statistics:
   Total tables: 10
   ✅ Successful: 9
   ❌ Failed: 1
   ⏱️  Total duration: 0:10:32
   Start time: 2025-10-21 01:00:00
   End time: 2025-10-21 01:10:32

✅ Successful tables:
   ra_mst_courses: 101 fetched, 2 inserted
   ra_mst_bookmakers: 22 fetched, 0 inserted
   ...

❌ Failed tables:
   ra_mst_races: API connection timeout

💾 Results saved to: logs/fetcher_daily_20251021_011032.json
================================================================================
```

---

## Logging and Results

### JSON Result Files

**Location:** `logs/fetcher_{mode}_{timestamp}.json`

**Structure:**
```json
{
  "mode": "daily",
  "timestamp": "2025-10-21T01:00:00",
  "duration": "0:10:32",
  "stats": {
    "total_tables": 10,
    "successful": 9,
    "failed": 1,
    "start_time": "2025-10-21T01:00:00",
    "end_time": "2025-10-21T01:10:32"
  },
  "results": {
    "ra_mst_courses": {
      "success": true,
      "fetched": 101,
      "inserted": 2,
      "duration": "0:00:05",
      "table": "ra_mst_courses"
    },
    ...
  }
}
```

### Log Files

- **Cron logs:** `logs/cron_scheduled.log`, `logs/cron_daily.log`, etc.
- **Application logs:** Standard logger output
- **Result JSON:** One file per execution

---

## Troubleshooting

### No Progress Displayed in Interactive Mode

**Cause:** tqdm not installed

**Solution:**
```bash
pip install tqdm
```

### Schedule Not Running

**Check:**
1. Cron is running: `sudo systemctl status cron`
2. Crontab is configured: `crontab -l`
3. Environment variables are set
4. Logs for errors: `tail -f logs/cron_scheduled.log`

### Interactive Mode Shows No Tables

**Cause:** Tables filter might be empty

**Solution:**
```bash
# Don't specify --tables for full sync
python3 fetchers/master_fetcher_controller.py --mode daily --interactive
```

---

## Command-Line Arguments Reference

### Modes

| Argument | Description | Use Case |
|----------|-------------|----------|
| `--mode backfill` | Fetch all data from 2015-present | Initial setup |
| `--mode daily` | Fetch last 3 days + current reference data | Daily sync |
| `--mode scheduled` | Check schedule, run appropriate tasks | Automated cron |
| `--mode manual` | Custom date ranges/tables | Recovery, testing |

### Options

| Argument | Description | Example |
|----------|-------------|---------|
| `--interactive` | Enable progress monitoring | Local runs |
| `--test` | Limit data for testing | Development |
| `--table TABLE` | Specific table (manual mode) | `--table ra_mst_races` |
| `--tables T1 T2` | Multiple tables | `--tables ra_mst_courses ra_mst_bookmakers` |
| `--start-date DATE` | Start date (manual mode) | `--start-date 2024-01-01` |
| `--end-date DATE` | End date (manual mode) | `--end-date 2024-01-31` |
| `--days-back N` | N days back (manual mode) | `--days-back 7` |
| `--list` | List all tables | Information |
| `--show-schedule` | Show schedule config | Information |

---

## Performance

### Backfill Mode
- **Duration:** 6-8 hours
- **Data:** ~10 years of racing data
- **Tables:** All 10 tables
- **Records:** ~13M total

### Daily Mode
- **Duration:** ~10 minutes
- **Data:** Last 3 days
- **Tables:** All 10 tables
- **Records:** ~1000 races, ~15000 runners

### Test Mode
- **Duration:** ~2 minutes
- **Data:** Limited (7 days for races, 5 pages for bulk)
- **Purpose:** Verification

---

## Best Practices

### Local Development

1. Always use `--interactive` for visibility
2. Use `--test` for quick verification
3. Monitor progress in real-time
4. Check JSON results after completion

### Production Deployment

1. Use automated mode (no `--interactive`)
2. Use scheduled mode for simplicity
3. Monitor logs regularly
4. Set up alerts for failures

### Testing

1. Test with `--test --interactive` before production
2. Verify schedule with `--show-schedule`
3. Check JSON results format
4. Ensure cron has correct permissions

---

## Next Steps

### For Local Development:
```bash
# Test the system
python3 fetchers/master_fetcher_controller.py --mode daily --test --interactive

# View schedule
python3 fetchers/master_fetcher_controller.py --show-schedule
```

### For Production Deployment:
```bash
# Add to crontab
crontab -e
# Add: 0 * * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1

# Verify cron entry
crontab -l | grep fetcher
```

---

## Summary

**Key Improvements:**
- ✅ Built-in scheduling (daily/weekly/monthly)
- ✅ Interactive progress monitoring
- ✅ Automated JSON logging
- ✅ Scheduled mode for cron
- ✅ Real-time stats tracking
- ✅ Detailed summaries

**Works Both:**
- Locally (with `--interactive`)
- Automated (without `--interactive`)

**Single Controller:**
- All modes in one script
- Consistent interface
- Easy to use and maintain

---

**Location:** `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/`
**Documentation:** See also `README.md`, `FETCHERS_INDEX.md`, `TABLE_TO_SCRIPT_MAPPING.md`
**Version:** 2.0 - Production Ready ✅
