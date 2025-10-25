# Statistics Field Mapping - Complete Reference

**Document Version:** 1.0
**Last Updated:** 2025-10-19
**Status:** Production Reference

## Overview

This document provides a comprehensive mapping of ALL statistics fields across `ra_jockeys`, `ra_trainers`, and `ra_owners` tables, including:
- Data source (API vs Database)
- Calculation method
- Current population status
- Dependencies
- Update frequency

## Summary Statistics (as of 2025-10-19)

**Total Entities:**
- Jockeys: 3,483
- Trainers: 2,781
- Owners: 48,165
- **TOTAL: 54,429 entities**

**Field Population Status:**
- ✓ Recent form fields (14d/30d): 100% populated
- ❌ Last date/days_since fields: 10-93% populated (needs backfill)
- ✓ Lifetime stats (total_*): 99% populated
- ✓ Win/place rates: 95-99% populated

---

## Field-by-Field Mapping

### Common Fields (All Three Tables)

#### 1. RECENT FORM STATISTICS (14-day and 30-day)

| Field | Source | Calculation | Status | Notes |
|-------|--------|-------------|--------|-------|
| `recent_14d_rides` / `recent_14d_runs` | **DATABASE** | COUNT from ra_runners WHERE race_date >= CURRENT_DATE - 14 days | ✓ 100% | Fast SQL query |
| `recent_14d_wins` | **DATABASE** | COUNT from ra_runners WHERE race_date >= CURRENT_DATE - 14 days AND position = 1 | ✓ 100% | Requires position data |
| `recent_14d_win_rate` | **CALCULATED** | (recent_14d_wins / recent_14d_rides) * 100 | ✓ 99% | NULL if no rides |
| `recent_30d_rides` / `recent_30d_runs` | **DATABASE** | COUNT from ra_runners WHERE race_date >= CURRENT_DATE - 30 days | ✓ 100% | Fast SQL query |
| `recent_30d_wins` | **DATABASE** | COUNT from ra_runners WHERE race_date >= CURRENT_DATE - 30 days AND position = 1 | ✓ 100% | Requires position data |
| `recent_30d_win_rate` | **CALCULATED** | (recent_30d_wins / recent_30d_rides) * 100 | ✓ 99% | NULL if no rides |

**Implementation:** `scripts/statistics_workers/update_recent_form_statistics.py`
**Performance:** 54,429 entities in ~10 seconds (2,700x faster than API)
**Dependencies:** Migration 005 (position fields), populated results data

---

#### 2. LIFETIME STATISTICS

| Field | Source | Calculation | Status | Notes |
|-------|--------|-------------|--------|-------|
| `total_rides` / `total_runners` | **DATABASE** | COUNT from ra_runners WHERE entity_id = X | ✓ 99% | Entire racing career |
| `total_wins` | **DATABASE** | COUNT from ra_runners WHERE entity_id = X AND position = 1 | ✓ 99% | Lifetime wins |
| `total_places` | **DATABASE** | COUNT from ra_runners WHERE entity_id = X AND position IN (1,2,3) | ✓ 99% | Top 3 finishes |
| `total_seconds` | **DATABASE** | COUNT from ra_runners WHERE entity_id = X AND position = 2 | ✓ 99% | Second place finishes |
| `total_thirds` | **DATABASE** | COUNT from ra_runners WHERE entity_id = X AND position = 3 | ✓ 99% | Third place finishes |
| `win_rate` | **CALCULATED** | (total_wins / total_rides) * 100 | ✓ 95-98% | NULL if no rides |
| `place_rate` | **CALCULATED** | (total_places / total_rides) * 100 | ✓ 95-98% | NULL if no rides |

**Implementation:** `scripts/populate_statistics_from_database.py`
**Performance:** Jockeys ~30s, Trainers ~25s, Owners ~5min (vs 4.5 days via API)
**Dependencies:** Position data in ra_runners or ra_race_results

---

#### 3. LAST DATE TRACKING

| Field | Source | Calculation | Status | Notes |
|-------|--------|-------------|--------|-------|
| `last_ride_date` / `last_runner_date` | **BOTH** | MAX(race_date) from ra_runners WHERE entity_id = X | ❌ 10-93% | Can use DB or API |
| `last_win_date` | **BOTH** | MAX(race_date) from ra_runners WHERE entity_id = X AND position = 1 | ❌ 9-58% | Can use DB or API |
| `days_since_last_ride` / `days_since_last_runner` | **CALCULATED** | CURRENT_DATE - last_ride_date | ❌ 10-93% | Derived from last_ride_date |
| `days_since_last_win` | **CALCULATED** | CURRENT_DATE - last_win_date | ❌ 9-58% | Derived from last_win_date |

**Current Implementation:** API-based workers (jockeys_statistics_worker.py, etc.)
**Issue:** Only fetches last 365 days of API data, misses older activity
**Solution:** Use database query (faster and complete)
**Dependencies:** Position data in ra_runners

---

#### 4. METADATA

| Field | Source | Calculation | Status | Notes |
|-------|--------|-------------|--------|-------|
| `stats_updated_at` | **SYSTEM** | CURRENT_TIMESTAMP when statistics updated | ✓ 99% | Timestamp field |

---

### Entity-Specific Fields

#### Owners Only

| Field | Source | Calculation | Status | Notes |
|-------|--------|-------------|--------|-------|
| `total_horses` | **DATABASE** | COUNT(DISTINCT horse_id) from ra_runners WHERE owner_id = X | ✓ 99% | Unique horses owned |
| `active_last_30d` | **DATABASE** | BOOL: EXISTS runners in last 30 days | ✓ 99% | Activity flag |

#### Trainers Only

| Field | Source | Calculation | Status | Notes |
|-------|--------|-------------|--------|-------|
| `location` | **API** | From trainers fetch endpoint | ✓ ~90% | Geographic location |

---

## Data Sources Comparison

### Option 1: API-Based (Current API Workers)

**Endpoints Used:**
- `/jockeys/{id}/results` - Last 365 days of results
- `/trainers/{id}/results` - Last 365 days of results
- `/owners/{id}/results` - Last 365 days of results

**Pros:**
- No dependency on position data migration
- Works immediately after entity creation
- Authoritative source

**Cons:**
- ❌ **VERY SLOW:** 54,429 entities × 0.5s = ~7.5 hours
- ❌ **INCOMPLETE:** Only last 365 days (misses older entities)
- ❌ **API INTENSIVE:** Rate limit concerns
- ❌ **DOES NOT POPULATE:** total_* lifetime statistics

**Files:**
- `scripts/statistics_workers/jockeys_statistics_worker.py`
- `scripts/statistics_workers/trainers_statistics_worker.py`
- `scripts/statistics_workers/owners_statistics_worker.py`

### Option 2: Database-Based (RECOMMENDED)

**Tables Used:**
- `ra_runners` (with position data from Migration 005)
- `ra_races` (for race dates)
- `ra_race_results` (alternative source if available)

**Pros:**
- ✓ **FAST:** 54,429 entities in ~6 minutes (1000x faster)
- ✓ **COMPLETE:** All historical data since 2015
- ✓ **EFFICIENT:** 3 SQL queries vs 54,429 API calls
- ✓ **COMPREHENSIVE:** Calculates ALL fields including total_*

**Cons:**
- Requires Migration 005 applied
- Requires position data populated (results fetcher)
- One-time backfill needed

**Files:**
- `scripts/populate_statistics_from_database.py` - **FULL statistics (all fields)**
- `scripts/statistics_workers/update_recent_form_statistics.py` - **Recent form only (14d/30d)**

---

## Current State Analysis

### What IS Populated (✓)

1. **Recent form statistics (14d/30d):** 100% populated
   - Source: Database queries (update_recent_form_statistics.py)
   - Updated regularly
   - Fast and efficient

2. **Lifetime statistics (total_*):** 99% populated
   - Source: Database queries (populate_statistics_from_database.py)
   - Comprehensive career data
   - One-time backfill complete

### What NEEDS Backfill (❌)

1. **Jockeys:**
   - `last_ride_date`: 10.5% populated (895 NULL)
   - `last_win_date`: 9.5% populated (905 NULL)
   - `days_since_last_ride`: 10.5% populated (895 NULL)
   - `days_since_last_win`: 9.5% populated (905 NULL)

2. **Trainers:**
   - `last_runner_date`: 10.0% populated (900 NULL)
   - `last_win_date`: 8.9% populated (911 NULL)
   - `days_since_last_runner`: 10.0% populated (900 NULL)
   - `days_since_last_win`: 8.9% populated (911 NULL)

3. **Owners:**
   - `last_runner_date`: 92.9% populated (71 NULL)
   - `last_win_date`: 57.8% populated (422 NULL)
   - `days_since_last_runner`: 92.9% populated (71 NULL)
   - `days_since_last_win`: 57.8% populated (422 NULL)

**Root Cause:** API workers only fetch last 365 days, missing inactive/older entities

---

## Recommended Implementation Strategy

### Phase 1: One-Time Backfill (PRIORITY)

**Script:** `scripts/backfill_all_statistics.py` (NEW - to be created)

**Approach:**
1. Use database-based calculation (fast, complete)
2. Populate ALL fields for ALL entities
3. Resume-capable with checkpoint
4. Progress tracking

**Fields to populate:**
- All last_*_date fields (from database MAX queries)
- All days_since_* fields (calculated from dates)
- Verify/fix any NULL total_* fields
- Verify/fix any NULL win_rate/place_rate

**Expected Duration:** ~10-15 minutes for all 54,429 entities

### Phase 2: Daily Updates (PRODUCTION)

**Script:** `scripts/statistics_workers/daily_statistics_update.py` (NEW - to be created)

**Schedule:** 1:00 AM UK time (after results fetcher completes)

**Approach:**
1. **Recent form (14d/30d):** Use update_recent_form_statistics.py (fast)
2. **Last dates:** Update from recent races only (incremental)
3. **Lifetime stats:** Update for entities with recent activity only (incremental)

**Expected Duration:** <5 minutes

### Phase 3: Integration with main.py

**Add to orchestrator:**
- New entity type: `statistics`
- Schedule: After results fetch (dependency)
- Mode: Daily update (not full recalculation)

---

## Dependencies

### Migration Dependencies

**Required:**
- ✓ Migration 005: `add_position_fields_to_runners.sql` - APPLIED

**Schema:**
```sql
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS position INTEGER;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS distance_beaten VARCHAR(50);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS prize_won DECIMAL(10,2);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS starting_price VARCHAR(20);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS finishing_time VARCHAR(20);
```

### Data Dependencies

**Required:**
1. ✓ Results data populated (results_fetcher running - currently in progress)
2. ✓ Race dates in ra_races (available since 2015)
3. ✓ Entity IDs in ra_runners (populated by races/results fetchers)

**Status Check:**
```bash
python3 scripts/populate_statistics_from_database.py --check
```

---

## Performance Metrics

### Database-Based Calculation (RECOMMENDED)

| Entity Type | Count | Duration | Rate | API Alternative |
|-------------|-------|----------|------|----------------|
| Jockeys | 3,483 | ~30s | 116/sec | ~29 min |
| Trainers | 2,781 | ~25s | 111/sec | ~23 min |
| Owners | 48,165 | ~5min | 161/sec | ~6.7 hours |
| **TOTAL** | **54,429** | **~6min** | **151/sec** | **~7.5 hours** |

**Speedup:** 1000x faster than API approach

### API-Based Calculation (LEGACY)

| Entity Type | Count | API Calls | Duration (2 req/sec) |
|-------------|-------|-----------|---------------------|
| Jockeys | 3,483 | 3,483 | ~29 minutes |
| Trainers | 2,781 | 2,781 | ~23 minutes |
| Owners | 48,165 | 48,165 | ~6.7 hours |
| **TOTAL** | **54,429** | **54,429** | **~7.5 hours** |

**Issues:**
- Rate limit pressure
- Incomplete historical data (365 days only)
- Does not populate total_* fields

---

## Update Frequencies

### Recommended Schedule

| Field Group | Update Frequency | Method | Duration | Schedule |
|-------------|-----------------|---------|----------|----------|
| Recent form (14d/30d) | Daily | Database query | ~10s | 1:00 AM |
| Last dates | Daily | Database query (incremental) | ~30s | 1:00 AM |
| Lifetime stats | Daily | Database query (active only) | ~2min | 1:00 AM |
| Full backfill | One-time | Database query (all) | ~10min | Manual |

**Total daily update:** <5 minutes

---

## Testing and Validation

### Validation Queries

**Check NULL counts:**
```sql
SELECT
  COUNT(*) as total,
  COUNT(last_ride_date) as has_last_ride,
  COUNT(recent_14d_rides) as has_recent_14d,
  COUNT(total_rides) as has_total_rides,
  COUNT(win_rate) as has_win_rate
FROM ra_jockeys
WHERE id NOT LIKE '**TEST**%';
```

**Spot-check calculation:**
```sql
-- Verify total_rides matches runner count
SELECT
  j.id,
  j.name,
  j.total_rides,
  COUNT(r.id) as actual_rides
FROM ra_jockeys j
LEFT JOIN ra_runners r ON r.jockey_id = j.id
WHERE j.id NOT LIKE '**TEST**%'
GROUP BY j.id, j.name, j.total_rides
HAVING j.total_rides != COUNT(r.id)
LIMIT 10;
```

### Validation Script

**File:** `tests/test_statistics_validation.py` (to be created)

**Tests:**
1. No unexpected NULLs (all fields populated for active entities)
2. Calculation accuracy (spot-check math)
3. Date consistency (last_ride_date <= today)
4. Win rate logic (win_rate <= 100%)
5. Recent form consistency (14d <= 30d counts)

---

## Troubleshooting

### Issue: Position data not available

**Error:**
```
ERROR: No position data found in database!
```

**Solution:**
```bash
# 1. Check migration status
psql -c "\d ra_runners" | grep position

# 2. Run results fetcher
python3 main.py --entities results

# 3. Verify data
python3 scripts/populate_statistics_from_database.py --check
```

### Issue: Some last_*_date fields NULL

**Cause:** Entity hasn't had activity in last 365 days (API limitation)

**Solution:** Use database-based backfill (checks ALL historical data)
```bash
python3 scripts/backfill_all_statistics.py --all
```

### Issue: Statistics outdated

**Check last update:**
```sql
SELECT
  MIN(stats_updated_at) as oldest,
  MAX(stats_updated_at) as newest,
  AVG(EXTRACT(EPOCH FROM (NOW() - stats_updated_at))/3600) as avg_hours_old
FROM ra_jockeys;
```

**Update:**
```bash
python3 scripts/statistics_workers/daily_statistics_update.py --all
```

---

## Related Documentation

- **Migration 005:** `migrations/005_add_position_fields_to_runners.sql`
- **Database schema:** `docs/CURRENT_DATABASE_SCHEMA.md`
- **Backfill instructions:** `docs/BACKFILL_INSTRUCTIONS.md` (to be updated)
- **Daily operations:** `CLAUDE.md` - Essential Commands

---

## Summary

**Current Status:**
- ✓ Recent form fields: 100% populated, database-based, fast
- ✓ Lifetime stats: 99% populated, database-based, comprehensive
- ❌ Last date fields: 10-93% populated, needs backfill

**Action Items:**
1. Create backfill script for last_*_date fields
2. Create daily statistics updater (unified)
3. Integrate with main.py orchestrator
4. Add validation tests
5. Update CLAUDE.md with statistics commands

**Expected Outcome:**
- 100% field population across all 54,429 entities
- <5 minute daily updates
- Complete historical coverage (2015+)
- Production-ready, maintainable solution
