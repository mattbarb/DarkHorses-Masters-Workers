# LINEAGE/PEDIGREE SYSTEM DESIGN PROPOSAL

**Date:** 2025-10-18
**Goal:** Create comprehensive lineage tracking linked to runner_id

---

## CURRENT STATE

### Existing Pedigree Data

**ra_horse_pedigree (111,578 records):**
```
horse_id (PK)
sire_id
sire (name)
dam_id
dam (name)
damsire_id
damsire (name)
breeder
region
created_at, updated_at
```

**ra_runners pedigree columns:**
```
sire_id
sire_name
sire_region
dam_id
dam_name
dam_region
damsire_id
damsire_name
damsire_region
breeder
```

**Key observations:**
1. ✅ **ra_horse_pedigree** stores lineage data per HORSE (3 generations: horse → sire/dam → damsire)
2. ✅ **ra_runners** also stores same pedigree data (denormalized for convenience)
3. ⚠️  **Both tables** have similar data (duplication)
4. ⚠️  **Limited depth** - only 3 generations currently
5. ⚠️  **No link to runner_id** - ra_horse_pedigree links via horse_id only

---

## PROPOSAL: Enhanced Lineage System

### Option 1: ra_lineage Table (Recommended) ✅

**Create new table linked to runner_id with unlimited generations:**

```sql
CREATE TABLE ra_lineage (
    lineage_id VARCHAR PRIMARY KEY,  -- Generated: runner_id_generation_type
    runner_id VARCHAR NOT NULL,       -- FK to ra_runners
    horse_id VARCHAR NOT NULL,        -- The horse in this race

    -- Lineage details
    generation INT NOT NULL,          -- 1=parent, 2=grandparent, 3=great-grand, etc.
    lineage_path VARCHAR NOT NULL,    -- 'sire' | 'dam' | 'sire.sire' | 'sire.dam' | 'dam.sire' | 'dam.dam', etc.
    relation_type VARCHAR NOT NULL,   -- 'sire' | 'dam' | 'grandsire_paternal' | 'granddam_paternal' | 'grandsire_maternal' | 'granddam_maternal', etc.

    -- Ancestor details
    ancestor_horse_id VARCHAR,        -- ID of the ancestor horse (can link to ra_horses)
    ancestor_name VARCHAR,            -- Name (e.g., "Galileo (IRE)")
    ancestor_region VARCHAR,          -- Breeding region
    ancestor_dob DATE,                -- Date of birth if known

    -- Metadata
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),

    FOREIGN KEY (runner_id) REFERENCES ra_runners(runner_id),
    UNIQUE (runner_id, lineage_path)  -- One record per ancestor per runner
);

CREATE INDEX idx_lineage_runner_id ON ra_lineage(runner_id);
CREATE INDEX idx_lineage_horse_id ON ra_lineage(horse_id);
CREATE INDEX idx_lineage_ancestor_id ON ra_lineage(ancestor_horse_id);
CREATE INDEX idx_lineage_generation ON ra_lineage(generation);
CREATE INDEX idx_lineage_relation ON ra_lineage(relation_type);
```

**Example data:**

For runner `rac_123_hrs_456` (horse "Sea The Stars Jr"):

| lineage_id | runner_id | generation | lineage_path | relation_type | ancestor_horse_id | ancestor_name |
|------------|-----------|------------|--------------|---------------|-------------------|---------------|
| rac_123_hrs_456_1_sire | rac_123_hrs_456 | 1 | sire | sire | sir_4868829 | Sea The Stars (IRE) |
| rac_123_hrs_456_1_dam | rac_123_hrs_456 | 1 | dam | dam | dam_5601218 | Urban Sea (USA) |
| rac_123_hrs_456_2_sire.sire | rac_123_hrs_456 | 2 | sire.sire | grandsire_paternal | sir_3722383 | Galileo (IRE) |
| rac_123_hrs_456_2_sire.dam | rac_123_hrs_456 | 2 | sire.dam | granddam_paternal | dam_4778515 | Lalun (IRE) |
| rac_123_hrs_456_2_dam.sire | rac_123_hrs_456 | 2 | dam.sire | grandsire_maternal | sir_3824619 | Miswaki (USA) |
| rac_123_hrs_456_2_dam.dam | rac_123_hrs_456 | 2 | dam.dam | granddam_maternal | dam_3563072 | Allegretta (GB) |

**Queries enabled:**

```sql
-- Get full 3-generation pedigree for a runner
SELECT * FROM ra_lineage
WHERE runner_id = 'rac_123_hrs_456'
ORDER BY generation, lineage_path;

-- Find all descendants of a specific sire
SELECT DISTINCT runner_id, horse_id
FROM ra_lineage
WHERE ancestor_horse_id = 'sir_3722383'  -- Galileo
AND relation_type LIKE '%sire%';

-- Analyze performance by sire line
SELECT
    l.ancestor_name,
    COUNT(*) as runners,
    AVG(r.position) as avg_position,
    COUNT(*) FILTER (WHERE r.position = 1) as wins
FROM ra_lineage l
JOIN ra_runners r ON l.runner_id = r.runner_id
WHERE l.relation_type = 'sire'
AND r.position IS NOT NULL
GROUP BY l.ancestor_name
ORDER BY wins DESC;

-- Find horses with same sire AND damsire (inbreeding analysis)
SELECT
    l1.runner_id,
    l1.ancestor_name as sire,
    l2.ancestor_name as damsire
FROM ra_lineage l1
JOIN ra_lineage l2 ON l1.runner_id = l2.runner_id
WHERE l1.relation_type = 'sire'
AND l2.relation_type = 'grandsire_maternal'
AND l1.ancestor_horse_id = l2.ancestor_horse_id;  -- Same horse!
```

**Pros:**
- ✅ **Unlimited generations** - Can store as deep as API provides
- ✅ **Linked to runner_id** - Per-race lineage data
- ✅ **Flexible queries** - Can analyze any ancestor path
- ✅ **Normalized** - No duplication
- ✅ **ML-friendly** - Easy to create features (e.g., "has Galileo in pedigree")
- ✅ **Inbreeding analysis** - Can detect ancestors appearing multiple times

**Cons:**
- ⚠️ **Requires JOINs** - Can't get lineage without joining
- ⚠️ **More complex** - Need recursive queries for full tree
- ⚠️ **More rows** - 5-10 rows per runner (vs 1 row in ra_runners)

---

### Option 2: Enhance ra_horse_pedigree (Keep Horse-Centric)

**Add more generations to existing table:**

```sql
ALTER TABLE ra_horse_pedigree ADD COLUMN IF NOT EXISTS
    grandsire_paternal_id VARCHAR,      -- sire's sire
    grandsire_paternal VARCHAR,
    granddam_paternal_id VARCHAR,       -- sire's dam
    granddam_paternal VARCHAR,
    grandsire_maternal_id VARCHAR,      -- dam's sire (currently "damsire")
    grandsire_maternal VARCHAR,
    granddam_maternal_id VARCHAR,       -- dam's dam
    granddam_maternal VARCHAR,

    -- 4th generation (great-grandparents) as JSONB
    great_grandparents JSONB;
```

**Example JSONB structure:**
```json
{
  "sire": {
    "sire": {
      "sire": {"id": "sir_XXX", "name": "Northern Dancer", "region": "CAN"},
      "dam": {"id": "dam_YYY", "name": "Special", "region": "USA"}
    },
    "dam": {
      "sire": {...},
      "dam": {...}
    }
  },
  "dam": {
    "sire": {...},
    "dam": {...}
  }
}
```

**Pros:**
- ✅ **Horse-centric** - Pedigree is property of horse, not runner
- ✅ **Simpler** - Single table
- ✅ **Existing infrastructure** - Just add columns

**Cons:**
- ❌ **Not linked to runner_id** - Would need JOIN through horse_id
- ❌ **Fixed depth** - Can't easily extend beyond 4 generations
- ❌ **Wide table** - Many columns for each generation
- ❌ **Harder queries** - JSONB queries more complex

---

### Option 3: Hybrid (Keep Both)

**Keep ra_horse_pedigree AND add ra_lineage:**

- **ra_horse_pedigree** - Canonical horse lineage (up to 3-4 generations)
- **ra_lineage** - Per-runner lineage snapshot linked to runner_id

**Use cases:**
- ra_horse_pedigree: "What is this horse's pedigree?"
- ra_lineage: "What was the lineage context for this specific race?"

**Pros:**
- ✅ **Best of both** - Horse-centric AND race-centric views
- ✅ **Historical accuracy** - ra_lineage captures state at race time
- ✅ **Flexible queries** - Can use either table as needed

**Cons:**
- ⚠️ **Data duplication** - Same lineage data in multiple places
- ⚠️ **Maintenance** - Need to keep both in sync

---

## RECOMMENDATION

### **Recommended Approach: Option 1 (ra_lineage table)** ✅

**Why:**
1. **Linked to runner_id** - Exactly what you requested
2. **Unlimited generations** - Can store as deep as API provides
3. **Future-proof** - Easy to extend with more API data
4. **ML-friendly** - Easy feature engineering
5. **Lineage analysis** - Can trace any ancestor path

**Implementation plan:**

1. **Create ra_lineage table**
2. **Populate from existing data** (ra_horse_pedigree + ra_runners)
3. **Update fetchers** to populate ra_lineage when creating runners
4. **Keep ra_runners pedigree columns** for convenience (denormalized)
5. **Keep ra_horse_pedigree** as horse-centric canonical source

---

## API ENDPOINTS TO COMBINE

Based on Racing API Pro account, relevant endpoints:

**1. `/v1/horses/{id}/pro` - Horse Details (Current)**
```json
{
  "horse_id": "hrs_XXX",
  "sire_id": "sir_YYY",
  "sire": "Galileo (IRE)",
  "dam_id": "dam_ZZZ",
  "dam": "Urban Sea (USA)",
  "damsire_id": "dsi_AAA",
  "damsire": "Miswaki (USA)",
  "breeder": "...",
  "region": "IRE"
}
```
**Provides:** 3 generations (horse → sire/dam → damsire)

**2. `/v1/racecards/pro` or `/v1/results/pro` (Current)**

**Already provides basic pedigree in runner data:**
```json
{
  "runners": [
    {
      "horse_id": "hrs_XXX",
      "sire_id": "sir_YYY",
      "sire": "Galileo (IRE)",
      "dam_id": "dam_ZZZ",
      "dam": "Urban Sea (USA)",
      "damsire_id": "dsi_AAA",
      "damsire": "Miswaki (USA)"
    }
  ]
}
```

**3. `/v1/dams/{dam_id}/progeny/results` - Dam Progeny Results (Pro)**

**Provides:** All offspring of a dam with their race results
**Use case:** Build maternal family line performance data

**4. `/v1/damsires/{damsire_id}/grandoffspring/results` - Damsire Grandoffspring Results (Pro)**

**Provides:** All grandoffspring of a damsire (horses whose dam's sire is this damsire) with results
**Use case:** Maternal grandsire influence analysis

**NOTE:** Extended pedigree endpoint `/v1/horses/{id}/pedigree` does not exist. Verified via comprehensive API testing.

---

## NAMING CONVENTION

**Table name:** `ra_lineage` (follows `ra_<entity>` pattern)

**Alternative names:**
- `ra_pedigree` - More specific to horses
- `ra_ancestry` - More general
- `ra_bloodline` - Racing-specific
- `ra_lineage` - ✅ Clean, clear, general enough

**Recommendation:** `ra_lineage`

---

## MIGRATION PLAN

### Phase 1: Create Table
```sql
CREATE TABLE ra_lineage (...);  -- As defined above
```

### Phase 2: Backfill from Existing Data
```sql
-- Populate from ra_horse_pedigree
INSERT INTO ra_lineage (runner_id, horse_id, generation, lineage_path, relation_type, ancestor_horse_id, ancestor_name, ancestor_region)
SELECT
    run.runner_id,
    run.horse_id,
    1 as generation,
    'sire' as lineage_path,
    'sire' as relation_type,
    ped.sire_id,
    ped.sire,
    ped.sire_region  -- If available
FROM ra_runners run
JOIN ra_horse_pedigree ped ON run.horse_id = ped.horse_id
WHERE ped.sire_id IS NOT NULL;

-- Repeat for dam, damsire, etc.
```

### Phase 3: Update Fetchers
- Modify `entity_extractor.py` to populate ra_lineage when enriching horses
- Add lineage extraction logic to runners fetcher

### Phase 4: Add Extended Pedigree (Future)
- Check if Racing API has `/v1/horses/{id}/pedigree` endpoint
- If yes, fetch and populate generations 4+
- Store in JSONB or additional ra_lineage rows

---

## EXAMPLE QUERIES

### Get Full Pedigree for a Runner
```sql
SELECT
    generation,
    relation_type,
    ancestor_name,
    ancestor_region
FROM ra_lineage
WHERE runner_id = 'rac_11745682_hrs_30455194'
ORDER BY generation, lineage_path;
```

### Find All Galileo Offspring in Database
```sql
SELECT DISTINCT
    l.runner_id,
    r.horse_name,
    rac.race_date,
    r.position
FROM ra_lineage l
JOIN ra_runners r ON l.runner_id = r.runner_id
JOIN ra_races rac ON r.race_id = rac.race_id
WHERE l.ancestor_horse_id = 'sir_3722383'  -- Galileo
AND l.relation_type = 'sire'
ORDER BY rac.race_date DESC;
```

### Sire Performance Analysis
```sql
SELECT
    l.ancestor_name as sire,
    COUNT(*) as total_runners,
    COUNT(*) FILTER (WHERE r.position = 1) as wins,
    COUNT(*) FILTER (WHERE r.position <= 3) as places,
    ROUND(AVG(r.position::int), 2) as avg_position,
    SUM(r.prize_won) as total_prize_money
FROM ra_lineage l
JOIN ra_runners r ON l.runner_id = r.runner_id
WHERE l.relation_type = 'sire'
AND r.position IS NOT NULL
GROUP BY l.ancestor_name
HAVING COUNT(*) >= 100  -- Minimum 100 runners
ORDER BY wins DESC
LIMIT 20;
```

---

## NEXT STEPS

1. ✅ **Review API docs** - Check if extended pedigree endpoint exists
2. ✅ **Create ra_lineage table**
3. ✅ **Backfill from existing data**
4. ✅ **Update fetchers** to populate on new runners
5. ✅ **Test queries** with sample data
6. ✅ **Document** lineage system

Does this approach make sense for your needs?
