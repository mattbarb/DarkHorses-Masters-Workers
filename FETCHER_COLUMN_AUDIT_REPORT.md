# FETCHER COLUMN AUDIT REPORT

**Date:** 2025-10-19
**Purpose:** Complete audit of all fetchers vs database schema to identify missing columns

---

## EXECUTIVE SUMMARY

### Audit Scope
- 8 fetcher files analyzed
- 9 database tables audited
- Sample API responses examined

### Key Findings

✅ **GOOD NEWS:**
- Most core columns are being captured correctly
- Position data, pedigree data, and entity relationships are complete
- Recent Migration 018 columns are mostly captured

❌ **GAPS FOUND:**

**High Priority (Available in API, Not Captured):**
1. **ra_races table:** 15+ missing columns from results API
2. **ra_race_results table:** NEW table, not yet populated by results_fetcher
3. **ra_runners table:** Several Pro endpoint fields not captured
4. **Statistics tables:** Jockeys/Trainers/Owners statistics endpoints not being called

**Low Priority (Likely not in API or calculated):**
5. **ra_courses:** Longitude/latitude (requires geocoding, not in API)
6. **Breeding stats tables:** 42 stats columns per table (calculated, not from API)

---

## TABLE 1: ra_races (47 total columns)

### Currently Captured by races_fetcher.py (24 columns) ✅

| Column | API Field | Status |
|--------|-----------|--------|
| id | race_id | ✅ |
| course_id | course_id | ✅ |
| course_name | course | ✅ |
| region | region | ✅ |
| race_name | race_name | ✅ |
| date | date | ✅ |
| off_dt | off_dt | ✅ |
| off_time | off_time | ✅ |
| type | type | ✅ |
| race_class | race_class | ✅ |
| distance | distance_f (numeric furlongs) | ✅ |
| distance_f | distance (string like "1m") | ✅ |
| distance_m | dist_m | ✅ |
| age_band | age_band | ✅ |
| surface | surface | ✅ |
| going | going | ✅ |
| track_condition | going_detailed | ✅ (mapped from going_detailed) |
| weather_conditions | weather | ✅ (mapped from weather) |
| rail_movements | rail_movements | ✅ |
| prize | prize (parsed) | ✅ |
| is_big_race | big_race | ✅ |
| is_abandoned | is_abandoned | ✅ |
| field_size | len(runners) | ✅ (calculated) |
| created_at | - | ✅ (generated) |

### Missing from races_fetcher.py but in results API (17 columns) ❌

| Column | API Field (results endpoint) | Type | Comment |
|--------|------------------------------|------|---------|
| race_number | ? | INTEGER | Race number on card - **CHECK API** |
| distance_round | ? | VARCHAR | Rounded distance - **CHECK API** |
| going_detailed | going_detailed | TEXT | Detailed going description |
| pattern | pattern | VARCHAR | Pattern race designation (Group 1/2/3) |
| sex_restriction | sex_rest | VARCHAR | Sex restrictions (colts/fillies) |
| rating_band | rating_band | VARCHAR | Rating band (e.g., "0-60") |
| stalls | ? | VARCHAR | Stall info - **CHECK API** |
| jumps | jumps | VARCHAR | Number of jumps (NH racing) |
| has_result | ? | BOOLEAN | Result available flag - **CALCULATE** |
| winning_time | time (winner) | VARCHAR | Winning time |
| winning_time_detail | winning_time_detail | TEXT | Detailed timing splits |
| comments | comments | TEXT | Race comments/verdict |
| non_runners | non_runners | TEXT | Non-runners list |
| tote_win | tote_win | VARCHAR | Tote win dividend |
| tote_pl | tote_pl | VARCHAR | Tote place dividend |
| tote_ex | tote_ex | VARCHAR | Exacta dividend |
| tote_csf | tote_csf | VARCHAR | CSF dividend |
| tote_tricast | tote_tricast | VARCHAR | Tricast dividend |
| tote_trifecta | tote_trifecta | VARCHAR | Trifecta dividend |
| tip | ? | VARCHAR | Racing Post tip - **CHECK API** |
| verdict | ? | TEXT | Race verdict - **CHECK API** |
| betting_forecast | ? | VARCHAR | Pre-race forecast - **CHECK API** |
| meet_id | ? | VARCHAR | Meeting ID - **CHECK API** |

**API SOURCE:** These fields are available in `/v1/results` endpoint (see test_api_response.json)

**ACTION REQUIRED:**
- Update `races_fetcher.py` to capture result-specific fields when they exist
- Update `results_fetcher.py` to capture these fields when populating ra_races

---

## TABLE 2: ra_runners (44 listed columns, actual 76+ from Migration 018)

### Currently Captured by races_fetcher.py (56 columns) ✅

**Core Identity (5):**
- id (runner_id composite), race_id, horse_id, horse_name, number

**Horse Details (8):**
- horse_age, horse_sex, horse_dob, horse_colour, horse_region, horse_sex_code, breeder, draw

**People (12):**
- jockey_id, jockey_name, jockey_claim_lbs, trainer_id, trainer_name, trainer_location, trainer_14_days, trainer_rtf, owner_id, owner_name, prev_trainers, prev_owners

**Pedigree (12):**
- sire_id, sire_name, sire_region, dam_id, dam_name, dam_region, damsire_id, damsire_name, damsire_region

**Equipment (6):**
- headgear, headgear_run, blinkers, cheekpieces, visor, tongue_tie

**Medical (2):**
- wind_surgery, wind_surgery_run

**Form (9):**
- form, days_since_last_run, last_run_date, last_run_performance, career_runs, career_wins, career_places, past_results_flags

**Ratings (3):**
- ofr, rpr, ts (tsr)

**Weight (2):**
- weight_lbs, weight_st_lbs

**Results/Position (10):**
- position, distance_beaten, prize_won, starting_price, starting_price_decimal, finishing_time, overall_beaten_distance, comment

**Analysis (4):**
- spotlight, quotes, stable_tour, medical (JSONB)

**Live Data (1):**
- odds (JSONB), silk_url

### Missing from races_fetcher.py (10 columns) ❌

| Column | API Field | Type | Comment |
|--------|-----------|------|---------|
| form_string | form_string | TEXT | Form with separators - **racecards may not have this** |
| apprentice_allowance | jockey_allowance | INTEGER | Already captured but column name mismatch |
| prize_money_won | prize | DECIMAL | Already captured as part of results |
| jockey_claim | jockey_claim | VARCHAR | Already captured |
| last_run | last_run | VARCHAR | Performance code - CHECK if different from last_run_performance |
| claiming_price_min | ? | DECIMAL | Claiming price min - **CHECK API** |
| claiming_price_max | ? | DECIMAL | Claiming price max - **CHECK API** |
| medication | ? | VARCHAR | Medication details - **CHECK API** |
| equipment | ? | VARCHAR | Equipment details - **CHECK API** |
| morning_line_odds | ? | VARCHAR | Morning line odds - **CHECK API** |
| is_scratched | ? | BOOLEAN | Scratched flag - **CHECK API** |

**NOTE:** Most columns appear to be captured. The missing ones may not exist in racecards API.

**ACTION REQUIRED:**
- Verify which columns exist in racecards Pro endpoint
- Add any missing columns that are available

---

## TABLE 3: ra_race_results (38 columns) - NEW TABLE

### Currently Populated: NONE ❌

This table was created in Migration 017 but **results_fetcher.py is NOT populating it**.

**Current State:**
- `results_fetcher.py` only populates `ra_races` table
- It prepares result records but inserts them into `ra_races`, not `ra_race_results`

**Required Columns (38 total):**

**Race Info (11):**
- id (race_id), race_date, course_id, course_name, race_name, off_time, off_datetime, region, type, class, pattern

**Race Conditions (12):**
- rating_band, age_band, sex_rest, dist, dist_y, dist_m, dist_f, going, surface, jumps

**Result Data (13):**
- winning_time_detail, comments, non_runners
- Tote pools: tote_win, tote_pl, tote_ex, tote_csf, tote_tricast, tote_trifecta
- Other: api_data

**Finisher Details (stored in ra_runners):**
- position, horse_id, horse_name, jockey, trainer, etc. → these go in ra_runners

**ACTION REQUIRED:**
- Update `results_fetcher.py._prepare_runner_records()` to ALSO populate ra_race_results table
- Ensure both tables are populated on each results fetch

---

## TABLE 4: ra_horses (15 columns)

### Currently Captured by horses_fetcher.py (11 columns) ✅

| Column | Status |
|--------|--------|
| id, name, sex | ✅ |
| dob, sex_code, colour, colour_code | ✅ (from Pro endpoint) |
| sire_id, dam_id, damsire_id | ✅ (stored in ra_horse_pedigree) |
| region | ✅ (extracted from name) |
| created_at, updated_at | ✅ |

### Missing from horses_fetcher.py (3 columns) ❌

| Column | API Field | Type | Comment |
|--------|-----------|------|---------|
| breeder | breeder | VARCHAR | ✅ Currently captured in pedigree table, **should also be in ra_horses** |
| age | - | INTEGER | **CALCULATED** from dob, not from API |

**NOTE:** Breeder is captured in `ra_horse_pedigree` but the user spec says it should also be in `ra_horses` table.

**ACTION REQUIRED:**
- Add `breeder` field to `ra_horses` insert in `horses_fetcher.py`
- Age is calculated from dob, not needed from API

---

## TABLE 5: ra_jockeys (12 columns)

### Currently Captured by jockeys_fetcher.py (4 columns) ✅

| Column | Status |
|--------|--------|
| id, name | ✅ |
| created_at, updated_at | ✅ |

### Missing Statistics (8 columns) ❌

| Column | API Endpoint | Type | Comment |
|--------|--------------|------|---------|
| total_rides | /v1/jockeys/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_wins | /v1/jockeys/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_places | /v1/jockeys/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_seconds | /v1/jockeys/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_thirds | /v1/jockeys/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| win_rate | /v1/jockeys/{id}/statistics | DECIMAL | **NEW ENDPOINT NEEDED** |
| place_rate | /v1/jockeys/{id}/statistics | DECIMAL | **NEW ENDPOINT NEEDED** |
| stats_updated_at | - | TIMESTAMP | **GENERATED** |

**ACTION REQUIRED:**
- Add statistics fetching to `jockeys_fetcher.py`
- Call `/v1/jockeys/{id}/statistics` for each jockey (or batch if available)
- Update schema with stats data

---

## TABLE 6: ra_trainers (13 columns)

### Currently Captured by trainers_fetcher.py (5 columns) ✅

| Column | Status |
|--------|--------|
| id, name | ✅ |
| location | ✅ |
| created_at, updated_at | ✅ |

### Missing Statistics (8 columns) ❌

| Column | API Endpoint | Type | Comment |
|--------|--------------|------|---------|
| total_runners | /v1/trainers/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_wins | /v1/trainers/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_places | /v1/trainers/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_seconds | /v1/trainers/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_thirds | /v1/trainers/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| win_rate | /v1/trainers/{id}/statistics | DECIMAL | **NEW ENDPOINT NEEDED** |
| place_rate | /v1/trainers/{id}/statistics | DECIMAL | **NEW ENDPOINT NEEDED** |
| stats_updated_at | - | TIMESTAMP | **GENERATED** |

**ACTION REQUIRED:**
- Add statistics fetching to `trainers_fetcher.py`
- Call `/v1/trainers/{id}/statistics` for each trainer

---

## TABLE 7: ra_owners (14 columns)

### Currently Captured by owners_fetcher.py (4 columns) ✅

| Column | Status |
|--------|--------|
| id, name | ✅ |
| created_at, updated_at | ✅ |

### Missing Statistics (10 columns) ❌

| Column | API Endpoint | Type | Comment |
|--------|--------------|------|---------|
| total_horses | /v1/owners/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_runners | /v1/owners/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_wins | /v1/owners/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_places | /v1/owners/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_seconds | /v1/owners/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| total_thirds | /v1/owners/{id}/statistics | INTEGER | **NEW ENDPOINT NEEDED** |
| win_rate | /v1/owners/{id}/statistics | DECIMAL | **NEW ENDPOINT NEEDED** |
| place_rate | /v1/owners/{id}/statistics | DECIMAL | **NEW ENDPOINT NEEDED** |
| active_last_30d | - | BOOLEAN | **CALCULATED** from recent races |
| stats_updated_at | - | TIMESTAMP | **GENERATED** |

**ACTION REQUIRED:**
- Add statistics fetching to `owners_fetcher.py`
- Call `/v1/owners/{id}/statistics` for each owner

---

## TABLE 8: ra_courses (8 columns)

### Currently Captured by courses_fetcher.py (6 columns) ✅

| Column | API Field | Status |
|--------|-----------|--------|
| id | id | ✅ |
| name | course | ✅ |
| region_code | region_code | ✅ (mapped to 'region' column) |
| region | region | ✅ (mapped to 'country' column) |
| created_at, updated_at | - | ✅ |

### Missing Geolocation (2 columns) ❌

| Column | Source | Type | Comment |
|--------|--------|------|---------|
| longitude | Geocoding API | DECIMAL | **NOT in Racing API - requires external geocoding** |
| latitude | Geocoding API | DECIMAL | **NOT in Racing API - requires external geocoding** |

**ACTION REQUIRED:**
- LOW PRIORITY - requires external geocoding service
- Consider OpenStreetMap Nominatim or Google Maps API
- Add in future enhancement

---

## TABLE 9: ra_bookmakers (6 columns)

### Currently Captured by bookmakers_fetcher.py (5 columns) ✅

| Column | Status |
|--------|--------|
| id (auto-increment) | ✅ |
| name | ✅ |
| code | ✅ |
| type | ✅ |
| is_active | ✅ |
| created_at | ✅ |

**All columns captured correctly.** No changes needed.

---

## TABLE 10: ra_sires / ra_dams / ra_damsires (47 columns each)

### Currently Captured (5 columns per table) ✅

| Column | Status |
|--------|--------|
| id, name | ✅ |
| horse_id | ✅ (from pedigree relationships) |
| created_at, updated_at | ✅ |

### Statistics Columns (42 columns) - NOT FROM API ⚠️

These tables have 42 additional statistics columns:
- total_runners, total_wins, total_places_2nd, total_places_3rd
- overall_win_percent, overall_ae_index
- best_class, best_class_ae, best_distance, best_distance_ae
- Plus 3x class breakdowns (name, runners, wins, ae) = 12 columns
- Plus 3x distance breakdowns (name, runners, wins, ae) = 12 columns
- Plus quality fields: data_quality_score, analysis_last_updated

**IMPORTANT:** These statistics are **CALCULATED from race results**, NOT from the Racing API.

**ACTION REQUIRED:**
- **NONE for fetchers** - These stats are calculated by separate analytics processes
- The masters workers should only insert basic data (id, name, horse_id)

---

## SUMMARY: ACTIONS REQUIRED

### High Priority Updates

1. **races_fetcher.py (ra_races table)**
   - Add 17 missing columns from results API
   - Fields: pattern, sex_restriction, rating_band, jumps, going_detailed, tote fields, comments, non_runners

2. **results_fetcher.py (CRITICAL)**
   - Populate ra_race_results table (currently NOT populated)
   - Add missing fields to ra_races inserts
   - Ensure both tables updated on each fetch

3. **horses_fetcher.py**
   - Add `breeder` field to ra_horses insert (currently only in pedigree table)

### Medium Priority Updates

4. **jockeys_fetcher.py**
   - Add statistics fetching from `/v1/jockeys/{id}/statistics`
   - Populate 8 statistics columns

5. **trainers_fetcher.py**
   - Add statistics fetching from `/v1/trainers/{id}/statistics`
   - Populate 8 statistics columns

6. **owners_fetcher.py**
   - Add statistics fetching from `/v1/owners/{id}/statistics`
   - Populate 9 statistics columns (+ active_last_30d calculated)

### Low Priority

7. **courses_fetcher.py**
   - Add geocoding for longitude/latitude (requires external service)

8. **ra_runners table**
   - Verify if any Pro endpoint fields are missing
   - Check for: claiming_price_min/max, medication, equipment, morning_line_odds, is_scratched

### Not Required

9. **Breeding stats tables (ra_sires/ra_dams/ra_damsires)**
   - Stats are calculated, not from API
   - No fetcher changes needed

---

## API FIELD MAPPING REFERENCE

### From test_api_response.json (Results API)

```json
{
  "race_id": "rac_11745682",
  "date": "2025-10-07",
  "region": "GB",
  "course": "Southwell (AW)",
  "course_id": "crs_10244",
  "off": "8:30",
  "off_dt": "2025-10-07T20:30:00+01:00",
  "race_name": "Arc All-Weather £1Million Bonus Returns Handicap",
  "type": "Flat",
  "class": "Class 6",
  "pattern": "",
  "rating_band": "0-60",
  "age_band": "3yo+",
  "sex_rest": "",
  "dist": "1m",
  "dist_y": "1773",
  "dist_m": "1621",
  "dist_f": "8f",
  "going": "Standard",
  "surface": "AW",
  "jumps": "",
  "winning_time_detail": "...",
  "comments": "...",
  "non_runners": "...",
  "tote_win": "...",
  "tote_pl": "...",
  "tote_ex": "...",
  "tote_csf": "...",
  "tote_tricast": "...",
  "tote_trifecta": "...",
  "runners": [...]
}
```

### Runner Fields (from same file)

```json
{
  "horse_id": "hrs_30455194",
  "horse": "Create (IRE)",
  "sp": "9/4",
  "sp_dec": "3.25",
  "number": "7",
  "position": "1",
  "draw": "8",
  "btn": "0",
  "ovr_btn": "0",
  "age": "5",
  "sex": "M",
  "weight": "8-10",
  "weight_lbs": "122",
  "headgear": "p",
  "time": "1:43.25",
  "or": "47",
  "rpr": "57",
  "tsr": "2",
  "prize": "3245.08",
  "jockey": "Kieran O'Neill",
  "jockey_claim_lbs": "0",
  "jockey_id": "jky_250764",
  "trainer": "Scott Dixon",
  "trainer_id": "trn_234891",
  "owner": "Dixon Wylam M Baldry Js Harrod",
  "owner_id": "own_1309284",
  "sire": "Harry Angel (IRE)",
  "sire_id": "sir_7013188",
  "dam": "Patent Joy (IRE)",
  "dam_id": "dam_5801159",
  "damsire": "Pivotal",
  "damsire_id": "dsi_753900",
  "comment": "Held up in rear...",
  "silk_url": "https://www.rp-assets.com/svg/1/2/3/327321.svg"
}
```

---

**END OF AUDIT REPORT**
