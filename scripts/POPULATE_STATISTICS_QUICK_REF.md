# Populate All Statistics - Quick Reference

## Location
```
scripts/populate_all_statistics.py
```

## Database Entity Counts
- **Jockeys**: 3,483
- **Trainers**: 2,781
- **Owners**: 48,165
- **Total**: 54,429

## Estimated Execution Times
- **Jockeys**: ~7 hours
- **Trainers**: ~6 hours
- **Owners**: ~4 days
- **All**: ~4.5 days continuous

## Quick Commands

### Production (Full Population)
```bash
# Stage 1: Jockeys (~7 hours)
python3 scripts/populate_all_statistics.py --entities jockeys

# Stage 2: Trainers (~6 hours)
python3 scripts/populate_all_statistics.py --entities trainers

# Stage 3: Owners (~4 days, run in background)
nohup python3 scripts/populate_all_statistics.py --entities owners > logs/owners_stats.log 2>&1 &
```

### Daily Update (Only New Entities)
```bash
python3 scripts/populate_all_statistics.py --all --skip-existing
```

### Resume After Interruption
```bash
python3 scripts/populate_all_statistics.py --all --resume
```

### Testing
```bash
# Dry run - preview without executing
python3 scripts/populate_all_statistics.py --all --dry-run --limit 10

# Small test - process 5 entities per type
python3 scripts/populate_all_statistics.py --all --limit 5
```

## Monitor Progress

### View Real-time Progress (Background Jobs)
```bash
tail -f logs/owners_stats.log
```

### Check Checkpoint Progress
```bash
cat logs/checkpoint_owners.json | jq '.count'
```

### Check Process Status
```bash
ps aux | grep populate_all_statistics
```

## Output Files
- **Checkpoints**: `logs/checkpoint_{entity_type}.json`
- **Reports**: `logs/statistics_population_report_{timestamp}.json`

## Help
```bash
python3 scripts/populate_all_statistics.py --help
```

## Full Documentation
- **Complete Guide**: `scripts/POPULATE_STATISTICS_GUIDE.md`
- **Execution Summary**: `scripts/POPULATE_STATISTICS_EXECUTION_SUMMARY.md`
