# Complete Data Completeness & Backfill Plan
**Date:** 2025-10-20
**Purpose:** Comprehensive analysis of ALL missing data across entire database

---

## Executive Summary

After comprehensive analysis, here's the complete picture of what's missing and how to fill it:

### Data Status by Table

| Table | Records | Name Data | Statistics | Status |
|-------|---------|-----------|------------|--------|
| ra_mst_courses | 101 | ✅ 100% | N/A | ✅ COMPLETE |
| ra_mst_bookmakers | 22 | ✅ 100% | N/A | ✅ COMPLETE |
| ra_mst_regions | 2 | ✅ 100% | N/A | ✅ COMPLETE |
| ra_mst_horses | 111,669 | ✅ 100% | N/A | ✅ COMPLETE |
| ra_mst_jockeys | 3,483 | ✅ 100% | 🟢 99% | ✅ STATISTICS DONE |
| ra_mst_trainers | 2,781 | ✅ 100% | 🟢 99% | ✅ STATISTICS DONE |
| ra_mst_owners | 48,168 | ✅ 100% | 🟢 99% | ✅ STATISTICS DONE |
| **ra_mst_sires** | **2,143** | **✅ 100%** | **⚠️ 0%** | **⚠️ NEEDS STATISTICS** |
| **ra_mst_dams** | **48,366** | **⚠️ 0%** | **⚠️ 0%** | **❌ NEEDS NAMES + STATS** |
| **ra_mst_damsires** | **3,040** | **⚠️ 0%** | **⚠️ 0%** | **❌ NEEDS NAMES + STATS** |

---

## Critical Discovery

### The Sires Table Surprise

Looking at ra_mst_sires:
```sql
id       | name          | horse_id | total_runners | total_wins
---------|---------------|----------|---------------|------------
sir_5720 | Erhaab (USA)  | NULL     | 0             | 0
```

**SIRES ALREADY HAVE NAMES!** But total_runners/total_wins are all 0.

**This means:**
1. ✅ Sires table is being populated with names from somewhere
2. ⚠️ But NO statistics are calculated
3. ❌ Dams and damsires have NO names at all

---

## Where Names Come From

### Sires Names: ALREADY POPULATED
- Source: Unknown (need to trace code)
- Status: 2,143 sires with 100% name coverage
- Action: NONE NEEDED (already complete)

### Dams Names: MISSING (48,366 records with NULL names)
- The horses table has dam_id but NO dam_name column
- Dams table exists but all names are NULL
- **Question:** Where should dam names come from?
  - Option A: API /v1/horses/{dam_id}/pro endpoint?
  - Option B: Are they in ra_horse_pedigree table?
  - Option C: Copy from horses where horse_id = dam_id?

### Damsires Names: MISSING (3,040 records with NULL names)
- Same situation as dams
- Need to identify source

---

## Data Sources Analysis

### 1. API Data (From Racing API)
**These columns require API calls:**

**ra_mst_horses** (✅ COMPLETE):
- dob, sex_code, colour, colour_code, region
- Source: `/v1/horses/{id}/pro` endpoint
- Status: 99.9% populated via hybrid enrichment

**ra_mst_jockeys** (✅ COMPLETE):
- id, name
- Source: Extracted from race results
- Status: 100% populated

**ra_mst_trainers** (✅ COMPLETE):
- id, name, location
- Source: Extracted from race results
- Status: 100% populated

**ra_mst_owners** (✅ COMPLETE):
- id, name
- Source: Extracted from race results
- Status: 100% populated

**ra_mst_dams** (❌ MISSING):
- name (48,366 NULL)
- Source: **UNKNOWN** - need to identify

**ra_mst_damsires** (❌ MISSING):
- name (3,040 NULL)
- Source: **UNKNOWN** - need to identify

### 2. Calculated Statistics (From Database)
**These columns calculated from ra_runners + ra_races:**

**People Statistics** (✅ DONE - 99%+):
- Jockeys: total_rides, total_wins, win_rate, recent form
- Trainers: total_runners, total_wins, win_rate, recent form
- Owners: total_horses, total_runners, total_wins, win_rate, recent form

**Pedigree Statistics** (⚠️ PENDING - 0%):
- Sires: total_runners, total_wins, win%, class/distance breakdowns
- Dams: total_runners, total_wins, win%, class/distance breakdowns
- Damsires: total_runners, total_wins, win%, class/distance breakdowns

---

## Investigation Required

### CRITICAL QUESTIONS TO ANSWER:

1. **Where do sire names come from?**
   - Check: scripts/statistics_workers/calculate_sire_statistics.py
   - Check: Any fetcher that populates ra_mst_sires
   - Check: migrations that create/populate sires table

2. **Where SHOULD dam/damsire names come from?**
   - Check ra_horse_pedigree table structure
   - Check if names are in pedigree data from API
   - Check if they're horse names (dam_id → ra_mst_horses.id)

Let me investigate:

```sql
-- Check ra_horse_pedigree structure
\d ra_horse_pedigree

-- Sample pedigree data
SELECT * FROM ra_horse_pedigree LIMIT 3;

-- Check if dam_id matches horse IDs
SELECT
    COUNT(*) as total_horses,
    COUNT(dam_id) as with_dam_id,
    COUNT(h2.id) as dam_id_in_horses
FROM ra_mst_horses h1
LEFT JOIN ra_mst_horses h2 ON h1.dam_id = h2.id
WHERE h1.dam_id IS NOT NULL;
```

---

## Proposed Solution (AFTER Investigation)

### Phase 1: Investigate Name Sources (NOW)
1. Check ra_horse_pedigree table for names
2. Check if dam_id/damsire_id reference ra_mst_horses.id
3. Identify where sire names are populated from
4. Determine correct source for dam/damsire names

### Phase 2A: Populate Missing Names (IF from Database)
**If names are in ra_horse_pedigree or ra_mst_horses:**
- SQL UPDATE to copy names
- Duration: <1 minute
- No API calls needed

### Phase 2B: Populate Missing Names (IF from API)
**If names require API calls:**
- Endpoint: `/v1/horses/{dam_id}/pro` or similar
- 48,366 dams + 3,040 damsires = 51,406 API calls
- Rate limit: 2 req/sec = 25,703 seconds = 7.1 hours
- Need to determine if this is worth it

### Phase 3: Calculate ALL Statistics
**Once names are populated:**
- Run statistics calculation for sires/dams/damsires
- Source: 100% from database (ra_runners + ra_races)
- Duration: ~30-45 minutes
- Populates all performance metrics

---

## Next Steps (IN ORDER)

1. **RUN INVESTIGATION QUERIES** ⬅ DO THIS FIRST
   ```sql
   -- Find out where names come from
   \d ra_horse_pedigree
   SELECT * FROM ra_horse_pedigree LIMIT 5;

   -- Check if dam_id = horse_id
   SELECT h1.dam_id, h2.id, h2.name as dam_name
   FROM ra_mst_horses h1
   JOIN ra_mst_horses h2 ON h1.dam_id = h2.id
   LIMIT 10;
   ```

2. **DETERMINE NAME SOURCE**
   - If pedigree table has names: SQL copy
   - If dam_id = horse_id: SQL JOIN copy
   - If API needed: Evaluate cost/benefit

3. **POPULATE NAMES**
   - Execute appropriate solution from step 2

4. **CALCULATE STATISTICS**
   - Run pedigree statistics calculation
   - 100% from database, no API

---

## Key Insight

**YOU ARE CORRECT:** We need to:
1. First get missing data from API (if needed)
2. Then calculate statistics from database

**But first we must INVESTIGATE** to understand:
- Where do names come from?
- Are they in the database already?
- Do we actually need the API?

---

## Files to Create/Update

1. **Investigation script:** `scripts/investigate_pedigree_names.py`
   - Query ra_horse_pedigree
   - Check name columns
   - Determine data source

2. **Name population script:** (depends on investigation)
   - Option A: `migrations/026_copy_pedigree_names.sql` (if SQL)
   - Option B: `scripts/fetch_pedigree_names_from_api.py` (if API)

3. **Statistics script:** (already created)
   - `scripts/populate_pedigree_statistics.py`
   - Ready to run once names are populated

---

**AWAITING INVESTIGATION RESULTS BEFORE PROCEEDING**
