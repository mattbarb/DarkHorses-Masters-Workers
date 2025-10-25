# Statistics Workers

This directory contains workers that populate enhanced statistics fields in the `ra_jockeys`, `ra_trainers`, and `ra_owners` tables.

## Overview

Each worker calculates 10 statistics fields from race results data:

### Jockeys (ra_jockeys)
- `last_ride_date` - Date of most recent ride
- `last_win_date` - Date of most recent win
- `days_since_last_ride` - Days since last ride
- `days_since_last_win` - Days since last win
- `recent_14d_rides` - Number of rides in last 14 days
- `recent_14d_wins` - Number of wins in last 14 days
- `recent_14d_win_rate` - Win rate in last 14 days (%)
- `recent_30d_rides` - Number of rides in last 30 days
- `recent_30d_wins` - Number of wins in last 30 days
- `recent_30d_win_rate` - Win rate in last 30 days (%)

### Trainers (ra_trainers)
- `last_runner_date` - Date of most recent runner
- `last_win_date` - Date of most recent win
- `days_since_last_runner` - Days since last runner
- `days_since_last_win` - Days since last win
- `recent_14d_runs` - Number of runners in last 14 days
- `recent_14d_wins` - Number of wins in last 14 days
- `recent_14d_win_rate` - Win rate in last 14 days (%)
- `recent_30d_runs` - Number of runners in last 30 days
- `recent_30d_wins` - Number of wins in last 30 days
- `recent_30d_win_rate` - Win rate in last 30 days (%)

### Owners (ra_owners)
- `last_runner_date` - Date of most recent runner
- `last_win_date` - Date of most recent win
- `days_since_last_runner` - Days since last runner
- `days_since_last_win` - Days since last win
- `recent_14d_runs` - Number of runners in last 14 days
- `recent_14d_wins` - Number of wins in last 14 days
- `recent_14d_win_rate` - Win rate in last 14 days (%)
- `recent_30d_runs` - Number of runners in last 30 days
- `recent_30d_wins` - Number of wins in last 30 days
- `recent_30d_win_rate` - Win rate in last 30 days (%)

## Workers

### Individual Workers

Each entity type has its own worker script:

1. **jockeys_statistics_worker.py** - Updates jockey statistics
2. **trainers_statistics_worker.py** - Updates trainer statistics
3. **owners_statistics_worker.py** - Updates owner statistics

### Master Worker

**run_all_statistics_workers.py** - Runs all three workers in sequence

## Usage

### Run All Workers (Recommended)

```bash
# Production: Process all entities
python3 scripts/statistics_workers/run_all_statistics_workers.py

# Test: Process only 10 entities per worker
python3 scripts/statistics_workers/run_all_statistics_workers.py --limit 10
```

### Run Individual Workers

```bash
# Jockeys only
python3 scripts/statistics_workers/jockeys_statistics_worker.py

# Trainers only
python3 scripts/statistics_workers/trainers_statistics_worker.py

# Owners only
python3 scripts/statistics_workers/owners_statistics_worker.py

# With limit (for testing)
python3 scripts/statistics_workers/jockeys_statistics_worker.py --limit 10
```

## How It Works

### Data Source

All statistics are calculated from Racing API results endpoints:
- `/v1/jockeys/{jockey_id}/results`
- `/v1/trainers/{trainer_id}/results`
- `/v1/owners/{owner_id}/results`

### Calculation Window

Workers fetch results from the **last 365 days** and calculate:
- Overall last ride/runner and win dates
- Days since last activity
- Form statistics for 14-day and 30-day windows

### Position Parsing

Winners are identified by position values:
- `"1"` or `"WON"` = Win
- `"2"` or `"2nd"` = Second place
- `"3"` or `"3rd"` = Third place

### Batch Processing

Workers process entities in batches of 100 to:
- Manage memory efficiently
- Handle large datasets (thousands of entities)
- Provide progress updates

### Error Handling

- Rate limiting: Automatic retry with exponential backoff
- API errors: Logged but don't stop processing
- Database errors: Logged with full details
- Failed entities are counted but don't affect others

## Performance

### Expected Duration

Based on typical entity counts:

| Entity Type | Count | Duration (estimate) |
|-------------|-------|---------------------|
| Jockeys     | ~2,000 | 30-60 minutes |
| Trainers    | ~1,500 | 20-40 minutes |
| Owners      | ~5,000 | 60-120 minutes |
| **TOTAL**   | ~8,500 | **2-3.5 hours** |

Duration varies based on:
- Number of results per entity
- API rate limits (2 requests/second)
- Pagination requirements (API limit: 50 results per page)

### Rate Limiting

Racing API enforces **2 requests per second**. The workers:
- Respect this limit automatically
- Include retry logic for rate limit errors
- Sleep between requests when needed

## Output

Workers provide detailed logging:

```
================================================================================
JOCKEYS STATISTICS WORKER
================================================================================
Fetching jockeys from database...
Found 2000 jockeys to process

Processing batch 1/20 (100 jockeys)...
Processing John Smith (jky_123456)...
Processing Jane Doe (jky_789012)...
...
Updated 100 jockeys in database
Batch 1 complete: 100 updated, 0 errors

...

================================================================================
JOCKEYS STATISTICS WORKER COMPLETE
================================================================================
Total jockeys: 2000
Processed: 2000
Updated: 2000
Errors: 0
Duration: 1842.50s
================================================================================
```

## Database Updates

Workers use **UPDATE** operations (not UPSERT) to:
- Only modify statistics fields
- Preserve existing entity data (name, etc.)
- Update `stats_updated_at` timestamp

Example update:
```python
{
    'last_ride_date': '2025-10-19',
    'days_since_last_ride': 0,
    'recent_14d_rides': 12,
    'recent_14d_wins': 2,
    'recent_14d_win_rate': 16.67,
    'stats_updated_at': '2025-10-19T10:30:00'
}
```

## Scheduling

### Recommended Schedule

Statistics should be updated **weekly** to:
- Keep recent form data current
- Track activity patterns
- Monitor win rates

### Cron Example

```bash
# Run every Sunday at 2am
0 2 * * 0 cd /path/to/DarkHorses-Masters-Workers && python3 scripts/statistics_workers/run_all_statistics_workers.py
```

### Integration with Main Worker

These workers can be integrated into the main worker schedule:
- Daily: Races and results (existing)
- Weekly: Entity statistics (new)
- Weekly: People and horses (existing)
- Monthly: Courses and bookmakers (existing)

## Testing

### Test with Limited Data

```bash
# Test with only 10 entities per worker
python3 scripts/statistics_workers/run_all_statistics_workers.py --limit 10
```

### Verify Results

```python
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

# Check updated jockeys
result = db.client.table('ra_jockeys')\
    .select('name, last_ride_date, recent_14d_rides, recent_14d_win_rate, stats_updated_at')\
    .not_.is_('stats_updated_at', 'null')\
    .order('stats_updated_at', desc=True)\
    .limit(10)\
    .execute()

for row in result.data:
    print(f"{row['name']}: {row['recent_14d_rides']} rides, {row['recent_14d_win_rate']}% win rate")
```

## Troubleshooting

### No Results Found

If a worker reports "No results found":
- Entity may be inactive (no races in last 365 days)
- API credentials may be incorrect
- Rate limits may be exceeded (wait and retry)

### Database Update Errors

If database updates fail:
- Check Supabase connection
- Verify table schema has statistics columns
- Check service key permissions

### Slow Performance

If workers are taking too long:
- Check API response times
- Verify rate limiting is working correctly
- Consider processing in smaller batches (reduce batch_size)

## Related Scripts

- `scripts/test_statistics_endpoints.py` - Test script showing calculation logic
- `main.py` - Main worker orchestrator (could integrate these workers)
- `start_worker.py` - Worker mode entry point

## Migration Reference

Statistics fields were added in Migration 021 (2025-10-19).

See migration files:
- `migrations/021_add_entity_statistics.sql` (if created)
- Database schema documentation

## Support

For issues or questions:
1. Check worker logs for error details
2. Verify API credentials and Supabase connection
3. Test with `--limit 10` to isolate issues
4. Review `scripts/test_statistics_endpoints.py` for calculation logic
