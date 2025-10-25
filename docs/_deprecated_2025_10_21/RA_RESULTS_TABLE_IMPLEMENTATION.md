# ra_results Table Implementation

## Overview

✅ **NEW TABLE:** `ra_results` stores race-level result data from the Racing API `/v1/results` endpoint.

This separates result-specific data (tote pools, winning time, comments, non-runners) from the `ra_races` table which stores race metadata.

## Why This Table?

Previously, we were only storing:
- **ra_races** - Race metadata (course, time, distance, going, etc.)
- **ra_runners** - Runner-level data and positions

We were **missing** valuable race-level result data:
- ❌ Tote pool dividends (win, place, exacta, CSF, tricast, trifecta)
- ❌ Winning time with details (e.g., "1:48.55 (slow by 3.25s)")
- ❌ Race comments and stewards notes
- ❌ Non-runners information

## Table Structure

### Primary Key
- `race_id` (VARCHAR 50) - Links to `ra_races.race_id`

### Race Identification (Duplicated for Convenience)
- `course_id`, `course_name`, `race_name`
- `race_date`, `off_time`, `off_datetime`
- `region`

### Race Classification
- `type` - Race type (Flat, NH Flat, Hurdle, Chase)
- `class` - Race class
- `pattern` - Pattern race indicator
- `rating_band`, `age_band`, `sex_rest`

### Distance Information
- `dist` - Distance string (e.g., "1m 2f")
- `dist_y` - Distance in yards
- `dist_m` - Distance in meters
- `dist_f` - Distance in furlongs

### Going and Surface
- `going` - Going description
- `surface` - Surface type
- `jumps` - Jumps information (for NH races)

### Result-Specific Data (NEW!)
- `winning_time_detail` - Winning time with details
- `comments` - Race comments/notes from stewards
- `non_runners` - Non-runners data

### Tote Pools (UK/IRE Betting)
- `tote_win` - Tote win dividend
- `tote_pl` - Tote place dividends (multiple values)
- `tote_ex` - Tote exacta
- `tote_csf` - Tote CSF (Computer Straight Forecast)
- `tote_tricast` - Tote tricast
- `tote_trifecta` - Tote trifecta

### Metadata
- `api_data` (JSONB) - Full API response
- `created_at`, `updated_at`

## Data Architecture

```
Racing API: /v1/results
    ↓
Results Fetcher
    ├─ Transform race data → ra_races (metadata)
    ├─ Transform result data → ra_results (tote pools, comments) ⭐ NEW
    └─ Transform runner data → ra_runners (positions, times)
```

## Example API Response

```json
{
  "race_id": "123456",
  "date": "2024-10-15",
  "region": "gb",
  "course": "Ascot",
  "course_id": "1",
  "off": "14:30",
  "off_dt": "2024-10-15T14:30:00",
  "race_name": "Queen Elizabeth II Stakes",
  "type": "Flat",
  "class": "1",
  "pattern": "Group 1",
  "dist": "1m",
  "dist_m": "1609",
  "going": "Good to Firm",
  "surface": "Turf",
  "winning_time_detail": "1:35.42 (fast by 1.23s)",
  "comments": "All stood well. Made all on rail.",
  "non_runners": "Horse withdrawn - lame",
  "tote_win": "3.20",
  "tote_pl": "1.80, 2.40, 1.60",
  "tote_ex": "8.70",
  "tote_csf": "7.42",
  "tote_tricast": "45.20",
  "tote_trifecta": "35.80",
  "runners": [...]
}
```

## Implementation Changes

### Migration 017: Create Table

**File:** `migrations/017_create_ra_results_table.sql`

- Creates `ra_results` table
- Adds foreign key constraint to `ra_races(race_id)`
- Creates indexes on common query fields
- Adds column comments

**Run in Supabase SQL Editor:**
```sql
-- Copy and paste entire migration file
```

### Results Fetcher Updates

**File:** `fetchers/results_fetcher.py`

**Changes:**
1. Added `results_to_insert` list alongside `races_to_insert`
2. Transform API response to extract result-specific fields
3. Call `db_client.insert_results(results_to_insert)` after races

**New code:**
```python
# Prepare result record for ra_results table
result_record = {
    'race_id': race_data.get('race_id'),
    'course_id': race_data.get('course_id'),
    # ... race identification ...
    # Result-specific data
    'winning_time_detail': race_data.get('winning_time_detail'),
    'comments': race_data.get('comments'),
    'non_runners': race_data.get('non_runners'),
    # Tote pools
    'tote_win': race_data.get('tote_win'),
    'tote_pl': race_data.get('tote_pl'),
    'tote_ex': race_data.get('tote_ex'),
    'tote_csf': race_data.get('tote_csf'),
    'tote_tricast': race_data.get('tote_tricast'),
    'tote_trifecta': race_data.get('tote_trifecta'),
    'api_data': race_data
}
```

### Supabase Client Updates

**File:** `utils/supabase_client.py`

**Added method:**
```python
def insert_results(self, results: List[Dict]) -> Dict:
    """
    Insert/update race results (ra_results table)

    This stores race-level result data including tote pools, winning time,
    comments, and non-runners. Runner-level results are stored in ra_runners.
    """
    logger.info(f"Inserting {len(results)} results")
    return self.upsert_batch('ra_results', results, 'race_id')
```

## Deployment Steps

### 1. Run Migration

In Supabase SQL Editor:
1. Open `migrations/017_create_ra_results_table.sql`
2. Copy all contents
3. Paste into SQL Editor
4. Click "Run"

**Verification:**
```sql
-- Check table exists
SELECT COUNT(*) FROM ra_results;

-- Check structure
\d ra_results;

-- Verify foreign key
SELECT
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_name = 'ra_results';
```

### 2. Deploy Code Changes

**Files changed:**
- `fetchers/results_fetcher.py` - Transform and store results
- `utils/supabase_client.py` - Added `insert_results()` method

**Deploy:**
```bash
git add migrations/017_create_ra_results_table.sql
git add fetchers/results_fetcher.py
git add utils/supabase_client.py
git add RA_RESULTS_TABLE_IMPLEMENTATION.md
git commit -m "Add ra_results table for race-level result data (tote pools, comments)"
git push
```

### 3. Test Results Collection

Run results fetcher to populate table:
```bash
# Fetch last 7 days of results
python3 main.py --entities results --test
```

**Expected logs:**
```
Inserting 45 races into ra_races and ra_results...
Inserting 45 results into ra_results...
Results inserted: {'inserted': 45, 'updated': 0, 'errors': 0}
```

### 4. Verify Data Population

```sql
-- Check result count
SELECT COUNT(*) FROM ra_results;

-- Sample tote data
SELECT
  race_id,
  course_name,
  race_name,
  tote_win,
  tote_pl,
  tote_ex,
  tote_csf
FROM ra_results
WHERE tote_win IS NOT NULL
ORDER BY race_date DESC
LIMIT 10;

-- Check winning time data
SELECT
  race_id,
  course_name,
  winning_time_detail,
  comments
FROM ra_results
WHERE winning_time_detail IS NOT NULL
ORDER BY race_date DESC
LIMIT 10;

-- Check non-runners
SELECT
  race_id,
  course_name,
  race_name,
  non_runners
FROM ra_results
WHERE non_runners IS NOT NULL
ORDER BY race_date DESC
LIMIT 10;
```

## Data Relationships

```
ra_races (race metadata)
    ↑
    | (1:1 relationship)
    |
ra_results (result data: tote, comments)
    ↓
    | (1:N relationship)
    ↓
ra_runners (runner results: positions, times)
```

## Query Examples

### Get Complete Race Result

```sql
SELECT
  r.race_id,
  r.course_name,
  r.race_name,
  r.race_date,
  r.off_time,
  r.going,
  res.winning_time_detail,
  res.comments,
  res.tote_win,
  res.tote_ex,
  res.tote_csf
FROM ra_races r
LEFT JOIN ra_results res ON res.race_id = r.race_id
WHERE r.race_date = '2024-10-15'
ORDER BY r.off_time;
```

### Analyze Tote Returns

```sql
-- Average tote win dividend by course
SELECT
  course_name,
  COUNT(*) as races,
  AVG(CAST(tote_win AS DECIMAL)) as avg_tote_win,
  MIN(CAST(tote_win AS DECIMAL)) as min_tote_win,
  MAX(CAST(tote_win AS DECIMAL)) as max_tote_win
FROM ra_results
WHERE tote_win IS NOT NULL
  AND tote_win ~ '^[0-9.]+$'  -- Filter numeric values only
GROUP BY course_name
ORDER BY races DESC
LIMIT 20;
```

### Find Races with Comments

```sql
SELECT
  race_id,
  course_name,
  race_name,
  comments,
  winning_time_detail
FROM ra_results
WHERE comments IS NOT NULL
  AND comments != ''
ORDER BY race_date DESC
LIMIT 20;
```

### Non-Runners Analysis

```sql
SELECT
  course_name,
  COUNT(*) as races_with_non_runners,
  AVG(ARRAY_LENGTH(STRING_TO_ARRAY(non_runners, ','), 1)) as avg_non_runners
FROM ra_results
WHERE non_runners IS NOT NULL
  AND non_runners != ''
GROUP BY course_name
ORDER BY races_with_non_runners DESC;
```

## Benefits for ML Models

### Tote Pool Data
- **Market sentiment:** Tote dividends reflect betting patterns
- **Value detection:** Compare model predictions with tote returns
- **Favorite analysis:** Identify tote favorites vs predictions

### Winning Time Details
- **Pace analysis:** Fast/slow times relative to standard
- **Track conditions:** How going affects times
- **Performance metrics:** Speed figures based on actual times

### Race Comments
- **Incident detection:** Races with interference/problems
- **Running style:** How races were run (made all, held up, etc.)
- **Context enrichment:** Additional race narrative

### Non-Runners
- **Market movements:** How withdrawals affect prices
- **Field size impact:** Smaller fields may affect results
- **Trainer/course patterns:** Who tends to withdraw

## Monitoring

### Daily Checks

```sql
-- Check today's results captured
SELECT COUNT(*) as results_today
FROM ra_results
WHERE race_date = CURRENT_DATE;

-- Check tote data completeness
SELECT
  COUNT(*) as total_results,
  COUNT(tote_win) as has_tote_win,
  ROUND(100.0 * COUNT(tote_win) / COUNT(*), 2) as tote_coverage_pct
FROM ra_results
WHERE race_date >= CURRENT_DATE - INTERVAL '7 days';
```

### Data Quality

```sql
-- Find results without tote data
SELECT
  race_id,
  course_name,
  race_name,
  race_date
FROM ra_results
WHERE tote_win IS NULL
  AND race_date >= CURRENT_DATE - INTERVAL '7 days'
ORDER BY race_date DESC;
```

## Troubleshooting

### No Results Inserted

**Check:**
1. Migration ran successfully: `SELECT COUNT(*) FROM ra_results;`
2. Foreign key constraint exists (prevents orphaned results)
3. `ra_races` records exist first (results depend on races)

**Solution:**
- Ensure `ra_races` inserts happen before `ra_results`
- Check foreign key constraint is not blocking inserts

### Missing Tote Data

**Cause:** Not all races have tote pools (e.g., some Irish races)

**Normal Behavior:** Expect ~70-80% coverage for GB races, less for IRE

### API Data in JSONB

If specific fields are NULL but you need data:
```sql
-- Query from api_data JSONB field
SELECT
  race_id,
  api_data->>'tote_win' as tote_win_from_json,
  api_data->>'comments' as comments_from_json
FROM ra_results
WHERE tote_win IS NULL
LIMIT 10;
```

## Summary

✅ **Implemented:**
- New `ra_results` table with all result-specific fields
- Migration 017 with foreign key constraints
- Updated `results_fetcher.py` to transform and store results
- Added `insert_results()` method to `supabase_client.py`

✅ **Data Captured:**
- Tote pool dividends (6 types)
- Winning time with details
- Race comments and stewards notes
- Non-runners information

✅ **Ready for:**
- ML model enrichment
- Betting analysis
- Market sentiment analysis
- Performance metrics

---

**Next Steps:**
1. Run Migration 017 in Supabase
2. Deploy code changes to production
3. Test with recent results fetch
4. Verify data population
5. Update ML models to use new data
