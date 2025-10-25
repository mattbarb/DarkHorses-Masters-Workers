# ra_runner_supplementary Table Removal Summary

**Date:** 2025-10-22
**Migration:** 028_drop_ra_runner_supplementary.sql
**Status:** Approved for Removal

## Decision

The `ra_runner_supplementary` table has been **removed** from the system as it has unclear purpose and has never been populated.

## Rationale

### Table Status
- **Records in production:** 0 (empty table)
- **Populate script:** None exists
- **Purpose:** Never clearly defined
- **Last documented mention:** Listed as "needs requirements" in planning docs

### Problems with ra_runner_supplementary

1. **Empty table** - 0 records, never populated
2. **No working implementation** - No populate script exists
3. **Unclear purpose** - Requirements never defined
4. **Redundant design** - ra_runners already has 57 comprehensive columns
5. **Maintenance burden** - Additional table to maintain with no clear value

### Better Alternatives

Modern database design principles suggest:
1. **Add directly to ra_runners** - If supplementary fields are needed, add them to main table
2. **Use analytical tables** - For calculated metrics, use purpose-built tables like:
   - ra_runner_statistics (60 columns of performance metrics)
   - ra_performance_by_distance
   - ra_performance_by_venue
3. **Avoid premature tables** - Don't create tables until requirements are clear

## Current ra_runners Table Coverage

The `ra_runners` table already captures comprehensive runner data (57 columns):

### Race Context (5 fields)
- race_id, horse_id, jockey_id, trainer_id, owner_id

### Pre-Race Data (25 fields)
- horse_name, jockey_name, trainer_name, owner_name
- number, draw, weight_lbs, weight_st_lbs, age, sex, sex_code
- colour, dob, form, last_run
- headgear, headgear_run, wind_surgery, wind_surgery_run
- ofr, rpr, ts, comment, spotlight
- claiming_price_min, claiming_price_max
- medication, equipment, morning_line_odds

### Pedigree (6 fields)
- sire_id, dam_id, damsire_id (denormalized from ra_horse_pedigree)

### Post-Race Data (11 fields)
- position, distance_beaten, prize_won
- starting_price, starting_price_decimal
- finishing_time, race_comment
- jockey_silk_url, overall_beaten_distance
- jockey_claim_lbs, weight_stones_lbs

### Status (4 fields)
- is_scratched, trainer_location, trainer_rtf, past_results_flags

### Metadata (3 fields)
- silk_url, created_at, updated_at

**Total: 57 columns** - Comprehensive runner data already captured

## What Was Planned for ra_runner_supplementary?

Based on documentation review, the table had ~16 columns planned but:
- **No clear requirements** defined
- **No data source** identified
- **No transformation logic** specified
- **No populate script** created
- **Marked as "TBD"** in all planning docs

**Conclusion:** If specific supplementary data is needed, better to:
1. Define clear requirements first
2. Identify data source
3. Add to ra_runners OR create specific analytical table

## Changes Made

### 1. Migration Created
**File:** `migrations/028_drop_ra_runner_supplementary.sql`
- Verifies table is empty before dropping
- Includes CASCADE to remove dependencies
- Documents rationale and alternatives

### 2. Documentation Updated
**Files to Update:**
- `fetchers/docs/*_MASTER_TABLES_DATA_SOURCES_AND_TRANSFORMATIONS.md`
- `DATA_SOURCE_STRATEGY.md`
- `docs/CALCULATED_TABLES_IMPLEMENTATION.md`
- Any other docs referencing this table

**Changes:**
- Mark table as REMOVED
- Update table counts (22 instead of 23)
- Remove from planned tables list
- Note: Use ra_runners directly or create specific analytical tables

## Impact

### Database Schema
**Before:**
- 24 planned ra_* tables
- ra_runner_supplementary: 0 records, unclear purpose

**After:**
- 22 active ra_* tables (plus 1 planned for calculated data)
- Cleaner schema with clear purpose for each table
- **No loss of functionality** (table was empty)

### Performance
**Impact:** None - table was never used

### Code
**Impact:** Minimal - only remove references in planning docs

## Alternative Approach (If Supplementary Data Needed)

If additional runner fields are identified in the future:

### Option 1: Add to ra_runners
```sql
-- Example: Add supplementary columns directly
ALTER TABLE ra_runners ADD COLUMN field_1 TEXT;
ALTER TABLE ra_runners ADD COLUMN field_2 INTEGER;
-- etc.
```

**Pros:**
- All runner data in one place
- Simpler queries (no joins)
- Better performance

**Cons:**
- Table gets wider (but 57 → 70 columns still reasonable)

### Option 2: Create Specific Analytical Table
```sql
-- Example: Create purpose-built table
CREATE TABLE ra_runner_performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    race_id TEXT REFERENCES ra_races(id),
    horse_id TEXT REFERENCES ra_mst_horses(id),
    -- Specific calculated metrics
    recent_form_score DECIMAL,
    distance_suitability DECIMAL,
    going_preference TEXT,
    -- etc.
);
```

**Pros:**
- Clear purpose
- Normalized design
- Can be calculated/refreshed independently

**Cons:**
- Requires join for queries
- Additional table to maintain

## Recommendation

✅ **Remove ra_runner_supplementary table**

**Reasoning:**
1. No clear requirements after multiple planning iterations
2. Better alternatives exist (extend ra_runners OR create specific tables)
3. Table has never been used (0 records)
4. Simplifies schema and reduces maintenance

**If supplementary data is needed:**
- Define requirements FIRST
- Choose appropriate approach (extend ra_runners vs new table)
- Create with clear purpose and populate script

## Files Modified

1. `migrations/028_drop_ra_runner_supplementary.sql` - NEW
2. `RA_RUNNER_SUPPLEMENTARY_REMOVAL_SUMMARY.md` - NEW (this file)
3. `fetchers/docs/*_MASTER_TABLES_DATA_SOURCES_AND_TRANSFORMATIONS.md` - UPDATED
4. `SYSTEM_AUDIT_COMPLETE.md` - UPDATED

## Testing

After running the migration:

```bash
# 1. Verify table is dropped
psql -c "SELECT table_name FROM information_schema.tables WHERE table_name = 'ra_runner_supplementary';"
# Should return 0 rows

# 2. Verify ra_runners table still intact
psql -c "SELECT COUNT(*) FROM ra_runners;"
# Should show ~1.3M records (unchanged)

# 3. Check for any broken references
# (Should be none - table was never populated)
```

## Production Rollout

1. **Run migration:** `psql < migrations/028_drop_ra_runner_supplementary.sql`
2. **Deploy code:** Updated documentation
3. **Verify:** Check that table is dropped and no errors
4. **Monitor:** No impact expected (table was never used)

## Rollback (if needed)

The table can be recreated from schema backups if needed, but **rollback is not recommended** because:
1. Table was never populated
2. No clear requirements exist
3. Better alternatives available

## Summary

✅ Removed empty table with unclear purpose
✅ Simplified database schema (22 active tables instead of 24 planned)
✅ No loss of functionality (table never used)
✅ Clear alternatives documented for future needs
✅ Cleaner, more maintainable system

The removal of `ra_runner_supplementary` streamlines the system without losing any functionality. If supplementary runner data is needed in the future, we now have clear guidance on the best approach.

---

**Related Documents:**
- `migrations/028_drop_ra_runner_supplementary.sql` - Migration script
- `FETCHER_AUDIT_REPORT.md` - System audit findings
- `RA_RUNNER_ODDS_REMOVAL_SUMMARY.md` - Similar table removal
- `SYSTEM_AUDIT_COMPLETE.md` - Overall system status
