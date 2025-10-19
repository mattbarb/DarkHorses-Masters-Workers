# ML Runner History - DEPRECATED

**Status:** Deprecated as of 2025-10-15
**Reason:** ML feature calculation moved to API-based approach (DarkHorses-AI-Engine project)

## What Was Here

This directory contains the deprecated ML runner history infrastructure:

### Files

1. **`compile_ml_data.py`** - Script that compiled ML-ready runner history
   - Calculated career statistics, form scores, relationship stats
   - Created denormalized records in `dh_ml_runner_history` table
   - Ran daily via scheduler

2. **`ml_data_monitor.py`** - Health check monitor for ML compilation
   - Monitored data freshness and coverage
   - Alerted on compilation failures

3. **`004_create_ml_runner_history.sql`** - Database migration
   - Created `dh_ml_runner_history` table
   - 90+ columns with pre-calculated features
   - Indexes and views for ML queries

4. **`ML_DATA_PIPELINE.md`** - Documentation
   - Explained ML compilation process
   - Usage examples and monitoring

## Why Deprecated

**Original Approach:**
- Pre-calculated all ML features daily
- Stored in denormalized `dh_ml_runner_history` table
- Required daily compilation job
- Fixed feature definitions

**New Approach (API-based):**
- ML features calculated on-demand via API
- Performed in DarkHorses-AI-Engine project
- More flexible - features can be customized per model
- Real-time calculations ensure fresh data
- Reduces database storage requirements
- Easier to version and update feature definitions
- Better separation of concerns (data storage vs ML logic)

## Migration Path

**Database:**
- The `dh_ml_runner_history` table can be dropped if it exists
- See migration: `migrations/drop_ml_runner_history.sql` (if created)
- All source data remains in `ra_*` tables

**Scheduler:**
- ML compilation removed from `config/scheduler_config.yaml`
- No longer runs daily

**API Reference:**
- Updated to reflect API-based approach
- See: `docs/api_reference/DATABASE_SCHEMA_ML_API_REFERENCE.md`

## Where ML Logic Went

**New Location:** DarkHorses-AI-Engine repository

**Responsibilities:**
- Feature calculation and caching
- Model training and versioning
- Prediction endpoints
- Performance optimization

**This Project (Masters-Workers) Now:**
- Focuses purely on data collection and storage
- Provides raw data via source tables (`ra_*`)
- Maintains data quality and enrichment (hybrid enrichment for horses)

## Historical Context

**When Active:** 2025-10-13 to 2025-10-15 (2 days)

**Why Short-Lived:**
- Initial implementation for ML feature compilation
- Quickly realized API approach was more flexible
- Architectural decision to separate ML logic from data collection

**What Was Learned:**
- Pre-calculating features is inflexible
- Database storage costs can be high for denormalized data
- Separation of concerns improves maintainability
- API-based calculations allow for better versioning

## For Reference

If you need to understand the old ML compilation logic, see:
- `compile_ml_data.py` - Complete feature calculation code
- `ML_DATA_PIPELINE.md` - Documentation of old approach
- `004_create_ml_runner_history.sql` - Table schema

**Do not use this code** - it's preserved for historical reference only.

---

**Deprecated:** 2025-10-15
**Superseded By:** DarkHorses-AI-Engine API project
