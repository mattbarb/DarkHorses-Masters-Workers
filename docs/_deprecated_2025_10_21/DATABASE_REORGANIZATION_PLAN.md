# Database Reorganization Plan - ra_mst_ Prefix Strategy

**Date:** 2025-10-19
**Status:** Planning Phase

---

## Overview

Reorganize database tables with clear naming convention and grouped fetcher architecture:
- **Master/Reference tables:** `ra_mst_` prefix
- **Transaction/Fact tables:** `ra_` prefix (no mst)
- **Odds tables:** Managed separately (excluded from this reorganization)

---

## Current → Proposed Table Mapping

### Master/Reference Tables (Add ra_mst_ prefix)

| Current Table | Proposed Table | Type | Rows | Dependencies |
|--------------|----------------|------|------|--------------|
| `ra_bookmakers` | `ra_mst_bookmakers` | Reference | 19 | None |
| `ra_courses` | `ra_mst_courses` | Reference | 101 | None |
| `ra_horses` | `ra_mst_horses` | Master | ~111K | None (root entity) |
| `ra_sires` | `ra_mst_sires` | Master | ~3K | → ra_mst_horses |
| `ra_dams` | `ra_mst_dams` | Master | ~66K | → ra_mst_horses |
| `ra_damsires` | `ra_mst_damsires` | Master | ~5K | → ra_mst_horses |
| `ra_jockeys` | `ra_mst_jockeys` | Master | ~3.5K | None |
| `ra_trainers` | `ra_mst_trainers` | Master | ~2.8K | None |
| `ra_owners` | `ra_mst_owners` | Master | ~48K | None |
| `ra_races` | `ra_mst_races` | Master | ~143K | → ra_mst_courses |

### Transaction/Fact Tables (Keep ra_ prefix)

| Current Table | Proposed Table | Type | Rows | Dependencies |
|--------------|----------------|------|------|--------------|
| `ra_runners` | `ra_runners` | Fact | ~1.2M | ALL masters |
| `ra_race_results` | ❌ **DEPRECATED** | Legacy | ~72 | (Use ra_runners) |
| `ra_horse_pedigree` | `ra_horse_pedigree` | Relationship | ~111K | → ra_mst_horses |
| `ra_entity_combinations` | `ra_entity_combinations` | Analytics | Small | → masters |
| `ra_performance_by_distance` | `ra_performance_by_distance` | Analytics | Small | → masters |
| `ra_performance_by_venue` | `ra_performance_by_venue` | Analytics | Small | → masters |
| `ra_runner_odds` | `ra_runner_odds` | Transaction | Small | → ra_runners |
| `ra_runner_statistics` | `ra_runner_statistics` | Derived | Small | → ra_runners |
| `ra_runner_supplementary` | `ra_runner_supplementary` | Transaction | Small | → ra_runners |
| `ra_regions` | `ra_regions` | Lookup | 2 | None |

### Odds Tables (Managed Elsewhere - NO CHANGES)

| Table | Status | Notes |
|-------|--------|-------|
| `ra_odds_historical` | ✅ KEEP AS-IS | 1.3 GB - managed by odds workers |
| `ra_odds_live` | ✅ KEEP AS-IS | 307 MB - managed by odds workers |
| `ra_odds_statistics` | ✅ KEEP AS-IS | 4.4 MB - managed by odds workers |

---

## Clarification Needed

**Your list includes several tables I don't see in the database:**

1. `ra_ace_results` - Listed 4 times in your message, but doesn't exist in DB
2. `ra_racesrunners` - Not in DB (is this `ra_runners`?)
3. `ra_racestrainers` - Not in DB
4. `ra_races_regions` - Not in DB (is this `ra_regions`?)

**Questions:**
1. Are these tables you want to **CREATE** as part of the reorganization?
2. Or were these typos/placeholders?
3. What data should they contain?

---

## Dependency Hierarchy (Critical for Migration)

### Level 1: Root Masters (No dependencies)
```
ra_mst_bookmakers
ra_mst_courses
ra_mst_horses     ← ROOT (all pedigree references this)
ra_mst_jockeys
ra_mst_trainers
ra_mst_owners
ra_regions
```

### Level 2: Pedigree Masters (Depend on horses)
```
ra_mst_sires      → ra_mst_horses
ra_mst_dams       → ra_mst_horses
ra_mst_damsires   → ra_mst_horses
```

### Level 3: Race Masters (Depend on courses)
```
ra_mst_races      → ra_mst_courses
```

### Level 4: Transaction Tables (Depend on ALL masters)
```
ra_runners        → ra_mst_races
                  → ra_mst_horses
                  → ra_mst_jockeys
                  → ra_mst_trainers
                  → ra_mst_owners
                  → ra_mst_sires
                  → ra_mst_dams
                  → ra_mst_damsires

ra_horse_pedigree → ra_mst_horses
                  → ra_mst_sires
                  → ra_mst_dams
                  → ra_mst_damsires
```

### Level 5: Derived Tables (Depend on runners)
```
ra_runner_odds         → ra_runners, ra_mst_bookmakers
ra_runner_statistics   → ra_runners
ra_runner_supplementary → ra_runners
ra_entity_combinations → ra_runners (implicitly)
```

---

## Proposed Grouped Fetcher Architecture

### Current Problem
- Each entity has separate fetcher (8 fetchers total)
- Lots of code duplication
- Hard to maintain consistency
- No clear grouping by data type

### Proposed Solution: 3 Grouped Fetchers

#### 1. **MasterReferenceFetcher** (Static/Slow-changing data)
**Tables:**
- `ra_mst_bookmakers`
- `ra_mst_courses`

**Schedule:** Monthly
**API Endpoints:**
- `/v1/bookmakers`
- `/v1/courses`

**Features:**
- Simple direct fetch → transform → insert
- No entity extraction needed
- Minimal relationships

---

#### 2. **MasterEntitiesFetcher** (People & Horses)
**Tables:**
- `ra_mst_horses` (+ `ra_horse_pedigree`)
- `ra_mst_sires`
- `ra_mst_dams`
- `ra_mst_damsires`
- `ra_mst_jockeys`
- `ra_mst_trainers`
- `ra_mst_owners`

**Schedule:** Weekly (people), Daily (horses via races)
**API Endpoints:**
- `/v1/horses/{id}/pro` (enrichment)
- `/v1/jockeys` (bulk)
- `/v1/trainers` (bulk)
- `/v1/owners` (bulk)

**Features:**
- Handles hybrid enrichment for horses
- Manages pedigree relationships (sires, dams, damsires)
- Entity extraction from races/results
- Validates foreign keys before insert

**Key Logic:**
```python
class MasterEntitiesFetcher:
    def fetch_horses_from_races(self):
        # Discovery phase (from runners)
        # Enrichment phase (Pro endpoint)
        # Pedigree extraction (sires, dams, damsires)
        pass

    def fetch_people_bulk(self, entity_type):
        # Bulk fetch jockeys/trainers/owners
        pass
```

---

#### 3. **RacesAndRunnersFetcher** (Transaction data)
**Tables:**
- `ra_mst_races`
- `ra_runners` (fact table)

**Schedule:** Daily (racecards), Daily (results)
**API Endpoints:**
- `/v1/racecards/pro` (racecards)
- `/v1/results/pro` (results)

**Features:**
- Fetches racecards (pre-race)
- Fetches results (post-race)
- Triggers entity extraction → MasterEntitiesFetcher
- Stores runner records with all relationships
- Handles position data (results only)

**Key Logic:**
```python
class RacesAndRunnersFetcher:
    def __init__(self):
        self.entity_fetcher = MasterEntitiesFetcher()

    def fetch_racecards(self, date):
        # Fetch races
        # Extract entities → entity_fetcher
        # Store races + runners
        pass

    def fetch_results(self, date):
        # Fetch results
        # Extract entities → entity_fetcher
        # Update runners with positions
        pass
```

---

## Migration Strategy

### Phase 1: Create New Tables (Parallel to existing)
1. Create all `ra_mst_*` tables with identical schemas
2. Create foreign keys pointing to new tables
3. Keep old tables running (no disruption)

### Phase 2: Dual-Write Period
1. Update all fetchers to write to BOTH old and new tables
2. Run for 1 week to validate
3. Monitor data consistency

### Phase 3: Data Backfill
1. Copy historical data from old → new tables
2. Validate row counts and relationships
3. Check foreign key integrity

### Phase 4: Switch Readers
1. Update all read queries to use new tables
2. Test extensively
3. Keep old tables as backup

### Phase 5: Deprecate Old Tables
1. Stop writing to old tables
2. Archive old tables (rename to `ra_old_*`)
3. Drop after 30 days if no issues

---

## Foreign Key Changes Required

### Current Foreign Keys (Must Update)

#### ra_runners (8 foreign keys)
```sql
-- BEFORE
ra_runners.horse_id → ra_horses.id
ra_runners.jockey_id → ra_jockeys.id
ra_runners.trainer_id → ra_trainers.id
ra_runners.owner_id → ra_owners.id
ra_runners.sire_id → ra_sires.id
ra_runners.dam_id → ra_dams.id
ra_runners.damsire_id → ra_damsires.id
ra_runners.race_id → ra_races.id

-- AFTER
ra_runners.horse_id → ra_mst_horses.id
ra_runners.jockey_id → ra_mst_jockeys.id
ra_runners.trainer_id → ra_mst_trainers.id
ra_runners.owner_id → ra_mst_owners.id
ra_runners.sire_id → ra_mst_sires.id
ra_runners.dam_id → ra_mst_dams.id
ra_runners.damsire_id → ra_mst_damsires.id
ra_runners.race_id → ra_mst_races.id
```

#### ra_horse_pedigree (4 foreign keys)
```sql
-- BEFORE
ra_horse_pedigree.horse_id → ra_horses.id
ra_horse_pedigree.sire_id → ra_sires.id (implicit)
ra_horse_pedigree.dam_id → ra_dams.id (implicit)
ra_horse_pedigree.damsire_id → ra_damsires.id (implicit)

-- AFTER
ra_horse_pedigree.horse_id → ra_mst_horses.id
(etc. for sire, dam, damsire)
```

#### ra_runner_odds (3 foreign keys)
```sql
-- BEFORE
ra_runner_odds.race_id → ra_races.id
ra_runner_odds.horse_id → ra_horses.id
ra_runner_odds.bookmaker_id → ra_bookmakers.id

-- AFTER
ra_runner_odds.race_id → ra_mst_races.id
ra_runner_odds.horse_id → ra_mst_horses.id
ra_runner_odds.bookmaker_id → ra_mst_bookmakers.id
```

---

## Code Changes Required

### Files to Update (Estimated)

#### Fetchers (3 new, 8 deprecated)
```
✅ NEW: fetchers/master_reference_fetcher.py
✅ NEW: fetchers/master_entities_fetcher.py
✅ NEW: fetchers/races_runners_fetcher.py

❌ DEPRECATE: fetchers/bookmakers_fetcher.py
❌ DEPRECATE: fetchers/courses_fetcher.py
❌ DEPRECATE: fetchers/horses_fetcher.py
❌ DEPRECATE: fetchers/jockeys_fetcher.py
❌ DEPRECATE: fetchers/trainers_fetcher.py
❌ DEPRECATE: fetchers/owners_fetcher.py
❌ DEPRECATE: fetchers/races_fetcher.py
❌ DEPRECATE: fetchers/results_fetcher.py
```

#### Database Client
```
📝 UPDATE: utils/supabase_client.py
   - Update all table names
   - Update foreign key references
   - Add new insert methods for grouped tables
```

#### Entity Extractor
```
📝 UPDATE: utils/entity_extractor.py
   - Update table references
   - Add pedigree extraction logic (sires, dams, damsires)
```

#### Configuration
```
📝 UPDATE: config/config.py (if table names hardcoded)
📝 UPDATE: main.py (new fetcher imports and configs)
```

#### Documentation
```
📝 UPDATE: CLAUDE.md
📝 UPDATE: docs/README.md
📝 UPDATE: docs/architecture/DATABASE_SCHEMA.md (create if missing)
```

---

## Benefits of This Approach

### 1. Clear Data Hierarchy
- `ra_mst_*` = Master/reference data (slow-changing)
- `ra_*` = Transaction/fact data (fast-changing)
- Easy to understand table purpose

### 2. Reduced Code Duplication
- 3 grouped fetchers instead of 8 individual ones
- Shared logic for similar entities (people, horses, pedigree)
- Easier to maintain

### 3. Better Relationship Management
- Foreign keys clearly point to master tables
- Dependency hierarchy is obvious
- Easier to validate data integrity

### 4. Improved Performance
- Can optimize master table indexes differently
- Separate read patterns (reference vs transaction)
- Better query planning

### 5. Clearer Production Schedule
- Monthly: Reference data (courses, bookmakers)
- Weekly: People (jockeys, trainers, owners)
- Daily: Races, runners, horses (via entity extraction)

---

## Estimated Effort

### Migration Scripts
- **Database:** 3-4 hours
  - Create new tables
  - Set up foreign keys
  - Write data migration scripts

### Code Changes
- **Fetchers:** 8-12 hours
  - Build 3 new grouped fetchers
  - Test with real data
  - Handle edge cases

- **Database Client:** 2-3 hours
  - Update method signatures
  - Update table references
  - Add validation logic

- **Testing:** 4-6 hours
  - Unit tests for new fetchers
  - Integration tests
  - Data validation queries

- **Documentation:** 2-3 hours
  - Update all docs
  - Create migration guide
  - Update CLAUDE.md

**Total:** ~20-30 hours

---

## Next Steps (Need Your Input)

### Before We Proceed:

1. **Clarify missing tables:**
   - What is `ra_ace_results`? (you listed it 4 times)
   - What are `ra_racesrunners`, `ra_racestrainers`, `ra_races_regions`?
   - Should we create these or were they typos?

2. **Confirm table mapping:**
   - Does the Current → Proposed mapping look correct?
   - Any tables you want grouped differently?

3. **Approve fetcher grouping:**
   - Does the 3-fetcher approach make sense?
   - Or would you prefer different groupings?

4. **Migration timeline:**
   - Do you want to do this in phases (dual-write) or all at once?
   - Any production constraints we need to consider?

5. **Odds tables:**
   - Confirm we leave `ra_odds_*` tables completely untouched?

---

**Please review and let me know:**
- Are there tables I'm missing?
- Does the grouping strategy make sense?
- Should I proceed with creating the migration scripts?
