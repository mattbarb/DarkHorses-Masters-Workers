# Autonomous Agents

This directory contains autonomous agents that run independently to populate and maintain data in the database.

## Pedigree Statistics Agent

**File:** `pedigree_statistics_agent.py`

### Purpose

Autonomously populates and maintains ALL statistics columns in the pedigree master tables:
- `ra_mst_sires`
- `ra_mst_dams`
- `ra_mst_damsires`

### Features

- **Complete Statistics Calculation:** Calculates all statistics from progeny performance data (runners/races in database)
- **AE Index Calculation:** Computes Actual vs Expected indices for overall, class, and distance performance
- **Data Quality Scoring:** Assigns quality scores (0.00-1.00) based on data completeness
- **Checkpoint/Resume:** Can resume from last processed entity if interrupted
- **Continuous Mode:** Runs indefinitely at configurable intervals for ongoing maintenance
- **Detailed Logging:** Comprehensive logging with error tracking and statistics

### Columns Populated

**Basic Statistics:**
- `total_runners` - Total progeny race starts
- `total_wins` - Total wins by progeny
- `total_places_2nd` - Total 2nd place finishes
- `total_places_3rd` - Total 3rd place finishes

**Performance Metrics:**
- `overall_win_percent` - Win percentage (wins/runners × 100)
- `overall_ae_index` - Actual vs Expected index (compares actual wins to expected based on class distribution)

**Best Performance:**
- `best_class` - Class with most wins
- `best_class_ae` - AE index for best class
- `best_distance` - Distance with most wins
- `best_distance_ae` - AE index for best distance

**Class Breakdown** (Top 3 classes by wins):
- `class_1_name`, `class_1_runners`, `class_1_wins`, `class_1_win_percent`, `class_1_ae`
- `class_2_name`, `class_2_runners`, `class_2_wins`, `class_2_win_percent`, `class_2_ae`
- `class_3_name`, `class_3_runners`, `class_3_wins`, `class_3_win_percent`, `class_3_ae`

**Distance Breakdown** (Top 3 distances by wins):
- `distance_1_name`, `distance_1_runners`, `distance_1_wins`, `distance_1_win_percent`, `distance_1_ae`
- `distance_2_name`, `distance_2_runners`, `distance_2_wins`, `distance_2_win_percent`, `distance_2_ae`
- `distance_3_name`, `distance_3_runners`, `distance_3_wins`, `distance_3_win_percent`, `distance_3_ae`

**Metadata:**
- `analysis_last_updated` - Timestamp of last calculation
- `data_quality_score` - Quality score (0.00-1.00)

### Usage

```bash
# Test mode (10 entities per table)
python3 agents/pedigree_statistics_agent.py --test

# Full run (all tables)
python3 agents/pedigree_statistics_agent.py

# Specific table only
python3 agents/pedigree_statistics_agent.py --table sires
python3 agents/pedigree_statistics_agent.py --table dams
python3 agents/pedigree_statistics_agent.py --table damsires

# Resume from checkpoint (if interrupted)
python3 agents/pedigree_statistics_agent.py --resume

# Continuous mode (runs every 24 hours)
python3 agents/pedigree_statistics_agent.py --continuous --interval 24
```

### How It Works

1. **Load Entities:** Fetches all sires/dams/damsires from master tables
2. **Get Progeny:** For each entity, finds all horses with that sire/dam/damsire
3. **Analyze Races:** Retrieves all race performances (runners) for those horses
4. **Calculate Stats:** Computes win rates, places, class/distance breakdowns
5. **Calculate AE Indices:** Compares actual performance to expected based on race conditions
6. **Score Quality:** Assigns quality score based on data completeness
7. **Update Database:** Upserts complete statistics record

### AE Index Calculation

**AE (Actual vs Expected) = (Actual Wins / Expected Wins) × 100**

- **AE = 100:** Performance exactly as expected
- **AE > 100:** Performance better than expected (e.g., AE=150 means 50% better)
- **AE < 100:** Performance worse than expected (e.g., AE=80 means 20% worse)

Expected wins are calculated based on:
- **Class distribution:** Different classes have different baseline win rates
- **Distance distribution:** Different distance categories have different baseline win rates

### Data Quality Score

Scoring breakdown (0.00 - 1.00):
- **0.20:** Has runner data
- **0.30:** Has class breakdown (0.10 per class, top 3)
- **0.30:** Has distance breakdown (0.10 per distance, top 3)
- **0.20:** Has AE indices (0.10 overall, 0.05 best class, 0.05 best distance)

### Performance

- **Test mode (10 entities):** ~4 seconds
- **Full run estimates:**
  - Sires (~3,000): ~10 minutes
  - Dams (~50,000): ~2-3 hours
  - Damsires (~3,000): ~10 minutes
- **Total:** ~3-4 hours for complete run

### Logs

- **Checkpoint:** `logs/pedigree_agent_checkpoint.json` - Resume point
- **Statistics:** `logs/pedigree_agent_stats.json` - Run statistics
- **Logs:** Standard logger output (console + log file)

### Scheduling Recommendations

**Daily:** Not needed (pedigree statistics change slowly)

**Weekly:** Recommended for production
```bash
python3 agents/pedigree_statistics_agent.py
```

**Continuous:** For real-time updates
```bash
python3 agents/pedigree_statistics_agent.py --continuous --interval 168  # Weekly
```

### Integration with Main System

The agent operates independently but uses the same database as the main fetchers:
- **Reads from:** `ra_mst_horses`, `ra_mst_runners`, `ra_races`
- **Writes to:** `ra_mst_sires`, `ra_mst_dams`, `ra_mst_damsires`

Can run concurrently with fetchers (uses database-level locking).

### Troubleshooting

**Slow performance:**
- Check database connection (Supabase pooler limits)
- Reduce batch size for race queries (default: 1000)
- Run specific tables instead of all at once

**Missing data:**
- Ensure fetchers have populated `ra_mst_runners` and `ra_races`
- Check that horses have pedigree IDs populated

**Errors:**
- Check logs for specific error messages
- Use `--test` mode to debug with limited data
- Verify database schema matches expected columns

---

**Last Updated:** 2025-10-21
**Status:** Production Ready
