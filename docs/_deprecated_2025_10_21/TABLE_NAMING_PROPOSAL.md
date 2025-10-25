# Supabase Table Naming Proposal

**Date:** 2025-10-19
**Current Tables:** 23 tables
**Total Data:** ~2.6 GB

---

## Complete Table Inventory with Proposed Names

### Category 1: Master/Reference Data (ra_mst_)
**Purpose:** Core reference entities that change infrequently. Root data for the system.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_bookmakers` | `ra_mst_bookmakers` | 22 | 120 KB | 6 | Betting companies | Monthly |
| `ra_courses` | `ra_mst_courses` | 99 | 104 KB | 8 | Race venues/tracks | Monthly |
| `ra_horses` | `ra_mst_horses` | 111,669 | 25 MB | 15 | Horse master data | Daily (via discovery) |
| `ra_jockeys` | `ra_mst_jockeys` | 3,486 | 1.2 MB | 22 | Jockey master data | Weekly |
| `ra_trainers` | `ra_mst_trainers` | 2,784 | 992 KB | 23 | Trainer master data | Weekly |
| `ra_owners` | `ra_mst_owners` | 48,168 | 17 MB | 24 | Owner master data | Weekly |
| `ra_regions` | `ra_mst_regions` | 14 | 24 KB | 3 | Geographic regions (GB, IRE) | Static |

**Total Master Records:** ~166,242 entities

---

### Category 2: Pedigree/Lineage Data (ra_mst_pedigree_)
**Purpose:** Horse breeding/lineage data. Specialized master data derived from horses.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_sires` | `ra_mst_pedigree_sires` | 2,143 | 624 KB | 47 | Sire (father) statistics | Weekly |
| `ra_dams` | `ra_mst_pedigree_dams` | 48,366 | 12 MB | 47 | Dam (mother) statistics | Weekly |
| `ra_damsires` | `ra_mst_pedigree_damsires` | 3,040 | 888 KB | 47 | Damsire (maternal grandfather) stats | Weekly |
| `ra_horse_pedigree` | `ra_pedigree` | 111,584 | 35 MB | 11 | Horse lineage relationships | Daily |

**Notes:**
- Pedigree tables have extensive statistics (47 columns each)
- Include class/distance performance breakdowns
- `ra_horse_pedigree` renamed to `ra_pedigree` (it's a relationship table, not master)

**Total Pedigree Records:** ~165,133 records

---

### Category 3: Race Master Data (ra_mst_races_)
**Purpose:** Race event master data. High-volume master data.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_races` | `ra_mst_races` | 136,960 | 52 MB | 47 | Race event master data | Daily |

**Notes:**
- Contains race metadata (date, time, venue, conditions, prize money)
- Large table (52 MB) but still reference data
- Could argue for `ra_races` (without mst) since it's event data
- **DECISION POINT:** Should this be `ra_mst_races` or just `ra_races`?

---

### Category 4: Transaction/Fact Data (ra_)
**Purpose:** High-volume transactional data. Main fact tables.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_runners` | `ra_runners` ✅ | 1,326,422 | 659 MB | 49 | Runner entries (MAIN FACT TABLE) | Daily |
| `ra_race_results` | ❌ `DEPRECATED` | 0 | 80 KB | 38 | Legacy results (NOT USED) | N/A |

**Notes:**
- `ra_runners` is the largest table (50% of total data)
- Contains race entries + results + position data
- `ra_race_results` appears to be EMPTY and deprecated

---

### Category 5: Runner Supplementary Data (ra_runner_)
**Purpose:** Additional runner-related fact data. Extensions of ra_runners.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_runner_odds` | `ra_runner_odds` ✅ | 0 | 40 KB | 10 | Runner odds by bookmaker | Real-time |
| `ra_runner_statistics` | `ra_runner_statistics` ✅ | 0 | 24 KB | 60 | Runner-level stats | Post-race |
| `ra_runner_supplementary` | `ra_runner_supplementary` ✅ | 0 | 32 KB | 16 | Additional runner data | Real-time |

**Notes:**
- All currently EMPTY (0 rows)
- Designed for future use or alternative data pipelines
- Keep `ra_runner_` prefix (clear relationship to `ra_runners`)

---

### Category 6: Analytics/Derived Data (ra_analytics_)
**Purpose:** Pre-calculated analytics and combinations. Derived from fact data.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_entity_combinations` | `ra_analytics_combinations` | 0 | 48 KB | 16 | Entity pair performance (e.g., jockey+trainer) | Weekly |
| `ra_performance_by_distance` | `ra_analytics_by_distance` | 0 | 48 KB | 20 | Performance by distance analysis | Weekly |
| `ra_performance_by_venue` | `ra_analytics_by_venue` | 0 | 48 KB | 15 | Performance by venue analysis | Weekly |

**Notes:**
- All currently EMPTY (0 rows)
- Store pre-computed analytics to speed up queries
- Rename with `ra_analytics_` prefix for clarity

---

### Category 7: Odds Data (KEEP AS-IS)
**Purpose:** Live and historical odds. Managed by separate odds workers.**

| Current Name | Proposed Name | Rows | Size | Columns | Purpose | Update Frequency |
|-------------|---------------|------|------|---------|---------|-----------------|
| `ra_odds_historical` | `ra_odds_historical` ✅ | 2,485 | 1.3 GB | 36 | Historical race odds | Daily |
| `ra_odds_live` | `ra_odds_live` ✅ | 193,034 | 307 MB | 32 | Live odds feed | Real-time |
| `ra_odds_statistics` | `ra_odds_statistics` ✅ | 7,274 | 4.4 MB | 11 | Odds statistics | Daily |

**Notes:**
- **NO CHANGES** - Managed by separate DarkHorses-Odds-Workers system
- Largest data volume (1.6 GB combined)
- Keep existing naming

---

## Summary by Category

### Proposed Naming Convention

| Prefix | Category | Tables | Purpose | Example |
|--------|----------|--------|---------|---------|
| `ra_mst_` | Master/Reference | 7 tables | Core entities (people, places) | `ra_mst_jockeys` |
| `ra_mst_pedigree_` | Pedigree Masters | 3 tables | Horse lineage masters | `ra_mst_pedigree_sires` |
| `ra_mst_races` | Race Master | 1 table | Race events (DEBATABLE) | `ra_mst_races` |
| `ra_pedigree` | Pedigree Relationship | 1 table | Horse lineage links | `ra_pedigree` |
| `ra_runners` | Main Fact Table | 1 table | Race entries + results | `ra_runners` |
| `ra_runner_` | Runner Extensions | 3 tables | Supplementary runner data | `ra_runner_odds` |
| `ra_analytics_` | Derived Analytics | 3 tables | Pre-calculated analytics | `ra_analytics_combinations` |
| `ra_odds_` | Odds Data | 3 tables | NO CHANGES | `ra_odds_historical` |

---

## Complete Renaming Table

### Tables to Rename (14 tables)

```sql
-- Master/Reference Data (7 renames)
ALTER TABLE ra_bookmakers RENAME TO ra_mst_bookmakers;
ALTER TABLE ra_courses RENAME TO ra_mst_courses;
ALTER TABLE ra_horses RENAME TO ra_mst_horses;
ALTER TABLE ra_jockeys RENAME TO ra_mst_jockeys;
ALTER TABLE ra_trainers RENAME TO ra_mst_trainers;
ALTER TABLE ra_owners RENAME TO ra_mst_owners;
ALTER TABLE ra_regions RENAME TO ra_mst_regions;

-- Pedigree Masters (3 renames)
ALTER TABLE ra_sires RENAME TO ra_mst_pedigree_sires;
ALTER TABLE ra_dams RENAME TO ra_mst_pedigree_dams;
ALTER TABLE ra_damsires RENAME TO ra_mst_pedigree_damsires;

-- Pedigree Relationship (1 rename)
ALTER TABLE ra_horse_pedigree RENAME TO ra_pedigree;

-- Race Master (1 rename - OPTIONAL)
ALTER TABLE ra_races RENAME TO ra_mst_races;

-- Analytics (3 renames)
ALTER TABLE ra_entity_combinations RENAME TO ra_analytics_combinations;
ALTER TABLE ra_performance_by_distance RENAME TO ra_analytics_by_distance;
ALTER TABLE ra_performance_by_venue RENAME TO ra_analytics_by_venue;
```

### Tables to Keep As-Is (9 tables)

```sql
-- Main fact table
ra_runners (no change)

-- Runner extensions
ra_runner_odds (no change)
ra_runner_statistics (no change)
ra_runner_supplementary (no change)

-- Odds tables (managed elsewhere)
ra_odds_historical (no change)
ra_odds_live (no change)
ra_odds_statistics (no change)

-- Deprecated
ra_race_results (no change - empty, can be dropped later)
```

---

## Decision Points for You

### 1. Race Master Data Naming
**Question:** Should `ra_races` be renamed to `ra_mst_races`?

**Option A: `ra_mst_races`** (Recommended)
- ✅ Consistent with other master data
- ✅ Clear it's reference data
- ✅ Race metadata (not transaction)

**Option B: `ra_races`** (Keep as-is)
- ✅ Feels more like "event" data
- ✅ Closely tied to `ra_runners` (same update cycle)
- ❌ Inconsistent with other masters

**Your preference?**

---

### 2. Pedigree Naming
**Question:** Is `ra_mst_pedigree_sires` too verbose?

**Option A: `ra_mst_pedigree_sires`** (Proposed)
- ✅ Clear these are pedigree-related
- ✅ Distinct from `ra_mst_horses`
- ❌ Longer names

**Option B: `ra_mst_sires`** (Simpler)
- ✅ Shorter
- ❌ Less clear they're pedigree-specific

**Your preference?**

---

### 3. Analytics Prefix
**Question:** Use `ra_analytics_` or `ra_analytic_` (singular)?

**Proposed:** `ra_analytics_combinations` (plural)
**Alternative:** `ra_analytic_combinations` (singular)

**Your preference?**

---

### 4. Deprecated Table
**Question:** What to do with `ra_race_results`?

- **Current status:** EMPTY (0 rows), deprecated
- **Options:**
  1. Drop now (clean slate)
  2. Rename to `ra_deprecated_race_results` (mark clearly)
  3. Keep as-is (ignore)

**Your preference?**

---

## Foreign Key Impact Analysis

### Tables with Foreign Keys to Renamed Tables (Must Update)

#### `ra_runners` (8 foreign keys)
```sql
-- Current → New
race_id: ra_races → ra_mst_races
horse_id: ra_horses → ra_mst_horses
jockey_id: ra_jockeys → ra_mst_jockeys
trainer_id: ra_trainers → ra_mst_trainers
owner_id: ra_owners → ra_mst_owners
sire_id: ra_sires → ra_mst_pedigree_sires
dam_id: ra_dams → ra_mst_pedigree_dams
damsire_id: ra_damsires → ra_mst_pedigree_damsires
```

#### `ra_pedigree` (formerly `ra_horse_pedigree`) (4 foreign keys)
```sql
-- Current → New
horse_id: ra_horses → ra_mst_horses
sire_id: ra_sires → ra_mst_pedigree_sires
dam_id: ra_dams → ra_mst_pedigree_dams
damsire_id: ra_damsires → ra_mst_pedigree_damsires
```

#### `ra_mst_pedigree_sires` (formerly `ra_sires`) (1 foreign key)
```sql
-- Current → New
horse_id: ra_horses → ra_mst_horses
```

#### `ra_runner_odds` (3 foreign keys)
```sql
-- Current → New
race_id: ra_races → ra_mst_races
horse_id: ra_horses → ra_mst_horses
bookmaker_id: ra_bookmakers → ra_mst_bookmakers
```

#### `ra_runner_statistics` (2 foreign keys)
```sql
-- Current → New
horse_id: ra_horses → ra_mst_horses
runner_id: ra_runners → ra_runners (no change)
```

#### `ra_runner_supplementary` (2 foreign keys)
```sql
-- Current → New
quote_race_id: ra_races → ra_mst_races
runner_id: ra_runners → ra_runners (no change)
```

#### `ra_race_results` (DEPRECATED - 8 foreign keys)
```sql
-- If we keep this table, need to update:
race_id: ra_races → ra_mst_races
horse_id: ra_horses → ra_mst_horses
(plus 6 more)

-- RECOMMEND: Drop this table entirely
```

---

## Migration Complexity Summary

### Tables to Rename: 14
- 7 master entities
- 3 pedigree masters
- 1 pedigree relationship
- 1 race master (optional)
- 3 analytics tables

### Foreign Keys to Update: ~24 constraints
- Most are in `ra_runners` (8 FK)
- Rest distributed across runner extensions

### Code Files to Update: ~15-20 files
- All fetchers (8 files)
- Database client
- Entity extractor
- Main orchestrator
- Tests
- Documentation

---

## Recommended Approach

### Phase 1: Rename Tables (Low Risk)
```sql
-- Use ALTER TABLE ... RENAME TO
-- PostgreSQL updates foreign keys automatically!
-- Views and functions need manual updates
```

### Phase 2: Update Code (Medium Risk)
- Update all table references in Python code
- Update insert/upsert methods
- Test extensively

### Phase 3: Update Documentation (Low Risk)
- Update CLAUDE.md
- Update all docs
- Update migration docs

---

## Questions for You

1. **Race master naming:** `ra_mst_races` or keep `ra_races`?
2. **Pedigree verbosity:** `ra_mst_pedigree_sires` or `ra_mst_sires`?
3. **Analytics prefix:** `ra_analytics_` or `ra_analytic_`?
4. **Deprecated table:** Drop `ra_race_results` now or later?
5. **Any other tables you want different prefixes for?**

---

## Next Steps

Once you approve the naming scheme:

1. ✅ Create migration SQL script
2. ✅ Test on dev database
3. ✅ Update all fetchers
4. ✅ Update database client
5. ✅ Run tests
6. ✅ Deploy to production

**Estimated time:** 4-6 hours for full migration

---

**Please review and let me know your preferences!**
