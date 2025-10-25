# Deprecated Root Directory Files - 2025-10-21

**Date Deprecated:** 2025-10-21
**Reason:** Root directory cleanup - moved old audit scripts, test outputs, and summaries
**Files Moved:** 23 files

---

## Why These Files Were Deprecated

These files were in the project root directory but are no longer needed for current development:
- Old audit scripts that have been replaced by organized scripts in `/scripts/`
- Test output files from development/debugging sessions
- Old summary documents that are now documented elsewhere

---

## Files in This Directory

### Audit Scripts (9 files)
**Location:** `audit_scripts/`

Old audit and analysis scripts that were used during development:
- `audit_direct.py` - Direct database audit script
- `audit_schema.py` - Schema audit script
- `comprehensive_audit.py` - Comprehensive audit script
- `data_quality_audit.py` - Data quality audit script
- `deep_analysis_script.py` - Deep analysis script
- `focused_audit.py` - Focused audit script
- `quick_audit.py` - Quick audit script
- `runners_sample_audit.py` - Runners table audit script
- `simple_sample_audit.py` - Simple sample audit script

**Status:** Superseded by organized audit scripts in `/scripts/` directory

### Test Outputs (12 files)
**Location:** `test_outputs/`

Old test and audit output files from development:
- `audit_summary.json` - Old audit summary
- `data_quality_audit_report.json` - Old data quality report
- `data_quality_audit_results.json` - Old data quality results
- `deep_analysis_results.json` - Old deep analysis results
- `focused_audit_output.txt` - Old focused audit output
- `focused_audit_results.json` - Old focused audit results
- `runners_audit_output.txt` - Old runners audit output
- `simple_audit_results.json` - Old simple audit results
- `test_api_response.json` - Old API test response
- `test_dam_progeny_response.json` - Old dam progeny test
- `test_damsire_grandoffspring_response.json` - Old damsire test
- `test_pro_endpoints_output.txt` - Old pro endpoints test

**Status:** Historical output files, no longer needed

### Old Summaries (2 files)
**Location:** `old_summaries/`

Summary documents that are now documented elsewhere:
- `DOCUMENTATION_CLEANUP_SUMMARY.md` - Now in `/docs/_deprecated_2025_10_21/`
- `VALIDATION_SUMMARY.txt` - Old validation summary

**Status:** Information now in current documentation

---

## Root Directory After Cleanup

**Files Remaining (9 essential files):**
- `.env.local` - Configuration
- `.gitattributes` - Git config
- `.gitignore` - Git config
- `CLAUDE.md` - Canonical AI assistant guide
- `DATA_SOURCE_STRATEGY.md` - Canonical data source reference
- `main.py` - Main entry point
- `start_worker.py` - Worker entry point
- `requirements.txt` - Python dependencies
- `render.yaml` - Deployment configuration

**Before Cleanup:** 32 files in root
**After Cleanup:** 9 files in root (72% reduction)

---

## Migration Guide

**If you need audit/analysis functionality:**
- Check `/scripts/` directory for organized audit scripts
- Check `/docs/audit/` for audit documentation

**If you need test output information:**
- Check `/tests/` directory for current tests
- Check `/docs/api/` for API test summaries

**If you need summary information:**
- Check `/docs/README.md` for master documentation index
- Check `/docs/_deprecated_2025_10_21/` for documentation cleanup summary

---

**Deprecation Date:** 2025-10-21
**Deprecated By:** Root directory cleanup
**Status:** Preserved for historical reference only
**Use:** Reference only - DO NOT use for current development
