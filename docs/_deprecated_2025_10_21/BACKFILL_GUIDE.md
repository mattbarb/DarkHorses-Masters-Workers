# Backfill Guide

Complete guide for backfilling historical horse racing data from 2015 to present.

## Overview

The DarkHorses backfill system provides autonomous, resumable data population for all database tables from January 1, 2015 to the current date. The system is designed to be production-ready with comprehensive error handling, progress tracking, and resume capability.

## What Gets Backfilled

### Master/Reference Tables (ra_mst_*)
- **ra_mst_bookmakers** - UK/Irish bookmakers (static list)
- **ra_mst_courses** - Racing venues (from API)
- **ra_mst_regions** - Geographic regions (GB, IRE)
- **ra_mst_horses** - Horses (via entity extraction from events)
- **ra_mst_jockeys** - Jockeys (via entity extraction from events)
- **ra_mst_trainers** - Trainers (via entity extraction from events)
- **ra_mst_owners** - Owners (via entity extraction from events)
- **ra_mst_sires** - Sires (via pedigree extraction)
- **ra_mst_dams** - Dams (via pedigree extraction)
- **ra_mst_damsires** - Dam's sires (via pedigree extraction)

### Event Tables (ra_*)
- **ra_races** - Race metadata (date, course, class, distance, going, prize)
- **ra_runners** - Runner records with pre-race and post-race data
- **ra_horse_pedigree** - Complete lineage for all horses

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Backfill Orchestrator                     │
│                   (backfill_all.py)                          │
└────────────────┬───────────────────────────┬─────────────────┘
                 │                           │
        ┌────────▼────────┐         ┌────────▼────────┐
        │ Masters Backfill│         │ Events Backfill │
        │ (bookmakers,    │         │ (racecards,     │
        │  courses,       │         │  results)       │
        │  regions)       │         │                 │
        └────────┬────────┘         └────────┬────────┘
                 │                           │
                 │                  ┌────────▼────────┐
                 │                  │ Entity Extractor│
                 │                  │ (horses,        │
                 │                  │  jockeys,       │
                 │                  │  trainers,      │
                 │                  │  owners,        │
                 │                  │  pedigree)      │
                 │                  └────────┬────────┘
                 │                           │
        ┌────────▼───────────────────────────▼────────┐
        │          Supabase PostgreSQL Database        │
        │                (ra_* tables)                 │
        └──────────────────────────────────────────────┘
```

## Quick Start

### Complete Backfill (Recommended)

```bash
# Backfill everything from 2015 to present
python3 scripts/backfill_all.py --start-date 2015-01-01

# Resume if interrupted (uses checkpoint)
python3 scripts/backfill_all.py --start-date 2015-01-01 --resume

# Check what would be done (dry run)
python3 scripts/backfill_all.py --start-date 2015-01-01 --dry-run
```

### Individual Components

**Masters only (fast - ~5 seconds):**
```bash
python3 scripts/backfill_masters.py
```

**Events only (slow - see estimates below):**
```bash
# Full backfill from 2015
python3 scripts/backfill_events.py --start-date 2015-01-01

# Specific date range
python3 scripts/backfill_events.py --start-date 2020-01-01 --end-date 2020-12-31

# Resume from checkpoint
python3 scripts/backfill_events.py --resume

# Check status before running
python3 scripts/backfill_events.py --check-status --start-date 2015-01-01
```

## Command Reference

### backfill_all.py (Orchestrator)

Runs complete backfill in the correct order.

**Options:**
- `--start-date YYYY-MM-DD` - **Required.** Start date for events backfill
- `--end-date YYYY-MM-DD` - End date (default: today)
- `--region-codes gb ire` - Regions to fetch (default: gb ire)
- `--skip-masters` - Skip master data backfill
- `--resume` - Resume events backfill from checkpoint
- `--dry-run` - Show what would be executed

**Examples:**
```bash
# Full backfill from 2015
python3 scripts/backfill_all.py --start-date 2015-01-01

# Resume from checkpoint
python3 scripts/backfill_all.py --start-date 2015-01-01 --resume

# Skip masters (if already complete)
python3 scripts/backfill_all.py --start-date 2015-01-01 --skip-masters
```

### backfill_masters.py

Backfills master reference data (bookmakers, courses, regions).

**Options:**
- `--region-codes gb ire` - Regions to fetch (default: gb ire)

**Examples:**
```bash
# Standard run
python3 scripts/backfill_masters.py

# GB only
python3 scripts/backfill_masters.py --region-codes gb
```

### backfill_events.py

Backfills historical event data with resume capability.

**Options:**
- `--start-date YYYY-MM-DD` - **Required** unless --resume
- `--end-date YYYY-MM-DD` - End date (default: today)
- `--region-codes gb ire` - Regions to fetch (default: gb ire)
- `--no-racecards` - Skip racecards (results only)
- `--no-results` - Skip results (racecards only)
- `--resume` - Resume from last checkpoint
- `--check-status` - Check status without running (dry run)
- `--checkpoint-file PATH` - Custom checkpoint file

**Examples:**
```bash
# Full backfill
python3 scripts/backfill_events.py --start-date 2015-01-01

# Specific year
python3 scripts/backfill_events.py --start-date 2020-01-01 --end-date 2020-12-31

# Resume from checkpoint
python3 scripts/backfill_events.py --resume

# Check estimates before running
python3 scripts/backfill_events.py --check-status --start-date 2015-01-01

# Racecards only (no results)
python3 scripts/backfill_events.py --start-date 2015-01-01 --no-results

# Results only (no racecards)
python3 scripts/backfill_events.py --start-date 2015-01-01 --no-racecards
```

## Time Estimates

### Full Backfill (2015-01-01 to 2025-10-19)

**Total Duration: ~1-2 hours**

| Component | API Calls | Time | Details |
|-----------|-----------|------|---------|
| Masters | 3-5 | ~5 seconds | Bookmakers, courses, regions |
| Events (racecards) | ~3,944 | ~0.5 hours | 1 API call per day |
| Events (results) | ~3,944 | ~0.5 hours | 1 API call per day |
| **Total** | **~7,891** | **~1 hour** | At 2 requests/second rate limit |

**Note:** Actual time may vary based on:
- Network latency
- API response times
- Database write performance
- Number of entities requiring enrichment

### Monthly Processing

For ongoing maintenance after initial backfill:
- **1 month of data**: ~60 API calls, ~30 seconds
- **1 year of data**: ~730 API calls, ~6 minutes

## Progress Tracking

### Checkpoint System

The backfill automatically saves progress to:
```
logs/backfill_events_checkpoint.json
```

**Checkpoint contains:**
- Timestamp of last save
- Chunks processed
- Total races/runners fetched
- Statistics for each chunk

**Example checkpoint:**
```json
{
  "timestamp": "2025-10-19T15:30:00.000Z",
  "stats": {
    "total_chunks": 131,
    "chunks_processed": 45,
    "total_races": 12543,
    "total_runners": 156789,
    "start_date": "2015-01-01",
    "end_date": "2025-10-19"
  }
}
```

### Error Logging

Errors are logged to:
```
logs/backfill_events_errors.json
```

**Example error log:**
```json
[
  {
    "timestamp": "2025-10-19T15:30:00.000Z",
    "chunk": "2020-05-01 to 2020-05-31",
    "error": "API timeout after 5 retries"
  }
]
```

### Real-time Monitoring

During execution, logs show:
```
============================================================
CHUNK 45/131: 2018-09-01 to 2018-09-30
============================================================
Fetching racecards for chunk 45...
Found 847 races for September 2018
Stored 847 races
Stored 9,124 runners
Extracting entities to master tables...
Entities extracted: {'horses': 1234, 'jockeys': 89, 'trainers': 123, 'owners': 456}
Chunk 45 completed successfully
```

## Resume Capability

The backfill system can be interrupted and resumed at any time.

### How Resume Works

1. **Automatic checkpoint saving** after each monthly chunk
2. **Resume detection** - finds last completed chunk
3. **Smart restart** - begins from next chunk
4. **No duplicate data** - UPSERT logic prevents duplicates

### Interrupting Backfill

**Safe to interrupt at any time:**
- Press `Ctrl+C` to stop gracefully
- Script saves checkpoint before exiting
- Database remains in consistent state

**To resume:**
```bash
python3 scripts/backfill_events.py --resume
```

**Or with orchestrator:**
```bash
python3 scripts/backfill_all.py --start-date 2015-01-01 --resume
```

## Rate Limiting

The Racing API enforces **2 requests per second** across all plan tiers.

### How Rate Limiting is Handled

1. **API Client** automatically sleeps between requests
2. **Retry logic** with exponential backoff on 429 errors
3. **Smart chunking** to avoid hitting limits

### API Call Breakdown

**Per day of data:**
- 1 call for racecards (all races for that day)
- 1 call for results (all results for that day)

**Monthly chunk (30 days):**
- 30 calls for racecards
- 30 calls for results
- Total: 60 calls
- Time: ~30 seconds at 2 req/sec

## Error Handling

### Automatic Retries

All API calls have automatic retry with exponential backoff:
- **Max retries:** 5
- **Backoff:** 2, 4, 8, 16, 32 seconds
- **Total retry time:** ~60 seconds per failed request

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| 401 Unauthorized | Invalid API credentials | Check .env.local file |
| 429 Rate Limited | Too many requests | Wait and retry (automatic) |
| 404 Not Found | No data for date | Normal - some dates have no races |
| Timeout | Network/API slow | Automatic retry |
| Database error | Connection issue | Check Supabase status |

### Critical vs Non-Critical Errors

**Critical (backfill stops):**
- Authentication failure
- Database connection failure
- Invalid date range

**Non-Critical (logged and continued):**
- Single date fetch failure
- Individual entity extraction failure
- Temporary network issues

## Database Tables Populated

### Execution Order

1. **ra_mst_bookmakers** (masters) - Static UK/Irish bookmakers
2. **ra_mst_courses** (masters) - Racing venues from API
3. **ra_mst_regions** (masters) - Geographic regions (GB, IRE)
4. **ra_races** (events) - Race metadata
5. **ra_runners** (events) - Runner records
6. **ra_mst_horses** (extracted) - Horses from runners
7. **ra_mst_jockeys** (extracted) - Jockeys from runners
8. **ra_mst_trainers** (extracted) - Trainers from runners
9. **ra_mst_owners** (extracted) - Owners from runners
10. **ra_mst_sires** (extracted) - Sires from pedigree
11. **ra_mst_dams** (extracted) - Dams from pedigree
12. **ra_mst_damsires** (extracted) - Dam's sires from pedigree
13. **ra_horse_pedigree** (extracted) - Complete lineage

### Entity Extraction

Entities are **automatically extracted** from event data:

**From racecards/results:**
- Horses (basic data)
- Jockeys (name, ID)
- Trainers (name, ID, location)
- Owners (name, ID)

**From horse enrichment (Pro API):**
- Complete horse data (DOB, sex, colour, region)
- Pedigree (sire, dam, damsire, breeder)

## Production Deployment

### Prerequisites

1. **Environment Variables:**
   ```bash
   RACING_API_USERNAME=your_username
   RACING_API_PASSWORD=your_password
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_SERVICE_KEY=your_service_key
   ```

2. **Disk Space:**
   - Logs: ~100MB for full backfill
   - Checkpoints: ~1MB
   - Database: Varies by data volume

3. **Network:**
   - Stable internet connection
   - Access to Racing API
   - Access to Supabase

### Running in Background

**Using nohup:**
```bash
nohup python3 scripts/backfill_all.py --start-date 2015-01-01 > logs/backfill.log 2>&1 &

# Check progress
tail -f logs/backfill.log

# Get PID
echo $!
```

**Using screen:**
```bash
screen -S backfill
python3 scripts/backfill_all.py --start-date 2015-01-01

# Detach: Ctrl+A, then D
# Reattach: screen -r backfill
```

**Using tmux:**
```bash
tmux new -s backfill
python3 scripts/backfill_all.py --start-date 2015-01-01

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t backfill
```

### Monitoring

**Check checkpoint:**
```bash
cat logs/backfill_events_checkpoint.json | python3 -m json.tool
```

**Check errors:**
```bash
cat logs/backfill_events_errors.json | python3 -m json.tool
```

**Check logs:**
```bash
tail -f logs/backfill_events_*.log
```

## Troubleshooting

### Backfill Stops Unexpectedly

**Check:**
1. Error log: `logs/backfill_events_errors.json`
2. Recent logs: `tail -100 logs/backfill_events_*.log`
3. Checkpoint exists: `ls -l logs/backfill_events_checkpoint.json`

**Solution:**
```bash
# Resume from checkpoint
python3 scripts/backfill_events.py --resume
```

### No Data for Certain Dates

**This is normal!** Not every day has racing events. The script will log:
```
No racecards for 2020-12-25
```

This is expected for holidays, off-season dates, etc.

### Database Connection Issues

**Check:**
1. Supabase status: https://status.supabase.com/
2. Environment variables: `echo $SUPABASE_URL`
3. Service key validity

**Solution:**
1. Verify credentials in `.env.local`
2. Test connection: `python3 -c "from utils.supabase_client import SupabaseReferenceClient; print('OK')"`

### API Authentication Failure

**Check:**
1. Racing API credentials valid
2. Account not expired
3. Plan includes historical data (Pro plan required)

**Solution:**
1. Verify credentials in `.env.local`
2. Test: `python3 -c "from utils.api_client import RacingAPIClient; print('OK')"`

### Slow Progress

**Normal speed:**
- ~2 requests per second (API rate limit)
- ~30 days per minute
- ~1 year per 25 minutes

**If slower:**
1. Check network latency
2. Check API response times
3. Consider running during off-peak hours

## Verification

### After Backfill Completes

**Check record counts:**
```sql
-- Races
SELECT COUNT(*) FROM ra_races;

-- Runners
SELECT COUNT(*) FROM ra_runners;

-- Entities
SELECT COUNT(*) FROM ra_mst_horses;
SELECT COUNT(*) FROM ra_mst_jockeys;
SELECT COUNT(*) FROM ra_mst_trainers;
SELECT COUNT(*) FROM ra_mst_owners;

-- Pedigree
SELECT COUNT(*) FROM ra_horse_pedigree;
```

**Check date coverage:**
```sql
SELECT
  DATE_TRUNC('year', date::date) as year,
  COUNT(*) as races
FROM ra_races
WHERE date >= '2015-01-01'
GROUP BY year
ORDER BY year;
```

**Check data quality:**
```sql
-- Races with runners
SELECT
  COUNT(DISTINCT r.id) as races_with_runners,
  COUNT(DISTINCT ru.race_id) as total_races
FROM ra_races r
LEFT JOIN ra_runners ru ON r.id = ru.race_id;

-- Horses with pedigree
SELECT
  COUNT(*) as total_horses,
  COUNT(p.horse_id) as horses_with_pedigree
FROM ra_mst_horses h
LEFT JOIN ra_horse_pedigree p ON h.id = p.horse_id;
```

## Best Practices

### Initial Backfill

1. **Check status first:**
   ```bash
   python3 scripts/backfill_events.py --check-status --start-date 2015-01-01
   ```

2. **Run in background session** (screen/tmux/nohup)

3. **Monitor periodically** (check logs/checkpoint)

4. **Don't interrupt** unless necessary (but safe if you do)

### Incremental Updates

For ongoing maintenance after initial backfill:

```bash
# Daily: Fetch yesterday's data
python3 scripts/backfill_events.py --start-date $(date -d "yesterday" +%Y-%m-%d)

# Weekly: Fetch last 7 days
python3 scripts/backfill_events.py --start-date $(date -d "7 days ago" +%Y-%m-%d)

# Monthly: Fetch last month
python3 scripts/backfill_events.py --start-date $(date -d "1 month ago" +%Y-%m-%d)
```

### Resource Management

1. **Logs:** Rotate or archive old logs periodically
2. **Checkpoints:** Keep recent checkpoints, archive old ones
3. **Database:** Monitor storage usage in Supabase

## Related Documentation

- **Architecture:** `docs/architecture/START_HERE.md`
- **API Details:** `docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md`
- **Entity Extraction:** `docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`
- **Database Schema:** `docs/database/SCHEMA.md`

## Support

For issues or questions:
1. Check logs: `logs/backfill_events_*.log`
2. Check errors: `logs/backfill_events_errors.json`
3. Review this guide
4. Check CLAUDE.md for architecture details

---

**Last Updated:** 2025-10-19
**Version:** 1.0
**Status:** Production Ready
