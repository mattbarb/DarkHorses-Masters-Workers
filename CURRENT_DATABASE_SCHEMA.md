# Current Database Schema - All Tables

**Generated:** 2025-10-19
**Database:** Supabase PostgreSQL (amsjvmlaknnvppxsgpfk)
**Total Tables:** 24

---

## Master/Reference Tables (Candidates)

### 1. ra_bookmakers (6 columns)
**Purpose:** Bookmaker reference data
**Columns:** id, name, code, is_active, created_at, type
**Primary Key:** id (bigint, auto-increment)
**Unique Key:** code

### 2. ra_courses (8 columns)
**Purpose:** Race course/venue reference data
**Columns:** id, name, region_code, region, longitude, latitude, created_at, updated_at
**Primary Key:** id (character varying(50))

### 3. ra_dams (47 columns)
**Purpose:** Dam breeding records WITH STATISTICS
**Columns:** id, name, horse_id, created_at, updated_at, total_runners, total_wins, total_places_2nd, total_places_3rd, overall_win_percent, overall_ae_index, best_class, best_class_ae, best_distance, best_distance_ae, analysis_last_updated, data_quality_score, [class breakdowns], [distance breakdowns]
**Primary Key:** id (character varying(50))
**Note:** Has extensive statistics - likely calculated/derived, not API source

### 4. ra_damsires (47 columns)
**Purpose:** Damsire breeding records WITH STATISTICS
**Columns:** Same structure as ra_dams
**Primary Key:** id (character varying(50))
**Note:** Has extensive statistics - likely calculated/derived, not API source

### 5. ra_horses (15 columns)
**Purpose:** Horse reference data
**Columns:** id, name, sire_id, dam_id, damsire_id, dob, age, sex, sex_code, colour, colour_code, breeder, region, created_at, updated_at
**Primary Key:** id (character varying(50))

### 6. ra_jockeys (12 columns)
**Purpose:** Jockey reference data WITH STATISTICS
**Columns:** id, name, created_at, updated_at, total_rides, total_wins, total_places, total_seconds, total_thirds, win_rate, place_rate, stats_updated_at
**Primary Key:** id (character varying(50))

### 7. ra_owners (14 columns)
**Purpose:** Owner reference data WITH STATISTICS
**Columns:** id, name, created_at, updated_at, total_horses, total_runners, total_wins, total_places, total_seconds, total_thirds, win_rate, place_rate, active_last_30d, stats_updated_at
**Primary Key:** id (character varying(50))

### 8. ra_regions (3 columns)
**Purpose:** Region reference data
**Columns:** code, name, created_at
**Primary Key:** code (character varying(10))

### 9. ra_sires (47 columns)
**Purpose:** Sire breeding records WITH STATISTICS
**Columns:** Same structure as ra_dams
**Primary Key:** id (character varying(50))
**Note:** Has extensive statistics - likely calculated/derived, not API source

### 10. ra_trainers (13 columns)
**Purpose:** Trainer reference data WITH STATISTICS
**Columns:** id, name, location, created_at, updated_at, total_runners, total_wins, total_places, total_seconds, total_thirds, win_rate, place_rate, stats_updated_at
**Primary Key:** id (character varying(50))

---

## Transaction/Event Tables

### 11. ra_races (47 columns)
**Purpose:** Race event data
**Columns:** id, course_id, course_name, date, off_time, off_dt, race_name, race_number, distance, distance_round, distance_f, distance_m, region, type, surface, going, going_detailed, pattern, race_class, age_band, sex_restriction, rating_band, prize, field_size, stalls, rail_movements, weather, jumps, is_big_race, is_abandoned, has_result, winning_time, winning_time_detail, comments, non_runners, tote_win, tote_pl, tote_ex, tote_csf, tote_tricast, tote_trifecta, tip, verdict, betting_forecast, meet_id, created_at, updated_at
**Primary Key:** id (character varying(50))

### 12. ra_runners (44 columns)
**Purpose:** Race entries (horses entered in races)
**Columns:** id, race_id, horse_id, horse_name, jockey_name, trainer_name, owner_name, number, draw, jockey_id, trainer_id, owner_id, sire_id, dam_id, damsire_id, weight_lbs, weight_st_lbs, age, sex, sex_code, colour, dob, headgear, headgear_run, wind_surgery, wind_surgery_run, form, last_run, ofr, rpr, ts, comment, spotlight, trainer_rtf, past_results_flags, claiming_price_min, claiming_price_max, medication, equipment, morning_line_odds, is_scratched, silk_url, created_at, updated_at
**Primary Key:** id (bigint, auto-increment)

### 13. ra_race_results (38 columns)
**Purpose:** Race result data (finalized positions)
**Columns:** id, race_id, race_date, horse_id, horse_name, jockey_name, trainer_name, owner_name, position, position_str, number, draw, jockey_id, jockey_claim_lbs, trainer_id, owner_id, sire_id, dam_id, damsire_id, age, sex, weight_lbs, weight_st_lbs, headgear, sp, sp_decimal, btn, ovr_btn, time_seconds, time_display, official_rating, rpr, tsr, prize_won, comment, silk_url, margin, created_at
**Primary Key:** id (bigint, auto-increment)

---

## Odds Tables (Likely from separate Odds Workers)

### 14. ra_odds_historical (36 columns)
**Purpose:** Historical betting odds data
**Source:** Likely external odds data files (see `file_source` column)

### 15. ra_odds_history (6 columns)
**Purpose:** Time-series odds history
**Columns:** id, runner_odds_id, fractional_odds, decimal_odds, timestamp, captured_at

### 16. ra_odds_live (32 columns)
**Purpose:** Live betting odds
**Columns:** Includes bookmaker data, race data, horse data, and live odds

### 17. ra_odds_live_latest (13 columns)
**Purpose:** Latest live odds snapshot

### 18. ra_odds_statistics (11 columns)
**Purpose:** Odds fetching statistics/metadata

### 19. ra_runner_odds (10 columns)
**Purpose:** Runner-level odds data
**Columns:** id, race_id, horse_id, bookmaker_id, fractional_odds, decimal_odds, ew_places, ew_denom, updated_at, captured_at

---

## Analytics/Derived Tables

### 20. ra_entity_combinations (16 columns)
**Purpose:** Performance data for entity pairs (e.g., jockey+trainer, trainer+owner)
**Columns:** id, entity1_type, entity1_id, entity2_type, entity2_id, total_runs, wins, places_2nd, places_3rd, win_percent, place_percent, ae_index, profit_loss_1u, query_filters, calculated_at, created_at

### 21. ra_performance_by_distance (20 columns)
**Purpose:** Distance-based performance analytics
**Columns:** id, entity_type, entity_id, distance_yards, distance_display, total_runs, wins, places_2nd, places_3rd, win_percent, place_percent, ae_index, profit_loss_1u, best_time_seconds, avg_time_seconds, last_time_seconds, going_breakdown, query_filters, calculated_at, created_at

### 22. ra_performance_by_venue (15 columns)
**Purpose:** Venue-based performance analytics
**Columns:** id, entity_type, entity_id, venue_id, total_runs, wins, places_2nd, places_3rd, win_percent, place_percent, ae_index, profit_loss_1u, query_filters, calculated_at, created_at

### 23. ra_runner_statistics (60 columns)
**Purpose:** Comprehensive runner performance statistics
**Columns:** Extensive stats including career prize, course/distance stats, going stats, jockey stats, last 10 runs, last 12 months, etc.

### 24. ra_runner_supplementary (16 columns)
**Purpose:** Supplementary runner data (quotes, stable tours, medical info)
**Columns:** id, runner_id, record_type, entity_type, entity_id, entity_name, change_date, medical_type, medical_date, quote_text, quote_race_id, stable_tour_text, stats_runs, stats_wins, stats_win_percent, created_at

---

## Table Classification Summary

### ✅ MASTER TABLES (Reference Data - Source of Truth from Racing API)
These should have workers that fetch from Racing API:

1. **ra_bookmakers** - Bookmaker reference
2. **ra_courses** - Venue/course reference
3. **ra_horses** - Horse reference
4. **ra_jockeys** - Jockey reference (+ basic stats from API)
5. **ra_owners** - Owner reference (+ basic stats from API)
6. **ra_regions** - Region reference (likely seeded, not API)
7. **ra_trainers** - Trainer reference (+ basic stats from API)

### ✅ BREEDING MASTER TABLES (Reference Data with Statistics)
Source from Racing API + calculated statistics:

8. **ra_sires** - Sire reference + calculated performance stats
9. **ra_dams** - Dam reference + calculated performance stats
10. **ra_damsires** - Damsire reference + calculated performance stats

### 📊 TRANSACTION/EVENT TABLES
Populated by workers fetching race data:

11. **ra_races** - Race events
12. **ra_runners** - Race entries
13. **ra_race_results** - Finalized race results

### 💰 ODDS TABLES
Likely populated by separate odds workers (DarkHorses-Odds-Workers repo):

14. ra_odds_historical
15. ra_odds_history
16. ra_odds_live
17. ra_odds_live_latest
18. ra_odds_statistics
19. ra_runner_odds

### 📈 ANALYTICS/DERIVED TABLES
Calculated from transaction data, not direct API sources:

20. ra_entity_combinations
21. ra_performance_by_distance
22. ra_performance_by_venue
23. ra_runner_statistics
24. ra_runner_supplementary

---

## Key Findings vs Migration Document

### ✅ Confirmed Changes:
1. **Primary keys standardized to `id`** - CONFIRMED
2. **Breeding tables created** (ra_sires, ra_dams, ra_damsires) - CONFIRMED
3. **Statistics fields added** to jockeys/trainers/owners - CONFIRMED
4. **Column renames in ra_races** (race_date→date, off_datetime→off_dt, etc.) - CONFIRMED

### 🆕 NEW TABLES (Not in Migration Doc):
- **ra_regions** - New reference table (3 columns)
- **ra_race_results** - Separate results table (38 columns)
- **ra_entity_combinations** - Analytics table
- **ra_performance_by_distance** - Analytics table
- **ra_performance_by_venue** - Analytics table
- **ra_runner_statistics** - Analytics table
- **ra_runner_supplementary** - Supplementary data table

### 📝 NOTABLE:
- **ra_sires/dams/damsires** now have 47 columns each (extensive statistics)
- Original migration doc showed only 4 columns (id, name, created_at, updated_at)
- Statistics have been added post-migration

---

## Recommendations for Worker Scope

### MASTERS WORKERS SHOULD HANDLE:
1. ✅ ra_bookmakers
2. ✅ ra_courses
3. ✅ ra_horses
4. ✅ ra_jockeys (basic + API stats)
5. ✅ ra_owners (basic + API stats)
6. ✅ ra_trainers (basic + API stats)
7. ✅ ra_sires (basic data only - stats are calculated)
8. ✅ ra_dams (basic data only - stats are calculated)
9. ✅ ra_damsires (basic data only - stats are calculated)
10. ✅ ra_races (events)
11. ✅ ra_runners (race entries)
12. ✅ ra_race_results (race results)

### OUT OF SCOPE (Different Worker Systems):
- **Odds tables** - DarkHorses-Odds-Workers repository
- **Analytics tables** - Calculation workers (separate concern)
- **ra_regions** - Likely seeded data, not API-sourced

---

**Next Step:** User to identify which tables are true "masters" for this worker system.
