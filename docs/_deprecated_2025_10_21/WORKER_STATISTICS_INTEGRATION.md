# Worker Statistics Integration - Complete

## Summary

✅ **Entity statistics are now automatically updated by the worker after each data fetch.**

## What Changed

### File Modified: `start_worker.py`

**New Function Added:**
```python
def update_entity_statistics():
    """Update entity statistics (jockeys, trainers, owners)"""
    # Calls Supabase rpc('update_entity_statistics')
    # Logs results: jockeys_updated, trainers_updated, owners_updated
    # Gracefully handles errors (logs but doesn't fail the run)
```

**Integration Points:**

1. **Daily Fetch (1:00 AM UTC)** - `run_daily_fetch()`
   - Fetches races and results
   - **Then updates statistics**

2. **Weekly Fetch (Sunday 2:00 AM UTC)** - `run_weekly_fetch()`
   - Fetches jockeys, trainers, owners, horses
   - **Then updates statistics**

## How It Works

```
Data Fetch Completes
    ↓
Check if successful
    ↓
If SUCCESS:
    ↓
Call update_entity_statistics()
    ↓
Execute: rpc('update_entity_statistics')
    ↓
Update ra_jockeys statistics
Update ra_trainers statistics
Update ra_owners statistics
    ↓
Log results:
  ✓ Jockeys updated:  1,234
  ✓ Trainers updated: 1,567
  ✓ Owners updated:   2,890
    ↓
Continue (even if error)
```

## Expected Logs

### Successful Update
```
================================================================================
DAILY FETCH SUMMARY
================================================================================
Races:   45 fetched, 42 new/updated
Runners: 543 fetched, 489 new/updated
Results: 38 fetched, 38 new/updated
         1/1 days had data
================================================================================
Daily fetch completed successfully

Updating entity statistics with new data...
--------------------------------------------------------------------------------
UPDATING ENTITY STATISTICS
--------------------------------------------------------------------------------
Calling update_entity_statistics() function...
✓ Jockeys updated:  1,234
✓ Trainers updated: 1,567
✓ Owners updated:   2,890
Entity statistics update completed successfully
--------------------------------------------------------------------------------
```

### Timeout Error (Graceful Handling)
```
Daily fetch completed successfully

Updating entity statistics with new data...
--------------------------------------------------------------------------------
UPDATING ENTITY STATISTICS
--------------------------------------------------------------------------------
Calling update_entity_statistics() function...
ERROR: Entity statistics update failed: statement timeout
Continuing despite statistics update failure (will retry on next run)
--------------------------------------------------------------------------------
```

## Backup Mechanism

If worker statistics updates timeout frequently, you can enable the Supabase cron job as a backup:

1. Run `SETUP_SUPABASE_CRON.sql` in Supabase SQL Editor
2. Cron job runs at 3:00 AM UTC (after worker completes)
3. Uses server-side execution (no timeout issues)

## Statistics Updated

### Jockeys (`ra_jockeys`)
- `total_rides`, `total_wins`, `total_places`
- `win_rate`, `place_rate`
- `stats_updated_at`

### Trainers (`ra_trainers`)
- `total_runners`, `total_wins`, `total_places`
- `win_rate`, `place_rate`
- `recent_14d_runs`, `recent_14d_wins`, `recent_14d_win_rate`
- `stats_updated_at`

### Owners (`ra_owners`)
- `total_horses`, `total_runners`, `total_wins`, `total_places`
- `win_rate`, `place_rate`
- `active_last_30d`
- `stats_updated_at`

## Deployment

To deploy this change:

1. **Commit the changes:**
   ```bash
   git add start_worker.py
   git commit -m "Add automatic entity statistics updates to worker"
   git push
   ```

2. **Deploy to Render:**
   - Render will automatically redeploy on git push
   - OR manually trigger deploy in Render dashboard

3. **Monitor logs:**
   - Check that statistics updates appear in worker logs
   - Look for "UPDATING ENTITY STATISTICS" section
   - Verify jockeys/trainers/owners counts

4. **Optional - Set up cron backup:**
   - Run `SETUP_SUPABASE_CRON.sql` in Supabase
   - Provides safety net if worker timeouts occur

## Testing Locally

Test the worker integration locally:

```bash
# Run daily fetch (includes statistics update)
python3 start_worker.py
```

Or test statistics update directly:

```bash
# In Python
from start_worker import update_entity_statistics
update_entity_statistics()
```

## Verification Queries

After deployment, verify statistics are updating:

```sql
-- Check last update time
SELECT
  'Jockeys' as entity,
  MAX(stats_updated_at) as last_updated,
  COUNT(*) as total_with_stats
FROM ra_jockeys
WHERE stats_updated_at IS NOT NULL

UNION ALL

SELECT
  'Trainers',
  MAX(stats_updated_at),
  COUNT(*)
FROM ra_trainers
WHERE stats_updated_at IS NOT NULL

UNION ALL

SELECT
  'Owners',
  MAX(stats_updated_at),
  COUNT(*)
FROM ra_owners
WHERE stats_updated_at IS NOT NULL;
```

Expected result: `last_updated` should be within the last day.

## Error Handling

The statistics update is designed to be **non-blocking**:

- ✅ If statistics update succeeds → Great!
- ❌ If statistics update fails → Logged as error, but worker continues
- 🔄 Next run will retry the update

This ensures that a statistics timeout doesn't break the entire data fetch workflow.

## Summary

- ✅ **Implementation complete** in `start_worker.py`
- ✅ **Automatic updates** after daily and weekly fetches
- ✅ **Graceful error handling** (non-blocking)
- ✅ **Comprehensive logging** of results
- ✅ **Backup mechanism** available via Supabase cron
- 🚀 **Ready for deployment** to production

---

**Files Modified:**
- `start_worker.py` - Added statistics update integration

**Files Created:**
- `SETUP_SUPABASE_CRON.sql` - Backup cron job setup
- `WORKER_STATISTICS_INTEGRATION.md` - This document

**Documentation Updated:**
- `STATISTICS_DEPLOYMENT_SUMMARY.md` - Updated with worker integration details
