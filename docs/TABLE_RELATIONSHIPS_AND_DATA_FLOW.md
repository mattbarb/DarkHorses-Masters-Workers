# TABLE RELATIONSHIPS & DATA FLOW

**Date:** 2025-10-18
**System:** DarkHorses Masters/Workers

---

## EXECUTIVE SUMMARY

### How The System Works

**The system stores ALL race data in `ra_runners` - NOT in separate racecard and results tables.**

Key Points:
1. **ra_runners is BOTH racecards AND results combined** - 1.3M+ rows
2. **ra_results table exists but is LEGACY/UNUSED** - only 130 rows
3. **Results update existing ra_runners rows** via UPSERT (don't create new rows)
4. **No foreign key constraints** on most tables (convention-based relationships)
5. **Same-day multiple races** - horses CAN run twice same day (rare but happens)

---

## DATABASE TABLES

### Current Table Inventory

| Table | Rows | Purpose | Status |
|-------|------|---------|--------|
| **ra_runners** | 1,326,334 | **MAIN TABLE:** Race entries + results | ✅ ACTIVE |
| **ra_races** | 136,932 | Race metadata (date, course, conditions) | ✅ ACTIVE |
| **ra_horses** | 111,652 | Horse reference data | ✅ ACTIVE |
| **ra_horse_pedigree** | 111,578 | Horse lineage (sire/dam/damsire) | ✅ ACTIVE |
| **ra_jockeys** | 3,482 | Jockey reference data | ✅ ACTIVE |
| **ra_trainers** | 2,781 | Trainer reference data | ✅ ACTIVE |
| **ra_owners** | 48,161 | Owner reference data | ✅ ACTIVE |
| **ra_courses** | 101 | Course/venue reference data | ✅ ACTIVE |
| **ra_bookmakers** | 19 | Bookmaker reference data | ✅ ACTIVE |
| **ra_odds_historical** | 2,434,014 | Historical odds data | ✅ ACTIVE (Odds Worker) |
| **ra_odds_live** | 176,020 | Live odds snapshots | ✅ ACTIVE (Odds Worker) |
| **ra_odds_live_latest** | 176,020 | Latest odds per runner | ✅ ACTIVE (Odds Worker) |
| **ra_odds_statistics** | 5,868 | Aggregated odds stats | ✅ ACTIVE (Odds Worker) |
| **ra_results** | 130 | **LEGACY - Not used** | ⚠️ DEPRECATED |
| **ra_collection_metadata** | 1 | System metadata | ✅ ACTIVE |

---

## TABLE RELATIONSHIPS

### Foreign Key Constraints (3 defined)

```
ra_runners.race_id        → ra_races.race_id       ✅ FK constraint
ra_results.race_id        → ra_races.race_id       ✅ FK constraint (unused table)
ra_horse_pedigree.horse_id → ra_horses.horse_id    ✅ FK constraint
```

### Convention-Based Relationships (No FK constraints)

```
ra_runners.horse_id       → ra_horses.horse_id     (by convention)
ra_runners.jockey_id      → ra_jockeys.jockey_id   (by convention)
ra_runners.trainer_id     → ra_trainers.trainer_id (by convention)
ra_runners.owner_id       → ra_owners.owner_id     (by convention)
ra_runners.sire_id        → ra_horses.horse_id     (by convention)
ra_runners.dam_id         → ra_horses.horse_id     (by convention)
ra_runners.damsire_id     → ra_horses.horse_id     (by convention)
ra_races.course_id        → ra_courses.course_id   (by convention)
```

**Why no FK constraints?**
- Allows data insertion even if referenced entities don't exist yet
- Application code ensures data consistency
- More flexible for API data that might be incomplete

---

## DATA FLOW: HOW RACECARDS & RESULTS WORK

### Scenario: Horse Runs in Race at 1pm, Wins, Runs Again at 2pm

**Question:** How does the system update the win from the previous race?

**Answer:** It doesn't work that way! Here's how it actually works:

### Step 1: Racecard Fetched (Before Race)

**Source:** `/v1/racecards/pro` API endpoint
**Fetcher:** `fetchers/races_fetcher.py`
**When:** Daily fetch (typically morning for that day's races)

**What happens:**
1. Creates race record in `ra_races` (race metadata)
2. Creates runner records in `ra_runners` (one per horse)
3. Runner record includes:
   - `position`: NULL (no result yet)
   - `distance_beaten`: NULL
   - `prize_won`: NULL
   - `starting_price`: NULL (populated later)
   - All horse/jockey/trainer data populated

**Example runner row created:**
```sql
INSERT INTO ra_runners (
  runner_id,
  race_id,
  horse_id,
  horse_name,
  position,      -- NULL (no result)
  ...
) VALUES (
  'rac_11745682_hrs_30455194',
  'rac_11745682',
  'hrs_30455194',
  'Create (IRE)',
  NULL,          -- No position yet
  ...
);
```

### Step 2: Results Fetched (After Race)

**Source:** `/v1/results/pro` API endpoint
**Fetcher:** `fetchers/results_fetcher.py`
**When:** Daily fetch (evening after races complete)

**What happens:**
1. **UPDATES** same race record in `ra_races` (adds result metadata)
2. **UPDATES** existing runner records in `ra_runners` via UPSERT
3. UPSERT logic:
   - Uses `runner_id` as unique key (`race_id` + `horse_id`)
   - If row exists: **UPDATE** it with result data
   - If row doesn't exist: **INSERT** new row (rare - means racecard wasn't fetched)

**Example UPSERT:**
```sql
INSERT INTO ra_runners (
  runner_id,
  race_id,
  horse_id,
  position,           -- NOW POPULATED
  distance_beaten,    -- NOW POPULATED
  prize_won,          -- NOW POPULATED
  starting_price,     -- NOW POPULATED
  ...
) VALUES (
  'rac_11745682_hrs_30455194',
  'rac_11745682',
  'hrs_30455194',
  1,                  -- Won!
  '0',                -- Winner - 0 beaten distance
  2983.38,            -- Prize money
  '5/1',              -- SP at off
  ...
)
ON CONFLICT (runner_id) DO UPDATE SET
  position = EXCLUDED.position,
  distance_beaten = EXCLUDED.distance_beaten,
  prize_won = EXCLUDED.prize_won,
  starting_price = EXCLUDED.starting_price,
  updated_at = NOW();
```

### Step 3: Same Horse Runs Again at 2pm

**Important:** Each race creates a SEPARATE runner row!

**1pm Race:**
```sql
runner_id: 'rac_11745682_hrs_30455194'  -- Race 1 + Horse ID
race_id:   'rac_11745682'                -- 1pm race
horse_id:  'hrs_30455194'
position:  1                             -- Won!
```

**2pm Race:**
```sql
runner_id: 'rac_11745999_hrs_30455194'  -- Race 2 + Horse ID (DIFFERENT runner_id)
race_id:   'rac_11745999'                -- 2pm race (DIFFERENT race_id)
horse_id:  'hrs_30455194'                -- SAME horse
position:  NULL → (later updated to 3)   -- 3rd place
```

**Key Point:** The `runner_id` is a composite of `race_id` + `horse_id`, so:
- Same horse in different races = **DIFFERENT runner rows**
- Same horse in same race = **SAME runner row** (updated)

### Career Stats Update: How Does Horse Know About Previous Win?

**Answer:** Career stats are stored in `ra_horses`, NOT calculated from `ra_runners`.

**Option 1: API Provides Career Stats (Current Implementation)**

The Racing API includes career stats in each runner record:
```json
{
  "horse_id": "hrs_30455194",
  "career_total": {
    "runs": 15,
    "wins": 3,    // After the 1pm win, API shows 3 wins
    "places": 7
  }
}
```

These are stored in `ra_runners.career_*` fields and updated with each fetch.

**Option 2: Calculate from ra_runners (Not Currently Implemented)**

You COULD calculate career stats by querying ra_runners:
```sql
SELECT
  horse_id,
  COUNT(*) as career_runs,
  COUNT(*) FILTER (WHERE position = 1) as career_wins,
  COUNT(*) FILTER (WHERE position <= 3) as career_places
FROM ra_runners
WHERE horse_id = 'hrs_30455194'
  AND position IS NOT NULL  -- Only count races with results
GROUP BY horse_id;
```

But the system currently uses API-provided stats (they're more reliable).

---

## DATA POPULATION STATISTICS

### ra_runners Current State (1,326,334 runners)

| Field | Populated | Percentage | Meaning |
|-------|-----------|------------|---------|
| Total runners | 1,326,334 | 100.0% | All entries (racecards + results) |
| With position | 1,194,682 | 90.1% | **Completed races with results** |
| With distance beaten | 1,271,670 | 95.9% | Result detail |
| With prize won | 532,593 | 40.2% | Only prize winners |
| With starting price | 1,271,653 | 95.9% | Result races (SP known) |
| With finishing time | 145,023 | 10.9% | Recent data only |

**Interpretation:**
- ~90% of runners have results (completed races)
- ~10% are future racecards or non-runners
- Prize only recorded for winners/placed horses
- Finishing times only in recent data (new field)

---

## SAME-DAY MULTIPLE RACES

### Analysis

Horses CAN run multiple races same day (rare but legitimate):

**Example: Zafaan on 2025-10-17**
- 3:15pm race: No result (non-runner?)
- 4:40pm race: Finished 2nd

**Creates TWO runner rows:**
```sql
runner_id: 'rac_XXXXX_hrs_zafaan'  -- 3:15pm race
runner_id: 'rac_YYYYY_hrs_zafaan'  -- 4:40pm race (DIFFERENT row)
```

**How System Handles:**
- Each race = separate row in ra_runners
- No conflicts because runner_id is unique (race_id + horse_id)
- Query by horse_id to see all races for that horse that day

**Query Example:**
```sql
SELECT
  r.race_date,
  r.off_time,
  run.position,
  run.prize_won
FROM ra_runners run
JOIN ra_races r ON run.race_id = r.race_id
WHERE run.horse_id = 'hrs_zafaan'
  AND r.race_date = '2025-10-17'
ORDER BY r.off_time;
```

---

## RA_RESULTS TABLE - LEGACY/UNUSED

### Status: DEPRECATED ⚠️

**What is it?**
- Old separate results table (only 130 rows)
- Has FK constraint to ra_races
- NOT actively used by fetchers

**Why exists?**
- Probably early design before switching to combined ra_runners approach
- Kept for historical reasons

**Should we drop it?**
- **Recommendation:** YES - it's confusing and unused
- Check if any external systems reference it first
- Migrate those 130 rows to ra_runners if needed

---

## TIMING & UPDATES

### Update Schedule

**Racecards (fetchers/races_fetcher.py):**
- Fetches daily for upcoming races
- Creates ra_races + ra_runners rows
- All result fields are NULL initially

**Results (fetchers/results_fetcher.py):**
- Fetches daily for completed races
- **UPDATES** existing ra_runners rows via UPSERT
- Adds position, SP, distance beaten, prize, etc.

### Data Freshness

Based on recent data (last 2 days):
- **Earliest result update:** 2025-10-17 12:04:29
- **Latest result update:** 2025-10-18 05:31:00
- **Days with updates:** 2 (ongoing daily updates)

**Recent Races (2025-10-18):**
- All today's races show `0/X` results (races haven't run yet)
- Racecards were added 05:15:16 (this morning)
- Results will be populated after races complete

---

## CROSS-REFERENCING EXAMPLE

### Query: "Show me all races for horse 'Create (IRE)' with results"

```sql
SELECT
  r.race_date,
  r.course_name,
  r.race_name,
  r.off_time,
  run.number,
  run.draw,
  run.position,
  run.distance_beaten,
  run.starting_price,
  run.prize_won,
  j.jockey_name,
  t.trainer_name
FROM ra_runners run
JOIN ra_races r ON run.race_id = r.race_id
LEFT JOIN ra_jockeys j ON run.jockey_id = j.jockey_id
LEFT JOIN ra_trainers t ON run.trainer_id = t.trainer_id
WHERE run.horse_id = 'hrs_30455194'  -- Create (IRE)
  AND run.position IS NOT NULL       -- Only races with results
ORDER BY r.race_date DESC, r.off_time DESC
LIMIT 20;
```

**Returns:**
- All completed races for this horse
- Cross-references jockey and trainer names
- Ordered by most recent first

---

## ENTITY EXTRACTION FLOW

### When Fetching Racecards/Results

**Process:**
1. Fetch race data from API
2. Extract runner data (includes IDs for jockey, trainer, owner, horse)
3. **EntityExtractor** (`utils/entity_extractor.py`):
   - Checks if entities exist in reference tables
   - For NEW horses: Enriches with `/v1/horses/{id}/pro` endpoint
   - Inserts/updates reference tables:
     - ra_jockeys
     - ra_trainers
     - ra_owners
     - ra_horses
     - ra_horse_pedigree
4. Insert/update ra_runners

**Key Insight:**
- Reference tables populated FROM ra_runners data
- Entity IDs link to reference tables (convention-based)
- Enrichment only for new horses (saves API calls)

---

## SUMMARY: ANSWERING YOUR QUESTION

### "How does the system track a horse's previous win when it runs again?"

**Answer:**

1. **Each race creates a SEPARATE row** in ra_runners
   - 1pm race win = one row (runner_id: race1_horse)
   - 2pm race = different row (runner_id: race2_horse)

2. **Career stats come from the API**, not calculated
   - API provides cumulative wins/runs/places
   - Stored in ra_runners.career_* fields
   - Updated each time horse fetched

3. **To find horse's previous races:**
   ```sql
   SELECT * FROM ra_runners
   WHERE horse_id = 'hrs_XXX'
   ORDER BY created_at DESC;
   ```

4. **Results UPDATE existing rows**, don't create new ones
   - Racecard fetch: Creates row with position=NULL
   - Results fetch: UPDATEs same row with position=1 (won)
   - Same runner_id (race_id + horse_id) ensures single row per race

5. **No automatic "previous race" field**
   - System doesn't store "last race result" in horse table
   - Must query ra_runners to find previous runs
   - Could add computed field if needed:
     ```sql
     -- Find horse's last race before this one
     SELECT position, race_date
     FROM ra_runners run
     JOIN ra_races r ON run.race_id = r.race_id
     WHERE run.horse_id = 'hrs_XXX'
       AND r.race_date < '2025-10-18'
     ORDER BY r.race_date DESC
     LIMIT 1;
     ```

---

## RECOMMENDATIONS

### 1. Drop ra_results Table ❌

**Reason:** Unused, confusing, only 130 rows

**Action:**
```sql
DROP TABLE ra_results CASCADE;
```

### 2. Add Missing FK Constraints? 🤔

**Pros:**
- Enforces referential integrity
- Prevents orphaned records

**Cons:**
- Might break if API provides IDs for entities we don't have
- More rigid - harder to backfill

**Recommendation:** Keep current approach (convention-based) but consider adding constraints later

### 3. Add Computed Previous Race Fields? 🤔

**Could add to ra_horses:**
- `last_race_date` - Most recent race
- `last_race_position` - How they finished
- `last_race_days_ago` - Recency

**Pros:**
- Faster queries (no JOIN needed)
- Easier for ML models

**Cons:**
- Needs maintenance (trigger or periodic update)
- Adds complexity

**Recommendation:** Add if needed for performance, otherwise query on demand

---

## CONCLUSION

The system uses a **single table (ra_runners) for both racecards AND results**, updating rows via UPSERT when results come in. Each race creates a separate row, even for the same horse on the same day. Career stats come from the API, not internal calculation. The ra_results table exists but is unused/deprecated.

**Key Takeaway:** Think of ra_runners as an event log where each row = "one horse in one race" - the position field determines if it's a completed race (not NULL) or upcoming racecard (NULL).
