# Region Extraction Implementation

**Date:** 2025-10-15
**Status:** Complete and deployed

## Summary

Implemented region extraction from horse names to populate `region` field in both `ra_horses` and `ra_horse_pedigree` tables. Region represents the **breeding origin** of the horse.

## Background

The Racing API Pro endpoint does not return a `region` field directly. However, horse names include country codes indicating breeding origin:
- `"Afternoon Delight (IRE)"` → Ireland
- `"Natavia (GB)"` → Great Britain
- `"Seattle Slew (USA)"` → USA

## Key Distinction

**Region in our system = BREEDING ORIGIN** (not racing region)
- A horse bred in Ireland `(IRE)` can race in Great Britain
- A horse bred in GB `(GB)` can race in Ireland
- The region field is stable (breeding origin never changes)
- Useful for ML analysis of breeding performance

**Racing region comes from** `ra_races.region` (where the race took place)

## Implementation

### 1. Region Extractor Utility

**File:** `utils/region_extractor.py`

**Function:**
```python
extract_region_from_name(horse_name: str) -> Optional[str]
```

**Supported Country Codes:**
- `IRE` → `ire` (Ireland)
- `GB`, `UK` → `gb` (Great Britain)
- `FR` → `fr` (France)
- `USA` → `usa` (United States)
- `GER` → `ger` (Germany)
- `AUS` → `aus` (Australia)
- `NZ` → `nz` (New Zealand)
- `SAF` → `saf` (South Africa)
- `JPN` → `jpn` (Japan)
- `ITY` → `ity` (Italy)
- `SPA` → `spa` (Spain)

**Pattern Matching:**
- Uses regex: `\(([A-Z]{2,3})\)\s*$`
- Extracts 2-3 letter country code in parentheses at end of name
- Returns lowercase region code or None if no code found

**Examples:**
```python
>>> extract_region_from_name("Afternoon Delight (IRE)")
'ire'

>>> extract_region_from_name("Natavia (GB)")
'gb'

>>> extract_region_from_name("Plain Horse Name")
None
```

### 2. Backfill Script Update

**File:** `scripts/backfill_horse_pedigree_enhanced.py`

**Changes:**
```python
# Import added
from utils.region_extractor import extract_region_from_name

# Extract region from name
horse_name = horse_data.get('name', '')
region = extract_region_from_name(horse_name)

# Use in horse update
horse_update = {
    ...
    'region': region,  # Extracted from name
    ...
}

# Use in pedigree record
pedigree_record = {
    ...
    'region': region,  # Extracted from horse name
    ...
}
```

### 3. Horses Fetcher Update

**File:** `fetchers/horses_fetcher.py`

**Changes:**
```python
# Import added
from utils.region_extractor import extract_region_from_name

# Extract region during Pro enrichment
horse_name = horse_pro.get('name', '')
region = extract_region_from_name(horse_name)

# Use in horse record
horse_record = {
    ...
    'region': region,  # Extracted from name
    ...
}

# Use in pedigree record
pedigree_record = {
    ...
    'region': region,  # Extracted from horse name
    ...
}
```

### 4. Database Migration

**File:** `migrations/010_add_region_to_pedigree_simple.sql`

**Actions:**
- ✅ Added `region VARCHAR(10)` column to `ra_horse_pedigree`
- ✅ Backfilled existing records (all NULL initially - expected)
- ✅ Created index `idx_horse_pedigree_region`

**Status:** Migration executed successfully

## Data Population

### Current State

**Before enrichment:**
- Total horses: ~111,430
- Horses with region: 0 (0%)
- Total pedigree records: 73,344
- Pedigrees with region: 0 (0%)

**After enrichment (ongoing):**
- As backfill processes horses, region will be populated
- Expected ~70-80% coverage (horses with country codes in names)
- Some horses may not have country codes (NULL region is acceptable)

### Expected Coverage

Based on testing:
- `"Afternoon Delight (IRE)"` → `ire` ✓
- `"Natavia (GB)"` → `gb` ✓
- `"Plain Name"` → `NULL` (acceptable)

## ML Benefits

### 1. Breeding Analysis
```sql
-- Compare Irish-bred vs British-bred performance
SELECT
    region,
    COUNT(*) as horses,
    AVG(win_rate) as avg_win_rate
FROM ra_horses h
JOIN ra_runners r ON r.horse_id = h.horse_id
WHERE region IN ('ire', 'gb')
GROUP BY region;
```

### 2. Pedigree Analysis
```sql
-- Analyze sire performance by breeding region
SELECT
    p.sire,
    p.region as breeding_region,
    COUNT(*) as offspring,
    AVG(r.win_rate) as avg_offspring_win_rate
FROM ra_horse_pedigree p
JOIN ra_runners r ON r.horse_id = p.horse_id
WHERE p.region IN ('ire', 'gb')
  AND p.sire_id IS NOT NULL
GROUP BY p.sire, p.region
ORDER BY offspring DESC
LIMIT 50;
```

### 3. Cross-Border Racing
```sql
-- Irish-bred horses racing in GB
SELECT
    h.horse_id,
    h.name,
    h.region as bred_in,
    races.region as racing_in,
    COUNT(*) as races,
    AVG(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) as win_rate
FROM ra_horses h
JOIN ra_runners r ON r.horse_id = h.horse_id
JOIN ra_races races ON r.race_id = races.race_id
WHERE h.region = 'ire'  -- Bred in Ireland
  AND races.region = 'gb'  -- Racing in GB
GROUP BY h.horse_id, h.name, h.region, races.region;
```

## Verification

### Test Region Extraction
```bash
python3 utils/region_extractor.py
```

**Expected Output:**
```
Testing region extraction:
============================================================
Afternoon Delight (IRE)        → ire
Natavia (GB)                   → gb
Seattle Slew (USA)             → usa
Plain Horse Name               → None
Dubawi (IRE)                   → ire
Frankel (GB)                   → gb
```

### Check Database Population
```sql
-- After backfill runs for a while
SELECT
    COUNT(*) as total_horses,
    COUNT(region) as with_region,
    COUNT(*) - COUNT(region) as without_region,
    ROUND(100.0 * COUNT(region) / COUNT(*), 1) as percentage
FROM ra_horses
WHERE dob IS NOT NULL;  -- Only enriched horses

-- Region distribution
SELECT region, COUNT(*) as count
FROM ra_horses
WHERE region IS NOT NULL
GROUP BY region
ORDER BY count DESC;

-- Pedigree region distribution
SELECT region, COUNT(*) as count
FROM ra_horse_pedigree
WHERE region IS NOT NULL
GROUP BY region
ORDER BY count DESC;
```

## Notes

### Why This Approach?

1. **API Limitation:** Racing API doesn't provide region field
2. **Stable Data:** Breeding origin never changes (unlike racing location)
3. **ML Value:** Breeding region is predictive of performance
4. **Available Data:** Country codes are in horse names

### What It Represents

- ✅ **Does represent:** Where the horse was bred/born
- ❌ **Does not represent:** Where the horse currently races
- ❌ **Does not represent:** Horse's nationality for competition

### Handling Missing Data

- Not all horses have country codes in names
- `NULL` region is acceptable and expected
- Can fallback to race region for filtering if needed

## Future Enhancements

### 1. Backfill Existing Horses

Create a script to backfill region for horses that already have names:

```sql
-- Update horses with region extracted from name
UPDATE ra_horses
SET region = CASE
    WHEN name ~ '\(IRE\)' THEN 'ire'
    WHEN name ~ '\(GB\)' THEN 'gb'
    WHEN name ~ '\(UK\)' THEN 'gb'
    WHEN name ~ '\(FR\)' THEN 'fr'
    WHEN name ~ '\(USA\)' THEN 'usa'
    WHEN name ~ '\(GER\)' THEN 'ger'
    WHEN name ~ '\(AUS\)' THEN 'aus'
    WHEN name ~ '\(NZ\)' THEN 'nz'
    WHEN name ~ '\(SAF\)' THEN 'saf'
    WHEN name ~ '\(JPN\)' THEN 'jpn'
    ELSE region
END
WHERE name IS NOT NULL
  AND region IS NULL;

-- Update pedigrees from horses
UPDATE ra_horse_pedigree p
SET region = h.region
FROM ra_horses h
WHERE p.horse_id = h.horse_id
  AND p.region IS NULL
  AND h.region IS NOT NULL;
```

### 2. Enhanced Extraction

Could extract additional breeding information:
- Year of birth from name (if present)
- Breeding stud/farm (if available in API)
- Pedigree country of origin

## Related Changes

This change is part of a larger effort:

1. **ML Runner History Cleanup** - Removed pre-calculated ML table
2. **Region Field Addition** - This implementation
3. **API-Based ML Features** - Moving to on-demand calculation
4. **ML API Documentation** - Comprehensive schema docs

## Testing

### Manual Test
```python
from utils.region_extractor import extract_region_from_name

# Test cases
assert extract_region_from_name("Afternoon Delight (IRE)") == "ire"
assert extract_region_from_name("Natavia (GB)") == "gb"
assert extract_region_from_name("Plain Name") is None
```

### Integration Test
```bash
# Run backfill with updated code
python3 scripts/backfill_horse_pedigree_enhanced.py --test

# Check results
# Should show horses WITH region populated
```

---

**Status:** Complete and deployed
**Next:** Monitor backfill to verify region population
