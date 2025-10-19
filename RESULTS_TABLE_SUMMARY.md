# ra_results Table - Quick Summary

## What Was Added

✅ **New Table:** `ra_results` - Stores race-level result data from Racing API

## What Data Does It Capture?

### Previously Missing Data (NOW CAPTURED!)

1. **Tote Pool Dividends** 💰
   - `tote_win` - Win dividend
   - `tote_pl` - Place dividends
   - `tote_ex` - Exacta
   - `tote_csf` - Computer Straight Forecast
   - `tote_tricast` - Tricast (1st, 2nd, 3rd in order)
   - `tote_trifecta` - Trifecta (1st, 2nd, 3rd any order)

2. **Winning Time Details** ⏱️
   - `winning_time_detail` - e.g., "1:48.55 (slow by 3.25s)"

3. **Race Comments** 📝
   - `comments` - Stewards notes, running commentary

4. **Non-Runners** 🐴
   - `non_runners` - Horses that didn't start

5. **Race Classification** 📊
   - `pattern`, `rating_band`, `age_band`, `sex_rest`
   - More detailed distance info (`dist_y`, `dist_m`, `dist_f`)

## Files Changed

### 1. Migration File (NEW)
**`migrations/017_create_ra_results_table.sql`**
- Creates `ra_results` table
- Foreign key to `ra_races(race_id)`
- Indexes for performance
- **ACTION REQUIRED:** Run in Supabase SQL Editor

### 2. Results Fetcher (UPDATED)
**`fetchers/results_fetcher.py`**
- Transforms API response to extract result fields
- Inserts into both `ra_races` AND `ra_results`
- Logs result statistics

### 3. Supabase Client (UPDATED)
**`utils/supabase_client.py`**
- New method: `insert_results()`
- Handles upsert on conflict

### 4. Documentation (NEW)
**`RA_RESULTS_TABLE_IMPLEMENTATION.md`**
- Complete technical documentation
- Query examples
- Troubleshooting guide

## How to Deploy

### Step 1: Run Migration
```sql
-- In Supabase SQL Editor, paste contents of:
migrations/017_create_ra_results_table.sql
```

### Step 2: Verify Table Created
```sql
SELECT COUNT(*) FROM ra_results;
-- Should return 0 (empty table ready for data)
```

### Step 3: Test with Real Data
```bash
# Fetch last 7 days of results
python3 main.py --entities results --test
```

### Step 4: Check Results Populated
```sql
SELECT
  COUNT(*) as total_results,
  COUNT(tote_win) as has_tote_win,
  COUNT(comments) as has_comments
FROM ra_results;
```

## Quick Verification Queries

### See Sample Results
```sql
SELECT
  race_id,
  course_name,
  race_name,
  tote_win,
  tote_ex,
  winning_time_detail
FROM ra_results
ORDER BY race_date DESC
LIMIT 10;
```

### Check Tote Coverage
```sql
SELECT
  COUNT(*) as total_races,
  COUNT(tote_win) as with_tote_data,
  ROUND(100.0 * COUNT(tote_win) / COUNT(*), 2) as coverage_pct
FROM ra_results;
```

## Data Architecture

```
API: /v1/results
    ↓
results_fetcher.py
    ├─ ra_races     (race metadata)
    ├─ ra_results   (tote, comments) ⭐ NEW
    └─ ra_runners   (positions, times)
```

## Why This Matters for ML

1. **Tote Pools** → Market sentiment analysis
2. **Winning Times** → Speed/pace figures
3. **Comments** → Race context (interference, running style)
4. **Non-Runners** → Field size and market impacts

## Expected Log Output

After deployment, you'll see:
```
Inserting 45 races into ra_races and ra_results...
Races inserted: {'inserted': 45, 'updated': 0, 'errors': 0}
Inserting 45 results into ra_results...
Results inserted: {'inserted': 45, 'updated': 0, 'errors': 0}
Runners inserted: {'inserted': 543, 'updated': 0, 'errors': 0}
```

## Checklist

- [ ] Run Migration 017 in Supabase
- [ ] Verify table exists with `SELECT * FROM ra_results LIMIT 1;`
- [ ] Test with `python3 main.py --entities results --test`
- [ ] Check data populated with verification queries
- [ ] Deploy to production

---

**Status:** ✅ Implementation complete, ready for deployment
**Priority:** HIGH - Captures valuable data for ML models
**Risk:** LOW - Non-breaking change (adds new table)
