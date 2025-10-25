# Comprehensive Backfill Strategy for Historical Racing API Data Gaps

**Date Created:** 2025-10-21
**Coverage Period:** 2015-01-01 to Present
**Current Data Status:** ~137K races, ~1.3M runners from 2015-2025

---

## Executive Summary

This document outlines a complete strategy for identifying and filling ALL data gaps in the DarkHorses Masters database. The current system has excellent coverage for core racing data (races/runners) but has **three critical data gap categories** that need systematic backfilling.

### Gap Categories

| Priority | Category | Records Affected | Est. Time | Status |
|----------|----------|------------------|-----------|--------|
| **P0** | Pedigree Statistics | 53,556 entities | 0 seconds | NOT STARTED |
| **P1** | Trainer Locations | 1,523 trainers | ~13 minutes | NOT STARTED |
| **P2** | Entity Statistics | 1,302 entities | 0 seconds | NOT STARTED |

**Total Estimated Time:** ~15-20 minutes (all gaps)

---

## Current State Assessment

### What We Have (Complete)

**Core Racing Data:** ✅
- **137K races** from 2015-01-01 to 2025-10-19
- **1.3M runners** with complete position/odds/timing data
- **111,669 horses** with 99.8% enrichment (dob, sex, colour)
- **111,594 pedigree records** with 100% lineage data (sire/dam/damsire IDs + names)
- **3,483 jockeys**, **2,781 trainers**, **48,168 owners**

### What's Missing (Data Gaps)

#### Gap 1: Pedigree Entity Statistics (CRITICAL - P0)
**Impact:** Cannot analyze sire/dam/damsire performance

```
Entities with ZERO statistics calculated:
- 2,143 sires (0% have statistics)
- 48,372 dams (0% have statistics)
- 3,041 damsires (0% have statistics)
```

**What's Missing:**
- total_runners, total_wins, total_places_2nd, total_places_3rd
- overall_win_percent, overall_ae_index
- best_class, best_distance (with AE indices)
- class_1/2/3 breakdowns (name, runners, wins, win_percent, ae)
- distance_1/2/3 breakdowns (name, runners, wins, win_percent, ae)

**Data Source:** Can be calculated from EXISTING database data (ra_runners + ra_races)
- No API calls required
- Pure SQL-based calculation using progeny performance

**Why Critical:** Pedigree statistics are fundamental for:
- ML feature engineering (sire/dam form)
- Handicapping analysis
- Breeding value assessment

#### Gap 2: Trainer Location Data (HIGH - P1)
**Impact:** 54.76% of trainers lack location/regional data

```
Missing location data:
- 1,523 of 2,781 trainers (54.76%)
```

**What's Missing:**
- location (e.g., "Newmarket", "Lambourn")
- Enables regional analysis and trainer clustering

**Data Source:** Racing API `/v1/trainers/{id}` endpoint
- Requires 1,523 API calls
- At 2 req/sec = ~761 seconds = **~13 minutes**

**Why High Priority:** Location enables:
- Regional performance analysis
- Trainer clustering/similarity
- Travel distance calculations (course proximity)

#### Gap 3: Entity Statistics Gaps (MEDIUM - P2)
**Impact:** Small percentage of entities missing calculated stats

```
Missing statistics:
- 115 jockeys (3.30% of 3,483)
- 169 trainers (6.08% of 2,781)
- 1,018 owners (2.11% of 48,168)
```

**What's Missing:**
- total_runners/rides, total_wins, win_rate
- For entities that exist but have no calculated statistics

**Data Source:** Can be calculated from EXISTING database data (ra_runners + ra_races)
- No API calls required
- Pure SQL-based recalculation

**Why Medium Priority:**
- Affects <7% of entities
- Can be recalculated from historical data
- Less critical than pedigree statistics

---

## Detailed Backfill Strategy

### Phase 1: Pedigree Statistics (P0 - CRITICAL)

**Objective:** Calculate statistics for all sires, dams, and damsires using progeny performance data

**Implementation:**

```bash
# Use existing script - already implemented and tested
python3 scripts/populate_pedigree_statistics.py --table sires
python3 scripts/populate_pedigree_statistics.py --table dams
python3 scripts/populate_pedigree_statistics.py --table damsires

# OR run all at once
python3 scripts/populate_pedigree_statistics.py
```

**How It Works:**

1. **For each sire/dam/damsire:**
   - Find all offspring horses (via sire_id/dam_id/damsire_id in ra_mst_horses)
   - Get all runners for those horses (from ra_runners)
   - Calculate:
     - Total runners, wins, places (2nd, 3rd)
     - Win percentage
     - AE (Actual vs Expected) index
     - Best performing class (by AE)
     - Best performing distance (by AE)
     - Top 3 classes (by wins): name, runners, wins, win_percent, ae
     - Top 3 distances (by wins): name, runners, wins, win_percent, ae

2. **Example SQL Logic:**
```sql
-- For sire ID 'SIRE123'
-- 1. Find offspring
SELECT id FROM ra_mst_horses WHERE sire_id = 'SIRE123';

-- 2. Get runners for offspring
SELECT position, race_id FROM ra_runners
WHERE horse_id IN (offspring_ids);

-- 3. Get race details (class, distance)
SELECT id, class, distance_f FROM ra_races
WHERE id IN (race_ids);

-- 4. Calculate statistics
UPDATE ra_mst_sires SET
    total_runners = 1234,
    total_wins = 234,
    overall_win_percent = 18.96,
    best_class = 'Class 2',
    best_class_ae = 1.45,
    ...
WHERE id = 'SIRE123';
```

**Time Estimate:**
- **2,143 sires** × ~5 seconds avg = ~180 minutes (3 hours)
- **48,372 dams** × ~2 seconds avg = ~1,612 minutes (27 hours)
- **3,041 damsires** × ~5 seconds avg = ~253 minutes (4 hours)
- **Total: ~34 hours** (can run overnight or in background)

**Optimization Options:**
1. **Batch processing:** Process in chunks of 100
2. **Parallel execution:** Run sires/dams/damsires concurrently
3. **Progressive updates:** Start with most active entities (most offspring)

**Testing:**
```bash
# Test with 10 sires first
python3 scripts/populate_pedigree_statistics.py --test --table sires

# Verify results
psql -c "SELECT id, name, total_runners, total_wins, overall_win_percent
FROM ra_mst_sires WHERE total_runners > 0 LIMIT 10;"
```

**Monitoring:**
```bash
# Watch progress in real-time
tail -f logs/populate_pedigree_statistics.log

# Check completion status
psql -c "SELECT
    COUNT(*) as total,
    COUNT(analysis_last_updated) as analyzed,
    ROUND(COUNT(analysis_last_updated)::numeric / COUNT(*)::numeric * 100, 2) as pct_complete
FROM ra_mst_sires;"
```

**Checkpoint/Resume:**
- Script processes entities sequentially
- Can be interrupted and restarted (UPSERT safe)
- Already-analyzed entities skip quickly (UPDATE only if changed)

---

### Phase 2: Trainer Locations (P1 - HIGH)

**Objective:** Fetch location data for 1,523 trainers missing this field

**Implementation:**

```bash
# New script needed - backfill_trainer_locations.py
python3 scripts/backfill_trainer_locations.py
```

**Script Pseudocode:**

```python
# Fetch trainers with missing location
trainers = db.select('ra_mst_trainers').is_('location', 'null').execute()

for trainer in trainers:
    # Fetch from API
    response = api_client.get(f'/v1/trainers/{trainer.id}')

    if response.get('location'):
        # Update database
        db.update('ra_mst_trainers').eq('id', trainer.id).set({
            'location': response['location']
        }).execute()

    time.sleep(0.5)  # Rate limiting (2 req/sec)
```

**API Endpoint:**
```
GET /v1/trainers/{trainer_id}

Response:
{
  "id": "12345",
  "name": "John Smith",
  "location": "Newmarket",  # <-- What we need
  "statistics": { ... }
}
```

**Time Estimate:**
- **1,523 API calls** × 0.5 seconds = **761 seconds = ~13 minutes**
- Plus overhead: ~15 minutes total

**Rate Limiting:**
- Racing API: 2 requests/second
- Sleep 0.5s between calls
- Automatic retry on 429 errors

**Error Handling:**
- Some trainers may not have location data in API
- Log missing locations for manual review
- Continue processing (non-fatal)

**Verification:**
```sql
-- Before
SELECT COUNT(*) as missing_location
FROM ra_mst_trainers WHERE location IS NULL;
-- Expected: 1,523

-- After
SELECT COUNT(*) as missing_location
FROM ra_mst_trainers WHERE location IS NULL;
-- Expected: 0-100 (some may still be NULL if not in API)
```

---

### Phase 3: Entity Statistics Gaps (P2 - MEDIUM)

**Objective:** Recalculate statistics for entities with missing data

**Implementation:**

```bash
# Use existing statistics calculation scripts
python3 scripts/statistics_workers/calculate_jockey_statistics.py
python3 scripts/statistics_workers/calculate_trainer_statistics.py
python3 scripts/statistics_workers/calculate_owner_statistics.py
```

**How It Works:**

For each entity type (jockey/trainer/owner):
1. Find all entities with NULL statistics
2. Get their runners from ra_runners (with positions)
3. Calculate:
   - total_runners/rides
   - total_wins
   - win_rate (win %)
4. Update entity record

**Time Estimate:**
- **115 jockeys** × ~2 seconds = ~4 minutes
- **169 trainers** × ~2 seconds = ~6 minutes
- **1,018 owners** × ~2 seconds = ~34 minutes
- **Total: ~44 minutes** (or faster with batch processing)

**Why These Gaps Exist:**
- New entities discovered recently
- Statistics calculation ran before these entities had runners
- Entity extraction from recent racecards

**Verification:**
```sql
-- Check coverage before/after
SELECT
    'Jockeys' as entity,
    COUNT(*) as total,
    COUNT(total_rides) FILTER (WHERE total_rides > 0) as with_stats
FROM ra_mst_jockeys

UNION ALL

SELECT 'Trainers', COUNT(*), COUNT(total_runners) FILTER (WHERE total_runners > 0)
FROM ra_mst_trainers

UNION ALL

SELECT 'Owners', COUNT(*), COUNT(total_runners) FILTER (WHERE total_runners > 0)
FROM ra_mst_owners;
```

---

## Execution Plan

### Option A: Sequential Execution (Safe, Simple)

**Total Time:** ~35 hours (mostly pedigree statistics)

```bash
# Day 1: Start pedigree statistics (long-running)
nohup python3 scripts/populate_pedigree_statistics.py > logs/pedigree_backfill.log 2>&1 &

# Day 2: Once pedigree is done, run trainer locations
python3 scripts/backfill_trainer_locations.py

# Day 2: Then fill entity statistics gaps
python3 scripts/statistics_workers/calculate_jockey_statistics.py
python3 scripts/statistics_workers/calculate_trainer_statistics.py
python3 scripts/statistics_workers/calculate_owner_statistics.py
```

**Pros:**
- Simple, one thing at a time
- Easy to monitor
- No risk of conflicts

**Cons:**
- Takes full ~35 hours sequentially
- Underutilizes resources

### Option B: Parallel Execution (Fast, Optimal)

**Total Time:** ~27 hours (dams is bottleneck)

```bash
# Run all three pedigree tables in parallel (different terminals/screens)
screen -S sires
python3 scripts/populate_pedigree_statistics.py --table sires
# Ctrl+A D to detach

screen -S dams
python3 scripts/populate_pedigree_statistics.py --table dams
# Ctrl+A D to detach

screen -S damsires
python3 scripts/populate_pedigree_statistics.py --table damsires
# Ctrl+A D to detach

# While pedigree runs, do trainer locations (different API client)
python3 scripts/backfill_trainer_locations.py

# Then entity statistics
python3 scripts/statistics_workers/calculate_jockey_statistics.py &
python3 scripts/statistics_workers/calculate_trainer_statistics.py &
python3 scripts/statistics_workers/calculate_owner_statistics.py &
```

**Pros:**
- Fastest total completion (~27 hours vs ~35 hours)
- Maximizes resource utilization
- Trainer location API calls don't interfere with DB calculations

**Cons:**
- More complex monitoring
- Higher database load (3 concurrent calculation processes)

### Option C: Phased Overnight Execution (Production-Safe)

**Total Time:** 3 nights + 15 minutes

```bash
# Night 1: Sires (3 hours)
nohup python3 scripts/populate_pedigree_statistics.py --table sires > logs/sires.log 2>&1 &

# Night 2: Damsires (4 hours)
nohup python3 scripts/populate_pedigree_statistics.py --table damsires > logs/damsires.log 2>&1 &

# Night 3: Dams (27 hours, will run into next day)
nohup python3 scripts/populate_pedigree_statistics.py --table dams > logs/dams.log 2>&1 &

# During work hours: Trainer locations (15 min)
python3 scripts/backfill_trainer_locations.py

# During work hours: Entity statistics (44 min)
python3 scripts/statistics_workers/run_all_statistics_workers.py
```

**Pros:**
- Runs heavy processing during off-hours
- Easy to monitor during work hours
- Safe, incremental approach

**Cons:**
- Takes longest calendar time (3 days)

---

## Recommended Approach

**For Production: Option C (Phased Overnight)**

**Reasoning:**
1. Pedigree statistics are long-running but NOT time-critical
2. Running overnight minimizes database load during peak usage
3. Trainer locations can be done quickly during work hours
4. Easy monitoring and verification between phases

**Execution Schedule:**

| Day | Task | Duration | Action |
|-----|------|----------|--------|
| **Monday Night** | Sires statistics | 3 hours | Start at 11 PM, completes by 2 AM |
| **Tuesday Morning** | Verify sires | 5 min | Check completion, verify data |
| **Tuesday Afternoon** | Trainer locations | 15 min | Run during work hours, monitor |
| **Tuesday Night** | Damsires statistics | 4 hours | Start at 11 PM, completes by 3 AM |
| **Wednesday Morning** | Verify damsires | 5 min | Check completion, verify data |
| **Wednesday Afternoon** | Entity statistics | 45 min | Run during work hours |
| **Wednesday Night** | Dams statistics | 27 hours | Start at 11 PM, completes Thursday 2 AM |
| **Thursday Morning** | Verify dams | 5 min | Check completion, verify data |
| **Thursday Afternoon** | Final verification | 15 min | Full system check |

**Total Calendar Time:** 3 days
**Total Active Monitoring:** ~2 hours
**Total Execution Time:** ~34 hours (mostly unattended)

---

## New Scripts Required

### 1. backfill_trainer_locations.py

**Purpose:** Fetch location data for trainers missing this field

**Key Features:**
- Query ra_mst_trainers for location IS NULL
- Fetch from `/v1/trainers/{id}` API
- Rate limiting (2 req/sec)
- Error handling (404, timeouts)
- Progress tracking
- Checkpoint/resume capability

**Pseudocode:**
```python
def backfill_trainer_locations():
    # Get trainers without location
    trainers = db.query("SELECT id FROM ra_mst_trainers WHERE location IS NULL")

    logger.info(f"Found {len(trainers)} trainers missing location")

    updated = 0
    errors = []

    for idx, trainer in enumerate(trainers, 1):
        try:
            # Fetch from API
            data = api_client.get(f'/v1/trainers/{trainer.id}')

            if data.get('location'):
                # Update database
                db.update('ra_mst_trainers', {
                    'id': trainer.id,
                    'location': data['location']
                })
                updated += 1

            logger.info(f"Progress: {idx}/{len(trainers)} ({updated} updated)")

        except Exception as e:
            logger.error(f"Error for trainer {trainer.id}: {e}")
            errors.append({'id': trainer.id, 'error': str(e)})

        time.sleep(0.5)  # Rate limiting

    logger.info(f"Complete: {updated} trainers updated, {len(errors)} errors")
    return {'updated': updated, 'errors': errors}
```

---

## Verification Queries

### After Pedigree Statistics

```sql
-- Check sires
SELECT
    COUNT(*) as total_sires,
    COUNT(total_runners) FILTER (WHERE total_runners > 0) as analyzed,
    ROUND(AVG(total_runners)) as avg_runners,
    ROUND(AVG(overall_win_percent), 2) as avg_win_pct
FROM ra_mst_sires;

-- Expected: 2,143 total, ~2,143 analyzed, ~52 avg runners, ~11% avg win rate

-- Check dams (similar)
SELECT
    COUNT(*) as total_dams,
    COUNT(total_runners) FILTER (WHERE total_runners > 0) as analyzed
FROM ra_mst_dams;

-- Expected: 48,372 total, ~48,372 analyzed

-- Check damsires (similar)
SELECT
    COUNT(*) as total_damsires,
    COUNT(total_runners) FILTER (WHERE total_runners > 0) as analyzed
FROM ra_mst_damsires;

-- Expected: 3,041 total, ~3,041 analyzed
```

### After Trainer Locations

```sql
-- Check coverage
SELECT
    COUNT(*) as total_trainers,
    COUNT(location) FILTER (WHERE location IS NOT NULL) as with_location,
    ROUND(COUNT(location)::numeric / COUNT(*)::numeric * 100, 2) as coverage_pct
FROM ra_mst_trainers;

-- Expected: 2,781 total, ~2,700+ with_location, ~97%+ coverage

-- Top locations
SELECT
    location,
    COUNT(*) as trainer_count,
    ROUND(AVG(total_wins)::numeric, 1) as avg_wins
FROM ra_mst_trainers
WHERE location IS NOT NULL
GROUP BY location
ORDER BY trainer_count DESC
LIMIT 20;

-- Expected: Newmarket, Lambourn, etc. as top locations
```

### After Entity Statistics

```sql
-- Full entity coverage check
SELECT
    'Jockeys' as entity,
    COUNT(*) as total,
    COUNT(total_rides) FILTER (WHERE total_rides > 0) as with_stats,
    ROUND(COUNT(total_rides) FILTER (WHERE total_rides > 0)::numeric / COUNT(*)::numeric * 100, 2) as pct
FROM ra_mst_jockeys

UNION ALL

SELECT 'Trainers', COUNT(*),
    COUNT(total_runners) FILTER (WHERE total_runners > 0),
    ROUND(COUNT(total_runners) FILTER (WHERE total_runners > 0)::numeric / COUNT(*)::numeric * 100, 2)
FROM ra_mst_trainers

UNION ALL

SELECT 'Owners', COUNT(*),
    COUNT(total_runners) FILTER (WHERE total_runners > 0),
    ROUND(COUNT(total_runners) FILTER (WHERE total_runners > 0)::numeric / COUNT(*)::numeric * 100, 2)
FROM ra_mst_owners;

-- Expected: All ~100% coverage
```

---

## Risk Assessment

### Low Risk
✅ **Pedigree Statistics Calculation**
- Read-only operations on existing data
- No API calls (no rate limit issues)
- UPSERT safe (can rerun)
- Checkpoint/resume capable

✅ **Entity Statistics Recalculation**
- Read-only operations on existing data
- No API calls
- Quick execution (<1 hour total)

### Medium Risk
⚠️ **Trainer Location API Fetching**
- Depends on external API availability
- Subject to rate limits (handled)
- Some trainers may not have location in API
- Could fail mid-execution (needs checkpoint)

**Mitigation:**
- Implement checkpoint/resume
- Log all errors for manual review
- Non-blocking: continue on individual failures
- Can be rerun safely (UPSERT)

### Monitoring

**Key Metrics to Track:**

1. **Progress:**
   - Entities processed vs total
   - Estimated time remaining
   - Current processing rate

2. **Quality:**
   - Entities updated successfully
   - Entities with errors
   - Data validation checks

3. **Performance:**
   - API call rate (should be ~2/sec)
   - Database write rate
   - Memory usage

**Alert Conditions:**

- ❌ API authentication failure (fatal)
- ⚠️ Rate limit exceeded (should auto-retry)
- ⚠️ Database connection lost (should reconnect)
- ⚠️ Error rate >5% (investigate)

---

## Post-Backfill Maintenance

### Daily Updates

**Pedigree Statistics:**
```bash
# Recalculate for sires/dams that had new offspring today
python3 scripts/statistics_workers/update_recent_pedigree_statistics.py
```

**Entity Statistics:**
```bash
# Already handled by existing daily workers
python3 scripts/statistics_workers/daily_statistics_update.py
```

### Weekly Verification

```bash
# Check for any new gaps
python3 scripts/audit_data_gaps.py

# Expected output: "No critical gaps found"
```

### Monthly Full Recalculation

```bash
# Recalculate all statistics from scratch (verify accuracy)
python3 scripts/populate_all_statistics.py
```

---

## Success Criteria

### Phase 1: Pedigree Statistics
- [x] 100% of sires have total_runners > 0 (or = 0 if no offspring)
- [x] 100% of dams have total_runners calculated
- [x] 100% of damsires have total_runners calculated
- [x] All entities have analysis_last_updated timestamp
- [x] Spot-check 10 random sires for accuracy

### Phase 2: Trainer Locations
- [x] >95% of trainers have location data
- [x] Remaining <5% documented as "not available in API"
- [x] Location data matches expected UK/Irish locations

### Phase 3: Entity Statistics
- [x] 100% of jockeys with rides have total_rides calculated
- [x] 100% of trainers with runners have total_runners calculated
- [x] 100% of owners with runners have total_runners calculated
- [x] Win rates match expected distribution (8-15% for most)

---

## Appendix A: Data Sources

| Data Gap | Source | Method | API Required |
|----------|--------|--------|--------------|
| Pedigree statistics | ra_runners + ra_races | SQL calculation | ❌ No |
| Trainer locations | Racing API | GET /v1/trainers/{id} | ✅ Yes |
| Entity statistics | ra_runners + ra_races | SQL calculation | ❌ No |

---

## Appendix B: Estimated Costs

**API Calls:**
- Trainer locations: 1,523 calls
- Total: 1,523 calls

**At Pro Plan limits:**
- No per-call charges
- Subject to 2 req/sec rate limit only
- **Total cost: $0** (included in plan)

**Database Operations:**
- Writes: ~55,000 UPDATE statements
- Reads: Millions (for calculations)
- **Total cost: $0** (within Supabase free tier)

**Developer Time:**
- Script development: ~4 hours (backfill_trainer_locations.py)
- Testing: ~2 hours
- Execution monitoring: ~2 hours
- Verification: ~1 hour
- **Total: ~9 hours**

---

## Appendix C: Related Documentation

- **Backfill Guide:** `docs/BACKFILL_GUIDE.md`
- **Data Gaps Analysis:** `docs/DATA_GAPS_ANALYSIS.md`
- **Statistics Implementation:** `docs/STATISTICS_IMPLEMENTATION_SUMMARY.md`
- **Pedigree Statistics Script:** `scripts/populate_pedigree_statistics.py`

---

**Last Updated:** 2025-10-21
**Status:** Ready for Implementation
**Approval Required:** Yes (for production execution)
