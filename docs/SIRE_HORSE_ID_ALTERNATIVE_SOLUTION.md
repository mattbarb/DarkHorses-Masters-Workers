# Sire/Dam/Damsire horse_id Mapping - Alternative Solution

**Date:** 2025-10-23
**Status:** 🔴 **CRITICAL** - API doesn't provide horse_ids directly
**Solution:** Database lookup via name matching + separate API endpoints

---

## Problem Confirmed

**Racing API Test Results:**
- ✅ Provides: `sire_id`, `sire` (name)
- ✅ Provides: `dam_id`, `dam` (name)
- ✅ Provides: `damsire_id`, `damsire` (name)
- ❌ **Does NOT provide:** `sire_horse_id`, `dam_horse_id`, `damsire_horse_id`

**Test horse:** Kobalt St Georges (FR) (`hrs_39698890`)
```json
{
  "sire_id": "sir_5344241",
  "sire": "Masked Marvel (GB)",
  "dam_id": "dam_21667310",
  "dam": "Une Deux Trois (FR)",
  "damsire_id": "dsi_3689966",
  "damsire": "Robin Des Champs (FR)"
}
```

**No `horse_id` fields available in `/v1/horses/{id}/pro` response.**

---

## Alternative Solutions

### Option 1: Database Name Matching (RECOMMENDED - Immediate)

**Approach:** Match sire/dam/damsire names to existing horses in `ra_mst_horses`

**Implementation:**
```python
# After backfill completes, run this update query:
UPDATE ra_mst_sires s
SET horse_id = h.horse_id
FROM ra_mst_horses h
WHERE LOWER(TRIM(s.name)) = LOWER(TRIM(h.horse_name))
  AND s.horse_id IS NULL;

# Repeat for dams and damsires
UPDATE ra_mst_dams d
SET horse_id = h.horse_id
FROM ra_mst_horses h
WHERE LOWER(TRIM(d.name)) = LOWER(TRIM(h.horse_name))
  AND d.horse_id IS NULL;

UPDATE ra_mst_damsires ds
SET horse_id = h.horse_id
FROM ra_mst_horses h
WHERE LOWER(TRIM(ds.name)) = LOWER(TRIM(h.horse_name))
  AND ds.horse_id IS NULL;
```

**Pros:**
- ✅ Simple and fast
- ✅ No additional API calls
- ✅ Can run after backfill completes
- ✅ Works for historical data

**Cons:**
- ⚠️ May miss some matches if names differ slightly
- ⚠️ Won't catch sires/dams that never raced (broodmares, foreign stallions)

**Expected match rate:** 70-85% (sires that raced in UK/IRE)

---

### Option 2: Separate API Endpoints (If Available)

**Investigate these endpoints:**
- `/v1/sires/{sire_id}`
- `/v1/dams/{dam_id}`
- `/v1/damsires/{damsire_id}`

**Test if they provide `horse_id` field.**

**If yes:**
```python
# Fetch each sire/dam/damsire separately during enrichment
sire_data = api_client._make_request(f'/sires/{sire_id}')
if sire_data and sire_data.get('horse_id'):
    sire_record['horse_id'] = sire_data['horse_id']
```

**Pros:**
- ✅ Direct linkage from API
- ✅ Most accurate

**Cons:**
- ❌ 3x more API calls during enrichment
- ❌ Rate limiting impact (significant)
- ❌ May not exist or may not provide horse_id

---

### Option 3: Hybrid Approach (BEST LONG-TERM)

**Combine both approaches:**

1. **During backfill:** Capture sire/dam/damsire IDs and names (as currently done)
2. **After backfill:** Run name-matching SQL to populate most horse_ids
3. **Ongoing:** For new sires/dams, check if separate endpoints provide horse_id
4. **Manual review:** Flag unmatched records for investigation

**Implementation Steps:**

#### Step 1: Add horse_id columns (they exist already, just NULL)
```sql
-- Already exists in schema, just need to populate
SELECT
  COUNT(*) as total,
  COUNT(horse_id) as with_horse_id,
  COUNT(*) - COUNT(horse_id) as missing
FROM ra_mst_sires;
```

#### Step 2: Create matching script
```python
# scripts/populate_pedigree_horse_ids.py
def match_pedigree_to_horses(db_client):
    """Match sires/dams/damsires to horses by name"""

    tables = ['ra_mst_sires', 'ra_mst_dams', 'ra_mst_damsires']

    for table in tables:
        logger.info(f"Matching {table} to ra_mst_horses...")

        # Update via name matching
        query = f"""
        UPDATE {table} pedigree
        SET horse_id = h.horse_id,
            updated_at = NOW()
        FROM ra_mst_horses h
        WHERE LOWER(TRIM(pedigree.name)) = LOWER(TRIM(h.horse_name))
          AND pedigree.horse_id IS NULL
        RETURNING pedigree.id, pedigree.name, h.horse_id
        """

        result = db_client.client.rpc('exec_sql', {'sql': query}).execute()
        logger.info(f"  ✅ Matched {len(result.data)} records")

    # Report unmatched
    for table in tables:
        unmatched = db_client.client.table(table).select('*').is_('horse_id', 'null').execute()
        logger.warning(f"  ⚠️  {table}: {len(unmatched.data)} unmatched records")
```

#### Step 3: Run after backfill
```bash
python3 scripts/populate_pedigree_horse_ids.py
```

---

## Implementation Plan

### Phase 1: Immediate (After Current Backfill Completes)

1. ✅ **Test completed** - Confirmed API doesn't provide horse_ids
2. ⏳ **Create matching script** - `scripts/populate_pedigree_horse_ids.py`
3. ⏳ **Run name-based matching** - Update ra_mst_sires/dams/damsires
4. ⏳ **Validate results** - Check match rates

**Expected outcome:** 70-85% of pedigree records linked to horses

### Phase 2: Enhanced (Future Improvement)

1. ⏳ **Test separate API endpoints** - Check `/v1/sires/{id}` etc.
2. ⏳ **If available, integrate** - Fetch horse_id during enrichment
3. ⏳ **Backfill gaps** - Populate remaining NULL horse_ids

---

## SQL Queries for Validation

### Check current state
```sql
-- Sires
SELECT
  COUNT(*) as total_sires,
  COUNT(horse_id) as with_horse_id,
  ROUND(COUNT(horse_id)::numeric / COUNT(*) * 100, 2) as match_pct
FROM ra_mst_sires;

-- Dams
SELECT
  COUNT(*) as total_dams,
  COUNT(horse_id) as with_horse_id,
  ROUND(COUNT(horse_id)::numeric / COUNT(*) * 100, 2) as match_pct
FROM ra_mst_dams;

-- Damsires
SELECT
  COUNT(*) as total_damsires,
  COUNT(horse_id) as with_horse_id,
  ROUND(COUNT(horse_id)::numeric / COUNT(*) * 100, 2) as match_pct
FROM ra_mst_damsires;
```

### Test name matching (dry run)
```sql
-- How many sires CAN be matched?
SELECT
  s.sire_id,
  s.name as sire_name,
  h.horse_id,
  h.horse_name
FROM ra_mst_sires s
JOIN ra_mst_horses h ON LOWER(TRIM(s.name)) = LOWER(TRIM(h.horse_name))
WHERE s.horse_id IS NULL
LIMIT 10;
```

### After matching - verify quality
```sql
-- Check linked horses
SELECT
  s.sire_id,
  s.name as sire_name,
  h.horse_id,
  h.horse_name,
  h.dob,
  h.sex
FROM ra_mst_sires s
JOIN ra_mst_horses h ON s.horse_id = h.horse_id
WHERE h.sex IN ('stallion', 'gelding', 'colt', 'horse')  -- Should be male
LIMIT 20;
```

---

## Why Name Matching Is Viable

### Racing API Name Format
All horse names include region code:
- "Masked Marvel **(GB)**"
- "Une Deux Trois **(FR)**"
- "Robin Des Champs **(FR)**"

**This makes matching MORE reliable** because:
1. Names are globally unique with region
2. No ambiguity between horses with same name in different countries
3. Format is consistent across API responses

### Expected Match Quality

**High confidence matches:**
- Sires that raced in UK/IRE: ~85% match rate
- Reason: They're in ra_mst_horses as runners

**Lower confidence:**
- Foreign stallions standing abroad: ~30% match rate
- Broodmares that never raced: ~40% match rate
- Reason: May not have run in UK/IRE races

**Overall expected:** 70-85% match rate across all pedigree records

---

## Alternative: Accept NULL horse_ids

### Option 4: Make horse_id Truly Optional

**Rationale:**
- Not all sires/dams/damsires raced in UK/IRE
- We still have sire_id/dam_id/damsire_id for relationships
- We still have names for display

**Keep horse_id as:**
- Nice-to-have enrichment (when available)
- Not critical for core functionality
- Valuable for ML features (when present)

**This is actually acceptable** because:
```sql
-- Can still query pedigree without horse_id
SELECT
  h.horse_name,
  p.sire,  -- Name available even without horse_id
  p.dam,
  p.damsire
FROM ra_mst_horses h
JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id;

-- horse_id just adds extra details when available
SELECT
  h.horse_name,
  sire_horse.dob as sire_dob,  -- Extra data via horse_id
  sire_horse.colour as sire_colour
FROM ra_mst_horses h
JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id
LEFT JOIN ra_mst_horses sire_horse ON p.sire_horse_id = sire_horse.horse_id;
```

---

## Recommended Immediate Action

### 1. Create populate_pedigree_horse_ids.py script

```python
#!/usr/bin/env python3
"""
Populate horse_id in ra_mst_sires/dams/damsires via name matching
Run after backfill completes
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('populate_pedigree_horse_ids')

def main():
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    logger.info("=" * 80)
    logger.info("POPULATING PEDIGREE HORSE_IDS VIA NAME MATCHING")
    logger.info("=" * 80)

    tables = [
        ('ra_mst_sires', 'sire'),
        ('ra_mst_dams', 'dam'),
        ('ra_mst_damsires', 'damsire')
    ]

    total_matched = 0

    for table_name, entity_type in tables:
        logger.info(f"\nProcessing {table_name}...")

        # Count before
        before = db_client.client.table(table_name).select('*', count='exact').execute()
        before_with_id = db_client.client.table(table_name).select('*', count='exact').not_.is_('horse_id', 'null').execute()

        logger.info(f"  Before: {before.count} total, {before_with_id.count} with horse_id")

        # Run matching query
        match_query = f"""
        UPDATE {table_name} pedigree
        SET horse_id = h.horse_id,
            updated_at = NOW()
        FROM ra_mst_horses h
        WHERE LOWER(TRIM(REGEXP_REPLACE(pedigree.name, '\\s*\\([A-Z]+\\)\\s*$', ''))) =
              LOWER(TRIM(REGEXP_REPLACE(h.horse_name, '\\s*\\([A-Z]+\\)\\s*$', '')))
          AND pedigree.horse_id IS NULL;
        """

        try:
            # Note: May need to use psql directly if RPC doesn't work
            result = db_client.client.rpc('exec_sql', {'sql': match_query}).execute()

            # Count after
            after_with_id = db_client.client.table(table_name).select('*', count='exact').not_.is_('horse_id', 'null').execute()
            matched = after_with_id.count - before_with_id.count

            logger.info(f"  ✅ Matched {matched} new records")
            logger.info(f"  After: {after_with_id.count} with horse_id ({after_with_id.count/before.count*100:.1f}%)")

            total_matched += matched

        except Exception as e:
            logger.error(f"  ❌ Error matching {table_name}: {e}")
            logger.info(f"  Note: You may need to run this SQL manually via psql or Supabase dashboard")

    logger.info("")
    logger.info("=" * 80)
    logger.info(f"TOTAL MATCHED: {total_matched} pedigree records linked to horses")
    logger.info("=" * 80)

if __name__ == '__main__':
    main()
```

### 2. Run after backfill completes

```bash
python3 scripts/populate_pedigree_horse_ids.py
```

### 3. Document acceptance of partial coverage

Update `SIRE_HORSE_ID_MAPPING_FIX.md` to reflect:
- API limitation discovered
- Name-based matching implemented
- Expected 70-85% coverage
- Remaining NULL values are acceptable (foreign stallions/broodmares)

---

## Summary

**✅ We CAN populate horse_ids** - just not directly from the API

**✅ Name matching is viable** - 70-85% expected coverage

**✅ No impact on current backfill** - can implement after it completes

**⏳ Next steps:**
1. Let backfill finish
2. Create and run matching script
3. Validate results
4. Accept partial coverage as OK

---

**Status:** Solution designed, ready to implement after backfill
**Priority:** ⭐⭐ Medium-High (improves data quality, not blocking)
**Estimated effort:** 2-3 hours (script + validation)
