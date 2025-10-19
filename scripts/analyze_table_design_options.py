#!/usr/bin/env python3
"""
Analyze table design options: Combined vs Separated runners table
"""

import psycopg2
import sys

# Connection string
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("TABLE DESIGN ANALYSIS: COMBINED vs SEPARATED RUNNERS")
print("=" * 100)
print()

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Analyze current ra_runners usage
    print("CURRENT STATE ANALYSIS")
    print("-" * 100)
    print()

    # 1. How many rows are racecards only vs results?
    cur.execute("""
        SELECT
            COUNT(*) as total_runners,
            COUNT(*) FILTER (WHERE position IS NULL) as racecards_only,
            COUNT(*) FILTER (WHERE position IS NOT NULL) as with_results,
            ROUND(COUNT(*) FILTER (WHERE position IS NULL)::numeric / COUNT(*)::numeric * 100, 1) as pct_racecards,
            ROUND(COUNT(*) FILTER (WHERE position IS NOT NULL)::numeric / COUNT(*)::numeric * 100, 1) as pct_results
        FROM ra_runners;
    """)

    stats = cur.fetchone()
    total, racecards_only, with_results, pct_rc, pct_res = stats

    print(f"RA_RUNNERS BREAKDOWN:")
    print(f"  Total rows:           {total:>12,}")
    print(f"  Racecards only:       {racecards_only:>12,} ({pct_rc:>5.1f}%) - Future races, no results yet")
    print(f"  With results:         {with_results:>12,} ({pct_res:>5.1f}%) - Completed races")
    print()

    # 2. Column usage analysis - which columns are racecard vs result specific?
    print("COLUMN USAGE BY TYPE:")
    print("-" * 100)
    print()

    cur.execute("""
        SELECT
            -- Racecard-only columns (populated before race)
            COUNT(horse_id) as has_horse_id,
            COUNT(jockey_id) as has_jockey_id,
            COUNT(trainer_id) as has_trainer_id,
            COUNT(draw) as has_draw,
            COUNT(weight_lbs) as has_weight,
            COUNT(official_rating) as has_rating,

            -- Result-only columns (populated after race)
            COUNT(position) as has_position,
            COUNT(distance_beaten) as has_distance_beaten,
            COUNT(prize_won) as has_prize,
            COUNT(starting_price) as has_sp,
            COUNT(finishing_time) as has_time
        FROM ra_runners;
    """)

    usage = cur.fetchone()
    horse_id, jockey_id, trainer_id, draw, weight, rating, position, dist, prize, sp, time = usage

    print("RACECARD COLUMNS (populated before race):")
    print(f"  horse_id:         {horse_id:>12,} ({horse_id/total*100:>5.1f}%)")
    print(f"  jockey_id:        {jockey_id:>12,} ({jockey_id/total*100:>5.1f}%)")
    print(f"  trainer_id:       {trainer_id:>12,} ({trainer_id/total*100:>5.1f}%)")
    print(f"  draw:             {draw:>12,} ({draw/total*100:>5.1f}%)")
    print(f"  weight_lbs:       {weight:>12,} ({weight/total*100:>5.1f}%)")
    print(f"  official_rating:  {rating:>12,} ({rating/total*100:>5.1f}%)")
    print()

    print("RESULT COLUMNS (populated after race):")
    print(f"  position:         {position:>12,} ({position/total*100:>5.1f}%)")
    print(f"  distance_beaten:  {dist:>12,} ({dist/total*100:>5.1f}%)")
    print(f"  prize_won:        {prize:>12,} ({prize/total*100:>5.1f}%)")
    print(f"  starting_price:   {sp:>12,} ({sp/total*100:>5.1f}%)")
    print(f"  finishing_time:   {time:>12,} ({time/total*100:>5.1f}%)")
    print()

    # 3. Storage analysis - how much overlap?
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE position IS NULL AND horse_id IS NOT NULL) as racecard_complete,
            COUNT(*) FILTER (WHERE position IS NOT NULL AND horse_id IS NOT NULL) as result_complete,
            COUNT(*) FILTER (WHERE position IS NULL AND horse_id IS NULL) as incomplete_racecard,
            COUNT(*) FILTER (WHERE position IS NOT NULL AND horse_id IS NULL) as incomplete_result
        FROM ra_runners;
    """)

    rc_complete, res_complete, rc_incomplete, res_incomplete = cur.fetchone()

    print("DATA COMPLETENESS:")
    print(f"  Complete racecards (no result):  {rc_complete:>12,}")
    print(f"  Complete results (with racecard): {res_complete:>12,}")
    print(f"  Incomplete racecards:             {rc_incomplete:>12,}")
    print(f"  Incomplete results:               {res_incomplete:>12,}")
    print()

    # 4. Duplication check - are there any duplicate runner_ids?
    cur.execute("""
        SELECT COUNT(*) as duplicate_runner_ids
        FROM (
            SELECT runner_id, COUNT(*)
            FROM ra_runners
            GROUP BY runner_id
            HAVING COUNT(*) > 1
        ) duplicates;
    """)

    duplicates = cur.fetchone()[0]
    print(f"Duplicate runner_ids: {duplicates}")
    print()

    # 5. Update frequency - how often do rows get updated?
    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE created_at = updated_at) as never_updated,
            COUNT(*) FILTER (WHERE created_at != updated_at) as has_updates,
            ROUND(COUNT(*) FILTER (WHERE created_at != updated_at)::numeric / COUNT(*)::numeric * 100, 1) as pct_updated
        FROM ra_runners;
    """)

    never_updated, has_updates, pct_updated = cur.fetchone()

    print(f"UPDATE PATTERNS:")
    print(f"  Never updated (created=updated): {never_updated:>12,} ({100-pct_updated:>5.1f}%)")
    print(f"  Updated after creation:          {has_updates:>12,} ({pct_updated:>5.1f}%)")
    print()

    # 6. Check ra_results table structure
    print("=" * 100)
    print("RA_RESULTS TABLE (Legacy/Unused)")
    print("=" * 100)
    print()

    cur.execute("""
        SELECT column_name, data_type
        FROM information_schema.columns
        WHERE table_name = 'ra_results'
        ORDER BY ordinal_position;
    """)

    print("Current schema:")
    for col, dtype in cur.fetchall():
        print(f"  {col:<30} {dtype}")
    print()

    cur.execute("SELECT COUNT(*) FROM ra_results;")
    results_count = cur.fetchone()[0]
    print(f"Row count: {results_count}")
    print()

    print("=" * 100)
    print("DESIGN OPTION ANALYSIS")
    print("=" * 100)
    print()

    # Calculate potential table sizes
    print("OPTION 1: KEEP CURRENT (Combined ra_runners)")
    print("-" * 100)
    print()
    print("Structure:")
    print("  • ra_runners: 1.3M rows (racecards + results combined)")
    print("  • Single table with all 75 columns")
    print()
    print("Pros:")
    print("  ✓ Simple queries - no JOINs needed for race + result data")
    print("  ✓ Single source of truth")
    print("  ✓ Natural UPDATE workflow (racecard → result)")
    print("  ✓ Easy to find 'races without results' (WHERE position IS NULL)")
    print("  ✓ Consistent runner_id across lifecycle")
    print()
    print("Cons:")
    print("  ✗ Many NULL values for racecards-only (9.9% of rows)")
    print("  ✗ Mixed purpose table (both static and mutable data)")
    print("  ✗ Can't easily distinguish 'never had result' vs 'result pending'")
    print("  ✗ Result columns wasted space for future racecards")
    print()

    print("OPTION 2: SEPARATE INTO TWO TABLES")
    print("-" * 100)
    print()
    print("Structure:")
    print("  • ra_racecards: ~132K rows (racecard data only)")
    print("  • ra_race_results: ~1.2M rows (result data only)")
    print("  • Or: ra_entries + ra_results")
    print()
    print("Pros:")
    print("  ✓ Clear separation of concerns")
    print("  ✓ Racecard table has fewer NULL columns")
    print("  ✓ Can add racecard-specific fields without affecting results")
    print("  ✓ Clearer data lifecycle (racecard → race → result)")
    print("  ✓ Better normalization")
    print()
    print("Cons:")
    print("  ✗ Requires JOIN for most queries (racecard + result)")
    print("  ✗ More complex UPDATE logic (insert racecard, later insert result)")
    print("  ✗ Need to maintain two tables instead of one")
    print("  ✗ Harder to find 'races pending results' (need LEFT JOIN)")
    print("  ✗ More foreign key constraints to manage")
    print()

    print("OPTION 3: HYBRID - Keep Combined + Add View")
    print("-" * 100)
    print()
    print("Structure:")
    print("  • ra_runners: 1.3M rows (current combined table)")
    print("  • CREATE VIEW ra_racecards AS SELECT ... WHERE position IS NULL")
    print("  • CREATE VIEW ra_results AS SELECT ... WHERE position IS NOT NULL")
    print()
    print("Pros:")
    print("  ✓ Best of both worlds")
    print("  ✓ Backward compatible (no code changes)")
    print("  ✓ Views provide logical separation")
    print("  ✓ Simple queries can use views")
    print("  ✓ Complex queries can use base table")
    print()
    print("Cons:")
    print("  ✗ Views add slight query overhead")
    print("  ✗ Still have NULL values in base table")
    print("  ✗ May confuse users about which to query")
    print()

    # Naming convention analysis
    print("=" * 100)
    print("NAMING CONVENTION ANALYSIS")
    print("=" * 100)
    print()

    print("CURRENT NAMING:")
    print("-" * 100)
    tables = [
        ('ra_courses', 'Reference data'),
        ('ra_bookmakers', 'Reference data'),
        ('ra_jockeys', 'Reference data'),
        ('ra_trainers', 'Reference data'),
        ('ra_owners', 'Reference data'),
        ('ra_horses', 'Reference data'),
        ('ra_horse_pedigree', 'Reference data (detail)'),
        ('ra_races', 'Race metadata'),
        ('ra_runners', 'Race entries + results (COMBINED)'),
        ('ra_results', 'Legacy - unused'),
        ('ra_odds_*', 'Odds data (separate system)'),
    ]

    for table, purpose in tables:
        print(f"  {table:<30} - {purpose}")
    print()

    print("PROPOSED NAMING (if separating):")
    print("-" * 100)
    print()
    print("Option A: Entry/Result Pattern")
    print("  ra_race_entries    - Racecard data (pre-race)")
    print("  ra_race_results    - Result data (post-race)")
    print()
    print("Option B: Racecard/Result Pattern")
    print("  ra_racecards       - Racecard data (pre-race)")
    print("  ra_results         - Result data (post-race)")
    print()
    print("Option C: Runner Status Pattern")
    print("  ra_runners         - Racecard data (pre-race)")
    print("  ra_runner_results  - Result data (post-race)")
    print()
    print("Option D: Keep Current + Views")
    print("  ra_runners         - Combined table (as is)")
    print("  CREATE VIEW ra_racecards AS ...")
    print("  CREATE VIEW ra_race_results AS ...")
    print()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
