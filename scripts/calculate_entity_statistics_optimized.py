#!/usr/bin/env python3
"""
Calculate Entity Statistics (Optimized - Direct SQL)
===================================================

Uses direct SQL updates instead of views to avoid timeout issues.
This approach is faster because it executes in a single transaction on the database.

Usage:
    python3 scripts/calculate_entity_statistics_optimized.py
"""

import sys
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
import psycopg2
from urllib.parse import urlparse
from utils.logger import get_logger

logger = get_logger('calculate_entity_statistics_optimized')


def get_db_connection():
    """Get direct PostgreSQL connection from Supabase URL"""
    config = get_config()

    # Parse Supabase URL to get connection params
    # Format: https://PROJECT.supabase.co
    url = config.supabase.url.replace('https://', '')
    project = url.split('.')[0]

    # Supabase connection string
    conn_str = f"postgresql://postgres.{project}:{config.supabase.service_key}@aws-0-us-west-1.pooler.supabase.com:6543/postgres"

    return psycopg2.connect(conn_str)


def calculate_statistics():
    """Calculate statistics using direct SQL"""
    logger.info("=" * 80)
    logger.info("CALCULATING ENTITY STATISTICS (OPTIMIZED SQL)")
    logger.info("=" * 80)

    start_time = datetime.now()

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Update jockeys
        logger.info("Updating jockey statistics...")
        cursor.execute("""
            UPDATE ra_jockeys j
            SET
                total_rides = COALESCE(stats.rides, 0),
                total_wins = COALESCE(stats.wins, 0),
                total_places = COALESCE(stats.places, 0),
                total_seconds = COALESCE(stats.seconds, 0),
                total_thirds = COALESCE(stats.thirds, 0),
                win_rate = COALESCE(stats.win_rate, 0),
                place_rate = COALESCE(stats.place_rate, 0),
                stats_updated_at = NOW()
            FROM (
                SELECT
                    r.jockey_id,
                    COUNT(r.runner_id) as rides,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as places,
                    COUNT(CASE WHEN r.position = 2 THEN 1 END) as seconds,
                    COUNT(CASE WHEN r.position = 3 THEN 1 END) as thirds,
                    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as win_rate,
                    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as place_rate
                FROM ra_runners r
                WHERE r.position IS NOT NULL
                GROUP BY r.jockey_id
            ) stats
            WHERE j.jockey_id = stats.jockey_id;
        """)
        jockeys_updated = cursor.rowcount
        logger.info(f"✓ Updated {jockeys_updated:,} jockeys")

        # Update trainers
        logger.info("Updating trainer statistics...")
        cursor.execute("""
            UPDATE ra_trainers t
            SET
                total_runners = COALESCE(stats.runners, 0),
                total_wins = COALESCE(stats.wins, 0),
                total_places = COALESCE(stats.places, 0),
                total_seconds = COALESCE(stats.seconds, 0),
                total_thirds = COALESCE(stats.thirds, 0),
                win_rate = COALESCE(stats.win_rate, 0),
                place_rate = COALESCE(stats.place_rate, 0),
                recent_14d_runs = COALESCE(stats.recent_runs, 0),
                recent_14d_wins = COALESCE(stats.recent_wins, 0),
                recent_14d_win_rate = COALESCE(stats.recent_win_rate, 0),
                stats_updated_at = NOW()
            FROM (
                SELECT
                    r.trainer_id,
                    COUNT(r.runner_id) as runners,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as places,
                    COUNT(CASE WHEN r.position = 2 THEN 1 END) as seconds,
                    COUNT(CASE WHEN r.position = 3 THEN 1 END) as thirds,
                    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as win_rate,
                    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as place_rate,
                    COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' THEN r.runner_id END) as recent_runs,
                    COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1 THEN 1 END) as recent_wins,
                    ROUND(100.0 * COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1 THEN 1 END) /
                          NULLIF(COUNT(CASE WHEN rc.race_date >= CURRENT_DATE - INTERVAL '14 days' THEN r.runner_id END), 0), 2) as recent_win_rate
                FROM ra_runners r
                LEFT JOIN ra_races rc ON rc.race_id = r.race_id
                WHERE r.position IS NOT NULL
                GROUP BY r.trainer_id
            ) stats
            WHERE t.trainer_id = stats.trainer_id;
        """)
        trainers_updated = cursor.rowcount
        logger.info(f"✓ Updated {trainers_updated:,} trainers")

        # Update owners
        logger.info("Updating owner statistics...")
        cursor.execute("""
            UPDATE ra_owners o
            SET
                total_horses = COALESCE(stats.horses, 0),
                total_runners = COALESCE(stats.runners, 0),
                total_wins = COALESCE(stats.wins, 0),
                total_places = COALESCE(stats.places, 0),
                total_seconds = COALESCE(stats.seconds, 0),
                total_thirds = COALESCE(stats.thirds, 0),
                win_rate = COALESCE(stats.win_rate, 0),
                place_rate = COALESCE(stats.place_rate, 0),
                active_last_30d = COALESCE(stats.active, FALSE),
                stats_updated_at = NOW()
            FROM (
                SELECT
                    r.owner_id,
                    COUNT(DISTINCT r.horse_id) as horses,
                    COUNT(r.runner_id) as runners,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as places,
                    COUNT(CASE WHEN r.position = 2 THEN 1 END) as seconds,
                    COUNT(CASE WHEN r.position = 3 THEN 1 END) as thirds,
                    ROUND(100.0 * COUNT(CASE WHEN r.position = 1 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as win_rate,
                    ROUND(100.0 * COUNT(CASE WHEN r.position <= 3 THEN 1 END) / NULLIF(COUNT(r.runner_id), 0), 2) as place_rate,
                    MAX(rc.race_date >= CURRENT_DATE - INTERVAL '30 days') as active
                FROM ra_runners r
                LEFT JOIN ra_races rc ON rc.race_id = r.race_id
                WHERE r.position IS NOT NULL
                GROUP BY r.owner_id
            ) stats
            WHERE o.owner_id = stats.owner_id;
        """)
        owners_updated = cursor.rowcount
        logger.info(f"✓ Updated {owners_updated:,} owners")

        # Commit changes
        conn.commit()

        duration = (datetime.now() - start_time).total_seconds()

        logger.info("-" * 80)
        logger.info("✓ Statistics calculation complete")
        logger.info("-" * 80)
        logger.info(f"Jockeys updated:  {jockeys_updated:,}")
        logger.info(f"Trainers updated: {trainers_updated:,}")
        logger.info(f"Owners updated:   {owners_updated:,}")
        logger.info(f"Duration:         {duration:.2f} seconds")
        logger.info("-" * 80)

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        logger.error(f"✗ Statistics calculation failed: {e}", exc_info=True)
        return False


def main():
    success = calculate_statistics()
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
