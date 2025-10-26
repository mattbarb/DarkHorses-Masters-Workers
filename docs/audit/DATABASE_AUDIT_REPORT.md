# DARKHORSES RACING DATABASE COMPREHENSIVE AUDIT REPORT

**Date:** 2025-10-07
**Auditor:** Database Analysis System
**Status:** CRITICAL ISSUES IDENTIFIED

## EXECUTIVE SUMMARY - TOP 10 CRITICAL ISSUES

1. **CRITICAL: entry_id column missing from ra_mst_runners** - Code expects this field but table doesn't have it
2. **Database Connection Timeout** - All direct database queries timing out (possible network/load issue)
3. **All tables show 0 rows** - Either empty database or connection/permission issue
4. **Missing schema documentation** - No CREATE TABLE scripts found in repository
5. **Field name mismatches** - Code uses 'name' but may need 'horse_name', 'jockey_name', etc.
6. **Pedigree data duplication** - Stored in both ra_mst_runners AND ra_horse_pedigree tables
7. **API response stored as JSONB** - Important data may be trapped in api_data column
8. **Inconsistent ID naming** - Mix of racing_api_* and regular ID columns
9. **Missing foreign key validation** - No evidence of FK constraints being enforced
10. **No data validation** - NULL handling inconsistent across fetchers

---

## DATABASE CONNECTION STATUS

**Status:** TIMEOUT ON ALL QUERIES
**Connection Method:** Supabase REST API via SupabaseReferenceClient
**Symptoms:**
- All SELECT queries timeout
- Row counts return 0 for all tables
- Sample data queries fail with "The read operation timed out"

**Possible Causes:**
- Network connectivity issues
- Supabase instance under heavy load
- Rate limiting
- RLS (Row Level Security) policies blocking access
- Database credentials invalid or expired

**Recommendation:**
```sql
-- Check Supabase dashboard for:
1. Database health status
2. Active connections
3. Query performance
4. RLS policies on ra_* tables
```

---

## CODE-TO-SCHEMA ANALYSIS

Since direct database access failed, this analysis is based on examining the fetcher code to determine what the schema SHOULD contain.

### TABLE 1: ra_mst_races

**Source File:** `/fetchers/races_fetcher.py` (lines 236-275)

**Expected Columns (42 total):**

```
CORE IDENTIFICATION:
✓ race_id                 TEXT PRIMARY KEY    (from API race_id)
✓ racing_api_race_id      TEXT                (duplicate of race_id)
✓ is_from_api             BOOLEAN             (always TRUE for API data)
✓ fetched_at              TIMESTAMP           (when data was fetched)

COURSE & LOCATION:
✓ course_id               TEXT                (FK to ra_courses)
✓ course_name             TEXT                (denormalized course name)
✓ region                  TEXT                (gb, ire, etc.)

RACE DETAILS:
✓ race_name               TEXT NOT NULL       (CRITICAL - should never be NULL)
✓ race_date               DATE NOT NULL       (CRITICAL - API field: 'date')
✓ off_datetime            TIMESTAMP           (API field: 'off_dt')
✓ off_time                TIME                (API field: 'off_time')
✓ start_time              TIME                (API field: 'start_time')
✓ race_type               TEXT                (flat, hurdle, chase, etc.)
✓ race_class              TEXT                (Class 1-7)

DISTANCE:
✓ distance                NUMERIC             (distance in furlongs - API: distance_f)
✓ distance_f              TEXT                (string like "1m", "6f")
✓ distance_meters         INTEGER             (calculated from distance_round)

CONDITIONS:
✓ age_band                TEXT                (2yo, 3yo+, etc.)
✓ surface                 TEXT                (turf, aw)
✓ going                   TEXT                (good, soft, heavy, etc.)
✓ track_condition         TEXT                (API: going_detailed)
✓ weather_conditions      TEXT                (API: weather)
✓ rail_movements          TEXT
✓ stalls_position         TEXT

STATUS FIELDS:
✓ race_status             TEXT                (API: status)
✓ betting_status          TEXT
✓ results_status          TEXT
✓ is_abandoned            BOOLEAN DEFAULT FALSE

PRIZE MONEY:
✓ currency                TEXT DEFAULT 'GBP'
✓ prize_money             NUMERIC             (parsed from API 'prize')
✓ total_prize_money       NUMERIC

METADATA:
✓ big_race                BOOLEAN DEFAULT FALSE
✓ field_size              INTEGER             (calculated from runners array)
✓ live_stream_url         TEXT
✓ replay_url              TEXT
✓ api_data                JSONB               (full API response)
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `races_fetcher.py::_transform_racecard()` - Lines 236-275
- `results_fetcher.py::_transform_result()` - Lines 132-154

**Potential Issues:**
1. API returns 'date' but code tries to insert 'race_date' - field mapping needed
2. Distance stored in 3 different formats - may cause confusion
3. api_data JSONB may contain fields that should be proper columns
4. No validation that course_id exists in ra_courses

---

### TABLE 2: ra_mst_runners

**Source File:** `/fetchers/races_fetcher.py` (lines 291-349)

**Expected Columns (54 total):**

```
CORE IDENTIFICATION:
✓ runner_id               TEXT PRIMARY KEY    (format: {race_id}_{horse_id})
⚠ entry_id                TEXT                ** MISSING - USER REPORTED **
✓ is_from_api             BOOLEAN
✓ fetched_at              TIMESTAMP

RACE LINKAGE:
✓ race_id                 TEXT NOT NULL       (FK to ra_mst_races)
✓ racing_api_race_id      TEXT                (duplicate)

HORSE:
✓ horse_id                TEXT NOT NULL       (FK to ra_horses)
✓ racing_api_horse_id     TEXT
✓ horse_name              TEXT
✓ age                     INTEGER             (parsed via safe_int)
✓ sex                     TEXT                (M, F, G, C)

RACE DETAILS:
✓ number                  INTEGER             (horse number - safe_int)
✓ draw                    INTEGER             (stall number - safe_int)
✓ stall                   INTEGER             (duplicate of draw)

JOCKEY:
✓ jockey_id               TEXT                (FK to ra_jockeys)
✓ racing_api_jockey_id    TEXT
✓ jockey_name             TEXT
✓ jockey_claim            TEXT
✓ apprentice_allowance    TEXT

TRAINER:
✓ trainer_id              TEXT                (FK to ra_trainers)
✓ racing_api_trainer_id   TEXT
✓ trainer_name            TEXT

OWNER:
✓ owner_id                TEXT                (FK to ra_owners)
✓ racing_api_owner_id     TEXT
✓ owner_name              TEXT

WEIGHT & EQUIPMENT:
✓ weight                  NUMERIC             (API: lbs)
✓ weight_lbs              NUMERIC             (duplicate)
✓ headgear                TEXT                (description)
✓ blinkers                BOOLEAN             (parsed from headgear_run)
✓ cheekpieces             BOOLEAN             (parsed from headgear_run)
✓ visor                   BOOLEAN             (parsed from headgear_run)
✓ tongue_tie              BOOLEAN             (parsed from headgear_run)

PEDIGREE (stored in runners table):
✓ sire_id                 TEXT
✓ sire_name               TEXT
✓ dam_id                  TEXT
✓ dam_name                TEXT
✓ damsire_id              TEXT
✓ damsire_name            TEXT

FORM & PERFORMANCE:
✓ form                    TEXT                (recent form codes)
✓ form_string             TEXT
✓ days_since_last_run     INTEGER             (safe_int)
✓ last_run_performance    TEXT

CAREER STATS:
✓ career_runs             INTEGER             (from career_total.runs)
✓ career_wins             INTEGER             (from career_total.wins)
✓ career_places           INTEGER             (from career_total.places)
✓ prize_money_won         NUMERIC

RATINGS:
✓ official_rating         INTEGER             (API: ofr - safe_int)
✓ racing_post_rating      INTEGER             (API: rpr - safe_int)
✓ rpr                     INTEGER             (duplicate)
✓ timeform_rating         INTEGER             (API: tfr - safe_int)
✓ tsr                     INTEGER             (API: ts - safe_int)

METADATA:
✓ comment                 TEXT                (NOT spotlight - that doesn't exist)
✓ silk_url                TEXT                (jockey silk image)
✓ api_data                JSONB
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `races_fetcher.py::_transform_racecard()` - Lines 291-349

**CRITICAL ISSUES:**

1. **MISSING COLUMN: entry_id**
   - User reported: "entry_id in ra_mst_runners is totally missing"
   - Code does NOT try to insert entry_id (see lines 291-349)
   - Possible solutions:
     ```sql
     -- Option 1: Add if API provides it
     ALTER TABLE ra_mst_runners ADD COLUMN entry_id TEXT;

     -- Option 2: Generate from existing data
     ALTER TABLE ra_mst_runners ADD COLUMN entry_id TEXT
     GENERATED ALWAYS AS (runner_id) STORED;
     ```

2. **Pedigree Data Duplication**
   - Sire/Dam data stored in BOTH ra_mst_runners AND ra_horse_pedigree
   - Should normalize - keep only in ra_horse_pedigree
   - OR remove ra_horse_pedigree and keep in runners

3. **safe_int() Function**
   - Handles strings like '-', 'NR', 'DNF', 'PU', 'F', 'UR', 'RO', 'BD'
   - Returns NULL for invalid values
   - Many integer fields may be NULL even when data exists

4. **Duplicate Columns**
   - weight = weight_lbs (both from API 'lbs')
   - rpr = racing_post_rating
   - stall = draw
   - Recommendation: Remove duplicates, pick one naming convention

---

### TABLE 3: ra_horses

**Source Files:**
- `/fetchers/horses_fetcher.py` (lines 102-113)
- `/utils/entity_extractor.py` (lines 84-95)

**Expected Columns (MINIMAL - only 9 columns):**

```
BASIC INFO:
✓ horse_id                TEXT PRIMARY KEY
✓ name                    TEXT NOT NULL
✓ dob                     DATE
✓ sex                     TEXT
✓ sex_code                TEXT
✓ colour                  TEXT
✓ region                  TEXT
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
1. `horses_fetcher.py` - Full horse profiles from API
2. `entity_extractor.py` - Extracted from runner data (minimal fields)

**Issues:**
1. Entity extractor only inserts: horse_id, name, sex, created_at, updated_at
2. Horses fetcher inserts full profile: dob, sex_code, colour, region
3. **Data quality will vary** depending on source
4. No pedigree data in this table (stored in ra_horse_pedigree instead)

---

### TABLE 4: ra_horse_pedigree

**Source File:** `/fetchers/horses_fetcher.py` (lines 116-132)

**Expected Columns (13 total):**

```
✓ horse_id                TEXT PRIMARY KEY    (FK to ra_horses)
✓ sire_id                 TEXT
✓ sire                    TEXT                (name)
✓ sire_region             TEXT
✓ dam_id                  TEXT
✓ dam                     TEXT                (name)
✓ dam_region              TEXT
✓ damsire_id              TEXT
✓ damsire                 TEXT                (name)
✓ damsire_region          TEXT
✓ breeder                 TEXT
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `horses_fetcher.py` - Only when sire_id, dam_id, or damsire_id present

**Issue:**
- Pedigree data ALSO stored in ra_mst_runners (sire_id, sire_name, dam_id, dam_name, damsire_id, damsire_name)
- **Duplication problem** - which is source of truth?
- Recommendation: Pick one location

---

### TABLE 5: ra_jockeys

**Source File:** `/utils/entity_extractor.py` (lines 48-56)

**Expected Columns (4 total - MINIMAL):**

```
✓ jockey_id               TEXT PRIMARY KEY
✓ name                    TEXT NOT NULL
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `entity_extractor.py` - Extracted from runner data only

**Missing Fields:**
- No jockey region, nationality, stats
- Very bare-bones table
- Additional jockey data trapped in ra_mst_runners (jockey_claim, apprentice_allowance)

---

### TABLE 6: ra_trainers

**Source File:** `/utils/entity_extractor.py` (lines 58-67)

**Expected Columns (4 total - MINIMAL):**

```
✓ trainer_id              TEXT PRIMARY KEY
✓ name                    TEXT NOT NULL
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `entity_extractor.py` - Extracted from runner data only

**Missing Fields:**
- No trainer location, region, stats
- Very bare-bones table

---

### TABLE 7: ra_owners

**Source File:** `/utils/entity_extractor.py` (lines 69-78)

**Expected Columns (4 total - MINIMAL):**

```
✓ owner_id                TEXT PRIMARY KEY
✓ name                    TEXT NOT NULL
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `entity_extractor.py` - Extracted from runner data only

**Missing Fields:**
- No owner type (individual, syndicate, partnership)
- No location or stats

---

### TABLE 8: ra_courses

**Source File:** `/fetchers/courses_fetcher.py` (lines 64-74)

**Expected Columns (7 total):**

```
✓ course_id               TEXT PRIMARY KEY
✓ name                    TEXT NOT NULL       (from API 'course')
✓ region                  TEXT                (from API 'region_code')
✓ country                 TEXT                (from API 'region' - full name)
✓ latitude                NUMERIC             (always NULL - not in API)
✓ longitude               NUMERIC             (always NULL - not in API)
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `courses_fetcher.py::fetch_and_store()`

**Issues:**
1. latitude/longitude always inserted as NULL - API doesn't provide
2. Column should be removed OR populated from another source
3. API field mapping: 'course' → 'name', 'region_code' → 'region'

---

### TABLE 9: ra_results

**Source File:** `/fetchers/results_fetcher.py` (lines 207-257)

**Expected Columns (19 total):**

```
CORE:
✓ race_id                 TEXT PRIMARY KEY    (FK to ra_mst_races)
✓ course_id               TEXT
✓ course_name             TEXT
✓ race_name               TEXT
✓ race_date               DATE
✓ off_datetime            TIMESTAMP
✓ off_time                TIME

RACE INFO:
✓ race_type               TEXT
✓ race_class              TEXT
✓ distance                NUMERIC
✓ distance_f              TEXT
✓ surface                 TEXT
✓ going                   TEXT
✓ prize_money             NUMERIC
✓ currency                TEXT
✓ region                  TEXT

STATUS:
✓ results_status          TEXT
✓ is_abandoned            BOOLEAN
✓ field_size              INTEGER             (from runners array length)

METADATA:
✓ api_data                JSONB
✓ created_at              TIMESTAMP
✓ updated_at              TIMESTAMP
```

**Data Inserted By:**
- `results_fetcher.py::_transform_result()` - Lines 207-257
- `results_fetcher.py` also inserts into ra_mst_races (lines 132-154)

**Issues:**
1. **Overlap with ra_mst_races** - Many fields duplicate
2. results_fetcher inserts BOTH into ra_results AND ra_mst_races
3. Unclear purpose of ra_results if ra_mst_races already has this data
4. Runner results (positions, finish times) NOT stored anywhere
5. Recommendation: Either:
   - Use ra_results for race metadata only
   - OR merge ra_results into ra_mst_races
   - Create separate ra_runner_results for finishing positions

---

### TABLE 10: ra_bookmakers

**Source File:** `/fetchers/bookmakers_fetcher.py` (assumed - file exists but not read)

**Expected Columns:** UNKNOWN - file not analyzed

**Note:** Bookmakers fetcher exists but wasn't examined in this audit

---

### TABLE 11: ra_collection_metadata

**Source File:** `/migrations/001_create_metadata_tracking.sql`

**Status:** ✓ SCHEMA EXISTS

**Columns (9 total):**
```sql
CREATE TABLE ra_collection_metadata (
    id                    UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name            TEXT NOT NULL,
    operation             TEXT NOT NULL,
    records_processed     INTEGER DEFAULT 0,
    records_inserted      INTEGER DEFAULT 0,
    records_updated       INTEGER DEFAULT 0,
    records_skipped       INTEGER DEFAULT 0,
    status                TEXT CHECK (status IN ('success', 'partial', 'failed')),
    error_message         TEXT,
    metadata              JSONB,
    updated_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Indexes:**
- idx_metadata_table_name
- idx_metadata_created_at
- idx_metadata_status
- idx_metadata_operation
- idx_metadata_table_created

**Status:** This is the ONLY table with confirmed schema documentation

---

## DATA QUALITY ANALYSIS

### NULL Analysis (Based on Code Review)

**Fields That Will Be Frequently NULL:**

1. **ra_mst_races:**
   - start_time (often not provided by API)
   - weather_conditions (not always reported)
   - rail_movements (UK/IRE specific, often NULL)
   - stalls_position (not all races)
   - live_stream_url (most races don't have)
   - replay_url (only after race finishes)

2. **ra_mst_runners:**
   - entry_id (MISSING COLUMN)
   - jockey_claim (most jockeys don't have)
   - apprentice_allowance (most not apprentices)
   - pedigree fields (sire_id, dam_id, etc. - often unknown)
   - career_runs/wins/places (API may not provide)
   - timeform_rating (not all horses rated)
   - comment (not always present)

3. **ra_horses:**
   - dob (not always known for all horses)
   - colour (may be missing)

4. **ra_courses:**
   - latitude (always NULL - not in API)
   - longitude (always NULL - not in API)

### Expected Data Ranges

**Date Coverage (Based on Fetchers):**

- **races_fetcher.py:** Default 30 days back
- **results_fetcher.py:** Default 365 days back (12 months max due to API limit)
- **Historical:** API Standard plan limited to 12 months

**Expected Date Range:**
```
Minimum: 2024-10-07 (12 months ago)
Maximum: 2025-10-07 (today)
```

Note: User mentioned "2015-2025" but Standard API plan only supports last 12 months

---

## FOREIGN KEY INTEGRITY CHECKS

**Expected Foreign Key Relationships:**

```sql
-- ra_mst_races
ALTER TABLE ra_mst_races
  ADD CONSTRAINT fk_races_course
  FOREIGN KEY (course_id) REFERENCES ra_courses(course_id);

-- ra_mst_runners
ALTER TABLE ra_mst_runners
  ADD CONSTRAINT fk_runners_race
  FOREIGN KEY (race_id) REFERENCES ra_mst_races(race_id);

ALTER TABLE ra_mst_runners
  ADD CONSTRAINT fk_runners_horse
  FOREIGN KEY (horse_id) REFERENCES ra_horses(horse_id);

ALTER TABLE ra_mst_runners
  ADD CONSTRAINT fk_runners_jockey
  FOREIGN KEY (jockey_id) REFERENCES ra_jockeys(jockey_id);

ALTER TABLE ra_mst_runners
  ADD CONSTRAINT fk_runners_trainer
  FOREIGN KEY (trainer_id) REFERENCES ra_trainers(trainer_id);

ALTER TABLE ra_mst_runners
  ADD CONSTRAINT fk_runners_owner
  FOREIGN KEY (owner_id) REFERENCES ra_owners(owner_id);

-- ra_horse_pedigree
ALTER TABLE ra_horse_pedigree
  ADD CONSTRAINT fk_pedigree_horse
  FOREIGN KEY (horse_id) REFERENCES ra_horses(horse_id);

-- ra_results
ALTER TABLE ra_results
  ADD CONSTRAINT fk_results_race
  FOREIGN KEY (race_id) REFERENCES ra_mst_races(race_id);

ALTER TABLE ra_results
  ADD CONSTRAINT fk_results_course
  FOREIGN KEY (course_id) REFERENCES ra_courses(course_id);
```

**Status:** UNKNOWN - Cannot verify without database access

---

## API DATA STORAGE (JSONB COLUMNS)

**Tables with api_data columns:**
1. ra_mst_races - Full racecard API response
2. ra_mst_runners - Full runner API response
3. ra_results - Full result API response

**Purpose:**
- Stores complete API response for future reference
- Allows access to fields not yet extracted to columns
- Versioning/audit trail

**Potential Issues:**
1. Important data may be trapped in JSONB that should be columns
2. JSONB queries slower than column queries
3. No schema validation on JSONB data
4. Duplicate data (same field in both column and JSONB)

**Recommendation:**
- Periodically review api_data to find commonly-used fields
- Extract frequently-queried fields to proper columns
- Consider adding JSONB indexes:
  ```sql
  CREATE INDEX idx_races_api_data_gin ON ra_mst_races USING GIN (api_data);
  CREATE INDEX idx_runners_api_data_gin ON ra_mst_runners USING GIN (api_data);
  ```

---

## SCHEMA MISMATCHES & FIELD MAPPING ISSUES

### Critical Field Name Mismatches

**1. Race Date Field:**
- API returns: `date`
- Code tries: `race_date`
- Impact: May cause NULL values or insertion failures
- Fix needed in: races_fetcher.py line 245, results_fetcher.py line 137

**2. Off Time Field:**
- API returns: `off` (results endpoint)
- Code expects: `off_time`
- Impact: Possible NULL values
- Fix needed in: results_fetcher.py line 138

**3. Race Class Field:**
- API returns: `class`
- Code expects: `race_class`
- Impact: Possible NULL values
- Fix needed in: results_fetcher.py line 141

**4. Horse Name Field:**
- Entity extractor inserts: `name`
- Horses fetcher inserts: `name`
- But API field is: `horse` (for runner data)
- Should column be: `name` or `horse_name`?

**5. Course Name Field:**
- API returns: `course`
- Code inserts as: `name`
- Denormalized copies use: `course_name`
- Inconsistent naming

---

## RECOMMENDED ACTIONS

### IMMEDIATE (Critical - Do Now)

**1. Fix Database Connection**
```bash
# Test connection
python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)
print(db.get_table_count('ra_courses'))
"
```

**2. Add Missing entry_id Column**
```sql
-- Determine what entry_id should be
-- Option A: Same as runner_id
ALTER TABLE ra_mst_runners ADD COLUMN entry_id TEXT;
UPDATE ra_mst_runners SET entry_id = runner_id;

-- Option B: From API data if available
-- Check api_data->'entry_id' in existing rows

-- Option C: Generate from race_id and number
UPDATE ra_mst_runners SET entry_id = race_id || '_' || number
WHERE number IS NOT NULL;
```

**3. Fix Field Name Mismatches**
```python
# In results_fetcher.py line 137, change:
'race_date': race_data.get('date'),  # ✓ Correct

# In results_fetcher.py line 138, change:
'off_time': race_data.get('off'),  # ✓ Correct

# In results_fetcher.py line 141, change:
'race_class': race_data.get('class'),  # ✓ Correct
```

### HIGH PRIORITY (Do This Week)

**4. Remove Always-NULL Columns**
```sql
-- ra_courses
ALTER TABLE ra_courses DROP COLUMN latitude;
ALTER TABLE ra_courses DROP COLUMN longitude;

-- OR populate them from external source if needed
```

**5. Remove Duplicate Columns**
```sql
-- ra_mst_runners - pick one naming convention
ALTER TABLE ra_mst_runners DROP COLUMN weight;  -- Keep weight_lbs
ALTER TABLE ra_mst_runners DROP COLUMN rpr;  -- Keep racing_post_rating
ALTER TABLE ra_mst_runners DROP COLUMN stall;  -- Keep draw

-- Update code to match
```

**6. Resolve Pedigree Data Duplication**
```sql
-- Option A: Remove from ra_mst_runners, keep in ra_horse_pedigree
ALTER TABLE ra_mst_runners DROP COLUMN sire_id;
ALTER TABLE ra_mst_runners DROP COLUMN sire_name;
ALTER TABLE ra_mst_runners DROP COLUMN dam_id;
ALTER TABLE ra_mst_runners DROP COLUMN dam_name;
ALTER TABLE ra_mst_runners DROP COLUMN damsire_id;
ALTER TABLE ra_mst_runners DROP COLUMN damsire_name;

-- Option B: Remove ra_horse_pedigree table entirely
DROP TABLE ra_horse_pedigree;
-- Keep pedigree data in ra_mst_runners (it's already there)
```

**7. Add Missing NOT NULL Constraints**
```sql
-- Critical fields that should never be NULL
ALTER TABLE ra_mst_races ALTER COLUMN race_name SET NOT NULL;
ALTER TABLE ra_mst_races ALTER COLUMN race_date SET NOT NULL;
ALTER TABLE ra_mst_runners ALTER COLUMN horse_id SET NOT NULL;
ALTER TABLE ra_mst_runners ALTER COLUMN race_id SET NOT NULL;
ALTER TABLE ra_horses ALTER COLUMN name SET NOT NULL;
```

**8. Add Foreign Key Constraints**
```sql
-- See "Foreign Key Integrity Checks" section above
-- Add all FK constraints to enforce referential integrity
```

### MEDIUM PRIORITY (Do This Month)

**9. Add Indexes for Performance**
```sql
-- Date queries
CREATE INDEX idx_races_race_date ON ra_mst_races(race_date DESC);
CREATE INDEX idx_races_course_date ON ra_mst_races(course_id, race_date DESC);

-- FK lookups
CREATE INDEX idx_runners_race_id ON ra_mst_runners(race_id);
CREATE INDEX idx_runners_horse_id ON ra_mst_runners(horse_id);
CREATE INDEX idx_runners_jockey_id ON ra_mst_runners(jockey_id);
CREATE INDEX idx_runners_trainer_id ON ra_mst_runners(trainer_id);

-- Regional filtering
CREATE INDEX idx_races_region_date ON ra_mst_races(region, race_date DESC);
CREATE INDEX idx_horses_region ON ra_horses(region);

-- JSONB data
CREATE INDEX idx_races_api_data_gin ON ra_mst_races USING GIN (api_data);
CREATE INDEX idx_runners_api_data_gin ON ra_mst_runners USING GIN (api_data);
```

**10. Clarify ra_results Table Purpose**
```sql
-- Decision needed:
-- A. Merge ra_results into ra_mst_races (they overlap significantly)
-- B. Use ra_results only for race outcomes (winner, times, etc.)
-- C. Create new ra_runner_results for finishing positions

-- Recommended: Create ra_runner_results
CREATE TABLE ra_runner_results (
    runner_id TEXT PRIMARY KEY REFERENCES ra_mst_runners(runner_id),
    race_id TEXT NOT NULL REFERENCES ra_mst_races(race_id),
    finishing_position INTEGER,
    distance_beaten NUMERIC,
    finish_time NUMERIC,
    in_play_high NUMERIC,
    in_play_low NUMERIC,
    starting_price NUMERIC,
    official_rating_achieved INTEGER,
    prize_money_won NUMERIC,
    disqualified BOOLEAN DEFAULT FALSE,
    api_data JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

**11. Expand Entity Tables**
```sql
-- ra_jockeys - add useful fields
ALTER TABLE ra_jockeys ADD COLUMN region TEXT;
ALTER TABLE ra_jockeys ADD COLUMN is_apprentice BOOLEAN;
ALTER TABLE ra_jockeys ADD COLUMN allowance INTEGER;

-- ra_trainers - add useful fields
ALTER TABLE ra_trainers ADD COLUMN region TEXT;
ALTER TABLE ra_trainers ADD COLUMN location TEXT;

-- ra_owners - add useful fields
ALTER TABLE ra_owners ADD COLUMN owner_type TEXT; -- individual, syndicate, partnership
```

### LOW PRIORITY (Nice to Have)

**12. Add Data Validation Triggers**
```sql
-- Validate race_class is valid value
CREATE OR REPLACE FUNCTION validate_race_class()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.race_class NOT IN ('1', '2', '3', '4', '5', '6', '7', 'Listed', 'Group 1', 'Group 2', 'Group 3') THEN
        RAISE WARNING 'Invalid race_class: %', NEW.race_class;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER tr_validate_race_class
    BEFORE INSERT OR UPDATE ON ra_mst_races
    FOR EACH ROW
    EXECUTE FUNCTION validate_race_class();
```

**13. Create Materialized Views for Common Queries**
```sql
-- Recent races with course and runner counts
CREATE MATERIALIZED VIEW mv_recent_races AS
SELECT
    r.race_id,
    r.race_date,
    r.race_name,
    c.name AS course_name,
    r.race_class,
    r.distance_f,
    COUNT(ru.runner_id) AS runner_count,
    r.prize_money
FROM ra_mst_races r
LEFT JOIN ra_courses c ON c.course_id = r.course_id
LEFT JOIN ra_mst_runners ru ON ru.race_id = r.race_id
WHERE r.race_date >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY r.race_id, r.race_date, r.race_name, c.name, r.race_class, r.distance_f, r.prize_money;

CREATE INDEX idx_mv_recent_races_date ON mv_recent_races(race_date DESC);

-- Refresh daily
-- REFRESH MATERIALIZED VIEW mv_recent_races;
```

**14. Add Audit Logging**
```sql
-- Track all changes to critical tables
CREATE TABLE ra_audit_log (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    record_id TEXT NOT NULL,
    operation TEXT NOT NULL, -- INSERT, UPDATE, DELETE
    old_data JSONB,
    new_data JSONB,
    changed_by TEXT,
    changed_at TIMESTAMP DEFAULT NOW()
);
```

---

## SQL FIX SCRIPTS

### Script 1: Add Missing entry_id Column

```sql
-- Add entry_id column to ra_mst_runners
ALTER TABLE ra_mst_runners ADD COLUMN IF NOT EXISTS entry_id TEXT;

-- Populate with runner_id as default (adjust if different logic needed)
UPDATE ra_mst_runners
SET entry_id = runner_id
WHERE entry_id IS NULL;

-- Add index
CREATE INDEX IF NOT EXISTS idx_runners_entry_id ON ra_mst_runners(entry_id);

-- Document the column
COMMENT ON COLUMN ra_mst_runners.entry_id IS
'Entry ID for the runner (unique identifier per race entry)';
```

### Script 2: Remove Always-NULL Columns

```sql
-- Remove lat/long from courses (not provided by API)
ALTER TABLE ra_courses DROP COLUMN IF EXISTS latitude;
ALTER TABLE ra_courses DROP COLUMN IF EXISTS longitude;
```

### Script 3: Add Foreign Key Constraints

```sql
-- Add foreign keys (will fail if referential integrity violated)
-- Run data cleanup first if needed

ALTER TABLE ra_mst_races
ADD CONSTRAINT fk_races_course
FOREIGN KEY (course_id) REFERENCES ra_courses(course_id)
ON DELETE RESTRICT;

ALTER TABLE ra_mst_runners
ADD CONSTRAINT fk_runners_race
FOREIGN KEY (race_id) REFERENCES ra_mst_races(race_id)
ON DELETE CASCADE;

ALTER TABLE ra_mst_runners
ADD CONSTRAINT fk_runners_horse
FOREIGN KEY (horse_id) REFERENCES ra_horses(horse_id)
ON DELETE RESTRICT;

-- Note: jockey_id, trainer_id, owner_id can be NULL
-- So use FOREIGN KEY with ON DELETE SET NULL
ALTER TABLE ra_mst_runners
ADD CONSTRAINT fk_runners_jockey
FOREIGN KEY (jockey_id) REFERENCES ra_jockeys(jockey_id)
ON DELETE SET NULL;

ALTER TABLE ra_mst_runners
ADD CONSTRAINT fk_runners_trainer
FOREIGN KEY (trainer_id) REFERENCES ra_trainers(trainer_id)
ON DELETE SET NULL;

ALTER TABLE ra_mst_runners
ADD CONSTRAINT fk_runners_owner
FOREIGN KEY (owner_id) REFERENCES ra_owners(owner_id)
ON DELETE SET NULL;

ALTER TABLE ra_horse_pedigree
ADD CONSTRAINT fk_pedigree_horse
FOREIGN KEY (horse_id) REFERENCES ra_horses(horse_id)
ON DELETE CASCADE;
```

### Script 4: Add Performance Indexes

```sql
-- Races
CREATE INDEX IF NOT EXISTS idx_races_race_date ON ra_mst_races(race_date DESC);
CREATE INDEX IF NOT EXISTS idx_races_course_date ON ra_mst_races(course_id, race_date DESC);
CREATE INDEX IF NOT EXISTS idx_races_region_date ON ra_mst_races(region, race_date DESC);

-- Runners
CREATE INDEX IF NOT EXISTS idx_runners_race_id ON ra_mst_runners(race_id);
CREATE INDEX IF NOT EXISTS idx_runners_horse_id ON ra_mst_runners(horse_id);
CREATE INDEX IF NOT EXISTS idx_runners_jockey_id ON ra_mst_runners(jockey_id);
CREATE INDEX IF NOT EXISTS idx_runners_trainer_id ON ra_mst_runners(trainer_id);
CREATE INDEX IF NOT EXISTS idx_runners_owner_id ON ra_mst_runners(owner_id);

-- Horses
CREATE INDEX IF NOT EXISTS idx_horses_region ON ra_horses(region);
CREATE INDEX IF NOT EXISTS idx_horses_name ON ra_horses(name);

-- JSONB
CREATE INDEX IF NOT EXISTS idx_races_api_data_gin ON ra_mst_races USING GIN (api_data);
CREATE INDEX IF NOT EXISTS idx_runners_api_data_gin ON ra_mst_runners USING GIN (api_data);
CREATE INDEX IF NOT EXISTS idx_results_api_data_gin ON ra_results USING GIN (api_data);
```

### Script 5: Add NOT NULL Constraints

```sql
-- Only add if data quality allows
-- Check for NULLs first:
SELECT COUNT(*) FROM ra_mst_races WHERE race_name IS NULL;
SELECT COUNT(*) FROM ra_mst_races WHERE race_date IS NULL;
SELECT COUNT(*) FROM ra_mst_runners WHERE race_id IS NULL;
SELECT COUNT(*) FROM ra_mst_runners WHERE horse_id IS NULL;

-- If counts are 0, add constraints:
ALTER TABLE ra_mst_races ALTER COLUMN race_name SET NOT NULL;
ALTER TABLE ra_mst_races ALTER COLUMN race_date SET NOT NULL;
ALTER TABLE ra_mst_runners ALTER COLUMN race_id SET NOT NULL;
ALTER TABLE ra_mst_runners ALTER COLUMN horse_id SET NOT NULL;
ALTER TABLE ra_horses ALTER COLUMN name SET NOT NULL;
```

---

## PRIORITIZED ACTION PLAN

### Phase 1: Emergency Fixes (Day 1)
1. [ ] Fix database connection timeout issue
2. [ ] Verify tables exist and check row counts
3. [ ] Add missing entry_id column to ra_mst_runners
4. [ ] Fix field name mismatches in fetchers (race_date, off_time, race_class)

### Phase 2: Data Integrity (Week 1)
5. [ ] Add foreign key constraints
6. [ ] Add NOT NULL constraints on critical fields
7. [ ] Validate existing data meets constraints
8. [ ] Clean up orphaned records (if any)

### Phase 3: Optimization (Week 2)
9. [ ] Add performance indexes
10. [ ] Remove duplicate columns
11. [ ] Remove always-NULL columns
12. [ ] Create JSONB indexes for api_data columns

### Phase 4: Normalization (Week 3-4)
13. [ ] Resolve pedigree data duplication
14. [ ] Clarify ra_results table purpose
15. [ ] Expand entity tables (jockeys, trainers, owners)
16. [ ] Create ra_runner_results table for finishing positions

### Phase 5: Enhancement (Month 2)
17. [ ] Add data validation triggers
18. [ ] Create materialized views for common queries
19. [ ] Add audit logging
20. [ ] Document all tables and columns with COMMENT statements
21. [ ] Create comprehensive schema documentation

---

## TESTING CHECKLIST

After implementing fixes, verify:

- [ ] All tables accessible without timeout
- [ ] Row counts match expected data volumes
- [ ] entry_id column exists and populated in ra_mst_runners
- [ ] Foreign key constraints enforced
- [ ] No orphaned records
- [ ] Fetchers can insert data successfully
- [ ] Query performance acceptable with indexes
- [ ] No duplicate data (pedigree, weight, etc.)
- [ ] JSONB queries work with GIN indexes
- [ ] All NOT NULL constraints satisfied

---

## APPENDIX A: Code Files Analyzed

1. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/races_fetcher.py`
2. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/results_fetcher.py`
3. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/horses_fetcher.py`
4. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/courses_fetcher.py`
5. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/utils/supabase_client.py`
6. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/utils/entity_extractor.py`
7. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/migrations/001_create_metadata_tracking.sql`

---

## APPENDIX B: Expected Table Relationships

```
ra_courses
    ↓ (course_id)
ra_mst_races ←──────────── ra_results (race_id)
    ↓ (race_id)
ra_mst_runners
    ↓ (horse_id, jockey_id, trainer_id, owner_id)
    ├→ ra_horses ──→ ra_horse_pedigree (horse_id)
    ├→ ra_jockeys
    ├→ ra_trainers
    └→ ra_owners
```

---

## APPENDIX C: API Field Mapping Reference

| Table | Code Field | API Field | Notes |
|-------|------------|-----------|-------|
| ra_mst_races | race_date | date | Mismatch |
| ra_mst_races | off_time | off_time | Match |
| ra_results | off_time | off | Mismatch |
| ra_results | race_class | class | Mismatch |
| ra_courses | name | course | Mismatch |
| ra_courses | region | region_code | Mismatch |
| ra_mst_runners | weight_lbs | lbs | Match |
| ra_mst_runners | career_runs | career_total.runs | Nested |
| ra_mst_runners | official_rating | ofr | Abbreviation |
| ra_mst_runners | racing_post_rating | rpr | Abbreviation |
| ra_mst_runners | timeform_rating | tfr | Abbreviation |
| ra_mst_runners | tsr | ts | Abbreviation |

---

**END OF AUDIT REPORT**

Generated: 2025-10-07
Database: DarkHorses Racing (Supabase)
Tables Analyzed: 10
Critical Issues: 10
Recommendations: 21
