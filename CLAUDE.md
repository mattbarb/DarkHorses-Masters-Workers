# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DarkHorses-Masters-Workers is a production system for fetching and maintaining UK and Ireland horse racing reference/master data from The Racing API into a Supabase PostgreSQL database. It implements a hybrid data enrichment strategy that automatically captures complete pedigree data for all discovered horses.

## Essential Commands

### Run All Fetchers (Full Sync)
```bash
python3 main.py --all
```

### Daily Operations (Production Schedule)
```bash
# Daily: Races and results
python3 main.py --daily

# Weekly: People and horses
python3 main.py --weekly

# Monthly: Courses and bookmakers
python3 main.py --monthly
```

### Fetch Specific Entities
```bash
python3 main.py --entities races results
python3 main.py --entities horses --test  # Limited data for testing
```

### Monitor Backfill Operations
```bash
# Check backfill status
python3 scripts/monitor_backfill.py --interval 60

# View backfill logs
tail -f logs/backfill_horse_pedigree_*.log

# Check if backfill is running
ps -p $(cat logs/backfill_pid.txt)
```

### Run Horse Pedigree Backfill
```bash
# Full backfill (all horses)
python3 scripts/backfill_horse_pedigree_enhanced.py

# Resume from checkpoint (if interrupted)
python3 scripts/backfill_horse_pedigree_enhanced.py --resume --non-interactive
```

### API Testing
```bash
# Comprehensive API endpoint testing
python3 scripts/comprehensive_api_test.py

# Test specific enrichment
python3 scripts/test_hybrid_enrichment.py

# Test enhanced data capture (6 new runner fields)
python3 scripts/test_enhanced_data_capture.py
```

## Architecture

### Hybrid Enrichment Strategy (Critical Concept)

The system uses a **two-step hybrid approach** for horse data:

1. **Discovery Phase (Fast):**
   - Fetches racecards from `/v1/racecards/pro`
   - Extracts basic horse data (id, name, sex) from race runners
   - Discovers 50-100 new horses daily

2. **Enrichment Phase (Complete Data):**
   - `EntityExtractor` checks if horses are new (not in database)
   - **NEW horses only:** Fetches complete data from `/v1/horses/{id}/pro`
   - Adds 9 additional fields: dob, sex_code, colour, colour_code, region, plus complete pedigree (sire, dam, damsire, breeder with IDs)
   - Rate-limited: 2 requests/second (0.5s sleep between calls)
   - Daily overhead: ~27 seconds for 50 new horses

**Key Implementation:**
- `utils/entity_extractor.py`: `_enrich_new_horses()` method implements hybrid logic
- `fetchers/races_fetcher.py` and `fetchers/results_fetcher.py`: Pass `api_client` to `EntityExtractor` to enable enrichment
- Enrichment is **automatic** - no manual intervention needed

### Data Flow

```
Racing API (/v1/racecards/pro)
    ↓
RacesFetcher (fetchers/races_fetcher.py)
    ↓
EntityExtractor (utils/entity_extractor.py)
    ├─ Extract entities (jockeys, trainers, owners, horses)
    ├─ Check database for existing horses
    ├─ For NEW horses: Fetch from /v1/horses/{id}/pro (enrichment)
    └─ Store complete data
    ↓
Supabase PostgreSQL
    ├─ ra_horses (with complete metadata)
    ├─ ra_horse_pedigree (complete lineage)
    ├─ ra_runners (race entries)
    ├─ ra_jockeys, ra_trainers, ra_owners
    └─ ra_races, ra_results
```

### Fetcher Architecture Pattern

All fetchers follow this consistent pattern:

```python
class SomeFetcher:
    def __init__(self):
        self.config = get_config()
        self.api_client = RacingAPIClient(...)
        self.db_client = SupabaseReferenceClient(...)
        # For fetchers that extract entities:
        self.entity_extractor = EntityExtractor(self.db_client, self.api_client)

    def fetch_and_store(self, **config) -> Dict:
        # 1. Fetch from Racing API
        # 2. Transform API data to database format
        # 3. Store in Supabase
        # 4. Return statistics
        pass
```

**Fetchers with Entity Extraction:**
- `races_fetcher.py`: Extracts entities from runners (uses enrichment)
- `results_fetcher.py`: Extracts entities from results (uses enrichment)

**Direct Fetchers (No Entity Extraction):**
- `courses_fetcher.py`, `bookmakers_fetcher.py`
- `jockeys_fetcher.py`, `trainers_fetcher.py`, `owners_fetcher.py`
- `horses_fetcher.py` (direct bulk fetch, no enrichment)

### Database Schema (ra_* prefix)

**⭐ MASTER REFERENCES:**
- **Complete Table Guide:** `fetchers/docs/*MASTER_DATABASE_TABLES_AND_DATA_SOURCES.md`
  - All 18 tables documented with fetchers, data sources, automation status
  - High-level overview with data flow diagrams
  - Quick reference for which fetcher populates which table

- **Detailed Transformations:** `fetchers/docs/*_MASTER_TABLES_DATA_SOURCES_AND_TRANSFORMATIONS.md`
  - Detailed field mappings and transformations
  - API endpoint specifications
  - Migration history and schema changes

**Reference Tables (Master Data):**
- `ra_mst_courses`, `ra_mst_bookmakers` - Venues and bookmakers
- `ra_mst_jockeys`, `ra_mst_trainers`, `ra_mst_owners` - People (extracted from racecards)
- `ra_mst_horses` - Horses with hybrid enrichment (discovery + Pro endpoint)
- `ra_horse_pedigree` - Complete lineage (sire, dam, damsire, breeder with IDs)
- `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires` - Pedigree statistics (calculated from database)

**Transaction Tables (Race Data):**
- `ra_races` - Race metadata
- `ra_runners` - Race entries with comprehensive runner details
- `ra_race_results` - Historical results (updates runners with positions)

**System Tables:**
- `ra_metadata_tracking` - Data freshness tracking

### Enhanced Runner Fields (Migration 011 - 2025-10-17)

The `ra_runners` table captures comprehensive race result data including 6 **newly added fields** that provide critical ML features and UI enhancements:

**Result/Position Fields (Existing):**
- `position` - Finishing position (1, 2, 3, etc.)
- `distance_beaten` - Distance behind winner
- `prize_won` - Prize money earned
- `starting_price` - Fractional odds (e.g., "7/2")
- `finishing_time` - Race time (e.g., "1:48.55")

**Enhanced Fields (NEW - Migration 011):**
1. `starting_price_decimal` (DECIMAL) - **CRITICAL for ML**: Decimal odds (e.g., 4.50) - enables direct numerical analysis without fractional parsing
2. `race_comment` (TEXT) - Race commentary/running notes - qualitative analysis, future NLP features
3. `jockey_silk_url` (TEXT) - Jockey silk image URL (SVG) - UI/display enhancement
4. `overall_beaten_distance` (DECIMAL) - Alternative distance metric in lengths - additional ML feature
5. `jockey_claim_lbs` (INTEGER) - Jockey weight allowance (0 if none) - race conditions data
6. `weight_stones_lbs` (VARCHAR) - Weight in UK format (e.g., "8-13") - display format

**Field Population Rates:**
- All enhanced fields: **100%** population in results data
- `finishing_time`, `starting_price_decimal`, `race_comment`: Only available AFTER race completion
- `jockey_silk_url`, `weight_stones_lbs`, `jockey_claim_lbs`: Available in both racecards (pre-race) and results (post-race)

**Implementation Details:**
- Captured automatically by `results_fetcher.py` and `races_fetcher.py`
- Uses safe parsing functions from `utils/position_parser.py`
- No additional API calls required (data comes from existing endpoints)
- Fully backward compatible (additive migration)

## Configuration

### Environment Variables (Required)

```bash
# Racing API credentials
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password

# Supabase credentials
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

Configuration loads from:
1. `.env.local` in project root (preferred)
2. `.env.local` in parent directory
3. Environment variables directly

**Config class:** `config/config.py` - `ReferenceDataConfig`

### API Rate Limiting

**Racing API:** 2 requests/second across ALL plan tiers
- Implemented in `utils/api_client.py`
- Automatic retry with exponential backoff
- 5 max retries by default

**Enrichment Impact:**
- 50 new horses/day × 0.5s = 25 seconds
- Well within rate limits

## Key Files and Their Purpose

### Entry Points
- `main.py` - Production orchestrator, handles all fetcher coordination
- `start_worker.py` - Worker mode entry point for scheduled tasks

### Core Modules
- `utils/entity_extractor.py` - **Critical:** Implements hybrid enrichment for horses
- `utils/api_client.py` - Racing API client with rate limiting and retries
- `utils/supabase_client.py` - Database operations with batch processing and UPSERT logic
- `config/config.py` - Configuration management

### Active Scripts
- `scripts/backfill_horse_pedigree_enhanced.py` - Production backfill (resume-capable)
- `scripts/monitor_backfill.py` - Real-time backfill monitoring
- `scripts/comprehensive_api_test.py` - API endpoint validation

### Important: Deprecated Code

**Location:** `_deprecated/` directory
- Old/superseded implementations
- Test scripts from development
- Outdated documentation

**DO NOT use code from `_deprecated/`** - it's preserved for reference only.

## Important Bug Fixes and Learnings

### ResultsFetcher Return Format (Fixed: 2025-10-17)

**Critical Bug:** The backfill script `scripts/backfill_all_ra_tables_2015_2025.py` was incorrectly checking for `result.get('races_fetched')` when `ResultsFetcher.fetch_and_store()` actually returns `result.get('fetched')`.

**What ResultsFetcher Returns:**
```python
{
    'success': True,
    'fetched': len(all_results),  # Number of races (NOT 'races_fetched')
    'inserted': results_dict.get('races', {}).get('inserted', 0),
    'days_fetched': days_fetched,
    'days_with_data': days_with_data,
    'db_stats': {
        'races': {'inserted': X, ...},
        'runners': {'inserted': Y, ...},
        'entities': {...}
    }
}
```

**Correct way to extract stats:**
```python
races_fetched = result.get('fetched', 0)  # NOT 'races_fetched'
runners_fetched = result.get('db_stats', {}).get('runners', {}).get('inserted', 0)
horses_enriched = result.get('db_stats', {}).get('entities', {}).get('horses', {}).get('inserted', 0)
```

**Impact:** This bug caused the backfill to report "No races on this date" for ALL dates, even though the Racing API Pro plan DOES have historical data back to 2015.

### Racing API Historical Data Coverage

**Pro Plan Coverage:** The Racing API Pro plan provides:
- ✅ **Historical results from 2015+** (confirmed tested back to 2015-01-01)
- ✅ Complete race data with finishing positions
- ✅ Full pedigree data
- ✅ Entity data (horses, jockeys, trainers, owners)

**Not a limitation:** The warning "Results API on Standard plan is limited to last 12 months" in `results_fetcher.py:60` is outdated/incorrect for Pro plan subscribers.

## Common Tasks and Patterns

### Adding a New Field to Extraction

**Example:** Adding a new field to horses from racecards

1. **Update transformer:** `fetchers/races_fetcher.py`
   ```python
   runner_record = {
       # ... existing fields ...
       'new_field': runner.get('new_api_field'),
   }
   ```

2. **Update database client:** `utils/supabase_client.py`
   - Ensure `insert_runners()` or relevant method handles new field

3. **Verify:** Database schema has column (may need migration)

### Testing Enrichment

```python
# Test with real API data
python3 scripts/test_hybrid_enrichment.py

# Expected output:
# ✓ Horses enriched with Pro endpoint
# ✓ Pedigree records captured
# ✓ Database verification successful
```

### Checking Data Completeness

```sql
-- Check horse enrichment status
SELECT
  COUNT(*) as total_horses,
  COUNT(dob) as enriched_horses,
  ROUND(COUNT(dob)::numeric / COUNT(*)::numeric * 100, 2) as enrichment_pct
FROM ra_horses;

-- Check pedigree coverage
SELECT
  COUNT(*) as total_horses,
  COUNT(p.horse_id) as horses_with_pedigree,
  ROUND(COUNT(p.horse_id)::numeric / COUNT(*)::numeric * 100, 2) as pedigree_pct
FROM ra_horses h
LEFT JOIN ra_horse_pedigree p ON h.horse_id = p.horse_id;
```

### Understanding Error Handling

**Pattern used throughout:**
```python
try:
    result = do_something()
    logger.info(f"Success: {result}")
    return {'success': True, 'data': result}
except Exception as e:
    logger.error(f"Failed: {e}", exc_info=True)
    return {'success': False, 'error': str(e)}
```

**All fetchers return:** `Dict` with at minimum:
- `success`: bool
- `fetched`: int (items from API)
- `inserted`: int (items in database)
- `error`: Optional[str]

## Documentation

**Start here:** `docs/README.md` - Master documentation index

**⭐ MASTER REFERENCES (Single Source of Truth):**
- **Tables & Data Sources:** `fetchers/docs/*_MASTER_TABLES_DATA_SOURCES_AND_TRANSFORMATIONS.md`
  - Complete mapping of all 13 ra_* tables
  - Data sources (Racing API, database calculation, external)
  - Transformations and field mappings
  - Population scripts and update frequencies
  - **USE THIS for all questions about table structure and data flow**

**For specific topics:**
- API details: `docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md`
- API endpoint availability: `docs/RACING_API_ENDPOINT_FINDINGS.md`
- API coverage by table: `docs/RACING_API_COVERAGE_SUMMARY.md`
- Enrichment strategy: `docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`
- Backfill operations: `docs/backfill/BACKFILL_EXECUTION_SUMMARY.md`
- Worker system: `docs/workers/WORKER_UPDATE_REPORT.md`
- Getting started: `docs/architecture/START_HERE.md`

**Finding information:**
- 60+ documentation files organized in 8 topic subdirectories
- Each subdirectory has a specific focus (api, enrichment, backfill, etc.)
- Canonical references marked with **bold** in docs/README.md
- Master tables document marked with ⭐ asterisk prefix

## Debugging and Troubleshooting

### Logging

**Logs location:** `logs/` directory

**Key logs:**
- `logs/fetch_results_TIMESTAMP.json` - Fetch operation summaries
- `logs/backfill_horse_pedigree_TIMESTAMP.log` - Backfill execution log
- `logs/backfill_checkpoint.json` - Resume checkpoint for backfill
- `logs/backfill_errors.json` - Backfill error tracking

**Logger usage:**
```python
from utils.logger import get_logger
logger = get_logger('module_name')

logger.info("Normal operation")
logger.warning("Potential issue")
logger.error("Error occurred", exc_info=True)  # Include traceback
```

### Common Issues

**Missing Pedigree Data:**
- Check if `api_client` is passed to `EntityExtractor` in fetcher `__init__`
- Verify environment variables are set (`RACING_API_USERNAME`, `RACING_API_PASSWORD`)
- Check enrichment stats in logs: `horses_enriched` should be > 0

**Rate Limit Errors:**
- Should auto-retry with backoff
- Check `api_client.py` configuration: `rate_limit_per_second = 2`
- For backfills: Verify `time.sleep(0.5)` between Pro endpoint calls

**Database Connection Issues:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check Supabase dashboard for connection limits
- Review batch size in config (default: 100)

## Regional Filtering

**All data is filtered to UK (GB) and Ireland (IRE) only.**

**Implementation:**
- `main.py`: `PRODUCTION_CONFIGS` specifies `region_codes: ['gb', 'ire']`
- Fetchers pass `region_codes` to API client
- Some fetchers (jockeys, owners) use post-fetch filtering
- Consistent across all data sources

## Testing

**Test mode (limited data):**
```bash
python3 main.py --test --entities horses
```

Applies custom configs:
- `max_pages: 5` for bulk fetchers
- `days_back: 7` for races
- `days_back: 30` for results

**Validation scripts:**
- `tests/endpoint_validation/` - API endpoint validation
- `scripts/test_hybrid_enrichment.py` - Enrichment validation
- `scripts/comprehensive_api_test.py` - Complete API testing

## Performance Considerations

**Batch Processing:**
- Database inserts use batches (default: 100 records)
- Configured in `SupabaseConfig.batch_size`

**UPSERT Strategy:**
- All inserts are UPSERT (insert or update on conflict)
- Uses primary keys for conflict resolution
- Prevents duplicate data

**Enrichment Performance:**
- Only NEW horses are enriched (skips existing)
- Daily overhead: ~27 seconds for 50 horses
- Historical backfill: ~24 hours for 111,000 horses

**API Optimization:**
- Pro endpoint used only for enrichment (not bulk fetch)
- Racecards fetched once daily per date
- Results fetched in date ranges

## Related Repositories

- **DarkHorses-Odds-Workers:** Live & historical odds collection
- **DarkHorses-AI-Engine:** ML prediction engine

**Integration point:** Both systems read from the same Supabase database (`ra_*` tables).

## Production Deployment

**Current status:** Production-ready

**Deployment targets:**
- Render.com (see `docs/deployment/RENDER_DEPLOYMENT.md`)
- Can run on any Python 3.9+ environment

**Required for deployment:**
- Environment variables configured
- Scheduled tasks set up (daily/weekly/monthly)
- Monitoring for backfill operations
- Log rotation for `logs/` directory

## Version and Maintenance

**System Version:** Production Release v1.0
**Last Updated:** 2025-10-15
**Code Quality:** Professional-grade, thoroughly documented
**Test Coverage:** All critical paths validated
**Documentation:** 60+ files, fully organized

---

**For comprehensive documentation, start at:** `docs/README.md`
