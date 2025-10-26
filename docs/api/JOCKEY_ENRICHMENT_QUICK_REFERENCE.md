# Jockey Data Enrichment - Quick Reference

**Quick Summary:** What jockey data is available and how to enrich it

**Full Report:** `/docs/api/JOCKEY_DATA_ENRICHMENT_RESEARCH.md`

---

## TL;DR - Key Findings

1. **The Racing API provides MINIMAL jockey data:**
   - Only 3 fields: `id`, `name`, `jockey_claim_lbs`
   - No profile endpoint, no statistics endpoint, no biographical data

2. **All enrichment comes from DATABASE AGGREGATION:**
   - Calculate statistics from `ra_mst_runners` table
   - Migration 007 already provides career stats
   - Can add recent form, contextual stats, partnerships

3. **Small gap found:**
   - Missing field: `apprentice_allowance` (available but not captured)
   - Fix: 5-minute code change

4. **Quick wins available:**
   - Recent form stats (14-day, 30-day)
   - Prize money tracking
   - Activity flags
   - Effort: 2-3 hours total

---

## What API Provides

### Jockey-Specific Endpoints

❌ **No individual jockey profile endpoint exists**
- `/v1/jockeys/{id}` - Does NOT exist (404)
- `/v1/jockeys/{id}/statistics` - Does NOT exist (404)
- `/v1/jockeys/{id}/form` - Does NOT exist (404)

✅ **Name search only:**
- `/v1/jockeys/search?name=Murphy` - Returns id and name ONLY

### Jockey Data in Race Endpoints

**Racecards (`/v1/racecards/pro`) per runner:**
```json
{
  "jockey": "Kieran O'Neill",
  "jockey_id": "jky_250764",
  "jockey_claim_lbs": "0",
  "jockey_allowance": "0"  // Sometimes present
}
```

**Results (`/v1/results`) per runner:**
```json
{
  "jockey": "Kieran O'Neill",
  "jockey_id": "jky_250764",
  "jockey_claim_lbs": "0"
}
```

**That's it. Nothing more.**

---

## What We Currently Capture

### From API (via EntityExtractor)

✅ `jockey_id` - Jockey identifier
✅ `name` - Jockey name
❌ `jockey_claim_lbs` - Claim amount (not stored in ra_jockeys)
❌ `apprentice_allowance` - Allowance (not currently captured)

### From Database (Migration 007)

✅ `total_rides` - Career rides
✅ `total_wins` - Career wins
✅ `total_places` - Career places (1st, 2nd, 3rd)
✅ `total_seconds` - Career seconds
✅ `total_thirds` - Career thirds
✅ `win_rate` - Win percentage
✅ `place_rate` - Place percentage
✅ `stats_updated_at` - Last calculation time

---

## What We Can Add (Easy)

### Recent Form Statistics (2-3 hours)

**New fields to add to ra_jockeys:**
```sql
recent_14d_rides          -- Rides in last 14 days
recent_14d_wins           -- Wins in last 14 days
recent_14d_win_rate       -- Win rate in last 14 days
recent_30d_rides          -- Rides in last 30 days
recent_30d_wins           -- Wins in last 30 days
recent_30d_win_rate       -- Win rate in last 30 days
last_ride_date            -- Date of most recent ride
days_since_last_ride      -- Days since last ride
active_last_30d           -- Boolean: rode in last 30 days
```

**Value:** Shows current form vs. career average
**Source:** Calculated from ra_mst_runners + ra_mst_races
**Effort:** 2-3 hours (extend migration 007)

---

### Prize Money Tracking (30 minutes)

**New fields:**
```sql
total_prize_money         -- Career prize money won
recent_30d_prize_money    -- Prize money in last 30 days
```

**Value:** Financial success metric
**Source:** Sum of `ra_mst_runners.prize_money_won` where position = 1
**Effort:** 30 minutes

---

### Contextual Statistics (4-6 hours)

**Create new table: `ra_jockey_context_stats`**

Tracks win rates by:
- Surface (AW vs. Turf)
- Distance band (Sprint, Mile, Middle, Distance)
- Class (Class 1-7)
- Going (Firm, Good, Soft, etc.)
- Course (specific tracks)

**Example query:**
```sql
SELECT context_value, total_rides, win_rate
FROM ra_jockey_context_stats
WHERE jockey_id = 'jky_250764' AND context_type = 'surface';
```

**Value:** Very high for ML models
**Effort:** 4-6 hours

---

### Partnership Analysis (2-3 hours)

**Create views:**
- `jockey_trainer_partnerships` - Jockey + Trainer combinations
- `jockey_horse_partnerships` - Jockey + Horse combinations

**Shows:**
- Rides together
- Wins together
- Partnership win rate
- Last/first ride together

**Value:** High for insights and predictions
**Effort:** 2-3 hours

---

## What We CANNOT Get

❌ Date of birth / Age
❌ Nationality
❌ Debut date
❌ Physical attributes (height, weight)
❌ License type/status
❌ Official rankings
❌ Biography
❌ Profile images

**These would require external data sources or manual entry.**
**Not needed for core functionality or predictions.**

---

## Quick Fixes

### 1. Capture Missing Field (5 minutes)

**Problem:** `apprentice_allowance` available but not captured

**Fix:** Edit `fetchers/races_fetcher.py`

```python
# Around line 287
runner_record = {
    # ... existing fields ...
    'jockey_claim': runner.get('jockey_claim'),
    'apprentice_allowance': runner.get('jockey_allowance'),  # ADD THIS LINE
    # ... rest of fields ...
}
```

Do the same in `fetchers/results_fetcher.py`.

---

### 2. Update Statistics Function (extend existing)

**File:** `migrations/011_add_jockey_recent_form.sql`

```sql
-- Add new columns
ALTER TABLE ra_jockeys
ADD COLUMN recent_14d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_14d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN recent_30d_rides INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_wins INTEGER DEFAULT NULL,
ADD COLUMN recent_30d_win_rate DECIMAL(5,2) DEFAULT NULL,
ADD COLUMN last_ride_date DATE DEFAULT NULL,
ADD COLUMN days_since_last_ride INTEGER DEFAULT NULL,
ADD COLUMN active_last_30d BOOLEAN DEFAULT FALSE;

-- Modify existing update_entity_statistics() function
-- (see full report for complete SQL)
```

---

## Data Flow

```
Racing API (/v1/racecards/pro, /v1/results)
    ↓
  Fetchers (races_fetcher, results_fetcher)
    ↓
  EntityExtractor
    ↓
  ra_jockeys (basic identity)
    ↓
  ra_mst_runners (race participation with jockey context)
    ↓
  Database Aggregation (update_entity_statistics())
    ↓
  ra_jockeys (enriched with statistics)
    ↓
  Optional: ra_jockey_context_stats (contextual analysis)
    ↓
  Optional: Partnership views (relationship analysis)
```

---

## Current Implementation

### Extraction (Working)

**File:** `utils/entity_extractor.py`

```python
def extract_from_runners(self, runner_records: List[Dict]) -> Dict[str, List[Dict]]:
    """Extract jockeys from runner records"""
    for runner in runner_records:
        jockey_id = runner.get('jockey_id')
        jockey_name = runner.get('jockey_name')
        if jockey_id and jockey_name:
            jockeys[jockey_id] = {
                'jockey_id': jockey_id,
                'name': jockey_name,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
```

### Statistics (Working)

**Database Function:**
```sql
SELECT * FROM update_entity_statistics();
```

Returns:
- jockeys_updated (count)
- trainers_updated (count)
- owners_updated (count)

**View:**
```sql
SELECT * FROM jockey_statistics WHERE calculated_win_rate > 15;
```

---

## Recommendations

### Immediate (Do Now)
1. ✅ Read full research report
2. ✅ Fix `apprentice_allowance` extraction (5 min)
3. ✅ Plan recent form statistics migration

### Short-Term (This Week)
1. Implement recent form statistics (Migration 011)
2. Add prize money tracking
3. Test statistics calculation

### Medium-Term (This Month)
1. Build contextual statistics table
2. Create partnership analysis views
3. Add automated testing

### Long-Term (Future)
1. Consider external data integration (only if specific need)
2. Profile images (only if building public-facing UI)
3. Biographical data (nice-to-have, not essential)

---

## Key SQL Queries

### Get Jockey Statistics
```sql
SELECT * FROM jockey_statistics WHERE jockey_id = 'jky_250764';
```

### Find Top Jockeys by Win Rate
```sql
SELECT name, win_rate, total_rides, total_wins
FROM ra_jockeys
WHERE total_rides >= 100
ORDER BY win_rate DESC
LIMIT 10;
```

### Find Active Jockeys
```sql
SELECT name, recent_30d_rides, recent_30d_win_rate
FROM ra_jockeys
WHERE active_last_30d = TRUE
ORDER BY recent_30d_win_rate DESC;
```

### Compare Career vs. Recent Form
```sql
SELECT
    name,
    win_rate as career_win_rate,
    recent_30d_win_rate,
    recent_30d_win_rate - win_rate as form_difference
FROM ra_jockeys
WHERE active_last_30d = TRUE
  AND recent_30d_rides >= 10
ORDER BY form_difference DESC;
```

---

## Testing

**After implementing new statistics:**

```bash
# Run statistics update
psql $SUPABASE_URL -c "SELECT * FROM update_entity_statistics();"

# Verify results
psql $SUPABASE_URL -c "
SELECT
    COUNT(*) as total_jockeys,
    COUNT(CASE WHEN total_rides IS NOT NULL THEN 1 END) as with_career_stats,
    COUNT(CASE WHEN recent_30d_rides IS NOT NULL THEN 1 END) as with_recent_stats
FROM ra_jockeys;
"
```

---

## Performance

**Statistics Update Time:**
- Career stats only: ~5 seconds (current)
- With recent form: ~10 seconds (estimated)
- With contextual stats: ~30 seconds (estimated)

**Recommended Schedule:**
- Career + Recent form: Daily at 02:00
- Contextual stats: Weekly on Sunday

---

## Related Files

**Code:**
- `utils/entity_extractor.py` - Jockey extraction logic
- `fetchers/races_fetcher.py` - Racecard fetching + extraction
- `fetchers/results_fetcher.py` - Results fetching + extraction
- `fetchers/jockeys_fetcher.py` - Direct jockey search (limited use)

**Database:**
- `migrations/007_add_entity_table_enhancements.sql` - Current statistics
- `migrations/011_add_jockey_recent_form.sql` - To be created

**Documentation:**
- `/docs/api/JOCKEY_DATA_ENRICHMENT_RESEARCH.md` - Full report
- `/docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md` - Endpoint testing
- `/docs/audit/DATABASE_SCHEMA_AUDIT_DETAILED.md` - Schema reference

---

**For complete details, SQL examples, and testing strategy:**
**→ See `/docs/api/JOCKEY_DATA_ENRICHMENT_RESEARCH.md`**
