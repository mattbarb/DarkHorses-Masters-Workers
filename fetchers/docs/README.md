# Fetchers Documentation Index

**Location:** `/fetchers/docs/`
**Purpose:** Complete documentation for the Racing API fetcher system

---

## 🎯 Start Here

**For Quick Start:**
1. **[CONTROLLER_QUICK_START.md](CONTROLLER_QUICK_START.md)** - Master controller usage guide (26 KB)
2. **[FETCHERS_INDEX.md](FETCHERS_INDEX.md)** - Quick navigation and complete data flow (10 KB)

**For Complete Reference:**
3. **[TABLE_TO_SCRIPT_MAPPING.md](TABLE_TO_SCRIPT_MAPPING.md)** - Definitive table-to-script mapping (17 KB)
4. **[COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md](COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md)** - Implementation guide (26 KB)

---

## 📊 Complete Data Reference

### Column Inventories (ALL 625+ Columns with Sources)

**JSON Format (Machine-Readable):**
- **[COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json](COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json)** - Complete inventory with:
  - All 24 ra_ tables
  - All 625+ columns
  - Data type for each column
  - Data source (API endpoint or calculation)
  - API field path
  - Implementation notes
  - Population statistics (populated/total/percentage)

**Markdown Format (Human-Readable):**
- **[COMPLETE_COLUMN_INVENTORY.md](COMPLETE_COLUMN_INVENTORY.md)** - Same data in readable markdown format

**Legacy JSON (Simplified):**
- **[TABLE_COLUMN_MAPPING.json](TABLE_COLUMN_MAPPING.json)** - Simplified column mapping (13.6 KB)

---

## 📁 File Descriptions

### 1. CONTROLLER_QUICK_START.md
**Size:** 26 KB
**Purpose:** Complete guide to using master_fetcher_controller.py

**Contents:**
- Interactive vs automated mode
- Built-in scheduling (daily/weekly/monthly)
- Command reference with examples
- Cron configuration
- Performance metrics
- Troubleshooting

**Use When:** You need to run the fetcher system

---

### 2. FETCHERS_INDEX.md
**Size:** 10 KB
**Purpose:** Quick navigation and complete data flow diagram

**Contents:**
- Complete data flow showing all 23 tables
- Phase 1: Racing API → 10 tables
- Phase 2: Database calculations → 3 tables
- Phase 3: Future/external → 10 tables
- Quick reference for each fetcher
- Table relationships

**Use When:** You need to understand the system architecture

---

### 3. TABLE_TO_SCRIPT_MAPPING.md
**Size:** 17 KB
**Purpose:** Definitive reference for which script populates which table

**Contents:**
- Table-by-table mapping to fetcher scripts
- Master tables (courses, bookmakers, people)
- Transaction tables (races, runners, results)
- Horse tables (horses, pedigree)
- Statistics tables (sires, dams, damsires)
- Future/TBD tables

**Use When:** You need to know which script handles a specific table

---

### 4. COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md
**Size:** 26 KB
**Purpose:** Comprehensive implementation guide and technical reference

**Contents:**
- Complete system architecture
- Fetcher-by-fetcher breakdown
- API endpoint mapping
- Regional filtering details
- Hybrid enrichment implementation
- Performance metrics
- Data flow diagrams

**Use When:** You need deep technical understanding or are modifying the system

---

### 5. TABLE_COLUMN_MAPPING.json
**Size:** 13.6 KB
**Purpose:** Simplified column mapping (legacy)

**Contents:**
- Table names
- Column lists
- Basic API endpoint mapping

**Use When:** You need quick column reference without full details

---

### 6. COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json
**Size:** Varies (comprehensive)
**Purpose:** **CANONICAL** - Complete inventory of all 625+ columns

**Contents:**
```json
{
  "generated": "2025-10-21 00:44:20",
  "total_tables": 24,
  "total_columns": 625,
  "columns": [
    {
      "table": "ra_mst_courses",
      "column": "course_id",
      "type": "character varying",
      "data_source": "Racing API - Courses Endpoint",
      "api_endpoint": "GET /v1/courses",
      "field_path": "courses[].id",
      "implementation_notes": "Primary key from Racing API",
      "populated": 101,
      "total": 101,
      "pct_populated": 100.0
    },
    ...
  ]
}
```

**Each Column Includes:**
- Table name
- Column name
- Data type
- Data source (specific API endpoint or calculation method)
- API field path
- Implementation notes
- Population statistics (how many rows have this field populated)

**Use When:**
- You need to know where ANY column comes from
- Building ML features (see data source and population stats)
- Understanding data completeness
- Planning new features
- Debugging missing data

---

### 7. COMPLETE_COLUMN_INVENTORY.md
**Size:** Varies (comprehensive)
**Purpose:** Human-readable version of column inventory

**Contents:**
- Same data as JSON version
- Formatted as markdown tables
- Table-by-table organization
- Easy to read and search

**Use When:**
- You prefer reading markdown over JSON
- You want to review column details without parsing JSON
- You need to share column information in documentation

---

## 🗂️ Documentation Organization

### By Use Case

**I need to run the fetchers:**
→ Start with **CONTROLLER_QUICK_START.md**

**I need to understand the system:**
→ Start with **FETCHERS_INDEX.md**

**I need to know which script handles a table:**
→ Use **TABLE_TO_SCRIPT_MAPPING.md**

**I need to know where a column comes from:**
→ Use **COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json** or **.md**

**I need complete technical details:**
→ Read **COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md**

---

## 📈 Statistics

### Coverage

**Tables Documented:** 24 ra_ tables
**Columns Documented:** 625+ columns
**Fetcher Scripts:** 8 fetchers
**API Endpoints:** 10+ endpoints documented

### Documentation Files

| File | Size | Type | Purpose |
|------|------|------|---------|
| CONTROLLER_QUICK_START.md | 26 KB | Guide | Controller usage |
| FETCHERS_INDEX.md | 10 KB | Reference | Quick navigation |
| TABLE_TO_SCRIPT_MAPPING.md | 17 KB | Reference | Table mapping |
| COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md | 26 KB | Guide | Implementation |
| TABLE_COLUMN_MAPPING.json | 13.6 KB | Data | Column mapping |
| COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json | Varies | Data | **CANONICAL** column inventory |
| COMPLETE_COLUMN_INVENTORY.md | Varies | Reference | Human-readable inventory |

---

## 🔄 Data Flow Summary

### Phase 1: Racing API → Database (10 tables)

```
Racing API → master_fetcher_controller.py → Individual Fetchers → Supabase
```

**Tables:** ra_mst_courses, ra_mst_bookmakers, ra_mst_regions, ra_mst_jockeys, ra_mst_trainers, ra_mst_owners, ra_mst_horses, ra_horse_pedigree, ra_mst_races, ra_mst_runners

**Scripts:**
- courses_fetcher.py
- bookmakers_fetcher.py
- jockeys_fetcher.py
- trainers_fetcher.py
- owners_fetcher.py
- races_fetcher.py (populates 5 tables)
- results_fetcher.py

### Phase 2: Database Calculations → Statistics (3 tables)

```
Database (horses + results) → populate_pedigree_statistics.py → Statistics Tables
```

**Tables:** ra_mst_sires, ra_mst_dams, ra_mst_damsires

**Scripts:**
- scripts/populate_pedigree_statistics.py

### Phase 3: Future/External Sources (10 tables)

**Tables:** ra_entity_combinations, ra_performance_by_distance, ra_performance_by_venue, ra_runner_statistics, ra_runner_supplementary, ra_odds_live, ra_odds_historical, ra_odds_statistics, ra_runner_odds, (1 more TBD)

**Status:** Not yet implemented

---

## 🔗 Related Documentation

**Parent Directory:**
- `/fetchers/README.md` - Main fetchers overview
- `/fetchers/master_fetcher_controller.py` - Primary tool

**Project Root:**
- `/DATA_SOURCE_STRATEGY.md` - CANONICAL data source reference
- `/CLAUDE.md` - AI assistant guide

**Main Docs:**
- `/docs/README.md` - Master documentation index
- `/docs/COMPLETE_DATA_FILLING_SUMMARY.md` - Statistics population guide
- `/docs/FETCHER_SCHEDULING_GUIDE.md` - Production scheduling

---

## 📝 Quick Reference

### Find Column Source

```bash
# Search JSON inventory
cat COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json | jq '.columns[] | select(.column=="column_name")'

# Search markdown inventory
grep -A 5 "column_name" COMPLETE_COLUMN_INVENTORY.md
```

### Find Table Information

```bash
# Get all columns for a table
cat COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json | jq '.columns[] | select(.table=="ra_mst_horses")'
```

### Count Columns

```bash
# Total columns
cat COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json | jq '.total_columns'

# Columns per table
cat COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json | jq '.columns[] | .table' | sort | uniq -c
```

---

## 🆕 Recent Updates

**2025-10-21:** Documentation reorganization
- Moved all fetcher docs to `/fetchers/docs/` subdirectory
- Created this index file
- Copied column inventory files from `/docs/` for easy access
- Updated parent README with documentation links

---

## 🎯 Key Principles

### 1. Single Source of Truth

**For Column Sources:** `COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json` is the CANONICAL reference
- All 625+ columns documented
- Every column has data source
- Population statistics included
- Regularly updated

### 2. Three-Phase Data Flow

**Phase 1:** Racing API (PRIMARY SOURCE)
- Get ALL raw data from Racing API first
- 10 tables populated directly

**Phase 2:** Database Calculations (SECONDARY SOURCE)
- Calculate statistics FROM the API data
- 3 statistics tables

**Phase 3:** External Sources (TERTIARY SOURCE)
- Future enhancements (odds, etc.)
- 10 tables planned

### 3. Documentation Hierarchy

**Quick Start** → CONTROLLER_QUICK_START.md
**Architecture** → FETCHERS_INDEX.md
**Reference** → TABLE_TO_SCRIPT_MAPPING.md
**Deep Dive** → COMPLETE_FETCHER_DATA_FILLING_SUMMARY.md
**Column Source** → COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json

---

**Documentation Version:** v2.0
**Last Updated:** 2025-10-21
**Maintainer:** DarkHorses-Masters-Workers Team
