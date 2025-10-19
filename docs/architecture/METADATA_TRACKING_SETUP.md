# Metadata Tracking Setup

Track when data was last updated, number of records created/updated, and view update history.

---

## Overview

The metadata tracking system records:
- **Last update time** for each table
- **Number of records** created/updated in each operation
- **Update history** with timestamps
- **Success/failure status** of each operation
- **Operation metadata** (date ranges, chunks, etc.)

---

## Setup

### Step 1: Create Metadata Table in Supabase

Run this SQL in your Supabase SQL Editor:

```sql
-- Create metadata tracking table
CREATE TABLE IF NOT EXISTS ra_collection_metadata (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    table_name TEXT NOT NULL,
    operation TEXT NOT NULL,
    records_processed INTEGER DEFAULT 0,
    records_inserted INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    status TEXT NOT NULL,
    error_message TEXT,
    metadata JSONB,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_metadata_table_name
    ON ra_collection_metadata(table_name);

CREATE INDEX IF NOT EXISTS idx_metadata_created_at
    ON ra_collection_metadata(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_metadata_status
    ON ra_collection_metadata(status);

CREATE INDEX IF NOT EXISTS idx_metadata_operation
    ON ra_collection_metadata(operation);

-- Add comment
COMMENT ON TABLE ra_collection_metadata IS
'Tracks data collection operations: when tables were updated, how many records, success/failure status';
```

### Step 2: Verify Table Creation

```bash
# View update history (will be empty initially)
python3 view_update_history.py
```

---

## Usage

### View Overall Summary

Shows last update for all tables:

```bash
python3 view_update_history.py
```

**Output:**
```
━━━ TABLE UPDATE SUMMARY ━━━

Table                Last Updated                                      Inserted     Updated      Status
──────────────────────────────────────────────────────────────────────────────────────────────────────
courses              2025-10-06 22:04:36 (45m ago)                    101          0            ✓ Success
bookmakers           2025-10-06 22:04:36 (45m ago)                    19           0            ✓ Success
results              2025-10-06 22:35:54 (15m ago)                    0            0            ✓ Success
races                Never                                             0            0            ○ Never Updated
...

━━━ RECENT UPDATE HISTORY (Last 20) ━━━

Time                   Table           Operation            Inserted   Status
──────────────────────────────────────────────────────────────────────────────
2025-10-06 22:35:54   results         initialization          1,234    ✓ Success
2025-10-06 22:25:32   results         initialization          1,180    ✓ Success
2025-10-06 22:15:07   results         initialization          1,205    ✓ Success
...
```

### View Detailed Table Statistics

```bash
# Show detailed stats for a specific table
python3 view_update_history.py --table ra_results

# Show stats for last 7 days
python3 view_update_history.py --table ra_results --days 7

# Show stats for last 90 days
python3 view_update_history.py --table ra_results --days 90
```

**Output:**
```
━━━ STATISTICS FOR RA_RESULTS (Last 30 days) ━━━

  Total Updates:     44
  Records Inserted:  52,345
  Records Updated:   0
  Success Rate:      100.0%

Recent Updates:

Time                   Operation                  Inserted   Updated    Status
──────────────────────────────────────────────────────────────────────────────
2025-10-06 22:35:54   initialization                1,234         0    ✓ Success
2025-10-06 22:25:32   initialization                1,180         0    ✓ Success
2025-10-06 22:15:07   initialization                1,205         0    ✓ Success
...
```

### View More History

```bash
# Show last 50 updates
python3 view_update_history.py --limit 50

# Show last 100 updates
python3 view_update_history.py --limit 100
```

---

## Integration with Data Collection Scripts

The metadata tracker is automatically integrated with all data collection operations when you use it in your scripts.

### Example: Recording an Update

```python
from utils.metadata_tracker import MetadataTracker
from utils.supabase_client import SupabaseReferenceClient

# Initialize
db = SupabaseReferenceClient(url, service_key)
tracker = MetadataTracker(db.client)

# After inserting data
tracker.record_update(
    table_name='ra_results',
    operation='daily_update',
    records_processed=1500,
    records_inserted=1234,
    records_updated=266,
    records_skipped=0,
    status='success',
    metadata={
        'date_range': {'start': '2025-10-05', 'end': '2025-10-06'},
        'chunk': '1/10'
    }
)
```

### Example: Handling Errors

```python
try:
    # Data collection operation
    result = fetch_and_store_data()

    tracker.record_update(
        table_name='ra_results',
        operation='daily_update',
        records_processed=result['processed'],
        records_inserted=result['inserted'],
        status='success'
    )
except Exception as e:
    tracker.record_update(
        table_name='ra_results',
        operation='daily_update',
        records_processed=0,
        records_inserted=0,
        status='failed',
        error_message=str(e)
    )
```

---

## Command Reference

```bash
# View overall summary
python3 view_update_history.py

# View detailed table statistics
python3 view_update_history.py --table ra_results
python3 view_update_history.py --table ra_races
python3 view_update_history.py --table ra_runners

# Customize time period
python3 view_update_history.py --table ra_results --days 7
python3 view_update_history.py --table ra_results --days 90

# Show more history
python3 view_update_history.py --limit 50
python3 view_update_history.py --limit 100
```

---

## Metadata Table Schema

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID | Primary key |
| `table_name` | TEXT | Name of table updated (e.g., 'ra_results') |
| `operation` | TEXT | Type of operation (e.g., 'initialization', 'daily_update') |
| `records_processed` | INTEGER | Total records processed |
| `records_inserted` | INTEGER | New records inserted |
| `records_updated` | INTEGER | Existing records updated |
| `records_skipped` | INTEGER | Records skipped (duplicates, errors) |
| `status` | TEXT | 'success', 'partial', or 'failed' |
| `error_message` | TEXT | Error message if operation failed |
| `metadata` | JSONB | Additional metadata (date ranges, chunks, etc.) |
| `updated_at` | TIMESTAMP | When record was last updated |
| `created_at` | TIMESTAMP | When operation occurred |

---

## Benefits

✅ **Track Progress**: See exactly when each table was last updated
✅ **Audit Trail**: Complete history of all data collection operations
✅ **Success Monitoring**: Track success rates and identify failures
✅ **Performance Metrics**: See how many records are being processed
✅ **Troubleshooting**: Quickly identify which operations failed and when
✅ **Reporting**: Generate reports on data collection activities

---

## Next Steps

1. **Create the metadata table** in Supabase (Step 1 above)
2. **Verify it works**: Run `python3 view_update_history.py`
3. **Integrate with existing scripts**: Add tracker.record_update() calls
4. **Monitor regularly**: Check update history to ensure data is current

---

For more information, see:
- `utils/metadata_tracker.py` - Metadata tracking utilities
- `monitors/view_update_history.py` - View update history script
