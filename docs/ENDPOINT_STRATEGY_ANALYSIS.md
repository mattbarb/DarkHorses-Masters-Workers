# Racing API Endpoint Strategy Analysis

**Date:** 2025-10-22
**Question:** Should we fetch entity data (jockeys, trainers, owners, horses) from dedicated endpoints instead of extracting from racecards?

---

## Current Approach: Extraction from Racecards

### How It Works Now

**Primary Data Flow:**
```
GET /v1/racecards/pro (date=2025-10-22)
  ↓
Returns races with nested runners
  ↓
Each runner contains:
  - jockey_id, jockey_name
  - trainer_id, trainer_name, trainer_location
  - owner_id, owner_name
  - horse_id, horse_name, sex
  - sire_id, sire_name, dam_id, dam_name
  - (50+ other fields)
  ↓
EntityExtractor extracts entities from runner records
  ↓
Stores in ra_mst_jockeys, ra_mst_trainers, ra_mst_owners, ra_mst_horses
```

**Benefits:**
- ✅ One API call gets races + all entities
- ✅ Automatically discovers active entities (racing recently)
- ✅ Entity data is contextual (we know when/where they raced)
- ✅ No need to know entity names in advance
- ✅ Efficient for daily updates

**Downsides:**
- ❌ "Tangled web of cross-references" as you mentioned
- ❌ Entity data is nested/indirect
- ❌ Harder to trace where data comes from

---

## Alternative Approach: Dedicated Endpoints

### Racing API Search Endpoints

**Available:**
- `GET /v1/jockeys/search?name={name}&limit=500&skip=0`
- `GET /v1/trainers/search?name={name}&limit=500&skip=0`
- `GET /v1/owners/search?name={name}&limit=500&skip=0`
- `GET /v1/horses/search?name={name}&limit=500&skip=0`

### The Problem: Name Parameter Requirement

**Critical limitation:** These endpoints **REQUIRE** a `name` parameter.

```python
# This WORKS:
api_client.search_jockeys(name="Ryan Moore", limit=500)

# This FAILS:
api_client.search_jockeys(limit=500)  # Error: name parameter required
```

**What this means:**
- ❌ **Cannot bulk fetch all jockeys** - must know names in advance
- ❌ **Cannot discover new entities** - must search one by one
- ❌ **Cannot get "all active jockeys"** - no way to list all

### Current Fetchers Using Search Endpoints

**Location:** `fetchers/jockeys_fetcher.py`, `trainers_fetcher.py`, `owners_fetcher.py`

**How they work:**
```python
def fetch_and_store_bulk(self, name: str = '', max_pages: int = None):
    # ...
    api_response = self.api_client.search_jockeys(name=name, limit=500, skip=skip)
```

**With `name=''` (empty string):**
- Sometimes returns partial results
- Not reliable for "get all" operations
- API behavior is undefined for empty name

**With specific name:**
- Works reliably
- Returns entities matching that name
- Good for lookup/enrichment, not for bulk discovery

---

## Comparison: Extraction vs Dedicated Endpoints

### Data Completeness

| Approach | Jockeys | Trainers | Owners | Horses |
|----------|---------|----------|--------|--------|
| **Racecards Extraction** | ✅ All active | ✅ All active | ✅ All active | ✅ All racing |
| **Search Endpoints** | ⚠️ Only if name known | ⚠️ Only if name known | ⚠️ Only if name known | ⚠️ Only if name known |

### Fields Available

**From Racecards (nested in runners):**
```json
{
  "jockey_id": "jky_123",
  "jockey": "Ryan Moore",
  "trainer_id": "trn_456",
  "trainer": "Aidan O'Brien",
  "trainer_location": "Ballydoyle, Co. Tipperary",
  "owner_id": "own_789",
  "owner": "Coolmore",
  "horse_id": "hrs_012",
  "horse": "City Of Troy",
  "sex": "C",
  // ... 50+ other runner fields
}
```

**From Search Endpoints:**
```python
# GET /v1/jockeys/search?name=Ryan Moore
{
  "jockeys": [
    {
      "jockey_id": "jky_123",
      "name": "Ryan Moore",
      // ... (other fields unknown - not documented)
    }
  ]
}
```

**Question:** Do search endpoints provide additional fields beyond id/name?
**Answer:** UNKNOWN - would need to test

### API Call Efficiency

**Racecards Extraction:**
- 1 API call → 10-15 races → 150-200 runners → All entities
- Daily: ~30 API calls (one per day, UK + IRE)
- Discovers 50-100 new horses per day automatically

**Dedicated Endpoints (if they worked without name):**
- Would need: separate calls for jockeys, trainers, owners, horses
- Pagination: multiple calls per entity type
- Still wouldn't get race context

---

## Hybrid Enrichment (Current Best Practice)

### For Horses: Two-Step Approach

**Step 1: Discovery (Racecards)**
```python
GET /v1/racecards/pro
# Extract: horse_id, horse_name, sex
```

**Step 2: Enrichment (Pro Endpoint)**
```python
GET /v1/horses/{horse_id}/pro
# Get: dob, colour, pedigree, breeder
```

**Benefits:**
- ✅ Discover new horses from racecards
- ✅ Enrich with complete data from dedicated endpoint
- ✅ Only enrich NEW horses (efficient)
- ✅ Best of both worlds

**Why this works:**
- `/v1/horses/{id}/pro` uses **ID**, not name
- We get the IDs from racecards
- Then fetch detailed data by ID

---

## Key Question: Do Other Endpoints Support ID-based Lookup?

**Horses:** ✅ Yes
```
GET /v1/horses/{horse_id}/pro
```

**Jockeys/Trainers/Owners:** ❓ NEED TO VERIFY

Do these exist?
```
GET /v1/jockeys/{jockey_id}
GET /v1/trainers/{trainer_id}
GET /v1/owners/{owner_id}
```

**If YES:** We could use hybrid approach for all entities
**If NO:** Extraction from racecards remains the best approach

---

## Proposed Investigation

### Test 1: ID-Based Endpoints

Test if these endpoints exist:
```bash
curl -X GET "https://api.theracingapi.com/v1/jockeys/jky_123456" \
  -H "Authorization: Basic {credentials}"

curl -X GET "https://api.theracingapi.com/v1/trainers/trn_123456" \
  -H "Authorization: Basic {credentials}"

curl -X GET "https://api.theracingapi.com/v1/owners/own_123456" \
  -H "Authorization: Basic {credentials}"
```

**If they exist:**
- Implement hybrid enrichment for jockeys/trainers/owners
- Extract IDs from racecards
- Enrich with dedicated endpoints

### Test 2: Search Endpoint Additional Fields

Test what fields search endpoints actually return:
```bash
curl -X GET "https://api.theracingapi.com/v1/jockeys/search?name=Ryan%20Moore" \
  -H "Authorization: Basic {credentials}"
```

**Compare:**
- Fields from racecard runners
- Fields from search endpoint
- Determine if search provides any additional data

### Test 3: Results Endpoint for Entity Data

Check if `/v1/results` provides same entity extraction:
```bash
curl -X GET "https://api.theracingapi.com/v1/results?date=2025-10-22" \
  -H "Authorization: Basic {credentials}"
```

**Benefits:**
- Results have same runner structure as racecards
- Could extract entities from results too
- Already implemented in `results_fetcher.py`

---

## Recommendation

### Before Redesigning

**FIRST: Investigate what endpoints actually exist and what they return**

1. Test ID-based endpoints for jockeys/trainers/owners
2. Compare data quality: racecards vs dedicated endpoints
3. Document what additional data (if any) dedicated endpoints provide

### If ID-Based Endpoints Exist

**Implement Hybrid Approach for All Entities:**

```python
# Step 1: Discovery from racecards
racecards = api_client.get_racecards_pro(date='2025-10-22')
jockey_ids = extract_jockey_ids(racecards)  # Get IDs

# Step 2: Enrichment from dedicated endpoints
for jockey_id in new_jockey_ids:
    jockey_data = api_client.get_jockey_details(jockey_id)  # If exists
    store_complete_jockey_data(jockey_data)
```

**Benefits:**
- ✅ Clean separation: discovery vs enrichment
- ✅ Direct endpoint usage (cleaner architecture)
- ✅ Can get additional fields if available
- ✅ Still efficient (only enrich new entities)

### If ID-Based Endpoints DON'T Exist

**Keep Current Extraction Approach:**
- Racecards extraction is the ONLY way to discover entities
- Search endpoints are not suitable for bulk operations
- Current approach is correct and efficient

**But Document Better:**
- Create clear data flow diagrams
- Document entity extraction in detail
- Make cross-references explicit and traceable

---

## Questions to Answer

1. **Do ID-based endpoints exist for jockeys/trainers/owners?**
   - `/v1/jockeys/{jockey_id}`
   - `/v1/trainers/{trainer_id}`
   - `/v1/owners/{owner_id}`

2. **What additional data do these endpoints provide (if they exist)?**
   - Beyond what's in racecard runners
   - Statistics? Historical data? Contact info?

3. **Is there a "list all" endpoint for any entity type?**
   - `/v1/jockeys` (no search, just paginated list)
   - `/v1/trainers` (no search, just paginated list)

4. **What does the Pro plan actually unlock?**
   - More endpoints?
   - More fields in existing endpoints?
   - Higher rate limits?

---

## Action Plan

### Phase 1: Investigation (1-2 hours)
- [ ] Test `/v1/jockeys/{id}` endpoint with known ID
- [ ] Test `/v1/trainers/{id}` endpoint with known ID
- [ ] Test `/v1/owners/{id}` endpoint with known ID
- [ ] Compare fields: racecards vs dedicated endpoints
- [ ] Document findings

### Phase 2: Decision (based on findings)
**If ID endpoints exist:**
- [ ] Redesign for hybrid approach (all entities)
- [ ] Implement entity enrichment workers
- [ ] Update documentation

**If ID endpoints DON'T exist:**
- [ ] Keep current extraction approach
- [ ] Improve documentation of data flow
- [ ] Create better tracing/logging

### Phase 3: Implementation
- [ ] Update fetcher architecture
- [ ] Add comprehensive tests
- [ ] Document new strategy
- [ ] Update CLAUDE.md

---

## Current Status

**What We Know:**
- ✅ Racecards provide: id + name (+ location for trainers)
- ✅ Horses have ID-based endpoint: `/v1/horses/{id}/pro`
- ✅ Search endpoints require name parameter (not suitable for bulk)
- ❓ ID-based endpoints for jockeys/trainers/owners: UNKNOWN

**What We Need to Know:**
- ❓ Do `/v1/jockeys/{id}`, `/v1/trainers/{id}`, `/v1/owners/{id}` exist?
- ❓ What data do they return?
- ❓ Is there value in using them over extraction?

**Decision Pending:**
- Wait for investigation results
- Then choose: Hybrid approach vs Current extraction

---

## Your Input Needed

You said: "instead of making a tangled web of cross references we should just be pulling it from the endpoints where possible"

**My questions:**
1. Should I test the ID-based endpoints to see if they exist?
2. If they don't exist, should we stick with extraction (since it's the only way)?
3. Or do you have API documentation showing these endpoints are available?

**Next Step:**
Would you like me to run tests against the Racing API to discover what endpoints are actually available and what they return?
