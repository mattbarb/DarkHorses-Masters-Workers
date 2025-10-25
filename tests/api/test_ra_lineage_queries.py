#!/usr/bin/env python3
"""
Test ra_lineage table with example queries from design proposal
"""

import psycopg2
import sys

# Connection string
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

print("=" * 100)
print("RA_LINEAGE TABLE TEST QUERIES")
print("=" * 100)
print()

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # =========================================================================
    # Query 1: Get full pedigree for a specific runner
    # =========================================================================
    print("QUERY 1: Get full pedigree for a specific runner")
    print("-" * 100)

    # First, pick a random runner with lineage data
    cur.execute("""
        SELECT DISTINCT runner_id
        FROM ra_lineage
        LIMIT 1;
    """)
    test_runner_id = cur.fetchone()[0]

    print(f"Runner ID: {test_runner_id}")
    print()

    cur.execute("""
        SELECT
            generation,
            relation_type,
            lineage_path,
            ancestor_name,
            ancestor_region
        FROM ra_lineage
        WHERE runner_id = %s
        ORDER BY generation, lineage_path;
    """, (test_runner_id,))

    print(f"{'Gen':<5} {'Relation':<25} {'Path':<15} {'Ancestor':<30} {'Region':<10}")
    print("-" * 100)
    for gen, rel, path, name, region in cur.fetchall():
        region_str = region or 'N/A'
        print(f"{gen:<5} {rel:<25} {path:<15} {name:<30} {region_str:<10}")

    print()
    print()

    # =========================================================================
    # Query 2: Find all runners with a specific sire (e.g., Galileo)
    # =========================================================================
    print("QUERY 2: Find all runners with a specific sire")
    print("-" * 100)

    # Find a popular sire first
    cur.execute("""
        SELECT
            ancestor_name,
            COUNT(DISTINCT runner_id) as runner_count
        FROM ra_lineage
        WHERE relation_type = 'sire'
        GROUP BY ancestor_name
        ORDER BY runner_count DESC
        LIMIT 1;
    """)

    top_sire, count = cur.fetchone()
    print(f"Most popular sire: {top_sire} ({count:,} runners)")
    print()

    # Get sample runners with this sire
    cur.execute("""
        SELECT DISTINCT
            l.runner_id,
            r.horse_name,
            rac.race_date,
            rac.course_name,
            r.position
        FROM ra_lineage l
        JOIN ra_runners r ON l.runner_id = r.runner_id
        JOIN ra_races rac ON r.race_id = rac.race_id
        WHERE l.ancestor_name = %s
        AND l.relation_type = 'sire'
        ORDER BY rac.race_date DESC
        LIMIT 10;
    """, (top_sire,))

    print(f"Sample runners with sire = {top_sire}:")
    print(f"{'Date':<12} {'Horse':<30} {'Course':<30} {'Pos':<5}")
    print("-" * 100)
    for runner_id, horse_name, race_date, course, position in cur.fetchall():
        pos_str = str(position) if position else 'N/A'
        print(f"{race_date} {horse_name:<30} {course:<30} {pos_str:<5}")

    print()
    print()

    # =========================================================================
    # Query 3: Sire Performance Analysis
    # =========================================================================
    print("QUERY 3: Sire Performance Analysis (Top 10 by wins)")
    print("-" * 100)

    cur.execute("""
        SELECT
            l.ancestor_name as sire,
            COUNT(*) as total_runners,
            COUNT(*) FILTER (WHERE r.position = '1') as wins,
            COUNT(*) FILTER (WHERE r.position::int <= 3) as places,
            ROUND(AVG(CASE WHEN r.position IS NOT NULL THEN r.position::int END), 2) as avg_position,
            SUM(COALESCE(r.prize_won, 0)) as total_prize_money
        FROM ra_lineage l
        JOIN ra_runners r ON l.runner_id = r.runner_id
        WHERE l.relation_type = 'sire'
        AND r.position IS NOT NULL
        GROUP BY l.ancestor_name
        HAVING COUNT(*) >= 100
        ORDER BY wins DESC
        LIMIT 10;
    """)

    print(f"{'Sire':<30} {'Runners':<10} {'Wins':<8} {'Places':<8} {'Avg Pos':<10} {'Prize £':<15}")
    print("-" * 100)
    for sire, runners, wins, places, avg_pos, prize in cur.fetchall():
        avg_pos_str = f"{avg_pos:.2f}" if avg_pos else 'N/A'
        prize_str = f"£{prize:,.0f}" if prize else '£0'
        print(f"{sire:<30} {runners:<10,} {wins:<8,} {places:<8,} {avg_pos_str:<10} {prize_str:<15}")

    print()
    print()

    # =========================================================================
    # Query 4: Dam Performance Analysis
    # =========================================================================
    print("QUERY 4: Dam Performance Analysis (Top 10 by win rate)")
    print("-" * 100)

    cur.execute("""
        SELECT
            l.ancestor_name as dam,
            COUNT(*) as total_runners,
            COUNT(*) FILTER (WHERE r.position = '1') as wins,
            ROUND(COUNT(*) FILTER (WHERE r.position = '1')::numeric / COUNT(*)::numeric * 100, 1) as win_rate
        FROM ra_lineage l
        JOIN ra_runners r ON l.runner_id = r.runner_id
        WHERE l.relation_type = 'dam'
        AND r.position IS NOT NULL
        GROUP BY l.ancestor_name
        HAVING COUNT(*) >= 50
        ORDER BY win_rate DESC, wins DESC
        LIMIT 10;
    """)

    print(f"{'Dam':<40} {'Runners':<10} {'Wins':<8} {'Win %':<10}")
    print("-" * 100)
    for dam, runners, wins, win_rate in cur.fetchall():
        print(f"{dam:<40} {runners:<10,} {wins:<8,} {win_rate:<10.1f}%")

    print()
    print()

    # =========================================================================
    # Query 5: Lineage Statistics Summary
    # =========================================================================
    print("QUERY 5: Lineage Statistics Summary")
    print("-" * 100)

    cur.execute("""
        SELECT
            COUNT(DISTINCT runner_id) as total_runners,
            COUNT(DISTINCT horse_id) as unique_horses,
            COUNT(DISTINCT ancestor_horse_id) as unique_ancestors,
            COUNT(*) as total_lineage_records
        FROM ra_lineage;
    """)

    total_runners, unique_horses, unique_ancestors, total_records = cur.fetchone()

    print(f"Total runners:          {total_runners:>12,}")
    print(f"Unique horses:          {unique_horses:>12,}")
    print(f"Unique ancestors:       {unique_ancestors:>12,}")
    print(f"Total lineage records:  {total_records:>12,}")
    print()

    # Breakdown by generation
    cur.execute("""
        SELECT
            generation,
            relation_type,
            COUNT(*) as count,
            COUNT(DISTINCT ancestor_horse_id) as unique_ancestors
        FROM ra_lineage
        GROUP BY generation, relation_type
        ORDER BY generation, relation_type;
    """)

    print("Breakdown by generation:")
    print(f"{'Gen':<5} {'Relation':<25} {'Records':<15} {'Unique Ancestors':<20}")
    print("-" * 100)
    for gen, rel, count, unique in cur.fetchall():
        print(f"{gen:<5} {rel:<25} {count:<15,} {unique:<20,}")

    print()
    print("=" * 100)
    print("TEST QUERIES COMPLETED SUCCESSFULLY")
    print("=" * 100)
    print()

    cur.close()
    conn.close()

except psycopg2.Error as e:
    print(f"❌ Database error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

except Exception as e:
    print(f"❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
