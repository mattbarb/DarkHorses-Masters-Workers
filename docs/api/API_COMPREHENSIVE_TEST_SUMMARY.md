# Racing API Comprehensive Endpoint Test Results

**Date:** 2025-10-14
**Test Results:** /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/api_endpoint_test_results.json

---

## Executive Summary

**Total Endpoints Tested:** 41
**Successful:** 20 (48.8%)
**Failed:** 21 (51.2%)

---

## CRITICAL FINDINGS

### 1. `/v1/horses/search` EXISTS BUT...

**Status:** ✅ WORKS (with correct parameters)
**Requirement:** Must provide `name` parameter
**Purpose:** Search horses by name, NOT bulk listing

**What it returns:**
```json
{
  "search_results": [
    {
      "id": "hrs_3356262",
      "name": "Whistle Test (GB)",
      "sire": "Kris (GB)",
      "sire_id": "sir_2109044",
      "dam": "Cut Velvet (USA)",
      "dam_id": "dam_2859066",
      "damsire": "Northern Dancer",
      "damsire_id": "dsi_2111935"
    }
  ]
}
```

**Fields Available:**
- ✅ `id` - Horse ID
- ✅ `name` - Horse name
- ✅ `sire` - Sire name
- ✅ `sire_id` - Sire ID
- ✅ `dam` - Dam name
- ✅ `dam_id` - Dam ID
- ✅ `damsire` - Damsire name
- ✅ `damsire_id` - Damsire ID

**Missing from search:**
- ❌ `dob` - Date of birth
- ❌ `sex` / `sex_code` - Sex information
- ❌ `colour` / `colour_code` - Colour information
- ❌ `region` - Region
- ❌ `breeder` - Breeder information

**Conclusion:** Search endpoint is for **NAME-BASED LOOKUPS**, not bulk discovery. Returns pedigree but not complete horse metadata.

---

### 2. Search Endpoints Require `name` Parameter

**All these require `name` parameter:**
- `/v1/horses/search` - ✅ Works with `name`
- `/v1/jockeys/search` - ✅ Works with `name`
- `/v1/trainers/search` - ✅ Works with `name`
- `/v1/owners/search` - ✅ Works with `name`

**Without `name` parameter:**
```json
{
  "detail": [
    {
      "loc": ["query", "name"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

**Implication:** These are SEARCH endpoints (for lookups), not LIST endpoints (for bulk discovery).

---

### 3. No Bulk Horse Listing Endpoint

**Endpoints that DO NOT EXIST:**
- ❌ `/v1/horses` (404)
- ❌ `/v1/horses/list` (404)
- ❌ `/v1/horses/all` (404)
- ❌ `/v1/jockeys` (404)
- ❌ `/v1/trainers` (404)
- ❌ `/v1/owners` (404)

**Conclusion:** API does NOT provide bulk entity listing. Entities are discovered through race data.

---

### 4. Richest Data Sources

**Racecards Pro** (`/v1/racecards/pro`) - **96 fields**
- Most complete data
- Historical and future racecards
- Includes odds
- Comprehensive runner details

**Racecards Big Races** (`/v1/racecards/big-races`) - **106 fields**
- Even richer than regular Pro
- Special events only
- Most comprehensive runner and race data

**Results** (`/v1/results`) - **70 fields**
- Historical race results
- Final positions and times
- Includes ratings data

---

## All Successful Endpoints

### Courses (4 endpoints)
1. ✅ `/v1/courses` - List all courses (6 fields)
2. ✅ `/v1/courses/regions` - List regions
3. ✅ `/v1/courses` + `region_codes=['gb']` - Filter by region
4. ✅ `/v1/courses` + `region_codes=['ire']` - Filter by region

### Horses (1 endpoint - NAME SEARCH ONLY)
5. ✅ `/v1/horses/search` + `name='test'` - Search by name (9 fields including pedigree)

### Jockeys (1 endpoint)
6. ✅ `/v1/jockeys/search` + `name='Murphy'` - Search by name (3 fields)

### Trainers (1 endpoint)
7. ✅ `/v1/trainers/search` + `name='Henderson'` - Search by name (3 fields)

### Owners (1 endpoint)
8. ✅ `/v1/owners/search` + `name='Qatar'` - Search by name (3 fields)

### Racecards (7 endpoints)
9. ✅ `/v1/racecards/free` + `day='today'` - Today's racecards (41 fields)
10. ✅ `/v1/racecards/free` + `day='tomorrow'` - Tomorrow's racecards (41 fields)
11. ✅ `/v1/racecards/basic` + `day='today'` - Detailed racecards (84 fields)
12. ✅ `/v1/racecards/standard` + `day='today'` - With odds (89 fields)
13. ✅ `/v1/racecards/pro` + `date='YYYY-MM-DD'` - Historical/future (89-96 fields)
14. ✅ `/v1/racecards/big-races` - Special events (106 fields) **RICHEST**
15. ✅ `/v1/racecards/summaries` + `date='YYYY-MM-DD'` - Race summaries (13 fields)

### Results (3 endpoints)
16. ✅ `/v1/results` + `start_date` + `end_date` - Historical results (70 fields)
17. ✅ `/v1/results` + dates + `region=['gb']` - Filter by region (70 fields)
18. ✅ `/v1/results` + dates + `limit=10` - Paginated results (70 fields)

---

## All Failed Endpoints

### Horses (4 failed)
- ❌ `/v1/horses` - 404 (doesn't exist)
- ❌ `/v1/horses/search` without `name` - 422 (requires name parameter)
- ❌ `/v1/horses/list` - 404 (doesn't exist)
- ❌ `/v1/horses/all` - 404 (doesn't exist)

### Jockeys (2 failed)
- ❌ `/v1/jockeys/search` without `name` - 422 (requires name parameter)
- ❌ `/v1/jockeys` - 404 (doesn't exist)

### Trainers (2 failed)
- ❌ `/v1/trainers/search` without `name` - 422 (requires name parameter)
- ❌ `/v1/trainers` - 404 (doesn't exist)

### Owners (2 failed)
- ❌ `/v1/owners/search` without `name` - 422 (requires name parameter)
- ❌ `/v1/owners` - 404 (doesn't exist)

### Pedigree (5 failed - NO DEDICATED ENDPOINTS)
- ❌ `/v1/pedigree` - 404
- ❌ `/v1/horses/pedigree` - 404
- ❌ `/v1/sires` - 404
- ❌ `/v1/dams` - 404
- ❌ `/v1/breeders` - 404

### Statistics (5 failed - NO STATS ENDPOINTS)
- ❌ `/v1/statistics` - 404
- ❌ `/v1/stats` - 404
- ❌ `/v1/horses/statistics` - 404
- ❌ `/v1/jockeys/statistics` - 404
- ❌ `/v1/trainers/statistics` - 404

---

## Data Completeness Analysis

### For Complete Horse Data

**Option 1: Search by Name** (if you know the name)
```
/v1/horses/search?name=SeaBiscuit
```
Returns: id, name, sire, dam, damsire (with IDs)
Missing: dob, sex_code, colour, colour_code, region, breeder

**Option 2: Individual Horse Pro** (if you know the ID)
```
/v1/horses/{horse_id}/pro
```
Returns: COMPLETE data including all pedigree and metadata

**Option 3: Race Participation** (discovery method)
```
/v1/racecards/pro?date=YYYY-MM-DD
```
Returns: horses through race runners
Provides: Basic horse data in runner context

**Option 4: Results** (historical)
```
/v1/results?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD
```
Returns: horses through race results

---

## Recommended Data Collection Strategy

### For Richest, Most Complete Data:

**1. Daily Race Data Collection**
- Use `/v1/racecards/pro` for upcoming races (96 fields)
- Use `/v1/racecards/big-races` for special events (106 fields) **RICHEST**
- Use `/v1/results` for completed races (70 fields)
- This discovers ALL active horses through race participation

**2. Complete Horse Enrichment**
- For each discovered horse_id: call `/v1/horses/{horse_id}/pro`
- This provides complete metadata + pedigree
- Can be done as backfill or on-demand

**3. Name-Based Lookups (Optional)**
- Use `/v1/horses/search?name=X` for known horse names
- Returns pedigree info without needing horse_id
- Useful for user-initiated searches

---

## Current Architecture Assessment

### ✅ What's Working Correctly

**races_fetcher.py:**
- Uses `/v1/racecards/pro` ✅ CORRECT
- Discovers horses through runners ✅ CORRECT
- Captures race and runner data ✅ CORRECT

**results_fetcher.py:**
- Uses `/v1/results` ✅ CORRECT
- Updates race results ✅ CORRECT
- Captures position data ✅ CORRECT

### ❌ What Doesn't Work

**horses_fetcher.py:**
- Tries to use `/v1/horses/search` without `name` parameter ❌ WRONG
- Cannot bulk list horses this way ❌ NOT SUPPORTED BY API
- Should be deprecated or redesigned

---

## Recommended Actions

### Immediate
1. ✅ **Keep races_fetcher.py as-is** - Working correctly
2. ✅ **Keep results_fetcher.py as-is** - Working correctly
3. ❌ **Deprecate horses_fetcher.py** - Cannot bulk list horses
4. ✅ **Run backfill_horse_pedigree.py** - Enrich existing horses

### Optional Enhancements
1. **Use `/v1/racecards/big-races`** - Richest data source (106 fields)
2. **Add name search feature** - Use `/v1/horses/search?name=X` for user lookups
3. **Weekly incremental backfill** - Enrich recent horses automatically

---

## Field Count Comparison

| Endpoint | Field Count | Notes |
|----------|-------------|-------|
| `/v1/racecards/big-races` | 106 | **RICHEST - Special events** |
| `/v1/racecards/pro` | 89-96 | **Very rich - All dates** |
| `/v1/racecards/standard` | 89 | With odds |
| `/v1/racecards/basic` | 84 | Detailed racecards |
| `/v1/results` | 70 | Historical results |
| `/v1/racecards/free` | 41 | Basic racecards |
| `/v1/racecards/summaries` | 13 | Summaries only |
| `/v1/horses/search` | 9 | Pedigree only |
| `/v1/courses` | 6 | Course info |
| `/v1/jockeys/search` | 3 | Name search |
| `/v1/trainers/search` | 3 | Name search |
| `/v1/owners/search` | 3 | Name search |

---

## Conclusion

**Key Insights:**
1. ✅ `/v1/horses/search` EXISTS but requires `name` parameter (not for bulk listing)
2. ❌ NO bulk entity listing endpoints (horses, jockeys, trainers, owners)
3. ✅ Entities discovered through race data (racecards/results) - THIS IS CORRECT
4. ✅ Complete data via individual Pro endpoints (`/v1/horses/{id}/pro`)
5. ✅ Richest data: `/v1/racecards/big-races` (106 fields)

**Current System:**
- ✅ races_fetcher.py + results_fetcher.py = CORRECT approach
- ❌ horses_fetcher.py = Cannot work as designed (no bulk listing)
- ✅ backfill_horse_pedigree.py = Correct enrichment strategy

**Next Steps:**
1. Deprecate or redesign horses_fetcher.py
2. Run backfill for historical horse enrichment
3. Consider adding big-races fetcher for richest data
4. Optionally add name search functionality for user lookups

---

**Full test results:** `docs/api_endpoint_test_results.json`
