#!/usr/bin/env python3
"""
Backfill ancestor statistics tables with:
1. Ancestor's own racing career results (from ra_mst_runners where horse_id = ancestor_id)
2. Progeny/grandoffspring performance statistics (from ra_lineage + ra_mst_runners)
"""

import psycopg2
import sys
from datetime import datetime

print("=" * 100)
print("BACKFILLING ANCESTOR STATISTICS TABLES")
print("=" * 100)
print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

# Database connection
conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

try:
    print("Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False  # Use transactions for data integrity
    cur = conn.cursor()
    print("✓ Connected")
    print()

    # =============================================================================
    # PART 1: Populate ra_sire_stats
    # =============================================================================

    print("=" * 100)
    print("PART 1: POPULATING ra_sire_stats")
    print("=" * 100)
    print()

    print("Step 1: Calculating sire statistics...")
    print("-" * 100)

    cur.execute("""
        INSERT INTO ra_sire_stats (
            sire_id,
            sire_name,
            sire_region,

            -- Own racing career (from ra_mst_runners where horse_id = sire_id)
            own_race_runs,
            own_race_wins,
            own_race_places,
            own_total_prize,
            own_best_position,
            own_avg_position,
            own_career_start,
            own_career_end,

            -- Progeny statistics (from ra_lineage + ra_mst_runners)
            total_progeny,
            progeny_total_runs,
            progeny_wins,
            progeny_places,
            progeny_total_prize,
            progeny_win_rate,
            progeny_place_rate,
            progeny_avg_position,

            created_at,
            updated_at
        )
        SELECT
            l.ancestor_horse_id as sire_id,
            l.ancestor_name as sire_name,
            l.ancestor_region as sire_region,

            -- Sire's own racing career
            COALESCE(own.race_runs, 0) as own_race_runs,
            COALESCE(own.race_wins, 0) as own_race_wins,
            COALESCE(own.race_places, 0) as own_race_places,
            COALESCE(own.total_prize, 0) as own_total_prize,
            own.best_position as own_best_position,
            own.avg_position as own_avg_position,
            own.career_start as own_career_start,
            own.career_end as own_career_end,

            -- Progeny statistics
            COALESCE(prog.total_progeny, 0) as total_progeny,
            COALESCE(prog.total_runs, 0) as progeny_total_runs,
            COALESCE(prog.wins, 0) as progeny_wins,
            COALESCE(prog.places, 0) as progeny_places,
            COALESCE(prog.total_prize, 0) as progeny_total_prize,
            CASE
                WHEN prog.total_runs > 0 THEN ROUND((prog.wins::numeric / prog.total_runs::numeric) * 100, 2)
                ELSE NULL
            END as progeny_win_rate,
            CASE
                WHEN prog.total_runs > 0 THEN ROUND((prog.places::numeric / prog.total_runs::numeric) * 100, 2)
                ELSE NULL
            END as progeny_place_rate,
            prog.avg_position as progeny_avg_position,

            NOW() as created_at,
            NOW() as updated_at

        FROM (
            -- Get unique sires from lineage (use MAX to handle duplicates with different names/regions)
            SELECT
                ancestor_horse_id,
                MAX(ancestor_name) as ancestor_name,
                MAX(ancestor_region) as ancestor_region
            FROM ra_lineage
            WHERE relation_type = 'sire'
            AND ancestor_horse_id IS NOT NULL
            GROUP BY ancestor_horse_id
        ) l

        -- Left join sire's own racing career
        LEFT JOIN (
            SELECT
                horse_id,
                COUNT(*) as race_runs,
                SUM(CASE WHEN position = '1' THEN 1 ELSE 0 END) as race_wins,
                SUM(CASE WHEN position::int <= 3 THEN 1 ELSE 0 END) as race_places,
                SUM(COALESCE(prize_won, 0)) as total_prize,
                MIN(CASE WHEN position IS NOT NULL THEN position::int ELSE NULL END) as best_position,
                ROUND(AVG(CASE WHEN position IS NOT NULL THEN position::int ELSE NULL END), 2) as avg_position,
                MIN(race_date) as career_start,
                MAX(race_date) as career_end
            FROM ra_mst_runners r
            JOIN ra_races rac ON r.race_id = rac.race_id
            WHERE r.position IS NOT NULL
            GROUP BY horse_id
        ) own ON l.ancestor_horse_id = own.horse_id

        -- Left join progeny performance
        LEFT JOIN (
            SELECT
                lin.ancestor_horse_id,
                COUNT(DISTINCT lin.horse_id) as total_progeny,
                COUNT(*) as total_runs,
                SUM(CASE WHEN r.position = '1' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.position::int <= 3 THEN 1 ELSE 0 END) as places,
                SUM(COALESCE(r.prize_won, 0)) as total_prize,
                ROUND(AVG(CASE WHEN r.position IS NOT NULL THEN r.position::int ELSE NULL END), 2) as avg_position
            FROM ra_lineage lin
            JOIN ra_mst_runners r ON lin.runner_id = r.runner_id
            WHERE lin.relation_type = 'sire'
            AND r.position IS NOT NULL
            GROUP BY lin.ancestor_horse_id
        ) prog ON l.ancestor_horse_id = prog.ancestor_horse_id

        ON CONFLICT (sire_id) DO UPDATE SET
            sire_name = EXCLUDED.sire_name,
            sire_region = EXCLUDED.sire_region,
            own_race_runs = EXCLUDED.own_race_runs,
            own_race_wins = EXCLUDED.own_race_wins,
            own_race_places = EXCLUDED.own_race_places,
            own_total_prize = EXCLUDED.own_total_prize,
            own_best_position = EXCLUDED.own_best_position,
            own_avg_position = EXCLUDED.own_avg_position,
            own_career_start = EXCLUDED.own_career_start,
            own_career_end = EXCLUDED.own_career_end,
            total_progeny = EXCLUDED.total_progeny,
            progeny_total_runs = EXCLUDED.progeny_total_runs,
            progeny_wins = EXCLUDED.progeny_wins,
            progeny_places = EXCLUDED.progeny_places,
            progeny_total_prize = EXCLUDED.progeny_total_prize,
            progeny_win_rate = EXCLUDED.progeny_win_rate,
            progeny_place_rate = EXCLUDED.progeny_place_rate,
            progeny_avg_position = EXCLUDED.progeny_avg_position,
            updated_at = NOW();
    """)

    sire_count = cur.rowcount
    conn.commit()
    print(f"✓ Inserted/updated {sire_count:,} sire records")
    print()

    # =============================================================================
    # PART 2: Populate ra_dam_stats
    # =============================================================================

    print("=" * 100)
    print("PART 2: POPULATING ra_dam_stats")
    print("=" * 100)
    print()

    print("Step 1: Calculating dam statistics...")
    print("-" * 100)

    cur.execute("""
        INSERT INTO ra_dam_stats (
            dam_id,
            dam_name,
            dam_region,

            -- Own racing career
            own_race_runs,
            own_race_wins,
            own_race_places,
            own_total_prize,
            own_best_position,
            own_avg_position,
            own_career_start,
            own_career_end,

            -- Progeny statistics
            total_progeny,
            progeny_total_runs,
            progeny_wins,
            progeny_places,
            progeny_total_prize,
            progeny_win_rate,
            progeny_place_rate,
            progeny_avg_position,

            created_at,
            updated_at
        )
        SELECT
            l.ancestor_horse_id as dam_id,
            l.ancestor_name as dam_name,
            l.ancestor_region as dam_region,

            -- Dam's own racing career
            COALESCE(own.race_runs, 0) as own_race_runs,
            COALESCE(own.race_wins, 0) as own_race_wins,
            COALESCE(own.race_places, 0) as own_race_places,
            COALESCE(own.total_prize, 0) as own_total_prize,
            own.best_position as own_best_position,
            own.avg_position as own_avg_position,
            own.career_start as own_career_start,
            own.career_end as own_career_end,

            -- Progeny statistics
            COALESCE(prog.total_progeny, 0) as total_progeny,
            COALESCE(prog.total_runs, 0) as progeny_total_runs,
            COALESCE(prog.wins, 0) as progeny_wins,
            COALESCE(prog.places, 0) as progeny_places,
            COALESCE(prog.total_prize, 0) as progeny_total_prize,
            CASE
                WHEN prog.total_runs > 0 THEN ROUND((prog.wins::numeric / prog.total_runs::numeric) * 100, 2)
                ELSE NULL
            END as progeny_win_rate,
            CASE
                WHEN prog.total_runs > 0 THEN ROUND((prog.places::numeric / prog.total_runs::numeric) * 100, 2)
                ELSE NULL
            END as progeny_place_rate,
            prog.avg_position as progeny_avg_position,

            NOW() as created_at,
            NOW() as updated_at

        FROM (
            -- Get unique dams from lineage (use MAX to handle duplicates with different names/regions)
            SELECT
                ancestor_horse_id,
                MAX(ancestor_name) as ancestor_name,
                MAX(ancestor_region) as ancestor_region
            FROM ra_lineage
            WHERE relation_type = 'dam'
            AND ancestor_horse_id IS NOT NULL
            GROUP BY ancestor_horse_id
        ) l

        -- Left join dam's own racing career
        LEFT JOIN (
            SELECT
                horse_id,
                COUNT(*) as race_runs,
                SUM(CASE WHEN position = '1' THEN 1 ELSE 0 END) as race_wins,
                SUM(CASE WHEN position::int <= 3 THEN 1 ELSE 0 END) as race_places,
                SUM(COALESCE(prize_won, 0)) as total_prize,
                MIN(CASE WHEN position IS NOT NULL THEN position::int ELSE NULL END) as best_position,
                ROUND(AVG(CASE WHEN position IS NOT NULL THEN position::int ELSE NULL END), 2) as avg_position,
                MIN(race_date) as career_start,
                MAX(race_date) as career_end
            FROM ra_mst_runners r
            JOIN ra_races rac ON r.race_id = rac.race_id
            WHERE r.position IS NOT NULL
            GROUP BY horse_id
        ) own ON l.ancestor_horse_id = own.horse_id

        -- Left join progeny performance
        LEFT JOIN (
            SELECT
                lin.ancestor_horse_id,
                COUNT(DISTINCT lin.horse_id) as total_progeny,
                COUNT(*) as total_runs,
                SUM(CASE WHEN r.position = '1' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.position::int <= 3 THEN 1 ELSE 0 END) as places,
                SUM(COALESCE(r.prize_won, 0)) as total_prize,
                ROUND(AVG(CASE WHEN r.position IS NOT NULL THEN r.position::int ELSE NULL END), 2) as avg_position
            FROM ra_lineage lin
            JOIN ra_mst_runners r ON lin.runner_id = r.runner_id
            WHERE lin.relation_type = 'dam'
            AND r.position IS NOT NULL
            GROUP BY lin.ancestor_horse_id
        ) prog ON l.ancestor_horse_id = prog.ancestor_horse_id

        ON CONFLICT (dam_id) DO UPDATE SET
            dam_name = EXCLUDED.dam_name,
            dam_region = EXCLUDED.dam_region,
            own_race_runs = EXCLUDED.own_race_runs,
            own_race_wins = EXCLUDED.own_race_wins,
            own_race_places = EXCLUDED.own_race_places,
            own_total_prize = EXCLUDED.own_total_prize,
            own_best_position = EXCLUDED.own_best_position,
            own_avg_position = EXCLUDED.own_avg_position,
            own_career_start = EXCLUDED.own_career_start,
            own_career_end = EXCLUDED.own_career_end,
            total_progeny = EXCLUDED.total_progeny,
            progeny_total_runs = EXCLUDED.progeny_total_runs,
            progeny_wins = EXCLUDED.progeny_wins,
            progeny_places = EXCLUDED.progeny_places,
            progeny_total_prize = EXCLUDED.progeny_total_prize,
            progeny_win_rate = EXCLUDED.progeny_win_rate,
            progeny_place_rate = EXCLUDED.progeny_place_rate,
            progeny_avg_position = EXCLUDED.progeny_avg_position,
            updated_at = NOW();
    """)

    dam_count = cur.rowcount
    conn.commit()
    print(f"✓ Inserted/updated {dam_count:,} dam records")
    print()

    # =============================================================================
    # PART 3: Populate ra_damsire_stats
    # =============================================================================

    print("=" * 100)
    print("PART 3: POPULATING ra_damsire_stats")
    print("=" * 100)
    print()

    print("Step 1: Calculating damsire statistics...")
    print("-" * 100)

    cur.execute("""
        INSERT INTO ra_damsire_stats (
            damsire_id,
            damsire_name,
            damsire_region,

            -- Own racing career
            own_race_runs,
            own_race_wins,
            own_race_places,
            own_total_prize,
            own_best_position,
            own_avg_position,
            own_career_start,
            own_career_end,

            -- Grandoffspring statistics
            total_grandoffspring,
            grandoffspring_total_runs,
            grandoffspring_wins,
            grandoffspring_places,
            grandoffspring_total_prize,
            grandoffspring_win_rate,
            grandoffspring_place_rate,
            grandoffspring_avg_position,

            created_at,
            updated_at
        )
        SELECT
            l.ancestor_horse_id as damsire_id,
            l.ancestor_name as damsire_name,
            l.ancestor_region as damsire_region,

            -- Damsire's own racing career
            COALESCE(own.race_runs, 0) as own_race_runs,
            COALESCE(own.race_wins, 0) as own_race_wins,
            COALESCE(own.race_places, 0) as own_race_places,
            COALESCE(own.total_prize, 0) as own_total_prize,
            own.best_position as own_best_position,
            own.avg_position as own_avg_position,
            own.career_start as own_career_start,
            own.career_end as own_career_end,

            -- Grandoffspring statistics
            COALESCE(grand.total_grandoffspring, 0) as total_grandoffspring,
            COALESCE(grand.total_runs, 0) as grandoffspring_total_runs,
            COALESCE(grand.wins, 0) as grandoffspring_wins,
            COALESCE(grand.places, 0) as grandoffspring_places,
            COALESCE(grand.total_prize, 0) as grandoffspring_total_prize,
            CASE
                WHEN grand.total_runs > 0 THEN ROUND((grand.wins::numeric / grand.total_runs::numeric) * 100, 2)
                ELSE NULL
            END as grandoffspring_win_rate,
            CASE
                WHEN grand.total_runs > 0 THEN ROUND((grand.places::numeric / grand.total_runs::numeric) * 100, 2)
                ELSE NULL
            END as grandoffspring_place_rate,
            grand.avg_position as grandoffspring_avg_position,

            NOW() as created_at,
            NOW() as updated_at

        FROM (
            -- Get unique damsires from lineage (use MAX to handle duplicates with different names/regions)
            SELECT
                ancestor_horse_id,
                MAX(ancestor_name) as ancestor_name,
                MAX(ancestor_region) as ancestor_region
            FROM ra_lineage
            WHERE relation_type = 'grandsire_maternal'
            AND ancestor_horse_id IS NOT NULL
            GROUP BY ancestor_horse_id
        ) l

        -- Left join damsire's own racing career
        LEFT JOIN (
            SELECT
                horse_id,
                COUNT(*) as race_runs,
                SUM(CASE WHEN position = '1' THEN 1 ELSE 0 END) as race_wins,
                SUM(CASE WHEN position::int <= 3 THEN 1 ELSE 0 END) as race_places,
                SUM(COALESCE(prize_won, 0)) as total_prize,
                MIN(CASE WHEN position IS NOT NULL THEN position::int ELSE NULL END) as best_position,
                ROUND(AVG(CASE WHEN position IS NOT NULL THEN position::int ELSE NULL END), 2) as avg_position,
                MIN(race_date) as career_start,
                MAX(race_date) as career_end
            FROM ra_mst_runners r
            JOIN ra_races rac ON r.race_id = rac.race_id
            WHERE r.position IS NOT NULL
            GROUP BY horse_id
        ) own ON l.ancestor_horse_id = own.horse_id

        -- Left join grandoffspring performance
        LEFT JOIN (
            SELECT
                lin.ancestor_horse_id,
                COUNT(DISTINCT lin.horse_id) as total_grandoffspring,
                COUNT(*) as total_runs,
                SUM(CASE WHEN r.position = '1' THEN 1 ELSE 0 END) as wins,
                SUM(CASE WHEN r.position::int <= 3 THEN 1 ELSE 0 END) as places,
                SUM(COALESCE(r.prize_won, 0)) as total_prize,
                ROUND(AVG(CASE WHEN r.position IS NOT NULL THEN r.position::int ELSE NULL END), 2) as avg_position
            FROM ra_lineage lin
            JOIN ra_mst_runners r ON lin.runner_id = r.runner_id
            WHERE lin.relation_type = 'grandsire_maternal'
            AND r.position IS NOT NULL
            GROUP BY lin.ancestor_horse_id
        ) grand ON l.ancestor_horse_id = grand.ancestor_horse_id

        ON CONFLICT (damsire_id) DO UPDATE SET
            damsire_name = EXCLUDED.damsire_name,
            damsire_region = EXCLUDED.damsire_region,
            own_race_runs = EXCLUDED.own_race_runs,
            own_race_wins = EXCLUDED.own_race_wins,
            own_race_places = EXCLUDED.own_race_places,
            own_total_prize = EXCLUDED.own_total_prize,
            own_best_position = EXCLUDED.own_best_position,
            own_avg_position = EXCLUDED.own_avg_position,
            own_career_start = EXCLUDED.own_career_start,
            own_career_end = EXCLUDED.own_career_end,
            total_grandoffspring = EXCLUDED.total_grandoffspring,
            grandoffspring_total_runs = EXCLUDED.grandoffspring_total_runs,
            grandoffspring_wins = EXCLUDED.grandoffspring_wins,
            grandoffspring_places = EXCLUDED.grandoffspring_places,
            grandoffspring_total_prize = EXCLUDED.grandoffspring_total_prize,
            grandoffspring_win_rate = EXCLUDED.grandoffspring_win_rate,
            grandoffspring_place_rate = EXCLUDED.grandoffspring_place_rate,
            grandoffspring_avg_position = EXCLUDED.grandoffspring_avg_position,
            updated_at = NOW();
    """)

    damsire_count = cur.rowcount
    conn.commit()
    print(f"✓ Inserted/updated {damsire_count:,} damsire records")
    print()

    # =============================================================================
    # SUMMARY
    # =============================================================================

    print("=" * 100)
    print("BACKFILL COMPLETE - SUMMARY")
    print("=" * 100)
    print()
    print(f"Sires:    {sire_count:,} records")
    print(f"Dams:     {dam_count:,} records")
    print(f"Damsires: {damsire_count:,} records")
    print(f"Total:    {sire_count + dam_count + damsire_count:,} records")
    print()

    # Show sample data
    print("Sample sire statistics (top 5 by progeny wins):")
    print("-" * 100)
    cur.execute("""
        SELECT
            sire_name,
            total_progeny,
            progeny_wins,
            progeny_win_rate,
            own_race_wins
        FROM ra_sire_stats
        WHERE progeny_wins > 0
        ORDER BY progeny_wins DESC
        LIMIT 5;
    """)

    print(f"{'Sire':<30} {'Progeny':<10} {'Wins':<10} {'Win %':<10} {'Own Wins':<10}")
    print("-" * 100)
    for row in cur.fetchall():
        sire_name, progeny_count, wins, win_rate, own_wins = row
        win_rate_str = f"{win_rate}%" if win_rate else "N/A"
        own_wins_str = str(own_wins) if own_wins else "N/A"
        print(f"{sire_name:<30} {progeny_count:<10} {wins:<10} {win_rate_str:<10} {own_wins_str:<10}")
    print()

    print("Sample dam statistics (top 5 by progeny wins):")
    print("-" * 100)
    cur.execute("""
        SELECT
            dam_name,
            total_progeny,
            progeny_wins,
            progeny_win_rate,
            own_race_wins
        FROM ra_dam_stats
        WHERE progeny_wins > 0
        ORDER BY progeny_wins DESC
        LIMIT 5;
    """)

    print(f"{'Dam':<30} {'Progeny':<10} {'Wins':<10} {'Win %':<10} {'Own Wins':<10}")
    print("-" * 100)
    for row in cur.fetchall():
        dam_name, progeny_count, wins, win_rate, own_wins = row
        win_rate_str = f"{win_rate}%" if win_rate else "N/A"
        own_wins_str = str(own_wins) if own_wins else "N/A"
        print(f"{dam_name:<30} {progeny_count:<10} {wins:<10} {win_rate_str:<10} {own_wins_str:<10}")
    print()

    cur.close()
    conn.close()

    print("=" * 100)
    print(f"✓ BACKFILL COMPLETED SUCCESSFULLY")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 100)
    print()

except Exception as e:
    print(f"✗ Error during backfill: {e}")
    import traceback
    traceback.print_exc()
    if conn:
        conn.rollback()
        conn.close()
    sys.exit(1)
