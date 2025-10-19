# Complete Data Collection Strategy: 2015-2025

## Executive Summary

**You have access to 10+ years of complete racing data** through two powerful API endpoints. The `/v1/results` endpoint (with your £299 premium add-on) provides **complete historical race results with full entity data from 2015 onwards**, including all horse, jockey, trainer, and owner information. The `/v1/racecards/pro` endpoint provides **detailed pre-race data from January 23, 2023 onwards**, including form, ratings, and odds histories.

**THE CRITICAL INSIGHT:** Both endpoints return full entity information (horse_id, jockey_id, trainer_id, owner_id, and their names). This means you can extract and populate your entity tables from BOTH results (2015-2022) AND racecards (2023-2025). Your current code already handles entity extraction from racecards - we just need to enable it for results as well.

---

## Data Availability Matrix

| Data Type | Time Period | Endpoint | Entity Data Available | Status |
|-----------|-------------|----------|----------------------|--------|
| **Historical Results** | 2015-01-01 to 2022-12-31 | `/v1/results` | ✅ YES (horse, jockey, trainer, owner IDs + names) | **Premium Add-on** |
| **Historical Results** | 2023-01-01 to 2023-01-22 | `/v1/results` | ✅ YES (horse, jockey, trainer, owner IDs + names) | **Premium Add-on** |
| **Racecards (Pre-race)** | 2023-01-23 to Present | `/v1/racecards/pro` | ✅ YES (horse, jockey, trainer, owner IDs + names + extra details) | **Pro Plan** |
| **Future Racecards** | Today to +7 days | `/v1/racecards/pro` | ✅ YES (horse, jockey, trainer, owner IDs + names + extra details) | **Pro Plan** |

### Field Comparison: Results vs Racecards

#### Results Endpoint (`/v1/results`) - 2015 to Present
**Race-level fields:**
- race_id, date, region, course, course_id, off, off_dt
- race_name, type, class, pattern, rating_band, age_band, sex_rest
- dist, dist_y, dist_m, dist_f (distance in multiple formats)
- going, surface, jumps
- winning_time_detail, comments, non_runners
- tote_win, tote_pl, tote_ex, tote_csf, tote_tricast, tote_trifecta

**Runner-level fields (includes FULL entity data):**
- **horse_id**, **horse** (name)
- **jockey_id**, **jockey** (name), jockey_claim_lbs
- **trainer_id**, **trainer** (name)
- **owner_id**, **owner** (name)
- **sire_id**, **sire** (name)
- **dam_id**, **dam** (name)
- **damsire_id**, **damsire** (name)
- sp, sp_dec (starting price), number, position, draw
- btn (beaten by), ovr_btn (overall beaten by)
- age, sex, weight, weight_lbs, headgear
- time, or (official rating), rpr (Racing Post Rating), tsr (Timeform Speed Rating)
- prize, comment, silk_url

#### Racecards Endpoint (`/v1/racecards/pro`) - 2023-01-23 to Present
**Race-level fields:**
- race_id, course, course_id, date, off_time, off_dt
- race_name, distance_round, distance, distance_f
- region, pattern, sex_restriction, race_class, type, age_band, rating_band
- prize, field_size, going, going_detailed, surface, jumps
- rail_movements, stalls, weather
- big_race, is_abandoned, tip, verdict, betting_forecast

**Runner-level fields (includes FULL entity data + extras):**
- **horse_id**, **horse** (name), dob, age, sex, sex_code, colour, region, breeder
- **jockey_id**, **jockey** (name)
- **trainer_id**, **trainer** (name), trainer_location, trainer_14_days, prev_trainers
- **owner_id**, **owner** (name), prev_owners
- **sire_id**, **sire** (name), sire_region
- **dam_id**, **dam** (name), dam_region
- **damsire_id**, **damsire** (name), damsire_region
- comment, spotlight, quotes, stable_tour, medical
- number, draw, headgear, headgear_run
- wind_surgery, wind_surgery_run, past_results_flags
- lbs (weight), ofr (official rating), rpr, ts (top speed)
- last_run, form, trainer_rtf
- **odds** (complete historical odds timeline)
- silk_url

---

## Three-Phase Collection Strategy

### Phase 1: Historical Results & Entity Extraction (2015-01-01 to 2023-01-22)
**Duration:** ~8 years (2,943 days)
**Endpoint:** `/v1/results`
**What You Get:**
- Complete race results for every UK & Ireland race
- Full finishing positions and performance data
- **ALL entity data**: horses, jockeys, trainers, owners (with IDs and names)
- Sire/dam/damsire lineage information
- Starting prices, ratings (OR, RPR, TSR)
- Tote returns and betting information

**Process:**
1. Fetch results day-by-day using `/v1/results?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD&region=gb,ire`
2. Store results in `ra_results` table
3. Extract runners from each result and store in `ra_runners` table
4. **Extract entities from runners:**
   - Horses (horse_id, name, sex) → `ra_horses`
   - Jockeys (jockey_id, name) → `ra_jockeys`
   - Trainers (trainer_id, name) → `ra_trainers`
   - Owners (owner_id, name) → `ra_owners`

**Tables Populated:**
- `ra_results` - Race result records
- `ra_runners` - Runner performance records (with finishing positions)
- `ra_horses` - Unique horses
- `ra_jockeys` - Unique jockeys
- `ra_trainers` - Unique trainers
- `ra_owners` - Unique owners

### Phase 2: Historical Racecards & Entity Extraction (2023-01-23 to Yesterday)
**Duration:** ~2.7 years (987 days as of Oct 2025)
**Endpoint:** `/v1/racecards/pro`
**What You Get:**
- Complete pre-race data (racecards) for every UK & Ireland race
- All entity data PLUS enhanced details (form, quotes, stable tours, medical notes)
- Complete odds histories for each runner
- Trainer and owner history (previous connections)
- More detailed horse information (DOB, colour, breeder, region)

**Process:**
1. Fetch racecards day-by-day using `/v1/racecards/pro?date=YYYY-MM-DD&region_codes=gb,ire`
2. Store races in `ra_races` table
3. Extract runners and store in `ra_runners` table
4. **Extract entities from runners** (same as Phase 1, but with more detailed data)

**Tables Populated:**
- `ra_races` - Race cards (pre-race data)
- `ra_runners` - Runner entries (with form, ratings, odds)
- `ra_horses` - Unique horses (updates with more details)
- `ra_jockeys` - Unique jockeys
- `ra_trainers` - Unique trainers
- `ra_owners` - Unique owners

### Phase 3: Reference Data (Courses & Bookmakers)
**Duration:** One-time fetch
**Endpoints:** `/v1/courses`, `/v1/bookmakers`
**What You Get:**
- Complete list of racecourses with IDs and regions
- Complete list of bookmakers with IDs

**Process:**
1. Fetch all courses once
2. Fetch all bookmakers once
3. Store in respective tables

**Tables Populated:**
- `ra_courses` - Racecourse reference data
- `ra_bookmakers` - Bookmaker reference data

---

## Expected Results (Estimated Counts)

Based on UK & Irish racing averages:

| Table | Estimated Records | Notes |
|-------|------------------|-------|
| `ra_courses` | ~150 | One-time reference data |
| `ra_bookmakers` | ~50 | One-time reference data |
| `ra_results` | ~40,000 | 2015-2023 (pre-racecards era) @ ~14 races/day |
| `ra_races` | ~15,000 | 2023-2025 (racecards era) @ ~15 races/day |
| `ra_runners` | ~600,000 | Combined from results + racecards (avg 11 runners/race) |
| `ra_horses` | ~80,000 | Unique horses across 10 years |
| `ra_jockeys` | ~3,000 | Unique jockeys (active + retired) |
| `ra_trainers` | ~2,500 | Unique trainers (active + retired) |
| `ra_owners` | ~25,000 | Unique owners/syndicates |

**Total Database Size:** ~1.4 million records across all tables

---

## Implementation Steps

### Step 1: Update Entity Extractor (ALREADY DONE ✅)
Your `utils/entity_extractor.py` already handles entity extraction from runner data. It extracts:
- Horse ID, name, and sex
- Jockey ID and name
- Trainer ID and name
- Owner ID and name

**No changes needed** - it works with data from both endpoints!

### Step 2: Update Results Fetcher to Extract Entities
Currently, `fetchers/results_fetcher.py` fetches and stores results but does NOT extract entities.

**Required Change:** Add entity extraction to results fetcher (similar to how `races_fetcher.py` does it).

**Add to ResultsFetcher class:**

```python
from utils.entity_extractor import EntityExtractor

def __init__(self):
    # ... existing code ...
    self.entity_extractor = EntityExtractor(self.db_client)
```

**Update the fetch_and_store method to extract entities from results:**

```python
# After storing results, extract entities from runners
if all_results:
    # First, we need to extract runners from results
    # The results API returns runners nested in each result
    all_runners = []
    for result in all_results:
        runners = result.get('api_data', {}).get('runners', [])
        for runner in runners:
            # Transform runner data to match expected format
            runner_data = {
                'horse_id': runner.get('horse_id'),
                'horse_name': runner.get('horse'),
                'sex': runner.get('sex'),
                'jockey_id': runner.get('jockey_id'),
                'jockey_name': runner.get('jockey'),
                'trainer_id': runner.get('trainer_id'),
                'trainer_name': runner.get('trainer'),
                'owner_id': runner.get('owner_id'),
                'owner_name': runner.get('owner')
            }
            if runner_data['horse_id'] and runner_data['horse_name']:
                all_runners.append(runner_data)

    # Extract and store entities
    if all_runners:
        logger.info("Extracting entities from runner data...")
        entity_stats = self.entity_extractor.extract_and_store_from_runners(all_runners)
        results_dict['entities'] = entity_stats
```

### Step 3: Run the Complete Initialization
The existing `initialize_data.py` script is already set up correctly! It:
1. Fetches results from 2015-2023 (Phase 1)
2. Fetches racecards from 2023-present (Phase 2)
3. Fetches reference data (Phase 3)

Once you update the results fetcher (Step 2), you can run:

```bash
python3 initialize_data.py
```

**That's it!** One command gets everything.

### Step 4: Monitor Progress
The initialization script provides detailed progress logging:
- Shows chunks being processed (90-day batches)
- Displays progress percentage
- Reports records inserted for each entity type
- Provides final summary with total counts

**Expected Runtime:**
- Phase 1 (2015-2023 results): ~8-12 hours (2,943 days @ 2 req/sec with pauses)
- Phase 2 (2023-2025 racecards): ~3-4 hours (987 days @ 2 req/sec with pauses)
- Phase 3 (Reference data): ~1 minute
- **Total: 11-16 hours**

---

## Code Changes Required

### File: `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/results_fetcher.py`

**Changes needed:**
1. Import EntityExtractor
2. Initialize entity_extractor in `__init__`
3. Extract runners from results data
4. Call entity_extractor.extract_and_store_from_runners()

**Detailed implementation** in Step 2 above.

---

## The Single Command

Once the code changes are made:

```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
python3 initialize_data.py
```

**What this command does:**
1. Fetches all courses and bookmakers (reference data)
2. Fetches all results from 2015-01-01 to 2023-01-22 in 90-day chunks
   - Stores results in `ra_results`
   - Extracts and stores entities (horses, jockeys, trainers, owners)
3. Fetches all racecards from 2023-01-23 to present in 90-day chunks
   - Stores racecards in `ra_races` and runners in `ra_runners`
   - Extracts and stores entities (with enhanced data)
4. Provides detailed progress logging and final summary

**Optional flags:**
```bash
# Start from a specific date (e.g., 2020)
python3 initialize_data.py --from 2020-01-01

# Skip reference data if already loaded
python3 initialize_data.py --skip-reference

# Test mode (only last 7 days)
python3 initialize_data.py --test
```

---

## Key Technical Details

### API Rate Limits
- **Rate limit:** 2 requests per second
- **Strategy:** Day-by-day fetching with 5-second pauses between 90-day chunks
- **Estimated API calls:** ~4,000 calls total (one per day from 2015-2025)
- **Estimated time:** 11-16 hours (includes rate limit compliance and processing time)

### Database Constraints
- All tables use **upsert** strategy (INSERT with ON CONFLICT DO UPDATE)
- Entity tables use **deduplication** (one record per unique ID)
- Foreign keys link runners to races and entities
- `api_data` JSONB field stores complete raw API response for audit trail

### Data Quality
- **Entity IDs are stable** - The Racing API uses consistent IDs across endpoints
- **Duplicate handling** - Entities extracted from both results and racecards will merge (same ID = same entity)
- **Data enrichment** - Racecards provide more detail than results, so entities get enriched over time
- **Missing data** - Some fields may be null (e.g., not all runners have owner_id in older races)

---

## Summary: What You're Actually Getting

### From 2015-2022 (8 years)
- ✅ Every race result
- ✅ Every runner's performance (position, time, beaten by)
- ✅ Every horse, jockey, trainer, owner (with IDs and names)
- ✅ Lineage data (sire, dam, damsire)
- ✅ Ratings and starting prices

### From 2023-2025 (2.7 years)
- ✅ Every racecard (pre-race data)
- ✅ Every runner's entry (form, ratings, odds history)
- ✅ Every horse, jockey, trainer, owner (with enhanced details)
- ✅ Form comments, spotlights, stable tours
- ✅ Complete odds movements over time

### Total Coverage
- **10+ years of complete racing data**
- **~80,000 unique horses**
- **~3,000 unique jockeys**
- **~2,500 unique trainers**
- **~25,000 unique owners**
- **~55,000 races**
- **~600,000 runner performances**

**You have everything you need to build comprehensive racing models, analyze performance trends, track connections, and identify patterns across a full decade of UK & Irish racing.**

---

## Next Steps

1. ✅ Review this plan (you're doing this now)
2. 🔨 Update `fetchers/results_fetcher.py` to extract entities (Step 2)
3. ▶️ Run `python3 initialize_data.py`
4. ⏱️ Wait 11-16 hours for completion
5. 🎉 Query your complete 2015-2025 database

**Questions or issues?** Check the logs in `/logs/` directory - every step is logged with timestamps and record counts.
