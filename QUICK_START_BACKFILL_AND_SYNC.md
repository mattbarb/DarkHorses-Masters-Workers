# Quick Start: Backfill from 2015 + Scheduled Sync

**Purpose:** Get complete historical data from 2015-01-01 and set up automated ongoing sync

---

## 🚀 Phase 1: Historical Backfill (One Command)

### Run Complete Backfill

```bash
# Interactive mode (see progress, ETA, statistics)
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

# OR background mode (for server/long-running)
nohup python3 fetchers/master_fetcher_controller.py --mode backfill > logs/backfill_2015_full.log 2>&1 &
```

**What this does:**
- ✅ Fetches ALL racecards from 2015-01-01 to today
- ✅ Populates races, runners, results
- ✅ Extracts all entities (jockeys, trainers, owners, horses)
- ✅ Auto-enriches horses with complete pedigree data
- ✅ Checkpoints every 10 dates (can resume if interrupted)

**Expected Duration:** 20-24 hours
**Expected Data:** ~1.5 million runners, ~200k horses, ~150k races

### Monitor Progress

```bash
# Watch live progress (if interactive mode)
# Progress bar shows in terminal

# Watch logs (if background mode)
tail -f logs/backfill_2015_full.log

# Check database growth
watch -n 60 'psql "$SUPABASE_URL" -c "SELECT COUNT(*) FROM ra_mst_runners;"'
```

### Verify Completion

```bash
# Check record counts
python3 -c "
from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config

config = get_config()
client = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

print('\n📊 Backfill Results:\n')
tables = ['ra_mst_races', 'ra_mst_runners', 'ra_mst_race_results', 'ra_mst_horses', 'ra_horse_pedigree']
for table in tables:
    count = client.client.table(table).select('id', count='exact').execute().count
    print(f'  {table}: {count:,} records')

print()
"
```

Expected results:
- `ra_mst_races`: ~150,000+
- `ra_mst_runners`: ~1,500,000+ (CRITICAL - should be ~10 per race)
- `ra_mst_race_results`: ~150,000+
- `ra_mst_horses`: ~200,000+
- `ra_horse_pedigree`: ~200,000+

---

## 🕐 Phase 2: Set Up Scheduled Sync (3 Cron Jobs)

Once backfill completes, set up automated ongoing sync:

### Install Cron Jobs

```bash
# Open crontab editor
crontab -e

# Add these 3 cron jobs:
```

```bash
# 1. Transaction tables (races, runners, results) - Every 4 hours
0 6,10,14,18,22 * * * cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_races ra_mst_runners ra_mst_race_results ra_horse_pedigree >> logs/cron_transactions.log 2>&1

# 2. Master tables (people, horses) - Daily at 1pm UK
0 13 * * * cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1

# 3. Statistics tables (calculated daily) - Daily at 2:30am UK
30 2 * * * cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers && python3 fetchers/populate_all_calculated_tables.py >> logs/cron_calculated_tables.log 2>&1
```

**Important:** Replace `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers` with your actual project path.

### Verify Cron Installation

```bash
# List installed cron jobs
crontab -l

# Should show 3 jobs:
# - Every 4 hours (6,10,14,18,22)
# - Daily at 1pm
# - Daily at 2:30am
```

### Test Manual Execution First

```bash
# Test transaction sync
python3 fetchers/master_fetcher_controller.py --mode daily --interactive

# Test scheduled sync
python3 fetchers/master_fetcher_controller.py --mode scheduled --interactive

# Test statistics calculation
python3 fetchers/populate_all_calculated_tables.py
```

---

## 📊 Phase 3: Verify Everything Works

### Check Daily Sync (Next Day)

```bash
# Check cron ran successfully
tail -50 logs/cron_transactions.log
tail -50 logs/cron_scheduled.log

# Verify fresh data
psql "$SUPABASE_URL" -c "
SELECT
  MAX(date) as latest_race_date,
  MAX(updated_at) as last_update
FROM ra_mst_races;
"
```

Expected: `latest_race_date` should be today or yesterday

### Check Statistics Calculation

```bash
# Verify statistics tables populated
psql "$SUPABASE_URL" -c "
SELECT
  'ra_runner_statistics' as table,
  COUNT(*) as records,
  MAX(created_at) as last_calculated
FROM ra_runner_statistics
UNION ALL
SELECT
  'ra_entity_combinations',
  COUNT(*),
  MAX(created_at)
FROM ra_entity_combinations;
"
```

Expected: Records should exist, `last_calculated` should be recent (within 24 hours)

---

## ⚠️ Troubleshooting

### Backfill Interrupted?

**Resume from checkpoint:**
```bash
# Backfill automatically resumes from last checkpoint
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

# Check checkpoint
cat logs/backfill_checkpoint.json
```

### Cron Not Running?

**Check cron status:**
```bash
# macOS
grep "cron" /var/log/system.log | tail -20

# Linux
grep "CRON" /var/log/syslog | tail -20

# Check for errors
grep -i "error\|failed" logs/cron_*.log
```

### Missing Data?

**Re-run specific date range:**
```bash
python3 fetchers/master_fetcher_controller.py \
  --mode manual \
  --table ra_mst_races \
  --start-date 2024-01-01 \
  --end-date 2024-01-31 \
  --interactive
```

---

## 📋 Complete Checklist

### Before Starting
- [ ] Verify API credentials (`RACING_API_USERNAME`, `RACING_API_PASSWORD`)
- [ ] Verify Supabase credentials (`SUPABASE_URL`, `SUPABASE_SERVICE_KEY`)
- [ ] Check available disk space (~3GB free recommended)
- [ ] Test with small date range first (optional but recommended)

### Phase 1: Backfill
- [ ] Start backfill: `python3 fetchers/master_fetcher_controller.py --mode backfill --interactive`
- [ ] Monitor progress (20-24 hours)
- [ ] Verify completion (check record counts)
- [ ] Confirm runner-to-race ratio (~10)

### Phase 2: Scheduled Sync
- [ ] Install 3 cron jobs (transaction, scheduled, statistics)
- [ ] Verify cron installation: `crontab -l`
- [ ] Test manual execution for each job
- [ ] Wait 24 hours for first scheduled runs

### Phase 3: Verification
- [ ] Check cron logs next day
- [ ] Verify fresh data in database
- [ ] Confirm statistics calculating
- [ ] Review error logs (should be minimal)

### Ongoing Maintenance
- [ ] Weekly: Review logs for errors
- [ ] Monthly: Audit data quality
- [ ] Quarterly: Review storage usage

---

## 🎯 Success Criteria

You're done when:

1. ✅ **Backfill complete:**
   - `ra_mst_runners` has ~1.5M+ records
   - `ra_mst_races` has ~150K+ records
   - Runner-to-race ratio is ~10 (not ~2.7)

2. ✅ **Scheduled sync working:**
   - Cron logs show successful runs
   - Latest races appear within 4 hours of racing
   - Statistics tables update daily

3. ✅ **Data quality verified:**
   - No unexpected NULL columns
   - All 18 tables have data
   - Coverage spans 2015-current

---

## 📚 Detailed Documentation

For more information, see:
- `/fetchers/schedules/COMPLETE_DATA_STRATEGY_2015_TO_CURRENT.md` - Complete strategy
- `/fetchers/schedules/COMPLETE_18_TABLES_SCHEDULE.md` - Detailed schedules
- `/docs/backfill/COMPREHENSIVE_BACKFILL_2015_2025.md` - Backfill details

---

## 🆘 Need Help?

**Common issues:**
- Backfill slow? Normal - takes 20-24 hours for 10 years of data
- Rate limit errors? Built-in retry handles this automatically
- Missing checkpoint? Backfill restarts from beginning (safe with UPSERT)
- Cron not running? Check paths in crontab match your project location

**Logs to check:**
```bash
ls -lh logs/
tail -100 logs/backfill_2015_full.log
tail -50 logs/cron_transactions.log
tail -50 logs/fetcher_backfill_*.json
```

---

**Last Updated:** 2025-10-23
**Status:** ✅ Ready to Execute
**Estimated Total Time:** 24-26 hours (mostly automated)

