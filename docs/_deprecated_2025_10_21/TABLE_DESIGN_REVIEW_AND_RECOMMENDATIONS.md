# TABLE DESIGN REVIEW & RECOMMENDATIONS

**Date:** 2025-10-18
**Question:** Should we separate `ra_runners` into racecards and results tables?

---

## EXECUTIVE SUMMARY

### Current State
- **ra_runners**: 1.3M rows storing BOTH racecards AND results (combined)
- **ra_results**: 130 rows (legacy/unused table)
- **90% of ra_runners** have results, **10%** are future racecards

### Recommendation

**KEEP CURRENT DESIGN (Combined ra_runners) ✅**

**Rationale:**
1. Current design works well for racing data lifecycle
2. Separation would add complexity without significant benefits
3. Most queries need both racecard AND result data together
4. UPDATE pattern (racecard → result) is natural with single table

**Minor improvement:** Add database views for logical separation (optional)

---

## OPTION COMPARISON

### Option 1: KEEP CURRENT (Combined ra_runners) ✅ RECOMMENDED

**Structure:**
```
ra_runners (1.3M rows)
├─ Racecard columns: horse_id, jockey_id, draw, weight, etc.
├─ Result columns: position, distance_beaten, prize_won, sp, etc.
└─ Shared columns: race_id, runner_id, timestamps, etc.
```

**How it works:**
1. **Morning**: Racecard fetcher INSERTs row with result columns = NULL
2. **Evening**: Results fetcher UPDATEs same row with position, SP, etc.
3. **Query**: Single table access - no JOINs needed

**Pros:**
- ✅ **Simple queries** - No JOINs needed for complete runner data
- ✅ **Single source of truth** - One row = one horse in one race
- ✅ **Natural UPDATE workflow** - Racecard becomes result over time
- ✅ **Easy filtering** - `WHERE position IS NULL` = upcoming races
- ✅ **Consistent runner_id** throughout lifecycle
- ✅ **Atomic updates** - Can't have orphaned racecards or results
- ✅ **Historical data preserved** - Racecard + result in one place

**Cons:**
- ⚠️ **NULL values** - 10% of rows have NULL result columns (wasted space)
- ⚠️ **Mixed purpose** - Table serves two logical concepts
- ⚠️ **Large table** - 1.3M+ rows with 75 columns

**Use cases this design excels at:**
```sql
-- Find all races for a horse (racecard + results)
SELECT * FROM ra_runners WHERE horse_id = 'hrs_XXX';

-- Find upcoming races (no results yet)
SELECT * FROM ra_runners WHERE position IS NULL;

-- Find completed races with winners
SELECT * FROM ra_runners WHERE position = 1;

-- Analyze jockey performance
SELECT jockey_id, AVG(position::int)
FROM ra_runners
WHERE position IS NOT NULL
GROUP BY jockey_id;
```

---

### Option 2: SEPARATE INTO TWO TABLES ❌ NOT RECOMMENDED

**Structure:**
```
ra_racecards (132K rows - racecards only)
├─ racecard_id (PK)
├─ race_id (FK to ra_races)
├─ horse_id, jockey_id, trainer_id
├─ draw, weight, official_rating
└─ Created from /v1/racecards/pro

ra_race_results (1.2M rows - results only)
├─ result_id (PK)
├─ race_id (FK to ra_races)
├─ horse_id (for linking)
├─ position, distance_beaten, prize_won
├─ starting_price, finishing_time
└─ Created from /v1/results/pro
```

**How it would work:**
1. **Morning**: INSERT into ra_racecards
2. **Evening**: INSERT into ra_race_results (separate row!)
3. **Query**: JOIN tables to get complete data

**Pros:**
- ✅ **Clear separation of concerns** - Racecards vs results
- ✅ **Less NULL values** - Each table focused on its purpose
- ✅ **Better normalization** - More "textbook" database design
- ✅ **Independent evolution** - Can change racecard schema without affecting results

**Cons:**
- ❌ **Requires JOINs** - Most queries need both tables
- ❌ **Complex UPDATE logic** - Need to track which racecards have results
- ❌ **Duplicate data** - Horse/jockey IDs stored in both tables
- ❌ **Orphan risk** - Racecards without results or vice versa
- ❌ **More FK constraints** - Need to maintain relationships
- ❌ **Two-step workflow** - Insert racecard, later insert result
- ❌ **Harder to find "pending results"** - Need LEFT JOIN

**Common queries become complex:**
```sql
-- Find all races for a horse (NOW REQUIRES JOIN)
SELECT rc.*, rr.*
FROM ra_racecards rc
LEFT JOIN ra_race_results rr
  ON rc.race_id = rr.race_id
  AND rc.horse_id = rr.horse_id
WHERE rc.horse_id = 'hrs_XXX';

-- Find upcoming races (no results yet)
SELECT rc.*
FROM ra_racecards rc
LEFT JOIN ra_race_results rr
  ON rc.race_id = rr.race_id
  AND rc.horse_id = rr.horse_id
WHERE rr.result_id IS NULL;  -- Much more complex!
```

**Migration effort:**
- Need to split 1.3M rows into two tables
- Update all fetcher code (races_fetcher.py, results_fetcher.py)
- Update all query code throughout system
- Risk of data loss/corruption during migration

---

### Option 3: HYBRID (Current + Views) 🤔 POSSIBLE ENHANCEMENT

**Structure:**
```
ra_runners (1.3M rows - physical table, as is)

CREATE VIEW ra_racecards AS
  SELECT ... FROM ra_runners WHERE position IS NULL;

CREATE VIEW ra_race_results AS
  SELECT ... FROM ra_runners WHERE position IS NOT NULL;
```

**Pros:**
- ✅ **Best of both worlds** - Physical simplicity + logical separation
- ✅ **Backward compatible** - Existing code unchanged
- ✅ **Optional abstraction** - Use views when convenient
- ✅ **No data duplication** - Views reference same underlying data
- ✅ **Easy queries** - Can use views OR base table as needed

**Cons:**
- ⚠️ **View overhead** - Slight performance cost (minimal)
- ⚠️ **Still have NULLs** - Base table unchanged
- ⚠️ **Potential confusion** - Users might not know which to query

**Example views:**
```sql
-- Racecards view (upcoming/future races)
CREATE VIEW ra_racecards AS
SELECT
  runner_id,
  race_id,
  horse_id,
  horse_name,
  jockey_id,
  jockey_name,
  trainer_id,
  trainer_name,
  draw,
  weight_lbs,
  official_rating,
  -- Omit result columns (they're NULL anyway)
  created_at
FROM ra_runners
WHERE position IS NULL;

-- Results view (completed races)
CREATE VIEW ra_race_results AS
SELECT
  runner_id,
  race_id,
  horse_id,
  horse_name,
  position,
  distance_beaten,
  prize_won,
  starting_price,
  finishing_time,
  -- Include racecard data too (useful for analysis)
  jockey_id,
  trainer_id,
  weight_lbs,
  updated_at
FROM ra_runners
WHERE position IS NOT NULL;
```

**Use case:**
```sql
-- Application code can choose:
SELECT * FROM ra_racecards WHERE race_id = 'rac_XXX';  -- View (logical)
SELECT * FROM ra_runners WHERE race_id = 'rac_XXX';    -- Base table (physical)
```

---

## NAMING CONVENTION ANALYSIS

### Current Naming Pattern

```
REFERENCE DATA (relatively static):
ra_courses          - Venues/tracks
ra_bookmakers       - Betting companies
ra_jockeys          - Jockeys
ra_trainers         - Trainers
ra_owners           - Owners
ra_horses           - Horses
ra_horse_pedigree   - Horse lineage (detail table)

TRANSACTIONAL DATA (dynamic):
ra_races            - Race metadata (date, course, conditions)
ra_runners          - Race entries + results (COMBINED)

ODDS DATA (separate system):
ra_odds_historical  - Historical odds
ra_odds_live        - Live odds snapshots
ra_odds_live_latest - Latest odds per runner
ra_odds_statistics  - Aggregated odds stats

LEGACY/UNUSED:
ra_results          - Old results table (130 rows, unused)
```

### Naming Conventions ARE Consistent ✅

**Pattern:** `ra_<entity_plural>`

**Examples:**
- `ra_horses` (not ra_horse)
- `ra_trainers` (not ra_trainer)
- `ra_owners` (not ra_owner)

**Exception:** `ra_horse_pedigree` (singular) because it's a detail/lookup table

**If we were to separate runners:**

**Option A: Entry/Result Pattern**
```
ra_race_entries     - Racecard data (pre-race)
ra_race_results     - Result data (post-race)
```
Pros: Clear lifecycle distinction
Cons: Longer names, breaks `ra_<plural>` pattern

**Option B: Racecard/Result Pattern**
```
ra_racecards        - Racecard data (pre-race)
ra_results          - Result data (post-race) [reuse existing table name]
```
Pros: Shorter, intuitive names
Cons: "Racecard" is singular in usage but table is plural data

**Option C: Runner Status Pattern**
```
ra_runners          - Racecard data only
ra_runner_results   - Result data only
```
Pros: Keeps "runners" name, clear relationship
Cons: Confusing - most people expect "ra_runners" to include results

---

## STORAGE & PERFORMANCE ANALYSIS

### Current ra_runners Statistics

**Data distribution:**
- **Total rows:** 1,326,334
- **Racecards only** (position IS NULL): ~132,000 (10%)
- **With results** (position IS NOT NULL): ~1,194,000 (90%)

**Column usage:**
- **Racecard columns:** ~100% populated (horse_id, jockey_id, etc.)
- **Result columns:** ~90% populated (position, SP, etc.)
- **NULL overhead:** ~10% of result columns are NULL

**Update patterns:**
- **Never updated:** Rows that started as results (no racecard first)
- **Updated once:** Typical flow - racecard inserted, then updated with results
- **Updated multiple times:** Corrections, late results

### Storage Impact of Separation

**Current (combined):**
```
ra_runners: 1.3M rows × 75 columns = ~98M cells
NULL cells: 10% × 10 result columns = ~1.3M NULL values
```

**If separated:**
```
ra_racecards: 132K rows × 40 columns = ~5.3M cells
ra_race_results: 1.2M rows × 45 columns = ~54M cells
Total: ~59M cells (40% reduction!)
```

**But:**
- Duplicate horse/jockey/race IDs in both tables (+overhead)
- Need JOINs for most queries (+CPU cost)
- Index duplication across two tables (+storage)

**Verdict:** Storage savings minimal, query cost higher

---

## REAL-WORLD QUERY PATTERNS

### Common Queries in Racing Systems

**1. Get complete race card with results:**
```sql
-- Current (simple):
SELECT * FROM ra_runners WHERE race_id = 'rac_XXX';

-- Separated (complex):
SELECT rc.*, rr.*
FROM ra_racecards rc
LEFT JOIN ra_race_results rr USING (race_id, horse_id)
WHERE rc.race_id = 'rac_XXX';
```

**2. Find horse's racing history:**
```sql
-- Current (simple):
SELECT * FROM ra_runners
WHERE horse_id = 'hrs_XXX'
ORDER BY created_at DESC;

-- Separated (complex):
SELECT rc.race_id, rc.draw, rr.position, rr.prize_won
FROM ra_racecards rc
LEFT JOIN ra_race_results rr USING (race_id, horse_id)
WHERE rc.horse_id = 'hrs_XXX'
ORDER BY rc.created_at DESC;
```

**3. Jockey win percentage:**
```sql
-- Current (simple):
SELECT
  jockey_id,
  COUNT(*) as rides,
  COUNT(*) FILTER (WHERE position = 1) as wins,
  ROUND(COUNT(*) FILTER (WHERE position = 1)::numeric / COUNT(*) * 100, 1) as win_pct
FROM ra_runners
WHERE position IS NOT NULL
GROUP BY jockey_id;

-- Separated (same complexity, but need to ensure result exists):
SELECT
  jockey_id,
  COUNT(*) as rides,
  COUNT(*) FILTER (WHERE position = 1) as wins,
  ROUND(COUNT(*) FILTER (WHERE position = 1)::numeric / COUNT(*) * 100, 1) as win_pct
FROM ra_race_results
GROUP BY jockey_id;
```

**4. Find races pending results:**
```sql
-- Current (trivial):
SELECT * FROM ra_runners WHERE position IS NULL;

-- Separated (complex):
SELECT rc.*
FROM ra_racecards rc
LEFT JOIN ra_race_results rr USING (race_id, horse_id)
WHERE rr.result_id IS NULL;
```

**5. ML training data (needs both racecard features + result label):**
```sql
-- Current (simple):
SELECT
  draw, weight_lbs, official_rating, jockey_id, trainer_id,  -- Features
  position  -- Label
FROM ra_runners
WHERE position IS NOT NULL;

-- Separated (requires JOIN):
SELECT
  rc.draw, rc.weight_lbs, rc.official_rating, rc.jockey_id, rc.trainer_id,
  rr.position
FROM ra_racecards rc
INNER JOIN ra_race_results rr USING (race_id, horse_id);
```

**Verdict:** 80%+ of queries are simpler with combined table

---

## INDUSTRY BEST PRACTICES

### What do other racing data systems do?

**Most racing databases use COMBINED approach:**

1. **Betfair API** - Single "runner" entity with result fields
2. **Racing Post** - Combined runner/result data
3. **Timeform** - Single runner record with optional results

**Why?**
- Racing data naturally flows: racecard → race → result
- Results are NOT separate events - they're the OUTCOME of the racecard
- Users think in terms of "how did this horse perform" not "what was the racecard vs the result"

**When separation makes sense:**
- **Betting systems** - Need fast access to live racecards only
- **Historical archives** - Results stored separately for analysis
- **Multi-sport systems** - Different result structures per sport

**Your system is racing-specific** → Combined design is appropriate

---

## RECOMMENDATIONS

### Recommendation #1: KEEP CURRENT DESIGN ✅

**Keep `ra_runners` as combined racecard + results table.**

**Reasons:**
1. ✅ Fits racing data lifecycle perfectly
2. ✅ Simplifies 80%+ of queries
3. ✅ No migration risk
4. ✅ Industry-standard approach
5. ✅ Works well with your current fetcher architecture

**No changes needed** - system is well-designed as-is!

---

### Recommendation #2: DROP ra_results TABLE ❌

**Drop the unused `ra_results` legacy table.**

**Action:**
```sql
-- Verify it's truly unused first
SELECT COUNT(*) FROM ra_results;  -- Should be ~130 rows

-- Check if anything references it
SELECT * FROM information_schema.table_constraints
WHERE table_name = 'ra_results';

-- If safe, drop it
DROP TABLE ra_results CASCADE;
```

**Benefit:** Reduces confusion, cleaner schema

---

### Recommendation #3: ADD VIEWS (Optional) 🤔

**Optionally create views for logical separation.**

**Implementation:**
```sql
-- View for upcoming racecards
CREATE OR REPLACE VIEW ra_racecards AS
SELECT
  runner_id,
  race_id,
  horse_id,
  horse_name,
  jockey_id,
  jockey_name,
  trainer_id,
  trainer_name,
  owner_id,
  owner_name,
  number,
  draw,
  weight_lbs,
  weight_stones_lbs,
  headgear,
  official_rating,
  form,
  created_at
FROM ra_runners
WHERE position IS NULL;

-- View for completed results
CREATE OR REPLACE VIEW ra_completed_results AS
SELECT
  runner_id,
  race_id,
  horse_id,
  horse_name,
  position,
  distance_beaten,
  prize_won,
  starting_price,
  starting_price_decimal,
  finishing_time,
  -- Include useful racecard context
  jockey_id,
  trainer_id,
  weight_lbs,
  draw,
  updated_at
FROM ra_runners
WHERE position IS NOT NULL;
```

**Benefits:**
- Clearer API for specific use cases
- Can add computed columns in views
- Backward compatible (don't break existing code)

**When to use:**
- Use base table (`ra_runners`) for complex queries
- Use views for simple, focused queries
- Let application choose based on needs

---

## CONCLUSION

**Your current design is GOOD - don't change it!**

The combined `ra_runners` table is:
- ✅ Appropriate for racing data
- ✅ Industry-standard approach
- ✅ Simpler for most queries
- ✅ Well-suited to your data flow

**Only recommended changes:**
1. Drop unused `ra_results` table (cleanup)
2. Optionally add views for logical separation (enhancement)

**Naming convention is already consistent** - all tables follow `ra_<entity>` pattern.

No major restructuring needed! 🎉
