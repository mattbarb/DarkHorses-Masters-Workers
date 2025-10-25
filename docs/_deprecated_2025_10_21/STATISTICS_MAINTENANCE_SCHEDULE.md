# Statistics Maintenance Schedule

**Purpose:** Track which statistics calculations need to run and when
**Last Updated:** 2025-10-20
**Status:** Production Ready

---

## 📋 Overview

This document defines the schedule for maintaining calculated statistics across all master tables. All statistics are derived from historical data in `ra_runners` and `ra_races` tables.

**Key Principle:** Statistics are NOT fetched from API - they are calculated from our historical race data.

---

## 🔄 Calculation Schedule

### Daily (After Results Fetch)

Run after fetching yesterday's race results to keep statistics current.

**Trigger:** After `main.py --entities results` completes
**Duration:** ~2-3 minutes
**Script:** `scripts/statistics_workers/update_daily_statistics.py`

#### Tables to Update:

##### 1. **ra_mst_jockeys** (Recent Form Only)
**Fields:**
- `recent_14d_rides` - Count rides in last 14 days
- `recent_14d_wins` - Count wins in last 14 days
- `recent_14d_win_rate` - Calculate (wins/rides * 100)
- `recent_30d_rides` - Count rides in last 30 days
- `recent_30d_wins` - Count wins in last 30 days
- `recent_30d_win_rate` - Calculate (wins/rides * 100)
- `last_ride_date` - MAX(race_date)
- `last_win_date` - MAX(race_date WHERE position=1)
- `days_since_last_ride` - CURRENT_DATE - last_ride_date
- `days_since_last_win` - CURRENT_DATE - last_win_date

**SQL Example:**
```sql
UPDATE ra_mst_jockeys j
SET
    recent_14d_rides = (
        SELECT COUNT(*)
        FROM ra_runners r
        JOIN ra_races rc ON r.race_id = rc.id
        WHERE r.jockey_id = j.id
          AND rc.date >= CURRENT_DATE - INTERVAL '14 days'
    ),
    recent_14d_wins = (
        SELECT COUNT(*)
        FROM ra_runners r
        JOIN ra_races rc ON r.race_id = rc.id
        WHERE r.jockey_id = j.id
          AND rc.date >= CURRENT_DATE - INTERVAL '14 days'
          AND r.position = 1
    ),
    stats_updated_at = NOW()
WHERE j.id IN (
    SELECT DISTINCT r.jockey_id
    FROM ra_runners r
    JOIN ra_races rc ON r.race_id = rc.id
    WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days'
);
```

##### 2. **ra_mst_trainers** (Recent Form Only)
**Fields:** Same as jockeys but for trainers
- `recent_14d_runs`, `recent_14d_wins`, `recent_14d_win_rate`
- `recent_30d_runs`, `recent_30d_wins`, `recent_30d_win_rate`
- `last_runner_date`, `last_win_date`
- `days_since_last_runner`, `days_since_last_win`

##### 3. **ra_mst_owners** (Recent Form Only)
**Fields:** Same as trainers plus activity flag
- `recent_14d_runs`, `recent_14d_wins`, `recent_14d_win_rate`
- `recent_30d_runs`, `recent_30d_wins`, `recent_30d_win_rate`
- `last_runner_date`, `last_win_date`
- `days_since_last_runner`, `days_since_last_win`
- `active_last_30d` - BOOLEAN (true if runs in last 30 days)

**Entities Affected:** Only those active in last 30 days (~500-1000 per day)
**Time:** ~30-60 seconds

---

### Weekly (Sunday Night)

Run every Sunday to recalculate lifetime statistics incorporating the week's races.

**Trigger:** Cron job Sunday 23:00
**Duration:** ~15 minutes
**Script:** `scripts/statistics_workers/update_weekly_statistics.py`

#### Tables to Update:

##### 1. **ra_mst_jockeys** (Full Lifetime Stats)
**Fields:**
- `total_rides` - COUNT(*)
- `total_wins` - COUNT(WHERE position=1)
- `total_places` - COUNT(WHERE position<=3)
- `total_seconds` - COUNT(WHERE position=2)
- `total_thirds` - COUNT(WHERE position=3)
- `win_rate` - (total_wins / total_rides * 100)
- `place_rate` - (total_places / total_rides * 100)
- All recent form fields (14d, 30d)
- All date fields

**Entities:** ALL jockeys (~3,500)
**Time:** ~2 minutes

##### 2. **ra_mst_trainers** (Full Lifetime Stats)
**Fields:** Same structure as jockeys
**Entities:** ALL trainers (~2,800)
**Time:** ~2 minutes

##### 3. **ra_mst_owners** (Full Lifetime Stats)
**Fields:** Same structure as trainers + total_horses
- All lifetime statistics
- `total_horses` - COUNT(DISTINCT horse_id)

**Entities:** ALL owners (~48,000)
**Time:** ~10 minutes

---

### Monthly (1st of Month, 02:00)

Run monthly for expensive calculations on pedigree entities.

**Trigger:** Cron job 1st of month 02:00
**Duration:** ~30-45 minutes
**Script:** `scripts/statistics_workers/update_monthly_statistics.py`

#### Tables to Update:

##### 1. **ra_sire_stats** (Progeny Performance)
**Fields:**
- Own Career (17 fields):
  - `runs`, `wins`, `places`, `prize`, `best_position`
  - `first_run`, `last_run`, `last_win`
- Progeny Performance:
  - `progeny_count` - COUNT(DISTINCT horses with this sire)
  - `progeny_runs`, `progeny_wins`, `progeny_prize`
  - `avg_runs_per_horse`, `avg_wins_per_horse`
- Timestamps: `calculated_at`

**Join Path:**
```sql
ra_mst_horses h (where h.sire_id = sire.id)
  -> ra_runners r (where r.horse_id = h.id)
  -> ra_races rc (where rc.id = r.race_id)
```

**Entities:** ~5,000-10,000 sires
**Time:** ~10-15 minutes

##### 2. **ra_dam_stats** (Progeny Performance)
**Fields:** Same structure as sires
**Join Path:** Same but h.dam_id = dam.id
**Entities:** ~10,000-20,000 dams
**Time:** ~10-15 minutes

##### 3. **ra_damsire_stats** (Grandoffspring Performance)
**Fields:** Same structure as sires
**Join Path:** Horses where h.damsire_id = damsire.id
**Entities:** ~5,000-10,000 damsires
**Time:** ~10-15 minutes

---

## 🔗 Integration with Daily Fetch

### Current Daily Workflow

```
1. Fetch Today's Racecards (Morning)
   python3 main.py --entities races

2. Fetch Yesterday's Results (Evening)
   python3 main.py --entities results
```

### Enhanced Daily Workflow (With Statistics)

```
1. Fetch Today's Racecards (Morning - 06:00)
   python3 main.py --entities races

2. Fetch Yesterday's Results (Evening - 23:00)
   python3 main.py --entities results

3. Update Daily Statistics (Evening - 23:05) ⭐ NEW
   python3 scripts/statistics_workers/update_daily_statistics.py
   Duration: ~2-3 minutes
   Updates: Recent form (14d/30d) for active entities
```

### Weekly Enhancement (Sunday 23:00)

```
1. Fetch Results (23:00)
   python3 main.py --entities results

2. Update Daily Statistics (23:05)
   python3 scripts/statistics_workers/update_daily_statistics.py

3. Update Weekly Statistics (23:10) ⭐ NEW
   python3 scripts/statistics_workers/update_weekly_statistics.py
   Duration: ~15 minutes
   Updates: Full lifetime statistics for all people
```

### Monthly Enhancement (1st of Month 02:00)

```
python3 scripts/statistics_workers/update_monthly_statistics.py
Duration: ~30-45 minutes
Updates: Pedigree entity progeny performance
```

---

## 📝 Scripts to Create

### 1. Daily Statistics Updater

**File:** `scripts/statistics_workers/update_daily_statistics.py`

**Purpose:** Update recent form (14d/30d) and last dates for active entities

**Features:**
- Only updates entities with races in last 30 days
- Fast execution (~2-3 minutes)
- Lightweight queries
- No full recalculation

**Command:**
```bash
python3 scripts/statistics_workers/update_daily_statistics.py
```

### 2. Weekly Statistics Updater

**File:** `scripts/statistics_workers/update_weekly_statistics.py`

**Purpose:** Full recalculation of lifetime statistics for all people

**Features:**
- Updates ALL jockeys, trainers, owners
- Includes lifetime + recent form + dates
- Runs efficiently with batching
- ~15 minutes total

**Command:**
```bash
python3 scripts/statistics_workers/update_weekly_statistics.py
```

### 3. Monthly Statistics Updater

**File:** `scripts/statistics_workers/update_monthly_statistics.py`

**Purpose:** Expensive pedigree progeny performance calculations

**Features:**
- Calculates sire/dam/damsire progeny statistics
- Complex joins across multiple tables
- ~30-45 minutes total
- Checkpoint/resume capability

**Command:**
```bash
python3 scripts/statistics_workers/update_monthly_statistics.py
```

---

## 🗓️ Cron Schedule

Add to crontab for automated execution:

```bash
# Daily Statistics (After evening results fetch)
5 23 * * * cd /path/to/DarkHorses-Masters-Workers && python3 scripts/statistics_workers/update_daily_statistics.py >> logs/daily_stats_$(date +\%Y\%m\%d).log 2>&1

# Weekly Statistics (Sunday night after results)
10 23 * * 0 cd /path/to/DarkHorses-Masters-Workers && python3 scripts/statistics_workers/update_weekly_statistics.py >> logs/weekly_stats_$(date +\%Y\%m\%d).log 2>&1

# Monthly Statistics (1st of month, 2 AM)
0 2 1 * * cd /path/to/DarkHorses-Masters-Workers && python3 scripts/statistics_workers/update_monthly_statistics.py >> logs/monthly_stats_$(date +\%Y\%m\%d).log 2>&1
```

---

## 📊 Statistics Calculation Details

### People Statistics (Jockeys/Trainers/Owners)

#### Lifetime Statistics
**Source:** ALL historical data in ra_runners + ra_races
**Calculation:** Aggregate COUNT, SUM, AVG across entire history
**Update Frequency:** Weekly
**Entities:** All (~54,000 total)

```sql
-- Example for jockeys
SELECT
    j.id,
    COUNT(r.id) as total_rides,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
    ROUND(COUNT(CASE WHEN r.position = 1 THEN 1 END)::numeric / COUNT(r.id)::numeric * 100, 2) as win_rate
FROM ra_mst_jockeys j
LEFT JOIN ra_runners r ON r.jockey_id = j.id
LEFT JOIN ra_races rc ON rc.id = r.race_id
GROUP BY j.id;
```

#### Recent Form Statistics
**Source:** Last 14/30 days only
**Calculation:** Same as lifetime but filtered by date
**Update Frequency:** Daily
**Entities:** Active only (~1,000 per day)

```sql
-- Example for 14-day recent form
SELECT
    j.id,
    COUNT(r.id) as recent_14d_rides,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as recent_14d_wins
FROM ra_mst_jockeys j
LEFT JOIN ra_runners r ON r.jockey_id = j.id
LEFT JOIN ra_races rc ON rc.id = r.race_id
WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days'
GROUP BY j.id;
```

#### Last Activity Dates
**Source:** MAX(date) from ra_races
**Calculation:** Find most recent race participation
**Update Frequency:** Daily
**Entities:** Active only

```sql
-- Example for last dates
SELECT
    j.id,
    MAX(rc.date) as last_ride_date,
    MAX(CASE WHEN r.position = 1 THEN rc.date END) as last_win_date,
    CURRENT_DATE - MAX(rc.date) as days_since_last_ride
FROM ra_mst_jockeys j
LEFT JOIN ra_runners r ON r.jockey_id = j.id
LEFT JOIN ra_races rc ON rc.id = r.race_id
GROUP BY j.id;
```

### Pedigree Statistics (Sires/Dams/Damsires)

#### Own Career Statistics
**Source:** ra_runners where horse_id = pedigree_entity.horse_id
**Calculation:** Aggregate the sire/dam/damsire's own racing career
**Update Frequency:** Monthly (historical data, rarely changes)

```sql
-- Example for sire's own career
SELECT
    s.id,
    COUNT(r.id) as runs,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins,
    SUM(r.prize_won) as prize,
    MIN(r.position) as best_position,
    MIN(rc.date) as first_run,
    MAX(rc.date) as last_run
FROM ra_mst_sires s
LEFT JOIN ra_mst_horses h ON h.id = s.horse_id
LEFT JOIN ra_runners r ON r.horse_id = h.id
LEFT JOIN ra_races rc ON rc.id = r.race_id
GROUP BY s.id;
```

#### Progeny/Grandoffspring Statistics
**Source:** ra_runners for offspring horses
**Calculation:** Aggregate performance of progeny
**Update Frequency:** Monthly

```sql
-- Example for sire progeny performance
SELECT
    s.id,
    COUNT(DISTINCT h.id) as progeny_count,
    COUNT(r.id) as progeny_runs,
    COUNT(CASE WHEN r.position = 1 THEN 1 END) as progeny_wins,
    ROUND(COUNT(r.id)::numeric / COUNT(DISTINCT h.id)::numeric, 2) as avg_runs_per_horse
FROM ra_mst_sires s
LEFT JOIN ra_mst_horses h ON h.sire_id = s.id
LEFT JOIN ra_runners r ON r.horse_id = h.id
LEFT JOIN ra_races rc ON rc.id = r.race_id
GROUP BY s.id;
```

---

## 🎯 Performance Optimization

### Indexes Required

```sql
-- For daily updates (recent form)
CREATE INDEX IF NOT EXISTS idx_races_date_desc ON ra_races(date DESC);
CREATE INDEX IF NOT EXISTS idx_runners_jockey_id ON ra_runners(jockey_id);
CREATE INDEX IF NOT EXISTS idx_runners_trainer_id ON ra_runners(trainer_id);
CREATE INDEX IF NOT EXISTS idx_runners_owner_id ON ra_runners(owner_id);

-- For weekly/monthly updates (lifetime stats)
CREATE INDEX IF NOT EXISTS idx_runners_position ON ra_runners(position) WHERE position IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_horses_sire_id ON ra_mst_horses(sire_id) WHERE sire_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_horses_dam_id ON ra_mst_horses(dam_id) WHERE dam_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_horses_damsire_id ON ra_mst_horses(damsire_id) WHERE damsire_id IS NOT NULL;
```

### Batch Processing

- **Daily:** Process 1000 entities per batch (active only)
- **Weekly:** Process 100 entities per batch (all people)
- **Monthly:** Process 50 entities per batch (pedigree - expensive joins)

### Materialized Views (Future Enhancement)

```sql
-- Create materialized view for recent form (refreshed daily)
CREATE MATERIALIZED VIEW mv_recent_form AS
SELECT
    r.jockey_id,
    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - 14) as rides_14d,
    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - 30) as rides_30d
FROM ra_runners r
JOIN ra_races rc ON rc.id = r.race_id
WHERE rc.date >= CURRENT_DATE - 30
GROUP BY r.jockey_id;

-- Refresh daily
REFRESH MATERIALIZED VIEW mv_recent_form;
```

---

## 📈 Monitoring & Validation

### Daily Health Checks

```sql
-- Check recent form is being updated
SELECT
    COUNT(*) FILTER (WHERE stats_updated_at >= CURRENT_DATE) as updated_today,
    COUNT(*) FILTER (WHERE stats_updated_at < CURRENT_DATE - 7) as stale,
    COUNT(*) as total
FROM ra_mst_jockeys
WHERE last_ride_date >= CURRENT_DATE - 30;
```

### Weekly Verification

```sql
-- Verify lifetime stats match raw data
SELECT
    j.id,
    j.total_rides as calculated_rides,
    COUNT(r.id) as actual_rides,
    j.total_rides - COUNT(r.id) as difference
FROM ra_mst_jockeys j
LEFT JOIN ra_runners r ON r.jockey_id = j.id
GROUP BY j.id, j.total_rides
HAVING j.total_rides - COUNT(r.id) != 0
LIMIT 10;
```

### Monthly Audit

```sql
-- Check progeny counts are reasonable
SELECT
    s.id,
    s.name,
    progeny_count,
    progeny_runs,
    CASE
        WHEN progeny_count = 0 AND progeny_runs > 0 THEN 'MISMATCH'
        WHEN progeny_runs::float / progeny_count > 100 THEN 'SUSPICIOUS'
        ELSE 'OK'
    END as status
FROM ra_sire_stats s
WHERE progeny_count IS NOT NULL;
```

---

## ⚠️ Important Notes

1. **No API Dependencies:** All calculations use existing database data only
2. **Idempotent:** Scripts can be run multiple times safely (UPSERT logic)
3. **Incremental:** Daily updates only touch active entities for speed
4. **Resume Capable:** Monthly scripts support checkpoints for long runs
5. **Logging:** All scripts log to `logs/stats_update_*.log`
6. **Alerting:** Monitor log files for ERROR messages

---

## 🔄 Update History

| Date | Change | Reason |
|------|--------|--------|
| 2025-10-20 | Initial creation | Define statistics maintenance schedule |

---

## 📞 Related Documentation

- `scripts/statistics_workers/populate_all_statistics.py` - Initial population (one-time)
- `scripts/statistics_workers/calculate_jockey_statistics.py` - Jockey calculator
- `scripts/statistics_workers/calculate_trainer_statistics.py` - Trainer calculator
- `scripts/statistics_workers/calculate_owner_statistics.py` - Owner calculator
- `COMPLETE_DATA_ENRICHMENT_SUMMARY.md` - Overall implementation summary

---

**Status:** READY FOR IMPLEMENTATION
**Next Step:** Create the 3 update scripts (daily/weekly/monthly)
