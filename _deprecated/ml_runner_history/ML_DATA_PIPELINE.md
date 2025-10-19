# ML Runner History Pipeline Documentation

## Overview

The ML Runner History Pipeline is an autonomous data compilation system that prepares race data for machine learning predictions. It runs daily at 6:00 AM UTC and compiles complete historical performance data for all runners in upcoming races.

## Table of Contents

1. [Architecture](#architecture)
2. [Database Schema](#database-schema)
3. [Compilation Process](#compilation-process)
4. [Deployment](#deployment)
5. [Monitoring](#monitoring)
6. [Usage](#usage)
7. [Troubleshooting](#troubleshooting)

---

## Architecture

### Components

```
┌─────────────────────────────────────────────────────────────┐
│                   DAILY SCHEDULE (6 AM UTC)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. update_daily_data.py                                    │
│     └─> Fetches upcoming racecards (next 7 days)           │
│     └─> Stores in ra_races + ra_runners                    │
│                                                             │
│  2. compile_ml_data.py (NEW)                                │
│     └─> Identifies upcoming runners                        │
│     └─> Compiles complete history per runner               │
│     └─> Calculates statistics & metrics                    │
│     └─> Stores in dh_ml_runner_history                     │
│                                                             │
│  3. ml_data_monitor.py                                      │
│     └─> Validates data quality                             │
│     └─> Checks coverage & freshness                        │
│     └─> Alerts on issues                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
┌──────────────┐      ┌──────────────┐      ┌─────────────────────┐
│  ra_races    │      │ ra_runners   │      │ dh_ml_runner_history│
│  (upcoming)  │──┐   │ (historical) │──┐   │  (ML-ready)         │
└──────────────┘  │   └──────────────┘  │   └─────────────────────┘
                  │                     │            ▲
                  │   ┌──────────────┐  │            │
                  └──>│ ra_horses    │──┘            │
                      └──────────────┘               │
                            │                        │
                      ┌──────────────┐               │
                      │ ra_jockeys   │───────────────┤
                      └──────────────┘               │
                            │                        │
                      ┌──────────────┐               │
                      │ ra_trainers  │───────────────┤
                      └──────────────┘               │
                            │                        │
                      ┌──────────────┐               │
                      │ ra_courses   │───────────────┘
                      └──────────────┘
```

---

## Database Schema

### dh_ml_runner_history Table

**Purpose**: Denormalized table containing complete runner history optimized for ML

**Key Fields**:

| Category | Fields | Description |
|----------|--------|-------------|
| **Identification** | `id`, `race_id`, `runner_id`, `horse_id` | Unique identifiers |
| **Race Context** | `race_date`, `course_id`, `distance_meters`, `going`, `race_class` | Upcoming race details |
| **Career Stats** | `total_races`, `total_wins`, `win_rate`, `place_rate` | All-time performance |
| **Context Performance** | `course_runs`, `course_wins`, `distance_wins`, `going_wins` | Specific conditions |
| **Recent Form** | `last_5_positions[]`, `recent_form_score` | Recent performance |
| **Relationships** | `horse_jockey_wins`, `horse_trainer_wins` | Combination stats |
| **Historical Data** | `historical_races` (JSONB) | Complete race history |

**Indexes**:
- Primary: `race_id`, `runner_id`, `horse_id`, `race_date`
- Composite: `race_date + course_id`, `region + race_date`
- JSONB: `historical_races`, `jockey_career_stats`, `trainer_career_stats`

**Helper Views**:
- `v_ml_upcoming_races`: Summary of upcoming races with ML data
- `v_ml_data_quality`: Data quality metrics by race date

---

## Compilation Process

### 1. Identify Upcoming Runners

```python
# Query upcoming races (next 7 days)
SELECT * FROM ra_races
WHERE race_date >= CURRENT_DATE
  AND race_date <= CURRENT_DATE + INTERVAL '7 days'
  AND region IN ('gb', 'ire')

# Get runners for these races
SELECT * FROM ra_runners
WHERE race_id IN (upcoming_race_ids)
```

### 2. Compile Historical Data

For each runner:

```python
# Get all historical races for this horse
SELECT r.*, races.*
FROM ra_runners r
JOIN ra_races races ON races.race_id = r.race_id
WHERE r.horse_id = {horse_id}
  AND races.race_date < CURRENT_DATE
ORDER BY races.race_date DESC
```

### 3. Calculate Statistics

**Career Statistics**:
- Total races, wins, places (1st, 2nd, 3rd)
- Win rate = (wins / total_races) * 100
- Place rate = (places / total_races) * 100
- Average finish position
- Days since last run

**Context-Specific Performance**:
- Course: races at same course
- Distance: races at similar distance (±10%)
- Surface: races on same surface (flat/jump)
- Going: races on similar going
- Class: races in same class

**Recent Form**:
- Last 5 positions: `[1, 3, 2, 5, 4]`
- Form score (0-100): Weighted by recency
  - Win = 10 pts, 2nd = 7, 3rd = 5, 4th = 3, 5th+ = 1
  - Most recent race weighted 2x

**Relationship Stats**:
- Horse + Jockey combination
- Horse + Trainer combination
- Jockey + Trainer combination

### 4. Store ML Record

```python
# Upsert to dh_ml_runner_history
INSERT INTO dh_ml_runner_history (...)
VALUES (...)
ON CONFLICT (runner_id, compilation_date)
DO UPDATE SET ...
```

### 5. Cleanup Old Data

```python
# Remove ML data for races older than 30 days
DELETE FROM dh_ml_runner_history
WHERE race_date < CURRENT_DATE - INTERVAL '30 days'
```

---

## Deployment

### Step 1: Run Database Migration

```bash
# Connect to your database
psql $DATABASE_URL

# Run migration
\i migrations/004_create_ml_runner_history.sql

# Verify
SELECT COUNT(*) FROM dh_ml_runner_history;
SELECT * FROM v_ml_upcoming_races LIMIT 5;
```

**Expected output**:
```
✓ Migration 004 Complete
Column count: 90+
Index count: 15+
```

### Step 2: Test Compilation Script

```bash
# Test in dry-run mode (no database writes)
python scripts/compile_ml_data.py --dry-run --days-ahead 7

# Test with limited scope
python scripts/compile_ml_data.py --days-ahead 1

# Full test
python scripts/compile_ml_data.py --days-ahead 7 --regions gb ire
```

**Expected output**:
```
ML RUNNER HISTORY COMPILATION - Starting
Found X upcoming races
Found Y upcoming runners
Compiled Y ML records
Successfully stored Y ML records
```

### Step 3: Verify Data Quality

```bash
# Run health check
python monitors/ml_data_monitor.py --health-check --verbose

# View metrics as JSON
python monitors/ml_data_monitor.py --json
```

**Expected metrics**:
```json
{
  "is_healthy": true,
  "data_freshness": "FRESH",
  "coverage_percentage": 95.0,
  "avg_historical_races": 8.5,
  "pct_with_5plus_races": 75.0
}
```

### Step 4: Add to Scheduler

The scheduler configuration has been updated in `config/scheduler_config.yaml`:

```yaml
ml_compilation:
  enabled: true
  frequency: "0 6 * * *"  # Daily at 6:00 AM UTC
  script: "scripts/compile_ml_data.py"
  args: "--days-ahead 7 --days-to-keep 30 --regions gb ire"
  timeout: 1800  # 30 minutes
  priority: high
  depends_on: "daily_data"
```

**Note**: Ensure your scheduler system supports the `depends_on` field, or manually sequence the jobs.

---

## Monitoring

### Health Checks

Run regularly (every 6 hours):

```bash
# Quick health check
python monitors/ml_data_monitor.py --health-check

# Detailed check with alerts
python monitors/ml_data_monitor.py --alert-on-issues --verbose
```

### Key Metrics to Monitor

1. **Data Freshness**
   - Alert if: compilation_age > 24 hours
   - Warning if: compilation_age > 12 hours

2. **Coverage**
   - Alert if: coverage < 50%
   - Warning if: coverage < 80%
   - Target: 90%+

3. **Historical Depth**
   - Target: avg > 5 races per horse
   - Warning if: avg < 3 races

4. **Form Completeness**
   - Target: 80%+ with last_5_positions
   - Target: 80%+ with form_score

### Database Queries

**Check latest compilation**:
```sql
SELECT
    MAX(compilation_date) as last_compiled,
    COUNT(*) as total_records,
    COUNT(DISTINCT race_date) as unique_race_dates
FROM dh_ml_runner_history
WHERE race_date >= CURRENT_DATE;
```

**Check coverage by date**:
```sql
SELECT * FROM v_ml_data_quality
ORDER BY race_date;
```

**Find gaps**:
```sql
-- Runners in upcoming races without ML data
SELECT r.runner_id, r.horse_name, races.race_date
FROM ra_runners r
JOIN ra_races races ON races.race_id = r.race_id
LEFT JOIN dh_ml_runner_history ml ON ml.runner_id = r.runner_id
WHERE races.race_date >= CURRENT_DATE
  AND races.race_date <= CURRENT_DATE + INTERVAL '7 days'
  AND ml.runner_id IS NULL;
```

---

## Usage

### For ML/Data Science

**Query upcoming races with complete history**:

```python
from supabase import create_client

supabase = create_client(url, key)

# Get all runners for tomorrow's races
tomorrow = (date.today() + timedelta(days=1)).isoformat()

response = supabase.table('dh_ml_runner_history')\
    .select('*')\
    .eq('race_date', tomorrow)\
    .eq('is_scratched', False)\
    .execute()

ml_data = response.data
```

**Key fields for ML models**:

```python
# Target variable (from results - to be added after race)
y = finish_position

# Feature categories
career_features = [
    'total_races', 'win_rate', 'place_rate',
    'avg_finish_position', 'days_since_last_run'
]

context_features = [
    'course_win_rate', 'distance_win_rate',
    'surface_win_rate', 'going_win_rate', 'class_win_rate'
]

form_features = [
    'last_5_positions', 'recent_form_score'
]

relationship_features = [
    'horse_jockey_win_rate', 'horse_trainer_win_rate'
]

race_features = [
    'distance_meters', 'race_class', 'field_size',
    'current_weight_lbs', 'current_draw', 'official_rating'
]
```

**Access full historical races**:

```python
# historical_races is a JSONB array
import json

for runner in ml_data:
    history = runner['historical_races']

    # Each race includes:
    # - race_date, course_name, distance, going
    # - position, weight, jockey, trainer
    # - race_class, field_size, etc.

    for past_race in history:
        print(f"{past_race['race']['race_date']}: "
              f"{past_race['race']['course_name']} - "
              f"Position: {past_race.get('position', 'N/A')}")
```

### Manual Compilation

**Compile for specific date range**:
```bash
python scripts/compile_ml_data.py \
    --days-ahead 14 \
    --regions gb ire
```

**Re-compile today's data**:
```bash
python scripts/compile_ml_data.py --days-ahead 1
```

---

## Troubleshooting

### Issue: No ML data compiled

**Symptoms**:
```
Found 0 upcoming races
Nothing to compile
```

**Checks**:
1. Verify ra_races has upcoming races:
   ```sql
   SELECT COUNT(*) FROM ra_races
   WHERE race_date >= CURRENT_DATE;
   ```

2. Check if daily_data ran successfully:
   ```bash
   python scripts/update_daily_data.py --dry-run
   ```

3. Check database connectivity:
   ```python
   python -c "from utils.supabase_client import SupabaseReferenceClient; \
              client = SupabaseReferenceClient(...); \
              print('Connected')"
   ```

### Issue: Low coverage (<50%)

**Symptoms**:
```
WARNING: Low ML coverage (45%). Only 150/333 runners compiled.
```

**Causes**:
1. Script timeout (default: 30 min)
2. API rate limits
3. Missing horse_id in ra_runners

**Solutions**:
1. Increase timeout in scheduler config
2. Run compilation multiple times
3. Fix missing horse_ids:
   ```sql
   SELECT COUNT(*) FROM ra_runners
   WHERE horse_id IS NULL;
   ```

### Issue: Historical races not populated

**Symptoms**:
```
historical_races_count = 0 for most runners
```

**Causes**:
1. No historical data in ra_runners for past races
2. JOIN issue in query

**Solutions**:
1. Check historical data exists:
   ```sql
   SELECT COUNT(*) FROM ra_races
   WHERE race_date < CURRENT_DATE;
   ```

2. Verify ra_runners has past race data:
   ```sql
   SELECT r.horse_id, COUNT(*) as races
   FROM ra_runners r
   JOIN ra_races races ON races.race_id = r.race_id
   WHERE races.race_date < CURRENT_DATE
   GROUP BY r.horse_id
   LIMIT 10;
   ```

3. Run historical backfill if needed

### Issue: Stale data (>24 hours old)

**Symptoms**:
```
WARNING: ML data is stale (36 hours old)
```

**Causes**:
1. Scheduler not running
2. Script failed silently
3. Lock file preventing execution

**Solutions**:
1. Check scheduler status
2. Review logs in `logs/compile_ml_data.log`
3. Remove stale lock files:
   ```bash
   rm /tmp/darkhorses_update_ml_compilation_*
   ```

---

## Performance

**Expected execution times**:
- 100 upcoming runners: 2-5 minutes
- 500 upcoming runners: 10-15 minutes
- 1000 upcoming runners: 20-30 minutes

**Optimization tips**:
1. Ensure database indexes are created (migration does this)
2. Batch queries where possible (script uses batching)
3. Consider running compilation twice daily during peak season
4. Monitor database query performance

**Database size impact**:
- Each ML record: ~2-10 KB (depends on historical_races JSONB size)
- 1000 runners: ~5-10 MB
- 30 days retention: ~150-300 MB

---

## Future Enhancements

Potential improvements:

1. **Odds Integration**
   - Fetch and store historical odds
   - Calculate odds movements
   - Add current_odds field

2. **Trainer/Jockey Stats**
   - Query ra_jockeys and ra_trainers for overall stats
   - Populate jockey_career_stats and trainer_career_stats

3. **Advanced Form Metrics**
   - Track performance trends (improving/declining)
   - Calculate speed figures
   - Distance suitability scores

4. **Weather Integration**
   - Store historical weather data
   - Correlate performance with weather

5. **Real-time Updates**
   - Update ML data when scratching occurs
   - Re-calculate when field changes

---

## Support

**Issues**:
- Check logs: `logs/compile_ml_data.log`
- Run health check: `python monitors/ml_data_monitor.py --verbose`
- Review git repo issues

**Questions**:
- See main README.md
- Review database audit reports in `docs/`

---

**Generated**: 2025-10-13
**Version**: 1.0
**Maintainer**: DarkHorses Development Team
