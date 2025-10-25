# Backfill Strategy - Quick Start Guide

**One-page implementation guide for filling all historical data gaps**

---

## Current State

| Category | Status | Records |
|----------|--------|---------|
| ✅ Races & Runners | Complete | 137K races, 1.3M runners (2015-present) |
| ✅ Core Entities | Complete | 112K horses, 3.5K jockeys, 2.8K trainers |
| ✅ Pedigree Data | Complete | 112K lineage records (100% coverage) |
| ❌ Pedigree Statistics | **Missing** | 0% of 53,556 entities analyzed |
| ⚠️ Trainer Locations | **Partial** | 45% coverage (1,523 missing) |
| ⚠️ Entity Statistics | **Partial** | 93-97% coverage (1,302 gaps) |

---

## Three Data Gaps to Fill

### Gap 1: Pedigree Statistics (P0 - CRITICAL)
**Who:** 2,143 sires + 48,372 dams + 3,041 damsires = **53,556 entities**
**What's Missing:** Total runners, wins, win %, best class/distance, performance breakdowns
**Source:** Calculate from existing ra_runners + ra_races data
**Time:** ~34 hours (database calculations, no API calls)

### Gap 2: Trainer Locations (P1 - HIGH)
**Who:** **1,523 trainers** (54.76% of total)
**What's Missing:** Location (e.g., "Newmarket", "Lambourn")
**Source:** Racing API `/v1/trainers/{id}`
**Time:** ~13 minutes (1,523 API calls)

### Gap 3: Entity Statistics (P2 - MEDIUM)
**Who:** 115 jockeys + 169 trainers + 1,018 owners = **1,302 entities**
**What's Missing:** Total rides/runners, wins, win rate
**Source:** Calculate from existing ra_runners + ra_races data
**Time:** ~44 minutes (database calculations)

---

## Quick Execution (Production Recommended)

### Night 1: Sires Statistics (3 hours)
```bash
nohup python3 scripts/populate_pedigree_statistics.py --table sires \
  > logs/backfill_sires.log 2>&1 &

# Start at 11 PM → Complete by 2 AM
```

### Day 2 Morning: Verify (5 min)
```bash
psql -c "SELECT COUNT(*) as total, COUNT(analysis_last_updated) as done
FROM ra_mst_sires;"
# Expected: 2,143 total, 2,143 done
```

### Day 2 Afternoon: Trainer Locations (15 min)
```bash
python3 scripts/backfill_trainer_locations.py

# NOTE: Script needs to be created - see template below
```

### Night 2: Damsires Statistics (4 hours)
```bash
nohup python3 scripts/populate_pedigree_statistics.py --table damsires \
  > logs/backfill_damsires.log 2>&1 &
```

### Day 3 Afternoon: Entity Statistics (45 min)
```bash
python3 scripts/statistics_workers/calculate_jockey_statistics.py
python3 scripts/statistics_workers/calculate_trainer_statistics.py
python3 scripts/statistics_workers/calculate_owner_statistics.py
```

### Night 3: Dams Statistics (27 hours)
```bash
nohup python3 scripts/populate_pedigree_statistics.py --table dams \
  > logs/backfill_dams.log 2>&1 &

# Start Wednesday 11 PM → Complete Thursday 2 AM (next day)
```

### Day 4: Final Verification (15 min)
```bash
# Run comprehensive data audit
python3 scripts/audit_data_gaps.py

# Expected: "All data gaps filled - 100% coverage"
```

---

## Total Timeline

| Phase | Duration | Calendar Time |
|-------|----------|---------------|
| Sires stats | 3 hours | Night 1 |
| Trainer locations | 15 min | Day 2 |
| Damsires stats | 4 hours | Night 2 |
| Entity stats | 45 min | Day 3 |
| Dams stats | 27 hours | Night 3-4 |
| **Total** | **~35 hours** | **3.5 days** |

---

## New Script Required: backfill_trainer_locations.py

**Location:** `scripts/backfill_trainer_locations.py`

**Template:**
```python
#!/usr/bin/env python3
"""
Backfill Trainer Locations from Racing API

Fetches location data for trainers missing this field.

Usage:
    python3 scripts/backfill_trainer_locations.py
    python3 scripts/backfill_trainer_locations.py --test  # 10 trainers only
"""

import sys
import os
import time
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('backfill_trainer_locations')


def main():
    parser = argparse.ArgumentParser(description='Backfill trainer location data')
    parser.add_argument('--test', action='store_true', help='Test mode (10 trainers only)')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("TRAINER LOCATIONS BACKFILL")
    logger.info("=" * 80)

    # Initialize clients
    config = get_config()
    api_client = RacingAPIClient(
        username=config.racing_api_username,
        password=config.racing_api_password,
        base_url=config.racing_api_base_url
    )
    db_client = SupabaseReferenceClient()

    # Get trainers without location
    query = db_client.client.table('ra_mst_trainers').select('id, name').is_('location', 'null')
    if args.test:
        query = query.limit(10)

    response = query.execute()
    trainers = response.data

    logger.info(f"Found {len(trainers)} trainers missing location data")

    if args.test:
        logger.info("TEST MODE: Processing only 10 trainers")

    updated = 0
    not_found = 0
    errors = []

    for idx, trainer in enumerate(trainers, 1):
        try:
            # Fetch from API
            endpoint = f'/v1/trainers/{trainer["id"]}'
            trainer_data = api_client.get(endpoint)

            if trainer_data and trainer_data.get('location'):
                # Update database
                db_client.client.table('ra_mst_trainers').update({
                    'location': trainer_data['location'],
                    'updated_at': datetime.utcnow().isoformat()
                }).eq('id', trainer['id']).execute()

                updated += 1
                logger.info(f"[{idx}/{len(trainers)}] Updated {trainer['name']}: {trainer_data['location']}")
            else:
                not_found += 1
                logger.warning(f"[{idx}/{len(trainers)}] No location data for {trainer['name']}")

        except Exception as e:
            logger.error(f"[{idx}/{len(trainers)}] Error for {trainer['name']}: {e}")
            errors.append({'id': trainer['id'], 'name': trainer['name'], 'error': str(e)})

        # Rate limiting (2 req/sec)
        time.sleep(0.5)

    logger.info("=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total processed: {len(trainers)}")
    logger.info(f"Updated: {updated}")
    logger.info(f"Not found in API: {not_found}")
    logger.info(f"Errors: {len(errors)}")

    if errors:
        logger.error(f"Failed trainers: {errors}")

    return 0 if len(errors) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
```

---

## Verification Queries

### After Pedigree Statistics
```sql
-- Check all three tables
SELECT 'Sires' as type, COUNT(*) as total,
       COUNT(analysis_last_updated) as analyzed
FROM ra_mst_sires
UNION ALL
SELECT 'Dams', COUNT(*), COUNT(analysis_last_updated)
FROM ra_mst_dams
UNION ALL
SELECT 'Damsires', COUNT(*), COUNT(analysis_last_updated)
FROM ra_mst_damsires;

-- Expected: 100% analyzed for all
```

### After Trainer Locations
```sql
-- Check coverage
SELECT
    COUNT(*) as total,
    COUNT(location) as with_location,
    ROUND(COUNT(location)::numeric / COUNT(*)::numeric * 100, 1) as pct
FROM ra_mst_trainers;

-- Expected: >95% coverage
```

### After Entity Statistics
```sql
-- Check all entities
SELECT 'Jockeys' as type,
       COUNT(total_rides) FILTER (WHERE total_rides > 0) as with_stats
FROM ra_mst_jockeys
UNION ALL
SELECT 'Trainers',
       COUNT(total_runners) FILTER (WHERE total_runners > 0)
FROM ra_mst_trainers
UNION ALL
SELECT 'Owners',
       COUNT(total_runners) FILTER (WHERE total_runners > 0)
FROM ra_mst_owners;

-- Expected: All ~100%
```

---

## Monitoring

### Check Progress (While Running)
```bash
# Watch logs
tail -f logs/backfill_*.log

# Check database (sires example)
psql -c "SELECT COUNT(analysis_last_updated) as done
FROM ra_mst_sires;"
```

### Check for Errors
```bash
# Grep for errors in logs
grep -i error logs/backfill_*.log

# Count successful updates
grep -c "Updated" logs/backfill_trainer_locations.log
```

---

## Quick Wins

### If Time Constrained: Do These First

1. **Trainer Locations** (15 min)
   - Highest value-to-time ratio
   - Enables regional analysis immediately

2. **Sires Statistics** (3 hours overnight)
   - Most important pedigree entity
   - 2,143 entities vs 48,372 dams (faster)

3. **Entity Statistics Gaps** (45 min)
   - Rounds out existing entities
   - Quick completion

### Can Skip Initially (Do Later)

1. **Dams Statistics** (27 hours)
   - Less commonly used than sires
   - Very large dataset
   - Can run during weekend/downtime

2. **Damsires Statistics** (4 hours)
   - Least commonly used pedigree entity
   - Can prioritize lower

---

## Rollback Plan

### If Something Goes Wrong

**All scripts use UPSERT:**
- Safe to rerun
- Won't create duplicates
- Can stop and restart anytime

**To reset (if needed):**
```sql
-- Clear pedigree statistics (nuclear option)
UPDATE ra_mst_sires SET
    total_runners = 0, total_wins = 0,
    analysis_last_updated = NULL;

-- Clear trainer locations
UPDATE ra_mst_trainers SET location = NULL;

-- Then rerun backfill scripts
```

---

## Success Checklist

- [ ] All 2,143 sires have statistics calculated
- [ ] All 48,372 dams have statistics calculated
- [ ] All 3,041 damsires have statistics calculated
- [ ] >95% of trainers have location data
- [ ] 100% of jockeys with rides have statistics
- [ ] 100% of trainers with runners have statistics
- [ ] 100% of owners with runners have statistics
- [ ] No errors in final verification audit

---

## Next Steps After Completion

1. **Enable ML Features:**
   - Sire/dam form factors now available
   - Location-based trainer clustering
   - Regional performance analysis

2. **Set Up Maintenance:**
   - Daily: Update statistics for new entities
   - Weekly: Verify no new gaps
   - Monthly: Full recalculation (accuracy check)

3. **Document Completion:**
   - Update system status docs
   - Mark data gaps as "RESOLVED"
   - Update README with 100% coverage status

---

**For detailed strategy, see:** `docs/COMPREHENSIVE_BACKFILL_STRATEGY.md`

**Last Updated:** 2025-10-21
