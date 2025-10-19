# DarkHorses Masters Workers - Documentation Index

Production-ready system for fetching and maintaining UK and Ireland racing reference/master data from The Racing API into Supabase PostgreSQL database.

## Quick Navigation

### Getting Started
- **[START HERE](architecture/START_HERE.md)** - Quick overview and entry point
- [Getting Started Guide](architecture/GETTING_STARTED.md) - Complete setup guide
- [Quick Start](architecture/QUICKSTART.md) - Rapid deployment
- [Idiots Guide](architecture/IDIOTS_GUIDE.md) - Simplified instructions

### Core Documentation by Topic

## ML API Reference (NEW)
**Location:** `docs/api_reference/`

- **[DATABASE SCHEMA ML API REFERENCE](api_reference/DATABASE_SCHEMA_ML_API_REFERENCE.md)** - **COMPREHENSIVE** database schema for ML API development
- [Field Quick Reference](api_reference/FIELD_QUICK_REFERENCE.md) - Condensed field lookup guide

**What's Inside:**
- Complete table schemas with all columns and data types
- Data source mappings (which API endpoints provide each field)
- Enrichment status (post-hybrid enrichment implementation)
- ML relevance ratings for each field
- Example queries for common ML operations
- Conceptual API endpoint designs

**Use This For:**
- Building ML prediction APIs
- Understanding which fields are available
- Designing feature extraction
- Planning database queries
- API development

## Racing API Documentation
**Location:** `docs/api/`

- **[API Comprehensive Test Summary](api/API_COMPREHENSIVE_TEST_SUMMARY.md)** - Complete API endpoint testing
- **[Jockey Data Enrichment Research](api/JOCKEY_DATA_ENRICHMENT_RESEARCH.md)** - Comprehensive jockey data source analysis (NEW)
- [Jockey Enrichment Quick Reference](api/JOCKEY_ENRICHMENT_QUICK_REFERENCE.md) - Quick jockey enrichment guide (NEW)
- [API Quick Reference](api/API_QUICK_REFERENCE.md) - Fast API lookup
- [API Cross Reference](api/API_CROSS_REFERENCE_ADDENDUM.md) - Endpoint relationships
- [Racing API Data Availability](api/RACING_API_DATA_AVAILABILITY.md) - What data is available
- [Data Sources for API](api/DATA_SOURCES_FOR_API.md) - API data mapping
- [Endpoint Validation Summary](api/ENDPOINT_VALIDATION_SUMMARY.md) - Validation results
- [App Fields Explanation](api/APP_FIELDS_EXPLANATION.md) - Field definitions

**Data Files:**
- `api_endpoint_test_results.json` - Detailed test results
- `entity_endpoint_test_results.json` - Entity endpoint tests
- `racing_api_openapi.json` - OpenAPI specification
- `api_endpoint_inventory.json` - Endpoint inventory

**Endpoint Validation Scripts:** `docs/api/endpoint_validation/`

## Enrichment & Data Quality
**Location:** `docs/enrichment/`

- **[Hybrid Enrichment Implementation](enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md)** - Main enrichment reference (CANONICAL)
- [Complete Enrichment Analysis](enrichment/COMPLETE_ENRICHMENT_ANALYSIS.md) - Detailed analysis
- [Enrichment Executive Summary](enrichment/ENRICHMENT_EXECUTIVE_SUMMARY.md) - High-level overview
- [Enrichment Quick Reference](enrichment/ENRICHMENT_QUICK_REFERENCE.md) - Quick lookup
- [Enrichment Architecture](enrichment/ENRICHMENT_ARCHITECTURE.md) - System design
- [Enrichment Index](enrichment/ENRICHMENT_INDEX.md) - Documentation navigation

**Key Concept:** The system uses a hybrid two-step approach to enrich horse data:
1. Discover horses from race data (fast)
2. Immediately enrich NEW horses with Pro endpoint (complete data including pedigree)

## Backfill Operations
**Location:** `docs/backfill/`

- **[Backfill Execution Summary](backfill/BACKFILL_EXECUTION_SUMMARY.md)** - Latest backfill status
- [Backfill Execution Report](backfill/BACKFILL_EXECUTION_REPORT.md) - Detailed backfill report

**Active Script:** `scripts/backfill_horse_pedigree_enhanced.py`

## Worker System
**Location:** `docs/workers/`

- **[Worker Update Report](workers/WORKER_UPDATE_REPORT.md)** - Latest worker changes
- [Worker Pedigree Capture Analysis](workers/WORKER_PEDIGREE_CAPTURE_ANALYSIS.md) - Pedigree capture strategy
- [Worker Fixes Completed](workers/WORKER_FIXES_COMPLETED.md) - Bug fixes log
- [Worker Update Summary Report](workers/WORKER_UPDATE_SUMMARY_REPORT.md) - Comprehensive update summary

## Architecture & Design
**Location:** `docs/architecture/`

- **[START HERE](architecture/START_HERE.md)** - Main entry point
- [Architecture](architecture/ARCHITECTURE.md) - System architecture
- [Project Structure](architecture/PROJECT_STRUCTURE.md) - File organization
- [How It Works](architecture/HOW_IT_WORKS.md) - System operations
- [Data Update Plan](architecture/DATA_UPDATE_PLAN.md) - Update strategy
- [Complete Data Capture Guide](architecture/COMPLETE_DATA_CAPTURE_GUIDE.md) - Data capture strategy
- [Metadata Tracking Setup](architecture/METADATA_TRACKING_SETUP.md) - Metadata system

## Deployment
**Location:** `docs/deployment/`

- **[Deployment Testing](deployment/DEPLOYMENT_TESTING.md)** - Deployment test procedures
- [Deployment Tests README](deployment/README_DEPLOYMENT_TESTS.md) - Test documentation
- [Render Deployment](deployment/RENDER_DEPLOYMENT.md) - Render.com deployment
- [Deployment Guide](deployment/DEPLOYMENT.md) - General deployment

## Database & Audit
**Location:** `docs/audit/`

- **[Audit Executive Summary](audit/AUDIT_EXECUTIVE_SUMMARY.md)** - Latest audit summary
- [Comprehensive Audit Report](audit/COMPREHENSIVE_AUDIT_REPORT.md) - Complete audit
- [Audit Executive Summary Final](audit/AUDIT_EXECUTIVE_SUMMARY_FINAL.md) - Final audit summary
- [Database Audit Report](audit/DATABASE_AUDIT_REPORT.md) - Database audit
- [Database Schema Audit Detailed](audit/DATABASE_SCHEMA_AUDIT_DETAILED.md) - Schema details
- [Database Coverage Summary](audit/DATABASE_COVERAGE_SUMMARY.md) - Coverage analysis
- [Data Gap Analysis](audit/DATA_GAP_ANALYSIS.md) - Data gaps identified
- [Complete Database Optimization Summary](audit/COMPLETE_DATABASE_OPTIMIZATION_SUMMARY.md) - Optimization work
- [Schema Optimization Report](audit/SCHEMA_OPTIMIZATION_REPORT.md) - Schema improvements
- [Ratings Coverage Analysis](audit/RATINGS_COVERAGE_ANALYSIS.md) - Ratings data coverage
- [Ratings Optimization Summary](audit/RATINGS_OPTIMIZATION_SUMMARY.md) - Ratings optimization
- [Remaining Tables Audit](audit/REMAINING_TABLES_AUDIT.md) - Unaudited tables
- `AUDIT_SUMMARY.txt` - Text summary

## Deprecated Documentation
**Location:** `docs/_deprecated/`

These documents have been superseded by newer implementations:
- [Corrected Horse Strategy](_deprecated/CORRECTED_HORSE_STRATEGY.md) - Superseded by HYBRID_ENRICHMENT_IMPLEMENTATION.md
- [Hybrid Worker Strategy](_deprecated/HYBRID_WORKER_STRATEGY.md) - Superseded by enrichment docs
- [Code Cleanup Completed](_deprecated/CODE_CLEANUP_COMPLETED.md) - Historical cleanup
- [Position Data Pipeline Fix](_deprecated/POSITION_DATA_PIPELINE_FIX.md) - Implemented
- [Position Data Status](_deprecated/POSITION_DATA_STATUS.md) - Resolved
- [Apply Position Fix Now](_deprecated/APPLY_POSITION_FIX_NOW.md) - Applied
- [Quick Fix Checklist](_deprecated/QUICK_FIX_CHECKLIST.md) - Completed

## Project Structure

```
DarkHorses-Masters-Workers/
├── config/              # Configuration management
├── fetchers/           # Data fetching modules
│   ├── courses_fetcher.py
│   ├── bookmakers_fetcher.py
│   ├── jockeys_fetcher.py
│   ├── trainers_fetcher.py
│   ├── owners_fetcher.py
│   ├── horses_fetcher.py
│   ├── races_fetcher.py
│   └── results_fetcher.py
├── utils/              # Utility modules
│   ├── api_client.py
│   ├── supabase_client.py
│   ├── entity_extractor.py
│   ├── metadata_tracker.py
│   └── regional_filter.py
├── scripts/            # Maintenance & backfill scripts
│   ├── backfill_horse_pedigree_enhanced.py (ACTIVE)
│   ├── monitor_backfill.py
│   ├── comprehensive_api_test.py
│   └── [other utility scripts]
├── tests/              # Test suite
│   ├── deployment/
│   └── [test files]
├── monitors/           # Monitoring tools
├── management/         # System management
├── migrations/         # Database migrations
├── docs/               # Documentation (YOU ARE HERE)
│   ├── README.md (THIS FILE)
│   ├── api/
│   ├── enrichment/
│   ├── backfill/
│   ├── workers/
│   ├── architecture/
│   ├── deployment/
│   ├── audit/
│   └── _deprecated/
├── _deprecated/        # Deprecated code
│   ├── code/
│   ├── scripts/
│   └── tests/
├── main.py             # Main orchestrator
└── start_worker.py     # Worker entry point
```

## Key Concepts

### Regional Filtering
All data is automatically filtered to include only UK (GB) and Ireland (IRE) racing.

### Hybrid Enrichment
The system uses a two-step approach for horse data:
1. **Discovery** - Fast bulk discovery from racecards
2. **Enrichment** - Complete data capture for NEW horses using Pro endpoint

This ensures all new horses have complete pedigree data immediately.

### Database Tables
Tables use `ra_` prefix (racing):
- `ra_courses`, `ra_bookmakers`, `ra_jockeys`, `ra_trainers`, `ra_owners`
- `ra_horses`, `ra_horse_pedigree`
- `ra_races`, `ra_runners`, `ra_results`
- `ra_metadata_tracking` (system metadata)

### Update Schedule
- **Daily:** Races and results
- **Weekly:** Jockeys, trainers, owners, horses
- **Monthly:** Courses and bookmakers
- **One-time:** Historical backfills

## Common Tasks

### View API Test Results
```bash
cat docs/api/api_endpoint_test_results.json | jq
```

### Run Backfill
```bash
python3 scripts/backfill_horse_pedigree_enhanced.py
```

### Monitor Backfill Progress
```bash
python3 scripts/monitor_backfill.py
```

### Check Data Quality
```bash
python3 scripts/validate_data_completeness.py
```

### Test API Endpoints
```bash
python3 scripts/comprehensive_api_test.py
```

## Finding Specific Information

### For API Questions
Start with: `docs/api/API_QUICK_REFERENCE.md`

### For Enrichment Strategy
Start with: `docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md`

### For Deployment
Start with: `docs/deployment/DEPLOYMENT_TESTING.md`

### For Database Issues
Start with: `docs/audit/AUDIT_EXECUTIVE_SUMMARY.md`

### For Worker Configuration
Start with: `docs/workers/WORKER_UPDATE_REPORT.md`

### For Getting Started
Start with: `docs/architecture/START_HERE.md`

## External Resources

- **Racing API:** https://theracingapi.com/docs
- **Supabase:** https://supabase.com/docs
- **GitHub (Masters Workers):** https://github.com/mattbarb/DarkHorses-Masters-Workers
- **GitHub (Odds Workers):** https://github.com/mattbarb/DarkHorses-Odds-Workers

## Maintenance

This documentation was reorganized on 2025-10-15 for improved navigation and clarity.

For project cleanup details, see: `docs/PROJECT_CLEANUP_REPORT.md` (when created)

## Related Repositories

- **[DarkHorses-Odds-Workers](https://github.com/mattbarb/DarkHorses-Odds-Workers)** - Live & historical odds collection
- **[DarkHorses-AI-Engine](https://github.com/mattbarb/DarkHorses-AI-Engine)** - ML prediction engine

## Version

Documentation Structure v2.0
Last Updated: 2025-10-15
System Version: Production Release v1.0
