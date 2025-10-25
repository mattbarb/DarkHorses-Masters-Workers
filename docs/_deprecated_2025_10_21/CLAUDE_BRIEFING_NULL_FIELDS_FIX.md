# CLAUDE BRIEFING: DarkHorses NULL Field Remediation Project

**Generated**: 2025-10-16
**Project**: DarkHorses Racing Data Platform
**Objective**: Fix all NULL field issues in ML training data endpoints

---

## PROJECT CONTEXT

You are working on the DarkHorses racing data platform, which consists of two main systems:

1. **DarkHorses-Masters-Workers** - Data collection workers that fetch from Racing API
2. **DarkHorses-API** - FastAPI application serving ML training data

A comprehensive data quality audit identified **4 major NULL field issues** affecting ML training endpoints. Investigation revealed that most issues stem from incomplete transformation logic in the API layer, but one critical issue (Issue #3) requires a data backfill first.

**Key Facts:**
- 76 endpoints tested, 8 have data quality issues
- Database (`ra_*` tables) contains source data (after backfill)
- Issues are mostly transformation/aggregation logic, NOT missing API data
- Total estimated fix time: 17-23 hours across 4 issues

---

## CRITICAL DISCOVERY: Results Data Architecture

**IMPORTANT:** During investigation, we discovered the actual data flow for position/results data:

### What We Found

1. **`ra_results` table is EMPTY and UNUSED** (0 records)
   - Originally planned but never implemented
   - Can be safely ignored or removed

2. **Position data is stored directly in `ra_runners` table**
   - The `results_fetcher.py` writes position data to `ra_runners`, NOT `ra_results`
   - Fields: `position`, `distance_beaten`, `prize_won`, `starting_price`
   - See `fetchers/results_fetcher.py` lines 324-329

3. **Racing API `/v1/results` endpoint DOES provide position data**
   - Position: "1", "2", "3", etc.
   - Distance beaten (btn): "0", "1.5", "3.25", etc.
   - Prize won: "4187.20", etc.
   - Starting price (sp): "17/2", "5/1", etc.
   - Endpoint is working correctly ✅

4. **Current data coverage: Only 0.2% of runners have position data**
   - Total runners: 379,422
   - Runners with position: 819 (0.2%)
   - **Problem**: Results fetcher hasn't been run recently
   - **Solution**: Backfill required before fixing Issue #3

### Correct Query Pattern

```python
# CORRECT: Query historical races from ra_runners
history_query = supabase.table('ra_runners')\
    .select('*, ra_races!inner(race_date, course_id, distance_meters, going)')\
    .eq('horse_id', horse_id)\
    .not_.is_('position', 'null')\  # Only completed races with results
    .order('ra_races.race_date', desc=True)\
    .limit(100)

# WRONG: Do NOT try to join with ra_results (it's empty!)
```

---

## YOUR MISSION

Fix all NULL field issues in priority order to enable complete ML training data pipelines. You will implement aggregation functions, enrichment logic, and caching to populate currently-NULL calculated fields.

**CRITICAL PRE-REQUISITE**: Issue #3 requires that the results backfill has been completed first. Verify position data coverage before implementing statistics calculations.

**Success Criteria:**
- All identified NULL fields reduced to <5%
- API response times <2 seconds for 100 records
- Match accuracy >95% for historical odds ID matching (Issue #1)
- Position data coverage >50% after backfill
- All changes fully tested and documented

---

## ISSUE #1: HISTORICAL ODDS MISSING race_id/horse_id (HIGH PRIORITY)

**Status:** 🔴 CRITICAL - Blocks ML training workflows

**Problem:**
- Endpoint: `/api/v2/data/odds/historical`
- Fields: `race_id` and `horse_id` are 100% NULL
- Impact: Cannot join historical odds with races/horses for ML training

**Root Cause:**
The `ra_odds_historical` table is from an external data source (Racing Bet Data Excel) with a different schema. It uses:
- `track` (course name)
- `date_of_race` (race date)
- `race_time` (race time)
- `horse_name` (horse name)

Instead of `race_id`/`horse_id`. These IDs must be derived via matching.

**Solution Required:**
1. Create `enrich_historical_odds_with_ids()` function in `/DarkHorses-API/services/data_sources/transformations.py`
2. Match logic:
   - Find race: Join `ra_races` on course_name + race_date + race_time (±30min window)
   - Find horse: Join `ra_runners` on horse_name within matched race
   - Handle fuzzy matching for course name variations (e.g., "Ayr" vs "AYR")
3. Integrate enrichment in `get_odds_historical()` in `/DarkHorses-API/services/data_sources/database_v2.py` (line 327)
4. Add Redis caching for matched IDs (TTL: 24 hours)
5. Log unmatched records for manual review

**Implementation Example:**

```python
# File: /DarkHorses-API/services/data_sources/transformations.py

def enrich_historical_odds_with_ids(historical_record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich historical odds with race_id and horse_id by matching against ra_races and ra_horses

    Matching strategy:
    1. Find race: match course_name + race_date + race_time (or closest time)
    2. Find horse: match horse_name within that race's runners
    """
    track = historical_record.get('track')
    date_of_race = historical_record.get('date_of_race')
    race_time = historical_record.get('race_time')
    horse_name = historical_record.get('horse_name')

    if not all([track, date_of_race, horse_name]):
        return historical_record  # Cannot match without these fields

    try:
        # Step 1: Find matching race
        # Convert track name to course_id (may need fuzzy matching for variations)
        race_query = supabase.table('ra_races')\
            .select('race_id, course_id, course_name, off_time')\
            .ilike('course_name', f'%{track}%')\
            .eq('race_date', date_of_race)

        # If race_time provided, filter to closest match
        if race_time:
            race_query = race_query.gte('off_time', adjust_time(race_time, -30))  # ±30 min window
            race_query = race_query.lte('off_time', adjust_time(race_time, +30))

        race_result = race_query.execute()

        if not race_result.data:
            logger.warning(f"No race match found for {track} on {date_of_race}")
            return historical_record

        race_id = race_result.data[0]['race_id']

        # Step 2: Find matching horse in that race's runners
        horse_query = supabase.table('ra_runners')\
            .select('horse_id, horse_name')\
            .eq('race_id', race_id)\
            .ilike('horse_name', f'%{horse_name}%')

        horse_result = horse_query.execute()

        if not horse_result.data:
            logger.warning(f"No horse match found for {horse_name} in race {race_id}")
            return historical_record

        horse_id = horse_result.data[0]['horse_id']

        # Enrich record
        historical_record['race_id'] = race_id
        historical_record['horse_id'] = horse_id

        logger.debug(f"Matched {horse_name} at {track}: race_id={race_id}, horse_id={horse_id}")
        return historical_record

    except Exception as e:
        logger.error(f"Error enriching historical odds: {e}")
        return historical_record
```

**Files to Modify:**
- `/DarkHorses-API/services/data_sources/transformations.py` - Add enrichment function
- `/DarkHorses-API/services/data_sources/database_v2.py` - Integrate in query pipeline (line 327)

**Testing Requirements:**
- Test with 100+ sample historical records
- Verify match accuracy >95%
- Check for course name variation handling
- Log and review unmatched records

**Time Estimate:** 4-6 hours

---

## ISSUE #2: LIVE ODDS CALCULATED FIELDS (MEDIUM PRIORITY)

**Status:** ⚠️ MEDIUM - Impacts ML model features

**Problem:**
- Endpoint: `/api/v2/data/odds/live`
- Fields (8 total, all 100% NULL):
  - `avg_odds`, `best_odds`, `worst_odds`
  - `bookmaker_count`
  - `market_rank`
  - `implied_probability`
  - `odds_movement`
  - `value_indicator`

**Root Cause:**
The `ra_odds_live` table stores individual bookmaker odds (one row per bookmaker per horse). The transformation layer should aggregate these to calculate market-wide metrics, but this logic doesn't exist.

**Solution Required:**
1. Modify `get_odds_live()` in `/DarkHorses-API/services/data_sources/database_v2.py` (line 275)
2. Add aggregation query:
   ```sql
   GROUP BY race_id, horse_id
   AVG(odds_decimal) as avg_odds,
   MIN(odds_decimal) as best_odds,
   MAX(odds_decimal) as worst_odds,
   COUNT(DISTINCT bookmaker_name) as bookmaker_count
   ```
3. Calculate market_rank: Sort horses by avg_odds within each race (1 = favorite)
4. Calculate implied_probability: `1.0 / avg_odds`
5. Calculate odds_movement: Compare current odds to 1-hour-ago snapshot (drift/shorten/stable)
6. Calculate value_indicator: `best_odds > avg_odds * 1.10` (10% threshold)
7. Add Redis caching (TTL: 2 minutes for live odds)

**Alternative Approach (Better Performance):**
Create materialized view `ra_odds_live_aggregated` with auto-refresh every 30 seconds. This offloads aggregation to database.

**Files to Modify:**
- `/DarkHorses-API/services/data_sources/database_v2.py` - Add aggregation logic (line 275)
- `/DarkHorses-API/services/data_sources/transformations.py` - Update `transform_odds_live()`
- (Optional) `/DarkHorses-Masters-Workers/migrations/` - Add materialized view

**Testing Requirements:**
- Verify aggregations match manual calculations
- Test with multiple races and varying bookmaker counts
- Performance test: ensure <2s response time for 100 records
- Test caching hit rates (target >70%)

**Time Estimate:** 5-8 hours

---

## ISSUE #3: RUNNER DERIVED STATISTICS (MEDIUM PRIORITY)

**Status:** ⚠️ MEDIUM - Critical for ML model accuracy
**PRE-REQUISITE:** ⚠️ **REQUIRES RESULTS BACKFILL COMPLETED FIRST**

**Problem:**
- Endpoint: `/api/v2/data/masters/runners`
- Fields (20+ total, all 100% NULL):
  - Form strings: `last_5_positions`, `last_10_positions`, `days_since_last_run`
  - Career stats: `career_wins`, `career_runs`, `career_win_rate`, `career_place_rate`
  - Context performance: `course_wins/runs/win_rate`, `distance_wins/runs/win_rate`, `going_wins/runs/win_rate`
  - Form analysis: `form_avg_position`, `form_wins`, `form_places`
  - `starting_price`

**Root Cause:**
These are calculated fields requiring aggregation from historical `ra_runners` data with position information. The transformation layer expects them to exist in the database, but they must be computed.

**CRITICAL FINDING:** Only 0.2% of runners currently have position data. Before implementing this fix:
1. ✅ **Run results fetcher backfill** to populate position data (see Pre-Requisite section below)
2. ✅ **Verify position data coverage >50%** before proceeding
3. Then implement calculated statistics (will work much better with proper data)

**Solution Required:**
1. Create `calculate_runner_statistics()` function in `/DarkHorses-API/services/data_sources/database_v2.py`
2. For each runner, query historical races from `ra_runners` (NOT ra_results - it's empty!):
   ```python
   # CORRECT: Query ra_runners with position data
   history_query = supabase.table('ra_runners')\
       .select('*, ra_races!inner(race_date, course_id, distance_meters, going)')\
       .eq('horse_id', horse_id)\
       .not_.is_('position', 'null')\  # Only completed races
       .lt('ra_races.race_date', current_race_date)\
       .order('ra_races.race_date', desc=True)\
       .limit(100)
   ```

3. Calculate:
   - **Form strings**: Extract last 5/10 positions (e.g., "13245")
   - **Days since last run**: Date difference from most recent race
   - **Career stats**: COUNT(*), COUNT(position=1), win rate, place rate
   - **Course stats**: Filter by course_id, calculate same metrics
   - **Distance stats**: Filter by distance (±200m tolerance), calculate metrics
   - **Going stats**: Filter by going type, calculate metrics
   - **Form analysis**: Average position, wins, places from last 5 races

4. Integrate in `get_masters_runners()` (line 518):
   - Fetch race context (date, course, distance, going) for each runner
   - Call `calculate_runner_statistics()` per runner
   - Merge calculated stats with base record

5. **CRITICAL**: Implement Redis caching:
   - Cache key: `runner_stats:{horse_id}:{race_date}`
   - TTL: 24 hours
   - Without caching, this will be EXTREMELY slow (N queries per runner)

**Implementation Example:**

```python
# File: /DarkHorses-API/services/data_sources/database_v2.py

def calculate_runner_statistics(
    runner_record: Dict[str, Any],
    race_date: datetime,
    course_id: str,
    distance: int,
    going: str
) -> Dict[str, Any]:
    """
    Calculate derived statistics for a runner based on historical performance

    IMPORTANT: Queries ra_runners table (NOT ra_results - it's empty!)
    """
    horse_id = runner_record.get('horse_id')

    if not horse_id:
        return {}

    try:
        # Get all historical runs for this horse (before current race)
        # IMPORTANT: Join with ra_races for race context, filter by position NOT NULL
        history_query = supabase.table('ra_runners')\
            .select('*, ra_races!inner(race_date, course_id, distance_meters, going)')\
            .eq('horse_id', horse_id)\
            .not_.is_('position', 'null')\  # CRITICAL: Only races with results
            .lt('ra_races.race_date', race_date)\
            .order('ra_races.race_date', desc=True)\
            .limit(100)  # Last 100 races should be enough

        history_response = history_query.execute()
        history = history_response.data

        if not history:
            return {}  # No historical data

        # Calculate form strings
        recent_runs = history[:10]
        last_5_positions = ''.join([str(r['position']) for r in recent_runs[:5]])
        last_10_positions = ''.join([str(r['position']) for r in recent_runs[:10]])

        # Calculate days since last run
        if recent_runs:
            last_run_date = datetime.fromisoformat(recent_runs[0]['ra_races']['race_date'])
            days_since_last_run = (race_date - last_run_date).days
        else:
            days_since_last_run = None

        # Career statistics
        career_runs = len(history)
        career_wins = len([r for r in history if r['position'] == 1])
        career_places = len([r for r in history if r['position'] <= 3])

        career_win_rate = career_wins / career_runs if career_runs > 0 else None
        career_place_rate = career_places / career_runs if career_runs > 0 else None

        # Course-specific statistics
        course_runs_data = [r for r in history
                           if r['ra_races'].get('course_id') == course_id]
        course_runs = len(course_runs_data)
        course_wins = len([r for r in course_runs_data if r['position'] == 1])
        course_win_rate = course_wins / course_runs if course_runs > 0 else None

        # Distance-specific statistics (±200m tolerance)
        distance_runs_data = [r for r in history
                             if abs(r['ra_races'].get('distance_meters', 0) - distance) <= 200]
        distance_runs = len(distance_runs_data)
        distance_wins = len([r for r in distance_runs_data if r['position'] == 1])
        distance_win_rate = distance_wins / distance_runs if distance_runs > 0 else None

        # Going-specific statistics
        going_runs_data = [r for r in history
                          if r['ra_races'].get('going', '').lower() == going.lower()]
        going_runs = len(going_runs_data)
        going_wins = len([r for r in going_runs_data if r['position'] == 1])
        going_win_rate = going_wins / going_runs if going_runs > 0 else None

        # Form analysis (from recent form)
        form_positions = [r['position'] for r in recent_runs[:5]]
        if form_positions:
            form_avg_position = statistics.mean(form_positions)
            form_wins = len([p for p in form_positions if p == 1])
            form_places = len([p for p in form_positions if p <= 3])
        else:
            form_avg_position = None
            form_wins = None
            form_places = None

        return {
            'last_5_positions': last_5_positions,
            'last_10_positions': last_10_positions,
            'days_since_last_run': days_since_last_run,
            'career_wins': career_wins,
            'career_runs': career_runs,
            'career_win_rate': career_win_rate,
            'career_place_rate': career_place_rate,
            'course_wins': course_wins,
            'course_runs': course_runs,
            'course_win_rate': course_win_rate,
            'distance_wins': distance_wins,
            'distance_runs': distance_runs,
            'distance_win_rate': distance_win_rate,
            'going_wins': going_wins,
            'going_runs': going_runs,
            'going_win_rate': going_win_rate,
            'form_avg_position': form_avg_position,
            'form_wins': form_wins,
            'form_places': form_places
        }

    except Exception as e:
        logger.error(f"Error calculating runner statistics for horse {horse_id}: {e}")
        return {}
```

**Files to Modify:**
- `/DarkHorses-API/services/data_sources/database_v2.py` - Add calculation function + integration (line 518)
- `/DarkHorses-API/services/data_sources/transformations.py` - Update `transform_masters_runner()`
- (Recommended) `/DarkHorses-Masters-Workers/migrations/` - Add indexes on (horse_id, race_date)

**Testing Requirements:**
- **FIRST**: Verify position data coverage >50% after backfill
- Verify calculations match manual analysis for sample horses
- Test with horses having varying amounts of history (0 races, 5 races, 100+ races)
- Performance test: ensure <2s response time with caching
- Test cache hit rates (target >70%)
- Edge case testing: first race, missing positions, non-finishers

**Time Estimate:** 10-14 hours (most complex issue)

### PRE-REQUISITE: Results Backfill

Before implementing Issue #3, you MUST run the results fetcher to populate position data:

```bash
# Run results backfill (takes 2-4 hours due to API rate limits)
python3 main.py --entities results

# This will:
# - Fetch last 365 days of UK/Ireland results from /v1/results endpoint
# - Update ra_runners with position, distance_beaten, prize_won, starting_price
# - Expected: ~180,000 runners updated (from 819 to ~180,000+)
```

**Verify backfill success:**
```python
# Check position data coverage
from supabase import create_client
supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

total = supabase.table('ra_runners').select('*', count='exact').execute()
with_position = supabase.table('ra_runners').select('*', count='exact').not_.is_('position', 'null').execute()

coverage = (with_position.count / total.count) * 100
print(f'Position data coverage: {coverage:.1f}%')
# Target: >50% (currently 0.2%)
```

Only proceed with Issue #3 implementation after confirming >50% position data coverage.

---

## ISSUE #4: HORSE EXTENDED METADATA (LOW PRIORITY)

**Status:** 💡 LOW - Nice-to-have features

**Problem:**
- Endpoint: `/api/v2/data/masters/horses`
- Fields (8 total, all 100% NULL):
  - `age` - Calculate from DOB
  - `origin` - Country of origin
  - `sire`, `dam`, `damsire` - Pedigree (should exist in `ra_horse_pedigree`)
  - `total_wins`, `total_runs`, `total_prize_money` - Career stats

**Root Cause:**
- **Pedigree fields**: Join with `ra_horse_pedigree` exists but extraction may be broken
- **Career stats**: Need aggregation from `ra_runners` (similar to Issue #3)
- **Age**: Simple calculation from `dob` field

**Solution Required:**
1. Debug pedigree extraction in `transform_masters_horse()` (`transformations.py` line 525):
   - Add logging to see if `ra_horse_pedigree` join returns data
   - Fix nested structure extraction (may be list or dict)
   - Handle cases where pedigree record doesn't exist

2. Add career statistics calculation in `get_masters_horses()` (`database_v2.py` line 572):
   ```python
   # Query ra_runners for career stats (NOT ra_results!)
   stats_query = supabase.table('ra_runners')\
       .select('position, prize_money_won')\
       .eq('horse_id', horse_id)\
       .not_.is_('position', 'null')  # Only completed races

   stats_response = stats_query.execute()

   if stats_response.data:
       runs = stats_response.data
       total_runs = len(runs)
       total_wins = len([r for r in runs if r['position'] == 1])
       total_prize_money = sum([r.get('prize_money_won', 0) or 0 for r in runs])
   ```

3. Calculate age from DOB:
   ```python
   if dob:
       age = (datetime.now() - dob).days // 365
   ```

4. Add Redis caching for career stats (TTL: 24 hours)

**Files to Modify:**
- `/DarkHorses-API/services/data_sources/transformations.py` - Debug pedigree extraction, add age calc (line 525)
- `/DarkHorses-API/services/data_sources/database_v2.py` - Add career stats aggregation (line 572)
- (Optional) `/DarkHorses-Masters-Workers/migrations/` - Add columns + trigger for pre-calculation

**Testing Requirements:**
- Verify pedigree data appears for horses with pedigree records
- Check career stats match manual calculations
- Test with horses having varying career lengths
- Validate age calculations

**Time Estimate:** 4-6 hours

---

## IMPLEMENTATION ROADMAP

**Recommended Execution Order:**

### Phase 0: Data Backfill (MUST DO FIRST)
- **Day 0**: Run results fetcher backfill (2-4 hours runtime)
- Verify position data coverage >50%
- **CRITICAL**: Do NOT proceed to Issue #3 without this

### Phase 1: High Priority
- **Day 1-2**: Issue #1 (HIGH) - Historical odds ID matching
- Implement matching functions
- Test match accuracy (target: >95%)
- **Deliverable**: `/api/v2/data/odds/historical` returns race_id/horse_id

### Phase 2: Medium Priority
- **Day 3-5**: Issue #2 (MEDIUM) - Live odds aggregation
- Create aggregation queries
- Add market rank calculation
- Implement caching
- **Deliverable**: `/api/v2/data/odds/live` returns all 8 calculated fields

- **Day 6-10**: Issue #3 (MEDIUM) - Runner statistics
- **PRE-CHECK**: Verify position data coverage >50%
- Create statistics calculation function
- Integrate with get_masters_runners()
- Implement caching strategy
- **Deliverable**: `/api/v2/data/masters/runners` returns all 20+ derived fields

### Phase 3: Low Priority
- **Day 11-12**: Issue #4 (LOW) - Horse metadata
- Debug pedigree join
- Add career statistics aggregation
- Calculate age from DOB
- **Deliverable**: `/api/v2/data/masters/horses` returns all 8 fields

### Phase 4: Testing & Documentation
- **Day 13-14**: Integration testing, performance optimization, documentation

---

## CRITICAL SUCCESS FACTORS

✅ **Phase 0 is MANDATORY** - Run results backfill before Issue #3
✅ **Caching is mandatory** - without it, Issues #2 and #3 will timeout
✅ **Test match accuracy** for Issue #1 before proceeding (>95% target)
✅ **Add comprehensive logging** to debug calculation issues
✅ **Monitor performance** - use database query profiling
✅ **Validate calculations** against manual analysis for sample data
✅ **Verify data coverage** - confirm >50% position data before Issue #3

---

## PERFORMANCE TARGETS

- API response time: <2 seconds for 100 records (95th percentile)
- Cache hit rate: >70% for repeated queries
- Database queries per request: <5 with caching
- Match accuracy (Issue #1): >95%
- Position data coverage (after backfill): >50%

---

## KEY FILES REFERENCE

**DarkHorses-API (where you'll work):**
- `/services/data_sources/database_v2.py` - Database query functions (Issues #1, #2, #3, #4)
- `/services/data_sources/transformations.py` - Transformation logic (Issues #1, #4)
- `/services/data_sources/models_v2.py` - Pydantic models (documentation updates)

**DarkHorses-Masters-Workers:**
- `/fetchers/results_fetcher.py` - Results fetcher (stores position data in ra_runners)
- `/utils/position_parser.py` - Position data extraction utilities
- `/main.py` - Orchestrator (run with `--entities results` for backfill)

**Database Tables:**
- `ra_odds_live` - Individual bookmaker odds (Issue #2)
- `ra_odds_historical` - External historical odds (Issue #1)
- `ra_runners` - **Race entries + POSITION DATA** (Issues #3, #4) ⚠️ IMPORTANT
- `ra_results` - **UNUSED/EMPTY** - ignore this table ⚠️
- `ra_horses` - Horse master data (Issue #4)
- `ra_horse_pedigree` - Pedigree data (Issue #4)
- `ra_races` - Race master data (context for calculations)

---

## TESTING CHECKLIST

For each issue, complete before marking done:

**Unit Tests:**
- [ ] Test calculation functions with known inputs/outputs
- [ ] Test edge cases (no history, missing fields, NULL values)
- [ ] Test error handling and graceful degradation

**Integration Tests:**
- [ ] Query endpoint and verify previously-NULL fields now populated
- [ ] Validate data types match model definitions
- [ ] Check logical constraints (e.g., best_odds ≤ avg_odds ≤ worst_odds)

**Performance Tests:**
- [ ] Test with 10, 100, 1000 record page sizes
- [ ] Measure response times (target: <2s for 100 records)
- [ ] Test concurrent requests (10, 50, 100 users)
- [ ] Monitor cache hit rates (target: >70%)

**Data Quality Tests:**
- [ ] Compare calculated values to manual analysis (10+ samples)
- [ ] Check for logical inconsistencies (negative values, rates >100%, etc.)
- [ ] Test boundary conditions (first race, no history, etc.)
- [ ] Verify position data coverage after backfill (target: >50%)

---

## RISK MITIGATION

**High-Risk Areas:**

1. **Historical Odds Matching Accuracy (Issue #1)**
   - Risk: Incorrect matches corrupt ML training data
   - Mitigation: Manual validation of 100+ matches, log unmatched records, add confidence scores

2. **Performance Degradation (Issues #2, #3)**
   - Risk: Aggregation queries too slow without optimization
   - Mitigation: Mandatory caching, consider materialized views, add database indexes

3. **Insufficient Position Data (Issue #3)**
   - Risk: Backfill doesn't populate enough data for meaningful statistics
   - Mitigation: Verify coverage >50% before proceeding, monitor backfill logs

4. **Calculation Errors (Issues #2, #3, #4)**
   - Risk: Incorrect statistics corrupt ML models
   - Mitigation: Extensive unit testing, manual validation, peer review of logic

---

## ENVIRONMENT SETUP

**Repository Locations:**
- DarkHorses-API: `/Users/matthewbarber/Documents/GitHub/DarkHorses-API` (not in current workspace)
- DarkHorses-Masters-Workers: `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers` (current workspace)

**You will need to work in the DarkHorses-API repository** for most changes. Use the Read tool with full paths:
```python
Read('/Users/matthewbarber/Documents/GitHub/DarkHorses-API/services/data_sources/database_v2.py')
```

**Database Access:**
- Supabase URL: Available in environment variables
- Connection established via `services/core/supabase.py`

**Redis Access:**
- Already configured via `services/core/redis.py`

---

## QUESTIONS TO ASK IF STUCK

1. For Issue #1: What course name variations exist in the data? (May need fuzzy matching library)
2. For Issue #2: Should we use materialized views or query-time aggregation? (Discuss performance tradeoffs)
3. For Issue #3:
   - **FIRST**: Has results backfill completed? What's the position data coverage?
   - Should statistics be pre-calculated and stored, or calculated on-demand with caching?
4. For Issue #4: Why is pedigree extraction failing? (Need to inspect actual database schema)

---

## SUCCESS METRICS SUMMARY

**Technical:**
- NULL rate: <5% for all identified fields
- Response time: <2s for 100 records (95th percentile)
- Cache hit rate: >70%
- Match accuracy: >95% (Issue #1)
- Position data coverage: >50% (after backfill)

**Functional:**
- ML training workflows can fetch complete feature sets
- All 4 issues resolved and deployed
- Data quality validated by ML team

**Timeline:**
- Phase 0 (Backfill): 2-4 hours (runtime)
- Phase 1 (Issue #1): 1 week
- Phase 2 (Issues #2, #3): 2 weeks
- Phase 3 (Issue #4): 1 week
- Total: 4 weeks maximum

---

## PRODUCTION DEPLOYMENT NOTES

### Scheduler Configuration

After completing fixes, update the worker schedule to ensure results fetcher runs regularly:

```python
# In start_worker.py or scheduler config
SCHEDULE = {
    'daily': {
        'entities': ['races', 'results'],  # IMPORTANT: Include results!
        'time': '02:00'  # Run at 2 AM daily
    },
    'weekly': {
        'entities': ['jockeys', 'trainers', 'owners', 'horses'],
        'time': '03:00'
    },
    'monthly': {
        'entities': ['courses', 'bookmakers'],
        'time': '04:00'
    }
}
```

### Monitoring

Set up alerts for:
- Empty results fetcher logs (indicates failures)
- Position data coverage dropping below 40%
- API response times exceeding 5 seconds
- Cache hit rates below 60%

---

## FINAL NOTES

- **Read CLAUDE.md** in the DarkHorses-Masters-Workers repo for project context
- **Read the full data quality audit report** at `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/DATA_QUALITY_AUDIT_REPORT.md`
- **CRITICAL**: Remember `ra_results` is EMPTY - always query `ra_runners` for position data
- **CRITICAL**: Run results backfill BEFORE implementing Issue #3
- **Start with Phase 0** (backfill) then Issue #1 - they're the highest priority
- **Ask questions early** if anything is unclear - these are complex aggregations

**Good luck! The ML team is counting on you to unlock complete training data. 🚀**

---

**END OF BRIEFING**
