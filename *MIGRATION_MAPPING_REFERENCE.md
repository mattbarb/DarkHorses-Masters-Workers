# Racing API Database Migration Mapping Reference

**Date:** 2025-10-19
**Database:** Supabase PostgreSQL
**Connection:** Session Pooler (IPv4 compatible)
**URL:** `postgresql://postgres.amsjvmlaknnvppxsgpfk:R0pMr1L58WH3hUkpVtPcwYnw@aws-0-eu-west-2.pooler.supabase.com:5432/postgres`

---

## Overview

This document details the complete migration from legacy `ra_*` tables (75 columns, denormalized) to the new normalized `ra_*` tables (44 columns, normalized with breeding tables). All `*ra_*` tables have been renamed to `ra_*` and are now in production.

**Total Migrated:** ~1.7 million rows across 11 core tables

---

## Table 1: `ra_races`

### Source
- **Legacy Table:** `ra_races`
- **API Endpoint:** Racing API `/races` endpoint
- **Worker:** Race data loader

### Column Mapping

| New Column (`ra_races`) | Old Column (Legacy) | Type | Notes |
|------------------------|---------------------|------|-------|
| `id` | `race_id` | VARCHAR | Primary key |
| `course_id` | `course_id` | VARCHAR | FK to `ra_courses` |
| `course_name` | `course_name` | VARCHAR | Denormalized for performance |
| `date` | `race_date` | DATE | Race date |
| `off_time` | `off_time` | TIME | Scheduled start time |
| `off_dt` | `off_datetime` | TIMESTAMP | Full datetime (renamed) |
| `race_name` | `race_name` | VARCHAR | |
| `distance` | `distance` | VARCHAR | Distance string (e.g., "1m 2f") |
| `distance_f` | `distance_f` | INTEGER | Distance in furlongs |
| `distance_m` | `distance_meters` | INTEGER | Distance in meters (renamed) |
| `region` | `region` | VARCHAR | Region code (gb, ire) |
| `type` | `race_type` | VARCHAR | Race type (renamed) |
| `surface` | `surface` | VARCHAR | Surface type |
| `going` | `going` | VARCHAR | Going description |
| `race_class` | `race_class` | VARCHAR | Race class |
| `age_band` | `age_band` | VARCHAR | Age restrictions |
| `prize` | `prize_money` | NUMERIC | Prize money (renamed) |
| `field_size` | `field_size` | INTEGER | Number of runners |
| `rail_movements` | `rail_movements` | VARCHAR | Rail position info |
| `is_big_race` | `big_race` | BOOLEAN | Big race flag (renamed) |
| `is_abandoned` | `is_abandoned` | BOOLEAN | Abandoned flag |
| `created_at` | `created_at` | TIMESTAMP | |
| `updated_at` | `updated_at` | TIMESTAMP | |

### Migration Stats
- **Rows:** 136,932
- **Time:** 4.3 seconds
- **Speed:** ~31,844 rows/sec

### API Configuration
```json
{
  "endpoint": "/races",
  "method": "GET",
  "params": {
    "date": "YYYY-MM-DD",
    "region": "gb|ire"
  },
  "auth": {
    "username": "RACING_API_USERNAME",
    "password": "RACING_API_PASSWORD"
  }
}
```

---

## Table 2: `ra_courses`

### Source
- **Legacy Table:** `ra_courses`
- **API Endpoint:** Racing API `/courses` endpoint
- **Worker:** Course data loader
- **Enhancement:** Geocoding via OpenCage API

### Column Mapping

| New Column (`ra_courses`) | Old Column (Legacy) | Type | Notes |
|--------------------------|---------------------|------|-------|
| `id` | `course_id` | VARCHAR | Primary key |
| `name` | `name` | VARCHAR | |
| `region_code` | `region` | VARCHAR | Short code (gb, ire) |
| `region` | `country` | VARCHAR | Full name derived from code |
| `longitude` | `longitude` | NUMERIC | |
| `latitude` | `latitude` | NUMERIC | |
| `created_at` | `created_at` | TIMESTAMP | |
| `updated_at` | `updated_at` | TIMESTAMP | |

### Region Mapping Logic
```sql
CASE
    WHEN region = 'gb' THEN 'Great Britain'
    WHEN region = 'ire' THEN 'Ireland'
    WHEN region = 'fr' THEN 'France'
    WHEN region = 'uae' THEN 'United Arab Emirates'
    WHEN region = 'aus' THEN 'Australia'
    WHEN region = 'usa' THEN 'United States'
    ELSE UPPER(region)
END
```

### Migration Stats
- **Rows:** 101 (69 GB, 32 IRE)
- **Time:** 0.054 seconds

### API Configuration
```json
{
  "endpoint": "/courses",
  "method": "GET",
  "geocoding_api": {
    "provider": "OpenCage",
    "url": "https://api.opencagedata.com/geocode/v1/json",
    "key": "OPENCAGE_API_KEY",
    "fields": ["latitude", "longitude"]
  }
}
```

---

## Table 3: `ra_jockeys`

### Source
- **Legacy Table:** `ra_jockeys`
- **API Endpoint:** Racing API `/jockeys` endpoint (statistics)
- **Worker:** Jockey data loader + statistics worker

### Column Mapping

| New Column (`ra_jockeys`) | Old Column (Legacy) | Type | Notes |
|---------------------------|---------------------|------|-------|
| `id` | `jockey_id` | VARCHAR | Primary key |
| `name` | `name` | VARCHAR | |
| `created_at` | `created_at` | TIMESTAMP | |
| `updated_at` | `updated_at` | TIMESTAMP | |
| **Statistics (Added)** | | | |
| `total_rides` | `total_rides` | INTEGER | Total career rides |
| `total_wins` | `total_wins` | INTEGER | Total wins |
| `total_places` | `total_places` | INTEGER | Total places (1st-3rd) |
| `total_seconds` | `total_seconds` | INTEGER | 2nd place finishes |
| `total_thirds` | `total_thirds` | INTEGER | 3rd place finishes |
| `win_rate` | `win_rate` | NUMERIC(5,2) | Win percentage |
| `place_rate` | `place_rate` | NUMERIC(5,2) | Place percentage |
| `stats_updated_at` | `stats_updated_at` | TIMESTAMP | Last stats update |

### Migration Stats
- **Rows:** 3,483 (3,482 with statistics)
- **Time:** <1 second
- **Top Jockey:** Oisin Murphy (1,621 wins, 18.02% win rate)

### API Configuration
```json
{
  "endpoint": "/jockeys/{jockey_id}/statistics",
  "method": "GET",
  "update_frequency": "daily",
  "fields": [
    "total_rides",
    "total_wins",
    "total_places",
    "total_seconds",
    "total_thirds",
    "win_rate",
    "place_rate"
  ]
}
```

---

## Table 4: `ra_trainers`

### Source
- **Legacy Table:** `ra_trainers`
- **API Endpoint:** Racing API `/trainers` endpoint (statistics)
- **Worker:** Trainer data loader + statistics worker

### Column Mapping

| New Column (`ra_trainers`) | Old Column (Legacy) | Type | Notes |
|----------------------------|---------------------|------|-------|
| `id` | `trainer_id` | VARCHAR | Primary key |
| `name` | `name` | VARCHAR | |
| `location` | - | VARCHAR | Not in legacy (NEW) |
| `created_at` | `created_at` | TIMESTAMP | |
| `updated_at` | `updated_at` | TIMESTAMP | |
| **Statistics (Added)** | | | |
| `total_runners` | `total_runners` | INTEGER | Total runners trained |
| `total_wins` | `total_wins` | INTEGER | Total wins |
| `total_places` | `total_places` | INTEGER | Total places |
| `total_seconds` | `total_seconds` | INTEGER | 2nd place finishes |
| `total_thirds` | `total_thirds` | INTEGER | 3rd place finishes |
| `win_rate` | `win_rate` | NUMERIC(5,2) | Win percentage |
| `place_rate` | `place_rate` | NUMERIC(5,2) | Place percentage |
| `recent_14d_runs` | `recent_14d_runs` | INTEGER | Recent form (14 days) |
| `recent_14d_wins` | `recent_14d_wins` | INTEGER | Recent wins |
| `recent_14d_win_rate` | `recent_14d_win_rate` | NUMERIC(5,2) | Recent win rate |
| `stats_updated_at` | `stats_updated_at` | TIMESTAMP | Last stats update |

### Migration Stats
- **Rows:** 2,781 (2,780 with statistics)
- **Time:** <1 second
- **Top Trainer:** W P Mullins (2,438 wins, 28.11% win rate)

### API Configuration
```json
{
  "endpoint": "/trainers/{trainer_id}/statistics",
  "method": "GET",
  "update_frequency": "daily",
  "fields": [
    "total_runners",
    "total_wins",
    "total_places",
    "win_rate",
    "place_rate",
    "recent_14d_runs",
    "recent_14d_wins",
    "recent_14d_win_rate"
  ]
}
```

---

## Table 5: `ra_owners`

### Source
- **Legacy Table:** `ra_owners`
- **API Endpoint:** Racing API `/owners` endpoint (statistics)
- **Worker:** Owner data loader + statistics worker

### Column Mapping

| New Column (`ra_owners`) | Old Column (Legacy) | Type | Notes |
|--------------------------|---------------------|------|-------|
| `id` | `owner_id` | VARCHAR | Primary key |
| `name` | `name` | VARCHAR | |
| `created_at` | `created_at` | TIMESTAMP | |
| `updated_at` | `updated_at` | TIMESTAMP | |
| **Statistics (Added)** | | | |
| `total_horses` | `total_horses` | INTEGER | Number of horses owned |
| `total_runners` | `total_runners` | INTEGER | Total runners |
| `total_wins` | `total_wins` | INTEGER | Total wins |
| `total_places` | `total_places` | INTEGER | Total places |
| `total_seconds` | `total_seconds` | INTEGER | 2nd place finishes |
| `total_thirds` | `total_thirds` | INTEGER | 3rd place finishes |
| `win_rate` | `win_rate` | NUMERIC(5,2) | Win percentage |
| `place_rate` | `place_rate` | NUMERIC(5,2) | Place percentage |
| `active_last_30d` | `active_last_30d` | BOOLEAN | Activity flag |
| `stats_updated_at` | `stats_updated_at` | TIMESTAMP | Last stats update |

### Migration Stats
- **Rows:** 48,161 (48,143 with statistics)
- **Time:** 1.2 seconds
- **Top Owner:** John P McManus (2,055 wins from 12,656 runners)

### API Configuration
```json
{
  "endpoint": "/owners/{owner_id}/statistics",
  "method": "GET",
  "update_frequency": "daily",
  "fields": [
    "total_horses",
    "total_runners",
    "total_wins",
    "total_places",
    "win_rate",
    "place_rate",
    "active_last_30d"
  ]
}
```

---

## Table 6: `ra_horses`

### Source
- **Legacy Table:** Extracted from `ra_runners`
- **API Endpoint:** Racing API `/horses` endpoint
- **Worker:** Horse data loader (extract unique from runners)

### Column Mapping

| New Column (`ra_horses`) | Old Column (Legacy) | Type | Notes |
|--------------------------|---------------------|------|-------|
| `id` | `horse_id` | VARCHAR | Primary key |
| `name` | `horse_name` | VARCHAR | |
| `age` | `horse_age` | INTEGER | Aggregated (MIN) |
| `sex` | `horse_sex` | VARCHAR | Aggregated (MIN) |
| `sex_code` | `horse_sex` | VARCHAR(5) | First 5 chars |
| `colour` | `horse_colour` | VARCHAR | Aggregated (MIN) |
| `dob` | `horse_dob` | DATE | Aggregated (MIN) |
| `sire_id` | `sire_id` | VARCHAR | FK to `ra_sires` |
| `dam_id` | `dam_id` | VARCHAR | FK to `ra_dams` |
| `damsire_id` | `damsire_id` | VARCHAR | FK to `ra_damsires` |
| `region` | - | VARCHAR | Derived from races |
| `is_active` | - | BOOLEAN | Derived (recent runs) |
| `last_run_date` | `last_run_date` | DATE | Aggregated (MAX) |
| `created_at` | `created_at` | TIMESTAMP | Aggregated (MIN) |
| `updated_at` | `updated_at` | TIMESTAMP | Aggregated (MAX) |

### Migration Query
```sql
INSERT INTO ra_horses (id, name, age, sex, sex_code, colour, dob, sire_id, dam_id, damsire_id, created_at, updated_at)
SELECT
    horse_id,
    MIN(horse_name),
    MIN(horse_age),
    MIN(horse_sex),
    MIN(SUBSTRING(horse_sex, 1, 5)),
    MIN(horse_colour),
    MIN(horse_dob),
    MIN(sire_id),
    MIN(dam_id),
    MIN(damsire_id),
    MIN(created_at),
    MAX(updated_at)
FROM ra_runners
WHERE horse_id IS NOT NULL
GROUP BY horse_id;
```

### Migration Stats
- **Rows:** 111,652 unique horses
- **Time:** 2.8 seconds
- **Source:** Aggregated from 1.3M runners

---

## Table 7: `ra_sires` (Breeding)

### Source
- **Legacy Table:** Extracted from `ra_runners.sire_id` + `sire_name`
- **API Endpoint:** Racing API `/breeding/sires` endpoint
- **Worker:** Breeding data loader

### Column Mapping

| New Column (`ra_sires`) | Old Column (Legacy) | Type | Notes |
|-------------------------|---------------------|------|-------|
| `id` | `sire_id` | VARCHAR | Primary key |
| `name` | `sire_name` | VARCHAR | Aggregated (MIN) |
| `created_at` | `created_at` | TIMESTAMP | Aggregated (MIN) |
| `updated_at` | `updated_at` | TIMESTAMP | Aggregated (MAX) |

### Migration Query
```sql
INSERT INTO ra_sires (id, name, created_at, updated_at)
SELECT
    sire_id,
    MIN(sire_name),
    MIN(created_at),
    MAX(updated_at)
FROM ra_runners
WHERE sire_id IS NOT NULL
GROUP BY sire_id;
```

### Migration Stats
- **Rows:** 2,143 unique sires
- **Time:** <1 second
- **Note:** Handles duplicate sire_id with different names by selecting MIN(name)

---

## Table 8: `ra_dams` (Breeding)

### Source
- **Legacy Table:** Extracted from `ra_runners.dam_id` + `dam_name`
- **API Endpoint:** Racing API `/breeding/dams` endpoint
- **Worker:** Breeding data loader

### Column Mapping

| New Column (`ra_dams`) | Old Column (Legacy) | Type | Notes |
|------------------------|---------------------|------|-------|
| `id` | `dam_id` | VARCHAR | Primary key |
| `name` | `dam_name` | VARCHAR | Aggregated (MIN) |
| `created_at` | `created_at` | TIMESTAMP | Aggregated (MIN) |
| `updated_at` | `updated_at` | TIMESTAMP | Aggregated (MAX) |

### Migration Query
```sql
INSERT INTO ra_dams (id, name, created_at, updated_at)
SELECT
    dam_id,
    MIN(dam_name),
    MIN(created_at),
    MAX(updated_at)
FROM ra_runners
WHERE dam_id IS NOT NULL
GROUP BY dam_id;
```

### Migration Stats
- **Rows:** 48,366 unique dams
- **Time:** 1.1 seconds

---

## Table 9: `ra_damsires` (Breeding)

### Source
- **Legacy Table:** Extracted from `ra_runners.damsire_id` + `damsire_name`
- **API Endpoint:** Racing API `/breeding/damsires` endpoint
- **Worker:** Breeding data loader

### Column Mapping

| New Column (`ra_damsires`) | Old Column (Legacy) | Type | Notes |
|----------------------------|---------------------|------|-------|
| `id` | `damsire_id` | VARCHAR | Primary key |
| `name` | `damsire_name` | VARCHAR | Aggregated (MIN) |
| `created_at` | `created_at` | TIMESTAMP | Aggregated (MIN) |
| `updated_at` | `updated_at` | TIMESTAMP | Aggregated (MAX) |

### Migration Query
```sql
INSERT INTO ra_damsires (id, name, created_at, updated_at)
SELECT
    damsire_id,
    MIN(damsire_name),
    MIN(created_at),
    MAX(updated_at)
FROM ra_runners
WHERE damsire_id IS NOT NULL
GROUP BY damsire_id;
```

### Migration Stats
- **Rows:** 3,040 unique damsires
- **Time:** <1 second

---

## Table 10: `ra_bookmakers`

### Source
- **Legacy Table:** `ra_bookmakers`
- **API Endpoint:** Racing API `/bookmakers` endpoint
- **Worker:** Bookmaker data loader

### Column Mapping

| New Column (`ra_bookmakers`) | Old Column (Legacy) | Type | Notes |
|------------------------------|---------------------|------|-------|
| `id` | - | BIGSERIAL | Auto-increment |
| `code` | `bookmaker_id` | VARCHAR | Unique identifier |
| `name` | `bookmaker_name` | VARCHAR | |
| `type` | `bookmaker_type` | VARCHAR(20) | Added after migration |
| `is_active` | `active` | BOOLEAN | |
| `created_at` | `created_at` | TIMESTAMP | |

### Type Values
- **online** (13 bookmakers): Bet365, William Hill, Paddy Power, etc.
- **exchange** (4 bookmakers): Betfair, Betdaq, Smarkets, Matchbook
- **spread** (2 bookmakers): Sporting Index, Spreadex

### Migration Stats
- **Rows:** 19 bookmakers
- **Time:** 0.06 seconds

### API Configuration
```json
{
  "endpoint": "/bookmakers",
  "method": "GET",
  "fields": ["bookmaker_id", "bookmaker_name", "bookmaker_type", "active"]
}
```

---

## Table 11: `ra_runners` (LARGEST TABLE)

### Source
- **Legacy Table:** `ra_runners` (75 columns)
- **API Endpoint:** Racing API `/races/{race_id}/runners`
- **Worker:** Runner data loader

### Column Mapping

| New Column (`ra_runners`) | Old Column (Legacy) | Type | Notes |
|---------------------------|---------------------|------|-------|
| `id` | - | BIGSERIAL | Auto-increment |
| `race_id` | `race_id` | VARCHAR | FK to `ra_races` |
| `horse_id` | `horse_id` | VARCHAR | FK to `ra_horses` |
| `horse_name` | `horse_name` | VARCHAR | Denormalized |
| `jockey_name` | `jockey_name` | VARCHAR | Denormalized |
| `trainer_name` | `trainer_name` | VARCHAR | Denormalized |
| `owner_name` | `owner_name` | VARCHAR | Denormalized |
| `number` | `number` | VARCHAR | Converted from INT with COALESCE |
| `draw` | `draw` | VARCHAR | Converted from INT with COALESCE |
| `jockey_id` | `jockey_id` | VARCHAR | FK (NULLIF empty strings) |
| `trainer_id` | `trainer_id` | VARCHAR | FK (NULLIF empty strings) |
| `owner_id` | `owner_id` | VARCHAR | FK (NULLIF empty strings) |
| `sire_id` | `sire_id` | VARCHAR | FK (NULLIF empty strings) |
| `dam_id` | `dam_id` | VARCHAR | FK (NULLIF empty strings) |
| `damsire_id` | `damsire_id` | VARCHAR | FK (NULLIF empty strings) |
| `weight_lbs` | `weight_lbs` | INTEGER | Converted from NUMERIC |
| `weight_st_lbs` | `weight_stones_lbs` | VARCHAR | |
| `age` | `horse_age` | INTEGER | |
| `sex` | `horse_sex` | VARCHAR | |
| `sex_code` | `horse_sex` | VARCHAR(5) | SUBSTRING first 5 chars |
| `colour` | `horse_colour` | VARCHAR | |
| `dob` | `horse_dob` | DATE | |
| `headgear` | `headgear` | VARCHAR | |
| `headgear_run` | `headgear_run` | VARCHAR | |
| `wind_surgery` | `wind_surgery` | VARCHAR | |
| `wind_surgery_run` | `wind_surgery_run` | VARCHAR | |
| `form` | `form` | VARCHAR | |
| `last_run` | `last_run_date` | VARCHAR | Converted to string |
| `ofr` | `official_rating` | INTEGER | Renamed |
| `rpr` | `rpr` | INTEGER | |
| `ts` | `tsr` | INTEGER | Renamed |
| `comment` | `comment` | TEXT | |
| `spotlight` | `spotlight` | TEXT | |
| `trainer_rtf` | `trainer_rtf` | TEXT | |
| `past_results_flags` | `past_results_flags` | JSONB | Converted from TEXT[] |
| `claiming_price_min` | - | NUMERIC | NULL (not in legacy) |
| `claiming_price_max` | - | NUMERIC | NULL (not in legacy) |
| `medication` | - | VARCHAR | NULL (not in legacy) |
| `equipment` | - | VARCHAR | NULL (not in legacy) |
| `morning_line_odds` | - | NUMERIC | NULL (not in legacy) |
| `is_scratched` | - | BOOLEAN | FALSE (default) |
| `silk_url` | `silk_url` | VARCHAR | |
| `created_at` | `created_at` | TIMESTAMP | |
| `updated_at` | `updated_at` | TIMESTAMP | |

### Data Transformations

#### Empty String to NULL
```sql
NULLIF(jockey_id, '')  -- Converts empty strings to NULL for FK constraints
```

#### Integer to VARCHAR with Default
```sql
COALESCE(number::varchar, '0')  -- Handles NULL values
COALESCE(draw::varchar, '0')
```

#### NUMERIC to INTEGER
```sql
weight_lbs::integer
```

#### TEXT[] to JSONB
```sql
to_jsonb(past_results_flags)
```

#### String Truncation
```sql
SUBSTRING(horse_sex, 1, 5)  -- sex_code limited to 5 chars
```

### Migration Stats
- **Rows:** 1,326,334 runners
- **Time:** 3.6 minutes (216 seconds)
- **Speed:** ~6,141 rows/second

### Special Handling

#### Missing Foreign Key Reference
One jockey `jky_0` was referenced but didn't exist:
```sql
INSERT INTO ra_jockeys (id, name, created_at, updated_at)
VALUES ('jky_0', 'Unknown', NOW(), NOW())
ON CONFLICT (id) DO NOTHING;
```

### API Configuration
```json
{
  "endpoint": "/races/{race_id}/runners",
  "method": "GET",
  "update_frequency": "real-time",
  "fields": [
    "race_id",
    "horse_id",
    "horse_name",
    "jockey_id",
    "jockey_name",
    "trainer_id",
    "trainer_name",
    "owner_id",
    "owner_name",
    "number",
    "draw",
    "weight_lbs",
    "age",
    "sex",
    "colour",
    "dob",
    "headgear",
    "form",
    "official_rating",
    "rpr",
    "tsr",
    "comment",
    "spotlight",
    "silk_url"
  ],
  "breeding_fields": [
    "sire_id",
    "dam_id",
    "damsire_id"
  ]
}
```

---

## Data Gaps & Missing Fields

### Fields NOT in Legacy Schema (Need Workers)

#### `ra_runners` - North America Support
```json
{
  "missing_fields": [
    "claiming_price_min",
    "claiming_price_max",
    "medication",
    "equipment",
    "morning_line_odds"
  ],
  "api_endpoint": "/races/{race_id}/runners",
  "region_filter": "usa|can",
  "worker": "north_america_runner_data_loader"
}
```

#### `ra_trainers` - Location Data
```json
{
  "missing_fields": ["location"],
  "api_endpoint": "/trainers/{trainer_id}",
  "data_sources": [
    "Racing API trainer profile",
    "Web scraping from racing sites",
    "Manual data entry"
  ],
  "worker": "trainer_location_enrichment_worker"
}
```

---

## Database Connection Configuration

### Environment Variables Required

```bash
# Supabase PostgreSQL (Session Pooler - IPv4 Compatible)
DATABASE_URL=postgresql://postgres.amsjvmlaknnvppxsgpfk:R0pMr1L58WH3hUkpVtPcwYnw@aws-0-eu-west-2.pooler.supabase.com:5432/postgres

SESSION_POOLER=postgresql://postgres.amsjvmlaknnvppxsgpfk:R0pMr1L58WH3hUkpVtPcwYnw@aws-0-eu-west-2.pooler.supabase.com:5432/postgres

# Racing API
RACING_API_USERNAME=l2fC3sZFIZmvpiMt6DdUCpEv
RACING_API_PASSWORD=R0pMr1L58WH3hUkpVtPcwYnw

# Geocoding API (for coordinates)
OPENCAGE_API_KEY=c885d740936d4556bb014846dcff83ce
```

### Important Notes
- **IPv4 Compatibility:** Use Session Pooler (port 5432) NOT direct connection
- **Direct Connection:** IPv6 only, requires IPv4 add-on ($4/month) or IPv6 network
- **Connection Pooling:** Session Pooler supports up to 3,000 connections

---

## Worker Priority List

### High Priority (Data Completeness)

1. **Jockey Statistics Worker**
   - Update `ra_jockeys` statistics daily
   - Endpoint: `/jockeys/{jockey_id}/statistics`
   - Fields: `total_rides`, `total_wins`, `win_rate`, `place_rate`

2. **Trainer Statistics Worker**
   - Update `ra_trainers` statistics daily
   - Endpoint: `/trainers/{trainer_id}/statistics`
   - Fields: `total_runners`, `total_wins`, `recent_14d_wins`

3. **Owner Statistics Worker**
   - Update `ra_owners` statistics daily
   - Endpoint: `/owners/{owner_id}/statistics`
   - Fields: `total_horses`, `total_runners`, `total_wins`

4. **Breeding Data Enhancement Worker**
   - Enrich `ra_sires`, `ra_dams`, `ra_damsires` with pedigree stats
   - Endpoint: `/breeding/{entity_type}/{id}/statistics`
   - Fields: Progeny wins, earnings, strike rates

### Medium Priority (Feature Enhancement)

5. **Trainer Location Enrichment Worker**
   - Add `location` to `ra_trainers`
   - Source: Scrape from Racing Post or use Racing API profile

6. **North America Runner Data Worker**
   - Populate NA-specific fields in `ra_runners`
   - Fields: `claiming_price_min/max`, `medication`, `equipment`, `morning_line_odds`
   - Region: USA/Canada races only

7. **Course Geocoding Refresh Worker**
   - Verify/update coordinates for all courses
   - API: OpenCage Geocoding API

### Low Priority (Optimization)

8. **Historical Data Backfill Worker**
   - Backfill older race data if needed
   - Date range: Configurable

9. **Data Quality Audit Worker**
   - Check for NULL values in critical fields
   - Validate foreign key relationships

---

## Testing & Validation Queries

### Check Table Row Counts
```sql
SELECT
    'ra_races' as table_name, COUNT(*) as rows FROM ra_races
UNION ALL SELECT 'ra_runners', COUNT(*) FROM ra_runners
UNION ALL SELECT 'ra_jockeys', COUNT(*) FROM ra_jockeys
UNION ALL SELECT 'ra_trainers', COUNT(*) FROM ra_trainers
UNION ALL SELECT 'ra_owners', COUNT(*) FROM ra_owners
UNION ALL SELECT 'ra_horses', COUNT(*) FROM ra_horses
UNION ALL SELECT 'ra_sires', COUNT(*) FROM ra_sires
UNION ALL SELECT 'ra_dams', COUNT(*) FROM ra_dams
UNION ALL SELECT 'ra_damsires', COUNT(*) FROM ra_damsires
UNION ALL SELECT 'ra_bookmakers', COUNT(*) FROM ra_bookmakers
UNION ALL SELECT 'ra_courses', COUNT(*) FROM ra_courses;
```

### Verify Foreign Key Integrity
```sql
-- Orphan runners (no race)
SELECT COUNT(*)
FROM ra_runners r
WHERE NOT EXISTS (SELECT 1 FROM ra_races WHERE id = r.race_id);

-- Invalid horse references
SELECT COUNT(*)
FROM ra_runners r
WHERE r.horse_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM ra_horses WHERE id = r.horse_id);

-- Invalid jockey references
SELECT COUNT(*)
FROM ra_runners r
WHERE r.jockey_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM ra_jockeys WHERE id = r.jockey_id);
```

### Check Statistics Coverage
```sql
-- Jockeys with stats
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE total_wins IS NOT NULL) as with_stats,
    ROUND(100.0 * COUNT(*) FILTER (WHERE total_wins IS NOT NULL) / COUNT(*), 2) as coverage_pct
FROM ra_jockeys;

-- Trainers with stats
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE total_wins IS NOT NULL) as with_stats,
    ROUND(100.0 * COUNT(*) FILTER (WHERE total_wins IS NOT NULL) / COUNT(*), 2) as coverage_pct
FROM ra_trainers;

-- Owners with stats
SELECT
    COUNT(*) as total,
    COUNT(*) FILTER (WHERE total_wins IS NOT NULL) as with_stats,
    ROUND(100.0 * COUNT(*) FILTER (WHERE total_wins IS NOT NULL) / COUNT(*), 2) as coverage_pct
FROM ra_owners;
```

---

## Migration Performance Summary

| Table | Rows | Time | Speed (rows/sec) |
|-------|------|------|------------------|
| `ra_races` | 136,932 | 4.3s | 31,844 |
| `ra_jockeys` | 3,483 | <1s | - |
| `ra_trainers` | 2,781 | <1s | - |
| `ra_owners` | 48,161 | 1.2s | 40,134 |
| `ra_horses` | 111,652 | 2.8s | 39,876 |
| `ra_sires` | 2,143 | <1s | - |
| `ra_dams` | 48,366 | 1.1s | 43,969 |
| `ra_damsires` | 3,040 | <1s | - |
| `ra_runners` | 1,326,334 | 216s | 6,141 |
| `ra_bookmakers` | 19 | 0.06s | 317 |
| `ra_courses` | 101 | 0.05s | 2,020 |
| **TOTAL** | **1,683,012** | **~4 min** | **~7,013 avg** |

---

## Key Learnings & Best Practices

### 1. Foreign Key Handling
- Always check for empty strings: `NULLIF(field, '')`
- Provide defaults for required fields: `COALESCE(field, 'default')`
- Create placeholder records for missing references (e.g., `jky_0`)

### 2. Type Conversions
- Use explicit casts: `::integer`, `::varchar`, `::jsonb`
- Handle NULL values before casting
- Use `to_jsonb()` for array-to-JSON conversions

### 3. Aggregation Strategy
- Use `MIN()` for IDs and names (consistency)
- Use `MAX()` for updated_at (latest timestamp)
- Use `GROUP BY` primary key to deduplicate

### 4. Performance Optimization
- **Avoid:** UNLOGGED tables (blocked by FK constraints on Supabase)
- **Avoid:** Disabling triggers (insufficient privileges)
- **Use:** Bulk INSERT SELECT (6,000+ rows/sec)
- **Use:** Session Pooler for IPv4 compatibility

### 5. Data Quality
- Validate row counts after migration
- Check foreign key integrity
- Verify statistics coverage
- Test sample queries

---

## Contact & Support

**Migration Completed:** 2025-10-19
**Database:** Supabase PostgreSQL (amsjvmlaknnvppxsgpfk)
**Total Tables:** 23 renamed from `*ra_*` to `ra_*`
**Total Sequences:** 10 renamed
**Total Indexes:** 22 renamed
**Total Constraints:** 24 renamed

**Next Steps:**
1. Update worker configurations to use new schema
2. Implement statistics update workers
3. Add missing fields (trainer location, NA runner data)
4. Set up daily statistics refresh cron jobs
5. Monitor data quality and foreign key integrity

---

*End of Migration Mapping Reference*
