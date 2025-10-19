# Project Structure

**Last Updated:** 2025-10-06
**Organization:** Clean, logical folder structure

---

## 📁 Directory Layout

```
DarkHorses-Masters-Workers/
│
├── 📄 Core Scripts (Root)
│   ├── initialize_data.py          Main initialization (2015-2025)
│   ├── main.py                     Core orchestrator
│   ├── start_worker.py             Background worker starter
│   └── run_scheduled_updates.py    Update scheduler
│
├── 📊 monitors/
│   ├── README.md                   Monitoring scripts documentation
│   ├── monitor_progress_bars.py    Year-by-year progress bars ⭐
│   ├── monitor_data_progress.py    Comprehensive dashboard
│   ├── health_check.py             System health verification
│   └── data_quality_check.py       Data validation
│
├── 🛠️  management/
│   ├── README.md                   Management scripts documentation
│   └── cleanup_and_reset.py        Database cleanup/reset
│
├── 📜 scripts/
│   ├── update_daily_data.py        Daily updates
│   ├── update_live_data.py         Live updates (15 min)
│   └── update_reference_data.py    Monthly reference data
│
├── ⚙️  config/
│   └── config.py                   Configuration management
│
├── 🔧 fetchers/
│   ├── courses_fetcher.py          Courses data fetcher
│   ├── bookmakers_fetcher.py       Bookmakers data fetcher
│   ├── races_fetcher.py            Racecards fetcher
│   ├── results_fetcher.py          Results fetcher
│   └── ...                         Other fetchers
│
├── 🔨 utils/
│   ├── api_client.py               Racing API client
│   ├── supabase_client.py          Supabase database client
│   ├── logger.py                   Logging utilities
│   ├── entity_extractor.py         Entity extraction
│   └── regional_filter.py          UK/Ireland filtering
│
├── 📚 docs/
│   ├── GETTING_STARTED.md          Main comprehensive guide ⭐
│   └── racing_api_openapi.json     Full API specification
│
├── 🗄️  logs/
│   └── *.log                       Application logs
│
├── 🧪 tests/
│   └── *.py                        Test files
│
└── 📦 _deprecated/
    ├── docs/                       Old documentation (10 files)
    ├── scripts/                    Old scripts (4 files)
    ├── logs/                       Old logs (158 files)
    └── README.md                   Deprecation summary
```

---

## 🎯 Quick Reference

### Monitoring

```bash
# Year-by-year progress bars (recommended)
python3 monitors/monitor_progress_bars.py

# Comprehensive dashboard
python3 monitors/monitor_data_progress.py

# System health check
python3 monitors/health_check.py

# Data quality check
python3 monitors/data_quality_check.py

# View update history
python3 monitors/view_update_history.py
```

### Database Management

```bash
# Preview database state
python3 management/cleanup_and_reset.py

# Clean database (requires confirmation)
python3 management/cleanup_and_reset.py --confirm
```

### Data Collection

```bash
# Initial data collection (2015-2025)
python3 scripts/initialize_data.py

# Daily updates
python3 scripts/update_daily_data.py

# Live updates
python3 scripts/update_live_data.py
```

---

## 📝 Notes

### Folder Organization

**monitors/** - Read-only monitoring and health checks
**management/** - Database management (write operations)
**scripts/** - Scheduled update scripts
**config/** - Configuration
**fetchers/** - API data fetchers
**utils/** - Shared utilities

### Documentation

- **Main Guide**: `docs/GETTING_STARTED.md` - Complete setup and usage guide
- **Folder READMEs**: Each folder has its own README explaining contents
- **Project Overview**: `README.md` - High-level project description
- **Deployment**: `RENDER_DEPLOYMENT.md` - Production deployment guide

---

## 🔄 Recent Changes

**2025-10-06** - Project reorganization
- Created `monitors/` folder for all monitoring scripts
- Created `management/` folder for database management
- Added README.md to each folder
- Maintained backwards compatibility with wrapper scripts
- Consolidated documentation into single guide

---

For detailed usage instructions, see **[docs/GETTING_STARTED.md](docs/GETTING_STARTED.md)**
