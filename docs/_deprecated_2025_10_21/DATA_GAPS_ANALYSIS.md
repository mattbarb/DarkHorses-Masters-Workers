# Database Data Gaps Analysis

**Date:** 2025-10-20
**Analysis Type:** Column Completeness Audit

## Executive Summary

Analysis reveals critical data gaps across master tables that need to be filled:

### Priority 1 - CRITICAL (0% populated)
- **ra_mst_horses:** Missing ALL pedigree IDs (sire_id, dam_id, damsire_id)
  - 111,669 horses with 0% pedigree ID coverage
  - Note: ra_horse_pedigree table HAS 100% pedigree data, but horses table is missing the IDs

### Priority 2 - HIGH (45-97% populated)
- **ra_mst_trainers:** 54.76% missing location data (1,523 of 2,781 trainers)
- **ra_mst_jockeys:** 3.30% missing statistics (115 of 3,483 jockeys)
- **ra_mst_trainers:** 6.08% missing statistics (169 of 2,781 trainers)
- **ra_mst_owners:** 2.11% missing statistics (1,018 of 48,165 owners)

### Priority 3 - MEDIUM (99.8% populated)
- **ra_mst_horses:** 0.2% missing enrichment data (dob, colour, sex_code)

---

## Detailed Analysis

### 1. ra_mst_horses - CRITICAL GAPS

**Total Records:** 111,669 horses

| Column | Populated | Missing | Coverage | Priority |
|--------|-----------|---------|----------|----------|
| sire_id | 0 | 111,669 | **0.0%** | CRITICAL |
| dam_id | 0 | 111,669 | **0.0%** | CRITICAL |
| damsire_id | 0 | 111,669 | **0.0%** | CRITICAL |
| dob | 111,445 | 224 | 99.8% | LOW |
| colour | 111,445 | 224 | 99.8% | LOW |
| colour_code | 23,300 | 88,369 | 20.9% | MEDIUM |
| region | 28,624 | 83,045 | 25.6% | MEDIUM |
| sex_code | 111,445 | 224 | 99.8% | LOW |

**Critical Issue:** The horses table is missing ALL pedigree IDs (sire_id, dam_id, damsire_id), but the `ra_horse_pedigree` table has 100% of this data! This is a design issue - pedigree IDs should be denormalized to horses table for easier querying.

**Data Source:**
- Pedigree IDs: Available in ra_horse_pedigree table (100% coverage)
- Missing enrichment: Available from `/v1/horses/{id}/pro` API endpoint

---

### 2. ra_mst_trainers - HIGH PRIORITY

**Total Records:** 2,781 trainers (excluding test data)

| Column | Populated | Missing | Coverage | Priority |
|--------|-----------|---------|----------|----------|
| location | 1,258 | 1,523 | **45.24%** | HIGH |
| total_runners | 2,612 | 169 | 93.92% | MEDIUM |
| total_wins | 2,612 | 169 | 93.92% | MEDIUM |
| win_rate | 2,612 | 169 | 93.92% | MEDIUM |

**Missing Data:**
- 54.76% lack location data (1,523 trainers)
- 6.08% lack statistics (169 trainers)

**Data Source:**
- Location: Available from `/v1/trainers/{id}` API endpoint (PRO plan)
- Statistics: Can be calculated from ra_runners + ra_races historical data OR fetched from API

---

### 3. ra_mst_jockeys - MEDIUM PRIORITY

**Total Records:** 3,483 jockeys (excluding test data)

| Column | Populated | Missing | Coverage | Priority |
|--------|-----------|---------|----------|----------|
| total_rides | 3,368 | 115 | 96.70% | MEDIUM |
| total_wins | 3,368 | 115 | 96.70% | MEDIUM |
| win_rate | 3,368 | 115 | 96.70% | MEDIUM |

**Missing Data:** 3.30% lack statistics (115 jockeys)

**Data Source:**
- Statistics: Available from `/v1/jockeys/{id}` API endpoint OR calculated from historical data

---

### 4. ra_mst_owners - LOW PRIORITY

**Total Records:** 48,165 owners (excluding test data)

| Column | Populated | Missing | Coverage | Priority |
|--------|-----------|---------|----------|----------|
| total_runners | 47,147 | 1,018 | 97.89% | LOW |
| total_wins | 47,147 | 1,018 | 97.89% | LOW |
| win_rate | 47,147 | 1,018 | 97.89% | LOW |

**Missing Data:** 2.11% lack statistics (1,018 owners)

**Data Source:**
- Statistics: Available from `/v1/owners/{id}` API endpoint OR calculated from historical data

---

### 5. ra_horse_pedigree - COMPLETE ✅

**Total Records:** 111,594 pedigree records

| Column | Populated | Missing | Coverage | Status |
|--------|-----------|---------|----------|--------|
| sire_id | 111,594 | 0 | 100.0% | ✅ COMPLETE |
| dam_id | 111,594 | 0 | 100.0% | ✅ COMPLETE |
| damsire_id | 111,594 | 0 | 100.0% | ✅ COMPLETE |
| breeder | 111,520 | 74 | 99.9% | ✅ COMPLETE |
| region | 38,820 | 72,774 | 34.8% | MEDIUM |

**Status:** Pedigree table is nearly complete. Only 'region' field needs backfilling (65.2% missing).

---

## Recommended Actions

### Action 1: Denormalize Pedigree IDs to ra_mst_horses
**Priority:** CRITICAL
**Effort:** Low (simple SQL UPDATE from existing data)
**Impact:** HIGH - enables easier queries without joins

```sql
-- Copy pedigree IDs from ra_horse_pedigree to ra_mst_horses
UPDATE ra_mst_horses h
SET
    sire_id = p.sire_id,
    dam_id = p.dam_id,
    damsire_id = p.damsire_id,
    updated_at = NOW()
FROM ra_horse_pedigree p
WHERE h.id = p.horse_id
  AND (h.sire_id IS NULL OR h.dam_id IS NULL OR h.damsire_id IS NULL);
```

### Action 2: Fill Trainer Locations
**Priority:** HIGH
**Effort:** Medium (1,523 API calls at 2 req/sec = ~12 minutes)
**Impact:** MEDIUM - improves trainer profiles

**Method:** Fetch from `/v1/trainers/{id}` API endpoint (PRO plan)

### Action 3: Fill Missing Statistics
**Priority:** MEDIUM
**Effort:** Low (calculate from existing data) OR Medium (API fetches)
**Impact:** MEDIUM - completes entity profiles

**Method Option A (Recommended):** Calculate from ra_runners + ra_races historical data
**Method Option B:** Fetch from respective API endpoints

### Action 4: Fill Missing Horse Enrichment
**Priority:** LOW
**Effort:** Very Low (224 API calls = ~2 minutes)
**Impact:** LOW - only 0.2% of horses

**Method:** Fetch from `/v1/horses/{id}/pro` API endpoint

---

## Autonomous Agent Requirements

The agent should:

1. **Phase 1 - Pedigree Denormalization (CRITICAL)**
   - Execute SQL UPDATE to copy pedigree IDs from ra_horse_pedigree to ra_mst_horses
   - Verify 111,594 horses updated
   - No API calls required

2. **Phase 2 - Trainer Locations (HIGH)**
   - Fetch 1,523 trainers without location from `/v1/trainers/{id}`
   - Rate limit: 2 req/sec (0.5s sleep between calls)
   - Time: ~12 minutes
   - Update ra_mst_trainers with location data

3. **Phase 3 - Entity Statistics (MEDIUM)**
   - Option A: Calculate from historical data (recommended)
     - Query ra_runners + ra_races for each entity
     - Calculate total rides/runners, wins, win_rate, etc.
   - Option B: Fetch from API endpoints
     - `/v1/jockeys/{id}` for 115 jockeys (~1 minute)
     - `/v1/trainers/{id}` for 169 trainers (~2 minutes)
     - `/v1/owners/{id}` for 1,018 owners (~9 minutes)

4. **Phase 4 - Horse Enrichment (LOW)**
   - Fetch 224 horses missing enrichment from `/v1/horses/{id}/pro`
   - Time: ~2 minutes

**Total Estimated Time:**
- Phase 1: <1 second (SQL only)
- Phase 2: ~12 minutes (API)
- Phase 3: ~5 minutes (calculation) OR ~12 minutes (API)
- Phase 4: ~2 minutes (API)
- **TOTAL: ~20 minutes (calculation) OR ~27 minutes (all API)**

---

## Implementation Priority

1. ✅ **CRITICAL:** Denormalize pedigree IDs (Phase 1)
2. 🔶 **HIGH:** Fill trainer locations (Phase 2)
3. 🔷 **MEDIUM:** Fill entity statistics (Phase 3)
4. 🟢 **LOW:** Fill horse enrichment (Phase 4)

---

## Next Steps

Create autonomous agent script: `scripts/fill_missing_data.py` with:
- Checkpoint-based resume capability
- Progress tracking
- Error handling
- Rate limiting
- Statistics reporting
- Dry-run mode

Command interface:
```bash
# Run all phases
python3 scripts/fill_missing_data.py --all

# Run specific phase
python3 scripts/fill_missing_data.py --phase 1

# Check status (dry run)
python3 scripts/fill_missing_data.py --check-status

# Resume from checkpoint
python3 scripts/fill_missing_data.py --resume
```
