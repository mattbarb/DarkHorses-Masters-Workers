# Database Tables and Data Sources Reference

**Last Updated**: 2025-10-23
**Status**: Production System
**Total Tables**: 18

---

## Table of Contents

1. [Master/Reference Tables (9)](#masterreference-tables)
2. [Transaction/Event Tables (4)](#transactionevent-tables)
3. [Calculated/Derived Tables (4)](#calculatedderived-tables)
4. [System Tables (1)](#system-tables)
5. [Data Flow Summary](#data-flow-summary)

---

## Master/Reference Tables

These tables store reference data about entities (horses, people, venues) that rarely changes.

### ⭐ 1. ra_mst_courses

**Purpose**: Racing venues/courses in UK and Ireland

**Data Source**: Racing API `/v1/courses` endpoint

**Fetcher**:
- Primary: `fetchers/masters_fetcher.py` → `MastersFetcher.fetch_courses()`
- Legacy: `fetchers/courses_fetcher.py` → `CoursesFetcher.fetch_and_store()`

**Update Frequency**: Monthly (`python3 main.py --monthly`)

**Key Fields**:
- `id` (PK) - Course ID from API (e.g., "crs_ascot")
- `name` - Course name (e.g., "Ascot")
- `region` - Country code (GB, IRE)
- `latitude`, `longitude` - Coordinates (auto-assigned from validated JSON)
- `surface_type` - Turf, All-Weather, etc.

**Automation**: ✅ Fully automated

**Notes**: Coordinates are automatically assigned from `fetchers/ra_courses_final_validated.json` during insertion

---

### ⭐ 2. ra_mst_bookmakers

**Purpose**: List of bookmakers operating in UK/Ireland

**Data Source**: Hard-coded static list (no API endpoint)

**Fetcher**:
- Primary: `fetchers/masters_fetcher.py` → `MastersFetcher.fetch_bookmakers()`
- Legacy: `fetchers/bookmakers_fetcher.py` → `BookmakersFetcher.fetch_and_store()`

**Update Frequency**: Rarely (only when new bookmakers added)

**Key Fields**:
- `id` (PK) - Bookmaker ID (e.g., "bkm_bet365")
- `name` - Bookmaker name (e.g., "Bet365")
- `region` - Always "GB" or "IRE"

**Automation**: ✅ Fully automated

**Notes**: Static data, manually maintained in fetcher code

---

### ⭐ 3. ra_mst_jockeys

**Purpose**: Jockeys extracted from race data

**Data Source**: Extracted from runners in racecards and results

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_from_runners()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Daily (automatic during race fetching)

**Key Fields**:
- `id` (PK) - Jockey ID from API (e.g., "jky_12345")
- `name` - Jockey name
- `nationality` - Country code

**Automation**: ✅ Fully automated (no manual fetcher needed)

**Notes**:
- Old `fetchers/jockeys_fetcher.py` was deleted - extraction now automatic
- Populated whenever races or results are fetched

---

### ⭐ 4. ra_mst_trainers

**Purpose**: Trainers extracted from race data

**Data Source**: Extracted from runners in racecards and results

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_from_runners()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Daily (automatic during race fetching)

**Key Fields**:
- `id` (PK) - Trainer ID from API (e.g., "trn_12345")
- `name` - Trainer name
- `nationality` - Country code

**Automation**: ✅ Fully automated (no manual fetcher needed)

**Notes**:
- Old `fetchers/trainers_fetcher.py` was deleted - extraction now automatic
- Populated whenever races or results are fetched

---

### ⭐ 5. ra_mst_owners

**Purpose**: Owners extracted from race data

**Data Source**: Extracted from runners in racecards and results

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_from_runners()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Daily (automatic during race fetching)

**Key Fields**:
- `id` (PK) - Owner ID from API (e.g., "own_12345")
- `name` - Owner name (individual or syndicate)

**Automation**: ✅ Fully automated (no manual fetcher needed)

**Notes**:
- Old `fetchers/owners_fetcher.py` was deleted - extraction now automatic
- Populated whenever races or results are fetched

---

### ⭐ 6. ra_mst_horses

**Purpose**: Complete horse records with pedigree and metadata

**Data Source**:
- **Discovery**: Extracted from runners (basic data: id, name, sex)
- **Enrichment**: Racing API `/v1/horses/{id}/pro` endpoint (complete data)

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_from_runners()` + `_enrich_new_horses()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Continuous (NEW horses enriched automatically)

**Key Fields**:
- `id` (PK) - Horse ID from API (e.g., "hrs_12345")
- `name` - Horse name
- `dob` - Date of birth (from enrichment)
- `sex`, `sex_code` - Gender (M/F/G/C)
- `colour`, `colour_code` - Coat color
- `region` - Country of origin (GB, IRE, FR, USA, etc.)
- `sire_id`, `dam_id` - Pedigree links

**Automation**: ✅ Fully automated (hybrid discovery + enrichment)

**Enrichment Process**:
1. Horse discovered in racecard → stored with basic data
2. System checks if horse is NEW (not in database)
3. If NEW: Fetch complete data from `/v1/horses/{id}/pro`
4. Store enriched data (dob, colour, pedigree, etc.)
5. Rate-limited: 2 requests/second (0.5s sleep)

**Notes**:
- ~50 new horses discovered daily
- Enrichment overhead: ~27 seconds/day
- If enrichment fails, stores basic data only

---

### ⭐ 7. ra_mst_sires

**Purpose**: Stallions (male breeding horses)

**Data Source**: Extracted from runner pedigree data

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_breeding_from_runners()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Daily (automatic during race fetching)

**Key Fields**:
- `id` (PK) - Sire ID from API (e.g., "sir_12345")
- `name` - Sire name
- `region` - Country code (from API)
- `horse_id` (FK) - Link to ra_mst_horses (via region-aware matching)

**Automation**: ✅ Fully automated with intelligent matching

**horse_id Matching**:
- **Primary**: Name + Region match (90-95% accuracy)
- **Fallback**: Name-only match (70-85% accuracy)
- **Automatic**: Happens during entity extraction (no manual script needed)

**Expected Coverage**: 40-60% after backfill (many sires didn't race in UK/IRE)

---

### ⭐ 8. ra_mst_dams

**Purpose**: Broodmares (female breeding horses)

**Data Source**: Extracted from runner pedigree data

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_breeding_from_runners()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Daily (automatic during race fetching)

**Key Fields**:
- `id` (PK) - Dam ID from API (e.g., "dam_12345")
- `name` - Dam name
- `region` - Country code (from API)
- `horse_id` (FK) - Link to ra_mst_horses (via region-aware matching)

**Automation**: ✅ Fully automated with intelligent matching

**horse_id Matching**:
- **Primary**: Name + Region match (90-95% accuracy)
- **Fallback**: Name-only match (70-85% accuracy)
- **Automatic**: Happens during entity extraction (no manual script needed)

**Expected Coverage**: 30-40% after backfill (fewer dams raced than sires)

---

### ⭐ 9. ra_mst_damsires

**Purpose**: Maternal grandfathers (dam's sire)

**Data Source**: Extracted from runner pedigree data

**Fetcher**: `utils/entity_extractor.py` → `EntityExtractor.extract_breeding_from_runners()`

**Triggered By**:
- `fetchers/races_fetcher.py` (racecards)
- `fetchers/results_fetcher.py` (results)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**: Daily (automatic during race fetching)

**Key Fields**:
- `id` (PK) - Damsire ID from API (e.g., "dsr_12345")
- `name` - Damsire name
- `region` - Country code (from API)
- `horse_id` (FK) - Link to ra_mst_horses (via region-aware matching)

**Automation**: ✅ Fully automated with intelligent matching

**horse_id Matching**:
- **Primary**: Name + Region match (90-95% accuracy)
- **Fallback**: Name-only match (70-85% accuracy)
- **Automatic**: Happens during entity extraction (no manual script needed)

**Expected Coverage**: 50-60% after backfill

---

## Transaction/Event Tables

These tables store race events and runner entries (transactional data).

### ⭐ 10. ra_races

**Purpose**: Race metadata and conditions

**Data Source**: Racing API `/v1/racecards/pro` AND `/v1/results` endpoints

**Fetcher**:
- `fetchers/races_fetcher.py` → `RacesFetcher.fetch_and_store()` (racecards)
- `fetchers/results_fetcher.py` → `ResultsFetcher.fetch_and_store()` (results)
- `fetchers/events_fetcher.py` → `EventsFetcher.backfill()` (both)

**Update Frequency**: Daily

**Key Fields**:
- `id` (PK) - Race ID from API (e.g., "race_12345")
- `course_id` (FK) - Link to ra_mst_courses
- `race_time` - Scheduled start time
- `race_name` - Race title
- `distance` - Race distance in meters
- `prize_money` - Total prize fund
- `going` - Ground conditions (Soft, Good to Firm, etc.)
- `race_class` - Class 1-7
- `surface_type` - Turf, All-Weather

**Automation**: ✅ Fully automated

**UPSERT Behavior**: Yes - updates existing races with latest data

**Notes**:
- Racecards provide pre-race data
- Results provide post-race updates (going, actual conditions)

---

### ⭐ 11. ra_runners

**Purpose**: Individual horse entries in races with results

**Data Source**: Nested in racecards and results from API

**Fetcher**:
- `fetchers/races_fetcher.py` → `_transform_racecard()` (pre-race)
- `fetchers/results_fetcher.py` → `_prepare_runner_records()` (post-race)
- `fetchers/events_fetcher.py` (both)

**Update Frequency**:
- Pre-race: Daily (racecards)
- Post-race: Daily (results update with positions)

**Key Fields**:

*Entity Links:*
- `race_id` (FK) - Link to ra_races
- `horse_id` (FK) - Link to ra_mst_horses
- `jockey_id` (FK) - Link to ra_mst_jockeys
- `trainer_id` (FK) - Link to ra_mst_trainers
- `owner_id` (FK) - Link to ra_mst_owners

*Pedigree Links (with validation):*
- `sire_id` (FK) - Link to ra_mst_sires (validated)
- `dam_id` (FK) - Link to ra_mst_dams (validated)
- `damsire_id` (FK) - Link to ra_mst_damsires (validated)

*Pre-Race Data:*
- `number` - Saddle cloth number
- `draw` - Starting stall position
- `weight_lbs` - Carried weight
- `age` - Horse age at race time
- `official_rating` - Handicap rating
- `jockey_claim_lbs` - Apprentice allowance
- `weight_stones_lbs` - UK format weight (e.g., "9-7")
- `jockey_silk_url` - SVG image URL

*Post-Race Data (NULL until race completes):*
- `position` - Finishing position (1, 2, 3, etc.)
- `distance_beaten` - Lengths behind winner
- `overall_beaten_distance` - Alternative distance metric
- `prize_won` - Prize money earned
- `starting_price` - Fractional odds (e.g., "7/2")
- `starting_price_decimal` - Decimal odds (e.g., 4.50)
- `finishing_time` - Race time (e.g., "1:48.55")
- `race_comment` - Running commentary/notes

**Automation**: ✅ Fully automated

**Pedigree Validation**: ✅ IDs validated before insertion (prevents FK violations)

**Enhanced Fields**: 6 new fields added via Migration 011 (2025-10-17)

**UPSERT Behavior**: Yes - racecards create records, results update with positions

---

### ⭐ 12. ra_race_results

**Purpose**: Denormalized view of race results (flattened for easier querying)

**Data Source**: Racing API `/v1/results` endpoint

**Fetcher**: `fetchers/results_fetcher.py` → `_transform_result()`

**Update Frequency**: Daily (last 365 days)

**Key Fields**:
- Combines race metadata + runner results in single record
- Flattened structure for ML/analytics queries
- Includes: race_name, course_name, horse_name, position, distance_beaten, etc.

**Automation**: ✅ Fully automated

**Notes**:
- Redundant with ra_races + ra_runners but optimized for queries
- Useful for reporting and analytics

---

### ⭐ 13. ra_horse_pedigree

**Purpose**: Complete pedigree lineage for horses

**Data Source**: Racing API `/v1/horses/{id}/pro` endpoint

**Fetcher**: `utils/entity_extractor.py` → `_enrich_new_horses()`

**Triggered By**: Automatic when NEW horse discovered

**Update Frequency**: Continuous (NEW horses only)

**Key Fields**:
- `horse_id` (FK) - Link to ra_mst_horses
- `sire_id`, `sire_name` - Father
- `dam_id`, `dam_name` - Mother
- `damsire_id`, `damsire_name` - Maternal grandfather
- `breeder_id`, `breeder_name` - Breeder

**Automation**: ✅ Fully automated for new horses

**Manual Backfill**: `scripts/backfill/backfill_horse_pedigree_enhanced.py`
- For existing horses that lack pedigree data
- One-time/occasional operation
- Resume-capable for large backfills

---

## Calculated/Derived Tables

These tables are calculated from existing data (not fetched from API).

### ⭐ 14-16. Sire/Dam/Damsire Statistics

**Tables**:
- `ra_mst_sires_statistics`
- `ra_mst_dams_statistics`
- `ra_mst_damsires_statistics`

**Purpose**: Career statistics for breeding horses

**Data Source**: Calculated from ra_runners + ra_race_results

**Script**: `scripts/backfill/backfill_ancestor_stats.py`

**Update Frequency**: ⚠️ **MANUAL** (should be scheduled monthly)

**Key Metrics Calculated**:
- Total offspring
- Total wins
- Win percentage
- Earnings
- Average finishing position
- Performance by surface/distance/class

**Automation**: ❌ Currently manual - should be automated

**Recommended Schedule**: Monthly (after race/results updates)

---

### ⭐ 17. ra_lineage

**Purpose**: Extended pedigree tree (beyond sire/dam/damsire)

**Data Source**: Calculated from ra_horse_pedigree

**Script**: `scripts/backfill/backfill_ra_lineage.py`

**Update Frequency**: ⚠️ **MANUAL** (should be automated)

**Purpose**: Multi-generation pedigree tracking

**Automation**: ❌ Currently manual - should integrate into entity extraction

**Status**: Unclear if actively used - needs review

---

## System Tables

### ⭐ 18. ra_metadata_tracking

**Purpose**: Track last update timestamp for each table

**Data Source**: Updated by fetchers after successful operations

**Update Frequency**: After every fetch operation

**Key Fields**:
- `table_name` - Table being tracked
- `last_updated` - Timestamp of last successful update
- `record_count` - Optional count of records

**Automation**: ✅ Should be automated (verify fetchers update this)

**Notes**: Used for monitoring data freshness

---

## Data Flow Summary

### Daily Operations (`python3 main.py --daily`)

```
1. Fetch Racecards (races_fetcher.py)
   ├─ Insert/Update: ra_races
   ├─ Extract & Insert: ra_mst_jockeys, ra_mst_trainers, ra_mst_owners
   ├─ Extract & Enrich: ra_mst_horses (NEW horses only)
   ├─ Extract Pedigree: ra_mst_sires, ra_mst_dams, ra_mst_damsires
   ├─ Capture Lineage: ra_horse_pedigree (NEW horses only)
   └─ Insert Runners: ra_runners (with pedigree validation)

2. Fetch Results (results_fetcher.py)
   ├─ Update: ra_races (with actual conditions)
   ├─ Extract & Insert: ra_mst_jockeys, ra_mst_trainers, ra_mst_owners
   ├─ Extract & Enrich: ra_mst_horses (NEW horses only)
   ├─ Extract Pedigree: ra_mst_sires, ra_mst_dams, ra_mst_damsires
   ├─ Capture Lineage: ra_horse_pedigree (NEW horses only)
   ├─ Update Runners: ra_runners (with positions/prizes)
   └─ Insert Results: ra_race_results (denormalized view)
```

### Weekly Operations (`python3 main.py --weekly`)

```
1. Fetch Horses (horses_fetcher.py)
   └─ Bulk sync of ra_mst_horses (rare - most come from races)
```

### Monthly Operations (`python3 main.py --monthly`)

```
1. Fetch Courses (masters_fetcher.py)
   └─ Update: ra_mst_courses (with coordinates)

2. Fetch Bookmakers (masters_fetcher.py)
   └─ Update: ra_mst_bookmakers
```

### Backfill Operations

**Events Backfill** (Fully Automated):
```bash
python3 scripts/backfill/backfill_events.py --start-date 2015-01-01
```
- Populates ALL tables listed in "Daily Operations" above
- Resume-capable via checkpoint
- ~11 days to complete 2015-2025

**Horse Pedigree Backfill** (Manual, One-Time):
```bash
python3 scripts/backfill/backfill_horse_pedigree_enhanced.py
```
- Enriches existing horses that lack pedigree data
- Resume-capable
- ~24 hours for 100,000+ horses

**Ancestor Statistics** (Manual, Should Be Scheduled):
```bash
python3 scripts/backfill/backfill_ancestor_stats.py
```
- Calculates sire/dam/damsire career stats
- Run monthly after race/results updates

---

## Automation Status Summary

| Table | Automation | Fetcher/Script | Frequency |
|-------|-----------|----------------|-----------|
| ra_mst_courses | ✅ Full | masters_fetcher.py | Monthly |
| ra_mst_bookmakers | ✅ Full | masters_fetcher.py | Rarely |
| ra_mst_jockeys | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_mst_trainers | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_mst_owners | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_mst_horses | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_mst_sires | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_mst_dams | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_mst_damsires | ✅ Full | entity_extractor.py | Daily (auto) |
| ra_races | ✅ Full | races/results_fetcher.py | Daily |
| ra_runners | ✅ Full | races/results_fetcher.py | Daily |
| ra_race_results | ✅ Full | results_fetcher.py | Daily |
| ra_horse_pedigree | ✅ Full | entity_extractor.py | Daily (auto) |
| *_statistics (3) | ⚠️ Manual | backfill_ancestor_stats.py | Should be monthly |
| ra_lineage | ⚠️ Manual | backfill_ra_lineage.py | Unclear |
| ra_metadata_tracking | ✅ Should be | All fetchers | After each fetch |

**Fully Automated**: 13/18 tables (72%)
**Manual (Should Automate)**: 4/18 tables (22%)
**System Table**: 1/18 tables (6%)

---

## Key Features

### ✅ Region-Aware horse_id Matching
- **Tables Affected**: ra_mst_sires, ra_mst_dams, ra_mst_damsires
- **Accuracy**: 90-95% with region, 70-85% name-only
- **Automation**: Fully automatic during entity extraction
- **Implementation**: `utils/entity_extractor.py` lines 116-248

### ✅ Pedigree ID Validation
- **Tables Affected**: ra_runners
- **Purpose**: Prevent foreign key violations
- **Automation**: Automatic before insertion
- **Implementation**:
  - `fetchers/races_fetcher.py` lines 368-433
  - `fetchers/results_fetcher.py` lines 378-443

### ✅ Hybrid Horse Enrichment
- **Table Affected**: ra_mst_horses
- **Discovery**: Extract from racecards (basic data)
- **Enrichment**: Fetch from `/v1/horses/{id}/pro` (complete data)
- **Rate Limit**: 2 req/sec (0.5s sleep)
- **Automation**: Automatic for NEW horses only

### ✅ UPSERT Strategy
- **All Tables**: Use INSERT ON CONFLICT UPDATE
- **Benefit**: Prevents duplicates, updates existing records
- **Implementation**: `utils/supabase_client.py`

---

## Notes

- **Regional Filter**: ALL data limited to UK (GB) and Ireland (IRE)
- **API Rate Limit**: 2 requests/second across all endpoints
- **Backfill Checkpoint**: Automatic resume capability for long-running operations
- **Foreign Keys**: All FK columns validated before insertion (no orphaned records)
- **Entity Extraction Order**: Entities inserted BEFORE runners (dependency management)

---

**Prepared by**: Claude Code
**Document Version**: 1.0
**System Status**: Production-Ready
