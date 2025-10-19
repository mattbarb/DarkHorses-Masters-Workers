# Monitoring Scripts

This folder contains all monitoring, health check, and data quality scripts.

## Scripts

### Progress Monitoring

**`monitor_progress_bars.py`** (Recommended)
- Clean year-by-year progress bars (2015-2025)
- Percentage completion per year
- Overall database status
- Auto-refreshes every 5 seconds

**`monitor_data_progress.py`** (Detailed)
- Comprehensive dashboard with all metrics
- Table counts, entity extraction rates
- Data quality indicators
- Recommendations
- Auto-refreshes every 2 seconds

### Health & Quality

**`health_check.py`**
- System health verification
- Database connection test
- API connectivity test
- Environment validation

**`data_quality_check.py`**
- Data validation and quality checks
- Missing data detection
- Data consistency verification

**`view_update_history.py`** ⭐ NEW
- View when tables were last updated
- Track number of records created/updated
- View complete update history
- Success rates and statistics
- Audit trail of all operations

## Usage

Run all scripts from the project root:

```bash
# From project root
python3 monitors/monitor_progress_bars.py
python3 monitors/monitor_data_progress.py
python3 monitors/health_check.py
python3 monitors/data_quality_check.py
python3 monitors/view_update_history.py              # View when tables were last updated
python3 monitors/view_update_history.py --table ra_results  # Detailed stats for specific table
```

Or from within the monitors/ folder:

```bash
# From monitors/ folder
cd monitors
python3 monitor_progress_bars.py
python3 monitor_data_progress.py
python3 health_check.py
python3 data_quality_check.py
python3 view_update_history.py
```

## Notes

- All monitoring scripts are non-invasive and safe to run anytime
- They do not modify data, only read and display it
- Press Ctrl+C to exit any running monitor (won't stop data collection)
