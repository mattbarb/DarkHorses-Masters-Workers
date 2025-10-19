# Field Quick Reference for ML API

**Quick lookup guide for database fields by category and ML importance**

---

## Tables at a Glance

| Table | Records | Primary Use | Key Fields |
|-------|---------|-------------|------------|
| `ra_horses` | 111,430 | Horse metadata | horse_id, dob, sex_code, colour, region |
| `ra_horse_pedigree` | 111,185+ | Pedigree lineage | sire_id, dam_id, damsire_id, breeder |
| `ra_jockeys` | 3,480 | Jockey reference | jockey_id, name |
| `ra_trainers` | 2,780 | Trainer reference | trainer_id, name, location |
| `ra_owners` | 48,092 | Owner reference | owner_id, name |
| `ra_courses` | 101 | Course reference | course_id, name, region |
| `ra_races` | 136,648 | Race metadata | race_id, race_date, course_id, distance_meters, going, race_class |
| `ra_runners` | 379,422 | **Core ML data** | runner_id, race_id, horse_id, position, ratings, form |

---

## Fields by ML Importance

### CRITICAL (Must Have)

**Identification:**
- `runner_id` - Unique runner identifier
- `horse_id` - Horse identifier
- `race_id` - Race identifier

**Performance:**
- `position` - Finish position (1st, 2nd, 3rd...)
- `win_rate` - Career win percentage
- `place_rate` - Career place percentage
- `course_win_rate` - Win rate at this course
- `distance_win_rate` - Win rate at this distance

**Ratings:**
- `official_rating` - Official handicap rating
- `rpr` - Racing Post Rating
- `tsr` - Topspeed Rating

**Form:**
- `last_5_positions` - Recent form array [1, 3, 2, 5, 4]
- `recent_form_score` - Weighted form score (0-100)

**Race Context:**
- `distance_meters` - Race distance
- `race_class` - Race classification
- `going` - Ground condition
- `draw` - Starting position
- `field_size` - Number of runners

**Time:**
- `days_since_last_run` - Fitness indicator

### HIGH (Important)

**Connections:**
- `jockey_id` - Jockey identifier
- `trainer_id` - Trainer identifier
- `horse_jockey_win_rate` - Combination performance
- `horse_trainer_win_rate` - Combination performance

**Pedigree:**
- `sire_id` - Sire identifier
- `dam_id` - Dam identifier
- `damsire_id` - Damsire identifier

**Results:**
- `starting_price` - SP odds
- `distance_beaten` - Margin of defeat
- `prize_won` - Prize money

**Entry Details:**
- `weight_lbs` - Carried weight
- `age` - Horse age
- `blinkers` - Wearing blinkers (boolean)

**Temporal:**
- `race_date` - Date of race
- `dob` - Horse date of birth

**Course:**
- `course_id` - Course identifier
- `surface` - Flat or Jump

### MEDIUM (Supporting)

**Stats:**
- `career_runs`, `career_wins`, `career_places`
- `going_win_rate`, `class_win_rate`, `surface_win_rate`

**Form:**
- `form` - Form string (e.g., "13-245")
- `form_string` - Extended form

**Equipment:**
- `headgear`, `cheekpieces`, `visor`, `tongue_tie`

**Other:**
- `sex`, `sex_code`
- `trainer_location`
- `timeform_rating`

### LOW (Reference Only)

**Names:**
- `horse_name`, `jockey_name`, `trainer_name`, `owner_name`, `course_name`, `race_name`

**Informational:**
- `silk_url`, `comment`, `tip`, `verdict`, `breeder`

---

## Essential Joins

### Get Complete Runner Data

```sql
SELECT
    -- Runner details
    r.runner_id, r.horse_id, r.jockey_id, r.trainer_id,
    r.position, r.starting_price, r.weight_lbs, r.draw,
    r.official_rating, r.rpr, r.tsr,
    r.blinkers,

    -- Horse details
    h.name as horse_name, h.dob, h.sex_code, h.region,

    -- Pedigree
    p.sire_id, p.dam_id, p.damsire_id,

    -- Race context
    races.race_date, races.course_id, races.distance_meters,
    races.going, races.race_class, races.surface, races.field_size

FROM ra_runners r
JOIN ra_horses h ON r.horse_id = h.horse_id
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id
JOIN ra_races races ON r.race_id = races.race_id

WHERE r.race_id = :race_id;
```

### Get Historical Performance

```sql
SELECT
    races.race_date,
    races.course_name,
    races.distance_meters,
    races.going,
    r.position,
    r.distance_beaten,
    r.official_rating,
    r.weight_lbs,
    r.jockey_name,
    r.starting_price
FROM ra_runners r
JOIN ra_races races ON r.race_id = races.race_id
WHERE r.horse_id = :horse_id
  AND r.position IS NOT NULL
ORDER BY races.race_date DESC;
```

---

## ML Feature Categories

**Note:** ML features are calculated on-demand via API (DarkHorses-AI-Engine project).
Source data comes from the tables below.

### Career Features
Calculate from `ra_runners`:
- `total_races`, `total_wins`, `total_places`
- `win_rate`, `place_rate`, `avg_finish_position`
- `days_since_last_run`

### Context Features
Calculate from `ra_runners` + `ra_races`:
- `course_win_rate`, `course_runs`, `course_wins`
- `distance_win_rate`, `distance_runs`, `distance_wins`
- `surface_win_rate`, `going_win_rate`, `class_win_rate`

### Form Features
Calculate from `ra_runners` + `ra_races`:
- `last_5_positions` (array)
- `last_10_positions` (array)
- `recent_form_score` (0-100)

### Relationship Features
Calculate from `ra_runners`:
- `horse_jockey_win_rate`, `horse_jockey_runs`, `horse_jockey_wins`
- `horse_trainer_win_rate`, `horse_trainer_runs`, `horse_trainer_wins`
- `jockey_trainer_win_rate`

### Entry Features
From `ra_runners` (current race):
- `current_weight_lbs`, `current_draw`, `current_number`
- `current_official_rating`, `current_rpr`, `current_tsr`
- `current_age`, `has_blinkers`

### Race Context Features
From `ra_races`:
- `distance_meters`, `race_class`, `race_type`
- `surface`, `going`, `field_size`

---

## Common Patterns

### Filter by Date Range
```sql
WHERE race_date >= CURRENT_DATE - INTERVAL '30 days'
  AND race_date <= CURRENT_DATE
```

### Filter UK/Ireland Only
```sql
WHERE region IN ('gb', 'ire')
```

### Filter Completed Races Only
```sql
WHERE position IS NOT NULL
```

### Get Upcoming Races
```sql
WHERE race_date >= CURRENT_DATE
  AND race_date <= CURRENT_DATE + INTERVAL '7 days'
```

### Calculate Win Rate
```sql
ROUND(100.0 * SUM(CASE WHEN position = 1 THEN 1 ELSE 0 END) / COUNT(*), 2) as win_rate
```

### Calculate Place Rate (Top 3)
```sql
ROUND(100.0 * SUM(CASE WHEN position <= 3 THEN 1 ELSE 0 END) / COUNT(*), 2) as place_rate
```

---

## Data Completeness

| Field | Availability | Notes |
|-------|--------------|-------|
| position | ~90% | Only available after race completion |
| official_rating | ~85% | Not all horses rated |
| rpr, tsr | ~70% | Pro subscription data |
| dob | ~95% | Via enrichment |
| pedigree | ~95% | Via enrichment |
| starting_price | ~85% | After betting markets form |
| form | ~85% | Most horses have some form |
| trainer_location | ~80% | From Pro racecards |

---

## Performance Tips

1. **Use ML Table** - `dh_ml_runner_history` has pre-calculated features
2. **Index on Dates** - Filter by race_date first
3. **Batch Queries** - Fetch multiple runners at once
4. **JSONB Access** - Use `historical_races` for complete history
5. **Limit Results** - Use LIMIT for pagination

---

**For Full Documentation:** See `DATABASE_SCHEMA_ML_API_REFERENCE.md`
**Last Updated:** 2025-10-15
