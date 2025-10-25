# LINEAGE SYSTEM - COMPLETE IMPLEMENTATION

**Date:** 2025-10-18
**Status:** ✅ Production Ready
**Version:** 1.0

---

## OVERVIEW

The lineage system provides comprehensive pedigree tracking and ancestor performance statistics for UK and Ireland horse racing. It combines detailed lineage relationships with aggregated performance metrics.

### System Components

1. **ra_lineage** - Complete pedigree tracking (3,979,002 records)
2. **ra_sire_stats** - Sire racing career + progeny performance (2,143 records)
3. **ra_dam_stats** - Dam racing career + progeny performance (48,366 records)
4. **ra_damsire_stats** - Damsire racing career + grandoffspring performance (3,040 records)

---

## TABLE STRUCTURE

### 1. ra_lineage Table

**Purpose:** Track complete pedigree for every runner

**Schema:**
```sql
CREATE TABLE ra_lineage (
    lineage_id VARCHAR PRIMARY KEY,              -- e.g., "RUN123_1_sire"
    runner_id VARCHAR NOT NULL,                  -- Links to ra_runners
    horse_id VARCHAR NOT NULL,                   -- The horse in this race
    generation INT NOT NULL,                     -- 1=parent, 2=grandparent, etc.
    lineage_path VARCHAR NOT NULL,               -- e.g., "sire", "dam", "sire.sire"
    relation_type VARCHAR NOT NULL,              -- sire, dam, grandsire_maternal, etc.
    ancestor_horse_id VARCHAR,                   -- ID of the ancestor
    ancestor_name VARCHAR,                       -- Name of the ancestor
    ancestor_region VARCHAR,                     -- Region code (GB, IRE)
    ancestor_dob DATE,                           -- Ancestor's date of birth
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (runner_id, lineage_path)
);
```

**Current Data:**
- **Total records:** 3,979,002
- **Runners tracked:** 1,326,334 (100% coverage)
- **Unique ancestors:** 53,548
- **Unique horses:** 111,646
- **Generations:** 2 (parents + grandparents)

**Relation Types:**
- `sire` - Father (generation 1)
- `dam` - Mother (generation 1)
- `grandsire_maternal` - Mother's father (generation 2)

**Indexes:**
- Primary key on `lineage_id`
- Index on `runner_id` (fast lookup by runner)
- Index on `horse_id` (fast lookup by horse)
- Index on `ancestor_horse_id` (fast progeny/grandoffspring queries)
- Index on `generation` (filter by generation)
- Index on `relation_type` (filter by relationship)
- Unique constraint on `(runner_id, lineage_path)`

---

### 2. ra_sire_stats Table

**Purpose:** Aggregate statistics for sires (own career + progeny performance)

**Schema:**
```sql
CREATE TABLE ra_sire_stats (
    sire_id VARCHAR PRIMARY KEY,
    sire_name VARCHAR NOT NULL,
    sire_region VARCHAR,

    -- Sire's own racing career
    own_race_runs INT DEFAULT 0,
    own_race_wins INT DEFAULT 0,
    own_race_places INT DEFAULT 0,              -- Positions 1-3
    own_total_prize DECIMAL(12,2) DEFAULT 0,
    own_best_position INT,
    own_avg_position DECIMAL(5,2),
    own_career_start DATE,
    own_career_end DATE,

    -- Progeny statistics
    total_progeny INT DEFAULT 0,                -- Unique offspring
    progeny_total_runs INT DEFAULT 0,
    progeny_wins INT DEFAULT 0,
    progeny_places INT DEFAULT 0,
    progeny_total_prize DECIMAL(15,2) DEFAULT 0,
    progeny_win_rate DECIMAL(5,2),              -- wins / total_runs * 100
    progeny_place_rate DECIMAL(5,2),            -- places / total_runs * 100
    progeny_avg_position DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Current Data:**
- **Total sires:** 2,143
- **Top sire by progeny wins:** Kodiac (GB) - 1,900 wins from 1,350 progeny (10.46% win rate)
- **Top sire by win rate:** Dubawi (IRE) - 19.40% win rate (1,364 wins from 970 progeny)

**Indexes:**
- Primary key on `sire_id`
- Index on `sire_name` (search by name)
- Index on `progeny_wins DESC` (top sires by wins)
- Index on `total_progeny DESC` (most prolific sires)
- Index on `progeny_win_rate DESC` (best win rates)
- Index on `own_race_wins DESC` (best racing careers)

---

### 3. ra_dam_stats Table

**Purpose:** Aggregate statistics for dams (own career + progeny performance)

**Schema:**
```sql
CREATE TABLE ra_dam_stats (
    dam_id VARCHAR PRIMARY KEY,
    dam_name VARCHAR NOT NULL,
    dam_region VARCHAR,

    -- Dam's own racing career (same fields as sire_stats)
    own_race_runs INT DEFAULT 0,
    own_race_wins INT DEFAULT 0,
    own_race_places INT DEFAULT 0,
    own_total_prize DECIMAL(12,2) DEFAULT 0,
    own_best_position INT,
    own_avg_position DECIMAL(5,2),
    own_career_start DATE,
    own_career_end DATE,

    -- Progeny statistics (same fields as sire_stats)
    total_progeny INT DEFAULT 0,
    progeny_total_runs INT DEFAULT 0,
    progeny_wins INT DEFAULT 0,
    progeny_places INT DEFAULT 0,
    progeny_total_prize DECIMAL(15,2) DEFAULT 0,
    progeny_win_rate DECIMAL(5,2),
    progeny_place_rate DECIMAL(5,2),
    progeny_avg_position DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Current Data:**
- **Total dams:** 48,366
- **Top dam by progeny wins:** Eternal Instinct (GB) - 45 wins from 6 progeny (12.75% win rate)
- **Top dam by win rate:** Jabbara (IRE) - 16.24% win rate (44 wins from 4 progeny)

**Indexes:** Same structure as ra_sire_stats

---

### 4. ra_damsire_stats Table

**Purpose:** Aggregate statistics for damsires (own career + grandoffspring performance)

**Schema:**
```sql
CREATE TABLE ra_damsire_stats (
    damsire_id VARCHAR PRIMARY KEY,
    damsire_name VARCHAR NOT NULL,
    damsire_region VARCHAR,

    -- Damsire's own racing career (same fields as sire_stats)
    own_race_runs INT DEFAULT 0,
    own_race_wins INT DEFAULT 0,
    own_race_places INT DEFAULT 0,
    own_total_prize DECIMAL(12,2) DEFAULT 0,
    own_best_position INT,
    own_avg_position DECIMAL(5,2),
    own_career_start DATE,
    own_career_end DATE,

    -- Grandoffspring statistics (maternal grandchildren)
    total_grandoffspring INT DEFAULT 0,         -- Unique horses
    grandoffspring_total_runs INT DEFAULT 0,
    grandoffspring_wins INT DEFAULT 0,
    grandoffspring_places INT DEFAULT 0,
    grandoffspring_total_prize DECIMAL(15,2) DEFAULT 0,
    grandoffspring_win_rate DECIMAL(5,2),
    grandoffspring_place_rate DECIMAL(5,2),
    grandoffspring_avg_position DECIMAL(5,2),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

**Current Data:**
- **Total damsires:** 3,040
- **Coverage:** Tracks maternal grandsires for all horses

**Indexes:**
- Primary key on `damsire_id`
- Index on `damsire_name`
- Index on `grandoffspring_wins DESC`
- Index on `total_grandoffspring DESC`
- Index on `grandoffspring_win_rate DESC`
- Index on `own_race_wins DESC`

---

## DATA RELATIONSHIPS

### Architecture Decision

**We use BOTH normalized and denormalized structures:**

1. **ra_runners** contains: `sire_id`, `dam_id`, `damsire_id` (denormalized)
   - Fast direct access to immediate pedigree
   - No JOINs needed for basic queries

2. **ra_lineage** contains: Complete pedigree graph (normalized)
   - Flexible queries (all ancestors, all descendants)
   - Extensible (can add generation 3, 4, 5+)
   - Powers aggregate statistics

3. **ra_*_stats** tables contain: Pre-aggregated statistics
   - Fast queries for ancestor performance
   - Combines own career + breeding success
   - Updated periodically (daily/weekly)

### Relationship Diagram

```
ra_runners
    ├─ runner_id (PRIMARY)
    ├─ horse_id (references ra_horses)
    ├─ sire_id (denormalized - quick access)
    ├─ dam_id (denormalized - quick access)
    └─ damsire_id (denormalized - quick access)

ra_lineage
    ├─ runner_id (FOREIGN KEY → ra_runners)
    ├─ horse_id (FOREIGN KEY → ra_horses)
    └─ ancestor_horse_id (FOREIGN KEY → ra_horses)

ra_sire_stats
    └─ sire_id (FOREIGN KEY → ra_horses)

ra_dam_stats
    └─ dam_id (FOREIGN KEY → ra_horses)

ra_damsire_stats
    └─ damsire_id (FOREIGN KEY → ra_horses)
```

---

## EXAMPLE QUERIES

### 1. Get Complete Pedigree for a Runner

```sql
SELECT
    lineage_path,
    relation_type,
    generation,
    ancestor_name,
    ancestor_region
FROM ra_lineage
WHERE runner_id = 'RUN123'
ORDER BY generation, lineage_path;
```

### 2. Find All Progeny of a Sire

```sql
SELECT
    r.horse_name,
    r.race_date,
    r.position,
    r.prize_won
FROM ra_lineage l
JOIN ra_runners r ON l.runner_id = r.runner_id
WHERE l.ancestor_horse_id = 'sir_123456'
AND l.relation_type = 'sire'
ORDER BY r.race_date DESC;
```

### 3. Find All Grandoffspring of a Damsire

```sql
SELECT
    r.horse_name,
    r.race_date,
    r.position,
    r.prize_won
FROM ra_lineage l
JOIN ra_runners r ON l.runner_id = r.runner_id
WHERE l.ancestor_horse_id = 'dsi_123456'
AND l.relation_type = 'grandsire_maternal'
ORDER BY r.race_date DESC;
```

### 4. Best Sires by Progeny Win Rate (min 100 runs)

```sql
SELECT
    sire_name,
    total_progeny,
    progeny_total_runs,
    progeny_wins,
    progeny_win_rate,
    own_race_wins
FROM ra_sire_stats
WHERE progeny_total_runs >= 100
ORDER BY progeny_win_rate DESC
LIMIT 20;
```

### 5. Dams Who Were Great Racers AND Great Producers

```sql
SELECT
    dam_name,
    own_race_wins,
    own_total_prize,
    total_progeny,
    progeny_wins,
    progeny_win_rate
FROM ra_dam_stats
WHERE own_race_wins >= 5           -- Won at least 5 races themselves
AND progeny_wins >= 10              -- Offspring won at least 10 races
ORDER BY progeny_win_rate DESC;
```

### 6. Compare Ancestor's Own Success vs Breeding Success

```sql
SELECT
    sire_name,
    own_race_wins as racing_wins,
    own_total_prize as racing_prize,
    progeny_wins as breeding_wins,
    progeny_total_prize as breeding_prize,
    CASE
        WHEN own_race_wins > 0 THEN ROUND(progeny_wins::numeric / own_race_wins::numeric, 2)
        ELSE NULL
    END as breeding_multiplier
FROM ra_sire_stats
WHERE own_race_wins > 0
AND progeny_wins > 0
ORDER BY breeding_multiplier DESC
LIMIT 20;
```

---

## MAINTENANCE

### Initial Population

1. **Migration 019:** Create ra_lineage table
   ```bash
   python3 scripts/run_migration_019_create_lineage.py
   ```

2. **Backfill ra_lineage:** Populate from existing ra_runners data
   ```bash
   python3 scripts/backfill_ra_lineage.py
   ```

3. **Migration 020:** Create ancestor stats tables
   ```bash
   python3 scripts/run_migration_020_create_ancestor_stats.py
   ```

4. **Backfill ancestor stats:** Calculate statistics
   ```bash
   python3 scripts/backfill_ancestor_stats.py
   ```

### Ongoing Updates

**For new runners (automatic):**
- Entity extraction automatically populates sire/dam/damsire in ra_runners
- TODO: Add trigger or scheduled job to create ra_lineage records for new runners

**For ancestor statistics (periodic):**
```bash
# Refresh ancestor statistics (run weekly or monthly)
python3 scripts/backfill_ancestor_stats.py
```

This will UPSERT all records, updating existing ones with latest statistics.

---

## PERFORMANCE

### Backfill Performance

**Migration 019 (create table):**
- Execution time: ~5 seconds
- Result: Empty table with 12 columns, 9 indexes

**Backfill ra_lineage:**
- Execution time: ~2 minutes
- Records inserted: 3,979,002
- Runners processed: 1,326,334

**Migration 020 (create stats tables):**
- Execution time: ~5 seconds
- Result: 3 empty tables (ra_sire_stats, ra_dam_stats, ra_damsire_stats)

**Backfill ancestor stats:**
- Execution time: ~4 minutes
- Records inserted: 53,549 total
  - 2,143 sires
  - 48,366 dams
  - 3,040 damsires

### Query Performance

With proper indexes:
- Pedigree lookup by runner_id: < 10ms
- Progeny lookup by sire_id: < 50ms (depending on progeny count)
- Ancestor stats lookup: < 5ms (direct primary key)

---

## RACING API PRO ENDPOINTS

### Available Endpoints

**Dam Progeny Results:**
```
GET /v1/dams/{dam_id}/results
```

**Damsire Grandoffspring Results:**
```
GET /v1/damsires/{damsire_id}/results
```

### Key Finding

These Pro endpoints return the **same race result structure** as `/v1/results`, just pre-filtered by lineage.

**Since we already fetch all results via `/v1/results` and track lineage in `ra_lineage`:**
- We already have this data locally
- No need to fetch from Pro endpoints for ongoing operations
- Pro endpoints useful for:
  - Validation (ensure we have all races)
  - Backfill (find historical gaps)
  - One-off analysis (without writing SQL)

See: `docs/PRO_ENDPOINTS_INVESTIGATION.md` for details

---

## FUTURE ENHANCEMENTS

### Potential Additions

1. **Extended Generations:**
   - Add generation 3 (great-grandparents)
   - Add generation 4+ if needed
   - Schema already supports this (just add more backfill logic)

2. **Paternal Grandsire:**
   - Currently only track maternal grandsire (damsire)
   - Could add paternal grandsire (sire's sire)
   - Would create ra_grandsire_paternal_stats

3. **Breeder Statistics:**
   - Track breeder performance
   - Similar structure to sire/dam stats
   - Would create ra_breeder_stats

4. **Time-Series Statistics:**
   - Track ancestor performance by year
   - Detect trends (improving/declining)
   - Would create ra_sire_stats_yearly, etc.

5. **Real-Time Updates:**
   - Trigger to create ra_lineage records on new runners
   - Incremental updates to ancestor stats (instead of full refresh)

---

## FILES

### Migrations
- `migrations/019_create_ra_lineage_table.sql` - Creates ra_lineage table
- `migrations/020_create_ancestor_stats_tables.sql` - Creates stats tables

### Scripts
- `scripts/run_migration_019_create_lineage.py` - Execute Migration 019
- `scripts/backfill_ra_lineage.py` - Populate ra_lineage from ra_runners
- `scripts/run_migration_020_create_ancestor_stats.py` - Execute Migration 020
- `scripts/backfill_ancestor_stats.py` - Calculate and populate ancestor statistics
- `scripts/test_ra_lineage_queries.py` - Test lineage queries
- `scripts/test_pro_lineage_endpoints.py` - Test Pro API endpoints
- `scripts/analyze_pro_lineage_data.py` - Analyze Pro endpoint responses

### Documentation
- `docs/LINEAGE_SYSTEM_DESIGN_PROPOSAL.md` - Initial design document
- `docs/LINEAGE_SYSTEM_IMPLEMENTATION_SUMMARY.md` - Implementation details
- `docs/PRO_ENDPOINTS_INVESTIGATION.md` - Pro endpoint testing results
- `docs/LINEAGE_SYSTEM_COMPLETE.md` - This file (complete system documentation)

---

## SUMMARY

✅ **Complete lineage system implemented and populated**

**Tables:**
- ra_lineage: 3,979,002 records (100% coverage)
- ra_sire_stats: 2,143 records
- ra_dam_stats: 48,366 records
- ra_damsire_stats: 3,040 records

**Total:** 4,032,551 lineage records tracking 111,646 unique horses

**Capabilities:**
- Complete pedigree tracking for every runner
- Ancestor's own racing career statistics
- Progeny/grandoffspring performance statistics
- Flexible queries for breeding analysis
- Extensible to additional generations

**Status:** Production ready, all backfills complete, queries tested and validated

---

**Last Updated:** 2025-10-18
**Author:** DarkHorses Masters Workers System
**Version:** 1.0
