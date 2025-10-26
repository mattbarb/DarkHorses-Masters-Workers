# DarkHorses-Masters-Workers

**Production system for fetching and maintaining UK/Ireland horse racing reference data from The Racing API into Supabase PostgreSQL.**

## Quick Start

### Prerequisites
- Python 3.9+
- Racing API credentials (Pro plan recommended)
- Supabase PostgreSQL database

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/DarkHorses-Masters-Workers.git
cd DarkHorses-Masters-Workers

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env.local
# Edit .env.local with your credentials
```

### Environment Variables

```bash
# Racing API
RACING_API_USERNAME=your_username
RACING_API_PASSWORD=your_password

# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your_service_key
```

### Run Your First Fetch

```bash
# Fetch today's races and results
python3 main.py --daily

# Test mode (limited data)
python3 main.py --test --entities races
```

## Key Features

- **Hybrid Horse Enrichment**: Automatically captures complete pedigree data for newly discovered horses
- **Entity Extraction**: Discovers jockeys, trainers, owners from race data (no separate API calls needed)
- **Smart Rate Limiting**: Respects Racing API limits (2 req/sec) with automatic retries
- **Resume-Capable Backfill**: Large-scale historical data imports with checkpoint recovery
- **Regional Filtering**: UK (GB) and Ireland (IRE) only
- **Professional-Grade Code**: 92/100 system health score, comprehensive error handling

## Project Structure

```
DarkHorses-Masters-Workers/
├── config/              # Configuration management
├── fetchers/            # Data fetchers from Racing API (10 active fetchers)
│   ├── races_fetcher.py
│   ├── results_fetcher.py
│   ├── events_fetcher.py (consolidated)
│   ├── masters_fetcher.py (consolidated)
│   └── ...
├── utils/               # Core utilities
│   ├── entity_extractor.py  # Hybrid enrichment engine
│   ├── api_client.py         # Racing API client
│   └── supabase_client.py    # Database operations
├── scripts/             # Automation scripts (95 utilities)
│   ├── backfill_*.py
│   ├── populate_*.py
│   └── test_*.py
├── tests/               # Test suite
├── migrations/          # Database migrations (28 migrations)
├── docs/                # Comprehensive documentation (60+ files)
│   ├── README.md        # Documentation index
│   ├── audit/           # System audits
│   ├── reports/         # Cleanup and summary reports
│   └── ...
├── logs/                # Execution logs
├── main.py              # Production orchestrator
└── CLAUDE.md            # Claude Code instructions
```

## Documentation

**Start here:** [docs/README.md](docs/README.md) - Master documentation index

**Quick references:**
- [Getting Started](docs/architecture/START_HERE.md) - Architecture overview and first steps
- [API Guide](docs/api/API_COMPREHENSIVE_TEST_SUMMARY.md) - Racing API endpoint details
- [Hybrid Enrichment](docs/enrichment/HYBRID_ENRICHMENT_IMPLEMENTATION.md) - Automatic pedigree capture strategy
- [Backfill Operations](docs/backfill/BACKFILL_EXECUTION_SUMMARY.md) - Historical data import guide
- [Worker System](docs/workers/WORKER_UPDATE_REPORT.md) - Scheduled task management

**For Claude Code:** See [CLAUDE.md](CLAUDE.md) for project instructions and common patterns

## Database Schema

All tables use `ra_*` prefix (22 active tables):

**Reference Tables (9):**
- `ra_mst_courses`, `ra_mst_bookmakers`, `ra_mst_regions`
- `ra_mst_jockeys`, `ra_mst_trainers`, `ra_mst_owners`
- `ra_mst_horses` (with complete pedigree metadata)
- `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires` (calculated statistics)

**Transaction Tables (3):**
- `ra_mst_races` - Race metadata
- `ra_mst_runners` - Race entries with results (57 columns)
- `ra_mst_race_results` - Historical results archive

**Pedigree & Analytics (10):**
- `ra_horse_pedigree` - Complete lineage (sire, dam, damsire)
- `ra_entity_combinations` - Calculated combinations
- `ra_runner_statistics`, `ra_performance_by_distance`, `ra_performance_by_venue`
- Plus odds tables (ra_odds_live, ra_odds_historical)

## Common Operations

### Daily Operations (Production)

```bash
# Daily: Races and results
python3 main.py --daily

# Weekly: People and horses
python3 main.py --weekly

# Monthly: Courses and bookmakers
python3 main.py --monthly

# Full sync (all data)
python3 main.py --all
```

### Fetch Specific Entities

```bash
python3 main.py --entities races results
python3 main.py --entities horses --test  # Test mode
```

### Historical Backfill

```bash
# Horse pedigree enrichment (resume-capable)
python3 scripts/backfill_horse_pedigree_enhanced.py

# Monitor backfill progress
python3 scripts/monitor_backfill.py --interval 60

# Check if running
ps -p $(cat logs/backfill_pid.txt)
```

### Testing

```bash
# Comprehensive API testing
python3 scripts/comprehensive_api_test.py

# Hybrid enrichment validation
python3 scripts/test_hybrid_enrichment.py

# Enhanced data capture testing
python3 scripts/test_enhanced_data_capture.py
```

## Architecture Highlights

### Hybrid Enrichment Strategy

**Two-step approach for optimal performance:**

1. **Discovery Phase (Fast):**
   - Fetch racecards from `/v1/racecards/pro`
   - Extract basic horse data from runners
   - Discover 50-100 new horses daily

2. **Enrichment Phase (Complete Data):**
   - Check if horses are NEW (not in database)
   - For NEW horses only: Fetch complete data from `/v1/horses/{id}/pro`
   - Capture 9 additional fields including complete pedigree
   - Rate-limited: 2 req/sec (daily overhead ~27 seconds)

**Result:** Complete pedigree data for 111,000+ horses with minimal API usage.

### Data Flow

```
Racing API
    ↓
Fetchers (races, results, courses, etc.)
    ↓
Primary Tables (ra_mst_races, ra_mst_runners, ra_mst_*)
    ↓
Entity Extraction (AUTOMATIC)
    ├─ ra_mst_jockeys, trainers, owners
    └─ ra_mst_horses → Hybrid Enrichment
        ↓
        ra_horse_pedigree (complete lineage)
        ↓
Statistics Calculation (SECONDARY)
    └─ ra_mst_sires, dams, damsires (47 stats each)
```

## System Health

**Overall Grade:** A- (92/100) - Excellent
**Status:** Production-Ready
**Total Records:** 1,675,869 across 14 primary tables
**Code Quality:** Professional-grade
**Documentation:** Comprehensive (60+ files)

**Latest Audit:** [docs/audit/SYSTEM_AUDIT_COMPLETE.md](docs/audit/SYSTEM_AUDIT_COMPLETE.md)

## Performance

- **Database Size:** 1.67M records
- **Largest Tables:** ra_mst_runners (1.3M), ra_mst_races (137K), ra_mst_horses (112K)
- **Enrichment:** ~50-100 new horses/day, 0.5s per horse
- **API Rate Limit:** 2 req/sec (automatic throttling)
- **Batch Processing:** 100 records per batch (configurable)

## Recent Updates

**2025-10-23:**
- ✅ Fetchers directory cleanup (24 → 10 focused files)
- ✅ Deprecated fetchers moved to `_deprecated/`
- ✅ Updated package exports for consolidated fetchers

**2025-10-22:**
- ✅ Fixed ra_mst_race_results population
- ✅ Removed redundant tables (ra_runner_odds, ra_runner_supplementary)
- ✅ Comprehensive system audit (92/100 score)
- ✅ Database schema cleanup (24 → 22 tables)

See [docs/reports/SESSION_SUMMARY_2025_10_22.md](docs/reports/SESSION_SUMMARY_2025_10_22.md) for details.

## Deployment

**Production-ready for:**
- Render.com (see [docs/deployment/RENDER_DEPLOYMENT.md](docs/deployment/RENDER_DEPLOYMENT.md))
- Any Python 3.9+ environment

**Requirements:**
- Environment variables configured
- Scheduled tasks (daily/weekly/monthly)
- Monitoring for backfill operations
- Log rotation for `logs/` directory

## Troubleshooting

### Missing Pedigree Data
- Verify `api_client` passed to `EntityExtractor` in fetcher `__init__`
- Check environment variables are set
- Review enrichment stats in logs: `horses_enriched` should be > 0

### Rate Limit Errors
- Should auto-retry with exponential backoff
- Verify `rate_limit_per_second = 2` in api_client.py
- For backfills: Check `time.sleep(0.5)` between Pro endpoint calls

### Database Connection Issues
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_KEY`
- Check Supabase dashboard for connection limits
- Review batch size in config (default: 100)

## Related Repositories

- **DarkHorses-Odds-Workers:** Live & historical odds collection
- **DarkHorses-AI-Engine:** ML prediction engine

**Integration:** All systems read from the same Supabase database (`ra_*` tables).

## Contributing

1. Read [CLAUDE.md](CLAUDE.md) for development guidelines
2. Follow existing code patterns (see fetcher examples)
3. Add tests for new features
4. Update documentation

## License

[Your license here]

## Support

For comprehensive documentation and guides, see [docs/README.md](docs/README.md).

---

**Version:** Production Release v1.0
**Last Updated:** 2025-10-23
**System Status:** Production-Ready (92/100)
