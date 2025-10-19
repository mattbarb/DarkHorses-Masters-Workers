# Corrected Horse Data Strategy

**Date:** 2025-10-14
**Critical Discovery:** Racing API has NO `/v1/horses/search` endpoint
**Impact:** Complete strategy change required

---

## The Problem

### Original Assumption (WRONG)
- horses_fetcher.py uses `/v1/horses/search` for bulk discovery
- New horses found via bulk search, then enriched with Pro endpoint

### Reality (CORRECT)
- **NO `/v1/horses/search` endpoint exists in Racing API**
- HTTP 422 error confirms endpoint doesn't exist
- Reviewed complete API documentation - no horses search/list endpoint

---

## How Horses Are Actually Discovered

### Method 1: Through Race Data ✅ CORRECT
Horses appear in:
- **Racecards** (`/v1/racecards/pro`) - horses running in upcoming races
- **Results** (`/v1/results`) - horses that ran in past races

**This is how the system ACTUALLY works:**

```
races_fetcher.py → /v1/racecards/pro
  ↓
Discovers races with runners
  ↓
Each runner has horse_id
  ↓
Inserts to ra_horses (basic data: id, name, sex from racecard)
  ↓
Inserts to ra_runners (race entries)
```

**Current flow is CORRECT** - horses are discovered through race data!

### Method 2: Individual Horse Lookup ✅ AVAILABLE
- `/v1/horses/{horse_id}/pro` - Get complete data for a specific horse
- Used for backfilling existing horses with complete data

---

## Correct Architecture

### Daily Operations (Already Working)
```
Step 1: races_fetcher.py runs
  → Fetches racecards for today/tomorrow
  → Discovers horses entered in races
  → Inserts horse_id, name, sex (from racecard)
  → Inserts runner records

Step 2: results_fetcher.py runs
  → Fetches results for completed races
  → Updates runner records with finishing positions
  → No new horses (already in racecards)
```

**This is working correctly!** Horses are discovered through race participation.

### Historical Backfill (One-Time)
```
Step 1: Get all existing horse IDs from database
  → Query ra_horses for all horse_id values
  → ~111,000 horses discovered through historical race data

Step 2: Enrich with Pro endpoint
  → For each horse_id: call /v1/horses/{id}/pro
  → Update dob, sex_code, colour, colour_code, region
  → Insert pedigree records
  → Time: 15.5 hours (111,000 × 0.5s)
```

**This is the ONLY way to get complete horse data.**

---

## Why horses_fetcher.py Was Wrong

### What horses_fetcher.py Tried to Do
```python
# This endpoint DOESN'T EXIST:
api_response = self.api_client.search_horses(limit=500, skip=skip)
```

### What Actually Happens
- HTTP 422 error - endpoint validation failed
- The endpoint `/v1/horses/search` is not in the API spec
- Racing API has these horse endpoints:
  - `/v1/horses/{horse_id}/standard` ✅ Exists
  - `/v1/horses/{horse_id}/pro` ✅ Exists
  - `/v1/horses/search` ❌ DOES NOT EXIST

### Purpose of horses_fetcher.py
**It's NOT NEEDED.** Horses are discovered through:
1. racecards (upcoming races)
2. results (past races)

There's NO separate "horse directory" to fetch from.

---

## Corrected Strategy

### Phase 1: Remove horses_fetcher.py
**Action:** Deprecate horses_fetcher.py - it's trying to use a non-existent endpoint

**Reason:** Horses are discovered through race data, not a separate endpoint

### Phase 2: Run Historical Backfill (One-Time)
**Script:** `scripts/backfill_horse_pedigree.py` (already created and tested)

**What it does:**
1. Gets all horse_ids from ra_horses table
2. For each horse: fetches complete data from `/v1/horses/{id}/pro`
3. Updates ra_horses with dob, sex_code, colour, colour_code, region
4. Inserts pedigree records to ra_horse_pedigree

**Command:**
```bash
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[YOUR-KEY]' \
RACING_API_USERNAME='[YOUR-USERNAME]' \
RACING_API_PASSWORD='[YOUR-PASSWORD]' \
python3 scripts/backfill_horse_pedigree.py
```

**Time:** 15.5 hours for ~111,000 horses

### Phase 3: Ongoing Maintenance (Already Working)
**No changes needed** - current workflow is correct:

1. **Daily:** races_fetcher.py discovers new horses in racecards
2. **Daily:** results_fetcher.py updates race results
3. **Weekly (optional):** Backfill script for recent horses only

---

## New Horse Discovery Flow (Current = Correct)

### When a new horse appears in racing:

1. **Horse enters a race** (trainer submits entry)
2. **Racecard published** (appears in API)
3. **races_fetcher.py runs** (fetches today's/tomorrow's racecards)
4. **New horse discovered** (horse_id appears in runners list)
5. **Basic data inserted:**
   ```python
   ra_horses: horse_id, name, sex (from racecard)
   ra_runners: full runner details
   ```
6. **Pedigree is NULL** (racecard doesn't include pedigree)

### To get complete data:

**Option A: Weekly Backfill (Recommended)**
```bash
# Run weekly to enrich horses from last 7 days
python3 scripts/backfill_horse_pedigree.py --days-recent 7
```
- Time: 30-60 seconds for ~50 new horses
- Automatic enrichment
- Pedigree data within 1 week

**Option B: On-Demand**
- ML training queries database
- Finds horses with NULL pedigree
- Triggers backfill for those horses

---

## Updated File Status

### KEEP (Working Correctly)
- ✅ `fetchers/races_fetcher.py` - Discovers horses through racecards
- ✅ `fetchers/results_fetcher.py` - Updates race results
- ✅ `scripts/backfill_horse_pedigree.py` - Enriches horses with complete data

### DEPRECATE (Using Non-Existent Endpoint)
- ❌ `fetchers/horses_fetcher.py` - Tries to use `/v1/horses/search` (doesn't exist)
- ❌ `test_hybrid_horses_fetcher.py` - Test for non-working fetcher

### UPDATE NEEDED
- ⚠️ `utils/api_client.py` - Remove `search_horses()` method (endpoint doesn't exist)

---

## Execution Plan (Corrected)

### Step 1: Clean Up Code ✅
```bash
# Remove or rename horses_fetcher.py
mv fetchers/horses_fetcher.py _deprecated/horses_fetcher.py.old

# Remove test file
rm test_hybrid_horses_fetcher.py

# Update api_client.py to remove search_horses() method
```

### Step 2: Run Historical Backfill (15.5 hours)
```bash
# One-time enrichment of all existing horses
python3 scripts/backfill_horse_pedigree.py
```

### Step 3: Set Up Weekly Enrichment (Optional)
```bash
# Add to cron or scheduler
# Every Sunday at 2 AM:
python3 scripts/backfill_horse_pedigree.py --days-recent 7
```

---

## Key Learnings

### 1. Racing API Structure
- **No bulk horse endpoint** - horses only accessible via:
  - Individual lookup: `/v1/horses/{id}/pro`
  - Race participation: racecards & results

### 2. Discovery Method
- Horses discovered through **race participation**, not separate directory
- This makes sense: horses exist because they race

### 3. Data Enrichment
- Racecards provide: horse_id, name, sex (basic)
- Pro endpoint provides: dob, colour, pedigree (complete)
- Backfill script bridges the gap

### 4. Current System Is Correct
- races_fetcher.py discovers horses ✅
- results_fetcher.py updates results ✅
- Backfill script enriches data ✅
- **No additional fetcher needed**

---

## Summary

### What We Thought
- Bulk horse search endpoint exists
- horses_fetcher.py discovers all horses
- Hybrid approach enriches new horses

### Reality
- No bulk horse search endpoint
- Horses discovered through race data
- Backfill enriches existing horses
- **Current architecture is already correct**

### Action Required
1. ❌ Remove horses_fetcher.py (uses non-existent endpoint)
2. ✅ Run backfill_horse_pedigree.py (one-time, 15.5 hours)
3. ✅ Optional: Schedule weekly incremental backfill
4. ✅ Keep current races_fetcher.py and results_fetcher.py (working correctly)

---

**Conclusion:** The system is already architected correctly. Horses are discovered through race participation (racecards/results), and the backfill script enriches them with complete pedigree data. No hybrid worker approach needed - just run the backfill!

---

**Next Step:** Run the backfill script to enrich all existing horses.
