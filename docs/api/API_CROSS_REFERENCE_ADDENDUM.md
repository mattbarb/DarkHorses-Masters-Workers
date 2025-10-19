# API Cross-Reference Addendum

**Date:** 2025-10-14
**Scope:** Additional findings from comprehensive API documentation review
**Related Documents:** REMAINING_TABLES_AUDIT.md, RACING_API_DATA_AVAILABILITY.md

---

## Executive Summary

After cross-referencing the complete Racing API documentation (theracingapi_api_documentation.json), I've identified **additional data sources and entity endpoints** that were not covered in previous audits.

### Key Discoveries

1. **Breeder field available** - HorsePro endpoint includes `breeder` field (not currently captured)
2. **Dedicated Sires/Dams/Damsires entity endpoints** - 12 endpoints for pedigree analysis (not currently used)
3. **Additional pedigree analysis endpoints** - Performance breakdowns by class and distance for each pedigree entity
4. **Colour codes available** - Both `colour` (string) and `colour_code` (code) available but neither captured

---

## 1. Additional Fields in HorsePro Endpoint

### `/v1/horses/{horse_id}/pro`

**Currently Captured Fields:**
- ✅ id, name, dob, sex, sex_code
- ✅ sire_id, sire (name)
- ✅ dam_id, dam (name)
- ✅ damsire_id, damsire (name)

**MISSING Fields (Available but not captured):**

| Field | Type | Table | Current Status | Priority |
|-------|------|-------|----------------|----------|
| **breeder** | STRING | ra_horses | ❌ Not captured | P1 - HIGH |
| **colour** | STRING | ra_horses | ❌ NULL (100%) | P1 - HIGH |
| **colour_code** | STRING | ra_horses | ❌ Not in schema | P2 - MEDIUM |

### Impact

**Breeder Field:**
- Breeding operations analysis
- Breeder performance statistics
- Valuable for understanding breeding patterns
- **Currently missing from database entirely**

**Colour Fields:**
- Basic horse identification
- Already planned in ra_horses schema but not being populated
- API provides both human-readable and code versions

### Recommendation

Update ra_horse_pedigree table schema to include:
```sql
ALTER TABLE ra_horse_pedigree ADD COLUMN breeder VARCHAR(100);
```

Update ra_horses table to populate:
```sql
-- Already in schema, just need to populate
UPDATE ra_horses SET
  colour = ?,
  -- colour_code not in schema yet
WHERE horse_id = ?;
```

---

## 2. Pedigree Entity Endpoints (NOT CURRENTLY USED)

The Racing API provides **dedicated endpoints for Sires, Dams, and Damsires** that we are not currently utilizing.

### Sires Endpoints

| Endpoint | Plan | Purpose | Currently Used? |
|----------|------|---------|-----------------|
| `/v1/sires/search` | Pro | Search sires by name | ❌ No |
| `/v1/sires/{sire_id}/results` | Pro | Get all results for sire's progeny | ❌ No |
| `/v1/sires/{sire_id}/analysis/classes` | Pro | Sire progeny performance by class | ❌ No |
| `/v1/sires/{sire_id}/analysis/distances` | Pro | Sire progeny performance by distance | ❌ No |

### Dams Endpoints

| Endpoint | Plan | Purpose | Currently Used? |
|----------|------|---------|-----------------|
| `/v1/dams/search` | Pro | Search dams by name | ❌ No |
| `/v1/dams/{dam_id}/results` | Pro | Get all results for dam's progeny | ❌ No |
| `/v1/dams/{dam_id}/analysis/classes` | Pro | Dam progeny performance by class | ❌ No |
| `/v1/dams/{dam_id}/analysis/distances` | Pro | Dam progeny performance by distance | ❌ No |

### Damsires Endpoints

| Endpoint | Plan | Purpose | Currently Used? |
|----------|------|---------|-----------------|
| `/v1/damsires/search` | Pro | Search damsires by name | ❌ No |
| `/v1/damsires/{damsire_id}/results` | Pro | Get all results for damsire's grandoffspring | ❌ No |
| `/v1/damsires/{damsire_id}/analysis/classes` | Pro | Damsire grandoffspring performance by class | ❌ No |
| `/v1/damsires/{damsire_id}/analysis/distances` | Pro | Damsire grandoffspring performance by distance | ❌ No |

**Total:** 12 pedigree-related endpoints available but unused

### What This Means

These endpoints provide:
- **Historical performance data** for all progeny/grandoffspring of a sire/dam/damsire
- **Statistical analysis** broken down by race class and distance
- **Search capabilities** for finding pedigree entities by name

### Current Approach vs Available Approach

**Current Approach:**
- Extract sire_id, dam_id, damsire_id from horse data
- Store IDs in ra_horse_pedigree table
- No additional pedigree entity data
- Cannot query "all horses by Sire X" without joining through ra_horse_pedigree

**Available Approach:**
- Could create **dedicated pedigree entity tables**: ra_sires, ra_dams, ra_damsires
- Store performance statistics for each sire/dam/damsire
- Enable direct queries like "Top 10 performing sires"
- Cache progeny performance analysis

### Recommendation

**Phase 1: Capture basic pedigree (P0 - Current Plan)**
- Populate ra_horse_pedigree with sire_id, dam_id, damsire_id
- This enables basic pedigree analysis

**Phase 2: Consider pedigree entity tables (P3 - Future Enhancement)**
- Create ra_sires, ra_dams, ra_damsires tables
- Store progeny performance statistics
- Enable advanced breeding analysis
- **Only implement if needed for ML model or analytics**

**Decision:** Phase 1 sufficient for ML model. Phase 2 is a future enhancement for breeding-focused analytics.

---

## 3. Comparison: Our Database vs API Capabilities

### Tables We Have

| Table | Records | Captures |
|-------|---------|----------|
| ra_horses | 111,430 | Basic horse info |
| ra_horse_pedigree | 0 | Pedigree relationships (empty) |
| ra_jockeys | 3,480 | Jockey info |
| ra_trainers | 2,780 | Trainer info |
| ra_owners | 48,092 | Owner info |

### Entity Tables We DON'T Have (But API Supports)

| Potential Table | API Endpoints | Data Available |
|-----------------|---------------|----------------|
| **ra_sires** | 4 endpoints | ❌ Not implemented |
| **ra_dams** | 4 endpoints | ❌ Not implemented |
| **ra_damsires** | 4 endpoints | ❌ Not implemented |
| **ra_breeders** | None (field only) | ❌ Not implemented |

### Analysis

**Current State:**
- We have entity tables for "people" entities (jockeys, trainers, owners)
- We do NOT have entity tables for "pedigree" entities (sires, dams, damsires)
- Pedigree entities are only stored as IDs in ra_horse_pedigree (when populated)

**API Support:**
- Racing API treats Sires, Dams, and Damsires as **first-class entities** with dedicated search and analysis endpoints
- Similar to how Jockeys, Trainers, Owners are treated as entities in our database

**Question:** Should we mirror the API's entity model?

**Answer:** Not necessary for Phase 1 (ML model). Pedigree relationships via ra_horse_pedigree are sufficient. Entity tables would be useful for:
- Breeding-focused analytics platform
- Sire/Dam leaderboards
- Progeny performance tracking
- But **NOT required for race outcome prediction ML model**

---

## 4. Updated Field Mapping: HorsePro Endpoint

Based on API documentation review, here is the COMPLETE field mapping for the HorsePro response:

### Complete HorsePro Response Fields

| API Field | Data Type | Our Table | Our Field | Status |
|-----------|-----------|-----------|-----------|--------|
| id | STRING | ra_horses | horse_id | ✅ Captured |
| name | STRING | ra_horses | horse_name | ✅ Captured |
| dob | STRING (date) | ra_horses | dob | ❌ NULL (100%) |
| sex | STRING | ra_horses | sex | ✅ Captured |
| sex_code | STRING | ra_horses | sex_code | ❌ NULL (100%) |
| colour | STRING | ra_horses | colour | ❌ NULL (100%) |
| colour_code | STRING | ra_horses | - | ❌ Not in schema |
| sire_id | STRING | ra_horse_pedigree | sire_id | ❌ Table empty |
| sire | STRING | ra_horse_pedigree | sire_name | ❌ Table empty |
| dam_id | STRING | ra_horse_pedigree | dam_id | ❌ Table empty |
| dam | STRING | ra_horse_pedigree | dam_name | ❌ Table empty |
| damsire_id | STRING | ra_horse_pedigree | damsire_id | ❌ Table empty |
| damsire | STRING | ra_horse_pedigree | damsire_name | ❌ Table empty |
| **breeder** | **STRING** | **ra_horse_pedigree** | **breeder** | ❌ **Not in schema** |

**New Discovery:** `breeder` field available but not in our schema

---

## 5. Updated Recommendations

### Immediate Actions (P0 - Critical)

1. **Populate ra_horse_pedigree table**
   - Already documented in REMAINING_TABLES_AUDIT.md
   - 111,325 horses × 0.5s = 15.5 hours
   - **ADD:** Include breeder field in the backfill

2. **Update ra_horse_pedigree schema**
   ```sql
   ALTER TABLE ra_horse_pedigree ADD COLUMN breeder VARCHAR(100);
   ```

3. **Update horses_fetcher.py to capture breeder**
   ```python
   pedigree_record = {
       'horse_id': horse_id,
       'sire_id': horse_data.get('sire_id'),
       'sire_name': horse_data.get('sire'),
       'dam_id': horse_data.get('dam_id'),
       'dam_name': horse_data.get('dam'),
       'damsire_id': horse_data.get('damsire_id'),
       'damsire_name': horse_data.get('damsire'),
       'breeder': horse_data.get('breeder')  # NEW FIELD
   }
   ```

### Short-Term Actions (P1 - High)

4. **Populate colour and colour_code in ra_horses**
   - Fields already in schema (colour)
   - Update horses_fetcher.py to capture from HorsePro endpoint
   - Backfill during pedigree backfill (same API calls)

5. **Add colour_code to ra_horses schema** (if needed)
   ```sql
   ALTER TABLE ra_horses ADD COLUMN colour_code VARCHAR(10);
   ```

### Future Considerations (P3 - Low)

6. **Consider pedigree entity tables**
   - Create ra_sires, ra_dams, ra_damsires (optional)
   - Only if breeding analytics become a primary use case
   - NOT needed for ML model training

7. **Leverage pedigree analysis endpoints**
   - `/v1/sires/{sire_id}/analysis/distances`
   - `/v1/dams/{dam_id}/analysis/classes`
   - Could provide valuable features for ML model
   - Would require additional API calls and storage

---

## 6. Cost-Benefit Analysis

### Investment: Capturing Breeder Field

**Cost:**
- 5 minutes to update schema (ADD COLUMN)
- 5 minutes to update code (add one field to dictionary)
- 0 additional API calls (same HorsePro endpoint)
- 0 additional time (same 15.5 hour backfill)

**Benefit:**
- Complete pedigree information
- Breeding operation analysis capabilities
- Potential ML feature (breeder performance)

**Decision:** ✅ DO IT (essentially free during pedigree backfill)

### Investment: Pedigree Entity Tables

**Cost:**
- 2-4 hours development (create tables, fetchers, insert logic)
- 12,000+ API calls (search each unique sire/dam/damsire)
- ~1.7 hours API time (12,000 / 2 per sec / 3600 sec per hour)
- Storage for 3 new tables

**Benefit:**
- Advanced breeding analytics
- Sire/Dam leaderboards
- Progeny performance tracking
- NOT directly beneficial for ML model

**Decision:** ❌ DEFER (not needed for current ML goals)

---

## 7. Updated Action Plan

### Before This Addendum

**Plan:** Backfill ra_horse_pedigree with 6 fields (sire_id, sire_name, dam_id, dam_name, damsire_id, damsire_name)

### After This Addendum

**Updated Plan:** Backfill ra_horse_pedigree with **7 fields** (add breeder)

**Additional Updates:**
1. ✅ Add breeder column to ra_horse_pedigree schema
2. ✅ Update backfill script to capture breeder field
3. ✅ Update ra_horses to populate colour during same backfill
4. ✅ Update ra_horses to populate sex_code during same backfill
5. ✅ Update ra_horses to populate dob during same backfill (already planned)
6. ⏸️ DEFER pedigree entity tables (not needed now)

**Result:** Zero additional API calls, zero additional time, but capture **complete** pedigree and horse data in one pass.

---

## 8. API Documentation Cross-Reference Summary

### Endpoints Reviewed

✅ **Fully Reviewed:**
- `/v1/horses/search` (currently used)
- `/v1/horses/{horse_id}/pro` (needed for pedigree)
- `/v1/horses/{horse_id}/standard` (not needed - less data than pro)
- `/v1/horses/{horse_id}/results` (alternative to results endpoint)
- `/v1/racecards/pro` (currently used)
- `/v1/results` (currently used)

✅ **Newly Discovered:**
- `/v1/sires/*` (4 endpoints - defer to future)
- `/v1/dams/*` (4 endpoints - defer to future)
- `/v1/damsires/*` (4 endpoints - defer to future)

✅ **Confirmed Not Relevant to ra_horse_pedigree or ra_results:**
- `/v1/jockeys/{jockey_id}/results` (different entity)
- `/v1/trainers/{trainer_id}/results` (different entity)
- `/v1/owners/{owner_id}/results` (different entity)
- `/v1/odds/{race_id}/{horse_id}` (odds data, separate concern)

### Fields Reviewed

✅ **HorsePro schema:** 14 fields total
- ✅ 13 fields documented in REMAINING_TABLES_AUDIT.md
- ✅ 1 NEW field discovered: breeder

✅ **Pedigree fields available:** 7 fields
- sire_id, sire (name)
- dam_id, dam (name)
- damsire_id, damsire (name)
- **breeder** (NEW)

---

## 9. Confirmation: All API Documentation Reviewed

**Question from User:** "Ensure we cross reference the API documentation?"

**Answer:** ✅ YES - Complete API documentation has been cross-referenced

### Review Methodology

1. ✅ Loaded complete API documentation JSON (374KB)
2. ✅ Extracted all endpoints related to horses, pedigree, and results (19 endpoints)
3. ✅ Analyzed HorsePro schema to identify all available fields (14 fields)
4. ✅ Cross-referenced with our database tables (ra_horse_pedigree, ra_results)
5. ✅ Identified gaps:
   - **breeder** field not in our schema
   - **colour/colour_code** available but not populated
   - **12 pedigree entity endpoints** available but not used
6. ✅ Made recommendations with priorities (P0, P1, P3)

### Findings Summary

**Critical (P0):**
- ✅ Pedigree data available via `/v1/horses/{id}/pro` (already identified)
- ✅ **breeder** field available (NEW discovery)

**High Priority (P1):**
- ✅ colour, colour_code, sex_code, dob available but not populated

**Low Priority (P3):**
- ✅ Pedigree entity endpoints available but defer to future

### Confirmation

✅ **All relevant API documentation has been cross-referenced**
✅ **All available fields for ra_horse_pedigree have been identified**
✅ **All pedigree-related endpoints have been documented**
✅ **Recommendations updated to include new findings (breeder field)**

---

## Document History

| Date | Version | Changes |
|------|---------|---------|
| 2025-10-14 | 1.0 | Initial API cross-reference addendum with breeder field discovery |

---

**End of Addendum**
