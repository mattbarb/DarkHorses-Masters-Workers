# Position Data Pipeline - Current Status

**Date:** 2025-10-14
**Status:** IN PROGRESS - Fixing database schema mismatches

## Summary

We're implementing the critical position data pipeline that will enable ML models to calculate win rates and learn winning patterns. This is the fix for the "all horses showing 0% win rate" problem.

## What We've Accomplished ✅

1. **Created database migration** (`005_add_position_fields_to_runners.sql`)
   - ✅ User has applied this (Step 1 complete)
   - Added: `position`, `distance_beaten`, `prize_won`, `starting_price`, `result_updated_at`

2. **Created position parsing utility** (`utils/position_parser.py`)
   - ✅ Parses position from various formats (1, "1st", "F" for fell, etc.)
   - ✅ Parses distance beaten (0, "1.25L", etc.)
   - ✅ Fixed: Decimal → float conversion for JSON serialization
   - ✅ Parses prize money and starting price

3. **Modified results fetcher** (`fetchers/results_fetcher.py`)
   - ✅ Added `_prepare_runner_records()` method
   - ✅ Extracts position data using `extract_position_data()`
   - ✅ Fixed: `or` → `official_rating` (SQL reserved word issue)
   - ⚠️  **ISSUE:** Using `race_date` field that doesn't exist in ra_runners schema

4. **Validated API has position data**
   - ✅ Tested with `test_position_extraction.py`
   - ✅ Confirmed: position, btn (distance beaten), prize, sp (starting price) all available

5. **Created sample fetcher** (`fetch_sample_results.py`)
   - ✅ Fetches small sample (3 days) for testing
   - Used for debugging without hitting API rate limits

## Current Blocker 🚫

**Schema Mismatch in `ra_runners` table:**

The code is trying to insert these fields that don't exist in the actual database:
- `race_date` - Need to remove this (race date is in ra_races table, linked by race_id)
- Possibly other fields

**Error message:**
```
Could not find the 'race_date' column of 'ra_runners' in the schema cache
```

## What Needs to Happen Next 📋

### Option 1: Fix the Code (Recommended - Faster)
Remove `race_date` from the runner record preparation in `fetchers/results_fetcher.py:308`

```python
# REMOVE THIS LINE:
'race_date': race_date,
```

The race date is already stored in the `ra_races` table and can be joined via `race_id`.

### Option 2: Check Actual Database Schema
Query the actual `ra_runners` table schema to see what columns exist:

```sql
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 'ra_runners'
ORDER BY ordinal_position;
```

Then match the code to only use existing columns.

## Impact Once Fixed 🎯

Once position data is being inserted correctly:

**Before (Current State):**
- 0% of runners have position data
- All 772 horses show 0% win rate
- 46 ML fields (43%) are non-functional
- ML model cannot learn win patterns

**After (With Position Data):**
- 100% of runners will have position data
- Win rates will vary realistically (10-30% for different horses)
- 46 ML fields become functional
- Data completeness jumps from 36% → 80%+
- ML model can learn what makes a winner

## Files Modified

1. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/migrations/005_add_position_fields_to_runners.sql` (✅ Applied)
2. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/utils/position_parser.py` (✅ Complete)
3. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetchers/results_fetcher.py` (⚠️ Needs one more fix)
4. `/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/fetch_sample_results.py` (✅ Complete)

## Test Commands

**Check current position data coverage:**
```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers

SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtc2p2bWxha25udnBweHNncGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDAxNjQxNSwiZXhwIjoyMDY1NTkyNDE1fQ.8JiQWlaTBH18o8PvElYC5aBAKGw8cfdMBe8KbXTAukI' \
python3 -c "
from utils.supabase_client import SupabaseReferenceClient
import os
client = SupabaseReferenceClient(os.environ['SUPABASE_URL'], os.environ['SUPABASE_SERVICE_KEY'])
total = client.client.table('ra_runners').select('*', count='exact').limit(1).execute()
with_pos = client.client.table('ra_runners').select('*', count='exact').not_.is_('position', 'null').limit(1).execute()
print(f'Total: {total.count}, With position: {with_pos.count}, Coverage: {(with_pos.count/total.count*100) if total.count > 0 else 0:.1f}%')
"
```

**Run sample fetcher (after fixing race_date issue):**
```bash
SUPABASE_URL='https://amsjvmlaknnvppxsgpfk.supabase.co' \
SUPABASE_SERVICE_KEY='eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtc2p2bWxha25udnBweHNncGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDAxNjQxNSwiZXhwIjoyMDY1NTkyNDE1fQ.8JiQWlaTBH18o8PvElYC5aBAKGw8cfdMBe8KbXTAukI' \
RACING_API_USERNAME='l2fC3sZFIZmvpiMt6DdUCpEv' \
RACING_API_PASSWORD='R0pMr1L58WH3hUkpVtPcwYnw' \
python3 fetch_sample_results.py --days-back 3
```

## Key Insight 💡

The position data IS available in the API and IS being extracted correctly. The issue is purely a schema mismatch between what the code tries to insert and what columns actually exist in the database.

We're very close - just need to align the code with the actual database schema!
