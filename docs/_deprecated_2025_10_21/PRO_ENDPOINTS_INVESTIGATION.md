# PRO ENDPOINTS INVESTIGATION

**Date:** 2025-10-18
**Status:** Testing dam progeny and damsire grandoffspring endpoints

---

## ENDPOINTS TESTED

### 1. Dam Progeny Results ✅
**Correct URL:** `/v1/dams/{dam_id}/results`
**Result:** **200 - Success!**

**Test case:**
- Dam: Whazzat (GB) - `dam_4206832`
- URL: `https://api.theracingapi.com/v1/dams/dam_4206832/results`

**Returns:** Race results for all horses that have this dam
**Structure:** Same as `/v1/results` - returns races with runners array
**Use case:** Get all progeny results for a specific dam

### 2. Damsire Grandoffspring Results ✅
**Correct URL:** `/v1/damsires/{damsire_id}/results`
**Result:** **200 - Success!**

**Test case:**
- Damsire: Galileo - `dsi_3722383`
- URL: `https://api.theracingapi.com/v1/damsires/dsi_3722383/results`

**Returns:** Race results for all horses that have this damsire (maternal grandsire)
**Structure:** Same as `/v1/results` - returns races with runners array
**Use case:** Get all grandoffspring results for a specific damsire

---

## POSSIBLE ALTERNATIVE ENDPOINTS

These Pro features might be under different URL patterns:

### Dam-related:
- `/v1/dams/{id}/results`
- `/v1/dams/{id}/offspring`
- `/v1/dams/{id}/progeny`
- `/v1/horses/{dam_id}/offspring`
- `/v1/horses/{dam_id}/progeny`

### Damsire-related:
- `/v1/damsires/{id}/results`
- `/v1/damsires/{id}/offspring`
- `/v1/sires/{damsire_id}/grandoffspring`
- `/v1/horses/{damsire_id}/grandoffspring`

---

## RECOMMENDATIONS

**Option 1: Check Official API Documentation**
- Review Racing API Pro tier documentation for exact endpoint paths
- Check if these features are under different names

**Option 2: Contact Racing API Support**
- Confirm availability of dam progeny results
- Confirm availability of damsire grandoffspring results
- Get exact endpoint paths and required parameters

**Option 3: Alternative Data Strategy**
- We already have comprehensive lineage data via `ra_lineage`
- Can calculate progeny/grandoffspring statistics from existing data
- May not need separate endpoints if we can derive this information

---

## CURRENT LINEAGE CAPABILITIES (Without Pro Endpoints)

We can already analyze:

### Dam Progeny Performance (from existing data)
```sql
-- Get all offspring of a dam with their results
SELECT
    r.horse_id,
    r.horse_name,
    rac.race_date,
    r.position,
    r.prize_won
FROM ra_lineage l
JOIN ra_runners r ON l.horse_id = r.horse_id
JOIN ra_races rac ON r.race_id = rac.race_id
WHERE l.ancestor_horse_id = 'dam_4206832'  -- Whazzat
AND l.relation_type = 'dam'
AND r.position IS NOT NULL;
```

### Damsire Grandoffspring Performance (from existing data)
```sql
-- Get all grandoffspring of a damsire with their results
SELECT
    r.horse_id,
    r.horse_name,
    rac.race_date,
    r.position,
    r.prize_won
FROM ra_lineage l
JOIN ra_runners r ON l.horse_id = r.horse_id
JOIN ra_races rac ON r.race_id = rac.race_id
WHERE l.ancestor_horse_id = 'dsi_3722383'  -- Galileo
AND l.relation_type = 'grandsire_maternal'
AND r.position IS NOT NULL;
```

**Note:** These queries work because we track which horses have which ancestors in `ra_lineage`, then join to their race results in `ra_runners`.

---

## NEXT STEPS

1. ⏳ **Verify correct endpoint paths** for Pro features
2. ⏳ **Test alternative URL patterns** if documentation unavailable
3. ✅ **Use existing data** for progeny/grandoffspring analysis (already working)
4. ⏳ **Create aggregation tables** if Pro endpoints not available:
   - `ra_dam_progeny_stats`
   - `ra_damsire_grandoffspring_stats`

---

## CONCLUSION

✅ **Pro endpoints confirmed working:**
- `/v1/dams/{dam_id}/results` - Returns race results for all progeny of a dam
- `/v1/damsires/{damsire_id}/results` - Returns race results for all grandoffspring of a damsire

**Key Finding:** These endpoints return the **same race result data structure** as `/v1/results`, just pre-filtered by lineage.

**Since we already fetch all results via `/v1/results` and track lineage in `ra_lineage`:**
- We already have this data in our database
- We can query it locally without API calls
- The Pro endpoints are useful for validation/backfill but not essential for ongoing operations

**Recommendation:**
1. Use our existing `ra_lineage` queries for real-time analysis (faster, no API limits)
2. Optionally use Pro endpoints for validation or finding historical gaps
3. Document Pro endpoints in API integration guide
