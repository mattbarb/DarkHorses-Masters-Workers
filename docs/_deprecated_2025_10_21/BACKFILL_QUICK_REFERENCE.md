# Backfill Quick Reference Card

One-page reference for backfilling historical data.

---

## Quick Commands

### Complete Backfill (Recommended)
```bash
# Full backfill from 2015 to present
python3 scripts/backfill_all.py --start-date 2015-01-01
```

### Resume After Interruption
```bash
# Continue from checkpoint
python3 scripts/backfill_events.py --resume
```

### Check Status (Dry Run)
```bash
# See what would be done
python3 scripts/backfill_events.py --check-status --start-date 2015-01-01
```

---

## Time Estimates

| Range | Duration |
|-------|----------|
| **2015-Present** | **1-2 hours** |
| 1 year | ~5-7 minutes |
| 1 month | ~30 seconds |
| 1 day | ~1 second |

---

## Script Reference

### backfill_all.py (Orchestrator)
**Use for:** Complete backfill (masters + events)

```bash
# Standard
python3 scripts/backfill_all.py --start-date 2015-01-01

# Resume events only
python3 scripts/backfill_all.py --start-date 2015-01-01 --resume --skip-masters

# Preview
python3 scripts/backfill_all.py --start-date 2015-01-01 --dry-run
```

### backfill_events.py (Events Only)
**Use for:** Racecards and results

```bash
# Full backfill
python3 scripts/backfill_events.py --start-date 2015-01-01

# Specific range
python3 scripts/backfill_events.py --start-date 2020-01-01 --end-date 2020-12-31

# Resume
python3 scripts/backfill_events.py --resume

# Status check
python3 scripts/backfill_events.py --check-status --start-date 2015-01-01
```

### backfill_masters.py (Masters Only)
**Use for:** Reference data only

```bash
# Standard
python3 scripts/backfill_masters.py
```

---

## Common Options

| Option | Description |
|--------|-------------|
| `--start-date YYYY-MM-DD` | Start date (required) |
| `--end-date YYYY-MM-DD` | End date (default: today) |
| `--resume` | Resume from checkpoint |
| `--check-status` | Dry run (no data fetched) |
| `--dry-run` | Preview what would run |
| `--skip-masters` | Skip master data |
| `--region-codes gb ire` | Filter regions |

---

## Background Execution

### Using screen
```bash
screen -S backfill
python3 scripts/backfill_all.py --start-date 2015-01-01
# Detach: Ctrl+A, then D
# Reattach: screen -r backfill
```

### Using tmux
```bash
tmux new -s backfill
python3 scripts/backfill_all.py --start-date 2015-01-01
# Detach: Ctrl+B, then D
# Reattach: tmux attach -t backfill
```

### Using nohup
```bash
nohup python3 scripts/backfill_all.py --start-date 2015-01-01 > logs/backfill.log 2>&1 &
tail -f logs/backfill.log
```

---

## Monitoring Progress

### Check checkpoint
```bash
cat logs/backfill_events_checkpoint.json | python3 -m json.tool
```

### Watch logs
```bash
tail -f logs/backfill_events_*.log
```

### Check errors
```bash
cat logs/backfill_events_errors.json | python3 -m json.tool
```

---

## Verification Queries

### Record counts
```sql
SELECT
  (SELECT COUNT(*) FROM ra_races) as races,
  (SELECT COUNT(*) FROM ra_runners) as runners,
  (SELECT COUNT(*) FROM ra_mst_horses) as horses;
```

### Date coverage
```sql
SELECT
  DATE_TRUNC('year', date::date) as year,
  COUNT(*) as races
FROM ra_races
WHERE date >= '2015-01-01'
GROUP BY year
ORDER BY year;
```

### Data quality
```sql
SELECT
  COUNT(DISTINCT r.id) as total_races,
  COUNT(DISTINCT ru.race_id) as races_with_runners
FROM ra_races r
LEFT JOIN ra_runners ru ON r.id = ru.race_id;
```

---

## Troubleshooting

### Problem: Backfill stops
**Solution:**
```bash
# Check errors
cat logs/backfill_events_errors.json

# Resume
python3 scripts/backfill_events.py --resume
```

### Problem: Slow progress
**Expected:** ~30 days per minute at 2 req/sec
**If slower:** Check network latency, API status

### Problem: Authentication error
**Solution:**
```bash
# Verify credentials
cat .env.local | grep RACING_API

# Test connection
python3 -c "from utils.api_client import RacingAPIClient; print('OK')"
```

---

## Daily Updates (After Initial Backfill)

### Manual
```bash
# Yesterday's data
python3 scripts/backfill_events.py --start-date $(date -d "yesterday" +%Y-%m-%d)
```

### Automated (Cron)
```bash
# Add to crontab (daily at 6 AM)
0 6 * * * cd /path/to/project && python3 scripts/backfill_events.py --start-date $(date -d "yesterday" +\%Y-\%m-\%d)
```

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Failure |
| 130 | Interrupted (Ctrl+C) |

---

## Files Generated

| File | Purpose |
|------|---------|
| `logs/backfill_events_checkpoint.json` | Resume data |
| `logs/backfill_events_errors.json` | Error log |
| `logs/backfill_events_*.log` | Execution log |

---

## Important Notes

**Rate Limit:** 2 requests/second (enforced by API client)

**Tables Populated:**
- Master: bookmakers, courses, regions, horses, jockeys, trainers, owners, pedigree
- Events: races, runners

**Entity Extraction:** Automatic (horses/jockeys/trainers/owners from events)

**Resume Safe:** Can interrupt at any time (Ctrl+C)

**UPSERT Logic:** No duplicates on re-run

---

## Full Documentation

- **User Guide:** `docs/BACKFILL_GUIDE.md`
- **Estimates:** `docs/BACKFILL_TIMELINE_ESTIMATES.md`
- **Summary:** `docs/BACKFILL_IMPLEMENTATION_SUMMARY.md`

---

**Last Updated:** 2025-10-19
