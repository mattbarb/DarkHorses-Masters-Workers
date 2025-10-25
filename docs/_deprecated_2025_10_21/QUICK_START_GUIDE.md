# DarkHorses Masters Workers - Quick Start Guide

**Version:** 2.0
**Date:** 2025-10-21

---

## 🚀 Quick Start (3 Commands)

### 1. Initial Backfill (First Time Only)
```bash
# Populate ALL data from 2015 to present (~6-8 hours)
python3 fetchers/master_fetcher_controller.py --mode backfill
```

### 2. Calculate Statistics
```bash
# Populate pedigree statistics (~3-4 hours)
python3 scripts/population_workers/pedigree_statistics_agent.py

# Calculate entity statistics (~15 minutes)
python3 scripts/statistics_workers/run_all_statistics_workers.py
```

### 3. Schedule Daily Sync
```bash
# Add to crontab
crontab -e

# Paste this line:
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1
```

**Done!** Your system is now fully operational.

---

## 📊 What Gets Populated

### Racing API Data (10 Tables)
- **Fetcher:** `fetchers/master_fetcher_controller.py`
- **Tables:** ra_mst_courses, bookmakers, jockeys, trainers, owners, horses, races, runners, results, horse_pedigree
- **Columns:** 300+ from Racing API
- **Schedule:** Daily at 1am UK

### Database Statistics (13 Tables)
- **Pedigree:** `scripts/population_workers/pedigree_statistics_agent.py`
- **Tables:** ra_mst_sires, dams, damsires (126 columns)
- **Schedule:** Weekly

- **Entity Stats:** `scripts/statistics_workers/`
- **Tables:** Jockeys, trainers, owners statistics
- **Schedule:** Weekly

**Total:** 23 tables, 625+ columns, fully automated

---

## 🎯 Common Tasks

### Check Status
```bash
# List all available tables
python3 fetchers/master_fetcher_controller.py --list

# Check population status
python3 scripts/population_workers/master_populate_all_ra_tables.py --status

# Monitor pedigree agent
bash agents/monitor_agent.sh
```

### Manual Fetch
```bash
# Fetch specific date range
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_races --start-date 2024-01-01 --end-date 2024-01-31

# Fetch last 7 days
python3 fetchers/master_fetcher_controller.py --mode manual \
    --table ra_races --days-back 7
```

### Update Statistics
```bash
# Update pedigree statistics
python3 scripts/population_workers/pedigree_statistics_agent.py

# Update specific pedigree table
python3 scripts/population_workers/pedigree_statistics_agent.py --table sires

# Update entity statistics
python3 scripts/statistics_workers/run_all_statistics_workers.py
```

### Test Mode
```bash
# Test daily sync (limited data)
python3 fetchers/master_fetcher_controller.py --mode daily --test

# Test pedigree agent (10 entities)
python3 scripts/population_workers/pedigree_statistics_agent.py --test
```

---

## 📁 Key Files

### Master Controllers
- `fetchers/master_fetcher_controller.py` - Racing API data
- `scripts/population_workers/master_populate_all_ra_tables.py` - All tables

### Documentation
- `FETCHER_SYSTEM_SUMMARY.md` - Fetcher system overview
- `COMPLETE_POPULATION_SYSTEM_SUMMARY.md` - Full system overview
- `docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json` - Master inventory
- `fetchers/README.md` - Fetcher guide
- `fetchers/TABLE_COLUMN_MAPPING.json` - Column mapping
- `docs/FETCHER_SCHEDULING_GUIDE.md` - Scheduling guide

### Logs
- `logs/fetcher_*.json` - Fetch results
- `logs/pedigree_agent_*.log` - Pedigree agent logs
- `logs/cron_daily.log` - Cron execution logs

---

## ⏱️ Time Estimates

### Initial Setup
| Task | Duration |
|------|----------|
| Backfill (2015-present) | 6-8 hours |
| Pedigree statistics | 3-4 hours |
| Entity statistics | 15 minutes |
| **Total First Time** | **~10-12 hours** |

### Daily Maintenance
| Task | Duration |
|------|----------|
| Daily sync (1am) | 10 minutes |
| Weekly stats update | 20 minutes |
| **Per Day** | **~10 minutes automated** |

---

## 🔍 Monitoring

### Logs
```bash
# View latest fetch
ls -lt logs/fetcher_*.json | head -1 | xargs cat | jq

# Check for errors
grep "ERROR" logs/cron_daily.log | tail -20

# Live monitoring
tail -f logs/cron_daily.log
```

### Database
```sql
-- Check data freshness
SELECT table_name, MAX(updated_at) as last_update
FROM information_schema.tables
WHERE table_name LIKE 'ra_%'
GROUP BY table_name;

-- Row counts
SELECT 'ra_races' as table, COUNT(*) FROM ra_races
UNION ALL SELECT 'ra_runners', COUNT(*) FROM ra_runners
UNION ALL SELECT 'ra_mst_horses', COUNT(*) FROM ra_mst_horses;
```

---

## 🛠️ Troubleshooting

### Fetch Not Running
1. Check crontab: `crontab -l`
2. Test manually: `python3 fetchers/master_fetcher_controller.py --mode daily`
3. Check logs: `tail -50 logs/cron_daily.log`

### Statistics Not Updating
1. Check agent running: `ps aux | grep pedigree`
2. Test manually: `python3 scripts/population_workers/pedigree_statistics_agent.py --test`
3. Check logs: `tail -50 logs/pedigree_agent_run.log`

### Environment Issues
1. Verify .env.local exists: `ls -la .env.local`
2. Check credentials: `python3 -c "from config.config import get_config; print(get_config().api.username)"`
3. Test connection: `python3 -c "from utils.api_client import RacingAPIClient; ..."`

---

## 📋 Schedules

### Daily (1:00 AM UK)
```bash
0 1 * * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1
```

### Weekly (Sunday 2:00 AM)
```bash
0 2 * * 0 cd /path/to/DarkHorses-Masters-Workers && python3 scripts/population_workers/pedigree_statistics_agent.py >> logs/cron_weekly.log 2>&1
```

### Monthly (1st at 3:00 AM)
```bash
0 3 1 * * cd /path/to/DarkHorses-Masters-Workers && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses ra_mst_bookmakers >> logs/cron_monthly.log 2>&1
```

---

## 🎓 Learn More

| Topic | Document |
|-------|----------|
| Fetcher System | `FETCHER_SYSTEM_SUMMARY.md` |
| Population System | `COMPLETE_POPULATION_SYSTEM_SUMMARY.md` |
| Column Inventory | `docs/COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json` |
| Scheduling | `docs/FETCHER_SCHEDULING_GUIDE.md` |
| Fetcher Details | `fetchers/README.md` |
| Column Mapping | `fetchers/TABLE_COLUMN_MAPPING.json` |

---

## ✅ Success Checklist

- [ ] Environment variables configured (.env.local)
- [ ] Backfill completed (6-8 hours)
- [ ] Pedigree statistics calculated (3-4 hours)
- [ ] Daily cron scheduled (1am UK)
- [ ] Logs directory created and writable
- [ ] Database access verified
- [ ] Racing API credentials working

---

**Need Help?**
1. Check system status: `python3 fetchers/master_fetcher_controller.py --list`
2. Review logs: `ls -lt logs/ | head -10`
3. Test connection: `python3 fetchers/master_fetcher_controller.py --mode daily --test`

**System Status:** ✅ Production Ready
**Next Action:** Run initial backfill or schedule daily sync
