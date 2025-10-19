# DarkHorses Masters Worker - Complete Guide

**Quick Start | Data Collection | Monitoring | Maintenance**

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Data Collection Strategy](#data-collection-strategy)
4. [Monitoring Progress](#monitoring-progress)
5. [Scheduled Updates](#scheduled-updates)
6. [Troubleshooting](#troubleshooting)
7. [API Reference](#api-reference)

---

## Overview

### What This Does

Collects and maintains a complete UK & Irish horse racing database from 2015 to present, including:
- **Results**: Race outcomes from 2015-2025 (~165,000 races)
- **Racecards**: Race details from 2023-2025 (~45,000 races)
- **Entities**: Horses, jockeys, trainers, owners (automatically extracted)
- **Reference Data**: Courses and bookmakers

### Prerequisites

- Python 3.9+
- Racing API Pro Plan with £299 premium add-on (30+ years of results)
- Supabase account with database configured
- Environment variables configured in `.env.local`

### Environment Setup

```bash
# .env.local
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_service_key
```

---

## Quick Start

### First Time Setup (Clean Database)

**1. Navigate to project directory:**
```bash
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers
```

**2. Preview database state:**
```bash
python3 management/cleanup_and_reset.py
```

**3. Clean database (if needed):**
```bash
# This will delete ALL existing data
python3 management/cleanup_and_reset.py --confirm
# Type 'DELETE' when prompted
```

**4. Start data collection:**
```bash
# This runs in the background and takes 11-16 hours
nohup python3 scripts/initialize_data.py > logs/initialization_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

**5. Monitor progress (in a new terminal):**
```bash
python3 monitors/monitor_data_progress.py
```

That's it! The process will run for 11-16 hours and collect all data from 2015 to present.

---

## Data Collection Strategy

### What Data is Available

| Data Type | Date Range | Source | Count |
|-----------|-----------|--------|-------|
| **Results** | 2015-01-01 to present | Racing API (Premium) | ~165,000 |
| **Racecards** | 2023-01-23 to present | Racing API (Pro) | ~45,000 |
| **Entities** | Extracted from above | Auto-extracted | ~80,000+ |
| **Courses** | Current | Racing API | ~150 |
| **Bookmakers** | Static | Racing API | ~50 |

### Data Collection Phases

**Phase 1: Reference Data (2 minutes)**
- Fetches courses and bookmakers
- Static data that rarely changes

**Phase 2A: Historical Results (4-6 hours)**
- Fetches results from 2015-2025
- Processes in 44 chunks of ~90 days each
- Extracts entities (horses, jockeys, trainers, owners) from results

**Phase 2B: Historical Racecards (2-4 hours)**
- Fetches racecards from 2023-2025
- Processes in 11 chunks of ~90 days each
- Extracts additional entity data from racecards

**Total Time: 11-16 hours**

### Database Tables

All tables use the `ra_` prefix:

```
ra_courses         ~150 records     ✅ Reference data
ra_bookmakers       ~50 records     ✅ Reference data
ra_results       ~55,000 records    📊 2015-2025 results
ra_races         ~15,000 records    📊 2023-2025 racecards
ra_runners      ~600,000 records    📊 2023-2025 runners
ra_horses        ~80,000 records    👤 Extracted entities
ra_jockeys        ~3,000 records    👤 Extracted entities
ra_trainers       ~2,500 records    👤 Extracted entities
ra_owners        ~25,000 records    👤 Extracted entities
────────────────────────────────────────────────
TOTAL:          ~781,700 records    ✅
```

---

## Monitoring Progress

### Option 1: Year-by-Year Progress Bars (Recommended)

```bash
python3 monitors/monitor_progress_bars.py
```

**Features:**
- 📊 Clean progress bars for each year (2015-2025)
- 📈 Percentage completion for each year
- 🎯 Overall progress summary
- 🔄 Auto-refreshes every 5 seconds
- ✨ Simple, easy-to-read format
- Press Ctrl+C to exit (won't stop data collection)

### Option 2: Comprehensive Dashboard

```bash
python3 monitors/monitor_data_progress.py
```

**Features:**
- Live table counts across all 9 tables
- Year-by-year breakdown (2015-2025)
- Data quality indicators
- Entity extraction rates
- Detailed recommendations
- Auto-refreshes every 2 seconds
- Press Ctrl+C to exit (won't stop data collection)

### Check Logs

```bash
# View latest initialization log
tail -f logs/initialization_$(ls -t logs/initialization_*.log | head -1 | xargs basename)

# View specific fetcher logs
tail -f logs/results_fetcher_*.log
tail -f logs/races_fetcher_*.log

# Check for errors
grep -i error logs/initialization_*.log
```

### Check Process Status

```bash
# Check if initialization is running
ps aux | grep initialize_data.py

# Kill process if needed (will resume from where it stopped)
pkill -f initialize_data.py
```

---

## Scheduled Updates

### After Initial Backfill

Once the initial 11-16 hour collection is complete, set up automated updates:

**Daily Updates (Tomorrow's races + Yesterday's results):**
```bash
python3 scripts/update_daily_data.py
```

**Live Updates (During racing hours):**
```bash
python3 scripts/update_live_data.py
```

**Monthly Reference Data:**
```bash
python3 scripts/update_reference_data.py
```

### Deployment on Render.com

See `RENDER_DEPLOYMENT.md` for instructions on deploying scheduled updates as background workers.

---

## Troubleshooting

### Common Issues

#### 1. Process Stopped Early

**Symptoms:** Initialization stopped before completing all 44 chunks

**Solution:**
```bash
# Simply re-run - it's idempotent (won't duplicate data)
nohup python3 scripts/initialize_data.py > logs/initialization_$(date +%Y%m%d_%H%M%S).log 2>&1 &
```

#### 2. No Data Appearing in Tables

**Symptoms:** Monitor shows 0 records after 30+ minutes

**Solution:**
```bash
# Check logs for errors
tail -100 logs/initialization_*.log | grep -i error

# Check API credentials
python3 monitors/health_check.py
```

#### 3. Rate Limiting Warnings

**Symptoms:** Logs show "Rate limited, waiting 5s before retry"

**This is normal!** The API limit is 2 requests/second. The script automatically handles rate limiting with exponential backoff.

#### 4. Missing race_id Warnings

**Symptoms:** Logs show "Result missing race ID, skipping"

**This is expected** for older historical data. Some results from 2015-2022 may not have race IDs. This doesn't affect data quality.

#### 5. Database Connection Issues

**Symptoms:** "Failed to connect to Supabase"

**Solution:**
```bash
# Verify environment variables
cat .env.local

# Test connection
python3 -c "from config.config import get_config; print(get_config().supabase.url)"
```

### Data Quality Checks

After collection completes:

```bash
# Run data quality check
python3 monitors/data_quality_check.py

# Check for missing years
python3 monitors/monitor_data_progress.py
```

---

## API Reference

### Key Scripts

| Script | Purpose | Usage |
|--------|---------|-------|
| `initialize_data.py` | Initial data backfill (2015-2025) | `python3 scripts/initialize_data.py` |
| `monitor_data_progress.py` | Real-time monitoring dashboard | `python3 monitors/monitor_data_progress.py` |
| `cleanup_and_reset.py` | Clean database for fresh start | `python3 management/cleanup_and_reset.py --confirm` |
| `health_check.py` | Verify system health | `python3 monitors/health_check.py` |
| `data_quality_check.py` | Validate data quality | `python3 monitors/data_quality_check.py` |
| `start_worker.py` | Start background worker | `python3 start_worker.py` |

### Command-Line Options

**initialize_data.py:**
```bash
python3 scripts/initialize_data.py                     # Full initialization (2015-2025)
python3 scripts/initialize_data.py --from 2020-01-01   # Start from specific date
python3 scripts/initialize_data.py --skip-reference    # Skip courses/bookmakers
python3 scripts/initialize_data.py --test              # Test mode (last 7 days only)
```

**cleanup_and_reset.py:**
```bash
python3 management/cleanup_and_reset.py                   # Dry run (preview)
python3 management/cleanup_and_reset.py --confirm         # Actually delete data
python3 management/cleanup_and_reset.py --confirm --tables ra_races ra_results  # Specific tables only
```

**monitor_data_progress.py:**
```bash
python3 monitors/monitor_data_progress.py               # Default (refresh every 2s)
python3 monitors/monitor_data_progress.py --refresh 5   # Refresh every 5s
python3 monitors/monitor_data_progress.py --year 2023   # Focus on specific year
```

### Data Collection Limits

**API Limits:**
- Rate limit: 2 requests/second
- Results: 30+ years with premium add-on
- Racecards: From 2023-01-23 onwards (API limitation)

**Processing Time:**
- Reference data: ~2 minutes
- Results (2015-2025): ~4-6 hours
- Racecards (2023-2025): ~2-4 hours
- **Total: 11-16 hours**

**Storage Requirements:**
- Initial data: ~3.2 GB
- Annual growth: ~870 MB/year

---

## Expected Results

### After Full Backfill Completes

```
✅ ra_courses         ~150 records
✅ ra_bookmakers       ~50 records
✅ ra_results       ~55,000 records    (2015-2025)
✅ ra_races         ~15,000 records    (2023-2025)
✅ ra_runners      ~600,000 records    (2023-2025)
✅ ra_horses        ~80,000 records    (2015-2025)
✅ ra_jockeys        ~3,000 records    (2015-2025)
✅ ra_trainers       ~2,500 records    (2015-2025)
✅ ra_owners        ~25,000 records    (2015-2025)
───────────────────────────────────────────────
TOTAL:          ~781,700 records
```

### Year-by-Year Coverage

| Year | Results | Racecards | Status |
|------|---------|-----------|--------|
| 2015 | ✅ | ❌ (API limitation) | Results only |
| 2016 | ✅ | ❌ (API limitation) | Results only |
| 2017 | ✅ | ❌ (API limitation) | Results only |
| 2018 | ✅ | ❌ (API limitation) | Results only |
| 2019 | ✅ | ❌ (API limitation) | Results only |
| 2020 | ✅ | ❌ (API limitation) | Results only |
| 2021 | ✅ | ❌ (API limitation) | Results only |
| 2022 | ✅ | ❌ (API limitation) | Results only |
| 2023 | ✅ | ✅ | Complete |
| 2024 | ✅ | ✅ | Complete |
| 2025 | ✅ | ✅ | Complete |

---

## Support & Additional Documentation

- **API Documentation**: See `docs/racing_api_openapi.json` for full API specification
- **Deployment Guide**: See `RENDER_DEPLOYMENT.md` for production deployment
- **Main README**: See `README.md` for project overview

---

## Quick Commands Cheat Sheet

```bash
# === SETUP ===
# Navigate to project
cd /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers

# Check current state
python3 management/cleanup_and_reset.py

# Clean database
python3 management/cleanup_and_reset.py --confirm

# === INITIALIZATION ===
# Start full data collection (11-16 hours)
nohup python3 scripts/initialize_data.py > logs/initialization_$(date +%Y%m%d_%H%M%S).log 2>&1 &

# Monitor progress
python3 monitors/monitor_data_progress.py

# === MONITORING ===
# Year-by-year progress bars (recommended)
python3 monitors/monitor_progress_bars.py

# Comprehensive dashboard
python3 monitors/monitor_data_progress.py

# Check if running
ps aux | grep initialize_data.py

# View logs
tail -f logs/initialization_*.log

# Check for errors
grep -i error logs/initialization_*.log

# === MAINTENANCE ===
# Daily updates
python3 scripts/update_daily_data.py

# Health check
python3 monitors/health_check.py

# Data quality check
python3 monitors/data_quality_check.py
```

---

**Last Updated:** 2025-10-06
**Version:** 1.0
**Status:** Production Ready ✅
