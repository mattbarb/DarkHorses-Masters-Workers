# Comprehensive Historical Backfill: 2015-2025

**Document Status:** Production Ready
**Created:** 2025-10-16
**Purpose:** Complete backfill of all RA tables with historical data from 2015 onwards

---

## Executive Summary

This document describes the comprehensive backfill strategy for populating all RA tables with complete historical data from January 1, 2015 to present.

### Current State Analysis

Based on analysis conducted on 2025-10-16:

| Table | Total Records | Coverage | Status |
|-------|--------------|----------|--------|
| **ra_mst_races** | 136,648 | 2015-2025 (100%) | ✅ COMPLETE |
| **ra_mst_runners** | 380,313 | 2025 only (~28%) | ⚠️ PARTIAL |
| **ra_horses** | 111,430 | 2025 only | ⚠️ PARTIAL |
| **ra_jockeys** | 3,482 | 2025 only | ⚠️ PARTIAL |
| **ra_trainers** | 2,780 | 2025 only | ⚠️ PARTIAL |
| **ra_owners** | 48,132 | 2025 only | ⚠️ PARTIAL |
| **ra_horse_pedigree** | 111,353 | 2025 only | ⚠️ PARTIAL |
| **ra_courses** | 101 | Complete | ✅ COMPLETE |
| **ra_bookmakers** | 19 | Complete | ✅ COMPLETE |

### Critical Finding

**The ra_mst_runners table only has ~28% coverage** (380,313 runners for 136,648 races = 2.78 runners per race average, when it should be ~10). This indicates that while we have runner data from October 2025, **we're missing runner data for the vast majority of historical races (2015-2024)**.

This is a **CRITICAL GAP** that blocks:
- Historical race analysis
- AI model training with complete data
- Comprehensive performance metrics
- Downstream analytics

---

## Solution: Comprehensive Backfill Script

### Script Location

```
/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/scripts/backfill_all_ra_tables_2015_2025.py
```

### What It Does

1. **Fetches racecards** for all dates from 2015-01-01 onwards using `/v1/racecards/pro` endpoint
2. **Extracts and stores:**
   - Race metadata → `ra_mst_races` (UPSERT, no duplicates)
   - Runner data → `ra_mst_runners` (CRITICAL - fills the gap)
   - Jockey entities → `ra_jockeys`
   - Trainer entities → `ra_trainers`
   - Owner entities → `ra_owners`
   - Horse entities → `ra_horses`
3. **Automatically enriches new horses** with Pro endpoint:
   - Fetches complete horse metadata (dob, sex_code, colour, region)
   - Captures pedigree data (sire, dam, damsire, breeder) → `ra_horse_pedigree`
4. **Respects API rate limits** (2 requests/second)
5. **Checkpoints progress** every 10 dates for resume capability
6. **Provides ETA** and progress tracking

### Key Features

- **UPSERT-safe:** Can be re-run without creating duplicates
- **Resume-capable:** Can restart from checkpoint if interrupted
- **Rate-limited:** Respects Racing API limits (2 req/sec)
- **Error-resilient:** Logs errors and continues processing
- **Progress tracking:** Real-time statistics and ETA
- **Automatic enrichment:** New horses get complete data automatically

---

## Backfill Estimates

### Data Volume

```
Date Range: 2015-01-01 to 2025-10-16 (3,942 days)

Expected Data:
- Races: ~47,304 (already have ~136,648, so minimal new races)
- Runners: ~473,040 NEW (critical gap to fill)
- New Horses: ~141,912 (requiring enrichment)
- Jockeys: ~3,500+ unique
- Trainers: ~2,800+ unique
- Owners: ~50,000+ unique
- Pedigrees: ~141,912 new records
```

### API Requirements

```
API Calls Required:
- Racecard fetches: 3,942 calls (1 per day)
- Horse enrichment: ~141,912 calls (Pro endpoint for new horses)
- Total API calls: ~145,854

Rate Limit: 2 requests/second
```

### Time Estimates

```
Estimated Duration:
- Seconds: 72,927 (~20.3 hours)
- Hours: 20.3
- Days: 0.8 (less than 1 day)

Conservative estimate: ~24 hours for full backfill
```

### Storage Requirements

```
Additional Storage Needed:
- Races: ~231 MB (minimal, mostly duplicates)
- Runners: ~1,386 MB (CRITICAL - new data)
- Total: ~1.58 GB additional storage
```

---

## Usage Guide

### 1. Analyze Current State

Before running the backfill, analyze the current database state:

```bash
# Run comprehensive analysis
python3 scripts/analyze_backfill_requirements.py

# Or use the backfill script's analyze mode
python3 scripts/backfill_all_ra_tables_2015_2025.py --analyze
```

This will show:
- Current record counts by table
- Coverage by year (2015-2025)
- Gaps that need filling
- Estimated backfill requirements

### 2. Test Mode (Recommended First)

Test with a small date range before running the full backfill:

```bash
# Test with 7 days (non-interactive)
python3 scripts/backfill_all_ra_tables_2015_2025.py --test --non-interactive

# Test with specific date range
python3 scripts/backfill_all_ra_tables_2015_2025.py \
  --start-date 2024-01-01 \
  --end-date 2024-01-07 \
  --non-interactive
```

### 3. Incremental Backfill (Recommended Strategy)

For safety and manageability, backfill by year in reverse chronological order:

```bash
# Backfill 2024 (most recent year)
python3 scripts/backfill_all_ra_tables_2015_2025.py \
  --start-date 2024-01-01 \
  --end-date 2024-12-31

# Backfill 2023
python3 scripts/backfill_all_ra_tables_2015_2025.py \
  --start-date 2023-01-01 \
  --end-date 2023-12-31

# Continue backwards through each year...
```

**Why this approach?**
- Lower risk (can stop/verify at any point)
- Recent data is most important for AI models
- Easier to monitor and validate
- Can parallelize if running on multiple machines

### 4. Full Backfill (Use with Caution)

For a complete backfill from 2015:

```bash
# Full backfill (will prompt for confirmation)
python3 scripts/backfill_all_ra_tables_2015_2025.py \
  --start-date 2015-01-01

# Full backfill (non-interactive for background job)
python3 scripts/backfill_all_ra_tables_2015_2025.py \
  --start-date 2015-01-01 \
  --non-interactive
```

### 5. Resume from Checkpoint

If the backfill is interrupted, resume from where it left off:

```bash
# Resume using checkpoint
python3 scripts/backfill_all_ra_tables_2015_2025.py --resume
```

The script automatically:
- Loads the checkpoint file (`logs/backfill_all_tables_checkpoint.json`)
- Skips already processed dates
- Continues from the last processed date

---

## Monitoring Progress

### Real-time Monitoring

Use the monitoring script to track progress in real-time:

```bash
# Monitor with 60-second interval (default)
python3 scripts/monitor_backfill.py

# Monitor with custom interval
python3 scripts/monitor_backfill.py --interval 30

# Single status check
python3 scripts/monitor_backfill.py --once
```

The monitor displays:
- Current progress (dates/races/runners processed)
- Insertion rates (per minute)
- Estimated time remaining (ETA)
- Database record counts
- Error statistics

### Checkpoint File

Location: `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/logs/backfill_all_tables_checkpoint.json`

Contains:
- Timestamp of last save
- Statistics (dates, races, runners, horses, etc.)
- List of processed dates (for resume)
- Last processed date

### Error Log

Location: `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/logs/backfill_all_tables_errors.json`

Logs all errors encountered during backfill:
- Timestamp
- Date that failed
- Error message

---

## Production Deployment Strategy

### Recommended Approach

**Option 1: Incremental Backfill (Safest)**

1. Start with most recent year (2024)
2. Verify data quality
3. Continue backwards year by year
4. Monitor database size and performance

**Timeline:** 10-15 days (running 1-2 hours per year)

**Pros:**
- Low risk
- Easy to validate
- Can stop/adjust at any time
- Minimal impact on database

**Cons:**
- Longer calendar time
- Requires manual intervention between years

---

**Option 2: Full Backfill (Faster)**

1. Run complete backfill from 2015-01-01
2. Use non-interactive mode
3. Monitor progress remotely
4. Verify at completion

**Timeline:** 1-2 days (20-24 hours of runtime)

**Pros:**
- Fastest approach
- Single operation
- Complete coverage

**Cons:**
- Higher risk if issues occur
- Harder to troubleshoot mid-run
- Longer continuous operation

---

**Option 3: Parallel Backfill (Advanced)**

If you have access to multiple servers/instances:

1. Split date range into chunks (e.g., by year)
2. Run parallel backfills on different servers
3. Each server processes different year range
4. Combine results in single database

**Timeline:** 2-3 hours (if running 10 parallel instances)

**Pros:**
- Fastest overall
- Distributes API load
- Can use different API keys if available

**Cons:**
- Most complex
- Requires infrastructure
- Need coordination

---

### Environment Considerations

**Run On:**
- Dedicated server/instance (recommended)
- Background process with tmux/screen
- Scheduled job with auto-resume on failure

**Don't Run On:**
- Local laptop (risk of interruption)
- Shared development environment
- Unstable network connection

**Pre-flight Checklist:**
1. ✅ Verify Supabase storage capacity (need ~1.6 GB)
2. ✅ Confirm API credentials are valid
3. ✅ Test with `--test` mode first
4. ✅ Set up monitoring script
5. ✅ Have rollback plan if needed

---

## Technical Architecture

### Data Flow

```
Racing API (/v1/racecards/pro)
    ↓
RacesFetcher.fetch_and_store()
    ↓
EntityExtractor.extract_and_store_from_runners()
    ├─ Extract entities (jockeys, trainers, owners, horses)
    ├─ Check database for existing horses
    ├─ For NEW horses: Fetch from /v1/horses/{id}/pro
    └─ Store complete data with pedigree
    ↓
Supabase PostgreSQL (UPSERT)
    ├─ ra_mst_races (race metadata)
    ├─ ra_mst_runners (runner data) ← CRITICAL GAP BEING FILLED
    ├─ ra_jockeys (jockeys)
    ├─ ra_trainers (trainers)
    ├─ ra_owners (owners)
    ├─ ra_horses (horses with enrichment)
    └─ ra_horse_pedigree (pedigree data)
```

### Hybrid Enrichment Strategy

The backfill uses the **hybrid enrichment approach**:

1. **Discovery:** Extract basic horse data from racecards
   - Fields: horse_id, name, sex

2. **Check:** Query database for existing horses
   - Compare horse_id against `ra_horses` table

3. **Enrich:** For NEW horses only:
   - Fetch from `/v1/horses/{id}/pro` endpoint
   - Add 9 additional fields: dob, sex_code, colour, colour_code, region
   - Capture complete pedigree: sire, dam, damsire, breeder (with IDs)

4. **Rate Limit:** 0.5 second sleep between Pro endpoint calls (2 req/sec)

**Efficiency:**
- Only new horses are enriched (skips existing)
- Estimated ~30% of horses are new (conservative)
- ~141,912 new horses × 0.5s = ~20 hours for enrichment

---

## API Constraints and Considerations

### Racing API Limits

```
Rate Limit: 2 requests/second (strictly enforced across ALL plan tiers)
Retry Logic: Automatic exponential backoff
Max Retries: 5 attempts per request
Timeout: 30 seconds per request
```

### Endpoint Capabilities

**✅ /v1/racecards/pro**
- Historical data: Back to 2015 ✅
- Returns: Complete race and runner data
- Use: Primary data source for backfill

**❌ /v1/results**
- Historical data: Only last 12 months ❌
- Returns: Race results with positions
- Use: NOT suitable for historical backfill

**✅ /v1/horses/{id}/pro**
- Returns: Complete horse metadata + pedigree
- Use: Enrichment for new horses

### Network Resilience

The script handles:
- Timeouts (auto-retry)
- Rate limits (exponential backoff)
- Network errors (retry with delay)
- API errors (log and continue)
- Connection drops (resume from checkpoint)

---

## Data Quality Assurance

### Validation Queries

After backfill, validate data quality:

```sql
-- 1. Check runner coverage by year
SELECT
  EXTRACT(YEAR FROM r.race_date) as year,
  COUNT(DISTINCT r.race_id) as total_races,
  COUNT(DISTINCT run.race_id) as races_with_runners,
  ROUND(COUNT(DISTINCT run.race_id)::numeric / COUNT(DISTINCT r.race_id)::numeric * 100, 2) as coverage_pct,
  COUNT(run.runner_id) as total_runners,
  ROUND(COUNT(run.runner_id)::numeric / COUNT(DISTINCT r.race_id)::numeric, 1) as avg_runners_per_race
FROM ra_mst_races r
LEFT JOIN ra_mst_runners run ON r.race_id = run.race_id
WHERE r.race_date >= '2015-01-01'
GROUP BY EXTRACT(YEAR FROM r.race_date)
ORDER BY year DESC;

-- 2. Check horse enrichment status
SELECT
  COUNT(*) as total_horses,
  COUNT(dob) as enriched_horses,
  COUNT(*) - COUNT(dob) as not_enriched,
  ROUND(COUNT(dob)::numeric / COUNT(*)::numeric * 100, 2) as enrichment_pct
FROM ra_horses;

-- 3. Check pedigree coverage
SELECT
  COUNT(DISTINCT h.horse_id) as total_horses,
  COUNT(DISTINCT p.horse_id) as horses_with_pedigree,
  ROUND(COUNT(DISTINCT p.horse_id)::numeric / COUNT(DISTINCT h.horse_id)::numeric * 100, 2) as pedigree_coverage_pct
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id;

-- 4. Check entity completeness
SELECT
  'Jockeys' as entity_type,
  COUNT(*) as total_count
FROM ra_jockeys
UNION ALL
SELECT 'Trainers', COUNT(*) FROM ra_trainers
UNION ALL
SELECT 'Owners', COUNT(*) FROM ra_owners
UNION ALL
SELECT 'Horses', COUNT(*) FROM ra_horses
UNION ALL
SELECT 'Pedigrees', COUNT(*) FROM ra_horse_pedigree;

-- 5. Check for orphaned runners (runners without horses)
SELECT COUNT(*)
FROM ra_mst_runners run
LEFT JOIN ra_horses h ON run.horse_id = h.horse_id
WHERE h.horse_id IS NULL;
```

### Expected Results

After successful backfill:

- **Runner coverage:** ~100% (all races should have runners)
- **Avg runners per race:** 8-12 (typical UK/IRE field size)
- **Horse enrichment:** 90%+ (some horses may not exist in Pro endpoint)
- **Pedigree coverage:** 90%+ (matches enrichment rate)
- **No orphaned runners:** All runners should have matching horse records

---

## Troubleshooting

### Common Issues

**1. Checkpoint not saving**
```bash
# Check logs directory exists and is writable
ls -la logs/

# Manual checkpoint verification
cat logs/backfill_all_tables_checkpoint.json | jq .
```

**2. Rate limit errors**
```
Solution: Script auto-retries with exponential backoff
Action: Monitor logs for repeated failures
If persistent: Check API plan tier and request limits
```

**3. Database connection errors**
```bash
# Verify Supabase credentials
echo $SUPABASE_URL
echo $SUPABASE_SERVICE_KEY

# Test connection
python3 -c "from utils.supabase_client import SupabaseReferenceClient; from config.config import get_config; c = get_config(); db = SupabaseReferenceClient(c.supabase.url, c.supabase.service_key); print(db.verify_connection())"
```

**4. Out of memory errors**
```
Solution: Batch size is already optimized (100 records)
Action: If still occurring, reduce batch size in config
```

**5. Duplicate records**
```
Solution: All inserts are UPSERT-based (no duplicates possible)
Action: Verify unique constraints on tables
```

### Recovery Procedures

**If backfill fails mid-run:**

1. **Don't panic** - checkpoint has your progress
2. **Check error log:** `logs/backfill_all_tables_errors.json`
3. **Review checkpoint:** `logs/backfill_all_tables_checkpoint.json`
4. **Resume:** `python3 scripts/backfill_all_ra_tables_2015_2025.py --resume`

**If checkpoint is corrupted:**

1. **Manual recovery:**
```bash
# Check last processed date from database
python3 -c "from utils.supabase_client import SupabaseReferenceClient; from config.config import get_config; c = get_config(); db = SupabaseReferenceClient(c.supabase.url, c.supabase.service_key); result = db.client.table('ra_mst_runners').select('fetched_at').order('fetched_at', desc=True).limit(1).execute(); print(result.data[0]['fetched_at'] if result.data else 'No data')"

# Resume from that date
python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date <LAST_DATE>
```

---

## Performance Optimization

### Already Implemented

- ✅ Batch processing (100 records per batch)
- ✅ UPSERT operations (no duplicate checks needed)
- ✅ Efficient queries (indexed lookups)
- ✅ Rate limiting (prevents API throttling)
- ✅ Checkpoint saving (minimal overhead)

### Further Optimizations (If Needed)

1. **Parallel processing:** Run multiple backfills for different years
2. **Increase batch size:** From 100 to 500 (test first)
3. **Database indexing:** Ensure indexes on race_date, horse_id
4. **Connection pooling:** If experiencing connection limits

---

## Success Criteria

### Backfill Completion Checklist

- [ ] All dates processed (2015-01-01 to present)
- [ ] Runner coverage > 95% (check with validation query)
- [ ] Avg runners per race 8-12 (typical field size)
- [ ] Horse enrichment rate > 90%
- [ ] Pedigree coverage > 90%
- [ ] No orphaned runners
- [ ] Error rate < 1%
- [ ] Checkpoint file shows 100% progress

### Post-Backfill Verification

```bash
# Run comprehensive analysis
python3 scripts/analyze_backfill_requirements.py

# Check validation queries (see Data Quality Assurance section)
# Review results for completeness
```

---

## Maintenance and Future Backfills

### Ongoing Operations

After initial backfill:

**Daily operations (via worker):**
- Fetch today's racecards → captures today's runners
- Enrich new horses automatically
- No manual backfill needed

**Periodic gap fills (if needed):**
```bash
# Fill any missed dates
python3 scripts/backfill_all_ra_tables_2015_2025.py \
  --start-date 2025-01-15 \
  --end-date 2025-01-20
```

### Database Maintenance

**Weekly:**
- Review error logs for patterns
- Validate runner coverage stays high
- Monitor database size growth

**Monthly:**
- Run data quality validation queries
- Archive old logs and checkpoints
- Verify enrichment coverage

---

## Related Documentation

- **API Documentation:** `docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md`
- **Enrichment Strategy:** `docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`
- **Worker System:** `docs/workers/WORKER_UPDATE_REPORT.md`
- **Architecture Overview:** `docs/architecture/START_HERE.md`

---

## Contact and Support

**For issues or questions:**
1. Check error logs: `logs/backfill_all_tables_errors.json`
2. Review this documentation
3. Consult API documentation: `docs/api/`
4. Check Racing API docs: https://www.theracingapi.com/docs

---

## Appendix: Command Reference

### Quick Reference

```bash
# Analysis
python3 scripts/analyze_backfill_requirements.py
python3 scripts/backfill_all_ra_tables_2015_2025.py --analyze

# Testing
python3 scripts/backfill_all_ra_tables_2015_2025.py --test --non-interactive

# Incremental backfill
python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date YYYY-MM-DD --end-date YYYY-MM-DD

# Full backfill
python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date 2015-01-01 --non-interactive

# Resume
python3 scripts/backfill_all_ra_tables_2015_2025.py --resume

# Monitoring
python3 scripts/monitor_backfill.py --interval 60
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-16
**Status:** Production Ready
