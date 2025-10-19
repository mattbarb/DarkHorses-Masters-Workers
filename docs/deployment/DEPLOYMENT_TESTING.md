# Deployment Testing Guide

This guide documents the comprehensive deployment test suite for the DarkHorses Masters Worker service deployed on Render.com.

## Overview

The deployment test suite verifies that the worker service is correctly configured, operational, and collecting data as expected. It consists of 5 specialized test modules plus a master orchestrator that runs all tests and generates a comprehensive report.

## Table of Contents

- [Test Files](#test-files)
- [Quick Start](#quick-start)
- [Test Modules](#test-modules)
- [Running Tests](#running-tests)
- [Expected Output](#expected-output)
- [Troubleshooting](#troubleshooting)
- [CI/CD Integration](#cicd-integration)

---

## Test Files

### Core Deployment Tests

| File | Purpose | Critical? |
|------|---------|-----------|
| `test_deployment.py` | Environment & connectivity verification | ✅ Yes |
| `test_schedule.py` | Scheduler configuration verification | ✅ Yes |
| `test_data_freshness.py` | Data age monitoring | ⚠️ Warning |
| `test_e2e_worker.py` | End-to-end pipeline test | ✅ Yes |
| `run_deployment_tests.py` | Master orchestrator | ✅ Yes |

### Worker Data Tests (Existing)

| File | Purpose | Critical? |
|------|---------|-----------|
| `test_courses_worker.py` | Courses data verification | ⚠️ Warning |
| `test_races_worker.py` | Races data verification | ⚠️ Warning |
| `test_people_horses_worker.py` | People/horses data verification | ⚠️ Warning |

---

## Quick Start

### Prerequisites

1. **Python 3.9+** installed
2. **Dependencies** installed: `pip install -r requirements.txt`
3. **Environment variables** configured (see below)

### Setup Environment

Create `.env.local` file in the project root:

```bash
cd /path/to/DarkHorses-Masters-Workers
cp .env.local.example .env.local
```

Edit `.env.local` with your credentials:

```bash
# Racing API Credentials
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password

# Supabase Credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

### Run All Tests

```bash
cd tests
python3 run_deployment_tests.py
```

This runs the complete deployment verification suite (~2-5 minutes).

---

## Test Modules

### 1. Deployment Verification (`test_deployment.py`)

**Purpose:** Verifies the deployment environment is correctly configured and all external services are accessible.

**Tests:**
1. ✅ Environment variables loaded
2. ✅ Configuration object initialized
3. ✅ Supabase connection working
4. ✅ Racing API connection working
5. ✅ All database tables exist
6. ✅ Regional filtering active (UK/Ireland only)

**Run individually:**
```bash
cd tests
python3 test_deployment.py
```

**Expected output:**
```
🚀 DEPLOYMENT VERIFICATION TEST
[TEST 1] Checking environment variables...
✅ PASS - All required environment variables set
[TEST 2] Checking configuration initialization...
✅ PASS - Configuration initialized successfully
...
🎉 DEPLOYMENT VERIFIED - All systems operational!
```

**What it checks:**
- `RACING_API_USERNAME` and `RACING_API_PASSWORD` are set
- `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` are set
- Configuration object can be created
- API authentication succeeds
- Database connection works
- All 8 tables exist: `racing_courses`, `racing_bookmakers`, `racing_jockeys`, `racing_trainers`, `racing_owners`, `racing_horses`, `racing_races`, `racing_results`
- Data filtering is UK/Ireland only

**Failure scenarios:**
- ❌ Missing environment variables → Check `.env.local`
- ❌ API connection failed → Check Racing API credentials
- ❌ Database connection failed → Check Supabase credentials
- ❌ Tables missing → Run database migrations

---

### 2. Schedule Verification (`test_schedule.py`)

**Purpose:** Verifies the scheduler is correctly configured and jobs are properly registered.

**Tests:**
1. ✅ Schedule module imports correctly
2. ✅ Jobs configured as expected
3. ✅ Schedule times are valid
4. ✅ Next run times calculated correctly
5. ✅ Scheduler can start/stop cleanly
6. ✅ Worker script exists and is executable

**Run individually:**
```bash
cd tests
python3 test_schedule.py
```

**Expected output:**
```
⏰ SCHEDULE VERIFICATION TEST
[TEST 1] Checking schedule module import...
✅ PASS - Schedule module imported successfully
[TEST 2] Checking schedule jobs configuration...
✅ PASS - Schedule jobs configured correctly
...
🎉 SCHEDULE VERIFIED - Scheduler configured correctly!
```

**What it checks:**
- Python `schedule` library is installed
- Jobs scheduled at correct times:
  - Daily: 01:00 UTC (races, results)
  - Weekly: Sunday 02:00 UTC (jockeys, trainers, owners, horses)
  - Monthly: First Monday 03:00 UTC (courses, bookmakers)
- `start_worker.py` exists
- Scheduler loop can start and stop

**Failure scenarios:**
- ❌ Schedule module missing → `pip install schedule`
- ❌ Jobs not configured → Check `start_worker.py`
- ❌ Worker script missing → Check repository structure

---

### 3. Data Freshness Monitoring (`test_data_freshness.py`)

**Purpose:** Monitors data age across all tables and alerts if data is stale.

**Tests:**
1. ✅ Monthly tables fresh (courses, bookmakers) - threshold: 35 days
2. ✅ Weekly tables fresh (jockeys, trainers, owners, horses) - threshold: 10 days
3. ✅ Daily tables fresh (races, results) - threshold: 3 days
4. ✅ Overall data health score
5. ⚠️ Stale data alerts generated

**Run individually:**
```bash
cd tests
python3 test_data_freshness.py
```

**Expected output:**
```
📊 DATA FRESHNESS MONITORING TEST
[TEST 1] Checking monthly tables freshness...
  ✓ racing_courses: 5 days old (threshold: 35 days)
  ✓ racing_bookmakers: 5 days old (threshold: 35 days)
✅ PASS - Monthly tables checked
...
💯 Health Score: 100.0%
🎉 DATA FRESHNESS OK - All data within acceptable thresholds!
```

**Freshness Thresholds:**

| Table | Schedule | Max Age | Purpose |
|-------|----------|---------|---------|
| `racing_courses` | Monthly | 35 days | Venue reference data |
| `racing_bookmakers` | Monthly | 35 days | Bookmaker list |
| `racing_jockeys` | Weekly | 10 days | Jockey profiles |
| `racing_trainers` | Weekly | 10 days | Trainer profiles |
| `racing_owners` | Weekly | 10 days | Owner profiles |
| `racing_horses` | Weekly | 10 days | Horse profiles |
| `racing_races` | Daily | 3 days | Race cards |
| `racing_results` | Daily | 3 days | Race results |

**What it checks:**
- Last update timestamp (`updated_at`) for each table
- Calculates age in days/hours
- Compares against schedule-specific thresholds
- Generates health score (fresh/warning/stale)
- Provides detailed freshness report

**Warning scenarios:**
- ⚠️ Data slightly stale → May be expected, monitor
- ⚠️ Health score < 75% → Check worker logs
- 🚨 Data very stale → Worker may not be running

**Recommended Actions (if stale):**
1. Check Render.com service logs
2. Verify worker is running (not free tier timeout)
3. Check Racing API rate limits
4. Verify database write permissions
5. Check scheduler execution times

---

### 4. End-to-End Pipeline Test (`test_e2e_worker.py`)

**Purpose:** Simulates a complete worker cycle to verify the full data pipeline works end-to-end.

**Tests:**
1. ✅ Configuration initializes
2. ✅ Fetcher initializes (API + DB clients)
3. ✅ API fetch succeeds
4. ✅ Database count before operation
5. ✅ Full fetch-and-store cycle
6. ✅ Database count after operation
7. ✅ Data quality validation
8. ✅ Error handling works

**Run individually:**
```bash
cd tests
python3 test_e2e_worker.py
```

**Expected output:**
```
🔄 END-TO-END WORKER TEST
[TEST 1] Testing configuration initialization...
✅ PASS - Configuration initialized
[TEST 2] Testing fetcher initialization...
✅ PASS - Fetcher initialized successfully
[TEST 3] Testing API data fetch...
✅ PASS - API fetch successful
  ✓ Courses fetched: 62
[TEST 5] Executing full fetch and store cycle...
✅ PASS - Fetch and store completed
  ✓ Fetched: 62 courses
  ✓ Inserted/Updated: 62 records
...
🎉 E2E TEST PASSED - Worker pipeline functioning correctly!
```

**Pipeline Stages Verified:**
```
Configuration → API Client → API Fetch → Transform → Database Upsert → Verify
```

**What it checks:**
- Config loads correctly
- `CoursesFetcher` can be instantiated
- Racing API responds with data
- Database queries work
- Upsert operation succeeds
- Records are inserted/updated
- Data quality is maintained (names, regions populated)
- Error handling doesn't crash

**Failure scenarios:**
- ❌ Configuration error → Check environment variables
- ❌ Fetcher init failed → Check imports
- ❌ API fetch failed → Check credentials, network
- ❌ Database error → Check Supabase connection
- ❌ Data quality issues → Check API response format

---

### 5. Master Test Runner (`run_deployment_tests.py`)

**Purpose:** Orchestrates all deployment tests and generates a comprehensive health report.

**Run:**
```bash
cd tests
python3 run_deployment_tests.py
```

**Test Phases:**

1. **Phase 1: Deployment Environment Verification** (Critical)
   - Runs `test_deployment.py`
   - Verifies environment, connectivity, database

2. **Phase 2: Scheduler Configuration Verification** (Critical)
   - Runs `test_schedule.py`
   - Verifies scheduler setup

3. **Phase 3: Data Freshness Monitoring** (Warning)
   - Runs `test_data_freshness.py`
   - Checks data age

4. **Phase 4: End-to-End Pipeline Test** (Critical)
   - Runs `test_e2e_worker.py`
   - Verifies full pipeline

5. **Phase 5: Worker Data Verification** (Warning)
   - Runs `test_courses_worker.py`
   - Runs `test_races_worker.py`
   - Runs `test_people_horses_worker.py`

**Expected Output:**

```
================================================================================
         DARKHORSES MASTERS WORKER - DEPLOYMENT VERIFICATION
================================================================================
                    Comprehensive deployment health check
                    Started: 2025-10-06 14:23:45
================================================================================

▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶
          PHASE 1: DEPLOYMENT ENVIRONMENT VERIFICATION
▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶▶

[... deployment tests run ...]

================================================================================
                    COMPREHENSIVE DEPLOYMENT REPORT
================================================================================

EXECUTIVE SUMMARY
================================================================================

🎯 Overall Status: ✅ OPERATIONAL
📊 Test Pass Rate: 98.5% (67/68)
⏱️  Total Duration: 45.23s (0.75 minutes)
🗓️  Completed: 2025-10-06 14:24:30

TEST PHASE RESULTS
================================================================================

📋 Deployment Environment: ✅ PASS
   Passed: 6, Failed: 0, Warnings: 0
📋 Scheduler Configuration: ✅ PASS
   Passed: 6, Failed: 0, Warnings: 0
📋 Data Freshness: ⚠️  WARNING
   Passed: 5, Failed: 0, Warnings: 1
📋 End-to-End Pipeline: ✅ PASS
   Passed: 8, Failed: 0, Warnings: 0
📋 Worker Data Verification: ✅ PASS
   ✓ Courses
   ✓ Races
   ✓ People Horses

SERVICE HEALTH DASHBOARD
================================================================================

● Environment Configuration    Healthy
● Scheduler Configuration      Healthy
● Data Freshness              Healthy
● Pipeline Integrity           Healthy
● Worker Data Quality          Healthy

RECOMMENDATIONS
================================================================================

✅ No issues detected - deployment is healthy
   • All systems operational
   • Continue monitoring with scheduled health checks
   • Review logs periodically for optimization opportunities

MONITORING INFORMATION
================================================================================

📍 Service: darkhorses-masters-worker on Render.com
📍 Region: UK/Ireland data only
📍 Update Schedules:
   • Daily (1:00 AM UTC): Races & Results
   • Weekly (Sunday 2:00 AM UTC): Jockeys, Trainers, Owners, Horses
   • Monthly (First Monday 3:00 AM UTC): Courses, Bookmakers

📍 Database Tables: 8 (racing_courses, racing_bookmakers, racing_jockeys,
                        racing_trainers, racing_owners, racing_horses,
                        racing_races, racing_results)

NEXT STEPS
================================================================================

1. Run this test suite daily to monitor deployment health
2. Set up automated alerts for critical failures
3. Review data freshness weekly
4. Monitor Render.com service logs for errors
5. Check Racing API usage and rate limits

================================================================================
```

**Exit Codes:**
- `0` = All critical tests passed (warnings are OK)
- `1` = Critical failures detected

**Report Sections:**

1. **Executive Summary** - Overall health status
2. **Test Phase Results** - Pass/fail for each phase
3. **Critical Failures** - Immediate issues requiring action
4. **Warnings** - Issues to monitor
5. **Service Health Dashboard** - Visual health indicators
6. **Recommendations** - Actionable next steps
7. **Monitoring Information** - Service details
8. **Next Steps** - What to do next

---

## Running Tests

### Individual Test Files

Run any test file individually:

```bash
cd tests

# Deployment verification
python3 test_deployment.py

# Schedule verification
python3 test_schedule.py

# Data freshness
python3 test_data_freshness.py

# End-to-end test
python3 test_e2e_worker.py

# Worker data tests
python3 test_courses_worker.py
python3 test_races_worker.py
python3 test_people_horses_worker.py
```

### Master Test Suite

Run all tests with comprehensive report:

```bash
cd tests
python3 run_deployment_tests.py
```

### Existing Test Runner

Run original worker tests only:

```bash
cd tests
python3 run_all_tests.py
```

---

## Expected Output

### Successful Test Run

```
✅ PASS - Test description
  ✓ Check 1
  ✓ Check 2
⏱️  Time: 0.45s
```

### Warning

```
⚠️  WARNING - Test description
  ⚠️  Issue detected but not critical
⏱️  Time: 0.32s
```

### Failure

```
❌ FAIL - Test description
  ✗ Check failed
  Error: Specific error message
⏱️  Time: 0.21s
```

### Timing Information

Each test reports execution time to help identify slow operations.

---

## Troubleshooting

### Common Issues

#### 1. Missing Environment Variables

**Error:**
```
❌ FAIL - Missing environment variables:
  ✗ RACING_API_USERNAME (Racing API username)
```

**Solution:**
- Create `.env.local` file: `cp .env.local.example .env.local`
- Add your credentials to `.env.local`

#### 2. API Connection Failed

**Error:**
```
❌ FAIL - Racing API connection failed: 401 Unauthorized
```

**Solution:**
- Verify Racing API credentials at https://theracingapi.com
- Check for typos in username/password
- Ensure API subscription is active

#### 3. Database Connection Failed

**Error:**
```
❌ FAIL - Supabase connection failed: Invalid API key
```

**Solution:**
- Check `SUPABASE_URL` format: `https://project.supabase.co`
- Verify `SUPABASE_SERVICE_KEY` (not anon key)
- Test connection in Supabase dashboard

#### 4. Tables Missing

**Error:**
```
❌ FAIL - Missing tables:
  ✗ racing_courses: relation does not exist
```

**Solution:**
- Run database migrations (check `sql/` directory)
- Verify database schema matches worker expectations
- Check table naming conventions

#### 5. Stale Data

**Warning:**
```
⚠️  WARNING - racing_races: 7 days old (threshold: 3 days)
```

**Solution:**
- Check Render.com service logs for errors
- Verify worker is running (not free tier timeout)
- Check scheduler execution times
- Verify Racing API rate limits not exceeded

#### 6. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'colorama'
```

**Solution:**
```bash
pip install -r requirements.txt
```

---

## CI/CD Integration

### GitHub Actions Example

Create `.github/workflows/deployment-tests.yml`:

```yaml
name: Deployment Tests

on:
  schedule:
    - cron: '0 2 * * *'  # Daily at 2 AM UTC
  workflow_dispatch:  # Manual trigger

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -r requirements.txt

    - name: Run deployment tests
      env:
        RACING_API_USERNAME: ${{ secrets.RACING_API_USERNAME }}
        RACING_API_PASSWORD: ${{ secrets.RACING_API_PASSWORD }}
        SUPABASE_URL: ${{ secrets.SUPABASE_URL }}
        SUPABASE_SERVICE_KEY: ${{ secrets.SUPABASE_SERVICE_KEY }}
      run: |
        cd tests
        python3 run_deployment_tests.py

    - name: Upload test results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: tests/*.log
```

### Render.com Health Checks

Add to `render.yaml`:

```yaml
services:
  - type: web
    name: darkhorses-masters-worker
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python3 start_worker.py"
    healthCheckPath: /health  # If you add a health endpoint
```

### Cron Job for Testing

Run tests daily via cron:

```bash
# Add to crontab
0 2 * * * cd /path/to/DarkHorses-Masters-Workers/tests && python3 run_deployment_tests.py >> /var/log/deployment-tests.log 2>&1
```

---

## Test Coverage Summary

### What's Tested

✅ Environment configuration
✅ API connectivity
✅ Database connectivity
✅ Scheduler configuration
✅ Data freshness
✅ Pipeline integrity
✅ Data quality
✅ Error handling
✅ Regional filtering
✅ Worker execution

### What's Not Tested

❌ Performance under load
❌ Concurrent worker execution
❌ Network resilience
❌ Rate limit handling
❌ Database transaction rollback

---

## Best Practices

1. **Run tests before deployment** - Catch issues early
2. **Monitor daily** - Set up automated runs
3. **Review warnings** - Don't ignore them
4. **Check logs** - Tests point to log files for details
5. **Test locally first** - Verify changes before deployment
6. **Document issues** - Keep track of recurring problems
7. **Update thresholds** - Adjust based on actual performance

---

## Additional Resources

- **Main README:** `../README.md`
- **Worker Documentation:** `../README_WORKER.md`
- **Deployment Guide:** `../RENDER_DEPLOYMENT.md`
- **Database Schema:** `../sql/`
- **Render.com Dashboard:** https://dashboard.render.com

---

## Support

For issues or questions:
1. Check test output for specific error messages
2. Review Render.com service logs
3. Check Racing API status page
4. Verify Supabase dashboard health
5. Review this documentation

---

**Last Updated:** 2025-10-06
**Version:** 1.0.0
**Maintainer:** DarkHorses Development Team
