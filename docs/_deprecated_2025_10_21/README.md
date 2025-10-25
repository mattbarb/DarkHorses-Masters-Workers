# Deprecated Documentation - 2025-10-21

**Date Deprecated:** 2025-10-21
**Reason:** Major documentation cleanup and reorganization
**Files Moved:** 102 documentation files

---

## Why These Files Were Deprecated

As part of a comprehensive documentation cleanup, we consolidated and organized the documentation structure:

### What Replaced These Files

**Canonical References (Current Documentation):**

1. **`/DATA_SOURCE_STRATEGY.md`** - CANONICAL data source reference
   - Replaces: Multiple scattered docs about data sources, API endpoints, table population
   - Definitive guide for what data comes from where

2. **`/fetchers/`** directory - Complete fetcher documentation
   - `README.md` - Complete fetcher system guide
   - `CONTROLLER_QUICK_START.md` - Master controller usage
   - `TABLE_TO_SCRIPT_MAPPING.md` - Table-to-script reference
   - `FETCHERS_INDEX.md` - Quick navigation
   - `COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md` - Implementation summary

3. **`/docs/README.md`** - Master documentation index
   - Updated with clear navigation to all current docs

4. **`/docs/CLAUDE.md`** - Updated AI assistant guidance
   - Completely rewritten with correct data flow
   - References canonical documentation

5. **Organized Subdirectories:**
   - `/docs/api/` - API documentation
   - `/docs/api_reference/` - ML API references
   - `/docs/architecture/` - System architecture
   - `/docs/audit/` - Database audits
   - `/docs/backfill/` - Backfill operations
   - `/docs/enrichment/` - Data enrichment
   - `/docs/workers/` - Worker system
   - `/docs/deployment/` - Deployment guides

---

## Files in This Directory

This directory contains **102 deprecated documentation files** from the `/docs` root directory.

### Categories of Deprecated Files

#### Fetcher-Related (Now in `/fetchers/`)
- Multiple FETCHER_*.md files
- Table mapping documents
- Column audit reports
- Architecture proposals

#### Audit Reports (Superseded)
- Multiple AUDIT_*.md files
- Database audit reports
- Schema analysis documents
- Coverage reports

#### Backfill Documentation (Superseded)
- Multiple BACKFILL_*.md files
- Strategy documents
- Timeline estimates
- Implementation reports

#### Statistics Implementation (Superseded)
- Multiple STATISTICS_*.md files
- Implementation reports
- Field mappings
- Worker integration docs

#### Data Analysis (Superseded)
- Gap analysis reports
- Standardization documents
- Quality audit reports
- Schema cleanup reports

#### General Implementation Reports (Historical)
- Multiple IMPLEMENTATION_*.md files
- Completion summaries
- Status reports
- Refactoring documentation

---

## How to Use Deprecated Files

**For Reference Only:**
These files are preserved for historical context but should NOT be used for current development.

**If You Need Information:**
1. Check the canonical references first (listed above)
2. Check organized subdirectories in `/docs`
3. Only refer to these deprecated files for historical context

**If You Find Useful Information Here:**
- Check if it's already in canonical docs
- If not, consider updating canonical docs rather than using these files

---

## Migration Guide

**Old Documentation → New Documentation**

| Old Location | New Location | Notes |
|--------------|--------------|-------|
| `docs/FETCHER_*.md` | `/fetchers/` directory | Complete fetcher documentation now consolidated |
| `docs/TABLE_*.md` | `/fetchers/TABLE_TO_SCRIPT_MAPPING.md` | Definitive table-to-script reference |
| `docs/AUDIT_*.md` | `/docs/audit/` subdirectory | Organized audit reports |
| `docs/BACKFILL_*.md` | `/docs/backfill/` subdirectory | Organized backfill docs |
| `docs/STATISTICS_*.md` | `/docs/COMPLETE_DATA_FILLING_SUMMARY.md` | Consolidated statistics guide |
| `docs/*_IMPLEMENTATION_*.md` | `/DATA_SOURCE_STRATEGY.md` + `/fetchers/` | Canonical implementation references |
| `docs/*_SUMMARY.md` | Canonical docs + organized subdirs | Consolidated summaries |

---

## Complete File List

Below is the complete list of 102 files moved to this directory:

```
$(ls -1 /Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/_deprecated_2025_10_21/ | grep -v README.md | head -102)
```

---

## Cleanup Rationale

**Problems with Old Structure:**
- 100+ files in docs root (overwhelming)
- Duplicate/overlapping information
- Unclear which docs were current
- No clear hierarchy
- Multiple "final" and "complete" summaries

**New Structure Benefits:**
- Clear canonical references
- Organized subdirectories by topic
- Only 6 files in docs root (essential references)
- Clear documentation hierarchy
- No ambiguity about current vs deprecated

---

## Future Deprecation

This directory uses date stamping (`_deprecated_2025_10_21`) to track when files were deprecated.

Future deprecations should:
1. Create new dated directory (e.g., `_deprecated_2025_11_15`)
2. Create README explaining what was deprecated and why
3. Update canonical references as needed

---

## Questions?

**Need current documentation?**
- Start at `/docs/README.md`
- Or `/DATA_SOURCE_STRATEGY.md` for data source info
- Or `/fetchers/README.md` for fetcher system info

**Need historical context?**
- Files in this directory are preserved for reference
- But check canonical docs first!

---

**Deprecation Date:** 2025-10-21
**Deprecated By:** Documentation cleanup and reorganization
**Status:** Preserved for historical reference only
**Use:** Reference only - DO NOT use for current development
