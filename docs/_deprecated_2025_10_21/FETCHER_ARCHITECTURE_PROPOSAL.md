# Fetcher Architecture Proposal - Consolidated Scripts

**Date:** 2025-10-19
**Purpose:** Consolidate 8 individual fetchers into 2 grouped scripts

---

## Current Problem

**8 separate fetcher files:**
```
fetchers/bookmakers_fetcher.py
fetchers/courses_fetcher.py
fetchers/horses_fetcher.py
fetchers/jockeys_fetcher.py
fetchers/trainers_fetcher.py
fetchers/owners_fetcher.py
fetchers/races_fetcher.py
fetchers/results_fetcher.py
```

**Issues:**
- ❌ Code duplication
- ❌ Hard to maintain consistency
- ❌ No clear grouping by update frequency
- ❌ Difficult to understand data flow

---

## Proposed Solution: 2 Master Scripts

### Script 1: `masters_fetcher.py`
**Purpose:** Fetch all master/reference data (ra_mst_* tables)
**Update Frequency:** Weekly (people/pedigree), Monthly (reference)
**Tables Managed:** 10 tables

### Script 2: `events_fetcher.py`
**Purpose:** Fetch event/transaction data (ra_* tables)
**Update Frequency:** Daily
**Tables Managed:** 2 main tables (races, runners)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Main Orchestrator                         │
│                      (main.py)                               │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ├─── Weekly ───► MastersFetcher
                 │                 └─ People (jockeys, trainers, owners)
                 │                 └─ Horses (horses, sires, dams, damsires)
                 │
                 ├─── Monthly ──► MastersFetcher
                 │                 └─ Reference (bookmakers, courses, regions)
                 │
                 └─── Daily ────► EventsFetcher
                                   └─ Races (racecards)
                                   └─ Results
                                   └─ Triggers entity extraction → MastersFetcher
```

---

## Detailed Design

### 1. MastersFetcher (masters_fetcher.py)

**Responsibility:** Maintain all master/reference data

**Features:**
- Grouped entity fetching (people, horses, reference)
- Bulk operations for efficiency
- Entity enrichment (horses from races)
- Pedigree extraction and storage

**Methods:**
```python
class MastersFetcher:
    def __init__(self):
        self.api_client = RacingAPIClient(...)
        self.db_client = SupabaseReferenceClient(...)

    # Reference data (monthly)
    def fetch_bookmakers(self) -> Dict:
        """Fetch all bookmakers"""
        pass

    def fetch_courses(self) -> Dict:
        """Fetch all courses/venues"""
        pass

    def fetch_regions(self) -> Dict:
        """Fetch region reference data"""
        pass

    # People (weekly bulk)
    def fetch_jockeys(self, **config) -> Dict:
        """Fetch all jockeys (bulk)"""
        pass

    def fetch_trainers(self, **config) -> Dict:
        """Fetch all trainers (bulk)"""
        pass

    def fetch_owners(self, **config) -> Dict:
        """Fetch all owners (bulk)"""
        pass

    # Horses and pedigree (daily via entity extraction)
    def extract_and_enrich_horses(self, runners: List[Dict]) -> Dict:
        """
        Extract horses from race runners
        Enrich new horses with Pro endpoint
        Extract pedigree (sires, dams, damsires)
        """
        pass

    def store_pedigree(self, horses: List[Dict]) -> Dict:
        """Store sire, dam, damsire entities"""
        pass

    # Convenience methods
    def fetch_all_reference(self) -> Dict:
        """Fetch all reference data (monthly run)"""
        bookmakers = self.fetch_bookmakers()
        courses = self.fetch_courses()
        regions = self.fetch_regions()
        return {
            'bookmakers': bookmakers,
            'courses': courses,
            'regions': regions
        }

    def fetch_all_people(self) -> Dict:
        """Fetch all people (weekly run)"""
        jockeys = self.fetch_jockeys()
        trainers = self.fetch_trainers()
        owners = self.fetch_owners()
        return {
            'jockeys': jockeys,
            'trainers': trainers,
            'owners': owners
        }
```

**Tables Updated:**
```
ra_mst_bookmakers      (monthly)
ra_mst_courses         (monthly)
ra_mst_regions         (monthly)
ra_mst_jockeys         (weekly)
ra_mst_trainers        (weekly)
ra_mst_owners          (weekly)
ra_mst_horses          (daily via entity extraction)
ra_mst_sires           (daily via entity extraction)
ra_mst_dams            (daily via entity extraction)
ra_mst_damsires        (daily via entity extraction)
ra_rel_pedigree        (daily via entity extraction)
```

---

### 2. EventsFetcher (events_fetcher.py)

**Responsibility:** Fetch race events and results

**Features:**
- Racecards (pre-race)
- Results (post-race)
- Triggers entity extraction
- Updates runners with positions

**Methods:**
```python
class EventsFetcher:
    def __init__(self):
        self.api_client = RacingAPIClient(...)
        self.db_client = SupabaseReferenceClient(...)
        self.masters_fetcher = MastersFetcher()

    def fetch_racecards(self, date: str = None, **config) -> Dict:
        """
        Fetch racecards for a date
        Extract entities → masters_fetcher
        Store races + runners
        """
        # 1. Fetch racecards from API
        races = self.api_client.get_racecards(date)

        # 2. Extract runners
        all_runners = []
        for race in races:
            all_runners.extend(race.get('runners', []))

        # 3. Extract and enrich entities (horses, jockeys, trainers, owners)
        entity_stats = self.masters_fetcher.extract_and_enrich_horses(all_runners)

        # 4. Store races
        race_stats = self.db_client.insert_races(races)

        # 5. Store runners
        runner_stats = self.db_client.insert_runners(all_runners)

        return {
            'success': True,
            'races': race_stats,
            'runners': runner_stats,
            'entities': entity_stats
        }

    def fetch_results(self, start_date: str, end_date: str, **config) -> Dict:
        """
        Fetch results for date range
        Extract entities → masters_fetcher
        Update runners with positions
        """
        # Similar to racecards but with position data
        pass

    def fetch_daily(self, **config) -> Dict:
        """
        Convenience method: Fetch today's racecards
        """
        today = datetime.now().strftime('%Y-%m-%d')
        return self.fetch_racecards(today, **config)
```

**Tables Updated:**
```
ra_races               (daily)
ra_runners             (daily)
+ Triggers updates to all ra_mst_* tables via entity extraction
```

---

## Usage Examples

### Weekly Master Data Update
```bash
# Fetch all people (jockeys, trainers, owners)
python3 main.py --masters people

# Behind the scenes:
# - MastersFetcher.fetch_all_people()
# - Updates ra_mst_jockeys, ra_mst_trainers, ra_mst_owners
```

### Monthly Reference Update
```bash
# Fetch all reference data
python3 main.py --masters reference

# Behind the scenes:
# - MastersFetcher.fetch_all_reference()
# - Updates ra_mst_bookmakers, ra_mst_courses, ra_mst_regions
```

### Daily Events Update
```bash
# Fetch today's racecards
python3 main.py --events racecards

# Behind the scenes:
# - EventsFetcher.fetch_daily()
# - Extracts entities → MastersFetcher.extract_and_enrich_horses()
# - Updates ra_races, ra_runners
# - Updates ra_mst_horses, ra_mst_sires, ra_mst_dams, ra_mst_damsires
```

### Daily Results Update
```bash
# Fetch results from yesterday
python3 main.py --events results --days-back 1

# Behind the scenes:
# - EventsFetcher.fetch_results()
# - Updates ra_runners with positions
# - Extracts entities → MastersFetcher (if any new entities)
```

---

## Main.py Configuration

```python
# main.py

PRODUCTION_CONFIGS = {
    # Monthly: Reference data
    'masters_reference': {
        'type': 'reference',  # bookmakers, courses, regions
        'description': 'Monthly reference data update'
    },

    # Weekly: People
    'masters_people': {
        'type': 'people',  # jockeys, trainers, owners
        'description': 'Weekly people data update'
    },

    # Daily: Racecards
    'events_racecards': {
        'date': 'today',
        'region_codes': ['gb', 'ire'],
        'description': 'Daily racecards fetch'
    },

    # Daily: Results
    'events_results': {
        'days_back': 1,
        'region_codes': ['gb', 'ire'],
        'description': 'Daily results fetch'
    }
}

FETCHERS = {
    'masters': MastersFetcher,
    'events': EventsFetcher
}
```

---

## Production Schedule

```bash
# Monthly (1st of month, 2 AM)
0 2 1 * * python3 main.py --masters reference

# Weekly (Sunday, 2 AM)
0 2 * * 0 python3 main.py --masters people

# Daily (6 AM - before racing)
0 6 * * * python3 main.py --events racecards

# Daily (11 PM - after racing)
0 23 * * * python3 main.py --events results --days-back 1
```

---

## Benefits of This Approach

### 1. Clear Separation of Concerns
- **Masters:** Reference data that changes slowly
- **Events:** Transaction data that changes daily

### 2. Reduced Code Duplication
- Common logic shared across similar entities
- Single place for entity extraction
- Unified error handling

### 3. Better Performance
- Bulk operations for people
- Efficient entity extraction
- Reduced API calls (smart enrichment)

### 4. Easier Maintenance
- 2 files instead of 8
- Clear grouping by update frequency
- Simpler to understand data flow

### 5. Flexible Scheduling
- Run masters weekly/monthly
- Run events daily
- Independent execution

---

## Migration Path

### Phase 1: Create New Fetchers (No Disruption)
1. ✅ Create `fetchers/masters_fetcher.py`
2. ✅ Create `fetchers/events_fetcher.py`
3. ✅ Test with `--test` mode
4. ✅ Validate data quality

### Phase 2: Update Main.py
1. ✅ Add new fetchers to `FETCHERS` registry
2. ✅ Add new configs to `PRODUCTION_CONFIGS`
3. ✅ Keep old fetchers available (backward compatibility)

### Phase 3: Transition Period (Parallel)
1. ✅ Run new fetchers alongside old ones
2. ✅ Compare data outputs
3. ✅ Verify no regressions

### Phase 4: Deprecate Old Fetchers
1. ✅ Move old fetchers to `_deprecated/`
2. ✅ Update documentation
3. ✅ Remove from production schedule

---

## File Structure

```
DarkHorses-Masters-Workers/
├── fetchers/
│   ├── masters_fetcher.py          # NEW - All ra_mst_* tables
│   ├── events_fetcher.py           # NEW - All ra_* event tables
│   └── statistics_fetcher.py       # EXISTING - Statistics updates
│
├── _deprecated/
│   ├── bookmakers_fetcher.py       # OLD
│   ├── courses_fetcher.py          # OLD
│   ├── horses_fetcher.py           # OLD
│   ├── jockeys_fetcher.py          # OLD
│   ├── trainers_fetcher.py         # OLD
│   ├── owners_fetcher.py           # OLD
│   ├── races_fetcher.py            # OLD
│   └── results_fetcher.py          # OLD
│
└── main.py                         # UPDATED - New fetcher registry
```

---

## Code Reuse Strategy

### Shared Logic (Keep)
```
utils/api_client.py         # API calls (unchanged)
utils/supabase_client.py    # DB operations (table names updated)
utils/entity_extractor.py   # Entity extraction (integrated into MastersFetcher)
utils/logger.py             # Logging (unchanged)
```

### Migrated Logic
```
OLD: fetchers/races_fetcher.py → NEW: events_fetcher.fetch_racecards()
OLD: fetchers/results_fetcher.py → NEW: events_fetcher.fetch_results()
OLD: fetchers/jockeys_fetcher.py → NEW: masters_fetcher.fetch_jockeys()
OLD: fetchers/trainers_fetcher.py → NEW: masters_fetcher.fetch_trainers()
OLD: fetchers/owners_fetcher.py → NEW: masters_fetcher.fetch_owners()
OLD: fetchers/horses_fetcher.py → NEW: masters_fetcher.extract_and_enrich_horses()
OLD: fetchers/bookmakers_fetcher.py → NEW: masters_fetcher.fetch_bookmakers()
OLD: fetchers/courses_fetcher.py → NEW: masters_fetcher.fetch_courses()
```

---

## Estimated Effort

### Development
- **masters_fetcher.py:** 6-8 hours
- **events_fetcher.py:** 6-8 hours
- **Database client updates:** 2-3 hours
- **Main.py updates:** 1-2 hours

### Testing
- **Unit tests:** 4-6 hours
- **Integration tests:** 4-6 hours
- **Production validation:** 2-3 hours

**Total:** ~25-35 hours

---

## Questions Before We Start

1. **Entity extraction:** Should `MastersFetcher` handle entity extraction or keep `EntityExtractor` separate?

2. **API methods:** Move all API calls into the fetchers or keep `api_client.py` as thin wrapper?

3. **Error handling:** Continue current approach (log + return dict) or raise exceptions?

4. **Testing:** Create new test files or update existing ones?

---

## Next Steps

1. ✅ Run migration SQL (rename tables)
2. ✅ Create `masters_fetcher.py`
3. ✅ Create `events_fetcher.py`
4. ✅ Update `supabase_client.py` (table names)
5. ✅ Update `main.py` (new fetchers)
6. ✅ Test with `--test` mode
7. ✅ Deploy to production

**Ready to proceed with implementation?**
