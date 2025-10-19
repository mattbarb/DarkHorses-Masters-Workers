# Data Collection Quick Start Guide

## TL;DR - The One Command

```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
python3 initialize_data.py
```

**This single command gets you 10 years of complete racing data (2015-2025).**

---

## What You'll Get

### 1.4 Million Records Across 10 Tables

| Table | Records | Description |
|-------|---------|-------------|
| `ra_courses` | ~150 | UK & Irish racecourses |
| `ra_bookmakers` | ~50 | Bookmaker reference data |
| `ra_results` | ~40,000 | Race results (2015-2023) |
| `ra_races` | ~15,000 | Racecards (2023-2025) |
| `ra_runners` | ~600,000 | All runner performances |
| `ra_horses` | ~80,000 | Every horse (with lineage) |
| `ra_jockeys` | ~3,000 | Every jockey |
| `ra_trainers` | ~2,500 | Every trainer |
| `ra_owners` | ~25,000 | Every owner/syndicate |

---

## Timeline

**Expected Duration:** 11-16 hours
- Phase 1 (Results 2015-2022): 8-12 hours
- Phase 2 (Racecards 2023-2025): 3-4 hours
- Phase 3 (Reference data): 1 minute

**Why so long?**
- API rate limit: 2 requests/second
- ~4,000 API calls needed (one per day from 2015-2025)
- Processing and database insertions

---

## What's Happening Behind the Scenes

### Phase 1: Historical Results (2015-2022)
- Fetches `/v1/results` endpoint day-by-day
- Extracts race results, runner performances, and entities
- Populates: `ra_results`, `ra_horses`, `ra_jockeys`, `ra_trainers`, `ra_owners`

### Phase 2: Historical Racecards (2023-2025)
- Fetches `/v1/racecards/pro` endpoint day-by-day
- Extracts race cards, runner entries, and entities (with enhanced data)
- Populates: `ra_races`, `ra_runners`, and enriches entity tables

### Phase 3: Reference Data
- Fetches courses and bookmakers once
- Populates: `ra_courses`, `ra_bookmakers`

---

## Monitoring Progress

### Log Files
All progress is logged to: `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/logs/`

### What You'll See
```
PHASE 1: REFERENCE DATA COLLECTION
✅ Courses: 143 records
✅ Bookmakers: 52 records

PHASE 2A: HISTORICAL RESULTS (2015-2023)
CHUNK 1/33: 2015-01-01 to 2015-03-31
📊 Progress: 90/2943 days (3.1%)

PHASE 2B: HISTORICAL RACECARDS (2023-2025)
CHUNK 1/11: 2023-01-23 to 2023-04-23
📊 Progress: 91/987 days (9.2%)

INITIALIZATION COMPLETE
📋 Reference Data: ✅
📊 Historical Data: ✅
🎉 Initialization complete! Database is ready.
```

---

## Optional Flags

### Start from a specific date
```bash
python3 initialize_data.py --from 2020-01-01
```
Only fetch results from 2020 onwards (faster, less data)

### Skip reference data
```bash
python3 initialize_data.py --skip-reference
```
Skip courses/bookmakers if already loaded

### Test mode
```bash
python3 initialize_data.py --test
```
Only fetch last 7 days (for testing)

---

## Troubleshooting

### Script stops or errors
- Check logs in `/logs/` directory
- Re-run with same command - it will skip duplicates
- Database uses upsert strategy - safe to re-run

### API rate limit errors
- Script includes automatic pauses
- If you hit limits, wait 60 seconds and restart
- Script will continue from where it left off

### Database connection issues
- Check your `.env` file for correct credentials
- Ensure Supabase service key is correct
- Verify network connection

---

## After Completion

### Verify Your Data
```sql
-- Check record counts
SELECT 'courses' as table_name, COUNT(*) FROM ra_courses
UNION ALL
SELECT 'results', COUNT(*) FROM ra_results
UNION ALL
SELECT 'races', COUNT(*) FROM ra_races
UNION ALL
SELECT 'runners', COUNT(*) FROM ra_runners
UNION ALL
SELECT 'horses', COUNT(*) FROM ra_horses
UNION ALL
SELECT 'jockeys', COUNT(*) FROM ra_jockeys
UNION ALL
SELECT 'trainers', COUNT(*) FROM ra_trainers
UNION ALL
SELECT 'owners', COUNT(*) FROM ra_owners;
```

### Example Queries
```sql
-- Top 10 horses by race wins (2015-2025)
SELECT
  h.name,
  COUNT(*) as wins
FROM ra_runners r
JOIN ra_horses h ON r.horse_id = h.horse_id
WHERE r.position = '1'
GROUP BY h.name
ORDER BY wins DESC
LIMIT 10;

-- Trainer performance by year
SELECT
  EXTRACT(YEAR FROM race_date)::int as year,
  t.name as trainer,
  COUNT(*) as races,
  COUNT(*) FILTER (WHERE position = '1') as wins,
  ROUND(COUNT(*) FILTER (WHERE position = '1')::numeric / COUNT(*) * 100, 2) as win_pct
FROM ra_runners r
JOIN ra_trainers t ON r.trainer_id = t.trainer_id
JOIN ra_results res ON r.race_id = res.race_id
GROUP BY year, t.name
ORDER BY year DESC, wins DESC;
```

---

## Need More Info?

See the complete strategy document:
`/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/COMPLETE_DATA_STRATEGY_2015-2025.md`

This includes:
- Detailed API endpoint analysis
- Field-by-field comparison
- Entity extraction explanation
- Complete implementation details
