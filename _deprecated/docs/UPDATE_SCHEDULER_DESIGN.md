# DarkHorses Masters Workers - Update Scheduler Design

## Overview

This document defines the design for the automated update scheduler that keeps the DarkHorses database current with racing data. The scheduler manages different update frequencies for different data types and ensures reliable, idempotent operation.

---

## Design Principles

### 1. Idempotency
- All update scripts must be safe to run multiple times
- Upsert logic prevents duplicate records
- Overlapping date ranges are handled gracefully
- Failed runs can be retried without side effects

### 2. Fault Tolerance
- Retry logic with exponential backoff
- Continue processing even if individual fetches fail
- Comprehensive logging for debugging
- Graceful degradation under API issues

### 3. Resource Efficiency
- Respect API rate limits (2 req/sec)
- Minimize unnecessary data fetching
- Batch database operations
- Optimize for cost on Render.com

### 4. Observability
- Detailed logging of all operations
- Statistics reporting on completion
- Health check endpoints
- Alert on anomalies

---

## Update Tiers

We implement a **four-tier update strategy** based on data volatility and business requirements:

### Tier 1: Live/Real-Time Updates
**Frequency:** Every 5-15 minutes during racing hours
**Data Types:** Current races, live odds (future), in-progress results
**Time Window:** 09:00-21:00 UTC on racing days
**Script:** `update_live_data.py`

### Tier 2: High-Frequency Updates
**Frequency:** Every 1-2 hours
**Data Types:** Race status updates, preliminary results
**Time Window:** 24/7
**Script:** `update_live_data.py --hourly`

### Tier 3: Daily Updates
**Frequency:** Once per day (06:00 UTC)
**Data Types:** Tomorrow's racecards, yesterday's results
**Time Window:** Early morning before racing starts
**Script:** `update_daily_data.py`

### Tier 4: Periodic Updates
**Frequency:** Weekly/Monthly
**Data Types:** Reference data (courses, bookmakers)
**Time Window:** Low-traffic periods
**Script:** `update_reference_data.py`

---

## Cron Schedule Expressions

### For Render.com Cron Jobs

Render.com uses standard cron syntax. Here are the recommended schedules:

#### Live Data Updates (Racing Hours)
```cron
# Every 15 minutes during racing hours (9 AM - 9 PM UTC)
*/15 9-20 * * * /usr/local/bin/python /opt/render/project/src/scripts/update_live_data.py
```

**Explanation:**
- `*/15`: Every 15 minutes
- `9-20`: Between 9:00 and 20:59 UTC (racing hours)
- `* * *`: Every day, every month, every day of week

**Alternative: Every 10 minutes (more frequent)**
```cron
*/10 9-20 * * * /usr/local/bin/python /opt/render/project/src/scripts/update_live_data.py
```

#### Daily Data Updates
```cron
# Once daily at 6:00 AM UTC (before racing starts)
0 6 * * * /usr/local/bin/python /opt/render/project/src/scripts/update_daily_data.py
```

**Explanation:**
- `0 6`: At 6:00 AM
- `* * *`: Every day, every month, every day of week

#### Weekly Reconciliation
```cron
# Sunday at 11:00 PM UTC (end of week reconciliation)
0 23 * * 0 /usr/local/bin/python /opt/render/project/src/scripts/update_daily_data.py --weekly
```

**Explanation:**
- `0 23`: At 11:00 PM
- `* *`: Every month, every day
- `0`: Sunday only (0=Sunday, 1=Monday, etc.)

#### Monthly Reference Data
```cron
# First day of each month at 3:00 AM UTC
0 3 1 * * /usr/local/bin/python /opt/render/project/src/scripts/update_reference_data.py
```

**Explanation:**
- `0 3`: At 3:00 AM
- `1`: On the 1st day of month
- `* *`: Every month, every day of week

---

## Script Specifications

### 1. update_live_data.py

**Purpose:** High-frequency updates during racing hours for time-sensitive data

**What It Updates:**
- Current day's race information (status, going, weather)
- Runner changes (withdrawals, jockey changes)
- Results as they become official

**Execution Pattern:**
- Runs every 15 minutes during 09:00-21:00 UTC
- Quick execution (< 1 minute)
- Minimal API calls (only today's data)

**Command-Line Options:**
```bash
python update_live_data.py                    # Full live update
python update_live_data.py --races-only       # Only update races
python update_live_data.py --results-only     # Only update results
python update_live_data.py --dry-run          # Test mode (no database writes)
```

**Logging:**
- Log file: `logs/live_update_YYYYMMDD.log`
- Level: INFO
- Rotation: Daily

**Success Metrics:**
- API calls made
- Races updated
- Runners updated
- Results captured
- Execution time

**Failure Handling:**
- Retry failed API calls up to 3 times
- Continue with other updates on partial failure
- Log errors but don't crash
- Exit code 0 for partial success, 1 for total failure

---

### 2. update_daily_data.py

**Purpose:** Daily batch updates for racecards and historical results

**What It Updates:**
- Tomorrow's racecards (races + runners)
- Day after tomorrow's racecards (optional, for lookahead)
- Yesterday's results (reconciliation)
- Entity extraction from new runners

**Execution Pattern:**
- Runs once daily at 06:00 UTC
- Moderate execution time (5-15 minutes)
- Moderate API calls (~20-50)

**Command-Line Options:**
```bash
python update_daily_data.py                      # Full daily update
python update_daily_data.py --racecards-only     # Only fetch tomorrow's racecards
python update_daily_data.py --results-only       # Only fetch yesterday's results
python update_daily_data.py --days-ahead 2       # Fetch racecards N days ahead
python update_daily_data.py --days-back 1        # Fetch results N days back
python update_daily_data.py --weekly             # Weekly reconciliation (last 7 days)
python update_daily_data.py --dry-run            # Test mode
```

**Logging:**
- Log file: `logs/daily_update_YYYYMMDD.log`
- Level: INFO
- Rotation: Keep 30 days

**Success Metrics:**
- Racecards fetched (by date)
- Races inserted/updated
- Runners inserted/updated
- Entities extracted (jockeys, trainers, owners, horses)
- Results fetched
- API calls made
- Execution time

**Failure Handling:**
- Retry API calls up to 5 times with exponential backoff
- Skip problematic dates and continue
- Send alert if > 50% of dates fail
- Exit code 0 if majority successful

---

### 3. update_reference_data.py

**Purpose:** Periodic updates for low-volatility reference data

**What It Updates:**
- Courses (new courses, updates to existing)
- Bookmakers (new bookmakers, status changes)

**Execution Pattern:**
- Runs monthly on 1st day at 03:00 UTC
- Quick execution (< 2 minutes)
- Minimal API calls (~2-5)

**Command-Line Options:**
```bash
python update_reference_data.py                  # Full reference update
python update_reference_data.py --courses-only   # Only courses
python update_reference_data.py --bookmakers-only # Only bookmakers
python update_reference_data.py --dry-run        # Test mode
```

**Logging:**
- Log file: `logs/reference_update_YYYYMMDD.log`
- Level: INFO
- Rotation: Keep 90 days

**Success Metrics:**
- Courses fetched/updated
- Bookmakers fetched/updated
- API calls made
- Execution time

**Failure Handling:**
- Retry up to 3 times
- Log errors
- Exit code 1 on failure (reference data is critical)

---

### 4. run_scheduled_updates.py

**Purpose:** Orchestration script that manages all scheduled updates

**Features:**
- Reads configuration from `config/scheduler_config.yaml`
- Determines which script to run based on time/schedule
- Manages concurrent executions (prevents overlaps)
- Centralized logging
- Health check monitoring

**Execution:**
```bash
python run_scheduled_updates.py               # Check schedule and run appropriate script
python run_scheduled_updates.py --force-all   # Force run all update types
python run_scheduled_updates.py --test        # Dry-run mode
```

**Concurrency Management:**
- Lock files prevent concurrent runs of same script
- Lock location: `/tmp/darkhorses_update_{script_name}.lock`
- Stale lock detection (> 1 hour = assume crashed, remove lock)
- Graceful skip if already running

**Logging:**
- Log file: `logs/scheduler_YYYYMMDD.log`
- Aggregates logs from all child scripts
- Level: INFO

---

## Configuration File: scheduler_config.yaml

**Location:** `/config/scheduler_config.yaml`

**Structure:**
```yaml
# Update intervals (in minutes or cron expressions)
intervals:
  live_data:
    enabled: true
    frequency: "*/15 9-20 * * *"  # Every 15 min during racing hours
    script: "scripts/update_live_data.py"
    timeout: 300  # 5 minutes max execution

  daily_data:
    enabled: true
    frequency: "0 6 * * *"  # Daily at 6 AM UTC
    script: "scripts/update_daily_data.py"
    timeout: 900  # 15 minutes max execution

  weekly_reconciliation:
    enabled: true
    frequency: "0 23 * * 0"  # Sunday at 11 PM UTC
    script: "scripts/update_daily_data.py"
    args: "--weekly"
    timeout: 1800  # 30 minutes max execution

  monthly_reference:
    enabled: true
    frequency: "0 3 1 * *"  # 1st of month at 3 AM UTC
    script: "scripts/update_reference_data.py"
    timeout: 300  # 5 minutes max execution

# Retry policies
retry:
  max_attempts: 5
  initial_delay: 5  # seconds
  max_delay: 300    # seconds
  backoff_factor: 2  # exponential backoff multiplier

# API rate limiting
api:
  rate_limit: 2.0  # requests per second
  burst_allowance: 5  # allow small bursts

# Alerting
alerts:
  enabled: true
  channels:
    - type: "log"  # Always log
    - type: "email"  # Optional: configure SMTP
      recipients:
        - "alerts@darkhorses.com"
    - type: "slack"  # Optional: configure webhook
      webhook_url: "${SLACK_WEBHOOK_URL}"

  thresholds:
    consecutive_failures: 3  # Alert after 3 consecutive failures
    api_error_rate: 0.1  # Alert if > 10% API calls fail
    stale_data_hours: 24  # Alert if no data fetched in 24 hours

# Logging
logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  rotation:
    max_bytes: 10485760  # 10 MB
    backup_count: 30  # Keep 30 days

# Health checks
health_check:
  enabled: true
  endpoint: "/health"  # If running as web service
  port: 8080
  checks:
    - name: "database_connection"
      type: "database"
      critical: true
    - name: "api_connectivity"
      type: "http"
      url: "https://api.theracingapi.com/health"
      critical: true
    - name: "data_freshness"
      type: "custom"
      script: "health_check.py"
      critical: false
```

---

## Error Handling & Retry Logic

### Retry Strategy: Exponential Backoff

```python
def retry_with_backoff(func, max_attempts=5, initial_delay=5, max_delay=300, backoff_factor=2):
    """
    Retry a function with exponential backoff

    Args:
        func: Function to retry
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        backoff_factor: Multiplier for each retry
    """
    attempt = 0
    delay = initial_delay

    while attempt < max_attempts:
        try:
            return func()
        except Exception as e:
            attempt += 1
            if attempt >= max_attempts:
                raise  # Re-raise on final attempt

            # Calculate next delay (exponential backoff with cap)
            delay = min(delay * backoff_factor, max_delay)
            logger.warning(f"Attempt {attempt} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)
```

### Error Categories

#### 1. Transient Errors (Retry)
- Network timeouts
- API rate limiting (429 status)
- Temporary API unavailability (500, 502, 503)
- Database connection issues

**Action:** Retry with exponential backoff

#### 2. Client Errors (Don't Retry)
- Invalid API credentials (401)
- Bad request parameters (400)
- Resource not found (404)

**Action:** Log error, skip, continue with next operation

#### 3. Data Errors (Skip & Log)
- Malformed API response
- Missing required fields
- Invalid data types

**Action:** Log detailed error, skip record, continue

#### 4. Critical Errors (Fail Fast)
- Database unavailable
- Configuration errors
- Permission issues

**Action:** Log error, alert, exit with error code

---

## Idempotent Design Patterns

### 1. Database Upserts
```python
# Supabase upsert pattern
supabase.table('ra_races').upsert(
    records,
    on_conflict='race_id',  # Primary key
    returning='minimal'
)
```

**Benefits:**
- Safe to re-run with same data
- Updates existing records
- Inserts new records
- No duplicates

### 2. Date Range Overlap
```python
# Safe to fetch overlapping date ranges
fetch_racecards(start_date='2025-10-05', end_date='2025-10-07')
fetch_racecards(start_date='2025-10-06', end_date='2025-10-08')
# Day 2025-10-06 is fetched twice, but upsert handles it
```

### 3. Graceful Re-runs
```python
# Check if already processed (optional optimization)
last_fetch = get_last_fetch_timestamp('races')
if datetime.now() - last_fetch < timedelta(hours=1):
    logger.info("Data already fresh, skipping")
    return
```

---

## Concurrency Management

### Lock File Pattern

```python
import fcntl
import os

class UpdateLock:
    """Context manager for update locks"""

    def __init__(self, script_name):
        self.lock_file = f"/tmp/darkhorses_update_{script_name}.lock"
        self.lock_fd = None

    def __enter__(self):
        self.lock_fd = open(self.lock_file, 'w')
        try:
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(str(os.getpid()))
            self.lock_fd.flush()
            return self
        except IOError:
            raise RuntimeError(f"Another instance of {script_name} is already running")

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.lock_fd:
            fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
            self.lock_fd.close()
            try:
                os.remove(self.lock_file)
            except:
                pass

# Usage
with UpdateLock('update_daily_data'):
    # Safe execution - won't run concurrently
    run_daily_update()
```

---

## Monitoring & Observability

### Metrics to Track

1. **Update Success Rate**
   - Percentage of successful updates per script
   - Target: > 99%

2. **API Health**
   - API calls made
   - API errors encountered
   - Rate limit hits
   - Average response time

3. **Data Freshness**
   - Last successful fetch timestamp per table
   - Age of oldest unfetched data
   - Gap detection (missing days)

4. **Performance**
   - Script execution time
   - Records processed per minute
   - Database write performance

### Health Check Endpoint

**If deployed as web service:**
```python
@app.route('/health')
def health_check():
    checks = {
        'database': check_database_connection(),
        'api': check_api_connectivity(),
        'data_freshness': check_data_freshness(),
        'last_update': get_last_update_timestamp()
    }

    all_healthy = all(check['status'] == 'ok' for check in checks.values())
    status_code = 200 if all_healthy else 503

    return jsonify(checks), status_code
```

### Alerting Rules

| Condition | Severity | Action |
|-----------|----------|--------|
| 3+ consecutive failures | CRITICAL | Email + Slack alert |
| No data fetched in 24h | CRITICAL | Email + Slack alert |
| API error rate > 10% | WARNING | Log alert |
| Slow execution (> 2x average) | WARNING | Log alert |
| Database connection issues | CRITICAL | Email + Slack alert |
| Stale lock file detected | WARNING | Auto-remove, log |

---

## Deployment on Render.com

### Cron Job Configuration

**render.yaml:**
```yaml
services:
  # Live data updates (every 15 min during racing hours)
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

  # Daily data updates
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

  # Weekly reconciliation
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

  # Monthly reference data
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

### Alternative: Single Orchestrator Cron Job

```yaml
services:
  # Main scheduler (checks schedule and runs appropriate script)
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

**Pros:** Single job, easier management
**Cons:** Less granular control, all-or-nothing execution

**Recommendation:** Use individual cron jobs for better control and easier debugging.

---

## Testing & Validation

### Dry-Run Mode

All scripts support `--dry-run` flag:
```bash
python update_daily_data.py --dry-run
```

**Behavior:**
- Fetch data from API (test API connectivity)
- Process and transform data
- Log what would be written
- **Do NOT write to database**
- Report statistics

### Local Testing

```bash
# Test daily update locally
python scripts/update_daily_data.py --dry-run

# Test with specific date range
python scripts/update_daily_data.py --days-back 7 --dry-run

# Test reference data
python scripts/update_reference_data.py --dry-run
```

### Validation Checks

After each update, run:
```bash
python data_quality_check.py
```

**Checks:**
- Record counts per table
- Missing foreign keys
- Orphaned records
- Duplicate detection
- Data anomalies

---

## Rollback & Recovery

### Scenario 1: Bad Data Fetched

**Detection:**
- Data quality check fails
- Anomaly detection (e.g., zero races on a racing day)

**Recovery:**
```bash
# Identify bad data by timestamp
SELECT * FROM ra_races WHERE updated_at > '2025-10-06T10:00:00';

# Delete bad records
DELETE FROM ra_races WHERE updated_at > '2025-10-06T10:00:00';

# Re-fetch correct data
python update_daily_data.py --date 2025-10-06
```

### Scenario 2: Script Crashes Mid-Execution

**Detection:**
- Incomplete logs
- Lock file left behind

**Recovery:**
```bash
# Remove stale lock
rm /tmp/darkhorses_update_*.lock

# Re-run script (idempotent design handles partial data)
python update_daily_data.py
```

### Scenario 3: Database Connection Lost

**Detection:**
- Database errors in logs
- Health check fails

**Recovery:**
- Wait for database to recover (auto-retry handles this)
- If database issue persists, check Supabase status
- Re-run script once database is available

---

## Performance Optimization

### 1. Batch Database Writes
```python
# Bad: Individual inserts
for race in races:
    db.insert(race)

# Good: Batch upsert
db.upsert_batch(races, batch_size=100)
```

### 2. Minimize API Calls
```python
# Fetch date ranges instead of individual days
fetch_racecards(start_date='2025-10-01', end_date='2025-10-07')
# vs.
for day in range(7):
    fetch_racecards(date=day)  # 7 separate API calls
```

### 3. Parallel Processing (Careful!)
```python
# Only parallelize independent operations
# BE CAREFUL: Don't exceed API rate limit
from concurrent.futures import ThreadPoolExecutor

with ThreadPoolExecutor(max_workers=2) as executor:
    future_races = executor.submit(fetch_races, date)
    future_results = executor.submit(fetch_results, date)

    races = future_races.result()
    results = future_results.result()
```

### 4. Caching
```python
# Cache reference data (courses, bookmakers) in memory
# Reload only when reference data is updated
```

---

## Summary of Design Decisions

1. **Four-tier update strategy** balances freshness vs. cost
2. **Idempotent scripts** allow safe re-runs and retries
3. **Lock files** prevent concurrent executions
4. **Exponential backoff** handles transient errors gracefully
5. **Comprehensive logging** enables debugging and monitoring
6. **Dry-run mode** allows safe testing
7. **Configurable via YAML** for easy adjustment
8. **Render.com cron jobs** for serverless execution
9. **Health checks** for proactive monitoring
10. **Alert thresholds** for critical issues

---

**Document Version:** 1.0
**Last Updated:** 2025-10-06
**Author:** DarkHorses Development Team
