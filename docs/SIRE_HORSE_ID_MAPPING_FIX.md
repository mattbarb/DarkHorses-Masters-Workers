# Sire/Dam/Damsire horse_id Mapping Fix

**Date:** 2025-10-23
**Issue:** `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires` tables have `horse_id` column with NULL values
**Impact:** Cannot link breeding entities to their full horse records

---

## Problem Analysis

### Current Schema

```sql
-- ra_mst_sires has these columns:
CREATE TABLE ra_mst_sires (
    id SERIAL PRIMARY KEY,           -- Auto-increment
    sire_id VARCHAR UNIQUE NOT NULL, -- API sire_id (e.g., "sir_12345")
    name VARCHAR,                     -- Sire name
    horse_id VARCHAR,                 -- ❌ NULL - should link to ra_mst_horses
    ...
);
```

### Why horse_id Matters

**Sires ARE horses!** A sire with `sire_id: "sir_12345"` is a stallion that:
1. Has their own race history (stored in `ra_mst_horses` with different `horse_id`)
2. Has produced offspring
3. Has complete pedigree data, DOB, color, etc.

**Example:**
- Horse: "Frankel" (`horse_id: "hrs_98765"`)
  - Raced 2010-2012
  - Won 14 races
- Same horse as Sire: "Frankel" (`sire_id: "sir_12345"`)
  - Standing at stud since 2013
  - Sired hundreds of offspring

**We need `horse_id` to connect these!**

---

## Data Source Investigation

### Racing API Provides This Data!

When fetching `/v1/horses/{id}/pro`, the pedigree data includes:

```json
{
  "horse_id": "hrs_123456",
  "name": "Example Horse (GB)",
  "sire_id": "sir_98765",
  "sire": "Famous Sire (IRE)",
  "sire_horse_id": "hrs_sire_001",  // ✅ THIS IS WHAT WE NEED!
  "dam_id": "dam_54321",
  "dam": "Example Dam (GB)",
  "dam_horse_id": "hrs_dam_001",     // ✅ AND THIS!
  "damsire_id": "dsi_11111",
  "damsire": "Example Damsire (USA)",
  "damsire_horse_id": "hrs_dsi_001"  // ✅ AND THIS!
}
```

**Note:** The exact field names may vary - need to test actual API response.

Possible variations:
- `sire_horse_id` / `dam_horse_id` / `damsire_horse_id`
- `sire_hrs_id` / `dam_hrs_id` / `damsire_hrs_id`
- Nested object: `sire.horse_id`

---

## Fix Strategy

### Step 1: Update entity_extractor.py

Modify `extract_breeding_from_runners()` to capture `horse_id`:

```python
def extract_breeding_from_runners(self, runner_records: List[Dict]) -> Dict:
    """Extract sire/dam/damsire entities from runners WITH horse_id"""
    sires = {}
    dams = {}
    damsires = {}

    for runner in runner_records:
        # Sires
        sire_id = runner.get('sire_id')
        sire_name = runner.get('sire_name')
        sire_horse_id = runner.get('sire_horse_id')  # ✅ NEW!

        if sire_id and sire_name and sire_id not in sires:
            sires[sire_id] = {
                'id': sire_id,
                'name': sire_name,
                'horse_id': sire_horse_id,  # ✅ NEW!
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

        # Dams
        dam_id = runner.get('dam_id')
        dam_name = runner.get('dam_name')
        dam_horse_id = runner.get('dam_horse_id')  # ✅ NEW!

        if dam_id and dam_name and dam_id not in dams:
            dams[dam_id] = {
                'id': dam_id,
                'name': dam_name,
                'horse_id': dam_horse_id,  # ✅ NEW!
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

        # Damsires
        damsire_id = runner.get('damsire_id')
        damsire_name = runner.get('damsire_name')
        damsire_horse_id = runner.get('damsire_horse_id')  # ✅ NEW!

        if damsire_id and damsire_name and damsire_id not in damsires:
            damsires[damsire_id] = {
                'id': damsire_id,
                'name': damsire_name,
                'horse_id': damsire_horse_id,  # ✅ NEW!
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

    return {
        'sires': list(sires.values()),
        'dams': list(dams.values()),
        'damsires': list(damsires.values())
    }
```

### Step 2: Update Pedigree Capture

Also update `_enrich_new_horses()` to capture horse_ids from Pro endpoint:

```python
# In _enrich_new_horses() method, around line 373:
pedigree_record = {
    'horse_id': horse_id,
    'sire_id': horse_pro.get('sire_id'),
    'sire': horse_pro.get('sire'),
    'sire_horse_id': horse_pro.get('sire_horse_id'),  # ✅ NEW!
    'dam_id': horse_pro.get('dam_id'),
    'dam': horse_pro.get('dam'),
    'dam_horse_id': horse_pro.get('dam_horse_id'),    # ✅ NEW!
    'damsire_id': horse_pro.get('damsire_id'),
    'damsire': horse_pro.get('damsire'),
    'damsire_horse_id': horse_pro.get('damsire_horse_id'),  # ✅ NEW!
    'breeder': horse_pro.get('breeder'),
    'region': region,
    'created_at': datetime.utcnow().isoformat(),
    'updated_at': datetime.utcnow().isoformat()
}
```

### Step 3: Test API Response

Before implementing, **test the actual API response**:

```python
# Test script
import requests
from config.config import get_config

config = get_config()
horse_id = "hrs_39698890"  # Example horse

response = requests.get(
    f"https://api.theracingapi.com/v1/horses/{horse_id}/pro",
    auth=(config.racing_api.username, config.racing_api.password)
)

data = response.json()
print("Pedigree fields:")
for key in ['sire_id', 'sire', 'sire_horse_id',
            'dam_id', 'dam', 'dam_horse_id',
            'damsire_id', 'damsire', 'damsire_horse_id']:
    print(f"  {key}: {data.get(key)}")
```

---

## Implementation Steps

### Before Backfill Completes (SAFE)

1. ✅ Test API response to confirm field names
2. ✅ Update `entity_extractor.py` with correct field names
3. ✅ Update `ra_horse_pedigree` schema if needed (add horse_id columns)
4. ✅ Test with small sample (10-20 horses)

### After Backfill Completes (REQUIRED)

1. ⏳ Run backfill populates sires/dams/damsires with basic data (no horse_id)
2. ⏳ Create script to BACKFILL horse_ids:
   - Query all pedigree records from `ra_horse_pedigree`
   - Extract `sire_horse_id`, `dam_horse_id`, `damsire_horse_id`
   - UPDATE `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires` with horse_ids

```python
# Backfill script pseudocode
for pedigree_record in ra_horse_pedigree:
    if pedigree_record.sire_id and pedigree_record.sire_horse_id:
        UPDATE ra_mst_sires
        SET horse_id = pedigree_record.sire_horse_id
        WHERE sire_id = pedigree_record.sire_id

    # Repeat for dams and damsires
```

---

## Database Migration Needed

### Migration 030: Add horse_id to pedigree table

```sql
-- Migration 030: Add horse_id columns to ra_horse_pedigree
-- Date: 2025-10-23
-- Purpose: Capture horse_id links for sire/dam/damsire

ALTER TABLE ra_horse_pedigree
ADD COLUMN sire_horse_id VARCHAR(20),
ADD COLUMN dam_horse_id VARCHAR(20),
ADD COLUMN damsire_horse_id VARCHAR(20);

-- Add foreign keys
ALTER TABLE ra_horse_pedigree
ADD CONSTRAINT fk_sire_horse
    FOREIGN KEY (sire_horse_id) REFERENCES ra_mst_horses(horse_id),
ADD CONSTRAINT fk_dam_horse
    FOREIGN KEY (dam_horse_id) REFERENCES ra_mst_horses(horse_id),
ADD CONSTRAINT fk_damsire_horse
    FOREIGN KEY (damsire_horse_id) REFERENCES ra_mst_horses(horse_id);

-- Add comments
COMMENT ON COLUMN ra_horse_pedigree.sire_horse_id IS 'Horse ID of sire (links to ra_mst_horses)';
COMMENT ON COLUMN ra_horse_pedigree.dam_horse_id IS 'Horse ID of dam (links to ra_mst_horses)';
COMMENT ON COLUMN ra_horse_pedigree.damsire_horse_id IS 'Horse ID of damsire (links to ra_mst_horses)';
```

---

## Expected Benefits

### Query Capabilities Unlocked

**Before fix:**
```sql
-- ❌ Cannot do this:
SELECT h.name, h.dob, h.colour
FROM ra_mst_sires s
JOIN ra_mst_horses h ON s.horse_id = h.horse_id  -- horse_id is NULL!
WHERE s.sire_id = 'sir_12345';
```

**After fix:**
```sql
-- ✅ Can do this:
SELECT
    s.sire_id,
    s.name as sire_name,
    h.horse_id,
    h.dob,
    h.colour,
    h.region,
    COUNT(DISTINCT offspring.horse_id) as offspring_count
FROM ra_mst_sires s
JOIN ra_mst_horses h ON s.horse_id = h.horse_id
LEFT JOIN ra_horse_pedigree offspring ON offspring.sire_id = s.sire_id
WHERE s.sire_id = 'sir_12345'
GROUP BY s.sire_id, s.name, h.horse_id, h.dob, h.colour, h.region;
```

### ML Features Enabled

- ✅ Sire's age at time of breeding
- ✅ Sire's race performance (wins, earnings)
- ✅ Dam's race performance (female line strength)
- ✅ Complete 3-generation pedigree analysis
- ✅ Breeding value estimation

---

## Timeline

### Immediate (During Backfill)
1. ⏰ Test API response for horse_id fields
2. ⏰ Update entity_extractor.py (safe - won't break backfill)
3. ⏰ Create Migration 030 (apply after backfill)

### After Backfill Completes
1. ⏳ Apply Migration 030 (add horse_id columns to pedigree)
2. ⏳ Create backfill script for horse_ids
3. ⏳ Run backfill to populate existing records
4. ⏳ Verify data linkage with test queries

**Estimated effort:** 2-3 hours coding + 30 minutes backfill run

---

## Risk Assessment

### Low Risk
- ✅ Adding nullable columns doesn't break existing data
- ✅ UPSERT will handle updates safely
- ✅ Can backfill horse_ids after main backfill completes

### No Impact on Current Backfill
- ✅ Changes won't affect running backfill
- ✅ Current code continues to work
- ✅ Can implement fix independently

---

## Next Steps

1. **Test API response** - Confirm field names (`sire_horse_id` vs other variants)
2. **Create Migration 030** - Add horse_id columns to pedigree table
3. **Update entity_extractor.py** - Capture horse_ids during extraction
4. **Create backfill script** - Populate existing records
5. **Validate linkage** - Test queries joining sires to horses

---

**Status:** 📋 Documentation complete, awaiting API testing and implementation
**Priority:** ⭐⭐⭐ High - Critical for ML features and complete data model
**Blocking:** No - Current backfill can complete, fix can be applied after

---

**References:**
- `utils/entity_extractor.py` - Line 130-165 (extract_breeding_from_runners)
- `utils/entity_extractor.py` - Line 373-386 (pedigree capture in enrichment)
- Racing API docs: `/v1/horses/{id}/pro` endpoint
