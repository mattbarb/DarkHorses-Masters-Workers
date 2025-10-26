# Table Analysis Guide

**Script:** `fetchers/analyze_tables.py`
**Controller Mode:** `--mode analyze`
**Purpose:** Comprehensive data quality and completeness analysis for all ra_ tables

---

## Overview

The Table Analyzer performs deep analysis of all 23 ra_ tables to understand:

1. **Missing Data** - Columns with NULL values
2. **Partial Data** - Columns partially populated (% filled)
3. **Temporal Coverage** - Data from 2015 to present (yearly breakdown)
4. **Population Statistics** - Row counts and data quality metrics
5. **Data Quality Status** - Overall health assessment

---

## Quick Start

### Run from Controller (Recommended)

```bash
# Analyze all tables with interactive output
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive

# Analyze specific tables
python3 fetchers/master_fetcher_controller.py --mode analyze --tables ra_mst_races ra_mst_runners --interactive

# Automated run (JSON output only)
python3 fetchers/master_fetcher_controller.py --mode analyze
```

### Run Standalone

```bash
# Analyze all tables
python3 fetchers/analyze_tables.py

# Analyze specific tables
python3 fetchers/analyze_tables.py --tables ra_mst_races ra_mst_runners ra_mst_horses

# Export to JSON only
python3 fetchers/analyze_tables.py --output json

# Custom output filename
python3 fetchers/analyze_tables.py --output-file my_analysis.json
```

---

## What It Analyzes

### 1. Table-Level Metrics

**For Each Table:**
- Total rows
- Total columns
- Overall status (good/partial/needs_attention/empty/error)
- Summary statistics

**Example Output:**
```
📊 ra_mst_horses
   Status: GOOD
   Rows: 111,669
   Columns: 15
   Complete: 10, Good: 3, Partial: 1, Sparse: 0, Empty: 1
   Date Range: 2015-01-02 to 2024-12-31
   Coverage Years: 10 years (2015, 2016, 2017, ..., 2024)
```

### 2. Column-Level Analysis

**For Each Column:**
- Data type
- Populated count (non-NULL values)
- NULL count
- Total rows
- Percentage populated
- Status classification

**Column Status Categories:**
- **Complete (100%)** - All rows have data
- **Good (80-99%)** - Most rows have data
- **Partial (50-79%)** - About half have data
- **Sparse (<50%)** - Less than half have data
- **Empty (0%)** - No data

**Example:**
```json
{
  "column": "dob",
  "data_type": "date",
  "populated": 90234,
  "null_count": 21435,
  "total": 111669,
  "pct_populated": 80.8,
  "status": "good"
}
```

### 3. Temporal Coverage (Date-Based Tables)

**Analyzed for Tables with Date Fields:**
- `ra_mst_races` (using `off_dt`)
- `ra_mst_runners` (using `created_at`)
- `ra_mst_race_results` (using `created_at`)
- `ra_mst_horses` (using `created_at`)
- `ra_horse_pedigree` (using `created_at`)

**Metrics:**
- Min date (earliest record)
- Max date (latest record)
- Yearly counts (2015-2024)
- Total years with data
- Coverage years list

**Example:**
```json
{
  "min_date": "2015-01-02T00:00:00",
  "max_date": "2024-12-31T23:59:59",
  "yearly_counts": {
    "2015": 75234,
    "2016": 78901,
    "2017": 81234,
    ...
  },
  "total_years": 10,
  "coverage_years": [2015, 2016, 2017, ..., 2024]
}
```

---

## Output Formats

### 1. Interactive Console Output

**When using `--interactive` flag:**
- Real-time progress display
- Emoji status indicators (✅ ⚠️ ❌ 📭)
- Human-readable summaries
- Key findings highlighted

**Example:**
```
================================================================================
ANALYSIS SUMMARY
================================================================================

Total Tables Analyzed: 23
Total Rows: 13,234,567
Total Columns: 625

Tables by Status:
  ✅ GOOD: 14
  ⚠️  PARTIAL: 5
  ❌ NEEDS_ATTENTION: 2
  📭 EMPTY: 2

Column Status Totals:
  Complete Columns: 421
  Good Columns: 135
  Partial Columns: 45
  Sparse Columns: 18
  Empty Columns: 6
```

### 2. JSON Export

**Automatically saved to:** `logs/table_analysis_YYYYMMDD_HHMMSS.json`

**Structure:**
```json
{
  "analysis_date": "2024-01-15T10:30:00",
  "tables_analyzed": 23,
  "summary": {
    "total_tables": 23,
    "tables_by_status": {
      "good": 14,
      "partial": 5,
      "needs_attention": 2,
      "empty": 2
    },
    "total_rows": 13234567,
    "total_columns": 625,
    "column_status_totals": {
      "complete_columns": 421,
      "good_columns": 135,
      "partial_columns": 45,
      "sparse_columns": 18,
      "empty_columns": 6
    }
  },
  "tables": [
    {
      "table": "ra_mst_horses",
      "total_rows": 111669,
      "total_columns": 15,
      "status": "good",
      "columns": [...],
      "summary": {...},
      "temporal_coverage": {...},
      "analyzed_at": "2024-01-15T10:30:15"
    },
    ...
  ]
}
```

---

## Use Cases

### 1. Data Quality Audit

**Question:** "Which columns are missing data?"

**Command:**
```bash
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive
```

**Review:** Check "Sparse/Empty Columns" in output

### 2. Backfill Verification

**Question:** "Did the backfill populate all years from 2015?"

**Command:**
```bash
python3 fetchers/analyze_tables.py --tables ra_mst_races ra_mst_runners
```

**Review:** Check `temporal_coverage.coverage_years` in JSON output

### 3. Table Comparison

**Question:** "Which tables are most complete vs which need work?"

**Command:**
```bash
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive
```

**Review:** "Tables by Status" summary

### 4. Column Population Tracking

**Question:** "What percentage of horses have pedigree data?"

**Command:**
```bash
python3 fetchers/analyze_tables.py --tables ra_mst_horses ra_horse_pedigree
```

**Review:** Check column-level `pct_populated` for pedigree fields

### 5. Temporal Gaps

**Question:** "Are there any years missing data?"

**Command:**
```bash
python3 fetchers/analyze_tables.py --tables ra_mst_races --output json
```

**Review:** `temporal_coverage.yearly_counts` - look for years with 0 or low counts

---

## Understanding Results

### Table Status Levels

**✅ GOOD**
- 80%+ of columns are complete or good
- High data quality
- Ready for production use

**⚠️ PARTIAL**
- 50-80% of columns are complete/good
- Some data gaps
- May need enrichment

**❌ NEEDS_ATTENTION**
- <50% of columns are complete/good
- Significant data gaps
- Requires investigation

**📭 EMPTY**
- No data (0 rows) or all columns empty
- Table not yet populated
- May be future/TBD table

### Column Status Guide

| Status | % Populated | Meaning | Action |
|--------|-------------|---------|--------|
| Complete | 100% | All rows have data | ✅ Perfect |
| Good | 80-99% | Most rows have data | ✅ Acceptable |
| Partial | 50-79% | About half have data | ⚠️ Consider enrichment |
| Sparse | 1-49% | Less than half have data | ❌ Investigate source |
| Empty | 0% | No data | ❌ Not captured |

---

## Common Issues & Solutions

### Issue: Column Shows "Sparse" or "Empty"

**Possible Causes:**
1. Field not available in API response
2. Field only in Pro endpoint (enrichment required)
3. Fetcher not capturing field
4. Recent schema addition (historical data missing)

**Solutions:**
1. Check API documentation for field availability
2. Verify fetcher code captures the field
3. Run enrichment if field requires Pro endpoint
4. Backfill if field was recently added

### Issue: Temporal Gaps (Years Missing)

**Possible Causes:**
1. Backfill not run for those years
2. API doesn't have data for those years
3. Regional filtering excluded data

**Solutions:**
1. Run backfill for missing years
2. Check Racing API data availability
3. Verify regional filters (GB/IRE only)

### Issue: "Needs Attention" Table Status

**Investigation Steps:**
1. Review which columns are sparse/empty
2. Check if columns are critical for ML
3. Determine if enrichment needed
4. Plan data filling strategy

**Action:**
- See `/docs/COMPLETE_DATA_FILLING_SUMMARY.md` for enrichment strategies

---

## Analysis Schedule

### Recommended Frequency

**Weekly:**
- Quick analysis to monitor ongoing data capture
- Check for any sudden drops in population

**Monthly:**
- Full analysis of all tables
- Review temporal coverage
- Identify enrichment opportunities

**After Major Changes:**
- After schema migrations
- After backfill operations
- After fetcher updates
- After API endpoint changes

### Automated Monitoring

**Set up cron job:**
```bash
# Weekly analysis (Sundays at 3am)
0 3 * * 0 cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode analyze >> logs/weekly_analysis.log 2>&1
```

---

## Performance

### Execution Time

**Varies by table size:**
- Small tables (<1000 rows): <10 seconds
- Medium tables (1K-100K rows): 10-60 seconds
- Large tables (100K-1M rows): 1-5 minutes
- Very large tables (>1M rows): 5-15 minutes

**Full Analysis (All 23 Tables):**
- Estimated time: 15-30 minutes
- Depends on database performance
- Mostly I/O bound (database queries)

### Optimization Tips

1. **Analyze specific tables:**
   ```bash
   # Only analyze tables you need
   python3 fetchers/analyze_tables.py --tables ra_mst_races ra_mst_runners
   ```

2. **Skip temporal analysis for non-temporal tables:**
   - Temporal analysis only runs on tables with date fields
   - Automatically skipped for master tables

3. **Run during off-peak hours:**
   - Schedule for low-traffic times
   - Reduces impact on production database

---

## Integration with Other Tools

### With Master Controller

```bash
# Combined workflow: Backfill then analyze
python3 fetchers/master_fetcher_controller.py --mode backfill --interactive && \
python3 fetchers/master_fetcher_controller.py --mode analyze --interactive
```

### With Data Filling Scripts

```bash
# Fill missing data then analyze
python3 scripts/populate_pedigree_statistics.py && \
python3 fetchers/master_fetcher_controller.py --mode analyze --tables ra_mst_sires ra_mst_dams ra_mst_damsires
```

### With Monitoring

```bash
# Export analysis and check for issues
python3 fetchers/analyze_tables.py --output json && \
cat logs/table_analysis_*.json | jq '.tables[] | select(.status=="needs_attention")'
```

---

## Output Files

**Location:** `logs/`

**Naming Convention:** `table_analysis_YYYYMMDD_HHMMSS.json`

**Examples:**
- `logs/table_analysis_20241215_103045.json`
- `logs/table_analysis_20241216_020000.json`

**Retention:**
- Keep recent analyses for comparison
- Archive monthly summaries
- Delete analyses older than 90 days (optional)

---

## JSON Query Examples

### Find Empty Columns

```bash
cat logs/table_analysis_*.json | jq '.tables[].columns[] | select(.status=="empty") | {table: .table, column: .column}'
```

### Find Tables Needing Attention

```bash
cat logs/table_analysis_*.json | jq '.tables[] | select(.status=="needs_attention") | {table: .table, total_rows: .total_rows}'
```

### Get Temporal Coverage Summary

```bash
cat logs/table_analysis_*.json | jq '.tables[] | select(.temporal_coverage != null) | {table: .table, years: .temporal_coverage.total_years, coverage: .temporal_coverage.coverage_years}'
```

### Column Population Percentage

```bash
cat logs/table_analysis_*.json | jq '.tables[] | {table: .table, columns: [.columns[] | {column: .column, pct: .pct_populated}]}'
```

---

## Troubleshooting

### Error: "exec_sql RPC not available"

**Cause:** Schema query fallback needed

**Solution:** Already handled - script falls back to sample-based schema detection

### Error: "Permission denied"

**Cause:** Database credentials issue

**Solution:** Verify `.env.local` has correct `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`

### Warning: "Could not get count for year YYYY"

**Cause:** Date field format or filtering issue

**Solution:** Check date column exists and is properly formatted

### Very Slow Execution

**Cause:** Large tables or slow database

**Solutions:**
1. Analyze fewer tables at once
2. Check database connection
3. Run during off-peak hours
4. Consider database performance tuning

---

## Related Documentation

- **[CONTROLLER_QUICK_START.md](CONTROLLER_QUICK_START.md)** - Master controller usage
- **[TABLE_TO_SCRIPT_MAPPING.md](TABLE_TO_SCRIPT_MAPPING.md)** - Which fetcher populates which table
- **[COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json](COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json)** - All columns with sources
- **[/docs/COMPLETE_DATA_FILLING_SUMMARY.md](/docs/COMPLETE_DATA_FILLING_SUMMARY.md)** - Data enrichment strategies

---

## Version History

**v1.0 (2025-10-21)**
- Initial release
- Comprehensive table and column analysis
- Temporal coverage analysis
- JSON export
- Controller integration

---

**Last Updated:** 2025-10-21
**Maintainer:** DarkHorses-Masters-Workers Team
