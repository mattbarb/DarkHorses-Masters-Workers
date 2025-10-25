# Database Audit - Master Index

**Generated:** 2025-10-20
**Database:** DarkHorses Masters Workers (Supabase PostgreSQL)
**Scope:** ALL 625 columns across 24 ra_* tables

---

## Quick Navigation

**Need a 5-minute overview?** → [Quick Reference](DATA_AUDIT_QUICK_REF.md)
**Want detailed findings?** → [Complete Guide](COMPLETE_DATA_FILLING_GUIDE.md)
**Need raw data for analysis?** → [JSON Audit](COMPLETE_DATABASE_AUDIT.json)
**Want executive summary?** → [Summary Report](DATABASE_AUDIT_SUMMARY.md)
**Need action plan?** → [Action Plan](DATA_GAPS_ACTION_PLAN.md)

---

## Document Guide

### 1. COMPLETE_DATABASE_AUDIT.json (209 KB)
**Purpose:** Raw audit data - every column analyzed
**Contains:**
- 625 columns across 24 tables
- Population percentages for each column
- NULL counts, empty string counts
- Data source classification
- Date range analysis

**Use when:**
- Building automated tools
- Creating custom reports
- Deep data analysis

**Structure:**
```json
{
  "audit_date": "2025-10-20 23:02:47",
  "summary": {
    "total_tables": 24,
    "total_columns": 625,
    "columns_100_pct": 189,
    "columns_with_gaps": 436
  },
  "date_ranges": {
    "ra_races": {
      "min_date": "2015-01-01",
      "max_date": "2025-10-19",
      "date_span_years": 10.8,
      "total_records": 136960
    }
  },
  "data_source_summary": {
    "columns_by_source": {
      "Calculated from database": 208,
      "Racing API (racecards/results)": 125,
      "Not implemented - future feature": 93
    }
  },
  "tables": [
    {
      "table_name": "ra_races",
      "total_records": 136960,
      "columns": [
        {
          "name": "id",
          "type": "varchar(50)",
          "pct_populated": 100.0,
          "data_source": "System-generated"
        }
      ]
    }
  ]
}
```

---

### 2. COMPLETE_DATA_FILLING_GUIDE.md (42 KB)
**Purpose:** Comprehensive guide to filling ALL data gaps
**Contains:**
- Data source breakdown (12 categories)
- Specific gap details for each column
- How-to instructions for filling each gap
- Priority action plan (P0 through P3)
- Verification queries
- Status by table

**Use when:**
- Planning data backfill operations
- Understanding where data comes from
- Troubleshooting missing data
- Implementing fixes

**Key Sections:**
1. **Data Sources Breakdown** - Where each column's data comes from
2. **Priority Action Plan** - What to fix first (P0 → P3)
3. **Data Completeness by Table** - Status of each table
4. **Verification Queries** - SQL to check progress

---

### 3. DATA_AUDIT_QUICK_REF.md (6.2 KB)
**Purpose:** Quick reference card - 5 minute read
**Contains:**
- At-a-glance metrics
- Critical issues (top 4)
- Data by category (well populated, needs attention, not implemented)
- Top 10 missing data by volume
- Immediate action checklist

**Use when:**
- Need quick status update
- Showing executives/stakeholders
- Daily standup reference
- Quick decision making

**Key Metrics:**
```
Total Columns: 625
- 189 (30.2%) Fully Populated ✅
- 49 (7.8%) Mostly Populated (90-99%) 🟢
- 68 (10.9%) Partially Populated (1-89%) 🟡
- 319 (51.0%) Empty ❌
```

---

### 4. DATABASE_AUDIT_SUMMARY.md (13 KB)
**Purpose:** Executive summary with analysis
**Contains:**
- Overview and scope
- Key findings
- Critical gaps
- Data quality assessment
- Recommendations

**Use when:**
- Need comprehensive analysis
- Writing status reports
- Strategic planning
- Understanding overall health

---

### 5. DATA_GAPS_ACTION_PLAN.md (14 KB)
**Purpose:** Prioritized action items with commands
**Contains:**
- Priority 0 (critical - do today)
- Priority 1 (high - this week)
- Priority 2 (medium - this month)
- Priority 3 (low - as needed)
- Ready-to-run SQL scripts
- Bash commands for each action

**Use when:**
- Ready to start fixing gaps
- Need specific commands
- Sprint planning
- Task assignment

---

## At-a-Glance Status

### Overall Health: B-

**Strengths:**
- ✅ Core master data: 95-100% complete
- ✅ Pre-race runner data: 95-100% complete
- ✅ 10.8 years of historical data (2015-2025)
- ✅ Complete pedigree lineage (99.93%)

**Critical Gaps:**
- 🚨 Enhanced runner fields: 0% (7 fields × 1.3M runners)
- 🚨 Course coordinates: 0% (2 fields × 101 courses)
- 🚨 Pedigree statistics: 0% (117 columns × 53K entities)
- ⚠️ Horse metadata: Gaps in age, breeder, colour_code, region
- ⚠️ Results coverage: Only 8-9% (investigate if expected)

---

## Data Timeline

**Primary Data (10.8 years):**
- **Races:** 2015-01-01 to 2025-10-19 (136,960 records)
- **Runners:** 2015-01-01 to 2025-10-19 (1,326,595 records)
- **Odds Historical:** 2015-01-01 to 2025-10-19 (2,434,732 records)

**Reference Data (Complete):**
- **Courses:** 101 records (100% complete except coordinates)
- **Bookmakers:** 22 records (100% complete)
- **Regions:** 14 records (100% complete)

**Master Entities:**
- **Horses:** 111,669 (99.87% core data, gaps in age/breeder)
- **Jockeys:** 3,483 (99.08% with statistics)
- **Trainers:** 2,781 (99.71% with statistics)
- **Owners:** 48,168 (99.89% with statistics)
- **Sires:** 2,143 (99.95% with names, 0% statistics)
- **Dams:** 48,372 (100% with names, 0% statistics)
- **Damsires:** 3,041 (99.97% with names, 0% statistics)

**Pedigree Data (Recent):**
- **Lineage:** 2025-10-14 to 2025-10-20 (111,594 records, 99.93% complete)

---

## Top 5 Critical Issues

### 1. Pedigree Statistics - 117 Columns at 0%
**Impact:** 53,556 entities × 39 statistics = 2.1M missing values
**Cause:** Script has schema bug (references non-existent column)
**Fix:** Update `scripts/populate_pedigree_statistics.py` to use correct JOIN
**Priority:** P0 - Critical
**Duration:** 30-60 minutes once fixed

### 2. Enhanced Runner Fields - 7 Columns at 0%
**Impact:** 1,326,595 runners × 7 fields = 9.3M missing values
**Cause:** Migration 011 added columns but fetchers not capturing data
**Fix:** Update field mapping in fetchers/results_fetcher.py
**Priority:** P0 - Critical
**Duration:** Code fix + backfill (if needed)

### 3. Course Coordinates - 2 Columns at 0%
**Impact:** 101 courses × 2 fields = 202 missing values
**Cause:** Migration not applied
**Fix:** Run migration 021 + populate script
**Priority:** P0 - Critical
**Duration:** < 5 minutes

### 4. Horse Metadata Gaps
**Impact:**
- age: 111,669 missing (simple calculation)
- breeder: 111,669 missing (data exists in pedigree table)
- colour_code: 84,613 missing (24% vs expected 100%)
- region: 79,553 missing (29% vs expected higher)

**Cause:** Not calculated (age), not migrated (breeder), API/mapping issue (colour_code, region)
**Fix:** SQL UPDATE for age/breeder, investigate API for colour_code/region
**Priority:** P1 - High
**Duration:** Minutes for SQL, investigation needed for others

### 5. Results Coverage Low (8-9%)
**Impact:** Potentially 1.2M runners missing result data
**Cause:** Unknown - could be expected (future races) or incomplete backfill
**Fix:** Investigate race date distribution, run backfill if needed
**Priority:** P1 - High
**Duration:** Investigation + potential multi-day backfill

---

## Data Source Summary

**625 total columns sourced from:**

| Source | Columns | With Gaps | Complete |
|--------|---------|-----------|----------|
| Calculated from database | 208 | 169 | 39 |
| Racing API (racecards/results) | 125 | 99 | 26 |
| Not implemented (future) | 93 | 93 | 0 |
| Odds worker system | 93 | 30 | 63 |
| System-generated | 56 | 17 | 39 |
| Racing API (enrichment) | 18 | 11 | 7 |
| Racing API (reference) | 9 | 0 | 9 |
| Racing API (results only) | 9 | 9 | 0 |
| Extracted from races | 6 | 2 | 4 |
| Unknown - investigate | 3 | 3 | 0 |
| Racing API (other) | 3 | 1 | 2 |
| External (geocoding) | 2 | 2 | 0 |

**Total:** 625 columns (189 complete, 436 with gaps)

---

## Quick Start

### I need to understand the overall situation
**Read:** [Quick Reference](DATA_AUDIT_QUICK_REF.md) (5 min)
**Then:** [Summary Report](DATABASE_AUDIT_SUMMARY.md) (10 min)

### I need to fix data gaps
**Read:** [Complete Guide](COMPLETE_DATA_FILLING_GUIDE.md) (comprehensive)
**Then:** [Action Plan](DATA_GAPS_ACTION_PLAN.md) (specific commands)

### I need raw data for analysis
**Use:** [JSON Audit](COMPLETE_DATABASE_AUDIT.json) (import into tools)

### I need to report status to stakeholders
**Use:** [Quick Reference](DATA_AUDIT_QUICK_REF.md) (metrics)
**And:** [Summary Report](DATABASE_AUDIT_SUMMARY.md) (analysis)

---

## Verification Commands

### Check if audit is up to date
```bash
# Audit date should be recent
cat docs/COMPLETE_DATABASE_AUDIT.json | grep -A 1 "audit_date"
```

### Re-run audit
```bash
# Full re-audit of all 625 columns (takes ~5 minutes)
python3 << 'EOF'
# (See COMPLETE_DATABASE_AUDIT.json generation script)
EOF
```

### Quick status check
```bash
# Check key metrics
PGPASSWORD='R0pMr1L58WH3hUkpVtPcwYnw' psql \
  -h aws-0-eu-west-2.pooler.supabase.com \
  -p 5432 \
  -U postgres.amsjvmlaknnvppxsgpfk \
  -d postgres \
  -c "
SELECT
  (SELECT COUNT(*) FROM ra_races) as races,
  (SELECT COUNT(*) FROM ra_runners) as runners,
  (SELECT COUNT(*) FROM ra_mst_horses) as horses,
  (SELECT MIN(date) || ' to ' || MAX(date) FROM ra_races) as date_range;
"
```

---

## Files Hierarchy

```
docs/
├── DATABASE_AUDIT_INDEX.md           ← YOU ARE HERE (master index)
├── COMPLETE_DATABASE_AUDIT.json      ← Raw audit data (209 KB)
├── COMPLETE_DATA_FILLING_GUIDE.md    ← Comprehensive guide (42 KB)
├── DATA_AUDIT_QUICK_REF.md           ← Quick reference (6.2 KB)
├── DATABASE_AUDIT_SUMMARY.md         ← Executive summary (13 KB)
└── DATA_GAPS_ACTION_PLAN.md          ← Prioritized actions (14 KB)
```

**Total:** 6 documents, ~290 KB documentation

---

## Related Documentation

**General:**
- `docs/README.md` - Master documentation index for entire project
- `CLAUDE.md` - Project overview for AI assistants

**Previous Completeness Work:**
- `COMPLETE_DATA_FILLING_SUMMARY.md` - Phase 1 & 2 summary (pedigree names/stats)
- `docs/COMPLETE_DATA_COMPLETENESS_PLAN.md` - Investigation & planning

**Statistics Implementation:**
- `scripts/statistics_workers/` - People statistics scripts (jockeys/trainers/owners)
- `scripts/populate_pedigree_statistics.py` - Pedigree statistics (needs fixing)

**Migrations:**
- `migrations/025_denormalize_pedigree_ids.sql` - Pedigree IDs (executed)
- `migrations/026_populate_pedigree_names.sql` - Pedigree names (executed)
- `migrations/021_add_course_coordinates.sql` - Coordinates (not yet applied)

---

## Audit Methodology

### Column Analysis
For each of 625 columns across 24 tables:
1. Count total records in table
2. Count NULL values
3. Count empty strings (for text fields)
4. Calculate populated count = not_null - empty_strings
5. Calculate percentage populated
6. Classify data source based on table/column patterns
7. Store in JSON with metadata

### Date Range Analysis
For tables with date/timestamp columns:
1. Find MIN and MAX dates
2. Calculate date span in years
3. Count total records
4. Store date range metadata

### Source Classification
Columns classified into 12 categories:
- System-generated (id, timestamps)
- Racing API (5 subcategories)
- Calculated from database
- Odds worker system
- External (geocoding)
- Not implemented (future features)
- Unknown - needs investigation

### Quality Grading
- **100%** = Fully populated ✅
- **90-99%** = Mostly populated 🟢
- **1-89%** = Partially populated 🟡
- **0%** = Empty ❌

---

## Change History

**2025-10-20:**
- ✅ Created comprehensive database audit (625 columns)
- ✅ Added data source classification
- ✅ Added date range analysis
- ✅ Created 6 documentation files
- ✅ Identified all critical gaps

**2025-10-20 (earlier):**
- ✅ Phase 1: Pedigree denormalization (migration 025)
- ✅ Phase 2: Pedigree names population (migration 026)
- ✅ People statistics calculation (jockeys/trainers/owners)

**Next:**
- Fix pedigree statistics script
- Investigate enhanced runner fields
- Apply course coordinates
- Fill horse metadata gaps

---

## Maintenance

**Recommended frequency:** Monthly audit

**Next audit:** 2025-11-20

**Focus areas for next audit:**
1. Pedigree statistics (should be 80-90% after fix)
2. Enhanced runner fields (should be 100% after fix)
3. Course coordinates (should be 100% after migration)
4. Results coverage (verify if improving with daily fetches)

**To update this audit:**
1. Re-run the audit script (generates fresh JSON)
2. Review and update guide if new gaps found
3. Update action plan priorities
4. Check off completed actions
5. Update this index

---

**Last Updated:** 2025-10-20
**Audit Version:** 1.0
**Tables Analyzed:** 24
**Columns Analyzed:** 625
**Documentation Files:** 6
**Overall Grade:** B-
