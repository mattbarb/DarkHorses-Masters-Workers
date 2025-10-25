# Backfill Timeline Estimates

Detailed time and resource estimates for historical data backfill from 2015 to present.

**Generated:** 2025-10-19
**Coverage:** 2015-01-01 to 2025-10-19 (3,944 days / 131.5 months)

---

## Executive Summary

| Metric | Estimate |
|--------|----------|
| **Total Duration** | **1-2 hours** |
| **Total API Calls** | **~7,891** |
| **Total Days** | **3,944 days** |
| **Monthly Chunks** | **131 months** |
| **Processing Rate** | **2 requests/second** |
| **Database Size** | **~500MB-1GB** (estimated) |

**Key Takeaway:** The full backfill from 2015 to present can be completed in approximately **1-2 hours** using the automated backfill system.

---

## Detailed Breakdown

### Component 1: Master Reference Data

**Tables:**
- ra_mst_bookmakers
- ra_mst_courses
- ra_mst_regions

**Estimates:**
| Metric | Value |
|--------|-------|
| API Calls | 3-5 |
| Duration | ~5 seconds |
| Records | ~120 |

**Details:**
- Bookmakers: 19 records (static list, no API call)
- Courses: ~100 records (1 API call)
- Regions: 2 records (static list, no API call)

---

### Component 2: Event Data (Racecards)

**Tables:**
- ra_races
- ra_runners (partial - pre-race data)

**Estimates:**
| Metric | Value |
|--------|-------|
| API Calls | ~3,944 (1 per day) |
| Duration | ~30-35 minutes |
| Processing Rate | 2 calls/second |
| Race Records | ~140,000 (estimated) |
| Runner Records | ~1,500,000 (estimated) |

**Calculation:**
```
API Calls: 3,944 days × 1 call/day = 3,944 calls
Time: 3,944 calls × 0.5 seconds/call = 1,972 seconds = 32.9 minutes
```

**Monthly Breakdown:**
- 2015: 12 months × ~30 calls = 360 calls (~3 min)
- 2016: 12 months × ~30 calls = 366 calls (~3 min)
- 2017-2024: Similar pattern
- 2025 (partial): 10 months × ~30 calls = 300 calls (~2.5 min)

---

### Component 3: Event Data (Results)

**Tables:**
- ra_runners (complete - post-race data added)

**Estimates:**
| Metric | Value |
|--------|-------|
| API Calls | ~3,944 (1 per day) |
| Duration | ~30-35 minutes |
| Processing Rate | 2 calls/second |
| Runner Updates | ~1,500,000 (estimated) |

**Calculation:**
```
API Calls: 3,944 days × 1 call/day = 3,944 calls
Time: 3,944 calls × 0.5 seconds/call = 1,972 seconds = 32.9 minutes
```

**Note:** Results API uses date ranges, so we fetch results for each day.

---

### Component 4: Entity Extraction (Automatic)

**Tables:**
- ra_mst_horses
- ra_mst_jockeys
- ra_mst_trainers
- ra_mst_owners
- ra_mst_sires
- ra_mst_dams
- ra_mst_damsires
- ra_horse_pedigree

**Estimates:**
| Metric | Value |
|--------|-------|
| API Calls | 0 (extracted from racecards/results) |
| Duration | Included in Components 2 & 3 |
| Horse Records | ~120,000 |
| Jockey Records | ~5,000 |
| Trainer Records | ~4,000 |
| Owner Records | ~60,000 |
| Pedigree Records | ~120,000 |

**Details:**
- Entities extracted during racecard/results processing
- No additional API calls required
- Pedigree data extracted automatically for new horses
- Processing time included in event data fetching

---

## Total Timeline

### Optimistic Scenario (Best Case)

| Component | Duration |
|-----------|----------|
| Masters | 5 seconds |
| Racecards | 30 minutes |
| Results | 30 minutes |
| **Total** | **~60 minutes** |

**Conditions:**
- Optimal network latency
- No API throttling
- Fast database writes
- No errors requiring retries

### Realistic Scenario (Expected)

| Component | Duration |
|-----------|----------|
| Masters | 10 seconds |
| Racecards | 35 minutes |
| Results | 35 minutes |
| Overhead | 10 minutes |
| **Total** | **~80 minutes (1.3 hours)** |

**Conditions:**
- Normal network latency
- Occasional API delays
- Standard database performance
- Some retries for transient errors

### Pessimistic Scenario (Worst Case)

| Component | Duration |
|-----------|----------|
| Masters | 30 seconds |
| Racecards | 45 minutes |
| Results | 45 minutes |
| Retries/Errors | 20 minutes |
| **Total** | **~110 minutes (1.8 hours)** |

**Conditions:**
- Higher network latency
- API rate limiting kicks in
- Slower database writes
- Multiple retries needed

---

## Processing Rate Details

### API Rate Limit

**Racing API:** 2 requests per second (across all plan tiers)

**Implementation:**
```python
# API client enforces rate limit
min_request_interval = 1.0 / 2  # 0.5 seconds between calls
time.sleep(0.5)  # Between each API call
```

### Database Write Performance

**Batch Processing:**
- Default batch size: 100 records
- UPSERT operation (insert or update on conflict)
- Optimized for Supabase PostgreSQL

**Estimated Rates:**
| Operation | Rate |
|-----------|------|
| Race inserts | ~1,000/minute |
| Runner inserts | ~10,000/minute |
| Entity inserts | ~5,000/minute |

---

## Resource Requirements

### API Calls

**Total API Calls: ~7,891**

| Component | Calls | Percentage |
|-----------|-------|------------|
| Racecards | 3,944 | 50% |
| Results | 3,944 | 50% |
| Masters | 3 | <0.1% |
| **Total** | **7,891** | **100%** |

**Daily Rate Limits:**
- Most API plans: Unlimited daily calls (rate limited only)
- Racing API Pro: Includes historical data access

### Network Bandwidth

**Estimated Data Transfer:**
| Direction | Volume |
|-----------|--------|
| Downloaded (from API) | ~500MB - 1GB |
| Uploaded (to Supabase) | ~300MB - 600MB |
| **Total** | **~800MB - 1.6GB** |

**Assumptions:**
- Average API response: ~100-200KB per day
- Database records: ~100-200 bytes per runner

### Disk Space

**Logs:**
- Main log: ~50-100MB
- Checkpoint: ~1MB
- Error log: <1MB
- **Total:** ~52-102MB

**Database (Supabase):**
- Races: ~50MB
- Runners: ~300MB
- Entities: ~50MB
- Pedigree: ~20MB
- **Total:** ~420MB

---

## Checkpoint Intervals

**Monthly Chunks:**
- Total: 131 chunks
- Duration per chunk: ~40 seconds
- Checkpoint saved after each chunk

**Progress Tracking:**
```
Chunk 1/131: 2015-01-01 to 2015-01-31 (0.8% complete)
Chunk 50/131: 2019-02-01 to 2019-02-28 (38.2% complete)
Chunk 100/131: 2023-04-01 to 2023-04-30 (76.3% complete)
Chunk 131/131: 2025-10-01 to 2025-10-19 (100% complete)
```

---

## Incremental Updates (After Initial Backfill)

### Daily Updates

**New data each day:**
- API Calls: 2 (1 racecard, 1 result)
- Duration: ~2 seconds
- Records: ~30 races, ~300 runners

**Schedule:**
```bash
# Daily cron job
0 6 * * * python3 /path/to/scripts/backfill_events.py --start-date $(date -d "yesterday" +\%Y-\%m-\%d)
```

### Weekly Catch-up

**7 days of data:**
- API Calls: 14
- Duration: ~10 seconds
- Records: ~200 races, ~2,000 runners

### Monthly Catch-up

**30 days of data:**
- API Calls: 60
- Duration: ~35 seconds
- Records: ~900 races, ~9,000 runners

---

## Failure Recovery

### Checkpoint Resume

**If interrupted at 50% (Chunk 66):**
- Already processed: 66 chunks (~40 minutes)
- Remaining: 65 chunks (~40 minutes)
- Resume time: ~40 minutes (not 80 minutes)

**Checkpoint contains:**
- Last completed chunk
- Total progress statistics
- Timestamp

### Error Retry

**Automatic retry logic:**
- Max retries: 5 per request
- Backoff: Exponential (2, 4, 8, 16, 32 seconds)
- Total retry time: ~60 seconds per failed request

**Error scenarios:**
| Error Type | Frequency | Impact |
|------------|-----------|--------|
| Transient network | ~1-2% | Auto-retry |
| Rate limit (429) | Rare | Auto-backoff |
| No data (404) | ~10-15% | Normal, logged |
| Authentication (401) | Fatal | Stops backfill |

---

## Comparison: Manual vs Automated

### Manual Approach (Without Backfill System)

**Estimated effort:**
- Planning: 2-4 hours
- Script development: 8-16 hours
- Testing: 2-4 hours
- Execution monitoring: 2-4 hours
- Error handling: 2-8 hours
- **Total:** 16-36 hours of developer time

### Automated Backfill System (This Implementation)

**Effort:**
- Setup: 5 minutes (environment variables)
- Execution: 1-2 hours (unattended)
- Verification: 10 minutes
- **Total:** ~15 minutes of developer time

**Time saved:** 15-35 hours

---

## Recommendations

### For Initial Backfill

1. **Check status first:**
   ```bash
   python3 scripts/backfill_events.py --check-status --start-date 2015-01-01
   ```

2. **Run in background session:**
   ```bash
   screen -S backfill
   python3 scripts/backfill_all.py --start-date 2015-01-01
   # Detach: Ctrl+A, D
   ```

3. **Monitor progress:**
   ```bash
   tail -f logs/backfill_events_*.log
   cat logs/backfill_events_checkpoint.json
   ```

4. **Allow 2-3 hours buffer** (for pessimistic scenario)

### For Production Deployment

1. **Initial backfill:** Run once with `--start-date 2015-01-01`
2. **Daily updates:** Cron job for yesterday's data
3. **Weekly verification:** Check data consistency
4. **Monthly catch-up:** Fill any gaps from daily runs

### For Development/Testing

1. **Test with small range first:**
   ```bash
   python3 scripts/backfill_events.py --start-date 2024-10-01 --end-date 2024-10-07
   ```

2. **Verify in database:**
   ```sql
   SELECT COUNT(*) FROM ra_races WHERE date >= '2024-10-01';
   ```

3. **Check checkpoint/resume:**
   - Interrupt with Ctrl+C
   - Resume with `--resume`
   - Verify no duplicates

---

## Conclusion

The automated backfill system provides:

**Efficiency:**
- Complete backfill in 1-2 hours (unattended)
- Saves 15-35 hours of developer time vs manual approach

**Reliability:**
- Automatic checkpoint/resume capability
- Built-in error handling and retry logic
- No data loss on interruption

**Maintainability:**
- Easy incremental updates (daily/weekly)
- Clear progress tracking
- Comprehensive logging

**Production Ready:**
- Handles rate limits automatically
- Respects API best practices
- Database-safe (UPSERT operations)

---

**For detailed usage instructions, see:** `docs/BACKFILL_GUIDE.md`
