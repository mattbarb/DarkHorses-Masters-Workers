# Historical Data Collection Guide (2015-2025)

## Overview

This guide explains how to collect all available historical data from 2015 to the current date using your £299 premium add-on.

## Data Availability

### With Premium Add-On (£299)

| Data Type | Available From | Available To | Source |
|-----------|---------------|--------------|--------|
| **Results** | 2015-01-01 | Current Date | Racing API (Premium) |
| **Racecards** | 2023-01-23 | Current Date | Racing API (Pro Plan) |
| **Entities** | 2023-01-23 | Current Date | Extracted from Racecards |

### Key Limitations

- **Racecards** are only available from 2023-01-23 onwards (API limitation)
- **Results** for 2015-2022 will NOT have corresponding racecard data
- **Entities** (jockeys, trainers, owners, horses) are extracted from racecards, so only available from 2023+

## Quick Start

### 1. Run Full Historical Backfill

```bash
# Fetch ALL data from 2015 to present (results + racecards)
python3 initialize_data.py

# This will:
# - Fetch results from 2015-01-01 to present (~10 years, 165,000 results)
# - Fetch racecards from 2023-01-23 to present (~2.5 years, 45,000 races)
# - Extract entities (jockeys, trainers, owners, horses) from racecards
# - Take approximately 4-8 hours depending on API speed
```

### 2. Monitor Progress in Real-Time

```bash
# In a separate terminal, run the monitoring dashboard
python3 monitor_data_progress.py

# This displays:
# - Live table counts
# - Year-by-year breakdown (2015-2025)
# - Collection progress bars
# - Data quality indicators
# - Auto-refreshes every 2 seconds
```

### 3. Run Scheduled Updates (After Initial Backfill)

```bash
# Daily updates (tomorrow's races + yesterday's results)
python3 scripts/update_daily_data.py

# Live updates during racing hours
python3 scripts/update_live_data.py

# Monthly reference data
python3 scripts/update_reference_data.py
```

## Detailed Instructions

### Step 1: Initial Setup

1. **Verify environment variables** (`.env.local`):
   ```bash
   RACING_API_USERNAME=your_username
   RACING_API_PASSWORD=your_password
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_service_key
   ```

2. **Verify premium add-on is enabled**:
   ```bash
   # The initialization script defaults to premium=True
   # If needed, explicitly enable:
   python3 initialize_data.py --premium
   ```

### Step 2: Run Historical Backfill

#### Option A: Full Backfill (Recommended)

```bash
# Start from 2015-01-01 (default)
python3 initialize_data.py

# Logs will be written to logs/initialization_YYYYMMDD_HHMMSS.log
# Monitor progress in real-time using the monitoring dashboard
```

#### Option B: Partial Backfill

```bash
# Start from a specific date (e.g., 2020)
python3 initialize_data.py --from 2020-01-01

# Skip reference data if already populated
python3 initialize_data.py --skip-reference

# Test mode (last 7 days only)
python3 initialize_data.py --test
```

### Step 3: Monitor Progress

Open a **second terminal** and run:

```bash
python3 monitor_data_progress.py
```

**Dashboard Features:**
- **Overall Table Status**: Live counts for all tables
- **Year-by-Year Breakdown**: 2015-2025 data completeness
- **Progress Bars**: Visual progress for results and racecards
- **Data Quality**: Entity extraction rates
- **Recommendations**: Next steps based on current state

**Advanced Options:**
```bash
# Custom refresh interval (default: 2 seconds)
python3 monitor_data_progress.py --refresh 5

# Focus on a specific year
python3 monitor_data_progress.py --year 2023
```

## Expected Data Volumes

### Results Data (2015-2025 with Premium)

| Year | Expected Results | Status |
|------|-----------------|--------|
| 2015 | ~15,000 | Pending |
| 2016 | ~15,000 | Pending |
| 2017 | ~15,000 | Pending |
| 2018 | ~15,000 | Pending |
| 2019 | ~15,000 | Pending |
| 2020 | ~15,000 | Pending |
| 2021 | ~15,000 | Pending |
| 2022 | ~15,000 | Pending |
| 2023 | ~15,000 | Pending |
| 2024 | ~15,000 | Pending |
| 2025 | ~12,000 | Pending |
| **Total** | **~165,000** | **0% Complete** |

### Racecards Data (2023-2025 Only)

| Year | Expected Races | Expected Runners | Status |
|------|---------------|------------------|--------|
| 2023 | ~15,000 | ~150,000 | Pending |
| 2024 | ~15,000 | ~150,000 | Pending |
| 2025 | ~15,000 | ~150,000 | 0.8% Complete |
| **Total** | **~45,000** | **~450,000** | **0.8% Complete** |

### Entity Data (Extracted from Racecards)

| Entity | Expected Count | Current | Status |
|--------|---------------|---------|--------|
| Jockeys | ~500-1,000 | 494 | ✅ Good |
| Trainers | ~600-1,200 | 658 | ✅ Good |
| Owners | ~2,500-5,000 | 2,674 | ✅ Good |
| Horses | ~30,000-60,000 | 3,367 | 🔄 Growing |

## Execution Time Estimates

### Initial Backfill

- **Results (2015-2025)**: ~120 chunks × 2 minutes = **4 hours**
- **Racecards (2023-2025)**: ~30 chunks × 5 minutes = **2.5 hours**
- **Total**: **~6-8 hours** (with API rate limits)

### Breakdown by Phase

| Phase | Data Range | Chunks | Est. Time |
|-------|-----------|--------|-----------|
| Phase 1: Reference Data | N/A | N/A | 2 minutes |
| Phase 2A: Results (2015-2025) | 3,931 days | 120 chunks | 4 hours |
| Phase 2B: Racecards (2023-2025) | 1,018 days | 30 chunks | 2.5 hours |
| **Total** | - | 150 chunks | **~6-8 hours** |

## Troubleshooting

### Common Issues

#### 1. No Results for 2015-2022

**Symptom**: Results table shows 0 records for years before 2023

**Cause**: Initial backfill hasn't run yet, or it failed

**Solution**:
```bash
# Re-run initialization from 2015
python3 initialize_data.py --from 2015-01-01

# Check logs for errors
tail -f logs/initialization_*.log
```

#### 2. No Racecards Before 2023

**Symptom**: Races table shows 0 records for years before 2023

**Cause**: This is expected - racecards only available from 2023-01-23

**Solution**: This is an API limitation. Results for 2015-2022 will not have corresponding racecard data.

#### 3. Low Entity Extraction Rate

**Symptom**: Monitoring dashboard shows <80% entity extraction

**Cause**: Entity extraction may have failed during backfill

**Solution**:
```bash
# Re-run backfill for racecards (entities will be re-extracted)
python3 initialize_data.py --from 2023-01-23 --skip-reference
```

#### 4. Slow Progress / Timeouts

**Symptom**: Initialization taking longer than expected

**Cause**: API rate limiting (2 req/sec), network issues, or large data volumes

**Solution**:
- This is normal - be patient
- The process is idempotent (safe to re-run)
- Monitor logs for actual errors vs. rate limiting
- If process crashes, just re-run - it will pick up where it left off (idempotent)

#### 5. Process Interrupted

**Symptom**: Initialization stopped before completion

**Cause**: Network interruption, manual stop, or crash

**Solution**:
```bash
# Simply re-run the initialization
# The upsert logic will skip existing records and continue
python3 initialize_data.py

# Or start from where you think it stopped
python3 initialize_data.py --from 2018-01-01
```

## Data Quality Checks

After backfill completes, verify data quality:

```bash
# Check table counts
python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

tables = ['ra_results', 'ra_races', 'ra_runners', 'ra_horses', 'ra_jockeys', 'ra_trainers', 'ra_owners']
for table in tables:
    result = db.client.table(table).select('*', count='exact').limit(0).execute()
    print(f'{table}: {result.count:,} records')
"
```

**Expected Results (After Full Backfill):**
```
ra_results: ~165,000 records     (2015-2025)
ra_races: ~45,000 records        (2023-2025)
ra_runners: ~450,000 records     (2023-2025)
ra_horses: ~50,000 records       (2023-2025)
ra_jockeys: ~1,000 records       (2023-2025)
ra_trainers: ~1,000 records      (2023-2025)
ra_owners: ~5,000 records        (2023-2025)
```

## Storage Requirements

### Database Size Estimates

| Time Period | Results | Racecards | Runners | Entities | Total |
|-------------|---------|-----------|---------|----------|-------|
| 2015-2022 (Results Only) | ~800 MB | 0 MB | 0 MB | 0 MB | **~800 MB** |
| 2023-2025 (Full Data) | ~150 MB | ~200 MB | ~2 GB | ~50 MB | **~2.4 GB** |
| **Total** | **~950 MB** | **~200 MB** | **~2 GB** | **~50 MB** | **~3.2 GB** |

### Annual Growth Rate

- **Results**: ~100 MB/year
- **Racecards**: ~70 MB/year
- **Runners**: ~700 MB/year
- **Total**: ~870 MB/year

## API Usage During Backfill

### Total API Calls

- **Results (2015-2025)**: ~120 chunks × 2 calls = 240 calls
- **Racecards (2023-2025)**: ~1,020 days × 1 call = 1,020 calls
- **Reference Data**: ~5 calls
- **Total**: ~1,265 API calls

### Rate Limiting

- API limit: 2 requests/second
- Actual rate: ~1.5 requests/second (with safety margin)
- Total time: ~1,265 calls ÷ 1.5 req/s = **~14 minutes of API time**
- Actual time: **~6-8 hours** (including processing, database operations, rate limit pauses)

## Best Practices

### 1. Run During Off-Peak Hours

- Start backfill during evening/night
- Allows process to run uninterrupted
- Less network congestion

### 2. Monitor Progress

- Keep monitoring dashboard running
- Check for errors in logs periodically
- Verify data quality after each major milestone

### 3. Incremental Backfill

If full backfill seems too long, break it into chunks:

```bash
# Year by year
python3 initialize_data.py --from 2015-01-01 --to 2015-12-31
python3 initialize_data.py --from 2016-01-01 --to 2016-12-31
# ... etc
```

### 4. Regular Health Checks

After backfill, set up daily checks:

```bash
# Add to crontab
0 8 * * * python3 monitor_data_progress.py --year $(date +%Y) > /tmp/data_check.log
```

## Next Steps

After completing historical backfill:

1. **Set up automated updates**:
   ```bash
   # Deploy scheduled update scripts to Render.com
   # See docs/SCHEDULER_README.md
   ```

2. **Verify data quality**:
   ```bash
   python3 monitor_data_progress.py
   ```

3. **Start using the data**:
   - Build analytics queries
   - Train ML models
   - Create dashboards

## Support

### Documentation

- **Data Collection Plan**: `docs/DATA_COLLECTION_PLAN.md`
- **Update Scheduler**: `docs/UPDATE_SCHEDULER_DESIGN.md`
- **Scheduler README**: `docs/SCHEDULER_README.md`

### Logs

- **Initialization Logs**: `logs/initialization_*.log`
- **Daily Update Logs**: `logs/daily_update_*.log`
- **Live Update Logs**: `logs/live_update_*.log`

### Quick Commands

```bash
# Start backfill
python3 initialize_data.py

# Monitor progress
python3 monitor_data_progress.py

# Check current status
python3 -c "from monitor_data_progress import DataProgressMonitor; m = DataProgressMonitor(); m.display_dashboard()"

# View logs
tail -f logs/initialization_*.log
```

---

## Summary

- ✅ **With £299 premium add-on**, you can access results from 2015-2025
- ✅ **Racecards** only available from 2023-01-23 onwards (API limitation)
- ✅ **Initial backfill** takes ~6-8 hours for all available data
- ✅ **Real-time monitoring** dashboard tracks progress across all years
- ✅ **Process is idempotent** - safe to re-run anytime
- ✅ **Entity extraction** happens automatically from racecards

**Start now:**
```bash
python3 initialize_data.py
```

**Monitor:**
```bash
python3 monitor_data_progress.py
```
