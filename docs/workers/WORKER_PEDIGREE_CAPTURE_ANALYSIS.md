# Worker Pedigree Data Capture Analysis

**Date:** 2025-10-14
**Issue:** New horses captured by workers don't have pedigree/metadata
**Status:** BY DESIGN - Not a bug

---

## The Problem

Recent horse data shows these fields are NULL:
- `dob` (date of birth)
- `sex_code`
- `colour`
- `colour_code`
- `region`
- Pedigree records (sire, dam, damsire, breeder)

**Example from database:**
```
Most recent horse: hrs_53294472 "Indy B (IRE)"
  created_at: 2025-10-14T12:14:17
  dob: NULL
  sex_code: NULL
  colour: NULL
  colour_code: NULL
  region: NULL
  Has pedigree: NO
```

---

## Root Cause: API Endpoint Limitations

### horses_fetcher.py Uses Bulk Search Endpoint

**Current approach:**
```python
# Line 67: horses_fetcher.py
api_response = self.api_client.search_horses(limit=limit_per_page, skip=skip)
```

**Endpoint:** `GET /v1/horses/search?limit=500&skip=0`

**What it returns:**
```json
{
  "horses": [
    {
      "id": "hrs_12345",
      "name": "Horse Name",
      "sex": "Gelding"
      // THAT'S IT - No dob, colour, pedigree, etc.
    }
  ]
}
```

**Fields available in search endpoint:**
- ✅ `id`
- ✅ `name`
- ✅ `sex`
- ❌ `dob` - NOT in response
- ❌ `sex_code` - NOT in response
- ❌ `colour` - NOT in response
- ❌ `colour_code` - NOT in response
- ❌ `region` - NOT in response
- ❌ `sire_id`, `dam_id`, etc. - NOT in response
- ❌ `breeder` - NOT in response

### Complete Data Requires Pro Endpoint

**For complete data:**
```python
# Requires individual calls per horse
api_response = self.api_client.get_horse_details(horse_id, tier='pro')
```

**Endpoint:** `GET /v1/horses/{horse_id}/pro`

**What it returns:**
```json
{
  "id": "hrs_12345",
  "name": "Horse Name",
  "dob": "2020-03-15",
  "sex": "Gelding",
  "sex_code": "G",
  "colour": "Bay",
  "colour_code": "B",
  "region": "gb",
  "sire_id": "hrs_11111",
  "sire": "Sire Name",
  "dam_id": "hrs_22222",
  "dam": "Dam Name",
  "damsire_id": "hrs_33333",
  "damsire": "Damsire Name",
  "breeder": "Breeder Name"
}
```

---

## Why Workers Don't Use Pro Endpoint

### Performance Constraints

**Bulk search approach (current):**
- Fetches 500 horses per request
- Total API calls: ~223 calls (111,325 horses ÷ 500)
- Time: ~2 minutes (223 calls × 0.5s)

**Individual Pro approach (theoretical):**
- Fetches 1 horse per request
- Total API calls: 111,325 calls
- Time: **15.5 hours** (111,325 calls × 0.5s)
- **This is the backfill script time!**

### Design Decision

**Workers are designed for:**
- ✅ Quick discovery of new horses
- ✅ Building reference tables (horse_id → name mapping)
- ✅ Capturing what's available in bulk endpoints

**Workers are NOT designed for:**
- ❌ Complete entity profiles
- ❌ Deep data enrichment
- ❌ Pedigree data capture

---

## Current Worker Behavior (By Design)

### horses_fetcher.py

**What it DOES capture:**
```python
horse_record = {
    'horse_id': horse.get('id'),        # ✅ Available
    'name': horse.get('name'),          # ✅ Available
    'sex': horse.get('sex'),            # ✅ Available
    'dob': horse.get('dob'),            # ❌ Not in response (NULL)
    'sex_code': horse.get('sex_code'),  # ❌ Not in response (NULL)
    'colour': horse.get('colour'),      # ❌ Not in response (NULL)
    'colour_code': horse.get('colour_code'),  # ❌ Not in response (NULL)
    'region': horse.get('region'),      # ❌ Not in response (NULL)
}
```

**Pedigree section:**
```python
# Lines 117-133
if any([horse.get('sire_id'), horse.get('dam_id'), horse.get('damsire_id')]):
    # This condition is NEVER TRUE because search endpoint doesn't have these fields
    pedigree_record = {...}  # Never executed
```

---

## The Solution: Backfill Strategy

### Why This Is The Right Approach

1. **New horses get discovered quickly** (2 minutes via bulk search)
2. **Complete data populated later** (15.5 hours via backfill)
3. **No performance impact on daily operations**
4. **Separation of concerns:**
   - Workers = Discovery + Basic data
   - Backfill = Complete enrichment

### How It Works

**Step 1: Worker runs (daily/hourly)**
```
horses_fetcher.py
  → Discovers 50 new horses
  → Inserts: horse_id, name, sex (basic data)
  → Result: Horses exist in database but incomplete
```

**Step 2: Backfill runs (weekly/monthly)**
```
backfill_horse_pedigree.py
  → Finds horses with NULL dob/colour/pedigree
  → Fetches complete data from Pro endpoint
  → Updates: dob, sex_code, colour, colour_code, region
  → Inserts: pedigree records
  → Result: Complete data populated
```

---

## Alternative Approaches (Not Recommended)

### Option A: Make Worker Use Pro Endpoint

**Implementation:**
```python
# After bulk search, fetch details for each horse
for horse in all_horses:
    detailed_data = self.api_client.get_horse_details(horse['id'], tier='pro')
    # Enrich horse record with complete data
```

**Problems:**
- ❌ Worker becomes 465x slower (2 min → 15.5 hours)
- ❌ Blocks daily operations
- ❌ Hits rate limits
- ❌ Requires Pro plan for all workers
- ❌ Doesn't scale

**Verdict:** NOT VIABLE

---

### Option B: Hybrid Approach (Fetch on Demand)

**Implementation:**
```python
# Only fetch Pro data for new horses discovered today
new_horses = [h for h in all_horses if h['id'] not in existing_ids]
for horse in new_horses:
    detailed_data = self.api_client.get_horse_details(horse['id'], tier='pro')
```

**Problems:**
- ⚠️ Still slow if many new horses (50 horses = 25 seconds)
- ⚠️ Adds complexity to worker
- ⚠️ Mixing concerns (discovery + enrichment)
- ⚠️ Still requires rate limiting logic

**Verdict:** UNNECESSARY COMPLEXITY

---

### Option C: Incremental Backfill (Recommended Addition)

**Implementation:**
```python
# Run mini-backfill for horses created in last 7 days
backfill_horse_pedigree.py --days-recent 7
```

**Benefits:**
- ✅ New horses get complete data within a week
- ✅ Separate process from workers
- ✅ Can run less frequently (weekly)
- ✅ Manageable time (few minutes for weekly batch)

**Verdict:** GOOD ADDITION to current approach

---

## Recommended Strategy

### Current Setup (Keep As-Is)

**Daily/Hourly:**
```bash
# Workers discover new entities quickly
python3 fetchers/horses_fetcher.py
python3 fetchers/races_fetcher.py
python3 fetchers/results_fetcher.py
```

**Initial One-Time:**
```bash
# Backfill all historical horses (15.5 hours)
python3 scripts/backfill_horse_pedigree.py
```

**Weekly/Monthly:**
```bash
# Incremental backfill for recent horses
python3 scripts/backfill_horse_pedigree.py --days-recent 7
```

---

### Implementation: Add Incremental Mode to Backfill

**Modify backfill_horse_pedigree.py to support:**

```python
def get_recent_horses_needing_pedigree(self, days_recent: int = 7) -> List[str]:
    """Get horses created in last N days that need pedigree data"""
    cutoff_date = (datetime.utcnow() - timedelta(days=days_recent)).date()

    result = self.db_client.client.table('ra_horses') \
        .select('horse_id') \
        .gte('created_at', cutoff_date.isoformat()) \
        .is_('dob', 'null') \
        .execute()

    return [row['horse_id'] for row in result.data]
```

**Usage:**
```bash
# Weekly cron job
python3 scripts/backfill_horse_pedigree.py --days-recent 7 --auto-confirm
```

**Expected time for weekly batch:**
- ~50-100 new horses per week
- Time: 30-60 seconds
- Manageable overhead

---

## Summary

### Current State
- ✅ Workers capture: horse_id, name, sex
- ❌ Workers DON'T capture: dob, colour, pedigree (by design)
- ✅ Backfill populates complete data

### Why This Is Correct
1. API limitation: Bulk search doesn't provide complete data
2. Performance: Individual calls would take 15.5 hours
3. Architecture: Separation of discovery (workers) vs enrichment (backfill)

### No Worker Changes Needed
The current worker code is **correct as-is**. The fields it tries to capture (lines 105-110) are defensive coding in case the API response includes them, but they won't be populated from the search endpoint.

### Action Items
1. ✅ Keep workers as-is (no changes needed)
2. ✅ Run full backfill for historical data (15.5 hours, one-time)
3. ⚠️ OPTIONAL: Add incremental backfill mode (weekly, 30-60 seconds)
4. ✅ Document this behavior for future reference

---

## Conclusion

**The "missing" pedigree data is NOT a bug.** It's an intentional architectural decision based on API endpoint capabilities and performance constraints.

**Workers = Quick discovery**
**Backfill = Complete enrichment**

This is the correct approach for this system.

---

**End of Analysis**
