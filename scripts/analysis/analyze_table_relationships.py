#!/usr/bin/env python3
"""
Analyze table relationships and data flow in the racing database
"""

import psycopg2
import sys
from datetime import datetime

# Connection string
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("DATABASE TABLE RELATIONSHIPS & DATA FLOW ANALYSIS")
print("=" * 100)
print()

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Get all ra_ tables
    cur.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        AND table_name LIKE 'ra_%'
        ORDER BY table_name;
    """)

    tables = [row[0] for row in cur.fetchall()]

    print("TABLES IN DATABASE:")
    print("-" * 100)

    # Get row counts for each table
    for table in tables:
        cur.execute(f"SELECT COUNT(*) FROM {table};")
        count = cur.fetchone()[0]
        print(f"  {table:<30} {count:>15,} rows")

    print()
    print("=" * 100)
    print("TABLE RELATIONSHIPS")
    print("=" * 100)
    print()

    # Check if ra_results exists as a separate table
    if 'ra_results' in tables:
        print("⚠️  DUPLICATE TABLE DETECTED: ra_results")
        print()
        print("Schema check:")
        cur.execute("""
            SELECT column_name, data_type
            FROM information_schema.columns
            WHERE table_name = 'ra_results'
            ORDER BY ordinal_position
            LIMIT 20;
        """)
        print("  ra_results columns:")
        for col, dtype in cur.fetchall():
            print(f"    - {col}: {dtype}")
        print()

    # Analyze ra_mst_runners - this is the main results table
    print("RA_RUNNERS STRUCTURE:")
    print("-" * 100)
    print()
    print("Purpose: Stores race entries AND results (combined)")
    print()
    print("Key Relationships:")
    print("  • race_id → ra_races (which race)")
    print("  • horse_id → ra_horses (which horse)")
    print("  • jockey_id → ra_jockeys")
    print("  • trainer_id → ra_trainers")
    print("  • owner_id → ra_owners")
    print()

    # Check for horses that ran multiple races in one day
    print("=" * 100)
    print("SAME-DAY MULTIPLE RACES ANALYSIS")
    print("=" * 100)
    print()

    cur.execute("""
        WITH race_dates AS (
            SELECT
                race_id,
                race_date,
                off_time,
                off_datetime
            FROM ra_races
            WHERE race_date IS NOT NULL
        )
        SELECT
            run.horse_id,
            run.horse_name,
            r.race_date,
            COUNT(*) as races_that_day,
            STRING_AGG(r.off_time || ' (' || COALESCE(run.position::text, 'no result') || ')', ', ' ORDER BY r.off_time) as race_times_and_positions
        FROM ra_mst_runners run
        JOIN race_dates r ON run.race_id = r.race_id
        WHERE r.race_date IS NOT NULL
        GROUP BY run.horse_id, run.horse_name, r.race_date
        HAVING COUNT(*) > 1
        ORDER BY r.race_date DESC
        LIMIT 10;
    """)

    multi_race_horses = cur.fetchall()

    if multi_race_horses:
        print(f"Found {len(multi_race_horses)} cases of horses running multiple races same day:")
        print()
        for horse_id, horse_name, race_date, num_races, details in multi_race_horses:
            print(f"  {horse_name} on {race_date}:")
            print(f"    Races: {num_races}")
            print(f"    Times & Results: {details}")
            print()
    else:
        print("No horses found running multiple races on the same day")
        print()

    # Check how results are stored
    print("=" * 100)
    print("RESULTS DATA STORAGE")
    print("=" * 100)
    print()

    cur.execute("""
        SELECT
            COUNT(*) as total_runners,
            COUNT(position) as with_position,
            COUNT(distance_beaten) as with_distance_beaten,
            COUNT(prize_won) as with_prize,
            COUNT(starting_price) as with_sp,
            COUNT(finishing_time) as with_time
        FROM ra_mst_runners;
    """)

    stats = cur.fetchone()
    total, pos, dist, prize, sp, time = stats

    print("RA_RUNNERS DATA POPULATION:")
    print(f"  Total runners:        {total:>12,}")
    print(f"  With position:        {pos:>12,} ({pos/total*100:>5.1f}%)")
    print(f"  With distance beaten: {dist:>12,} ({dist/total*100:>5.1f}%)")
    print(f"  With prize won:       {prize:>12,} ({prize/total*100:>5.1f}%)")
    print(f"  With starting price:  {sp:>12,} ({sp/total*100:>5.1f}%)")
    print(f"  With finishing time:  {time:>12,} ({time/total*100:>5.1f}%)")
    print()

    # Check timing of updates
    print("=" * 100)
    print("UPDATE TIMING ANALYSIS")
    print("=" * 100)
    print()

    cur.execute("""
        SELECT
            COUNT(*) FILTER (WHERE position IS NOT NULL) as results_count,
            MIN(updated_at) as earliest_result_update,
            MAX(updated_at) as latest_result_update,
            COUNT(DISTINCT DATE(updated_at)) as days_with_updates
        FROM ra_mst_runners
        WHERE position IS NOT NULL;
    """)

    res_stats = cur.fetchone()
    res_count, earliest, latest, days = res_stats

    print("RESULT UPDATE HISTORY:")
    print(f"  Total results:      {res_count:>12,}")
    print(f"  Earliest update:    {earliest}")
    print(f"  Latest update:      {latest}")
    print(f"  Days with updates:  {days:>12,}")
    print()

    # Check if there's a pattern - are results added later?
    print("=" * 100)
    print("RACECARD vs RESULTS TIMING")
    print("=" * 100)
    print()

    cur.execute("""
        SELECT
            r.race_date,
            r.off_time,
            COUNT(*) as runners,
            COUNT(run.position) as with_results,
            MIN(run.created_at) as first_runner_added,
            MAX(run.updated_at) as last_runner_updated
        FROM ra_races r
        LEFT JOIN ra_mst_runners run ON r.race_id = run.race_id
        WHERE r.race_date >= CURRENT_DATE - INTERVAL '7 days'
        GROUP BY r.race_id, r.race_date, r.off_time
        ORDER BY r.race_date DESC, r.off_time DESC
        LIMIT 20;
    """)

    print("Recent races (last 7 days):")
    print(f"{'Date':<12} {'Time':<8} {'Runners':<8} {'Results':<8} {'First Added':<20} {'Last Updated':<20}")
    print("-" * 100)

    for race_date, off_time, runners, results, first_add, last_upd in cur.fetchall():
        results_pct = f"{results}/{runners}" if runners else "0/0"
        print(f"{str(race_date):<12} {str(off_time):<8} {runners:<8} {results_pct:<8} {str(first_add)[:19]:<20} {str(last_upd)[:19]:<20}")

    print()

    # Check for foreign key constraints
    print("=" * 100)
    print("FOREIGN KEY CONSTRAINTS")
    print("=" * 100)
    print()

    cur.execute("""
        SELECT
            tc.table_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        JOIN information_schema.constraint_column_usage AS ccu
            ON ccu.constraint_name = tc.constraint_name
            AND ccu.table_schema = tc.table_schema
        WHERE tc.constraint_type = 'FOREIGN KEY'
        AND tc.table_name LIKE 'ra_%'
        ORDER BY tc.table_name, kcu.column_name;
    """)

    fks = cur.fetchall()

    if fks:
        print("Foreign keys defined:")
        for table, col, ref_table, ref_col in fks:
            print(f"  {table}.{col} → {ref_table}.{ref_col}")
        print()
    else:
        print("⚠️  NO FOREIGN KEY CONSTRAINTS DEFINED")
        print()
        print("This means:")
        print("  • Tables are related by convention (matching IDs) not constraints")
        print("  • No referential integrity enforced at database level")
        print("  • Application code is responsible for data consistency")
        print()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
