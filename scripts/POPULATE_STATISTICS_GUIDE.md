# Populate All Statistics - Complete Guide

## Overview

`populate_all_statistics.py` is a comprehensive, production-ready script that populates statistics for jockeys, trainers, and owners in a unified process. It handles pagination, progress tracking, checkpoints, and error recovery.

**Location:** `/scripts/populate_all_statistics.py`

## Features

- **Unified Execution**: Single script handles all three entity types
- **Pagination Support**: Automatically handles Supabase's 1000-row limit
- **Real-time Progress Tracking**: Shows completion %, rate, and ETA
- **Resume Capability**: Can resume from where it left off if interrupted
- **Checkpoint Files**: Saves progress every 100 entities
- **Error Handling**: Comprehensive error handling with detailed logging
- **Skip Existing**: Option to only process entities without statistics
- **Dry Run Mode**: Preview what would be processed without executing
- **Detailed Reports**: Saves JSON report of each run

## Database Counts (as of October 2025)

- **Jockeys**: 3,483 total
- **Trainers**: 2,781 total
- **Owners**: 48,165 total
- **Total**: 54,429 entities

## Command-Line Options

### Entity Selection

```bash
--all                          # Process all three entity types
--entities jockeys trainers    # Process specific entity types only
```

### Processing Options

```bash
--limit N                      # Limit to N entities per type (testing)
--skip-existing               # Only process entities without statistics
--resume                      # Resume from checkpoint if interrupted
--dry-run                     # Show what would be processed (no execution)
--clear-checkpoints           # Clear all checkpoint files before starting
```

## Usage Examples

### 1. Process All Entity Types (Production)

```bash
python3 scripts/populate_all_statistics.py --all
```

**Estimated Time:**
- Jockeys (3,483): ~8-12 hours
- Trainers (2,781): ~6-10 hours
- Owners (48,165): ~130-170 hours (5-7 days)
- **Total: ~6-8 days continuous**

### 2. Process Only New Entities (Incremental Update)

```bash
python3 scripts/populate_all_statistics.py --all --skip-existing
```

Use this for daily/weekly updates after initial population.

**Estimated Time:** Depends on number of new entities (typically minutes to hours)

### 3. Process Specific Entity Types

```bash
# Just jockeys
python3 scripts/populate_all_statistics.py --entities jockeys

# Just trainers and owners
python3 scripts/populate_all_statistics.py --entities trainers owners
```

### 4. Resume Interrupted Processing

If processing was interrupted (network issue, system restart, etc.):

```bash
python3 scripts/populate_all_statistics.py --all --resume
```

The script will:
1. Load checkpoint files
2. Skip already-processed entities
3. Continue from where it left off

### 5. Dry Run (Preview Mode)

See what would be processed without actually doing it:

```bash
python3 scripts/populate_all_statistics.py --all --dry-run --limit 100
```

### 6. Testing with Limited Entities

Test the script with a small number of entities:

```bash
# Test with 10 jockeys
python3 scripts/populate_all_statistics.py --entities jockeys --limit 10

# Test all types with 5 each
python3 scripts/populate_all_statistics.py --all --limit 5
```

### 7. Clear Old Checkpoints and Start Fresh

```bash
python3 scripts/populate_all_statistics.py --all --clear-checkpoints
```

## Output and Logging

### Console Output

The script provides real-time progress updates:

```
Jockeys: 1234/3483 (35.4%) | Rate: 0.15/s | ETA: 250.0m | Success: 1230 | Failed: 4 | Skipped: 0
```

Where:
- **Progress**: Current/Total (Percentage)
- **Rate**: Entities processed per second
- **ETA**: Estimated time remaining in minutes
- **Success**: Successfully processed entities
- **Failed**: Entities that encountered errors
- **Skipped**: Entities skipped (in resume mode)

### Log Files

All output is logged with timestamps to console. Additional files created:

**Checkpoint Files** (`logs/checkpoint_{entity_type}.json`):
```json
{
  "entity_type": "jockeys",
  "processed_ids": ["jky_301080", "jky_311451", ...],
  "count": 1234,
  "timestamp": "2025-10-19T14:17:47.759849"
}
```

**Report Files** (`logs/statistics_population_report_{timestamp}.json`):
```json
{
  "timestamp": "2025-10-19T14:17:14.492810",
  "entity_types": ["jockeys", "trainers", "owners"],
  "mode": "production",
  "options": {
    "skip_existing": false,
    "resume": false,
    "limit": null
  },
  "statistics": {
    "jockeys": {
      "total": 3483,
      "processed": 3483,
      "successful": 3480,
      "failed": 3,
      "skipped": 0,
      "duration": 25434.23,
      "rate": 0.137
    }
  },
  "overall": {
    "total_entities": 54429,
    "total_processed": 54429,
    "total_successful": 54400,
    "total_failed": 29,
    "total_skipped": 0,
    "duration": 518400.0
  }
}
```

## Performance Characteristics

### Processing Rate

Based on API rate limits (2 requests/second) and typical result counts:

- **Average rate**: 0.10-0.20 entities/second
- **Factors affecting rate**:
  - Number of results per entity (more results = slower)
  - API response time
  - Network latency
  - Database update speed

### Memory Usage

- **Minimal**: ~50-100 MB
- Processes entities one at a time
- No large data structures held in memory

### API Rate Limiting

The script respects Racing API rate limits:
- 2 requests/second maximum
- Automatic retry with exponential backoff on rate limit errors
- Each entity requires 1-10+ API calls depending on result count

## Error Handling

### Automatic Retry

API errors (rate limits, timeouts) are automatically retried with exponential backoff:
- 1st retry: 5 seconds
- 2nd retry: 10 seconds
- 3rd retry: 20 seconds
- Maximum 5 retries

### Failed Entities

Entities that fail after all retries are:
- Counted in "failed" statistics
- Logged to console with error details
- **Not** added to checkpoint (can be reprocessed)

### Resume After Failure

If the script crashes or is interrupted:
1. Checkpoint files preserve progress
2. Use `--resume` to continue
3. Already-processed entities are skipped

## Recommended Workflow

### Initial Population (First Time)

```bash
# Step 1: Test with small sample
python3 scripts/populate_all_statistics.py --all --dry-run --limit 10

# Step 2: Process jockeys first (smallest dataset)
python3 scripts/populate_all_statistics.py --entities jockeys

# Step 3: Process trainers
python3 scripts/populate_all_statistics.py --entities trainers

# Step 4: Process owners (largest, run in background)
nohup python3 scripts/populate_all_statistics.py --entities owners > owners_stats.log 2>&1 &
```

### Daily/Weekly Updates

```bash
# Only process entities without statistics (new entities)
python3 scripts/populate_all_statistics.py --all --skip-existing
```

### Recovery from Interruption

```bash
# Resume from checkpoint
python3 scripts/populate_all_statistics.py --all --resume
```

## Monitoring Long-Running Jobs

### Run in Background

```bash
# Start in background
nohup python3 scripts/populate_all_statistics.py --all > stats_population.log 2>&1 &

# Save process ID
echo $! > stats_population.pid

# Monitor progress
tail -f stats_population.log

# Check if still running
ps -p $(cat stats_population.pid)
```

### Check Progress

Monitor checkpoint files to see progress:

```bash
# Count processed entities
jq '.count' logs/checkpoint_jockeys.json
jq '.count' logs/checkpoint_trainers.json
jq '.count' logs/checkpoint_owners.json
```

## Troubleshooting

### Script Runs But No Updates

**Problem**: Script completes but statistics not populated.

**Solutions**:
1. Check API credentials in `.env.local`
2. Verify Racing API plan has access to results endpoints
3. Check console logs for API errors

### Rate Limit Errors

**Problem**: Excessive rate limit warnings.

**Solutions**:
1. This is normal - script handles automatically
2. If persistent, check if other processes are using API
3. Verify API rate limit tier (should be 2/second)

### Out of Memory

**Problem**: Script crashes with memory error.

**Solutions**:
1. Shouldn't happen - each entity processed individually
2. If occurs, report as bug with details

### Checkpoint Not Working

**Problem**: Resume doesn't skip processed entities.

**Solutions**:
1. Check `logs/checkpoint_{type}.json` exists
2. Verify JSON is valid
3. Use `--clear-checkpoints` to start fresh

## Integration with Other Scripts

### Standalone Workers

Individual entity type workers can still be used:

```bash
python3 scripts/statistics_workers/jockeys_statistics_worker.py --limit 10
python3 scripts/statistics_workers/trainers_statistics_worker.py --limit 10
python3 scripts/statistics_workers/owners_statistics_worker.py --limit 10
```

### Run All Workers (Legacy)

The legacy runner script:

```bash
python3 scripts/statistics_workers/run_all_statistics_workers.py --limit 10
```

**Recommendation**: Use `populate_all_statistics.py` instead - it has more features.

## Statistics Populated

### Jockeys (ra_jockeys)

- `last_ride_date` - Date of most recent ride
- `last_win_date` - Date of most recent win
- `days_since_last_ride` - Days since last ride
- `days_since_last_win` - Days since last win
- `recent_14d_rides` - Rides in last 14 days
- `recent_14d_wins` - Wins in last 14 days
- `recent_14d_win_rate` - Win rate % in last 14 days
- `recent_30d_rides` - Rides in last 30 days
- `recent_30d_wins` - Wins in last 30 days
- `recent_30d_win_rate` - Win rate % in last 30 days
- `stats_updated_at` - Timestamp of statistics update

### Trainers (ra_trainers)

- `last_runner_date` - Date of most recent runner
- `last_win_date` - Date of most recent win
- `days_since_last_runner` - Days since last runner
- `days_since_last_win` - Days since last win
- `recent_14d_runs` - Runners in last 14 days
- `recent_14d_wins` - Wins in last 14 days
- `recent_14d_win_rate` - Win rate % in last 14 days
- `recent_30d_runs` - Runners in last 30 days
- `recent_30d_wins` - Wins in last 30 days
- `recent_30d_win_rate` - Win rate % in last 30 days
- `stats_updated_at` - Timestamp of statistics update

### Owners (ra_owners)

Same fields as trainers (uses "runners" not "rides").

## API Endpoints Used

The script uses these Racing API Pro endpoints:

- `/v1/jockeys/{id}/results` - Jockey results (last 365 days)
- `/v1/trainers/{id}/results` - Trainer results (last 365 days)
- `/v1/owners/{id}/results` - Owner results (last 365 days)

All filtered to UK (gb) and Ireland (ire) regions only.

## Best Practices

1. **Test First**: Always test with `--dry-run` and `--limit` before full run
2. **Start Small**: Process jockeys and trainers first, then owners
3. **Monitor Progress**: Check logs and checkpoint files regularly
4. **Use Background Jobs**: For owners (48K+ entities), run in background
5. **Regular Updates**: Use `--skip-existing` for daily/weekly updates
6. **Keep Checkpoints**: Don't delete checkpoint files during active processing

## Support

For issues or questions:
1. Check console logs for error messages
2. Review report JSON files in `logs/`
3. Verify API credentials and access
4. Test with small sample (`--limit 5`) to isolate issues

## Version History

- **v1.0** (2025-10-19): Initial production release
  - Unified script for all entity types
  - Pagination support
  - Checkpoint/resume capability
  - Progress tracking
  - Dry-run mode
  - Skip-existing option
