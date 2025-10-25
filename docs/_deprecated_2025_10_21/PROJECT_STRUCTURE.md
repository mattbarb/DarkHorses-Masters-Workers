# DarkHorses Masters Workers - Project Structure

**Last Updated:** 2025-10-15
**Status:** Clean and Organized

---

## Quick Start

**New to this project?** Start here:
1. Read: `docs/README.md` (Master Documentation Index)
2. Then: `docs/architecture/START_HERE.md`
3. Setup: `docs/architecture/GETTING_STARTED.md`

**Looking for something specific?**
- See `docs/README.md` for complete navigation guide

---

## Directory Structure

```
DarkHorses-Masters-Workers/
│
├── config/                      # Configuration Management
│   ├── __init__.py
│   └── config.py               # Environment and settings
│
├── fetchers/                   # Data Fetching Modules (8 fetchers)
│   ├── __init__.py
│   ├── bookmakers_fetcher.py  # Bookmakers reference data
│   ├── courses_fetcher.py     # Racing courses/venues
│   ├── horses_fetcher.py      # Horse profiles (hybrid enrichment)
│   ├── jockeys_fetcher.py     # Jockey profiles
│   ├── owners_fetcher.py      # Horse owner profiles
│   ├── races_fetcher.py       # Race cards and runners
│   ├── results_fetcher.py     # Historical race results
│   └── trainers_fetcher.py    # Trainer profiles
│
├── utils/                      # Utility Modules (5 utilities)
│   ├── __init__.py
│   ├── api_client.py          # Racing API client
│   ├── entity_extractor.py    # Entity extraction & enrichment
│   ├── metadata_tracker.py    # Metadata tracking system
│   ├── regional_filter.py     # UK/Ireland filtering
│   └── supabase_client.py     # Supabase database client
│
├── scripts/                    # Active Scripts (17 scripts)
│   ├── backfill_horse_pedigree_enhanced.py  ⭐ ACTIVE BACKFILL
│   ├── backfill_race_ratings.py
│   ├── monitor_backfill.py
│   ├── comprehensive_api_test.py
│   ├── compile_ml_data.py
│   ├── analyze_database_coverage.py
│   ├── diagnose_missing_runners.py
│   ├── execute_data_updates.py
│   ├── run_scheduled_updates.py
│   ├── test_all_entity_endpoints.py
│   ├── test_hybrid_enrichment.py
│   ├── update_daily_data.py
│   ├── update_live_data.py
│   ├── update_reference_data.py
│   ├── validate_api_data.py
│   ├── validate_data_completeness.py
│   └── validate_data_updates.py
│
├── tests/                      # Test Suite (14 test files)
│   ├── README.md
│   ├── run_all_tests.py
│   ├── run_deployment_tests.py
│   ├── test_courses_worker.py
│   ├── test_data_freshness.py
│   ├── test_deployment.py
│   ├── test_e2e_worker.py
│   ├── test_people_horses_worker.py
│   ├── test_races_worker.py
│   └── test_schedule.py
│
├── monitors/                   # Monitoring Tools
│   ├── README.md
│   ├── check_progress.py
│   ├── data_quality_check.py
│   ├── health_check.py
│   ├── ml_data_monitor.py
│   ├── monitor_data_progress.py
│   ├── monitor_progress_bars.py
│   └── view_update_history.py
│
├── management/                 # System Management
│   ├── README.md
│   └── cleanup_and_reset.py
│
├── migrations/                 # Database Migrations (9 migrations)
│   ├── 001_create_metadata_tracking.sql
│   ├── 002_database_fixes.sql
│   ├── 003_add_missing_fields.sql
│   ├── 004_create_ml_runner_history.sql
│   ├── 005_add_position_fields_to_runners.sql
│   ├── 006_add_finishing_time_field.sql
│   ├── 007_add_entity_table_enhancements.sql
│   ├── 008_add_pedigree_and_horse_fields.sql
│   └── 009_remove_unused_columns.sql
│
├── docs/                       # Documentation (ORGANIZED)
│   │
│   ├── README.md              ⭐ MASTER DOCUMENTATION INDEX
│   │
│   ├── api/                   # API Documentation
│   │   ├── API_COMPREHENSIVE_TEST_SUMMARY.md
│   │   ├── API_QUICK_REFERENCE.md
│   │   ├── API_CROSS_REFERENCE_ADDENDUM.md
│   │   ├── RACING_API_DATA_AVAILABILITY.md
│   │   ├── DATA_SOURCES_FOR_API.md
│   │   ├── ENDPOINT_VALIDATION_SUMMARY.md
│   │   ├── APP_FIELDS_EXPLANATION.md
│   │   ├── api_endpoint_test_results.json
│   │   ├── entity_endpoint_test_results.json
│   │   ├── racing_api_openapi.json
│   │   ├── api_endpoint_inventory.json
│   │   └── endpoint_validation/ (validation scripts)
│   │
│   ├── enrichment/            # Enrichment Strategy
│   │   ├── HYBRID_ENRICHMENT_IMPLEMENTATION.md  ⭐ CANONICAL
│   │   ├── COMPLETE_ENRICHMENT_ANALYSIS.md
│   │   ├── ENRICHMENT_EXECUTIVE_SUMMARY.md
│   │   ├── ENRICHMENT_QUICK_REFERENCE.md
│   │   ├── ENRICHMENT_ARCHITECTURE.md
│   │   └── ENRICHMENT_INDEX.md
│   │
│   ├── backfill/              # Backfill Operations
│   │   ├── BACKFILL_EXECUTION_SUMMARY.md
│   │   └── BACKFILL_EXECUTION_REPORT.md
│   │
│   ├── workers/               # Worker System
│   │   ├── WORKER_UPDATE_REPORT.md
│   │   ├── WORKER_PEDIGREE_CAPTURE_ANALYSIS.md
│   │   ├── WORKER_FIXES_COMPLETED.md
│   │   └── WORKER_UPDATE_SUMMARY_REPORT.md
│   │
│   ├── architecture/          # System Architecture
│   │   ├── START_HERE.md     ⭐ PROJECT ENTRY POINT
│   │   ├── ARCHITECTURE.md
│   │   ├── PROJECT_STRUCTURE.md
│   │   ├── HOW_IT_WORKS.md
│   │   ├── DATA_UPDATE_PLAN.md
│   │   ├── COMPLETE_DATA_CAPTURE_GUIDE.md
│   │   ├── ML_DATA_PIPELINE.md
│   │   ├── METADATA_TRACKING_SETUP.md
│   │   ├── GETTING_STARTED.md
│   │   ├── QUICKSTART.md
│   │   └── IDIOTS_GUIDE.md
│   │
│   ├── deployment/            # Deployment Guides
│   │   ├── DEPLOYMENT_TESTING.md
│   │   ├── README_DEPLOYMENT_TESTS.md
│   │   ├── RENDER_DEPLOYMENT.md
│   │   └── DEPLOYMENT.md
│   │
│   ├── audit/                 # Database Audits
│   │   ├── AUDIT_EXECUTIVE_SUMMARY.md
│   │   ├── COMPREHENSIVE_AUDIT_REPORT.md
│   │   ├── AUDIT_EXECUTIVE_SUMMARY_FINAL.md
│   │   ├── DATABASE_AUDIT_REPORT.md
│   │   ├── DATABASE_SCHEMA_AUDIT_DETAILED.md
│   │   ├── DATABASE_COVERAGE_SUMMARY.md
│   │   ├── DATA_GAP_ANALYSIS.md
│   │   ├── COMPLETE_DATABASE_OPTIMIZATION_SUMMARY.md
│   │   ├── SCHEMA_OPTIMIZATION_REPORT.md
│   │   ├── RATINGS_COVERAGE_ANALYSIS.md
│   │   ├── RATINGS_OPTIMIZATION_SUMMARY.md
│   │   └── REMAINING_TABLES_AUDIT.md
│   │
│   ├── _deprecated/           # Superseded Documentation
│   │   ├── CORRECTED_HORSE_STRATEGY.md
│   │   ├── HYBRID_WORKER_STRATEGY.md
│   │   ├── CODE_CLEANUP_COMPLETED.md
│   │   ├── POSITION_DATA_PIPELINE_FIX.md
│   │   ├── POSITION_DATA_STATUS.md
│   │   ├── APPLY_POSITION_FIX_NOW.md
│   │   └── QUICK_FIX_CHECKLIST.md
│   │
│   └── PROJECT_CLEANUP_REPORT.md  ⭐ THIS CLEANUP SUMMARY
│
├── _deprecated/                # Deprecated Code (ARCHIVED)
│   ├── code/                  # Deprecated code files
│   ├── scripts/               # Deprecated scripts (14 files)
│   │   ├── api_field_comparison.py
│   │   ├── apply_migration.py
│   │   ├── apply_migration_supabase.py
│   │   ├── backfill_horse_pedigree_old.py
│   │   ├── database_audit.py
│   │   ├── database_audit_scripts.py
│   │   ├── database_audit_simple.py
│   │   ├── fetch_sample_results.py
│   │   ├── initialize_data.py
│   │   ├── verify_all_fetchers.py
│   │   └── [historical scripts...]
│   └── tests/                 # Deprecated test files (3 files)
│       ├── test_hybrid_horses_fetcher.py
│       ├── test_position_extraction.py
│       └── test_results_fetcher_enrichment.py
│
├── logs/                       # Log Files (gitignored)
│
├── main.py                    ⭐ MAIN ORCHESTRATOR
├── start_worker.py            ⭐ WORKER ENTRY POINT
│
├── .env                       # Environment variables (gitignored)
├── .env.example               # Environment template
├── .gitignore
├── requirements.txt
├── README.md                  # Project overview
└── PROJECT_STRUCTURE.md       # This file
```

---

## Key Files

### Entry Points
- **`main.py`** - Main orchestrator for scheduled data fetching
- **`start_worker.py`** - Worker entry point for continuous operations

### Configuration
- **`config/config.py`** - Central configuration management
- **`.env`** - Environment variables (not in repo)

### Active Scripts
- **`scripts/backfill_horse_pedigree_enhanced.py`** - Current backfill implementation
- **`scripts/monitor_backfill.py`** - Backfill progress monitoring
- **`scripts/comprehensive_api_test.py`** - API endpoint testing

### Documentation
- **`docs/README.md`** - Master documentation index (START HERE)
- **`docs/architecture/START_HERE.md`** - Project entry point
- **`docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`** - Enrichment strategy

---

## File Counts

| Category | Count | Location |
|----------|-------|----------|
| **Active Code** |
| Root Python files | 2 | `/` |
| Fetchers | 8 | `/fetchers/` |
| Utilities | 5 | `/utils/` |
| Active Scripts | 17 | `/scripts/` |
| Test Files | 14 | `/tests/` |
| Monitors | 8 | `/monitors/` |
| Migrations | 9 | `/migrations/` |
| **Documentation** |
| API Docs | 12 | `/docs/api/` |
| Enrichment Docs | 6 | `/docs/enrichment/` |
| Backfill Docs | 2 | `/docs/backfill/` |
| Worker Docs | 4 | `/docs/workers/` |
| Architecture Docs | 11 | `/docs/architecture/` |
| Deployment Docs | 4 | `/docs/deployment/` |
| Audit Docs | 13 | `/docs/audit/` |
| **Deprecated** |
| Deprecated Scripts | 14 | `/_deprecated/scripts/` |
| Deprecated Tests | 3 | `/_deprecated/tests/` |
| Deprecated Docs | 7 | `/docs/_deprecated/` |

---

## Database Tables

### Reference Tables (ra_*)
- `ra_courses` - Racing venues (UK & Ireland)
- `ra_bookmakers` - Bookmakers
- `ra_jockeys` - Jockey profiles
- `ra_trainers` - Trainer profiles
- `ra_owners` - Owner profiles
- `ra_horses` - Horse profiles (with enrichment)
- `ra_horse_pedigree` - Horse pedigree data

### Race Data Tables
- `ra_races` - Race cards
- `ra_runners` - Race runners (entries)
- `ra_results` - Race results

### System Tables
- `ra_metadata_tracking` - Metadata tracking
- `ra_ml_runner_history` - ML data history

---

## Common Commands

### Run Main Worker
```bash
python3 main.py --all
python3 main.py --daily
```

### Run Backfill
```bash
python3 scripts/backfill_horse_pedigree_enhanced.py
```

### Monitor Progress
```bash
python3 scripts/monitor_backfill.py
```

### Test API
```bash
python3 scripts/comprehensive_api_test.py
```

### Validate Data
```bash
python3 scripts/validate_data_completeness.py
```

---

## Navigation Tips

### I want to...

**Get started with the project**
→ Read `docs/README.md` then `docs/architecture/START_HERE.md`

**Understand the API**
→ Read `docs/api/API_QUICK_REFERENCE.md`

**Learn about enrichment**
→ Read `docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`

**Deploy the system**
→ Read `docs/deployment/DEPLOYMENT_TESTING.md`

**Check database schema**
→ Read `docs/audit/DATABASE_SCHEMA_AUDIT_DETAILED.md`

**Run a backfill**
→ Read `docs/backfill/BACKFILL_EXECUTION_SUMMARY.md`

**Find a specific file**
→ Check this document or `docs/README.md`

---

## Related Repositories

- **[DarkHorses-Odds-Workers](https://github.com/mattbarb/DarkHorses-Odds-Workers)** - Live & historical odds collection
- **[DarkHorses-AI-Engine](https://github.com/mattbarb/DarkHorses-AI-Engine)** - ML prediction engine

---

## Cleanup Status

Last major cleanup: **2025-10-15**

See `docs/PROJECT_CLEANUP_REPORT.md` for details on:
- Files moved to `_deprecated/`
- Documentation reorganization
- Structure improvements

---

**Structure Version:** 2.0
**Last Updated:** 2025-10-15
**Status:** Clean and Organized ✅
