# Statistics Workers Implementation Plan

**Date:** 2025-10-23
**Purpose:** Plan for implementing workers to populate the 174 "expected NULL" statistics columns using Racing API data

---

## 🎯 Executive Summary

**GOOD NEWS:** The 174 "expected NULL" columns CAN be populated from the Racing API!

The API provides `/results` endpoints for jockeys, trainers, and owners that return complete historical race data. We can calculate ALL statistics locally without needing additional API endpoints.

---

## 📊 Available API Endpoints

### ✅ Entity Results Endpoints (Confirmed Working)

1. **`/jockeys/{id}/results`**
   - Returns: All races for this jockey with complete runner data
   - Includes: position, SP, prize money, age, weight, headgear, etc.
   - Pagination: limit/skip parameters
   - Total: Returns total count

2. **`/trainers/{id}/results`**
   - Returns: All races for this trainer with complete runner data
   - Same structure as jockey results

3. **`/owners/{id}/results`**
   - Returns: All races for this owner with complete runner data
   - Same structure as jockey/trainer results

### ✅ What Each Result Contains

Each result includes:
```json
{
  "race_id": "rac_11779378",
  "date": "2025-10-23",
  "course": "Clonmel (IRE)",
  "course_id": "crs_4602",
  "type": "Chase",
  "class": "",
  "rating_band": "0-100",
  "dist_f": "21f",
  "dist_m": 4224,
  "runners": [
    {
      "horse_id": "hrs_39698890",
      "horse": "Kobalt St Georges (FR)",
      "position": "1",
      "sp": "9/2",
      "sp_dec": "5.50",
      "prize": "€5900",
      "weight_lbs": "159",
      "age": "5",
      "jockey_id": "jky_248040",
      "trainer_id": "trn_49986",
      "owner_id": "own_907200",
      "sire_id": "sir_5344241",
      "dam_id": "dam_21667310",
      "damsire_id": "dsi_3689966"
      // ... many more fields
    }
  ]
}
```

---

## 📋 Statistics to Calculate

### Master Tables - People (Jockeys/Trainers/Owners)

**4 NULL columns per table (time-based statistics):**

1. `last_ride_date` / `last_runner_date` - Most recent race date
2. `last_win_date` - Most recent win date
3. `days_since_last_ride` / `days_since_last_runner` - Days since last race
4. `days_since_last_win` - Days since last win

**Calculation:**
- Fetch all results for entity using `/{entity}/{id}/results`
- Find most recent race where entity participated
- Find most recent race where entity won (position = 1)
- Calculate days difference from today

---

### Master Tables - Pedigree (Sires/Dams/Damsires)

**28-39 NULL columns per table (performance statistics):**

#### Top-level Statistics (7 columns):
1. `horse_id` - Optional reference to the sire/dam/damsire as a horse
2. `best_distance` - Distance with best win rate
3. `best_distance_ae` - AE index at best distance
4. `best_class` - Class with best win rate
5. `best_class_ae` - AE index at best class
6. `analysis_last_updated` - Timestamp of last calculation
7. `data_quality_score` - Quality metric (0-100)

#### Class Performance Breakdowns (15 columns - 3 classes × 5 metrics):
For each of class_1, class_2, class_3:
- `class_N_name` - Class name (e.g., "Class 1")
- `class_N_runners` - Total runners in this class
- `class_N_wins` - Total wins in this class
- `class_N_win_percent` - Win percentage
- `class_N_ae` - Actual vs Expected index

#### Distance Performance Breakdowns (15 columns - 3 distances × 5 metrics):
For each of distance_1, distance_2, distance_3:
- `distance_N_name` - Distance range (e.g., "Sprint (5-6f)")
- `distance_N_runners` - Total runners at this distance
- `distance_N_wins` - Total wins at this distance
- `distance_N_win_percent` - Win percentage
- `distance_N_ae` - Actual vs Expected index

**Calculation:**
- Query `ra_mst_race_results` table for all races where sire/dam/damsire appears
- Group by class and distance
- Calculate win rates and AE indices
- Identify top 3 classes and distances by performance

---

## 🏗️ Worker Architecture

### Option 1: Hybrid Approach (RECOMMENDED)

**Use API for time-based statistics, Database for performance analysis**

**Advantages:**
- ✅ API provides real-time, complete historical data
- ✅ Database analysis is faster for complex aggregations
- ✅ Can validate database completeness against API
- ✅ Reduces database query complexity

**Workers:**

1. **`scripts/statistics_workers/populate_jockey_statistics.py`**
   - Fetches `/jockeys/{id}/results` from API
   - Calculates last_ride_date, last_win_date, days_since_*
   - Updates `ra_mst_jockeys` table

2. **`scripts/statistics_workers/populate_trainer_statistics.py`**
   - Fetches `/trainers/{id}/results` from API
   - Calculates last_runner_date, last_win_date, days_since_*
   - Updates `ra_mst_trainers` table

3. **`scripts/statistics_workers/populate_owner_statistics.py`**
   - Fetches `/owners/{id}/results` from API
   - Calculates last_runner_date, last_win_date, days_since_*
   - Updates `ra_mst_owners` table

4. **`scripts/statistics_workers/populate_pedigree_statistics.py`**
   - Queries `ra_mst_race_results` table
   - Groups by class/distance for each sire/dam/damsire
   - Calculates performance breakdowns
   - Updates `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires` tables

### Option 2: Pure Database Approach

**Use only database queries for all statistics**

**Advantages:**
- ✅ No API calls needed (faster, no rate limits)
- ✅ Single source of truth (database)

**Disadvantages:**
- ❌ Requires complete historical data in database
- ❌ Database might not have ALL historical races

**Workers:**
- Same as Option 1, but query `ra_mst_race_results` instead of API

---

## 💻 Implementation Plan

### Phase 1: Time-Based Statistics (Quick Win)

**Estimated Time:** 2-3 hours
**Impact:** Populates 12 columns (4 each for jockeys/trainers/owners)

1. Create `scripts/statistics_workers/` directory
2. Implement `populate_jockey_statistics.py`
3. Implement `populate_trainer_statistics.py`
4. Implement `populate_owner_statistics.py`
5. Test on sample data
6. Run full population

**Code Structure:**
```python
# scripts/statistics_workers/populate_jockey_statistics.py

from datetime import datetime, date
from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('jockey_statistics')

def calculate_jockey_statistics(jockey_id: str, api_client: RacingAPIClient) -> dict:
    """Calculate time-based statistics for a jockey"""

    # Fetch all results
    results = api_client._make_request(f'/jockeys/{jockey_id}/results', params={'limit': 1000})

    if not results or not results.get('results'):
        return {}

    races = results['results']

    # Find last ride
    if races:
        last_ride = races[0]  # Results are ordered by date desc
        last_ride_date = datetime.strptime(last_ride['date'], '%Y-%m-%d').date()
        days_since_last_ride = (date.today() - last_ride_date).days
    else:
        last_ride_date = None
        days_since_last_ride = None

    # Find last win
    winning_races = [r for r in races if any(runner['position'] == '1' and runner.get('jockey_id') == jockey_id for runner in r.get('runners', []))]

    if winning_races:
        last_win = winning_races[0]
        last_win_date = datetime.strptime(last_win['date'], '%Y-%m-%d').date()
        days_since_last_win = (date.today() - last_win_date).days
    else:
        last_win_date = None
        days_since_last_win = None

    return {
        'last_ride_date': last_ride_date.isoformat() if last_ride_date else None,
        'last_win_date': last_win_date.isoformat() if last_win_date else None,
        'days_since_last_ride': days_since_last_ride,
        'days_since_last_win': days_since_last_win
    }

def main():
    config = get_config()
    api_client = RacingAPIClient(...)
    db_client = SupabaseReferenceClient(...)

    # Get all jockeys
    jockeys = db_client.client.table('ra_mst_jockeys').select('id, name').execute()

    logger.info(f"Processing {len(jockeys.data)} jockeys...")

    for idx, jockey in enumerate(jockeys.data):
        logger.info(f"[{idx+1}/{len(jockeys.data)}] Processing {jockey['name']}...")

        stats = calculate_jockey_statistics(jockey['id'], api_client)

        if stats:
            db_client.client.table('ra_mst_jockeys').update(stats).eq('id', jockey['id']).execute()
            logger.info(f"  ✓ Updated statistics")

        # Rate limiting
        time.sleep(0.5)

if __name__ == '__main__':
    main()
```

---

### Phase 2: Pedigree Performance Statistics (Complex)

**Estimated Time:** 4-6 hours
**Impact:** Populates 117 columns (39 each for sires/dams/damsires)

1. Implement `populate_pedigree_statistics.py`
2. Create SQL queries for class/distance aggregation
3. Calculate AE indices
4. Test on sample data
5. Run full population

**Code Structure:**
```python
# scripts/statistics_workers/populate_pedigree_statistics.py

def calculate_sire_statistics(sire_id: str, db_client) -> dict:
    """Calculate performance statistics for a sire"""

    # Query all results where sire appears
    query = """
    SELECT
        r.class,
        r.distance_f,
        r.distance_m,
        rr.position,
        rr.sp_decimal
    FROM ra_mst_race_results rr
    JOIN ra_mst_races r ON rr.race_id = r.id
    WHERE rr.sire_id = %s
    """

    results = db_client.execute_query(query, (sire_id,))

    # Group by class
    class_stats = {}
    for result in results:
        class_name = result['class'] or 'Unknown'
        if class_name not in class_stats:
            class_stats[class_name] = {'runners': 0, 'wins': 0}

        class_stats[class_name]['runners'] += 1
        if result['position'] == 1:
            class_stats[class_name]['wins'] += 1

    # Calculate win percentages
    for class_name, stats in class_stats.items():
        stats['win_percent'] = (stats['wins'] / stats['runners'] * 100) if stats['runners'] > 0 else 0

    # Get top 3 classes
    top_classes = sorted(class_stats.items(), key=lambda x: x[1]['win_percent'], reverse=True)[:3]

    # Similar logic for distances...

    return {
        'class_1_name': top_classes[0][0] if len(top_classes) > 0 else None,
        'class_1_runners': top_classes[0][1]['runners'] if len(top_classes) > 0 else None,
        # ... etc
    }
```

---

## 📅 Execution Timeline

| Phase | Time | Impact |
|-------|------|--------|
| **Phase 1: Time-based stats** | 2-3 hours | 12 columns (jockeys/trainers/owners) |
| **Phase 2: Pedigree stats** | 4-6 hours | 117 columns (sires/dams/damsires) |
| **Phase 3: Analytics tables** | 2-3 hours | 14 columns (combinations/distance/venue) |
| **Total** | **8-12 hours** | **143 columns** |

**Remaining 31 columns:**
- Statistics analytics tables (ra_entity_combinations, ra_performance_by_distance, ra_performance_by_venue, ra_runner_statistics)
- These are calculated from `ra_mst_race_results` data
- Simpler aggregations

---

## 🎯 Final Coverage Projection

**Current State:**
- Raw Coverage: 333/507 (65.7%)
- Actual Coverage: 333/333 (100% for core data)

**After Statistics Workers:**
- Raw Coverage: 476/507 (93.9%)
- Actual Coverage: 476/476 (100% including statistics)

**Remaining 31 NULL columns:**
- AE indices (requires market probability calculations)
- Profit/loss tracking (requires bet simulation)
- Query filters (metadata, not critical)

---

## ✅ Next Steps

1. **Create workers directory structure:**
   ```
   scripts/statistics_workers/
   ├── __init__.py
   ├── populate_jockey_statistics.py
   ├── populate_trainer_statistics.py
   ├── populate_owner_statistics.py
   ├── populate_pedigree_statistics.py
   └── README.md
   ```

2. **Implement Phase 1 workers** (time-based statistics)

3. **Test on sample data** (10-20 entities)

4. **Run full population** (all jockeys/trainers/owners)

5. **Implement Phase 2 workers** (pedigree statistics)

6. **Validate coverage** reaches 93.9%

---

## 📚 Related Documentation

- `docs/NULL_COLUMN_CATEGORIZATION.md` - Complete NULL categorization
- `docs/100_PERCENT_COVERAGE_ACHIEVEMENT.md` - Current coverage status
- `logs/racing_api_endpoint_discovery.json` - API endpoint testing results

---

**Last Updated:** 2025-10-23
**Status:** ✅ READY TO IMPLEMENT
**Estimated Effort:** 8-12 hours to reach 93.9% raw coverage
