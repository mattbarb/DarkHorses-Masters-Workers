# Jockey Results Endpoint Comprehensive Analysis

**Analysis Date:** 2025-10-17
**Endpoint:** `/v1/jockeys/{jockey_id}/results`
**Analyst:** Claude Code
**Status:** Complete

## Executive Summary

The `/v1/jockeys/{jockey_id}/results` endpoint provides race results filtered by jockey, but **does NOT provide any unique data** that isn't already available in the `/v1/results` endpoint. All key fields including `time`, `sp_dec`, `ovr_btn`, and `weight` (stones-lbs format) are already present in `/v1/results`.

**Key Finding:** Continue using `/v1/results` as primary data source. No changes needed to current architecture.

---

## 1. Endpoint Details

### A. URL Structure
```
GET /v1/jockeys/{jockey_id}/results
```

### B. Authentication
- Basic Auth (username:password)
- Same credentials as other Racing API endpoints

### C. Query Parameters

| Parameter | Type | Required | Description | Example |
|-----------|------|----------|-------------|---------|
| `jockey_id` | string | Yes | Jockey identifier | `jky_268488` |
| `limit` | integer | No | Results per page | `25` (default), no max |
| `skip` | integer | No | Pagination offset | `0` |
| `start_date` | string | No | Filter from date | `2024-01-01` |
| `end_date` | string | No | Filter to date | `2024-12-31` |
| `region` | array | No | Region codes | `['gb', 'ire']` |

### D. Rate Limiting
- 2 requests/second (same as all Racing API endpoints)
- 120 jockeys/minute theoretical maximum
- ~4.7 hours to query all 34,000 jockeys in database

### E. Pagination
```json
{
  "results": [...],
  "total": 398,
  "limit": 25,
  "skip": 0,
  "query": {...}
}
```

### F. Pro Tier Endpoint
- `/v1/jockeys/{jockey_id}/results/pro` **does NOT exist**
- Returns 404
- Standard endpoint is sufficient

---

## 2. Response Structure

### A. Top-Level Structure
```json
{
  "results": [
    {
      "race_id": "rac_11236277",
      "date": "2024-05-03",
      "course": "Cheltenham",
      "course_id": "crs_286",
      "race_name": "Junior Jumpers Open Hunters' Chase",
      "runners": [...]
    }
  ],
  "total": 398,
  "limit": 25,
  "skip": 0,
  "query": {...}
}
```

### B. Race-Level Fields (30 total)

| Field | Description | Always Present |
|-------|-------------|----------------|
| `race_id` | Race identifier | Yes |
| `date` | Race date (YYYY-MM-DD) | Yes |
| `region` | Region code (GB, IRE) | Yes |
| `course` | Course name | Yes |
| `course_id` | Course identifier | Yes |
| `off` | Off time (HH:MM) | Yes |
| `off_dt` | Off datetime (ISO 8601) | Yes |
| `race_name` | Full race name | Yes |
| `type` | Race type (Flat, Hurdle, Chase) | Yes |
| `class` | Race class (Class 1-7) | Yes |
| `age_band` | Age restriction (e.g., "4yo+") | Yes |
| `dist` | Distance (human readable, e.g., "1m4f") | Yes |
| `dist_y` | Distance in yards | Yes |
| `dist_m` | Distance in meters | Yes |
| `dist_f` | Distance in furlongs | Yes |
| `going` | Going description | Yes |
| `surface` | Surface (Turf, AW) | Yes |
| `jumps` | Jump description (e.g., "12 hurdles") | Yes |
| `runners` | Array of runners | Yes |
| `winning_time_detail` | Winning time with standard comparison | Yes |
| `rating_band` | Rating band restriction | Sometimes |
| `pattern` | Pattern race indicator | Rarely |
| `sex_rest` | Sex restriction | Sometimes |
| `non_runners` | Non-runners description | Sometimes |
| `comments` | Race comments | Sometimes |
| `tote_win` | Tote win dividend | Yes |
| `tote_pl` | Tote place dividends | Usually |
| `tote_ex` | Tote exacta | Yes |
| `tote_csf` | Tote CSF | Yes |
| `tote_tricast` | Tote tricast | Sometimes |
| `tote_trifecta` | Tote trifecta | Usually |

### C. Runner-Level Fields (34 total)

**Identity Fields:**
- `horse_id` - Horse identifier
- `horse` - Horse name
- `jockey_id` - Jockey identifier
- `jockey` - Jockey name
- `trainer_id` - Trainer identifier
- `trainer` - Trainer name
- `owner_id` - Owner identifier
- `owner` - Owner name

**Basic Information:**
- `age` - Horse age
- `sex` - Horse sex (M, G, F, C)
- `number` - Saddle cloth number
- `draw` - Starting stall (flat racing)
- `weight` - Weight in stones-pounds (e.g., "11-7")
- `weight_lbs` - Weight in pounds (e.g., 161)
- `headgear` - Headgear code

**Pedigree:**
- `sire_id` - Sire identifier
- `sire` - Sire name
- `dam_id` - Dam identifier
- `dam` - Dam name
- `damsire_id` - Damsire identifier
- `damsire` - Damsire name

**Performance:**
- `position` - Finishing position
- `btn` - Beaten distance (lengths)
- `ovr_btn` - Overall beaten distance
- `time` - Individual finishing time (e.g., "6:59.54")
- `prize` - Prize money won

**Ratings:**
- `or` - Official rating
- `rpr` - Racing Post Rating
- `tsr` - Top Speed Rating

**Betting:**
- `sp` - Starting price (fractional, e.g., "11/1")
- `sp_dec` - Starting price (decimal, e.g., "12.00")

**Other:**
- `jockey_claim_lbs` - Jockey allowance (pounds)
- `comment` - Race comment/analysis
- `silk_url` - Jockey silk image URL

---

## 3. Data Gap Analysis

### A. Comparison with /v1/results

**CRITICAL FINDING:** All 34 runner-level fields in `/v1/jockeys/{id}/results` are **ALSO PRESENT** in `/v1/results`.

Tested fields:
```python
# All present in /v1/results:
✓ time          # "1:27.07"
✓ sp_dec        # "19.00"
✓ ovr_btn       # "0"
✓ weight        # "9-7"
✓ sp            # "18/1"
✓ btn           # "0"
✓ comment       # Race comments
✓ silk_url      # Silk image URL
```

### B. Fields Currently NOT Captured

Despite being available in `/v1/results`, we're not capturing:

| Field | Type | Example | Database Column | Priority |
|-------|------|---------|-----------------|----------|
| `time` | string | "1:27.07" | `finishing_time` | **HIGH** |
| `sp_dec` | string | "19.00" | `starting_price_decimal` | **HIGH** |
| `ovr_btn` | string | "0" | `overall_beaten_distance` | MEDIUM |
| `weight` | string | "9-7" | `weight_stones_lbs` | LOW |
| `comment` | string | "Led..." | `comment` | **HIGH** |
| `silk_url` | string | "https://..." | `silk_url` | **HIGH** |
| `jockey_claim_lbs` | string | "5" | `jockey_claim` | MEDIUM |

**Note:** `comment` and `silk_url` are in our schema but may not be populated from results.

### C. Why Time is Critical for ML

Individual finishing times are essential for:

1. **Performance Analysis**
   - True speed assessment (not just relative position)
   - Pace analysis (early/late speed)
   - Track record comparisons

2. **Track Condition Impact**
   - Fast/slow ground calculation
   - Standard time comparisons
   - Weather impact modeling

3. **Horse Form**
   - True ability vs. position
   - Consistency measurement
   - Improvement/decline tracking

4. **Predictive Modeling**
   - Speed ratings
   - Time-based handicapping
   - Sectional time analysis (if available)

**Current Gap:** We capture position and beaten distance, but not actual finishing times. This is a significant data loss for ML models.

---

## 4. Comparison Table

| Field | In /v1/results | In /v1/jockeys/{id}/results | Currently Captured | Should Capture | Priority |
|-------|----------------|----------------------------|-------------------|----------------|----------|
| **Identity** |
| horse_id | Yes | Yes | Yes | Yes | - |
| horse_name | Yes | Yes | Yes | Yes | - |
| jockey_id | Yes | Yes | Yes | Yes | - |
| jockey_name | Yes | Yes | Yes | Yes | - |
| trainer_id | Yes | Yes | Yes | Yes | - |
| trainer_name | Yes | Yes | Yes | Yes | - |
| owner_id | Yes | Yes | Yes | Yes | - |
| owner_name | Yes | Yes | Yes | Yes | - |
| **Basic Info** |
| age | Yes | Yes | Yes | Yes | - |
| sex | Yes | Yes | Yes | Yes | - |
| number | Yes | Yes | Yes | Yes | - |
| draw | Yes | Yes | Yes | Yes | - |
| weight_lbs | Yes | Yes | Yes | Yes | - |
| weight (stones-lbs) | **Yes** | Yes | No | Yes | LOW |
| headgear | Yes | Yes | Yes | Yes | - |
| **Pedigree** |
| sire_id/name | Yes | Yes | Yes | Yes | - |
| dam_id/name | Yes | Yes | Yes | Yes | - |
| damsire_id/name | Yes | Yes | Yes | Yes | - |
| **Ratings** |
| official_rating | Yes | Yes | Yes | Yes | - |
| rpr | Yes | Yes | Yes | Yes | - |
| tsr | Yes | Yes | Yes | Yes | - |
| **Results** |
| position | Yes | Yes | Yes | Yes | - |
| btn (distance_beaten) | Yes | Yes | Yes | Yes | - |
| ovr_btn | **Yes** | Yes | No | Yes | MEDIUM |
| prize | Yes | Yes | Yes | Yes | - |
| time | **Yes** | Yes | **No** | **Yes** | **HIGH** |
| **Betting** |
| sp (fractional) | Yes | Yes | Partial | Yes | HIGH |
| sp_dec (decimal) | **Yes** | Yes | **No** | **Yes** | **HIGH** |
| **Other** |
| jockey_claim_lbs | **Yes** | Yes | Partial | Yes | MEDIUM |
| comment | **Yes** | Yes | Schema only | Yes | **HIGH** |
| silk_url | **Yes** | Yes | Schema only | Yes | HIGH |
| **From Racecards Only** |
| form | No | No | Yes | Yes | - |
| form_string | No | No | Yes | Yes | - |
| days_since_last_run | No | No | Yes | Yes | - |
| career_runs/wins/places | No | No | Yes | Yes | - |

---

## 5. Comparison with Other Entity Results Endpoints

### A. Testing Results

| Endpoint | Exists | Response Structure | Notes |
|----------|--------|-------------------|-------|
| `/v1/jockeys/{id}/results` | **Yes** | Full race + runners | Tested successfully |
| `/v1/trainers/{id}/results` | **Yes** | Same structure | Returns trainer's runners |
| `/v1/horses/{id}/results` | **Yes** | Same structure | Returns horse's race history |
| `/v1/owners/{id}/results` | **Yes** | Same structure | Returns owner's runners |

### B. Pattern Consistency

All entity-specific results endpoints follow the same pattern:
```
GET /v1/{entity_type}/{entity_id}/results
```

Where `{entity_type}` can be:
- `jockeys`
- `trainers`
- `horses`
- `owners`

All return the same response structure with complete race and runner data.

---

## 6. Enrichment Strategy Evaluation

### Option 1: Replace /v1/results with Entity-Specific Endpoints
**Verdict: REJECT**

**Pros:**
- Complete historical data (no 12-month limit)
- Same data quality

**Cons:**
- Must iterate all jockeys/trainers/horses/owners
- Extremely slow (4.7+ hours per entity type)
- Would need to deduplicate races
- Complex coordination logic
- No advantage for recent data

**Conclusion:** Inefficient and unnecessary.

---

### Option 2: Use for Entity-Specific Enrichment (like horse Pro enrichment)
**Verdict: REJECT**

**Pros:**
- Could add entity-specific historical context
- Pattern matches existing horse enrichment

**Cons:**
- **No unique data** - all fields in /v1/results
- Added complexity for no benefit
- Rate limit impact
- Maintenance burden

**Conclusion:** No value add over /v1/results.

---

### Option 3: Use for Historical Backfill Only
**Verdict: POSSIBLE but UNNECESSARY**

**Pros:**
- Can access >12 months historical data
- Complete result history per entity

**Cons:**
- /v1/results covers 12 months (sufficient for most ML)
- Very slow (4.7 hours per 34K entities)
- Would need deduplication logic
- **No unique fields to justify effort**

**Conclusion:** Only consider if you specifically need >12 months of historical results AND current 12-month data is insufficient for ML training.

---

### Option 4: Continue Current Strategy (/v1/results only)
**Verdict: RECOMMENDED ✓**

**Pros:**
- Efficient bulk fetching
- Gets all races and runners
- Simple architecture
- No duplication
- **Already has all fields**

**Cons:**
- Limited to 12 months history (acceptable)

**Conclusion:** No changes needed to current architecture.

---

## 7. Implementation Plan

### A. Immediate Actions (High Priority)

**Update `results_fetcher.py` to capture missing fields:**

```python
# In _prepare_runner_records() method, add:

runner_record = {
    # ... existing fields ...

    # NEW FIELDS (already in API, not yet captured):
    'finishing_time': runner.get('time'),  # "1:27.07"
    'starting_price_decimal': runner.get('sp_dec'),  # "19.00"
    'starting_price_fractional': runner.get('sp'),  # "18/1"
    'overall_beaten_distance': runner.get('ovr_btn'),  # "0"
    'weight_stones_lbs': runner.get('weight'),  # "9-7"
    'jockey_claim_lbs': runner.get('jockey_claim_lbs'),  # "5"

    # These exist in schema but may not be populated:
    'comment': runner.get('comment'),
    'silk_url': runner.get('silk_url'),
}
```

### B. Database Schema Changes

Add columns to `ra_runners` table:

```sql
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS finishing_time TEXT;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS starting_price_decimal DECIMAL(10,2);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS starting_price_fractional TEXT;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS overall_beaten_distance DECIMAL(10,2);
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS weight_stones_lbs TEXT;
ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS jockey_claim_lbs INTEGER;

-- Verify comment and silk_url already exist:
-- comment TEXT (should exist)
-- silk_url TEXT (should exist)
```

### C. Validation

After implementation:

1. Run results fetcher for recent date
2. Verify new fields populated in database
3. Check data quality:
   - `finishing_time` format consistent
   - `starting_price_decimal` converts from fractional
   - `ovr_btn` vs `btn` comparison
4. Update test suite

### D. Rate Limit Impact

**None.** No additional API calls required - just capturing more fields from existing responses.

---

## 8. Entity Results Endpoints - Use Cases

While not needed for current operations, entity-specific results endpoints could be valuable for:

### A. Horse History (/v1/horses/{id}/results)
**Use Case:** Complete race history for individual horse
- Full career record
- Performance progression
- Track/distance preferences
- Historical form analysis

**When to use:**
- Building individual horse profiles
- Historical performance research
- Track specialization analysis

### B. Jockey History (/v1/jockeys/{id}/results)
**Use Case:** Complete ride history for individual jockey
- Career statistics
- Course/trainer partnerships
- Strike rate analysis
- Historical form

**When to use:**
- Jockey performance analysis
- Trainer-jockey combinations
- Course specialist identification

### C. Trainer History (/v1/trainers/{id}/results)
**Use Case:** Complete runner history for individual trainer
- Stable form
- Horse placement patterns
- Historical win rates
- Seasonal trends

**When to use:**
- Trainer form analysis
- Stable profile building
- Pattern recognition

### D. Owner History (/v1/owners/{id}/results)
**Use Case:** Complete ownership history
- Investment performance
- Trainer relationships
- Horse acquisition patterns

**When to use:**
- Ownership analysis
- Investment research
- Breeding program analysis

---

## 9. Code Examples

### A. Query Jockey Results

```python
from utils.api_client import RacingAPIClient

api_client = RacingAPIClient(username='...', password='...')

# Get jockey's last 50 results
response = api_client._make_request(
    f'/jockeys/{jockey_id}/results',
    params={'limit': 50}
)

# Get jockey's results for date range
response = api_client._make_request(
    f'/jockeys/{jockey_id}/results',
    params={
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'region': ['gb', 'ire'],
        'limit': 100
    }
)
```

### B. Parse Response

```python
if response and response.get('results'):
    for race in response['results']:
        race_id = race['race_id']
        race_date = race['date']
        course = race['course']

        for runner in race.get('runners', []):
            # This runner is where our jockey rode
            horse_name = runner['horse']
            position = runner['position']
            finishing_time = runner['time']
            sp_decimal = runner['sp_dec']

            print(f"{race_date} - {course}: {horse_name} finished {position} in {finishing_time}")
```

### C. Add Method to RacingAPIClient

```python
def get_jockey_results(self, jockey_id: str, start_date: Optional[str] = None,
                       end_date: Optional[str] = None, region_codes: Optional[List[str]] = None,
                       limit: int = 25, skip: int = 0) -> Optional[Dict]:
    """
    Get race results for a specific jockey

    Args:
        jockey_id: Jockey identifier
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        region_codes: Region codes to filter
        limit: Results per page
        skip: Pagination offset

    Returns:
        Response data or None
    """
    params = {'limit': limit, 'skip': skip}
    if start_date:
        params['start_date'] = start_date
    if end_date:
        params['end_date'] = end_date
    if region_codes:
        params['region'] = region_codes

    return self._make_request(f'/jockeys/{jockey_id}/results', params)
```

---

## 10. Performance Considerations

### A. Rate Limit Calculations

**Scenario: Query all 34,000 jockeys**
- Rate: 2 requests/second
- Time: 34,000 / 2 = 17,000 seconds = 4.7 hours

**Scenario: Query 1,000 active jockeys**
- Rate: 2 requests/second
- Time: 1,000 / 2 = 500 seconds = 8.3 minutes

**Scenario: Daily results fetch (current)**
- Fetch 1 day of results: 1-5 API calls
- Covers all races and all runners
- Time: 0.5 - 2.5 seconds

### B. Data Volume

**Jockey results endpoint:**
- Average: 200-500 results per jockey
- Top jockeys: 1,000+ results
- Data per result: ~2-10 KB
- Total: 100-500 KB per jockey

**Bulk results endpoint (current):**
- 1 day: 50-200 races
- 1 month: 1,500-6,000 races
- 1 year: 18,000-72,000 races
- Far more efficient for bulk operations

---

## 11. Testing Summary

### A. Endpoints Tested

1. ✓ `/v1/jockeys/{jockey_id}/results` - Standard
2. ✗ `/v1/jockeys/{jockey_id}/results/pro` - Does not exist (404)
3. ✓ `/v1/trainers/{trainer_id}/results` - Exists
4. ✓ `/v1/horses/{horse_id}/results` - Exists
5. ✓ `/v1/owners/{owner_id}/results` - Exists

### B. Parameters Tested

- ✓ `limit` - Works (no max limit observed)
- ✓ `skip` - Works (pagination)
- ✓ `start_date` / `end_date` - Works (date filtering)
- ✓ `region` - Works (region filtering)

### C. Sample Data

- 3 jockeys tested
- 400+ total results examined
- 100% field coverage achieved
- All fields present in /v1/results confirmed

---

## 12. Final Recommendations

### **PRIMARY RECOMMENDATION: No Changes to Architecture**

1. **Continue using `/v1/results` as primary source**
   - Most efficient for daily operations
   - Contains all necessary fields
   - Simple, proven architecture

2. **Update `results_fetcher.py` to capture missing fields**
   - Add: `finishing_time`, `sp_dec`, `ovr_btn`, `weight`, `jockey_claim_lbs`
   - Populate: `comment`, `silk_url` (schema exists)
   - No additional API calls needed

3. **Update database schema**
   - Add new columns to `ra_runners`
   - Run migration script
   - Validate data quality

4. **Do NOT use entity-specific results endpoints for daily operations**
   - No unique data benefit
   - Significantly slower
   - Added complexity

5. **OPTIONAL: Consider entity endpoints for special use cases**
   - Individual entity profile building
   - Historical research (>12 months)
   - Specific analysis projects
   - NOT for daily data pipeline

---

## 13. Next Steps

### Immediate (This Week)
1. ✓ Complete endpoint analysis (DONE)
2. Add missing fields to results_fetcher.py
3. Create database migration script
4. Test with recent data

### Short Term (Next Sprint)
1. Validate data quality
2. Update ML pipelines to use new fields
3. Document finishing_time interpretation
4. Create time-based analysis examples

### Long Term (Future Enhancement)
1. Consider historical backfill if needed
2. Build entity profile endpoints (API layer)
3. Time-based performance metrics
4. Advanced pace analysis

---

## 14. Resources

### Test Scripts
- `/scripts/test_jockey_results_endpoint.py` - Comprehensive endpoint testing
- `/scripts/analyze_jockey_results_data_gaps.py` - Data gap analysis

### Sample Data
- `/logs/jockey_results_*.json` - Raw API responses
- `/logs/data_gap_analysis.txt` - Analysis output
- `/logs/jockey_endpoint_test_output.txt` - Test execution log

### Related Documentation
- `/docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md` - API testing
- `/fetchers/results_fetcher.py` - Current implementation
- `/utils/position_parser.py` - Result parsing utilities

---

## Conclusion

The `/v1/jockeys/{jockey_id}/results` endpoint is well-designed and provides complete race result data, but it **does not offer any unique fields** beyond what's already available in `/v1/results`.

**Key Insight:** The missing fields (`time`, `sp_dec`, `ovr_btn`, etc.) are not missing from the API - they're missing from our data capture. All fields are present in `/v1/results`, we just haven't been storing them.

**Action Required:** Update `results_fetcher.py` to capture the 6-7 missing fields. No architectural changes needed.

**Time Investment:** This is a simple code change, requiring:
- 30 minutes: Code update
- 15 minutes: Database migration
- 15 minutes: Testing
- Total: ~1 hour

**Value Impact:**
- **HIGH** - Finishing times enable advanced performance analysis
- **HIGH** - Decimal odds simplify betting calculations
- **MEDIUM** - Additional fields improve data completeness

---

**Analysis completed by:** Claude Code
**Date:** 2025-10-17
**Status:** Production recommendations ready for implementation
