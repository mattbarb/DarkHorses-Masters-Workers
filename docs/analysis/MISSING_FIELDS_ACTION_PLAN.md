# Missing Fields - Action Plan

**Status:** Ready for Implementation
**Effort:** ~1 hour
**Risk:** Low
**Value:** High

---

## The Discovery

While analyzing the `/v1/jockeys/{jockey_id}/results` endpoint, we discovered that **we're not capturing 7 important fields** that are already available in our current `/v1/results` data source.

This is not about the jockey endpoint - it's about fields we're already getting from the API but not storing in the database.

---

## Missing Fields

### Critical (High Value for ML)

| Field | API Name | Example | Current Status | Database Column |
|-------|----------|---------|----------------|-----------------|
| Finishing Time | `time` | "1:27.07" | **NOT CAPTURED** | `finishing_time` |
| Starting Price (Decimal) | `sp_dec` | "19.00" | **NOT CAPTURED** | `starting_price_decimal` |
| Race Comment | `comment` | "Led final furlong..." | Schema exists, not populated | `comment` |
| Silk URL | `silk_url` | "https://..." | Schema exists, not populated | `silk_url` |

### Useful (Medium Value)

| Field | API Name | Example | Current Status | Database Column |
|-------|----------|---------|----------------|-----------------|
| Overall Beaten Distance | `ovr_btn` | "0" | **NOT CAPTURED** | `overall_beaten_distance` |
| Jockey Claim | `jockey_claim_lbs` | "5" | **NOT CAPTURED** | `jockey_claim_lbs` |
| Starting Price (Fractional) | `sp` | "18/1" | Partial capture | `starting_price_fractional` |

### Nice to Have (Low Priority)

| Field | API Name | Example | Current Status | Database Column |
|-------|----------|---------|----------------|-----------------|
| Weight (Stones-Lbs) | `weight` | "9-7" | Have `weight_lbs` only | `weight_stones_lbs` |

---

## Why This Matters

### 1. Finishing Time (`time`)

**Current Situation:**
```
We capture: position=3, distance_beaten=5.0
We know: Horse finished 3rd, beaten by 5 lengths
```

**What We're Missing:**
```
Finishing time: "1:27.07"
Winner's time: "1:26.50"
Standard time: "1:25.00"
```

**Why It's Critical:**
- **True Performance:** Position only shows relative performance, time shows absolute performance
- **Pace Analysis:** Can calculate early/late speed, identify closers vs front-runners
- **Track Conditions:** Compare actual time vs standard time to assess going
- **Form Analysis:** Horse that runs 1:26.50 for 2nd is better than horse that runs 1:30.00 for 1st in different race
- **ML Features:** Speed ratings, time-based handicapping, consistency analysis

**Example Use Case:**
```
Horse A: Position 3rd, time 1:27.07, standard 1:25.00 (slow by 2.07s)
Horse B: Position 1st, time 1:30.50, standard 1:25.00 (slow by 5.50s)

Horse A performed better despite lower position!
```

### 2. Starting Price Decimal (`sp_dec`)

**Current Situation:**
```
We capture: starting_price="18/1" (as text)
```

**What We're Missing:**
```
Decimal format: 19.00
```

**Why It Matters:**
- Easier calculations (no fraction parsing)
- Standard format for odds modeling
- Direct probability conversion: P = 1 / 19.00 = 5.26%
- Simplifies ML features

### 3. Race Comments (`comment`)

**Current Situation:**
```
Field exists in schema but not populated
```

**What We're Missing:**
```
"Travelled strongly - held up in rear - headway 14th -
bit short of room before 4 out - going best when led
after 2 out - clear last - hung left but went further
clear run-in - easily(op 9/1)"
```

**Why It Matters:**
- Tactical insights (held up, led, challenged)
- Running style identification (front runner, closer)
- Trip issues (short of room, hampered)
- Jockey instructions
- Natural language processing features

---

## Implementation Plan

### Step 1: Update Database Schema (15 minutes)

```sql
-- Add new columns to ra_mst_runners table
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS finishing_time TEXT;
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS starting_price_decimal DECIMAL(10,2);
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS starting_price_fractional TEXT;
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS overall_beaten_distance DECIMAL(10,2);
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS weight_stones_lbs TEXT;
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS jockey_claim_lbs INTEGER;

-- Verify existing columns (these should already exist)
-- comment TEXT
-- silk_url TEXT

-- Create index on finishing_time for performance analysis
CREATE INDEX IF NOT EXISTS idx_runners_finishing_time ON ra_mst_runners(finishing_time)
WHERE finishing_time IS NOT NULL;

-- Create index on starting_price_decimal
CREATE INDEX IF NOT EXISTS idx_runners_sp_decimal ON ra_mst_runners(starting_price_decimal)
WHERE starting_price_decimal IS NOT NULL;
```

### Step 2: Update results_fetcher.py (30 minutes)

**File:** `/fetchers/results_fetcher.py`

**Location:** In `_prepare_runner_records()` method, around line 307

**Current code:**
```python
runner_record = {
    'runner_id': runner_id,
    'race_id': race_id,
    'horse_id': horse_id,
    'horse_name': runner.get('horse'),
    # ... existing fields ...
    'position': position_data['position'],
    'distance_beaten': position_data['distance_beaten'],
    'prize_won': position_data['prize_won'],
    'starting_price': position_data['starting_price'],
    # ... rest of fields ...
}
```

**Add these fields:**
```python
runner_record = {
    # ... existing fields ...

    # ===== NEW FIELDS (from API, not yet captured) =====
    # Finishing time - CRITICAL for ML
    'finishing_time': runner.get('time'),  # e.g., "1:27.07"

    # Starting prices
    'starting_price_decimal': runner.get('sp_dec'),  # e.g., "19.00"
    'starting_price_fractional': runner.get('sp'),  # e.g., "18/1"

    # Additional performance metrics
    'overall_beaten_distance': runner.get('ovr_btn'),  # e.g., "0"

    # Weight format
    'weight_stones_lbs': runner.get('weight'),  # e.g., "9-7"

    # Jockey information
    'jockey_claim_lbs': parse_int_field(runner.get('jockey_claim_lbs')),  # e.g., 5

    # These fields exist in schema but were not being populated
    'comment': runner.get('comment'),  # Race comment
    'silk_url': runner.get('silk_url'),  # Silk image URL

    # ... rest of existing fields ...
}
```

**Also update races_fetcher.py** (same pattern)

**File:** `/fetchers/races_fetcher.py`

**Location:** In `_transform_racecard()` method, around line 268

Add the same fields to runner_record.

### Step 3: Update Supabase Client (5 minutes)

**File:** `/utils/supabase_client.py`

**Verify:** The `insert_runners()` method uses upsert, so new fields will automatically be handled. No code changes needed, but verify the method is passing all fields through.

### Step 4: Test (10 minutes)

```bash
# Test with recent data
python3 main.py --entities results --test

# Check database
psql $DATABASE_URL -c "
SELECT
    horse_name,
    position,
    finishing_time,
    starting_price_decimal,
    starting_price_fractional,
    comment
FROM ra_mst_runners
WHERE finishing_time IS NOT NULL
LIMIT 5;
"

# Verify data quality
python3 -c "
from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config

config = get_config()
db = SupabaseReferenceClient(
    url=config.supabase.url,
    service_key=config.supabase.service_key
)

result = db.client.table('ra_mst_runners').select('*').not_.is_('finishing_time', 'null').limit(10).execute()

for runner in result.data:
    print(f\"{runner['horse_name']}: {runner['position']} in {runner['finishing_time']}\")
    print(f\"  SP: {runner['starting_price_fractional']} = {runner['starting_price_decimal']}\")
    print(f\"  Comment: {runner['comment'][:100] if runner['comment'] else 'None'}...\")
    print()
"
```

---

## Validation Checklist

After implementation, verify:

- [ ] Database migration completed successfully
- [ ] New columns exist in `ra_mst_runners` table
- [ ] Indexes created
- [ ] `results_fetcher.py` updated
- [ ] `races_fetcher.py` updated
- [ ] Test fetch completes without errors
- [ ] `finishing_time` is populated (check sample records)
- [ ] `starting_price_decimal` is populated
- [ ] `starting_price_fractional` matches existing `starting_price` or is new
- [ ] `comment` is populated (at least for some records)
- [ ] `silk_url` is populated
- [ ] Data types are correct (decimal for sp_dec, text for time, etc.)
- [ ] No NULL values where data should exist
- [ ] Full production fetch works correctly

---

## Sample Queries After Implementation

### Check Finishing Times
```sql
SELECT
    r.race_date,
    r.course_name,
    r.race_name,
    ru.horse_name,
    ru.position,
    ru.finishing_time,
    ru.distance_beaten
FROM ra_mst_runners ru
JOIN ra_mst_races r ON ru.race_id = r.race_id
WHERE ru.finishing_time IS NOT NULL
ORDER BY r.race_date DESC, r.race_id, ru.position::INTEGER
LIMIT 20;
```

### Fastest Times by Distance
```sql
SELECT
    r.distance_f,
    ru.horse_name,
    ru.finishing_time,
    r.going,
    r.course_name,
    r.race_date
FROM ra_mst_runners ru
JOIN ra_mst_races r ON ru.race_id = r.race_id
WHERE ru.finishing_time IS NOT NULL
    AND ru.position = '1'
    AND r.distance_f BETWEEN 7.9 AND 8.1  -- About 1 mile
ORDER BY ru.finishing_time ASC
LIMIT 10;
```

### Analyze Odds Accuracy
```sql
SELECT
    ru.starting_price_decimal::DECIMAL(10,2) as odds,
    ru.position,
    COUNT(*) as races,
    SUM(CASE WHEN ru.position = '1' THEN 1 ELSE 0 END) as wins,
    ROUND(100.0 * SUM(CASE WHEN ru.position = '1' THEN 1 ELSE 0 END) / COUNT(*), 2) as win_pct,
    ROUND(100.0 / AVG(ru.starting_price_decimal::DECIMAL(10,2)), 2) as implied_prob
FROM ra_mst_runners ru
WHERE ru.starting_price_decimal IS NOT NULL
GROUP BY 1, 2
ORDER BY 1, 2;
```

### Performance Comments Analysis
```sql
SELECT
    horse_name,
    position,
    finishing_time,
    comment
FROM ra_mst_runners
WHERE comment LIKE '%easily%'
    AND position = '1'
ORDER BY finishing_time ASC
LIMIT 10;
```

---

## ML Feature Examples

### Time-Based Features

```python
# Speed rating (simple version)
def calculate_speed_rating(finishing_time_seconds, distance_meters, going='Good'):
    """Calculate simple speed rating"""
    going_adjustment = {
        'Firm': 0.95,
        'Good to Firm': 0.97,
        'Good': 1.00,
        'Good to Soft': 1.03,
        'Soft': 1.05,
        'Heavy': 1.10
    }

    adjustment = going_adjustment.get(going, 1.00)
    adjusted_time = finishing_time_seconds * adjustment
    meters_per_second = distance_meters / adjusted_time

    # Normalize to rating scale (e.g., 0-100)
    speed_rating = meters_per_second * 10  # Simplified

    return speed_rating

# Time conversion
def parse_finishing_time(time_str):
    """Convert 'M:SS.ss' to seconds"""
    if ':' in time_str:
        parts = time_str.split(':')
        minutes = int(parts[0])
        seconds = float(parts[1])
        return minutes * 60 + seconds
    return float(time_str)

# Example
time = "1:27.07"
distance = 1600  # meters
seconds = parse_finishing_time(time)  # 87.07
rating = calculate_speed_rating(seconds, distance)
```

### Pace Analysis

```python
def analyze_pace_distribution(race_times):
    """Identify early vs late speed"""
    winner_time = min(race_times)

    for horse_time in race_times:
        time_behind = horse_time - winner_time

        # Classify pace
        if time_behind < 2.0:
            pace_type = "front_runner"
        elif time_behind < 5.0:
            pace_type = "prominent"
        else:
            pace_type = "held_up"

    return pace_type
```

### Consistency Features

```python
def calculate_time_consistency(horse_times):
    """Measure performance consistency"""
    if len(horse_times) < 3:
        return None

    mean_time = np.mean(horse_times)
    std_time = np.std(horse_times)

    # Coefficient of variation
    consistency_score = (std_time / mean_time) * 100

    # Lower is more consistent
    return consistency_score
```

---

## Expected Impact

### Data Quality
- **+30%** completeness (7 new fields)
- **+100%** ML feature potential (time-based analysis)
- **Better** odds analysis (decimal format)
- **Richer** context (comments)

### ML Models
- **New features:** Speed ratings, pace analysis, time consistency
- **Better features:** Odds as decimal, normalized starting prices
- **Context features:** Running style from comments (NLP)
- **Performance metrics:** True speed vs relative position

### Development
- **No complexity:** Simple additive changes
- **No risk:** Existing data unchanged
- **Fast:** ~1 hour implementation
- **High ROI:** Major ML value for minimal effort

---

## Files to Modify

1. **Database Migration**
   - Create: `migrations/add_runner_finishing_time_fields.sql`

2. **Fetcher Updates**
   - Edit: `fetchers/results_fetcher.py` (line ~307)
   - Edit: `fetchers/races_fetcher.py` (line ~268)

3. **Documentation**
   - Update: `docs/data/FIELD_MAPPING.md` (if exists)
   - Update: `README.md` (mention new fields)

4. **Tests**
   - Update: `tests/test_results_fetcher.py` (verify new fields)
   - Create: `tests/test_finishing_time_parsing.py`

---

## Timeline

| Task | Time | Status |
|------|------|--------|
| Database migration | 15 min | Not started |
| Update results_fetcher.py | 20 min | Not started |
| Update races_fetcher.py | 10 min | Not started |
| Testing | 10 min | Not started |
| Validation | 5 min | Not started |
| **Total** | **~1 hour** | **Ready to start** |

---

## Success Criteria

Implementation is successful when:

1. ✓ All 7 new fields are captured from API
2. ✓ Database schema updated
3. ✓ No errors during fetch
4. ✓ `finishing_time` populated for >95% of result records
5. ✓ `starting_price_decimal` populated for >95% of records
6. ✓ `comment` populated for >80% of records
7. ✓ Data types correct (decimal, text, integer)
8. ✓ Full production fetch completes successfully
9. ✓ ML team can access finishing times for analysis
10. ✓ Documentation updated

---

## Questions?

**Q: Why didn't we capture these fields before?**
A: We were focused on position-based results (1st, 2nd, 3rd). Finishing times weren't recognized as critical for ML until now.

**Q: Will this break anything?**
A: No. These are additive changes. Existing data and code unchanged.

**Q: Do we need to backfill historical data?**
A: No. New fields will populate for new fetches. Historical data can be backfilled later if needed (we have it in `api_data` JSONB column).

**Q: What about the jockey endpoint?**
A: Not needed. All these fields are already in `/v1/results`. The jockey endpoint analysis just helped us discover what we were missing.

**Q: Is there a performance impact?**
A: Minimal. No additional API calls, just capturing more fields. Database queries might be slightly slower if querying time fields, but indexes will help.

---

**Status:** Ready for Implementation
**Priority:** High (especially for ML features)
**Effort:** Low (~1 hour)
**Risk:** Low (additive changes only)

**Next Step:** Run database migration and update fetchers.
