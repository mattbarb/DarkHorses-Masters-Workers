# DarkHorses Masters Workers - Data Collection Plan

## Executive Summary

This document outlines the comprehensive data collection strategy for the DarkHorses horse racing database. The system is designed to work within the constraints of The Racing API's different subscription tiers while maximizing data coverage for UK and Ireland horse racing.

**Key Constraints:**
- Historical racecards available from **2023-01-23 onwards** (Pro plan)
- Results API limited to **last 12 months only** (Standard plan)
- Entity search endpoints require name parameters (not suitable for bulk collection)
- API rate limit: **2 requests/second**

**Solution Approach:**
- Extract entities (jockeys, trainers, owners, horses) from race/runner data automatically
- Backfill from 2023-01-23 to present for maximum historical coverage
- Implement multi-tier update strategy (live, daily, weekly, monthly)
- Design idempotent processes safe for re-execution

---

## Data Sources & Availability

### What's Available & When

| Data Type | API Endpoint | Historical Availability | Current Status |
|-----------|--------------|------------------------|----------------|
| **Racecards/Races** | `/v1/racecards` | 2023-01-23 onwards (Pro) | IMPLEMENTED |
| **Results** | `/v1/results` | Last 12 months only | IMPLEMENTED |
| **Courses** | `/v1/courses` | Static/Reference data | IMPLEMENTED |
| **Bookmakers** | `/v1/bookmakers` | Static/Reference data | IMPLEMENTED |
| **Jockeys** | Entity extraction | From race data | IMPLEMENTED |
| **Trainers** | Entity extraction | From race data | IMPLEMENTED |
| **Owners** | Entity extraction | From race data | IMPLEMENTED |
| **Horses** | Entity extraction | From race data | IMPLEMENTED |

### Pre-2023 Data Gap

**Problem:** Racecards API only provides data from 2023-01-23 onwards. We cannot access 2015-2022 data via the current API.

**Options for Pre-2023 Data:**

1. **Premium Data Add-On (Recommended if budget permits)**
   - Cost: £299 for 30+ years of results
   - Provides: Complete historical results back to 1990s
   - Implementation: Modify `initialize_data.py` to fetch from 2015 or earlier

2. **External Data Sources**
   - Racing Post historical data exports
   - British Horseracing Authority (BHA) data
   - Timeform historical database
   - Manual CSV imports from alternative providers

3. **Gradual Accumulation**
   - Accept 2023-01-23 as starting point
   - Build dataset forward from that date
   - Advantage: Free, fully automated
   - Disadvantage: No pre-2023 historical context

4. **Hybrid Approach**
   - Use API for 2023+ (automated)
   - One-time manual import for 2015-2022 (if source available)
   - Merge datasets in database

**Current Implementation:** We start from 2023-01-23 (earliest available via API).

---

## Historical Backfill Strategy

### Initial Population (One-Time Setup)

**Script:** `initialize_data.py` (already implemented)

**Process:**
1. Fetch reference data (courses, bookmakers)
2. Fetch historical races from 2023-01-23 to present in 90-day chunks
3. Auto-extract entities from race/runner data
4. Store all data with idempotent upsert logic

**Date Range:** 2023-01-23 to current date
**Estimated Records:**
- ~750 days of racing (2023-01-23 to 2025-10-06)
- ~50-100 races per day (GB+IRE)
- ~37,500-75,000 total races
- ~10-15 runners per race
- ~375,000-1,125,000 runner records

**Execution Time:**
- 90-day chunks processed sequentially
- ~5 second pause between chunks
- Estimated total: 2-4 hours (depends on API response times)

**API Usage:**
- 2 requests per day (racecard + results)
- ~1,500 requests total for full backfill
- Rate-limited to 2 req/sec = safe execution

### 12-Month Quick Start (Alternative)

**Script:** `initialize_12months.py` (already implemented)

**Use Case:** When full historical backfill isn't needed, or for testing

**Process:**
- Last 12 months of races/results
- 30-day chunks for faster processing
- ~365 days = ~12 chunks
- Execution time: ~30-60 minutes

---

## Table-by-Table Collection Plan

### 1. Courses (ra_courses)

**Data Source:** `/v1/courses` API endpoint
**Update Frequency:** Monthly
**Business Criticality:** HIGH (required for all race data)
**Dependencies:** None (foundational)

**Collection Strategy:**
- Initial: Fetch all GB/IRE courses
- Updates: Monthly refresh to catch new courses or changes
- Approximately 60-80 UK/IRE courses total
- Very low change frequency (new courses are rare)

**Update Script:** `update_reference_data.py --monthly`

**Idempotency:** Upsert by `course_id`

---

### 2. Bookmakers (ra_bookmakers)

**Data Source:** `/v1/bookmakers` API endpoint
**Update Frequency:** Monthly
**Business Criticality:** MEDIUM (needed for odds tracking)
**Dependencies:** None (static reference)

**Collection Strategy:**
- Initial: Fetch all bookmakers
- Updates: Monthly refresh for new bookmakers
- Approximately 20-30 active UK/IRE bookmakers
- Low change frequency

**Update Script:** `update_reference_data.py --monthly`

**Idempotency:** Upsert by `bookmaker_id`

---

### 3. Jockeys (ra_jockeys)

**Data Source:** Extracted from runner data
**Update Frequency:** Daily (via race updates)
**Business Criticality:** HIGH (core entity)
**Dependencies:** Races, Runners

**Collection Strategy:**
- Initial: Extracted during historical backfill
- Updates: Automatically extracted from daily race updates
- New jockeys appear in runner data
- Existing jockeys auto-update when appearing in races

**Update Script:** Automatic via `update_daily_data.py`

**Idempotency:** Upsert by `jockey_id` (from API)

**Notes:**
- No separate API fetch needed
- Data freshness tied to race participation
- Inactive jockeys remain in database but don't update

---

### 4. Trainers (ra_trainers)

**Data Source:** Extracted from runner data
**Update Frequency:** Daily (via race updates)
**Business Criticality:** HIGH (core entity)
**Dependencies:** Races, Runners

**Collection Strategy:**
- Initial: Extracted during historical backfill
- Updates: Automatically extracted from daily race updates
- New trainers appear in runner data
- Existing trainers auto-update when appearing in races

**Update Script:** Automatic via `update_daily_data.py`

**Idempotency:** Upsert by `trainer_id` (from API)

---

### 5. Owners (ra_owners)

**Data Source:** Extracted from runner data
**Update Frequency:** Daily (via race updates)
**Business Criticality:** MEDIUM (analytics/insights)
**Dependencies:** Races, Runners

**Collection Strategy:**
- Initial: Extracted during historical backfill
- Updates: Automatically extracted from daily race updates
- New owners appear in runner data
- Existing owners auto-update when appearing in races

**Update Script:** Automatic via `update_daily_data.py`

**Idempotency:** Upsert by `owner_id` (from API)

---

### 6. Horses (ra_horses)

**Data Source:** Extracted from runner data
**Update Frequency:** Daily (via race updates)
**Business Criticality:** HIGH (core entity)
**Dependencies:** Races, Runners

**Collection Strategy:**
- Initial: Extracted during historical backfill
- Updates: Automatically extracted from daily race updates
- New horses appear in runner data
- Existing horses auto-update (age, form, etc.) when racing

**Update Script:** Automatic via `update_daily_data.py`

**Idempotency:** Upsert by `horse_id` (from API)

**Notes:**
- Includes pedigree data (sire, dam, damsire)
- Form data updates with each race appearance
- Retired/inactive horses remain in database

---

### 7. Races (ra_races)

**Data Source:** `/v1/racecards` API endpoint
**Update Frequency:**
- **Future races:** Daily (racecards for tomorrow)
- **Historical races:** One-time backfill + daily for yesterday
- **Live races:** Every 5-15 minutes during racing hours

**Business Criticality:** CRITICAL (core data)
**Dependencies:** Courses

**Collection Strategy:**

**Daily Updates:**
- Fetch racecards for next 2 days (tomorrow + day after)
- Fetch results for yesterday to backfill any missed races
- Time: 06:00 UTC (before racing starts)

**Live Updates (Racing Days):**
- Fetch current day's racecards every 15 minutes
- Update race status, going conditions, off times
- Time: 09:00-21:00 UTC on racing days

**Historical Backfill:**
- One-time: 2023-01-23 to present
- Incremental: Yesterday's races each day

**Update Scripts:**
- Daily: `update_daily_data.py --racecards`
- Live: `update_live_data.py --races`

**Idempotency:** Upsert by `race_id`

**Key Fields to Update:**
- `off_datetime` (may change)
- `going` (track conditions)
- `weather_conditions`
- `race_status` (abandoned, postponed, etc.)
- `field_size` (non-runners reduce field)

---

### 8. Runners (ra_runners)

**Data Source:** `/v1/racecards` API endpoint (nested in races)
**Update Frequency:** Same as Races
**Business Criticality:** CRITICAL (core data)
**Dependencies:** Races, Horses, Jockeys, Trainers, Owners

**Collection Strategy:**
- Always fetched with race data
- Updates include withdrawals (non-runners)
- Live updates capture late changes (jockey changes, etc.)

**Update Scripts:**
- Daily: `update_daily_data.py --racecards`
- Live: `update_live_data.py --races`

**Idempotency:** Upsert by `runner_id` (race_id + horse_id)

**Key Fields to Update:**
- `number` (may change)
- `draw` (may be reassigned after withdrawals)
- `jockey_id` / `jockey_name` (jockey changes)
- `weight` (weight changes)
- `headgear` (equipment changes)

---

### 9. Results (ra_results)

**Data Source:** `/v1/results` API endpoint
**Update Frequency:**
- **Post-race:** Every 30 minutes (during racing hours)
- **Daily backfill:** 06:00 UTC for yesterday
- **Weekly reconciliation:** Sunday night for past week

**Business Criticality:** CRITICAL (outcome data)
**Dependencies:** Races

**Collection Strategy:**

**Live Updates (Racing Days):**
- Poll every 30 minutes during racing hours (12:00-21:00 UTC)
- Capture results as they become official
- Store finishing positions, times, distances

**Daily Backfill:**
- 06:00 UTC: Fetch all results from yesterday
- Ensures any missed live results are captured
- Reconciles any provisional results

**Weekly Reconciliation:**
- Sunday 23:00 UTC: Fetch past 7 days
- Catch any late amendments or corrections
- Handle objections, steward inquiries

**Historical Limit:**
- API only provides last 12 months
- Cannot backfill beyond 12 months ago
- If premium add-on purchased: can extend back to 1990s

**Update Scripts:**
- Live: `update_live_data.py --results`
- Daily: `update_daily_data.py --results`
- Weekly: `update_daily_data.py --results --days-back 7`

**Idempotency:** Upsert by `race_id` (one result record per race)

**Key Fields:**
- `results_status` (provisional, official, amended)
- `api_data.runners` (finishing positions)
- `winner`, `placed_horses`

---

## Update Frequency Requirements Summary

| Update Type | Frequency | Tables Updated | Time Window | Script |
|-------------|-----------|----------------|-------------|--------|
| **Live/Real-time** | Every 5-15 min | Races, Runners, Results | 09:00-21:00 UTC | `update_live_data.py` |
| **Daily** | Once per day | Races, Runners, Results | 06:00 UTC | `update_daily_data.py` |
| **Weekly** | Once per week | Races, Results (reconciliation) | Sunday 23:00 UTC | `update_daily_data.py --weekly` |
| **Monthly** | Once per month | Courses, Bookmakers | 1st day, 03:00 UTC | `update_reference_data.py` |
| **One-time** | Initial setup | All tables | On deployment | `initialize_data.py` |

---

## Dependency Graph

```
Foundational (No Dependencies):
├── ra_courses
└── ra_bookmakers

Core Racing Data (Depends on Courses):
├── ra_races (requires: courses)
│   └── ra_runners (requires: races)
│       └── ra_results (requires: races)

Extracted Entities (Depends on Runners):
├── ra_jockeys (extracted from: runners)
├── ra_trainers (extracted from: runners)
├── ra_owners (extracted from: runners)
└── ra_horses (extracted from: runners)
```

**Execution Order:**
1. Courses, Bookmakers (can run in parallel)
2. Races (depends on courses)
3. Runners (depends on races)
4. Entities extraction (depends on runners)
5. Results (depends on races)

---

## Data Quality & Reconciliation

### Idempotency Strategy

All update scripts implement **upsert logic** (insert or update):
- Primary key: Entity-specific ID from API
- On conflict: Update all fields with latest data
- Safe to re-run: No duplicate records created

### Missing Data Handling

**Scenario 1: API Unavailable**
- Retry with exponential backoff (up to 5 attempts)
- Log failure, continue with next entity
- Alert if consecutive failures exceed threshold

**Scenario 2: Partial Data**
- Store incomplete records with `is_complete=false` flag
- Retry fetch in next cycle
- Fill gaps during weekly reconciliation

**Scenario 3: Late Results**
- Some results marked "provisional" initially
- Weekly reconciliation catches amendments
- Compare with race status field

### Deduplication

**By Design:**
- Supabase upsert handles duplicates automatically
- Unique constraints on API IDs prevent duplicates
- Safe to fetch overlapping date ranges

---

## Options for Pre-2023 Data

### Option 1: Premium API Add-On (Best Quality)

**Cost:** £299 one-time for 30+ years of results

**Benefits:**
- Official Racing API data
- Consistent data structure
- Easy integration with existing code
- Historical results back to 1990s

**Implementation:**
```python
# Modify initialize_data.py
start_date = '2015-01-01'  # Or earlier
# Rest of code works as-is
```

### Option 2: Alternative Data Providers

**Sources:**
- **Racing Post:** Historical data exports (may require license)
- **Timeform:** Historical database access
- **BHA (British Horseracing Authority):** Official historical records
- **Betfair Historical Data:** Race results and market data

**Challenges:**
- Data format may differ (requires transformation)
- One-time manual import needed
- Data quality varies by source
- Licensing costs may apply

**Implementation:**
- Create separate import script: `import_historical_data.py`
- Map external data to our schema
- Handle format conversions
- Merge with API data post-2023

### Option 3: Web Scraping (Not Recommended)

**Sources:**
- Racing Post website archives
- Timeform website
- Various racing statistics sites

**Risks:**
- Terms of Service violations
- Data quality issues
- Requires constant maintenance (sites change)
- Legal issues

**Verdict:** Not recommended. Use official sources only.

### Option 4: Accept 2023+ Start Date (Most Practical)

**Rationale:**
- Zero additional cost
- Fully automated
- Clean, consistent data
- ~2.5 years of history already substantial
- Dataset grows daily

**Use Cases:**
- MVP/Initial launch: Sufficient for most features
- Machine learning: 2.5 years = good training data
- Live betting features: Recent data more relevant
- Form analysis: Recent form most predictive

**Recommendation:** Start with Option 4, upgrade to Option 1 if business requires older data.

---

## Storage & Retention

### Database Size Estimates

**Current (2023-01-23 to 2025-10-06):**
- Races: ~50,000 records × ~5 KB = 250 MB
- Runners: ~500,000 records × ~3 KB = 1.5 GB
- Results: ~50,000 records × ~2 KB = 100 MB
- Entities: ~10,000 records × ~2 KB = 20 MB
- **Total:** ~2 GB (compressed)

**Annual Growth:**
- ~20,000 races/year
- ~200,000 runners/year
- ~500 MB/year growth

**5-Year Projection:** ~5 GB total

### Retention Policy

**Production Data:** Retain indefinitely
- Historical value for analysis
- Storage costs low (Supabase free tier: 500 MB, Pro tier: 8 GB+)
- Regulatory: No specific retention requirements for horse racing data

**Logs:** Retain 90 days
- Application logs in `/logs` directory
- Rotate daily, compress weekly
- Archive critical error logs

**API Response Cache:** 24 hours
- Cache full API responses in `api_data` JSONB field
- Useful for debugging, reprocessing
- Can be purged if storage constrained

---

## Monitoring & Alerts

### Health Checks

**Metrics to Monitor:**
1. **Data Freshness:** Last successful fetch timestamp per table
2. **API Success Rate:** Percentage of successful API calls
3. **Record Counts:** Daily growth in each table
4. **Failure Rate:** Consecutive failures trigger alert

**Implementation:** `health_check.py` (already exists)

### Alert Thresholds

- **CRITICAL:** No data fetched for 24+ hours
- **WARNING:** API failure rate > 10%
- **INFO:** Unexpected record count (> 50% deviation from average)

### Logging Strategy

**Log Levels:**
- **DEBUG:** Detailed API request/response (dev only)
- **INFO:** Normal operations, record counts, success messages
- **WARNING:** Retries, missing data, minor issues
- **ERROR:** API failures, database errors, critical issues

**Log Destinations:**
- **Local:** `/logs` directory (development)
- **Production:** Render.com logs (stdout/stderr)
- **Optional:** External service (Sentry, Datadog) for production monitoring

---

## Next Steps

### Immediate (Week 1)
1. Run initial backfill: `python initialize_data.py`
2. Verify data quality: `python data_quality_check.py`
3. Deploy scheduler: `run_scheduled_updates.py` on Render.com

### Short-term (Month 1)
1. Monitor data freshness and API usage
2. Tune update frequencies based on actual racing schedules
3. Implement alerting for failures
4. Add dashboard for monitoring

### Long-term (Quarter 1)
1. Evaluate pre-2023 data needs based on product requirements
2. Consider premium API add-on if historical data valuable
3. Optimize queries and add database indexes
4. Implement data analytics pipeline

---

## Appendix: API Endpoints Reference

| Endpoint | Method | Parameters | Notes |
|----------|--------|------------|-------|
| `/v1/racecards` | GET | `date`, `region_codes` | Pro plan: from 2023-01-23 |
| `/v1/results` | GET | `start_date`, `end_date`, `region` | Standard: last 12 months |
| `/v1/courses` | GET | `region_codes` | Static reference data |
| `/v1/bookmakers` | GET | - | Static reference data |

**Rate Limit:** 2 requests/second (enforced by API client)

**Regional Codes:**
- `gb` = Great Britain (England, Scotland, Wales)
- `ire` = Ireland

---

**Document Version:** 1.0
**Last Updated:** 2025-10-06
**Author:** DarkHorses Development Team
