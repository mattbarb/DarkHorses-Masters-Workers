# Database Schema Audit - Quick Fix Checklist

**Last Updated:** 2025-10-14

Use this checklist to track implementation progress.

---

## P0 - CRITICAL (Do Immediately)

### ✓ Task 1: Enable Position Data Extraction
**File:** `fetchers/results_fetcher.py`
**Line:** ~195 (in `fetch_and_store()` method)
**Action:** Add/uncomment runner extraction code
**Effort:** 1 hour
**Test:** Run on 2025-10-01, check position field populated

**Code to add:**
```python
# After race insertion, add this:
if all_runners:
    logger.info(f"Inserting {len(all_runners)} runner records with position data...")
    runner_records = self._prepare_runner_records(all_results)
    if runner_records:
        runner_stats = self.db_client.insert_runners(runner_records)
        results_dict['runners'] = runner_stats
        logger.info(f"Runners inserted: {runner_stats}")
```

**Status:** [ ] Not Started [ ] In Progress [ ] Done [ ] Tested

---

### ✓ Task 2: Backfill Position Data
**Script:** Create `scripts/backfill_position_data.py`
**Action:** Re-run results fetcher for last 12 months
**Effort:** 3 hours runtime
**Test:** Check position NULL percentage drops from 100% to <10%

**Command:**
```bash
python3 scripts/backfill_position_data.py \
    --start-date 2024-10-01 \
    --end-date 2025-10-14 \
    --region gb,ire
```

**Status:** [ ] Not Started [ ] In Progress [ ] Done [ ] Verified

---

## P1 - HIGH (This Week)

### ✓ Task 3: Fix Distance Meters Extraction
**File:** `fetchers/results_fetcher.py`
**Line:** ~144 (in race_record dict)
**Action:** Verify dist_m extraction
**Effort:** 30 minutes

**Current code:**
```python
'distance': race_data.get('dist_m'),  # Should be distance_meters
'distance_f': race_data.get('dist_f'),
```

**Fix:**
```python
'distance': race_data.get('dist_f'),  # Furlongs
'distance_meters': race_data.get('dist_m'),  # Meters
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 4: Fix Prize Money Parsing
**File:** `fetchers/races_fetcher.py` & `fetchers/results_fetcher.py`
**Line:** Multiple locations
**Action:** Use parse_prize_money() function
**Effort:** 1 hour

**Code already exists in utils/position_parser.py:**
```python
from utils.position_parser import parse_prize_money

# In race_record:
'prize_money': parse_prize_money(racecard.get('prize')),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 5: Extract Weather & Track Conditions
**File:** `fetchers/races_fetcher.py`
**Line:** ~240 (in race_record dict)
**Action:** Update field mappings
**Effort:** 1 hour

**Current:**
```python
'track_condition': racecard.get('going_detailed'),  # NULL
'weather_conditions': racecard.get('weather'),  # NULL
```

**Fix:** (Already correct, just verify extraction)

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 6: Populate Horse DOB
**File:** `utils/entity_extractor.py`
**Line:** ~95 (in extract_from_runners)
**Action:** Add dob to horse record
**Effort:** 30 minutes

**Add to horse_record:**
```python
'dob': runner.get('dob'),
'sex_code': runner.get('sex_code'),
'colour': runner.get('colour'),
'region': runner.get('region'),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 7: Populate Trainer Location
**File:** `utils/entity_extractor.py`
**Line:** ~65 (in trainers section)
**Action:** Add location to trainer record
**Effort:** 30 minutes

**Add to trainer_record:**
```python
'location': runner.get('trainer_location'),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 8: Extract Trainer 14-Day Stats
**File:** `fetchers/races_fetcher.py`
**Line:** ~330 (in runner_record dict)
**Action:** Add trainer_14_days_data field
**Effort:** 1 hour

**Add to runner_record:**
```python
'trainer_14_days_data': runner.get('trainer_14_days'),  # JSONB
'trainer_location': runner.get('trainer_location'),
'trainer_rtf': runner.get('trainer_rtf'),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 9: Extract Days Since Last Run
**File:** `fetchers/races_fetcher.py`
**Line:** ~320 (in runner_record dict)
**Action:** Parse last_run field
**Effort:** 30 minutes

**Add to runner_record:**
```python
'days_since_last_run': parse_int_field(runner.get('last_run')),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 10: Fix Headgear Population
**File:** `fetchers/races_fetcher.py`
**Line:** ~305 (in runner_record dict)
**Action:** Verify headgear extraction
**Effort:** 30 minutes
**Current:** 57% NULL (should be 10% NULL)

**Current code (verify it's working):**
```python
'headgear': runner.get('headgear'),
'blinkers': 'b' in (runner.get('headgear_run') or '').lower(),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

## P2 - MEDIUM (Next 2 Weeks)

### ✓ Task 11: Run Migration 007
**File:** `migrations/007_add_entity_table_enhancements.sql`
**Action:** Add statistics fields to entity tables
**Effort:** 5 minutes

**Command:**
```bash
psql $SUPABASE_URL -f migrations/007_add_entity_table_enhancements.sql
```

**Status:** [ ] Not Started [ ] Done [ ] Verified

---

### ✓ Task 12: Calculate Entity Statistics
**File:** Create `scripts/calculate_entity_statistics.py`
**Action:** Calculate jockey/trainer/owner stats from runners
**Effort:** 4 hours

**SQL to run:**
```sql
SELECT * FROM update_entity_statistics();
```

**Status:** [ ] Not Started [ ] Done [ ] Verified

---

### ✓ Task 13: Extract Pedigree Regions
**File:** `fetchers/races_fetcher.py`
**Line:** ~310 (in runner_record dict)
**Action:** Add pedigree region fields
**Effort:** 1 hour

**Add to runner_record:**
```python
'dam_region': runner.get('dam_region'),
'sire_region': runner.get('sire_region'),
'damsire_region': runner.get('damsire_region'),
```

**Status:** [ ] Not Started [ ] Done [ ] Tested

---

### ✓ Task 14: Investigate Low Runner Count
**Action:** Debug why only 2.78 runners/race
**Effort:** 2-4 hours
**Expected:** 8-12 runners/race

**Investigation steps:**
1. Check API response - does it include all runners?
2. Check filtering logic - are we removing valid runners?
3. Check extraction logic - are we skipping runners?
4. Compare race with 2 runners vs API data

**Status:** [ ] Not Started [ ] In Progress [ ] Resolved

---

## Testing & Validation

### ✓ Test 1: Position Data Populated
**Query:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(position) as with_position,
    ROUND(100.0 * COUNT(position) / COUNT(*), 2) as percentage
FROM ra_runners;
```

**Expected:** percentage > 90%
**Status:** [ ] Not Run [ ] Failed [ ] Passed

---

### ✓ Test 2: Horse DOB Populated
**Query:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(dob) as with_dob,
    ROUND(100.0 * COUNT(dob) / COUNT(*), 2) as percentage
FROM ra_horses;
```

**Expected:** percentage > 90%
**Status:** [ ] Not Run [ ] Failed [ ] Passed

---

### ✓ Test 3: Trainer Location Populated
**Query:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(location) as with_location,
    ROUND(100.0 * COUNT(location) / COUNT(*), 2) as percentage
FROM ra_trainers;
```

**Expected:** percentage > 80%
**Status:** [ ] Not Run [ ] Failed [ ] Passed

---

### ✓ Test 4: Distance & Prize Fixed
**Query:**
```sql
SELECT
    COUNT(*) as total,
    COUNT(distance_meters) as with_distance,
    COUNT(prize_money) as with_prize
FROM ra_races
WHERE race_date >= CURRENT_DATE - INTERVAL '30 days';
```

**Expected:** > 90% for both
**Status:** [ ] Not Run [ ] Failed [ ] Passed

---

### ✓ Test 5: ML Compilation Works
**Command:**
```bash
python3 compile_ml_data.py --race-date 2025-10-14 --test
```

**Expected:** No errors, win_rate > 0%
**Status:** [ ] Not Run [ ] Failed [ ] Passed

---

## Progress Tracking

**Overall Progress:**

P0 Tasks: [ ] 0/2 [ ] 1/2 [ ] 2/2 ✓
P1 Tasks: [ ] 0/8 [ ] 4/8 [ ] 8/8 ✓
P2 Tasks: [ ] 0/4 [ ] 2/4 [ ] 4/4 ✓

**Total Hours Spent:** _____ / 33.5 hours estimated

**Completion Date:** __________

---

## Success Criteria

### Week 1 (P0 + P1 Complete)
- [ ] Position data > 90% populated
- [ ] Win rates calculating correctly (not 0%)
- [ ] Horse DOB > 90% populated
- [ ] Trainer location > 80% populated
- [ ] Distance meters > 90% populated
- [ ] Prize money > 90% populated
- [ ] ML compilation successful
- [ ] No errors in fetchers

### Week 3 (P2 Complete)
- [ ] Entity statistics calculated
- [ ] All API fields being captured
- [ ] Runner count issue investigated
- [ ] All tests passing
- [ ] Documentation updated

---

## Notes & Issues

**Blockers:**


**Decisions Made:**


**Questions for Team:**


---

**Checklist maintained by:** _____________
**Last updated:** _____________
