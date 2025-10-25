# Pedigree Statistics Agent - Quick Reference

## Agent Control

```bash
# Start agent (full run)
python3 agents/pedigree_statistics_agent.py

# Start in background
nohup python3 agents/pedigree_statistics_agent.py > logs/pedigree_agent_run.log 2>&1 &

# Test mode (10 entities per table)
python3 agents/pedigree_statistics_agent.py --test

# Specific table
python3 agents/pedigree_statistics_agent.py --table sires

# Resume from checkpoint
python3 agents/pedigree_statistics_agent.py --resume

# Continuous mode (weekly updates)
python3 agents/pedigree_statistics_agent.py --continuous --interval 168
```

## Monitoring

```bash
# Run monitor script
bash agents/monitor_agent.sh

# Check if running
pgrep -f pedigree_statistics_agent.py

# View logs
tail -f logs/pedigree_agent_run.log

# Check progress in database
psql -c "SELECT 'Sires' as type, COUNT(*) as total,
         COUNT(overall_ae_index) FILTER (WHERE overall_ae_index IS NOT NULL) as populated
         FROM ra_mst_sires;"
```

## Agent Control

```bash
# Stop agent (graceful)
kill $(pgrep -f pedigree_statistics_agent.py)

# Force stop
kill -9 $(pgrep -f pedigree_statistics_agent.py)

# Then resume later
python3 agents/pedigree_statistics_agent.py --resume
```

## Files

- **Agent:** `agents/pedigree_statistics_agent.py`
- **Monitor:** `agents/monitor_agent.sh`
- **Logs:** `logs/pedigree_agent_run.log`
- **Checkpoint:** `logs/pedigree_agent_checkpoint.json`
- **Stats:** `logs/pedigree_agent_stats.json`

## Verify Data

```sql
-- Check population status
SELECT
    'Sires' as entity_type,
    COUNT(*) as total,
    COUNT(overall_ae_index) FILTER (WHERE overall_ae_index IS NOT NULL) as populated,
    ROUND(COUNT(overall_ae_index) FILTER (WHERE overall_ae_index IS NOT NULL)::numeric / COUNT(*)::numeric * 100, 2) as pct
FROM ra_mst_sires;

-- Check data quality
SELECT
    name,
    total_runners,
    total_wins,
    overall_win_percent,
    overall_ae_index,
    data_quality_score
FROM ra_mst_sires
WHERE total_runners > 100
ORDER BY overall_ae_index DESC
LIMIT 10;

-- Check best performers
SELECT name, overall_ae_index, best_class, best_distance
FROM ra_mst_sires
WHERE total_runners > 50 AND overall_ae_index > 0
ORDER BY overall_ae_index DESC
LIMIT 20;
```

## Columns Populated (47 per table)

### Core (5)
`id`, `name`, `horse_id`, `created_at`, `updated_at`

### Basic Stats (5)
`total_runners`, `total_wins`, `total_places_2nd`, `total_places_3rd`, `overall_win_percent`

### Performance (6)
`overall_ae_index`, `best_class`, `best_class_ae`, `best_distance`, `best_distance_ae`, `data_quality_score`

### Class Breakdown (15)
`class_1/2/3_name`, `_runners`, `_wins`, `_win_percent`, `_ae`

### Distance Breakdown (15)
`distance_1/2/3_name`, `_runners`, `_wins`, `_win_percent`, `_ae`

### Metadata (1)
`analysis_last_updated`

## Performance

- **Test (30 entities):** ~12 seconds
- **Full run (53,556 entities):** ~2-3 hours
- **Processing rate:** ~10-15 entities/minute
- **Checkpoint:** Every 10 entities

## AE Index Interpretation

- **AE = 100:** Exactly as expected
- **AE > 100:** Better than expected (e.g., 150 = 50% better)
- **AE < 100:** Worse than expected (e.g., 80 = 20% worse)

## Data Quality Score

- **1.00:** Complete data (all fields populated)
- **0.80:** Good (basic + some breakdowns)
- **0.50:** Moderate (basic stats only)
- **0.20:** Minimal (runner data only)

## Common Issues

**Agent slow?**
- Check database connection
- Run tables separately
- Check Supabase dashboard for rate limits

**Missing data?**
- Ensure fetchers have populated `ra_runners`
- Check pedigree IDs in `ra_mst_horses`

**Need to stop?**
- Use `kill $(pgrep -f pedigree_statistics_agent.py)`
- Resume later with `--resume`

---

**Quick Status Check:** `bash agents/monitor_agent.sh`
