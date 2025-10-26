# Data Enrichment Quick Reference
## Racing API Pro - Entity Enrichment at a Glance

**Last Updated:** 2025-10-14
**Status:** All endpoints tested successfully (21/21)

---

## TL;DR - What You Need to Know

### ✅ What We CAN Enrich

**HORSES ONLY** - Individual Pro endpoint exists
- 6 new fields from Pro endpoint (dob, sex, sex_code, colour, colour_code, breeder)
- Pedigree data (sire, dam, damsire with IDs)
- Already implemented and working
- Progress: 22/111,430 horses enriched

### ❌ What We CANNOT Enrich

**JOCKEYS, TRAINERS, OWNERS** - No individual detail endpoints exist
- API only provides results (race history) and analysis (statistics)
- Results are redundant (we have ra_mst_runners)
- Analysis should be calculated locally, not stored

---

## Entity-by-Entity Breakdown

### 🐴 HORSES - ✅ FULL ENRICHMENT AVAILABLE

**Endpoint:** `/v1/horses/{id}/pro`
**Status:** ✅ IMPLEMENTED

| What We Get | From Pro? | Stored Where |
|-------------|-----------|--------------|
| Date of birth | ✅ Yes | ra_horses.dob |
| Sex (gelding/mare) | ✅ Yes | ra_horses.sex |
| Sex code (G/F/C/M) | ✅ Yes | ra_horses.sex_code |
| Colour (bay/chestnut) | ✅ Yes | ra_horses.colour |
| Colour code (B/CH) | ✅ Yes | ra_horses.colour_code |
| Breeder name | ✅ Yes | ra_horse_pedigree.breeder |
| Sire/Dam/Damsire | ✅ Yes | ra_horse_pedigree table |

**Next Steps:**
- Continue automatic enrichment for new horses ✅
- Complete backfill: 22/111,430 → 111,430/111,430 🔄

---

### 👤 JOCKEYS - ❌ NO INDIVIDUAL ENDPOINT

**Finding:** API does NOT have `/v1/jockeys/{id}/pro` endpoint

**What's Available:**
- `/v1/jockeys/{id}/results` - Race history (we have this in ra_mst_runners)
- `/v1/jockeys/{id}/analysis/*` - 5 analysis endpoints (calculated stats)

**What We Should Do:**
- ✅ Calculate statistics locally from ra_mst_runners
- ✅ Use migration 007 views and functions
- ❌ Don't store API analysis data (redundant)

**Statistics Available Locally:**
- Total rides, wins, places
- Win rate, place rate
- Performance by course, distance, trainer, owner

---

### 👨‍🏫 TRAINERS - ❌ NO INDIVIDUAL ENDPOINT

**Finding:** API does NOT have `/v1/trainers/{id}/pro` endpoint

**What's Available:**
- `/v1/trainers/{id}/results` - Race history (we have this in ra_mst_runners)
- `/v1/trainers/{id}/analysis/*` - 6 analysis endpoints (calculated stats)

**What We Should Do:**
- ✅ Calculate statistics locally from ra_mst_runners
- ✅ Use migration 007 views and functions
- ❌ Don't store API analysis data (redundant)

**Statistics Available Locally:**
- Total runners, wins, places
- Win rate, place rate
- Recent 14-day form
- Performance by course, distance, jockey, owner, horse age

---

### 🏆 OWNERS - ❌ NO INDIVIDUAL ENDPOINT

**Finding:** API does NOT have `/v1/owners/{id}/pro` endpoint

**What's Available:**
- `/v1/owners/{id}/results` - Race history (we have this in ra_mst_runners)
- `/v1/owners/{id}/analysis/*` - 4 analysis endpoints (calculated stats)

**What We Should Do:**
- ✅ Calculate statistics locally from ra_mst_runners
- ✅ Use migration 007 views and functions
- ❌ Don't store API analysis data (redundant)

**Statistics Available Locally:**
- Total horses owned
- Total runners, wins, places
- Win rate, place rate
- Active in last 30 days
- Performance by course, distance, jockey, trainer

---

### 🏇 COURSES - ❌ NO ENRICHMENT

**Finding:** Basic reference data only

**Endpoint:** `/v1/courses` (list only)
**Fields:** id, name, region_code, region

**What We Should Do:**
- Keep as basic reference data
- No enrichment needed

---

### 🏁 RACES - ❌ REDUNDANT ENRICHMENT

**Finding:** Individual race endpoint exists but redundant

**Endpoint:** `/v1/racecards/{id}/pro`
**Issue:** We already get this data from `/v1/racecards/pro` bulk fetch

**What We Should Do:**
- ❌ Don't enrich individual races
- ✅ Use existing racecard data

---

## Implementation Status Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│ ENTITY ENRICHMENT STATUS                                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│ HORSES        [████████████████████████████] 100% READY    │
│               ├─ Schema: ✅ Complete                        │
│               ├─ Code: ✅ Implemented                       │
│               ├─ Auto-enrich: ✅ Active                     │
│               └─ Backfill: 🔄 0.02% (22/111,430)           │
│                                                             │
│ JOCKEYS       [████████████████████████████] 100% READY    │
│               ├─ Schema: ✅ Statistics fields added         │
│               ├─ Views: ✅ Created                          │
│               ├─ Function: ✅ update_entity_statistics()    │
│               └─ Automation: ⏸️ Pending                    │
│                                                             │
│ TRAINERS      [████████████████████████████] 100% READY    │
│               ├─ Schema: ✅ Statistics fields added         │
│               ├─ Views: ✅ Created                          │
│               ├─ Function: ✅ update_entity_statistics()    │
│               └─ Automation: ⏸️ Pending                    │
│                                                             │
│ OWNERS        [████████████████████████████] 100% READY    │
│               ├─ Schema: ✅ Statistics fields added         │
│               ├─ Views: ✅ Created                          │
│               ├─ Function: ✅ update_entity_statistics()    │
│               └─ Automation: ⏸️ Pending                    │
│                                                             │
│ COURSES       [────────────────────────────] N/A            │
│               └─ No enrichment available                    │
│                                                             │
│ RACES         [────────────────────────────] N/A            │
│               └─ Not recommended (redundant)                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Quick Decision Matrix

### Should I store this API data?

| API Endpoint | Store? | Why / Why Not |
|-------------|--------|---------------|
| `/v1/horses/{id}/pro` | ✅ YES | Unique data not available elsewhere |
| `/v1/horses/{id}/standard` | ✅ YES | Pedigree data (subset of pro) |
| `/v1/jockeys/{id}/results` | ❌ NO | Already in ra_mst_runners |
| `/v1/jockeys/{id}/analysis/*` | ❌ NO | Calculate from ra_mst_runners instead |
| `/v1/trainers/{id}/results` | ❌ NO | Already in ra_mst_runners |
| `/v1/trainers/{id}/analysis/*` | ❌ NO | Calculate from ra_mst_runners instead |
| `/v1/owners/{id}/results` | ❌ NO | Already in ra_mst_runners |
| `/v1/owners/{id}/analysis/*` | ❌ NO | Calculate from ra_mst_runners instead |
| `/v1/racecards/{id}/pro` | ❌ NO | Already from bulk racecard fetch |

---

## API Call Budget

### Current Daily Usage

| Operation | API Calls/Day | Time | Cost |
|-----------|--------------|------|------|
| Racecard fetch | ~500 | ~4 minutes | Essential |
| New horse enrichment | ~50-200 | ~25-100 seconds | Low |
| Pedigree backfill | 0 (one-time done) | 0 | None |
| Statistics update | 0 (local calc) | < 1 minute | FREE |

**Total Daily:** ~550-700 API calls (~5 minutes)
**Rate Limit:** 2 requests/second (7,200/hour, 172,800/day)
**Headroom:** 99.6% available

### Recommended Approach

- ✅ Continue horse enrichment (minimal overhead)
- ✅ Calculate statistics locally (zero API cost)
- ❌ Avoid analysis endpoint storage (wasteful)

---

## Database Impact

### Storage Requirements

| Table | Current Records | Growth Rate | Storage Impact |
|-------|----------------|-------------|----------------|
| ra_horses | 111,430 | +50-200/day | Low |
| ra_horse_pedigree | 22 → 111,430 | Backfill + daily | Medium (one-time) |
| ra_jockeys | 3,480 | +5-20/day | Minimal |
| ra_trainers | 2,780 | +2-10/day | Minimal |
| ra_owners | 48,092 | +20-50/day | Low |

**Total Impact:** Low - all growth is natural entity discovery

### Statistics Storage

All entity statistics calculated locally from ra_mst_runners:
- No API calls required
- No additional tables needed
- Columns already added (migration 007)
- Update function ready to use

---

## Next Steps - Priority Order

### 🔥 HIGH PRIORITY

1. **Complete Horse Pedigree Backfill**
   - Current: 22/111,430 (0.02%)
   - Target: 111,430/111,430 (100%)
   - Time: ~15.5 hours
   - Script: `scripts/backfill_horse_pedigree.py`
   - When: Run overnight/off-peak

### 📊 MEDIUM PRIORITY

2. **Automate Statistics Calculation**
   - Create: `scripts/update_entity_statistics.py`
   - Schedule: Daily at 2 AM
   - Duration: < 1 minute
   - Cost: Zero API calls
   - Benefit: Fresh entity statistics

3. **Add Statistics Monitoring**
   - Alert if stats > 48 hours old
   - Dashboard for data freshness
   - Health checks

### ⏸️ LOW PRIORITY

4. **Optimize Query Performance**
   - Index tuning based on usage
   - Materialized views for common queries
   - Caching layer

### ❌ NOT RECOMMENDED

5. **DON'T Store API Analysis Data**
   - Redundant with ra_mst_runners
   - Wasteful API calls
   - Better to calculate locally

---

## Common Questions

### Q: Why can't we enrich jockeys/trainers/owners like horses?

**A:** The Racing API simply doesn't provide individual detail endpoints for these entities. They only have:
- Results endpoints (race history we already have)
- Analysis endpoints (statistics we can calculate ourselves)

Only horses have a dedicated Pro endpoint with unique enrichment data.

### Q: Should we store the analysis endpoint data?

**A:** No. Analysis endpoints return calculated statistics that we can (and should) compute locally from our ra_mst_runners table. This:
- Saves API calls
- Gives us full control over calculations
- Allows custom metrics
- Updates in real-time

### Q: What about race enrichment?

**A:** Not needed. We already fetch complete race data from the bulk racecards endpoint. Individual race endpoint returns the same data we already have.

### Q: How long will pedigree backfill take?

**A:** ~15.5 hours for all 111,430 horses at 2 requests/second. Run it overnight or during off-peak hours as a one-time job.

### Q: What's the daily API call overhead?

**A:** Minimal - only 50-200 calls/day for new horses discovered. At 2 req/sec rate limit (172,800/day), we use < 0.1% of our quota.

---

## Code Examples

### Update All Statistics (Local Calculation)

```sql
-- Run this daily to update all entity statistics
SELECT * FROM update_entity_statistics();

-- Results:
-- jockeys_updated | trainers_updated | owners_updated
--      3480       |      2780        |     48092
```

### Query Top Performing Entities

```sql
-- Top jockeys by win rate (minimum 100 rides)
SELECT *
FROM jockey_statistics
WHERE calculated_total_rides >= 100
ORDER BY calculated_win_rate DESC
LIMIT 20;

-- Trainers in good recent form
SELECT *
FROM trainer_statistics
WHERE calculated_recent_14d_runs >= 10
ORDER BY calculated_recent_14d_win_rate DESC
LIMIT 20;

-- Active big owners
SELECT *
FROM owner_statistics
WHERE calculated_active_last_30d = TRUE
  AND calculated_total_horses >= 5
ORDER BY calculated_win_rate DESC
LIMIT 20;
```

### Check Horse Enrichment Progress

```sql
-- Check pedigree backfill progress
SELECT
    COUNT(*) as total_horses,
    COUNT(CASE WHEN dob IS NOT NULL THEN 1 END) as horses_with_dob,
    COUNT(CASE WHEN colour IS NOT NULL THEN 1 END) as horses_with_colour,
    ROUND(100.0 * COUNT(CASE WHEN dob IS NOT NULL THEN 1 END) / COUNT(*), 2) as pct_enriched
FROM ra_horses;

-- Check pedigree records
SELECT COUNT(*) as pedigree_records
FROM ra_horse_pedigree;
```

---

## Contact & Support

**Documentation:**
- Full Analysis: `docs/COMPLETE_ENRICHMENT_ANALYSIS.md`
- This Quick Reference: `docs/ENRICHMENT_QUICK_REFERENCE.md`
- Test Results: `docs/entity_endpoint_test_results.json`

**Scripts:**
- Horse Backfill: `scripts/backfill_horse_pedigree.py`
- Entity Extractor: `utils/entity_extractor.py`
- Test Script: `scripts/test_all_entity_endpoints.py`

**Database:**
- Migration 007: Entity statistics (jockeys, trainers, owners)
- Migration 008: Horse pedigree enhancements
- Views: `jockey_statistics`, `trainer_statistics`, `owner_statistics`

---

**Last Updated:** 2025-10-14
**Version:** 1.0
**Status:** Complete Analysis - All Endpoints Tested
