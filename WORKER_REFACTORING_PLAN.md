# Worker Refactoring Plan for Normalized Database Schema

**Date:** 2025-10-19
**Purpose:** Refactor all workers to support the new normalized database schema
**Migration Reference:** `*MIGRATION_MAPPING_REFERENCE.md`

---

## Executive Summary

The database has been normalized from a monolithic structure (75 columns in `ra_runners`) to a properly structured relational database with:
- **3 new breeding tables**: `ra_sires`, `ra_dams`, `ra_damsires`
- **Statistics fields added** to `ra_jockeys`, `ra_trainers`, `ra_owners`
- **Column renames** across `ra_races`, `ra_runners`, and other tables
- **Primary key standardization**: All tables use `id` as PK (but FKs still use `{entity}_id`)

---

## Critical Breaking Changes

### 1. Breeding Data Normalization (HIGHEST PRIORITY)

**Problem:**
Current code stores breeding data denormalized in `ra_runners`:
- `sire_name`, `dam_name`, `damsire_name` columns **NO LONGER EXIST**
- Only `sire_id`, `dam_id`, `damsire_id` remain in `ra_runners`

**Solution Required:**
- Extract sire/dam/damsire entities from runner data
- Insert into separate `ra_sires`, `ra_dams`, `ra_damsires` tables
- Update `utils/entity_extractor.py` to handle breeding entities
- Update `utils/supabase_client.py` to add insert methods for breeding tables

**Files to Update:**
- `utils/entity_extractor.py:90-106` - Remove sire/dam name handling, add breeding entity extraction
- `utils/supabase_client.py` - Add `insert_sires()`, `insert_dams()`, `insert_damsires()` methods
- `fetchers/races_fetcher.py:298-304` - Store breeding IDs only (no names)
- `fetchers/results_fetcher.py` - Similar updates for result runners

**Migration Queries for Reference:**
```sql
-- Extract sires from legacy data
INSERT INTO ra_sires (id, name, created_at, updated_at)
SELECT sire_id, MIN(sire_name), MIN(created_at), MAX(updated_at)
FROM ra_runners
WHERE sire_id IS NOT NULL
GROUP BY sire_id;

-- Similar for dams and damsires
```

---

### 2. Primary Key Changes

**Problem:**
Primary keys changed from `{entity}_id` to `id`, but foreign keys still use `{entity}_id`.

**Example:**
```python
# OLD - ra_jockeys table
{
    'jockey_id': 'jky_123',  # Primary key
    'name': 'John Smith'
}

# NEW - ra_jockeys table
{
    'id': 'jky_123',  # Primary key (renamed)
    'name': 'John Smith'
}

# But in ra_runners (foreign key still uses jockey_id)
{
    'jockey_id': 'jky_123',  # Foreign key (unchanged)
    'horse_id': 'hrs_456'     # Foreign key (unchanged)
}
```

**Solution Required:**
- Update `upsert_batch()` `unique_key` parameters from `{entity}_id` to `id`
- Keep foreign key column names unchanged in runner/race records

**Files to Update:**
- `utils/supabase_client.py:121` - `insert_courses()` - Change `'course_id'` → `'id'`
- `utils/supabase_client.py:126` - `insert_horses()` - Change `'horse_id'` → `'id'`
- `utils/supabase_client.py:131` - `insert_jockeys()` - Change `'jockey_id'` → `'id'`
- `utils/supabase_client.py:136` - `insert_trainers()` - Change `'trainer_id'` → `'id'`
- `utils/supabase_client.py:141` - `insert_owners()` - Change `'owner_id'` → `'id'`
- `utils/supabase_client.py:151` - `insert_races()` - Change `'race_id'` → `'id'`
- `utils/supabase_client.py:161` - `insert_results()` - Change `'race_id'` → `'id'`
- `utils/supabase_client.py:177` - `insert_bookmakers()` - Change `'bookmaker_id'` → `'code'` (special case - uses `code` column)
- `utils/supabase_client.py:146` - `insert_pedigree()` - Keep as `'horse_id'` (compound key)

**Entity Record Updates:**
- Update `utils/entity_extractor.py:62-67` - jockeys: Change `'jockey_id'` → `'id'`
- Update `utils/entity_extractor.py:72-78` - trainers: Change `'trainer_id'` → `'id'`
- Update `utils/entity_extractor.py:84-89` - owners: Change `'owner_id'` → `'id'`
- Update `utils/entity_extractor.py:95-106` - horses: Change `'horse_id'` → `'id'`

---

### 3. Column Renames in `ra_races`

| Old Column | New Column | Type | Notes |
|------------|------------|------|-------|
| `race_date` | `date` | DATE | Race date field |
| `off_datetime` | `off_dt` | TIMESTAMP | Race start time |
| `distance_meters` | `distance_m` | INTEGER | Distance in meters |
| `prize_money` | `prize` | NUMERIC | Prize money |
| `big_race` | `is_big_race` | BOOLEAN | Big race flag |
| `race_type` | `type` | VARCHAR | Race type |
| `race_class` | `race_class` | VARCHAR | **UNCHANGED** |

**Files to Update:**
- `fetchers/races_fetcher.py:229` - Change `'race_date'` → `'date'`
- `fetchers/races_fetcher.py:230` - Change `'off_datetime'` → `'off_dt'`
- `fetchers/races_fetcher.py:233` - Change `'race_type'` → `'type'`
- `fetchers/races_fetcher.py:237` - Change `'distance_meters'` → `'distance_m'`
- `fetchers/races_fetcher.py:247` - Change `'prize_money'` → `'prize'`
- `fetchers/races_fetcher.py:249` - Change `'big_race'` → `'is_big_race'`
- `fetchers/results_fetcher.py:144` - Similar changes in results fetcher

**Also update `race_id` → `id` in race records:**
- `fetchers/races_fetcher.py:223` - Change `'race_id': race_id` → `'id': race_id`
- `fetchers/results_fetcher.py:140` - Same update

---

### 4. Column Renames in `ra_runners`

| Old Column | New Column | Type | Notes |
|------------|------------|------|-------|
| `official_rating` | `ofr` | INTEGER | Official rating |
| `tsr` | `ts` | INTEGER | Timeform rating |
| `weight_stones_lbs` | `weight_st_lbs` | VARCHAR | UK weight format |

**Files to Update:**
- `fetchers/races_fetcher.py` (search for `official_rating`, `tsr`, `weight_stones_lbs`)
- `fetchers/results_fetcher.py` (same search)

**Note:** The migration doc shows `ofr` is the NEW name for `official_rating`.

---

### 5. Column Renames in `ra_horses`

The `ra_horses` table now has a simpler structure. Based on migration doc line 288-313:

**Files to Update:**
- `utils/entity_extractor.py:95-106` - Horse records should use `id` instead of `horse_id`

```python
# NEW format
horse_record = {
    'id': horse_id,  # Changed from 'horse_id'
    'name': horse_name,
    'sex': runner.get('sex'),
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}
```

---

### 6. Statistics Fields (NEW REQUIREMENT)

Three new workers are needed to populate statistics:

#### A. Jockey Statistics Worker
**API Endpoint:** `/jockeys/{jockey_id}/statistics`
**New Fields in `ra_jockeys`:**
- `total_rides` (INTEGER)
- `total_wins` (INTEGER)
- `total_places` (INTEGER)
- `total_seconds` (INTEGER)
- `total_thirds` (INTEGER)
- `win_rate` (NUMERIC(5,2))
- `place_rate` (NUMERIC(5,2))
- `stats_updated_at` (TIMESTAMP)

**Implementation:** Create `fetchers/jockeys_stats_fetcher.py`

#### B. Trainer Statistics Worker
**API Endpoint:** `/trainers/{trainer_id}/statistics`
**New Fields in `ra_trainers`:**
- `total_runners` (INTEGER)
- `total_wins` (INTEGER)
- `total_places` (INTEGER)
- `total_seconds` (INTEGER)
- `total_thirds` (INTEGER)
- `win_rate` (NUMERIC(5,2))
- `place_rate` (NUMERIC(5,2))
- `recent_14d_runs` (INTEGER)
- `recent_14d_wins` (INTEGER)
- `recent_14d_win_rate` (NUMERIC(5,2))
- `stats_updated_at` (TIMESTAMP)

**Implementation:** Create `fetchers/trainers_stats_fetcher.py`

#### C. Owner Statistics Worker
**API Endpoint:** `/owners/{owner_id}/statistics`
**New Fields in `ra_owners`:**
- `total_horses` (INTEGER)
- `total_runners` (INTEGER)
- `total_wins` (INTEGER)
- `total_places` (INTEGER)
- `total_seconds` (INTEGER)
- `total_thirds` (INTEGER)
- `win_rate` (NUMERIC(5,2))
- `place_rate` (NUMERIC(5,2))
- `active_last_30d` (BOOLEAN)
- `stats_updated_at` (TIMESTAMP)

**Implementation:** Create `fetchers/owners_stats_fetcher.py`

**Scheduler Update Required:**
- Add daily cron jobs for all three statistics workers
- See migration doc line 864 for setup instructions

---

### 7. Bookmakers Table Change

**Change:**
Primary key changed from `bookmaker_id` to `code`, with auto-increment `id`.

**Migration doc shows:**
```sql
| id | code | name | type | is_active |
|----|------|------|------|-----------|
| 1  | bet365 | Bet365 | online | true |
```

**Files to Update:**
- `utils/supabase_client.py:177` - Change unique key to `'code'` instead of `'bookmaker_id'`
- `fetchers/bookmakers_fetcher.py` - Update record format to use `code` field

---

## Detailed File-by-File Changes

### File 1: `utils/supabase_client.py`

**Changes Required:**

1. **Update primary key parameters** (lines 118-178):
```python
# BEFORE
def insert_courses(self, courses: List[Dict]) -> Dict:
    return self.upsert_batch('ra_courses', courses, 'course_id')

def insert_horses(self, horses: List[Dict]) -> Dict:
    return self.upsert_batch('ra_horses', horses, 'horse_id')

def insert_jockeys(self, jockeys: List[Dict]) -> Dict:
    return self.upsert_batch('ra_jockeys', jockeys, 'jockey_id')

def insert_trainers(self, trainers: List[Dict]) -> Dict:
    return self.upsert_batch('ra_trainers', trainers, 'trainer_id')

def insert_owners(self, owners: List[Dict]) -> Dict:
    return self.upsert_batch('ra_owners', owners, 'owner_id')

def insert_races(self, races: List[Dict]) -> Dict:
    return self.upsert_batch('ra_races', races, 'race_id')

def insert_results(self, results: List[Dict]) -> Dict:
    return self.upsert_batch('ra_results', results, 'race_id')

def insert_bookmakers(self, bookmakers: List[Dict]) -> Dict:
    return self.upsert_batch('ra_bookmakers', bookmakers, 'bookmaker_id')

# AFTER
def insert_courses(self, courses: List[Dict]) -> Dict:
    return self.upsert_batch('ra_courses', courses, 'id')

def insert_horses(self, horses: List[Dict]) -> Dict:
    return self.upsert_batch('ra_horses', horses, 'id')

def insert_jockeys(self, jockeys: List[Dict]) -> Dict:
    return self.upsert_batch('ra_jockeys', jockeys, 'id')

def insert_trainers(self, trainers: List[Dict]) -> Dict:
    return self.upsert_batch('ra_trainers', trainers, 'id')

def insert_owners(self, owners: List[Dict]) -> Dict:
    return self.upsert_batch('ra_owners', owners, 'id')

def insert_races(self, races: List[Dict]) -> Dict:
    return self.upsert_batch('ra_races', races, 'id')

def insert_results(self, results: List[Dict]) -> Dict:
    return self.upsert_batch('ra_results', results, 'id')

def insert_bookmakers(self, bookmakers: List[Dict]) -> Dict:
    return self.upsert_batch('ra_bookmakers', bookmakers, 'code')  # Special: uses 'code' not 'id'
```

2. **Add new breeding table methods** (insert after line 178):
```python
def insert_sires(self, sires: List[Dict]) -> Dict:
    """Insert/update sires"""
    logger.info(f"Inserting {len(sires)} sires")
    return self.upsert_batch('ra_sires', sires, 'id')

def insert_dams(self, dams: List[Dict]) -> Dict:
    """Insert/update dams"""
    logger.info(f"Inserting {len(dams)} dams")
    return self.upsert_batch('ra_dams', dams, 'id')

def insert_damsires(self, damsires: List[Dict]) -> Dict:
    """Insert/update damsires"""
    logger.info(f"Inserting {len(damsires)} damsires")
    return self.upsert_batch('ra_damsires', damsires, 'id')
```

3. **Update `get_existing_ids()` calls** (line 191):
```python
# This method is generic and should work with any id_column, so no changes needed
# BUT callers may need updates - check all uses
```

---

### File 2: `utils/entity_extractor.py`

**Changes Required:**

1. **Update entity record keys to use `id`** (lines 62-106):
```python
# BEFORE
jockeys[jockey_id] = {
    'jockey_id': jockey_id,
    'name': jockey_name,
    ...
}

trainers[trainer_id] = {
    'trainer_id': trainer_id,
    'name': trainer_name,
    ...
}

owners[owner_id] = {
    'owner_id': owner_id,
    'name': owner_name,
    ...
}

horses[horse_id] = {
    'horse_id': horse_id,
    'name': horse_name,
    ...
}

# AFTER
jockeys[jockey_id] = {
    'id': jockey_id,  # Changed
    'name': jockey_name,
    ...
}

trainers[trainer_id] = {
    'id': trainer_id,  # Changed
    'name': trainer_name,
    ...
}

owners[owner_id] = {
    'id': owner_id,  # Changed
    'name': owner_name,
    ...
}

horses[horse_id] = {
    'id': horse_id,  # Changed
    'name': horse_name,
    ...
}
```

2. **Add breeding entity extraction** (new method after line 113):
```python
def extract_breeding_from_runners(self, runner_records: List[Dict]) -> Dict[str, List[Dict]]:
    """
    Extract unique breeding entities (sires, dams, damsires) from runner records

    Args:
        runner_records: List of runner dictionaries

    Returns:
        Dictionary with breeding entity types as keys and lists of entity records as values
    """
    sires = {}
    dams = {}
    damsires = {}

    for runner in runner_records:
        # Extract sire
        sire_id = runner.get('sire_id')
        sire_name = runner.get('sire_name')
        if sire_id and sire_name and sire_id not in sires:
            sires[sire_id] = {
                'id': sire_id,
                'name': sire_name,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

        # Extract dam
        dam_id = runner.get('dam_id')
        dam_name = runner.get('dam_name')
        if dam_id and dam_name and dam_id not in dams:
            dams[dam_id] = {
                'id': dam_id,
                'name': dam_name,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

        # Extract damsire
        damsire_id = runner.get('damsire_id')
        damsire_name = runner.get('damsire_name')
        if damsire_id and damsire_name and damsire_id not in damsires:
            damsires[damsire_id] = {
                'id': damsire_id,
                'name': damsire_name,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

    return {
        'sires': list(sires.values()),
        'dams': list(dams.values()),
        'damsires': list(damsires.values())
    }
```

3. **Update `store_entities()` to store breeding entities** (insert at line 188):
```python
# Store sires
sires = entities.get('sires', [])
if sires:
    try:
        db_result = self.db_client.insert_sires(sires)
        results['sires'] = db_result
        self.stats['sires'] += db_result.get('inserted', 0)
        logger.info(f"Stored {db_result.get('inserted', 0)} sires")
    except Exception as e:
        logger.error(f"Failed to store sires: {e}")
        results['sires'] = {'error': str(e)}

# Store dams
dams = entities.get('dams', [])
if dams:
    try:
        db_result = self.db_client.insert_dams(dams)
        results['dams'] = db_result
        self.stats['dams'] += db_result.get('inserted', 0)
        logger.info(f"Stored {db_result.get('inserted', 0)} dams")
    except Exception as e:
        logger.error(f"Failed to store dams: {e}")
        results['dams'] = {'error': str(e)}

# Store damsires
damsires = entities.get('damsires', [])
if damsires:
    try:
        db_result = self.db_client.insert_damsires(damsires)
        results['damsires'] = db_result
        self.stats['damsires'] += db_result.get('inserted', 0)
        logger.info(f"Stored {db_result.get('inserted', 0)} damsires")
    except Exception as e:
        logger.error(f"Failed to store damsires: {e}")
        results['damsires'] = {'error': str(e)}
```

4. **Update `_get_existing_horse_ids()` to use correct column** (line 200):
```python
# BEFORE
result = self.db_client.client.table('ra_horses').select('horse_id').execute()
return {row['horse_id'] for row in result.data}

# AFTER
result = self.db_client.client.table('ra_horses').select('id').execute()
return {row['id'] for row in result.data}
```

5. **Update enriched horse record format** (line 277-286):
```python
# BEFORE
enriched_horse = {
    **horse,  # Keep basic data
    'dob': horse_pro.get('dob'),
    ...
}

# AFTER - horse already has 'id' from extract_from_runners(), so this should work
enriched_horse = {
    **horse,  # Keep basic data (includes 'id' not 'horse_id')
    'dob': horse_pro.get('dob'),
    ...
}
```

6. **Update `extract_and_store_from_runners()` to handle breeding** (line 322-343):
```python
def extract_and_store_from_runners(self, runner_records: List[Dict]) -> Dict:
    """
    Extract entities from runners and store them in database
    """
    # Extract people and horses
    entities = self.extract_from_runners(runner_records)

    # Extract breeding entities
    breeding_entities = self.extract_breeding_from_runners(runner_records)

    # Merge breeding into entities
    entities.update(breeding_entities)

    # Log summary
    logger.info(f"Extracted {len(entities['jockeys'])} unique jockeys")
    logger.info(f"Extracted {len(entities['trainers'])} unique trainers")
    logger.info(f"Extracted {len(entities['owners'])} unique owners")
    logger.info(f"Extracted {len(entities['horses'])} unique horses")
    logger.info(f"Extracted {len(entities['sires'])} unique sires")
    logger.info(f"Extracted {len(entities['dams'])} unique dams")
    logger.info(f"Extracted {len(entities['damsires'])} unique damsires")

    # Store in database
    results = self.store_entities(entities)

    return results
```

---

### File 3: `fetchers/races_fetcher.py`

**Changes Required:**

1. **Update race record field names** (lines 222-255):
```python
# BEFORE
race_record = {
    'race_id': race_id,
    'race_date': racecard.get('date'),
    'off_datetime': racecard.get('off_dt'),
    'race_type': racecard.get('type'),
    'distance_meters': racecard.get('dist_m'),
    'prize_money': parse_prize_money(racecard.get('prize')),
    'big_race': racecard.get('big_race', False),
    ...
}

# AFTER
race_record = {
    'id': race_id,  # Changed from 'race_id'
    'date': racecard.get('date'),  # Changed from 'race_date'
    'off_dt': racecard.get('off_dt'),  # Changed from 'off_datetime'
    'type': racecard.get('type'),  # Changed from 'race_type'
    'distance_m': racecard.get('dist_m'),  # Changed from 'distance_meters'
    'prize': parse_prize_money(racecard.get('prize')),  # Changed from 'prize_money'
    'is_big_race': racecard.get('big_race', False),  # Changed from 'big_race'
    ...
}
```

2. **Remove sire_name, dam_name, damsire_name from runner records** (lines 298-304):
```python
# BEFORE (lines 298-304)
'sire_id': runner.get('sire_id'),
'sire_name': runner.get('sire'),
'dam_id': runner.get('dam_id'),

# AFTER - Keep IDs, remove names
'sire_id': runner.get('sire_id'),
'dam_id': runner.get('dam_id'),
'damsire_id': runner.get('damsire_id'),
# sire_name, dam_name, damsire_name will be extracted separately for breeding tables
```

3. **BUT - still need names for breeding extraction!**
   Keep temporary fields for entity extractor:
```python
runner_record = {
    # ... existing fields ...
    'sire_id': runner.get('sire_id'),
    'sire_name': runner.get('sire'),  # Keep for breeding entity extraction
    'dam_id': runner.get('dam_id'),
    'dam_name': runner.get('dam'),  # Keep for breeding entity extraction
    'damsire_id': runner.get('damsire_id'),
    'damsire_name': runner.get('damsire'),  # Keep for breeding entity extraction
    # ... rest ...
}
```

Then filter them out before database insert OR update the database client to filter them.

**RECOMMENDATION:** Update `supabase_client.py` to add breeding columns to `DROPPED_RUNNER_COLUMNS`:
```python
DROPPED_RUNNER_COLUMNS = {
    # ... existing ...
    'sire_name',  # Moved to ra_sires table
    'dam_name',  # Moved to ra_dams table
    'damsire_name',  # Moved to ra_damsires table
}
```

---

### File 4: `fetchers/results_fetcher.py`

**Changes Required:**

Similar to `races_fetcher.py`:

1. **Update race record field names** (lines 140-159)
2. **Remove breeding name fields from runners** (similar to races_fetcher)
3. **Update `_prepare_runner_records()` method** to use new schema

---

### File 5: `fetchers/bookmakers_fetcher.py`

**Changes Required:**

1. **Update bookmaker record format** to use `code` and `id`:
```python
# BEFORE
bookmaker_record = {
    'bookmaker_id': bookmaker.get('code'),
    'bookmaker_name': bookmaker.get('name'),
    ...
}

# AFTER
bookmaker_record = {
    'code': bookmaker.get('code'),  # Primary unique key
    'name': bookmaker.get('name'),
    'type': bookmaker.get('type'),  # NEW field
    'is_active': bookmaker.get('active'),
    'created_at': datetime.utcnow().isoformat()
}
# Note: 'id' is auto-increment, don't include in insert
```

---

## Testing Plan

### Phase 1: Unit Tests
1. Test `utils/supabase_client.py` insert methods with new schema
2. Test `utils/entity_extractor.py` breeding extraction
3. Test primary key changes

### Phase 2: Integration Tests
1. Run `fetchers/races_fetcher.py --test` - verify race and runner inserts
2. Run `fetchers/results_fetcher.py --test` - verify result inserts
3. Check breeding tables populated correctly

### Phase 3: Validation Queries
```sql
-- Check breeding table coverage
SELECT
    'Sires' as entity,
    COUNT(*) as count
FROM ra_sires
UNION ALL
SELECT 'Dams', COUNT(*) FROM ra_dams
UNION ALL
SELECT 'Damsires', COUNT(*) FROM ra_damsires;

-- Check orphan runners (missing breeding FKs)
SELECT COUNT(*)
FROM ra_runners r
WHERE r.sire_id IS NOT NULL
AND NOT EXISTS (SELECT 1 FROM ra_sires WHERE id = r.sire_id);
```

---

## Implementation Priority

### Priority 1 (CRITICAL - Breaks current system):
1. ✅ Update `utils/supabase_client.py` - Change primary keys to `id`
2. ✅ Update `utils/supabase_client.py` - Add breeding table insert methods
3. ✅ Update `utils/entity_extractor.py` - Change entity records to use `id`
4. ✅ Update `utils/entity_extractor.py` - Add breeding entity extraction
5. ✅ Update `fetchers/races_fetcher.py` - Column renames + breeding handling
6. ✅ Update `fetchers/results_fetcher.py` - Column renames + breeding handling

### Priority 2 (HIGH - Missing functionality):
7. ⬜ Create `fetchers/jockeys_stats_fetcher.py`
8. ⬜ Create `fetchers/trainers_stats_fetcher.py`
9. ⬜ Create `fetchers/owners_stats_fetcher.py`
10. ⬜ Update `main.py` to call statistics fetchers
11. ⬜ Update scheduler to run statistics workers daily

### Priority 3 (MEDIUM - Edge cases):
12. ⬜ Update `fetchers/bookmakers_fetcher.py` - `code` field handling
13. ⬜ Update all test files for new schema
14. ⬜ Update documentation (CLAUDE.md, docs/*)

---

## Database Connection Update

**IMPORTANT:** The migration uses Session Pooler for IPv4 compatibility.

Update `.env.local`:
```bash
# Use Session Pooler (IPv4 compatible)
DATABASE_URL=postgresql://postgres.amsjvmlaknnvppxsgpfk:R0pMr1L58WH3hUkpVtPcwYnw@aws-0-eu-west-2.pooler.supabase.com:5432/postgres

# DO NOT use direct connection (IPv6 only)
# DATABASE_URL=postgresql://postgres.amsjvmlaknnvppxsgpfk:[PASSWORD]@db.amsjvmlaknnvppxsgpfk.supabase.co:5432/postgres
```

---

## Risk Assessment

### High Risk:
- **Breeding data loss** if not extracted properly - MUST test thoroughly
- **Primary key mismatches** causing upsert failures
- **Foreign key violations** if breeding tables not populated first

### Medium Risk:
- **Column rename mismatches** causing insert failures
- **Statistics fields** being NULL (acceptable - can be backfilled)

### Low Risk:
- **Bookmaker code field** - only 19 records, easy to fix
- **Test file updates** - isolated impact

---

## Rollback Plan

If issues occur:
1. Do NOT drop the new `ra_sires`, `ra_dams`, `ra_damsires` tables
2. Keep the normalized schema - it's better long-term
3. Fix the workers incrementally
4. Use the validation queries to identify gaps

---

## Questions to Resolve

1. **Should we drop sire_name/dam_name/damsire_name from ra_runners entirely?**
   - ✅ YES - Migration doc shows they're removed (lines 495-541)
   - Store in breeding tables only
   - JOIN when needed for queries

2. **How to handle existing data in ra_runners with breeding names?**
   - Migration already handled this (lines 359-441)
   - Breeding tables populated from legacy data
   - Safe to proceed with new inserts

3. **Do we need to update ra_horse_pedigree table structure?**
   - Check current schema vs migration doc
   - May need to update FK references

---

## Next Steps

1. Read this document thoroughly
2. Start with Priority 1 changes
3. Test each file after updating
4. Run validation queries
5. Move to Priority 2 (statistics workers)

---

**End of Refactoring Plan**
