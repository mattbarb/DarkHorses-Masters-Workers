# Statistics Calculation - Quick Start

**One-stop guide for populating ALL statistics from database**

## Quick Commands

### Test First (Recommended)
```bash
# Process 10 entities per worker (1-2 minutes)
python3 scripts/statistics_workers/populate_all_statistics.py --test
```

### Full Run
```bash
# Process ALL entities (30-60 minutes)
python3 scripts/statistics_workers/populate_all_statistics.py
```

### Resume If Interrupted
```bash
# Continue from last checkpoint
python3 scripts/statistics_workers/populate_all_statistics.py --resume
```

## What Gets Calculated

### Pedigree Statistics (Sires, Dams, Damsires)
- Own racing career (runs, wins, places, prize money, best/avg position, career dates)
- Offspring performance (progeny/grandoffspring counts, runs, wins, win rates)
- Stored in: `ra_sire_stats`, `ra_dam_stats`, `ra_damsire_stats`

### People Statistics (Jockeys, Trainers, Owners)
- Lifetime stats (total rides/runs, wins, places, win/place rates)
- Recent form (14-day and 30-day windows)
- Last activity dates (last ride/runner, last win, days since)
- Updated in: `ra_mst_jockeys`, `ra_mst_trainers`, `ra_mst_owners`

## Requirements

1. **Position data populated:**
   ```bash
   python3 main.py --entities results
   ```

2. **Pedigree data populated:**
   - Automatically populated by races/results fetcher
   - Check: `ra_rel_pedigree` table should have records

3. **Race dates available:**
   ```bash
   python3 main.py --entities races
   ```

## Expected Performance

| Worker | Entities | Duration |
|--------|----------|----------|
| Sires | ~5,000-10,000 | 10-15 min |
| Dams | ~10,000-20,000 | 10-15 min |
| Damsires | ~5,000-10,000 | 10-15 min |
| Jockeys | ~3,500 | 30-60 sec |
| Trainers | ~2,800 | 30-60 sec |
| Owners | ~48,000 | 5-10 min |
| **TOTAL** | **~80,000** | **30-60 min** |

## Troubleshooting

### No position data?
```bash
python3 main.py --entities results --days-back 365
```

### Worker timing out?
```bash
# Run workers individually
python3 scripts/statistics_workers/calculate_jockey_statistics.py
python3 scripts/statistics_workers/calculate_trainer_statistics.py
python3 scripts/statistics_workers/calculate_owner_statistics.py
python3 scripts/statistics_workers/calculate_sire_statistics.py
python3 scripts/statistics_workers/calculate_dam_statistics.py
python3 scripts/statistics_workers/calculate_damsire_statistics.py
```

### Resume not working?
- Check `logs/*_checkpoint.json` files exist
- Delete corrupted checkpoint and restart worker

## Validation

```bash
# Check populated statistics
python3 -c "
from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient

config = get_config()
db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

# Jockeys
jockeys = db.client.table('ra_mst_jockeys').select('total_rides, win_rate, last_ride_date').execute()
jockeys_with_stats = len([j for j in jockeys.data if j.get('total_rides')])
print(f'Jockeys with statistics: {jockeys_with_stats}/{len(jockeys.data)}')

# Sires
sires = db.client.table('ra_sire_stats').select('*', count='exact').limit(1).execute()
print(f'Sire statistics records: {sires.count:,}')
"
```

## Advanced Usage

### Run Specific Workers
```bash
# Only pedigree stats
python3 scripts/statistics_workers/populate_all_statistics.py --workers sires dams damsires

# Only people stats
python3 scripts/statistics_workers/populate_all_statistics.py --workers jockeys trainers owners
```

### Individual Workers
```bash
# Sires only
python3 scripts/statistics_workers/calculate_sire_statistics.py

# With limit (testing)
python3 scripts/statistics_workers/calculate_sire_statistics.py --limit 100

# Resume from checkpoint
python3 scripts/statistics_workers/calculate_sire_statistics.py --resume
```

## Daily Updates

For incremental updates (after results fetcher runs):

```bash
# Update people stats only (faster for daily use)
python3 scripts/statistics_workers/populate_all_statistics.py --workers jockeys trainers owners
```

**Duration:** 5-10 minutes (vs 30-60 minutes for full run)

## Full Documentation

See `STATISTICS_CALCULATION_GUIDE.md` for:
- Complete field definitions
- Data source details
- Architecture decisions
- Validation queries
- Integration patterns

---

**Quick checklist:**
1. ✓ Run test mode first
2. ✓ Verify results with validation script
3. ✓ Run full calculation
4. ✓ Add to daily schedule

**Time investment:** 5 minutes setup + 30-60 minutes processing = Production-ready statistics system
