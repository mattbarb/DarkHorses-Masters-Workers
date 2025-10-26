# API Developer Quick Reference

**Quick Start Guide for DarkHorses Racing API Development**

---

## 📊 Database Tables Overview

| Table | Primary Key | Purpose | Row Count (Typical) |
|-------|-------------|---------|---------------------|
| **ra_mst_races** | race_id | Race details | ~50k races/year |
| **ra_mst_runners** | runner_id | Runner + Results | ~500k runners/year |
| **ra_horses** | horse_id | Horse reference | ~50k horses |
| **ra_jockeys** | jockey_id | Jockey reference | ~500 jockeys |
| **ra_trainers** | trainer_id | Trainer reference | ~1000 trainers |
| **ra_owners** | owner_id | Owner reference | ~20k owners |
| **ra_courses** | course_id | Course reference | ~60 courses |

---

## 🔑 Key Relationships

```
ra_mst_races (1) ──────► (N) ra_mst_runners
                         ├─► (1) ra_horses
                         ├─► (1) ra_jockeys
                         ├─► (1) ra_trainers
                         └─► (1) ra_owners
```

---

## 🎯 Most Important Fields

### Race Data (ra_mst_races)
```sql
race_id              -- Unique identifier
course_name          -- e.g., "Newmarket"
race_date            -- DATE
off_datetime         -- TIMESTAMPTZ (with timezone)
race_type            -- "Flat", "Hurdle", "Chase"
race_class           -- "Class 1", "Group 1", etc.
distance_meters      -- INTEGER (in meters)
surface              -- "Turf", "AW", "Sand"
going                -- "Good", "Soft", "Heavy"
prize_money          -- DECIMAL (total prize fund)
field_size           -- INTEGER (number of runners)
```

### Runner Data (ra_mst_runners)
```sql
runner_id            -- Unique identifier
race_id              -- FK to ra_mst_races
horse_id             -- FK to ra_horses
jockey_id            -- FK to ra_jockeys
trainer_id           -- FK to ra_trainers
owner_id             -- FK to ra_owners

-- Pre-Race
number               -- Cloth number
draw                 -- Stall draw
weight_lbs           -- Weight carried
official_rating      -- Handicap rating
racing_post_rating   -- RPR
form                 -- Form string "121-"

-- Results (NULL until race finishes)
position             -- Finishing position (1, 2, 3, ...)
distance_beaten      -- Distance behind winner
prize_won            -- Prize money for this race
starting_price       -- Starting odds "5/2F"
finishing_time       -- Race time "1:48.55"
```

---

## 📋 Common Queries

### Get Today's Races
```sql
SELECT
    race_id,
    course_name,
    race_name,
    off_datetime,
    race_type,
    race_class,
    distance_meters,
    field_size
FROM ra_mst_races
WHERE race_date = CURRENT_DATE
ORDER BY off_datetime;
```

### Get Runners for a Race
```sql
SELECT
    r.runner_id,
    r.number,
    r.draw,
    h.name AS horse_name,
    j.name AS jockey_name,
    t.name AS trainer_name,
    r.weight_lbs,
    r.official_rating,
    r.racing_post_rating,
    r.form,
    r.position,
    r.starting_price
FROM ra_mst_runners r
JOIN ra_horses h ON r.horse_id = h.horse_id
LEFT JOIN ra_jockeys j ON r.jockey_id = j.jockey_id
LEFT JOIN ra_trainers t ON r.trainer_id = t.trainer_id
WHERE r.race_id = 'rac_12345678'
ORDER BY r.number;
```

### Get Horse Career Stats
```sql
SELECT
    h.name AS horse_name,
    COUNT(*) AS total_races,
    COUNT(*) FILTER (WHERE r.position = 1) AS wins,
    COUNT(*) FILTER (WHERE r.position <= 3) AS places,
    ROUND(
        COUNT(*) FILTER (WHERE r.position = 1)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS win_rate_pct,
    SUM(r.prize_won) AS total_earnings
FROM ra_horses h
LEFT JOIN ra_mst_runners r ON h.horse_id = r.horse_id
WHERE h.horse_id = 'hrs_12345678'
  AND r.position IS NOT NULL
GROUP BY h.horse_id, h.name;
```

### Get Recent Form (Last 5 Races)
```sql
SELECT
    races.race_date,
    races.course_name,
    r.position,
    r.distance_beaten,
    r.starting_price
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
WHERE r.horse_id = 'hrs_12345678'
  AND r.position IS NOT NULL
ORDER BY races.race_date DESC
LIMIT 5;
```

### Get Course-Specific Performance
```sql
SELECT
    c.name AS course_name,
    COUNT(*) AS runs,
    COUNT(*) FILTER (WHERE r.position = 1) AS wins,
    ROUND(
        COUNT(*) FILTER (WHERE r.position = 1)::NUMERIC /
        NULLIF(COUNT(*), 0) * 100,
        2
    ) AS win_rate
FROM ra_mst_runners r
JOIN ra_mst_races races ON r.race_id = races.race_id
JOIN ra_courses c ON races.course_id = c.course_id
WHERE r.horse_id = 'hrs_12345678'
  AND r.position IS NOT NULL
  AND c.course_id = 'crs_12345'
GROUP BY c.course_id, c.name;
```

---

## 🧮 Calculated Metrics

### Win Rate
```sql
ROUND(
    COUNT(*) FILTER (WHERE position = 1)::NUMERIC /
    NULLIF(COUNT(*), 0) * 100,
    2
) AS win_rate
```

### Place Rate (Top 3)
```sql
ROUND(
    COUNT(*) FILTER (WHERE position IN (1,2,3))::NUMERIC /
    NULLIF(COUNT(*), 0) * 100,
    2
) AS place_rate
```

### Average Finish Position
```sql
ROUND(
    AVG(position) FILTER (WHERE position IS NOT NULL),
    2
) AS avg_position
```

### Days Since Last Run
```sql
CURRENT_DATE - MAX(race_date) AS days_since_last_run
```

### Recent Form Score (Python)
```python
def calculate_form_score(last_5_positions):
    """
    Calculate weighted form score from last 5 positions
    Returns 0-100 score
    """
    if not last_5_positions:
        return None

    weights = [2.0, 1.5, 1.2, 1.0, 1.0]  # Recent weighted higher
    points = {1: 10, 2: 7, 3: 5, 4: 3}  # Points per position

    score = 0
    max_score = sum(w * 10 for w in weights)  # Max possible

    for position, weight in zip(last_5_positions, weights):
        score += points.get(position, 1) * weight

    return round((score / max_score) * 100, 2)
```

---

## 🚦 Data Availability

| Field Type | Availability | Notes |
|------------|--------------|-------|
| Core race data | 95%+ | Always present |
| Core runner data | 95%+ | Always present |
| Ratings (OR, RPR) | 80%+ | Varies by plan |
| Position data | 95%+ | NULL for non-finishers (F, PU) |
| Prize won | 90%+ | Winners and placed horses |
| Pedigree | 95%+ | Sire, dam, damsire |
| Comments | 70%+ | Pro plan features |
| Weather details | 40%+ | Often not provided |

---

## ⚠️ Important Notes

### Position Data
- `position` is **NULL** for:
  - Races that haven't finished yet
  - Non-finishers (fell, pulled up, etc.)
- Always check `position IS NOT NULL` when calculating stats

### Foreign Keys
- Always use LEFT JOIN for entities (jockey, trainer, owner)
- Some runners may have NULL jockey_id/trainer_id

### Dates & Times
- `race_date` is DATE type (YYYY-MM-DD)
- `off_datetime` is TIMESTAMPTZ (includes timezone)
- Always use `off_datetime` for sorting today's races

### IDs
- All IDs are VARCHAR (e.g., "hrs_12345678", "rac_12345678")
- Never assume IDs are numeric
- IDs come from Racing API and are stable

### Ratings
- Rating fields can be NULL (horse not rated)
- API returns "-" which is parsed to NULL
- Different ratings available on different plan tiers

---

## 🔍 Useful Filters

### Get Flat Races Only
```sql
WHERE race_type = 'Flat'
```

### Get National Hunt Races
```sql
WHERE race_type IN ('Hurdle', 'Chase', 'NH Flat')
```

### Get High-Value Races
```sql
WHERE prize_money >= 50000
```

### Get Recent Results (Last 7 Days)
```sql
WHERE race_date >= CURRENT_DATE - INTERVAL '7 days'
  AND position IS NOT NULL
```

### Get Winners Only
```sql
WHERE position = 1
```

### Get Placed Horses (Top 3)
```sql
WHERE position IN (1, 2, 3)
```

### Get Horses with Form
```sql
WHERE EXISTS (
    SELECT 1 FROM ra_mst_runners r2
    WHERE r2.horse_id = r.horse_id
      AND r2.position IS NOT NULL
)
```

---

## 📊 Performance Tips

### Always Use Indexes
```sql
-- These indexes already exist
CREATE INDEX idx_runners_race_id ON ra_mst_runners(race_id);
CREATE INDEX idx_runners_horse_id ON ra_mst_runners(horse_id);
CREATE INDEX idx_runners_position ON ra_mst_runners(position);
CREATE INDEX idx_races_race_date ON ra_mst_races(race_date);
```

### Optimize Calculated Stats
- Consider materialized views for expensive calculations
- Cache career statistics that don't change often
- Use partial indexes for common filters

### Pagination
```sql
-- Always paginate large result sets
SELECT ...
FROM ra_mst_races
WHERE race_date BETWEEN '2024-01-01' AND '2024-12-31'
ORDER BY off_datetime DESC
LIMIT 50 OFFSET 0;
```

---

## 🎨 API Response Example

```json
{
  "race": {
    "race_id": "rac_11746137",
    "course_name": "Wolverhampton (AW)",
    "race_name": "Download The Raceday Ready App Handicap",
    "race_date": "2025-10-11",
    "off_datetime": "2025-10-11T20:20:00+01:00",
    "race_type": "Flat",
    "race_class": "Class 6",
    "distance_meters": 1739,
    "surface": "AW",
    "going": "Standard",
    "prize_money": 5175.00,
    "field_size": 8
  },
  "runners": [
    {
      "runner_id": "rac_11746137_hrs_21866964",
      "number": 4,
      "draw": 4,
      "horse": {
        "horse_id": "hrs_21866964",
        "name": "River Wharfe (GB)",
        "age": 7,
        "sex": "G"
      },
      "jockey": {
        "jockey_id": "jky_309594",
        "name": "Jack Doughty"
      },
      "trainer": {
        "trainer_id": "trn_87426",
        "name": "Tony Carroll"
      },
      "weight_lbs": 131,
      "official_rating": 56,
      "racing_post_rating": 64,
      "form": "542-",
      "result": {
        "position": 1,
        "distance_beaten": "0",
        "prize_won": 3245.08,
        "starting_price": "11/4",
        "finishing_time": "1:48.55"
      },
      "career_stats": {
        "total_races": 45,
        "wins": 8,
        "places": 15,
        "win_rate": 17.78,
        "total_earnings": 28450.00
      }
    }
  ]
}
```

---

## 📚 Full Documentation

For complete details, see:
- **Field Mappings**: `/docs/DATA_SOURCES_FOR_API.md` (100+ pages)
- **System Architecture**: `/docs/ARCHITECTURE.md`
- **How It Works**: `/docs/HOW_IT_WORKS.md`

---

## 🧪 Test Connection

```python
from supabase import create_client

# Initialize client
supabase = create_client(
    "https://amsjvmlaknnvppxsgpfk.supabase.co",
    "[YOUR_SERVICE_KEY]"
)

# Test query
result = supabase.table('ra_mst_races').select('*').limit(1).execute()
print(f"Connected! Sample race: {result.data[0]['race_name']}")
```

---

**Last Updated**: 2025-10-14
**For Questions**: Review full documentation in `/docs/DATA_SOURCES_FOR_API.md`
