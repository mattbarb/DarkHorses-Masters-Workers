# Complete Data Capture Implementation Guide

**Date:** 2025-10-14
**Goal:** Capture 100% of available data from Racing API
**Status:** Ready to implement

---

## Executive Summary

This guide provides step-by-step instructions to ensure workers capture 100% of available data from the Racing API. Based on comprehensive audits of all 9 ra_* tables and the complete Racing API documentation, we've identified missing fields and created the necessary migrations, scripts, and validations.

### What's Being Added

1. **Pedigree Data** - ra_horse_pedigree table (currently empty → 80-90% populated)
2. **Breeder Field** - New field discovered in API audit
3. **Colour Code** - Additional field for horse colour coding
4. **Complete Horse Metadata** - DOB, sex_code, colour, region (currently NULL → 95%+ populated)

### Expected Outcome

- ra_horse_pedigree: 0 records → ~100,000 records (90% of horses)
- Horses with DOB: 0% → 95%+
- Horses with colour: 0% → 95%+
- Pedigree with breeder: 0% → 90%+
- **Overall data completeness: 70% → 95%+**

---

## Implementation Steps

### Step 1: Apply Database Migration ⏱️ 2 minutes

**File:** `migrations/008_add_pedigree_and_horse_fields.sql`

**What it does:**
- Adds `breeder` column to ra_horse_pedigree
- Adds `colour_code` column to ra_horses
- Verifies existing fields (dob, sex_code, colour, region)
- Creates indexes for performance

**How to run:**

**Option A: Via Supabase Dashboard (Recommended)**
```
1. Go to https://supabase.com/dashboard
2. Select your project
3. Go to SQL Editor
4. Copy/paste the contents of migrations/008_add_pedigree_and_horse_fields.sql
5. Click "Run"
6. Check output for success messages
```

**Option B: Via psql**
```bash
psql "postgresql://postgres.amsjvmlaknnvppxsgpfk:[YOUR-PASSWORD]@aws-0-us-west-1.pooler.supabase.com:6543/postgres" \
  -f migrations/008_add_pedigree_and_horse_fields.sql
```

**Validation:**
```sql
-- Check breeder column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_horse_pedigree' AND column_name = 'breeder';

-- Check colour_code column exists
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_horses' AND column_name = 'colour_code';
```

**Expected output:**
```
============================================
MIGRATION 008 VALIDATION
============================================
Pedigree records: 0
Horses with DOB: 0
Horses with colour: 0
Pedigree records with breeder: 0
============================================
NOTE: ra_horse_pedigree is empty. Run backfill script to populate.
```

---

### Step 2: Run Backfill Script (Test Mode) ⏱️ 1 minute

**File:** `scripts/backfill_horse_pedigree.py`

**What it does:**
- Fetches detailed horse data from `/v1/horses/{id}/pro` endpoint
- Updates ra_horses with dob, sex_code, colour, colour_code, region
- Inserts pedigree data (sire, dam, damsire, breeder) into ra_horse_pedigree

**Test mode (10 horses):**
```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers

SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[YOUR-KEY]' \
RACING_API_USERNAME='[YOUR-USERNAME]' \
RACING_API_PASSWORD='[YOUR-PASSWORD]' \
python3 scripts/backfill_horse_pedigree.py --test
```

**Expected output:**
```
TEST MODE: Processing only 10 horses
Processing 10 horses
Estimated time: 0.0 hours (0 minutes)
Ready to process 10 horses (est. 0.0 hours)? (yes/no):
```

**What to check:**
- API calls successful (no errors)
- Pedigree records inserted
- Horse records updated with DOB, colour, etc.

---

### Step 3: Validate Test Results ⏱️ 1 minute

**File:** `scripts/validate_data_completeness.py`

**Run validation:**
```bash
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[YOUR-KEY]' \
python3 scripts/validate_data_completeness.py
```

**Expected output (after test):**
```
================================================================================
TABLE RECORD COUNTS
================================================================================
✅ ra_courses                          101 records
✅ ra_bookmakers                        19 records
✅ ra_horses                       111,430 records
✅ ra_jockeys                        3,480 records
✅ ra_trainers                       2,780 records
✅ ra_owners                        48,092 records
✅ ra_races                        136,648 records
✅ ra_runners                      379,422 records
✅ ra_horse_pedigree                    10 records  <-- NEW!
❌ ra_results                            0 records  <-- Expected (deprecated)

================================================================================
HORSE PEDIGREE COVERAGE
================================================================================
Total horses: 111,430
Horses with pedigree: 10 (0.0%)  <-- Will increase after full backfill
Horses with DOB: 10 (0.0%)       <-- Will increase after full backfill
Horses with colour: 10 (0.0%)    <-- Will increase after full backfill
```

**If test successful, proceed to full backfill.**

---

### Step 4: Run Full Backfill ⏱️ 15.5 hours

**IMPORTANT:** This will run for 15-16 hours. Run in a screen/tmux session or background.

**Full backfill (all 111,325 horses):**
```bash
# Start a screen session (recommended)
screen -S pedigree_backfill

# Run backfill
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[YOUR-KEY]' \
RACING_API_USERNAME='[YOUR-USERNAME]' \
RACING_API_PASSWORD='[YOUR-PASSWORD]' \
python3 scripts/backfill_horse_pedigree.py

# Detach from screen: Ctrl+A, then D
# Reattach later: screen -r pedigree_backfill
```

**Progress monitoring:**
The script logs progress every 100 horses:
```
Progress: 1000/111325 (0.9%) | Pedigrees: 903 | Errors: 2 | Rate: 2.0/sec | ETA: 15.3h
Progress: 2000/111325 (1.8%) | Pedigrees: 1806 | Errors: 4 | Rate: 2.0/sec | ETA: 15.2h
...
```

**Alternative: Run in chunks (if you want to stop/resume)**
```bash
# Process first 10,000 horses
python3 scripts/backfill_horse_pedigree.py --max 10000

# Resume from horse 10,000
python3 scripts/backfill_horse_pedigree.py --skip 10000 --max 10000

# And so on...
```

**Expected completion time:**
- 111,325 horses × 0.5 seconds = 55,662 seconds
- 55,662 seconds / 3600 = **15.5 hours**

---

### Step 5: Validate Full Backfill ⏱️ 1 minute

**After backfill completes, run validation:**
```bash
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[YOUR-KEY]' \
python3 scripts/validate_data_completeness.py
```

**Expected output (after full backfill):**
```
================================================================================
HORSE PEDIGREE COVERAGE
================================================================================
Total horses: 111,430
Horses with pedigree: 100,287 (90.0%)    ✅ Target: 80%+
Horses with DOB: 109,362 (98.1%)         ✅ Target: 90%+
Horses with colour: 108,948 (97.8%)      ✅ Target: 90%+
Horses with colour_code: 108,948 (97.8%) ✅ Target: 90%+
Pedigree with breeder: 90,258 (90.0%)    ✅ Target: 80%+

================================================================================
POSITION DATA COVERAGE
================================================================================
Total runners: 379,422
Runners with position: 368,152 (97.0%)        ✅ Good coverage
Runners with distance_beaten: 367,890 (96.9%) ✅ Good coverage
Runners with prize_won: 368,152 (97.0%)       ✅ Good coverage
Runners with starting_price: 368,152 (97.0%)  ✅ Good coverage

================================================================================
RATINGS DATA COVERAGE
================================================================================
Total runners: 379,422
Runners with official_rating: 265,595 (70.0%) ✅ OK (varies by race type)
Runners with RPR: 303,538 (80.0%)             ✅ OK
Runners with TSR: 265,595 (70.0%)             ✅ OK

================================================================================
VALIDATION SUMMARY
================================================================================
✅ All validation checks passed!
```

---

### Step 6: Verify Workers Capture Data Going Forward ⏱️ 5 minutes

**Updated files:**
- ✅ `fetchers/horses_fetcher.py` - Now captures colour_code
- ✅ `fetchers/races_fetcher.py` - Already captures complete data (from WORKER_FIXES_COMPLETED.md)
- ✅ `fetchers/results_fetcher.py` - Already captures position data (from WORKER_FIXES_COMPLETED.md)

**Test forward capture:**
```bash
# Run horses fetcher (small test)
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='[YOUR-KEY]' \
RACING_API_USERNAME='[YOUR-USERNAME]' \
RACING_API_PASSWORD='[YOUR-PASSWORD]' \
python3 fetchers/horses_fetcher.py

# Check logs for colour_code being captured
# Expected: No errors, colour_code field populated
```

**For ongoing operations:**
The workers are now configured to capture:
- ✅ All horse fields (including colour_code, dob, sex_code, colour, region)
- ✅ All pedigree fields (including breeder)
- ✅ All race fields (already complete)
- ✅ All runner fields (already complete after WORKER_FIXES)
- ✅ All position data (already complete after WORKER_FIXES)

---

## Expected Results

### Before Implementation

| Metric | Value |
|--------|-------|
| ra_horse_pedigree records | 0 (EMPTY) |
| Horses with DOB | 0% |
| Horses with colour | 0% |
| Horses with colour_code | 0% |
| Pedigree with breeder | N/A (table empty) |
| Overall data completeness | ~70% |

### After Implementation

| Metric | Value |
|--------|-------|
| ra_horse_pedigree records | ~100,000 (90% of horses) |
| Horses with DOB | 95%+ |
| Horses with colour | 95%+ |
| Horses with colour_code | 95%+ |
| Pedigree with breeder | 90%+ |
| **Overall data completeness** | **95%+** |

---

## Troubleshooting

### Issue: API Rate Limit Errors

**Symptoms:**
```
Error fetching horse 12345: 429 Too Many Requests
```

**Solution:**
The backfill script already includes rate limiting (0.5s between requests = 2/sec).
If you still get errors, increase the sleep time in `backfill_horse_pedigree.py`:
```python
# Change line 140:
time.sleep(0.5)  # Change to 0.6 or 0.7
```

### Issue: Database Connection Errors

**Symptoms:**
```
Error updating ra_horses for 12345: Connection timeout
```

**Solution:**
1. Check your Supabase service key is correct
2. Check your internet connection
3. Restart the backfill from where it left off using `--skip`:
```bash
# If failed at horse 5000
python3 scripts/backfill_horse_pedigree.py --skip 5000
```

### Issue: Pedigree Coverage Below 80%

**Symptoms:**
```
⚠️  Pedigree coverage at 65.0% (target: 80%+)
```

**Possible causes:**
1. Backfill didn't complete (check logs)
2. Many horses don't have pedigree data in API (expected for some old horses)
3. API errors during backfill

**Solution:**
1. Check backfill completion:
```sql
SELECT COUNT(*) FROM ra_horse_pedigree;
-- Should be ~100,000
```

2. Check for horses without pedigree:
```sql
SELECT COUNT(*) as horses_without_pedigree
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id
WHERE p.horse_id IS NULL;
```

3. Re-run backfill for missing horses:
```sql
-- Get IDs of horses without pedigree
SELECT h.horse_id
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id
WHERE p.horse_id IS NULL
LIMIT 10;

-- Manually process these with the backfill script
```

---

## Post-Implementation Checklist

- [ ] Migration 008 applied successfully
- [ ] Test backfill (10 horses) completed
- [ ] Test validation passed
- [ ] Full backfill started (screen/tmux session)
- [ ] Full backfill completed (15.5 hours)
- [ ] Final validation passed
- [ ] Pedigree coverage ≥ 80%
- [ ] DOB coverage ≥ 90%
- [ ] Colour coverage ≥ 90%
- [ ] Position data coverage ≥ 60% (varies with results vs racecards ratio)
- [ ] Forward capture verified (new horses get pedigree data)

---

## Files Modified/Created

### Modified Files
1. `fetchers/horses_fetcher.py`
   - Added: colour_code field capture (line 109)
   - Already captures: breeder field (line 128)

### New Files Created
1. `migrations/008_add_pedigree_and_horse_fields.sql`
   - Adds breeder and colour_code columns
   - Validates existing fields

2. `scripts/backfill_horse_pedigree.py`
   - Backfills pedigree data for all horses
   - Supports test mode, skip, and max parameters
   - Includes progress tracking and rate limiting

3. `scripts/validate_data_completeness.py`
   - Validates data completeness across all tables
   - Checks pedigree, position data, and ratings coverage
   - Provides actionable warnings

4. `docs/COMPLETE_DATA_CAPTURE_GUIDE.md` (this file)
   - Step-by-step implementation guide

5. `docs/REMAINING_TABLES_AUDIT.md`
   - Complete audit of ra_horse_pedigree and ra_results

6. `docs/API_CROSS_REFERENCE_ADDENDUM.md`
   - Additional findings from API documentation review
   - Discovery of breeder and colour_code fields

---

## Timeline

| Step | Time | When |
|------|------|------|
| 1. Apply Migration | 2 min | Now |
| 2. Test Backfill | 1 min | Now |
| 3. Validate Test | 1 min | Now |
| 4. Full Backfill | 15.5 hrs | Overnight |
| 5. Final Validation | 1 min | Next day |
| 6. Verify Forward Capture | 5 min | Next day |
| **Total** | **15.7 hrs** | **~16 hours** |

---

## Next Steps After Implementation

### Short-Term (Next Week)
1. ✅ Monitor workers to ensure new horses get pedigree data
2. ✅ Run validation weekly to catch any data gaps
3. ✅ Check pedigree coverage stays above 80%

### Medium-Term (Next Month)
1. Consider implementing pedigree entity tables (ra_sires, ra_dams) if breeding analytics needed
2. Leverage pedigree analysis endpoints for ML features
3. Add breeder performance statistics

### Long-Term (Next Quarter)
1. Build ML Data API (already designed in previous docs)
2. Train ML model with complete 95%+ data coverage
3. Deploy prediction system

---

## Support

**Related Documents:**
- WORKER_FIXES_COMPLETED.md - Position data fixes (already done)
- REMAINING_TABLES_AUDIT.md - Complete table audit
- API_CROSS_REFERENCE_ADDENDUM.md - API documentation findings
- RACING_API_DATA_AVAILABILITY.md - Complete API capabilities
- DATA_SOURCES_FOR_API.md - Field mappings for API development

**Questions?**
Review the related documents above or check logs in:
- `logs/backfill_horse_pedigree.log` (when running backfill)
- `logs/validate_data_completeness.log` (when running validation)

---

**End of Implementation Guide**
**Status:** Ready to implement
**Expected Outcome:** 95%+ data completeness
**Estimated Time:** 16 hours (mostly automated)
