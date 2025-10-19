# Data Gap Analysis & Solutions

**Date:** 2025-10-14
**Database:** Supabase (amsjvmlaknnvppxsgpfk)
**Total Records:** 682,372 across 9 tables

---

## Summary

| Category | Current Coverage | Target | Gap | Can Be Fixed? |
|----------|-----------------|--------|-----|---------------|
| **Horse Metadata** | 0.0% | 95%+ | 111,416 horses | ✅ YES - 15.5 hrs |
| **Horse Pedigree** | 0.0% | 80%+ | 111,420 horses | ✅ YES - 15.5 hrs |
| **Position Data** | 0.2% | 60%+ | 378,603 runners | ⚠️ PARTIAL - needs results fetcher |
| **Ratings Data** | 75-87% | 70%+ | N/A | ✅ COMPLETE |

---

## CRITICAL GAPS (Must Fix)

### 1. Horse Metadata - 111,416 Horses Missing Data (99.99%)

**What's Missing:**
- Date of Birth (DOB): 111,416 horses
- Sex Code (G/C/F/M): 111,416 horses
- Colour: 111,416 horses
- Colour Code: 111,416 horses

**Where the data is:**
- Available in Racing API `/v1/horses/{id}/pro` endpoint

**How to fix:**
✅ **SOLUTION READY** - Run backfill script
```bash
# Time required: 15.5 hours (111,325 horses × 0.5s)
python3 scripts/backfill_horse_pedigree.py
```

**Expected result:**
- DOB coverage: 0.0% → 95%+
- Sex code coverage: 0.0% → 95%+
- Colour coverage: 0.0% → 95%+
- Colour code coverage: 0.0% → 95%+

**Status:** ✅ Script tested successfully with 10 horses

---

### 2. Horse Pedigree - 111,420 Horses Missing Pedigree (99.99%)

**What's Missing:**
- Sire (father) information
- Dam (mother) information
- Damsire (maternal grandfather) information
- Breeder information

**Current state:**
- ra_horse_pedigree: 10 records (0.0% coverage)
- Of those 10: 100% have breeder field ✅

**Where the data is:**
- Available in Racing API `/v1/horses/{id}/pro` endpoint

**How to fix:**
✅ **SOLUTION READY** - Same backfill script as above
```bash
# Time required: 15.5 hours (included in horse metadata backfill)
python3 scripts/backfill_horse_pedigree.py
```

**Expected result:**
- Pedigree coverage: 0.0% → 80-90% (not all horses have pedigree data)
- Breeder coverage: 100% → 90%+ (maintained)

**Status:** ✅ Script tested successfully with 10 horses

---

## MODERATE GAPS (Performance Issue)

### 3. Position Data (Results) - 378,603 Runners Missing (99.8%)

**What's Missing:**
- Position (finishing position): 378,603 runners missing
- Distance beaten: 378,574 runners missing
- Prize won: 379,088 runners missing
- Starting price (SP): 378,574 runners missing

**Current coverage:**
- Position: 819 / 379,422 (0.2%)
- Distance beaten: 848 / 379,422 (0.2%)
- Starting price: 848 / 379,422 (0.2%)

**Why so low?**
This is likely because:
1. We're fetching more **racecards** (future races) than **results** (past races)
2. Results fetcher may not be running regularly
3. Historical results not backfilled

**Where the data is:**
- Available in Racing API `/v1/results` endpoint
- Workers already configured to capture this data

**How to fix:**
⚠️ **PARTIAL SOLUTION** - Multi-step approach

**Step 1: Check results fetcher frequency**
```bash
# Check if results fetcher is running
# Should run daily to capture completed races
```

**Step 2: Run historical results backfill**
```bash
# Need to create: scripts/backfill_historical_results.py
# Would fetch results for all past races in ra_races table
# Estimated time: TBD (depends on race count)
```

**Expected result after fix:**
- Position coverage: 0.2% → 60-70%
- Will never be 100% because:
  - Future racecards don't have results yet
  - Some old races may not have results available

**Status:** ⚠️ Requires new backfill script + scheduler check

---

## COMPLETE (No Action Needed)

### 4. Ratings Data - Good Coverage

**Current coverage:**
- Official Rating: 283,738 / 379,422 (74.8%) ✅
- RPR (Racing Post Rating): 330,701 / 379,422 (87.2%) ✅
- TSR (Top Speed Rating): 292,867 / 379,422 (77.2%) ✅

**Why not 100%?**
- Ratings not always available (depends on race type, region, horse experience)
- Expected to be 70-85% coverage

**Status:** ✅ No action needed - coverage is good

---

### 5. Reference Data - Complete

| Table | Records | Status |
|-------|---------|--------|
| ra_courses | 101 | ✅ COMPLETE |
| ra_bookmakers | 19 | ✅ COMPLETE |
| ra_jockeys | 3,480 | ✅ COMPLETE |
| ra_trainers | 2,780 | ✅ COMPLETE |
| ra_owners | 48,092 | ✅ COMPLETE |

**Status:** ✅ No action needed - reference data is complete

---

## Action Plan

### Immediate Actions (Ready to Execute)

#### ✅ Action 1: Run Horse Pedigree Backfill
**Priority:** CRITICAL
**Time:** 15.5 hours
**Impact:** Fixes horse metadata (95%+) AND pedigree (80%+)

**Command:**
```bash
# Start screen session
screen -S pedigree_backfill

# Run backfill
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[KEY]' \
RACING_API_USERNAME='[USER]' \
RACING_API_PASSWORD='[PASS]' \
python3 scripts/backfill_horse_pedigree.py

# Detach: Ctrl+A, D
# Reattach: screen -r pedigree_backfill
```

**Files:**
- Script: `scripts/backfill_horse_pedigree.py` ✅ Ready
- Migration: `migrations/008_add_pedigree_and_horse_fields.sql` ✅ Applied
- Validation: `scripts/validate_data_completeness.py` ✅ Ready

---

### Future Actions (Requires Development)

#### ⚠️ Action 2: Fix Position Data Coverage
**Priority:** MEDIUM
**Time:** TBD (depends on results count)
**Impact:** Position data: 0.2% → 60-70%

**Steps:**
1. Check results fetcher is running regularly
2. Create `scripts/backfill_historical_results.py`
3. Run historical results backfill
4. Monitor forward capture

**Status:** Not started - requires investigation

---

## Expected State After Action 1

### Before Backfill (Current)
```
Overall Data Completeness: ~70%

ra_horses:
  ✅ name:        111,430 (100.0%)
  ❌ dob:              14 (  0.0%)
  ❌ sex_code:         14 (  0.0%)
  ❌ colour:           14 (  0.0%)
  ❌ colour_code:      14 (  0.0%)

ra_horse_pedigree:
  ❌ Coverage:         10 (  0.0%)
```

### After Backfill (Expected)
```
Overall Data Completeness: ~85%

ra_horses:
  ✅ name:        111,430 (100.0%)
  ✅ dob:         105,859 ( 95.0%)
  ✅ sex_code:    105,859 ( 95.0%)
  ✅ colour:      105,859 ( 95.0%)
  ✅ colour_code: 105,859 ( 95.0%)

ra_horse_pedigree:
  ✅ Coverage:     89,144 ( 80.0%)
  ✅ breeder:      80,230 ( 90.0%)
```

### After Action 2 (Future)
```
Overall Data Completeness: ~90%

ra_runners:
  ✅ position:        265,595 ( 70.0%)
  ✅ distance_beaten: 265,595 ( 70.0%)
  ✅ prize_won:       265,595 ( 70.0%)
  ✅ starting_price:  265,595 ( 70.0%)
```

---

## Files Reference

### Ready to Use
- ✅ `migrations/008_add_pedigree_and_horse_fields.sql` - Applied
- ✅ `scripts/backfill_horse_pedigree.py` - Tested successfully
- ✅ `scripts/validate_data_completeness.py` - Working
- ✅ `fetchers/horses_fetcher.py` - Updated to capture new fields
- ✅ `docs/COMPLETE_DATA_CAPTURE_GUIDE.md` - Step-by-step guide

### Needs Creation
- ⚠️ `scripts/backfill_historical_results.py` - Not created yet

---

## Decision Required

### Ready to execute now:
**Run horse pedigree backfill (15.5 hours)?**
- Fixes: 111,416 horses with metadata + 111,420 horses with pedigree
- Impact: 70% → 85% overall data completeness
- Risk: Low (tested successfully with 10 horses)
- Reversible: No (but safe - only adds data, doesn't delete)

### Future consideration:
**Create and run results backfill?**
- Fixes: ~265,000 runners with position data
- Impact: 85% → 90% overall data completeness
- Risk: Medium (needs development + testing)
- Time: TBD

---

**End of Data Gap Analysis**
