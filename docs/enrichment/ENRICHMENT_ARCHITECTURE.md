# Data Enrichment Architecture
## Racing API Pro - Complete System Overview

**Last Updated:** 2025-10-14

---

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RACING API PRO                                     │
│                      https://api.theracingapi.com                           │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
        ┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
        │   RACECARDS     │ │   HORSES    │ │   RESULTS    │
        │  (Bulk Fetch)   │ │(Individual) │ │  (Optional)  │
        └─────────────────┘ └─────────────┘ └──────────────┘
                │                   │                │
                │ Daily fetch       │ On-demand      │ Not used
                │ ~500 calls        │ ~50-200/day    │ (redundant)
                ▼                   ▼                │
        ┌─────────────────────────────────────────────────┐
        │         ENTITY EXTRACTION LAYER                  │
        │      (utils/entity_extractor.py)                │
        │                                                  │
        │  • Discovers: Horses, Jockeys, Trainers, Owners │
        │  • Enriches: NEW horses via Pro endpoint        │
        │  • Rate limit: 2 requests/second                │
        └─────────────────────────────────────────────────┘
                │
                │ Upsert batches (100 records)
                │
                ▼
        ┌─────────────────────────────────────────────────┐
        │            POSTGRESQL DATABASE                   │
        │         (Supabase - amsjvmlaknnvppxsgpfk)       │
        │                                                  │
        │  ┌──────────────┐  ┌───────────────┐           │
        │  │  ra_horses   │  │ ra_horse_     │           │
        │  │              │  │   pedigree    │           │
        │  │ • horse_id   │  │               │           │
        │  │ • name       │  │ • sire/dam    │           │
        │  │ • dob ✨     │  │ • damsire     │           │
        │  │ • sex ✨     │  │ • breeder ✨  │           │
        │  │ • colour ✨  │  │               │           │
        │  └──────────────┘  └───────────────┘           │
        │                                                  │
        │  ┌──────────────┐  ┌──────────────┐            │
        │  │ ra_jockeys   │  │ ra_trainers  │            │
        │  │              │  │              │            │
        │  │ • jockey_id  │  │ • trainer_id │            │
        │  │ • name       │  │ • name       │            │
        │  │ • stats 📊   │  │ • stats 📊   │            │
        │  └──────────────┘  └──────────────┘            │
        │                                                  │
        │  ┌──────────────┐  ┌──────────────┐            │
        │  │ ra_owners    │  │ ra_courses   │            │
        │  │              │  │              │            │
        │  │ • owner_id   │  │ • course_id  │            │
        │  │ • name       │  │ • name       │            │
        │  │ • stats 📊   │  │ • region     │            │
        │  └──────────────┘  └──────────────┘            │
        │                                                  │
        │  ┌──────────────┐  ┌──────────────┐            │
        │  │  ra_mst_races    │  │ ra_mst_runners   │            │
        │  │              │  │              │            │
        │  │ • race_id    │  │ • runner_id  │            │
        │  │ • course_id  │  │ • horse_id   │            │
        │  │ • race_date  │  │ • jockey_id  │            │
        │  │ • distance   │  │ • trainer_id │            │
        │  └──────────────┘  │ • owner_id   │            │
        │                    │ • position   │            │
        │                    └──────────────┘            │
        └─────────────────────────────────────────────────┘
                │
                │ Materialized statistics
                │
                ▼
        ┌─────────────────────────────────────────────────┐
        │      STATISTICS CALCULATION LAYER                │
        │      (SQL Views + Functions)                     │
        │                                                  │
        │  • jockey_statistics (view)                     │
        │  • trainer_statistics (view)                    │
        │  • owner_statistics (view)                      │
        │  • update_entity_statistics() (function)        │
        │                                                  │
        │  NO API CALLS - Pure SQL calculation            │
        └─────────────────────────────────────────────────┘

Legend:
  ✨ = Pro endpoint only fields
  📊 = Calculated from ra_mst_runners (NOT from API)
```

---

## Data Flow - Entity Discovery & Enrichment

```
STEP 1: DAILY RACECARD FETCH
┌────────────────────────────────────────────────────────────┐
│  GET /v1/racecards/pro?date=2025-10-14                     │
│  Returns: ~500 races with runners                          │
└────────────────────────────────────────────────────────────┘
                        │
                        ▼
STEP 2: ENTITY EXTRACTION
┌────────────────────────────────────────────────────────────┐
│  For each runner, extract:                                 │
│   • horse_id, horse_name                                   │
│   • jockey_id, jockey_name                                 │
│   • trainer_id, trainer_name                               │
│   • owner_id, owner_name                                   │
│                                                             │
│  Result: Unique sets of each entity type                   │
└────────────────────────────────────────────────────────────┘
                        │
            ┌───────────┴──────────┐
            ▼                      ▼
STEP 3a: BASIC ENTITIES    STEP 3b: HORSE ENRICHMENT
┌──────────────────────┐   ┌──────────────────────────────┐
│ Jockeys: Insert as-is│   │ Check if horse is NEW        │
│ Trainers: Insert as-is│   │                              │
│ Owners: Insert as-is │   │ IF NEW:                      │
│ (Only name+id)       │   │   GET /v1/horses/{id}/pro    │
└──────────────────────┘   │   • dob, sex, colour         │
                           │   • breeder                  │
                           │   • sire/dam/damsire         │
                           │                              │
                           │ IF EXISTING:                 │
                           │   Skip API call              │
                           └──────────────────────────────┘
                                       │
                                       ▼
STEP 4: DATABASE UPSERT
┌────────────────────────────────────────────────────────────┐
│  Batch upsert (100 records at a time):                     │
│   • ra_horses (enriched with Pro data)                     │
│   • ra_horse_pedigree (separate table)                     │
│   • ra_jockeys (basic name+id)                             │
│   • ra_trainers (basic name+id)                            │
│   • ra_owners (basic name+id)                              │
│   • ra_mst_races (full race details)                           │
│   • ra_mst_runners (links everything together)                 │
└────────────────────────────────────────────────────────────┘
                        │
                        ▼
STEP 5: STATISTICS CALCULATION (Daily/Weekly)
┌────────────────────────────────────────────────────────────┐
│  SELECT * FROM update_entity_statistics();                 │
│                                                             │
│  Calculates from ra_mst_runners:                               │
│   • Jockey win rates, total rides                          │
│   • Trainer win rates, recent form                         │
│   • Owner win rates, active status                         │
│                                                             │
│  Updates statistics columns in entity tables               │
└────────────────────────────────────────────────────────────┘
```

---

## Enrichment Decision Tree

```
                    ┌──────────────────┐
                    │  New Entity      │
                    │  Discovered      │
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Is it a HORSE?  │
                    └────────┬─────────┘
                             │
                ┌────────────┴────────────┐
                │                         │
               YES                        NO
                │                         │
                ▼                         ▼
    ┌──────────────────────┐   ┌──────────────────────┐
    │ Check if NEW horse   │   │ Jockey/Trainer/Owner │
    │ (not in ra_horses)   │   │                      │
    └──────────┬───────────┘   │ Store name + ID only │
               │               │ NO API enrichment    │
         ┌─────┴─────┐         │ (no endpoint exists) │
         │           │         └──────────────────────┘
        NEW      EXISTING
         │           │
         ▼           ▼
    ┌─────────┐ ┌─────────┐
    │ Enrich  │ │  Skip   │
    │ via Pro │ │ API call│
    │ endpoint│ │ (exists)│
    └─────────┘ └─────────┘
         │
         ▼
    ┌─────────────────────────┐
    │ GET /v1/horses/{id}/pro │
    │                         │
    │ Returns:                │
    │ • dob, sex, colour      │
    │ • breeder               │
    │ • sire/dam/damsire IDs  │
    └─────────────────────────┘
         │
         ▼
    ┌─────────────────────────┐
    │ Store in 2 tables:      │
    │ • ra_horses             │
    │ • ra_horse_pedigree     │
    └─────────────────────────┘
```

---

## Statistics Calculation Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      ra_mst_runners                              │
│  (Source of Truth for All Performance Data)                 │
│                                                              │
│  Every race result with:                                    │
│  • horse_id, jockey_id, trainer_id, owner_id                │
│  • position (1st, 2nd, 3rd, etc.)                           │
│  • race_date, course_id, distance                           │
└────────────────────┬────────────────────────────────────────┘
                     │
      ┌──────────────┼──────────────┐
      │              │              │
      ▼              ▼              ▼
┌──────────┐  ┌──────────┐  ┌──────────┐
│ Jockey   │  │ Trainer  │  │  Owner   │
│Statistics│  │Statistics│  │Statistics│
│  VIEW    │  │   VIEW   │  │   VIEW   │
└──────────┘  └──────────┘  └──────────┘
      │              │              │
      │   SQL        │   SQL        │   SQL
      │   JOIN &     │   JOIN &     │   JOIN &
      │   GROUP BY   │   GROUP BY   │   GROUP BY
      │              │              │
      ▼              ▼              ▼
┌──────────────────────────────────────────┐
│  Calculated Statistics:                  │
│                                          │
│  • Total rides/runners                   │
│  • Total wins (position = 1)             │
│  • Total places (position <= 3)          │
│  • Win rate = wins/rides * 100           │
│  • Place rate = places/rides * 100       │
│  • Recent form (last 14 days)            │
│  • Active status (last 30 days)          │
└──────────────────────────────────────────┘
                     │
                     │ Daily/Weekly
                     │
                     ▼
┌─────────────────────────────────────────────┐
│  update_entity_statistics() FUNCTION        │
│                                             │
│  UPDATE ra_jockeys                          │
│  SET total_rides = calculated,              │
│      total_wins = calculated,               │
│      win_rate = calculated, ...             │
│  FROM jockey_statistics                     │
│                                             │
│  (Same for trainers and owners)             │
└─────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────┐
│         Entity Tables Updated               │
│                                             │
│  ra_jockeys.total_rides = 14,573            │
│  ra_jockeys.win_rate = 11.2%                │
│  ra_jockeys.stats_updated_at = NOW()        │
└─────────────────────────────────────────────┘
```

**KEY INSIGHT:** No API calls needed for statistics - all calculated from our own data!

---

## API Endpoint Utilization Map

```
┌───────────────────────────────────────────────────────────────┐
│                    RACING API ENDPOINTS                        │
└───────────────────────────────────────────────────────────────┘

BULK ENDPOINTS (Used Daily)
┌─────────────────────────────────────────────────────────┐
│ /v1/racecards/pro                                       │
│ ├─ Status: ✅ ACTIVE                                    │
│ ├─ Frequency: Daily                                     │
│ ├─ Calls/day: ~500                                      │
│ ├─ Purpose: Discover races, runners, all entities       │
│ └─ Returns: Complete race + runner data                 │
└─────────────────────────────────────────────────────────┘

INDIVIDUAL DETAIL ENDPOINTS (Selective Use)
┌─────────────────────────────────────────────────────────┐
│ /v1/horses/{id}/pro                                     │
│ ├─ Status: ✅ ACTIVE (Hybrid enrichment)               │
│ ├─ Frequency: Per NEW horse only                        │
│ ├─ Calls/day: 50-200 (new horses)                       │
│ ├─ Purpose: Enrich new horses with pedigree             │
│ └─ Returns: dob, sex, colour, breeder, pedigree         │
└─────────────────────────────────────────────────────────┘

RESULTS ENDPOINTS (Not Used)
┌─────────────────────────────────────────────────────────┐
│ /v1/horses/{id}/results                                 │
│ /v1/jockeys/{id}/results                                │
│ /v1/trainers/{id}/results                               │
│ /v1/owners/{id}/results                                 │
│ ├─ Status: ⏸️ NOT USED                                 │
│ ├─ Reason: Redundant with ra_mst_runners                    │
│ ├─ Alternative: Query ra_mst_runners directly               │
│ └─ Savings: 1000s of API calls                          │
└─────────────────────────────────────────────────────────┘

ANALYSIS ENDPOINTS (Not Stored)
┌─────────────────────────────────────────────────────────┐
│ /v1/jockeys/{id}/analysis/*                             │
│ /v1/trainers/{id}/analysis/*                            │
│ /v1/owners/{id}/analysis/*                              │
│ /v1/horses/{id}/analysis/*                              │
│ ├─ Status: ⏸️ NOT STORED                               │
│ ├─ Reason: Can calculate locally from ra_mst_runners        │
│ ├─ Use case: On-demand queries only                     │
│ └─ Savings: 10,000s of API calls                        │
└─────────────────────────────────────────────────────────┘

INDIVIDUAL RACE ENDPOINT (Not Used)
┌─────────────────────────────────────────────────────────┐
│ /v1/racecards/{id}/pro                                  │
│ ├─ Status: ⏸️ NOT USED                                 │
│ ├─ Reason: Already get from bulk racecards fetch        │
│ ├─ Alternative: Use cached racecard data                │
│ └─ Savings: 1000s of API calls                          │
└─────────────────────────────────────────────────────────┘

SUMMARY:
  Total Available: ~50 endpoints
  Actively Used: 2 endpoints (racecards + horse pro)
  API Efficiency: 96% of calls eliminated via local calculations
```

---

## Storage & Performance Metrics

### Current Database State (2025-10-14)

```
┌──────────────────┬──────────────┬─────────────────────────────┐
│ Table            │ Records      │ Growth Rate                 │
├──────────────────┼──────────────┼─────────────────────────────┤
│ ra_horses        │ 111,430      │ +50-200/day (new discovers) │
│ ra_horse_pedigree│ 22           │ → 111,430 (backfill target) │
│ ra_jockeys       │ 3,480        │ +5-20/day                   │
│ ra_trainers      │ 2,780        │ +2-10/day                   │
│ ra_owners        │ 48,092       │ +20-50/day                  │
│ ra_courses       │ 101          │ Stable (complete)           │
│ ra_mst_races         │ Variable     │ +500-700/day                │
│ ra_mst_runners       │ Large        │ +5,000-8,000/day            │
└──────────────────┴──────────────┴─────────────────────────────┘
```

### Enrichment Progress

```
Horse Pro Enrichment:
  ┌─────────────────────────────────────────────────────┐
  │ Auto-enrich: █████████████████████████ 100% ACTIVE  │
  │ New horses enriched automatically on discovery      │
  └─────────────────────────────────────────────────────┘

Horse Pedigree Backfill:
  ┌─────────────────────────────────────────────────────┐
  │ Progress: ▏                              0.02%      │
  │ 22 / 111,430 horses                                 │
  │ Estimated time: 15.5 hours @ 2 req/sec              │
  └─────────────────────────────────────────────────────┘

Entity Statistics:
  ┌─────────────────────────────────────────────────────┐
  │ Schema:   █████████████████████████ 100% READY      │
  │ Views:    █████████████████████████ 100% READY      │
  │ Function: █████████████████████████ 100% READY      │
  │ Automation: ░░░░░░░░░░░░░░░░░░░░░░░  0% PENDING    │
  └─────────────────────────────────────────────────────┘
```

### API Rate Limit Utilization

```
Daily API Budget: 172,800 calls/day @ 2 req/sec
Daily Usage:      ~550-700 calls/day
Utilization:      0.4% (99.6% headroom)

┌─────────────────────────────────────────────────────────┐
│ API CAPACITY                                            │
├─────────────────────────────────────────────────────────┤
│ Used:     ▏                                     0.4%    │
│ Available: ████████████████████████████████   99.6%    │
└─────────────────────────────────────────────────────────┘

Breakdown:
  Racecards fetch:  ~500 calls/day (90%)
  Horse enrichment: ~50-200 calls/day (10%)
  Statistics:       0 calls (local calculation)
  Analysis queries: 0 calls (on-demand only)
```

---

## Technology Stack

```
┌─────────────────────────────────────────────────────┐
│                   APPLICATION LAYER                  │
├─────────────────────────────────────────────────────┤
│ Language: Python 3.9+                               │
│ Framework: Custom workers + schedulers              │
│ API Client: requests + HTTPBasicAuth                │
│ Rate Limiting: time.sleep(0.5) = 2 req/sec          │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   DATABASE LAYER                     │
├─────────────────────────────────────────────────────┤
│ Platform: Supabase (PostgreSQL 15)                  │
│ Client: supabase-py 2.3.4+                          │
│ Batching: 100 records per upsert                    │
│ Migrations: SQL files in migrations/                │
│ Views: 3 statistics views                           │
│ Functions: 1 update function                        │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│                   EXTERNAL APIs                      │
├─────────────────────────────────────────────────────┤
│ Provider: The Racing API (theracingapi.com)         │
│ Plan: Pro (required for historical data)            │
│ Rate Limit: 2 requests/second                       │
│ Auth: HTTP Basic Authentication                     │
│ Endpoints Used: 2/50+ available                     │
└─────────────────────────────────────────────────────┘
```

---

## File Structure

```
DarkHorses-Masters-Workers/
│
├── config/
│   └── scheduler_config.yaml         # Worker schedules
│
├── utils/
│   ├── entity_extractor.py           # ✨ Horse enrichment logic
│   ├── supabase_client.py            # Database operations
│   └── metadata_tracker.py           # Fetch tracking
│
├── fetchers/
│   ├── races_fetcher.py              # Racecard bulk fetch
│   └── results_fetcher.py            # Results fetch
│
├── scripts/
│   ├── backfill_horse_pedigree.py    # 🔄 Pedigree backfill
│   ├── test_all_entity_endpoints.py  # Endpoint testing
│   └── update_entity_statistics.py   # 📊 Stats update (TODO)
│
├── migrations/
│   ├── 007_add_entity_table_enhancements.sql  # Statistics fields
│   └── 008_add_pedigree_and_horse_fields.sql  # Pedigree support
│
└── docs/
    ├── COMPLETE_ENRICHMENT_ANALYSIS.md        # This analysis
    ├── ENRICHMENT_QUICK_REFERENCE.md          # Quick guide
    ├── ENRICHMENT_ARCHITECTURE.md             # This document
    ├── api_endpoint_inventory.json            # Endpoint catalog
    └── entity_endpoint_test_results.json      # Test results
```

---

## Key Decisions & Rationale

### ✅ Decision 1: Enrich Horses via Pro Endpoint

**Rationale:**
- Only entity with individual Pro endpoint
- Provides 6 unique fields not available elsewhere
- Pedigree data valuable for breeding analysis
- Minimal API overhead (50-200 calls/day)

**Implementation:** COMPLETE

### 📊 Decision 2: Calculate Statistics Locally

**Rationale:**
- API analysis endpoints return calculated stats
- We can calculate same stats from ra_mst_runners
- Avoids 10,000s of redundant API calls
- Gives us full control and customization
- Real-time updates possible

**Implementation:** Schema ready, automation pending

### ❌ Decision 3: Don't Store Results Endpoints

**Rationale:**
- Results endpoints return race history
- We already have this in ra_mst_runners table
- Completely redundant data
- Would waste API quota

**Implementation:** Not implemented (by design)

### ❌ Decision 4: Don't Enrich Individual Races

**Rationale:**
- Individual race endpoint returns same data
- We already fetch complete data via bulk racecards
- Would double our API calls for no benefit

**Implementation:** Not implemented (by design)

### 🔄 Decision 5: Hybrid Horse Enrichment

**Rationale:**
- Only enrich NEW horses (not in database)
- Automatic enrichment on discovery
- One-time backfill for historical horses
- Minimizes API calls while maximizing coverage

**Implementation:** COMPLETE and working

---

## Monitoring & Alerts

### Key Metrics to Track

```
1. Enrichment Coverage
   ✓ Horses with pedigree: 22/111,430 (0.02%)
   ✓ Target: 100% (111,430/111,430)

2. Statistics Freshness
   ⚠ Last updated: (pending automation)
   ✓ Target: < 24 hours old

3. Daily API Usage
   ✓ Current: ~550-700 calls/day
   ✓ Limit: 172,800 calls/day
   ✓ Utilization: 0.4%

4. New Entity Discovery
   ✓ New horses: ~50-200/day
   ✓ New jockeys: ~5-20/day
   ✓ New trainers: ~2-10/day
   ✓ New owners: ~20-50/day
```

### Recommended Alerts

```
CRITICAL:
  - API rate limit > 80% (unlikely at current usage)
  - Database connection failures
  - Enrichment failures > 5%

WARNING:
  - Statistics older than 48 hours
  - Pedigree backfill stalled
  - New entity discovery rate drops 50%

INFO:
  - Daily enrichment summary
  - Statistics update completion
  - API usage trending report
```

---

## Next Steps & Roadmap

### Phase 1: Complete Current Work (Week 1)

```
[ ] 1. Complete pedigree backfill
       - Current: 22/111,430 (0.02%)
       - Run: scripts/backfill_horse_pedigree.py
       - Time: ~15.5 hours
       - When: Overnight/off-peak

[✓] 2. Continue automatic enrichment
       - Already running
       - Monitor: New horses enriched daily
```

### Phase 2: Statistics Automation (Week 2)

```
[ ] 3. Create statistics update script
       - File: scripts/update_entity_statistics.py
       - Function: Call update_entity_statistics()
       - Schedule: Daily at 2 AM

[ ] 4. Add statistics monitoring
       - Alert if stats > 48 hours old
       - Dashboard for freshness
       - Health check endpoints
```

### Phase 3: Optimization (Month 2)

```
[ ] 5. Query performance tuning
       - Analyze slow queries
       - Add targeted indexes
       - Consider materialized views

[ ] 6. Data quality metrics
       - Pedigree completeness %
       - Statistics accuracy validation
       - Missing data reports
```

### Not Planned (By Design)

```
[x] DON'T store API analysis endpoints
[x] DON'T store results endpoints
[x] DON'T enrich individual races
[x] DON'T create jockey/trainer/owner Pro endpoints (don't exist)
```

---

## Conclusion

This architecture provides:

- ✅ **Efficient enrichment** - Only horses (the only entity with Pro endpoint)
- ✅ **Minimal API usage** - 0.4% of rate limit (99.6% headroom)
- ✅ **Local statistics** - No API calls needed, full control
- ✅ **Scalable design** - Can handle 100K+ entities
- ✅ **Future-proof** - Ready for new API endpoints if added

**Key Success:** By calculating statistics locally instead of storing API analysis data, we save 100,000s of API calls while gaining more flexibility and control.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-14
**Status:** Complete architecture documented
**Next Review:** After pedigree backfill completion
