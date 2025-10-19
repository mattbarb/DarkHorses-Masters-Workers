# DarkHorses Masters Workers - Scheduler System

## Quick Start Guide

This guide helps you deploy and manage the automated data collection scheduler for the DarkHorses racing database.

---

## Overview

The scheduler system consists of:

1. **Documentation**
   - `DATA_COLLECTION_PLAN.md` - Comprehensive data strategy and API limitations
   - `UPDATE_SCHEDULER_DESIGN.md` - Technical design and architecture
   - This file - Quick start and deployment guide

2. **Configuration**
   - `config/scheduler_config.yaml` - Centralized scheduler configuration

3. **Update Scripts**
   - `scripts/update_live_data.py` - High-frequency updates (every 15 min)
   - `scripts/update_daily_data.py` - Daily racecards and results
   - `scripts/update_reference_data.py` - Monthly reference data

4. **Orchestrator**
   - `run_scheduled_updates.py` - Main scheduler orchestrator

---

## Initial Setup

### 1. Install Dependencies

Ensure PyYAML is installed (already in requirements.txt):

```bash
pip install pyyaml
```

### 2. Run Initial Data Backfill

Before starting scheduled updates, populate the database with historical data:

```bash
# Full backfill from 2023-01-23 (earliest available)
python initialize_data.py

# OR: Quick 12-month backfill
python initialize_12months.py
```

This one-time process takes 2-4 hours for full backfill or 30-60 minutes for 12 months.

### 3. Verify Data Quality

After initialization, check data quality:

```bash
python data_quality_check.py
```

---

## Testing the Scheduler

Before deploying to production, test locally:

### Test Individual Update Scripts

```bash
# Test live data update (dry-run)
python scripts/update_live_data.py --dry-run

# Test daily update (dry-run)
python scripts/update_daily_data.py --dry-run

# Test reference data update (dry-run)
python scripts/update_reference_data.py --dry-run
```

### Test Orchestrator

```bash
# Test orchestrator (dry-run)
python run_scheduled_updates.py --test

# Force run all updates in test mode
python run_scheduled_updates.py --force-all --test

# Run specific update in test mode
python run_scheduled_updates.py --update daily_data --test
```

---

## Deployment on Render.com

### Option 1: Individual Cron Jobs (Recommended)

Create separate cron jobs for each update type in your `render.yaml`:

```yaml
services:
  # Live updates (every 15 minutes during racing hours)
  - type: cron
    name: darkhorses-live-updates
    env: docker
    schedule: "*/15 9-20 * * *"
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/update_live_data.py
    envVars:
      - key: RACING_API_USERNAME
        sync: false
      - key: RACING_API_PASSWORD
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false

  # Daily updates (6 AM UTC)
  - type: cron
    name: darkhorses-daily-updates
    env: docker
    schedule: "0 6 * * *"
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/update_daily_data.py
    envVars:
      - key: RACING_API_USERNAME
        sync: false
      - key: RACING_API_PASSWORD
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false

  # Weekly reconciliation (Sunday 11 PM UTC)
  - type: cron
    name: darkhorses-weekly-reconciliation
    env: docker
    schedule: "0 23 * * 0"
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/update_daily_data.py --weekly
    envVars:
      - key: RACING_API_USERNAME
        sync: false
      - key: RACING_API_PASSWORD
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false

  # Monthly reference data (1st of month, 3 AM UTC)
  - type: cron
    name: darkhorses-monthly-reference
    env: docker
    schedule: "0 3 1 * *"
    buildCommand: pip install -r requirements.txt
    startCommand: python scripts/update_reference_data.py
    envVars:
      - key: RACING_API_USERNAME
        sync: false
      - key: RACING_API_PASSWORD
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
```

### Option 2: Single Orchestrator Job

Alternatively, use a single orchestrator that checks schedules:

```yaml
services:
  - type: cron
    name: darkhorses-scheduler
    env: docker
    schedule: "*/10 * * * *"  # Every 10 minutes
    buildCommand: pip install -r requirements.txt
    startCommand: python run_scheduled_updates.py
    envVars:
      - key: RACING_API_USERNAME
        sync: false
      - key: RACING_API_PASSWORD
        sync: false
      - key: SUPABASE_URL
        sync: false
      - key: SUPABASE_SERVICE_KEY
        sync: false
```

**Recommendation:** Use Option 1 (individual jobs) for better control and easier debugging.

---

## Recommended Cron Schedules

| Update Type | Schedule | Cron Expression | Description |
|-------------|----------|----------------|-------------|
| **Live Data** | Every 15 min (9 AM - 9 PM UTC) | `*/15 9-20 * * *` | Race updates during racing hours |
| **Daily Data** | Daily at 6 AM UTC | `0 6 * * *` | Tomorrow's racecards + yesterday's results |
| **Weekly Reconciliation** | Sunday 11 PM UTC | `0 23 * * 0` | Catch missed data from past week |
| **Monthly Reference** | 1st of month, 3 AM UTC | `0 3 1 * *` | Courses and bookmakers refresh |

### Alternative: More Frequent Live Updates

For more real-time data, increase live update frequency:

```cron
# Every 10 minutes during racing hours
*/10 9-20 * * *

# Every 5 minutes during racing hours (higher cost)
*/5 9-20 * * *
```

**Note:** More frequent updates = more API calls = higher costs. Balance frequency with budget.

---

## Manual Execution

### Run Updates Manually

```bash
# Live data update
python scripts/update_live_data.py

# Daily update
python scripts/update_daily_data.py

# Reference data update
python scripts/update_reference_data.py

# Force run all via orchestrator
python run_scheduled_updates.py --force-all
```

### Run with Custom Parameters

```bash
# Daily update: fetch 3 days ahead
python scripts/update_daily_data.py --days-ahead 3

# Daily update: only fetch racecards
python scripts/update_daily_data.py --racecards-only

# Daily update: only fetch results
python scripts/update_daily_data.py --results-only

# Daily update: last 7 days (reconciliation)
python scripts/update_daily_data.py --days-back 7

# Live update: races only
python scripts/update_live_data.py --races-only

# Live update: results only
python scripts/update_live_data.py --results-only
```

---

## Monitoring & Logs

### View Logs

Logs are stored in the `/logs` directory:

```bash
# View today's live update log
tail -f logs/live_update_20251006.log

# View today's daily update log
tail -f logs/daily_update_20251006.log

# View orchestrator log
tail -f logs/scheduler_20251006.log
```

### Check Health

```bash
# Run health check
python health_check.py

# Run data quality check
python data_quality_check.py
```

### Monitor on Render.com

1. Navigate to your Render.com dashboard
2. Select the cron job
3. Click "Logs" tab
4. View real-time execution logs

---

## Troubleshooting

### Common Issues

#### 1. Lock File Errors

**Error:** `Another instance is already running`

**Cause:** Previous run didn't clean up lock file

**Solution:**
```bash
# Remove stale locks
rm /tmp/darkhorses_update_*.lock

# Re-run script
python scripts/update_daily_data.py
```

#### 2. API Authentication Errors

**Error:** `Authentication failed - check API credentials`

**Cause:** Invalid or expired API credentials

**Solution:**
- Verify `RACING_API_USERNAME` and `RACING_API_PASSWORD` environment variables
- Check credentials at https://theracingapi.com
- Ensure credentials are set in Render.com environment variables

#### 3. Database Connection Errors

**Error:** `Database connection failed`

**Cause:** Invalid Supabase credentials or database down

**Solution:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check Supabase project status
- Verify network connectivity

#### 4. No Data Fetched

**Error:** `No racecards/results returned`

**Possible Causes:**
- No races scheduled for the date
- API issue or maintenance
- Regional filtering (only GB/IRE races)

**Solution:**
- Check if races were actually scheduled for that date
- Verify API status at https://theracingapi.com
- Check logs for detailed error messages

#### 5. Rate Limit Errors

**Error:** `Rate limited, waiting 5s before retry`

**Cause:** Exceeding API rate limit (2 req/sec)

**Solution:**
- This is normal - the script handles it automatically
- If persistent, reduce update frequency
- Check for multiple concurrent script runs

---

## Performance Tuning

### Reduce API Calls

```bash
# Fetch fewer days ahead
python scripts/update_daily_data.py --days-ahead 1

# Skip entity extraction (faster but incomplete)
# Edit scheduler_config.yaml:
# features:
#   skip_entity_extraction: true
```

### Optimize Execution Time

1. **Batch Database Writes**
   - Default batch size: 100 records
   - Increase in `config/scheduler_config.yaml` if needed

2. **Reduce Retry Attempts**
   - Default: 5 attempts
   - Reduce in `config/scheduler_config.yaml` for faster failures

3. **Parallel Processing** (Use with caution!)
   - Disabled by default (API rate limit is strict)
   - Only enable if you have higher API tier

---

## Configuration Reference

### scheduler_config.yaml

Key configuration options:

```yaml
# Update intervals
intervals:
  live_data:
    enabled: true
    frequency: "*/15 9-20 * * *"
    timeout: 300  # 5 minutes

# Retry policies
retry:
  max_attempts: 5
  initial_delay: 5
  backoff_factor: 2

# API rate limiting
api:
  rate_limit: 2.0  # requests/sec
  timeout: 30

# Database settings
database:
  batch_size: 100
  query_timeout: 300

# Alerting
alerts:
  enabled: true
  thresholds:
    consecutive_failures: 3
    stale_data_hours: 24
```

### Environment Variables

Required:
- `RACING_API_USERNAME` - Racing API username
- `RACING_API_PASSWORD` - Racing API password
- `SUPABASE_URL` - Supabase project URL
- `SUPABASE_SERVICE_KEY` - Supabase service role key

Optional:
- `LOG_LEVEL` - Logging level (DEBUG, INFO, WARNING, ERROR)
- `DARKHORSES_LOGGING_LEVEL` - Override scheduler log level
- `DARKHORSES_API_RATE_LIMIT` - Override API rate limit
- `DARKHORSES_FEATURES_DRY_RUN` - Enable dry-run mode globally

---

## Maintenance

### Weekly Tasks

- Review logs for errors
- Check data freshness (health_check.py)
- Verify API usage (logs show API call counts)

### Monthly Tasks

- Run data quality check (data_quality_check.py)
- Review database size and growth
- Update scheduler configuration if needed
- Check for Racing API updates or changes

### Quarterly Tasks

- Evaluate pre-2023 data requirements
- Consider premium API add-on for historical data
- Optimize queries and add database indexes
- Review and tune update frequencies

---

## Cost Estimation

### API Calls Per Day

| Update Type | Frequency | Calls/Execution | Daily Calls |
|-------------|-----------|----------------|-------------|
| Live (15 min) | 48x/day | ~2 calls | 96 |
| Daily | 1x/day | ~5-10 calls | 10 |
| Weekly | 0.14x/day | ~15 calls | 2 |
| Monthly | 0.03x/day | ~2 calls | 0.1 |
| **TOTAL** | - | - | **~108/day** |

### Monthly Costs

- **API Calls:** ~3,240/month (well within most plans)
- **Render.com Cron Jobs:** $0-5/month (depends on execution time)
- **Database Storage:** Minimal (<100 MB/month growth)

**Total Monthly Cost:** $5-15 (excluding API subscription)

---

## Next Steps

### Immediate (Today)
1. Test scripts locally with `--dry-run`
2. Run initial backfill if not done
3. Deploy to Render.com with test schedule

### This Week
1. Monitor initial runs
2. Verify data quality
3. Tune update frequencies based on needs
4. Set up alerting (email/Slack)

### This Month
1. Optimize based on actual usage patterns
2. Implement monitoring dashboard (optional)
3. Evaluate need for more frequent updates
4. Consider pre-2023 historical data options

### Long-term
1. Add machine learning features using collected data
2. Implement odds tracking (requires additional API endpoints)
3. Build analytics dashboards
4. Scale to additional regions if needed

---

## Support & Resources

### Documentation
- `/docs/DATA_COLLECTION_PLAN.md` - Data strategy and limitations
- `/docs/UPDATE_SCHEDULER_DESIGN.md` - Technical design details
- `README.md` - Main project README
- `RENDER_DEPLOYMENT.md` - Render.com deployment guide

### API Documentation
- Racing API: https://theracingapi.com/documentation

### Contact
- Issues: GitHub Issues
- Questions: [Your support channel]

---

## Appendix: Script Reference

### update_live_data.py

**Purpose:** High-frequency updates during racing hours

**Options:**
- `--races-only` - Only update races
- `--results-only` - Only update results
- `--dry-run` - Test mode (no DB writes)

**Example:**
```bash
python scripts/update_live_data.py --dry-run
```

### update_daily_data.py

**Purpose:** Daily racecards and results updates

**Options:**
- `--racecards-only` - Only fetch racecards
- `--results-only` - Only fetch results
- `--days-ahead N` - Fetch N days of future racecards (default: 2)
- `--days-back N` - Fetch N days of past results (default: 1)
- `--weekly` - Weekly reconciliation (7 days back)
- `--dry-run` - Test mode

**Example:**
```bash
python scripts/update_daily_data.py --days-ahead 3 --dry-run
```

### update_reference_data.py

**Purpose:** Monthly reference data refresh

**Options:**
- `--courses-only` - Only update courses
- `--bookmakers-only` - Only update bookmakers
- `--dry-run` - Test mode

**Example:**
```bash
python scripts/update_reference_data.py --dry-run
```

### run_scheduled_updates.py

**Purpose:** Orchestrate all scheduled updates

**Options:**
- `--force-all` - Run all updates now
- `--update NAME` - Run specific update only
- `--config PATH` - Custom config file path
- `--test` - Dry-run mode

**Example:**
```bash
python run_scheduled_updates.py --update daily_data --test
```

---

**Document Version:** 1.0
**Last Updated:** 2025-10-06
**Author:** DarkHorses Development Team
