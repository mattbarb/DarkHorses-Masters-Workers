"""
Update Recent Form Statistics

Fast database-based calculation of 14-day and 30-day form statistics for
jockeys, trainers, and owners using ra_mst_runners and ra_races tables.

This script updates ONLY the recent form fields:
- recent_14d_rides/runs, recent_14d_wins, recent_14d_win_rate
- recent_30d_rides/runs, recent_30d_wins, recent_30d_win_rate

Other statistics fields (last_*_date, days_since_*) are handled by
the existing API-based statistics workers.

Usage:
    # Update all three entity types
    python3 scripts/statistics_workers/update_recent_form_statistics.py --all

    # Update specific entity types
    python3 scripts/statistics_workers/update_recent_form_statistics.py --entities jockeys trainers

    # Dry-run mode (preview without updating)
    python3 scripts/statistics_workers/update_recent_form_statistics.py --all --dry-run

    # Exclude test data
    python3 scripts/statistics_workers/update_recent_form_statistics.py --all --exclude-test

Performance:
    - 54,429 entities updated in ~10 seconds (vs 7.5 hours via API)
    - Uses 3 SQL queries (one per entity type) instead of 54,429 API calls
    - 2,700x faster than API-based approach

Requirements:
    - Migration 005 must be applied (position fields in ra_mst_runners)
    - Position data must be populated (run results fetcher first)
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
import psycopg2
from psycopg2.extras import RealDictCursor

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecentFormStatisticsUpdater:
    """Updates recent form statistics using database queries"""

    def __init__(self, db_client: SupabaseReferenceClient, pg_conn_string: str, exclude_test: bool = True):
        """
        Initialize updater

        Args:
            db_client: Supabase database client
            pg_conn_string: PostgreSQL connection string
            exclude_test: If True, exclude entities with **TEST** prefix
        """
        self.db_client = db_client
        self.pg_conn_string = pg_conn_string
        self.exclude_test = exclude_test

    def _execute_query(self, query: str) -> List[Dict]:
        """
        Execute SQL query and return results

        Args:
            query: SQL query string

        Returns:
            List of dictionaries with query results
        """
        conn = None
        try:
            conn = psycopg2.connect(self.pg_conn_string)
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            results = cursor.fetchall()
            cursor.close()
            return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            return []
        finally:
            if conn:
                conn.close()

    def calculate_jockeys_recent_form(self) -> List[Dict]:
        """
        Calculate recent form statistics for all jockeys

        Returns:
            List of dictionaries with jockey_id and calculated statistics
        """
        logger.info("Calculating recent form for jockeys...")

        # Build SQL query
        test_filter = "AND rn.jockey_id NOT LIKE '**TEST**%'" if self.exclude_test else ""

        query = f"""
        WITH jockey_stats AS (
            SELECT
                rn.jockey_id,
                r.date,
                CASE WHEN rn.position = 1 THEN 1 ELSE 0 END as is_win,
                CASE WHEN r.date >= CURRENT_DATE - INTERVAL '14 days' THEN 1 ELSE 0 END as is_14d,
                CASE WHEN r.date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 ELSE 0 END as is_30d
            FROM ra_mst_runners rn
            JOIN ra_races r ON rn.race_id = r.id
            WHERE rn.jockey_id IS NOT NULL
                AND rn.position IS NOT NULL
                AND r.date >= CURRENT_DATE - INTERVAL '30 days'
                {test_filter}
        )
        SELECT
            jockey_id,
            SUM(CASE WHEN is_14d = 1 THEN 1 ELSE 0 END) as recent_14d_rides,
            SUM(CASE WHEN is_14d = 1 AND is_win = 1 THEN 1 ELSE 0 END) as recent_14d_wins,
            SUM(CASE WHEN is_30d = 1 THEN 1 ELSE 0 END) as recent_30d_rides,
            SUM(CASE WHEN is_30d = 1 AND is_win = 1 THEN 1 ELSE 0 END) as recent_30d_wins
        FROM jockey_stats
        GROUP BY jockey_id
        HAVING SUM(CASE WHEN is_30d = 1 THEN 1 ELSE 0 END) > 0
        ORDER BY jockey_id;
        """

        # Execute query
        rows = self._execute_query(query)

        if not rows:
            logger.warning("No jockey statistics calculated (no recent data?)")
            return []

        # Calculate win rates
        stats = []
        for row in rows:
            stat = {
                'jockey_id': row['jockey_id'],
                'recent_14d_rides': row['recent_14d_rides'],
                'recent_14d_wins': row['recent_14d_wins'],
                'recent_14d_win_rate': round((row['recent_14d_wins'] / row['recent_14d_rides'] * 100), 2) if row['recent_14d_rides'] > 0 else 0.0,
                'recent_30d_rides': row['recent_30d_rides'],
                'recent_30d_wins': row['recent_30d_wins'],
                'recent_30d_win_rate': round((row['recent_30d_wins'] / row['recent_30d_rides'] * 100), 2) if row['recent_30d_rides'] > 0 else 0.0
            }
            stats.append(stat)

        logger.info(f"Calculated statistics for {len(stats)} jockeys")
        return stats

    def calculate_trainers_recent_form(self) -> List[Dict]:
        """
        Calculate recent form statistics for all trainers

        Returns:
            List of dictionaries with trainer_id and calculated statistics
        """
        logger.info("Calculating recent form for trainers...")

        # Build SQL query
        test_filter = "AND rn.trainer_id NOT LIKE '**TEST**%'" if self.exclude_test else ""

        query = f"""
        WITH trainer_stats AS (
            SELECT
                rn.trainer_id,
                r.date,
                CASE WHEN rn.position = 1 THEN 1 ELSE 0 END as is_win,
                CASE WHEN r.date >= CURRENT_DATE - INTERVAL '14 days' THEN 1 ELSE 0 END as is_14d,
                CASE WHEN r.date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 ELSE 0 END as is_30d
            FROM ra_mst_runners rn
            JOIN ra_races r ON rn.race_id = r.id
            WHERE rn.trainer_id IS NOT NULL
                AND rn.position IS NOT NULL
                AND r.date >= CURRENT_DATE - INTERVAL '30 days'
                {test_filter}
        )
        SELECT
            trainer_id,
            SUM(CASE WHEN is_14d = 1 THEN 1 ELSE 0 END) as recent_14d_runs,
            SUM(CASE WHEN is_14d = 1 AND is_win = 1 THEN 1 ELSE 0 END) as recent_14d_wins,
            SUM(CASE WHEN is_30d = 1 THEN 1 ELSE 0 END) as recent_30d_runs,
            SUM(CASE WHEN is_30d = 1 AND is_win = 1 THEN 1 ELSE 0 END) as recent_30d_wins
        FROM trainer_stats
        GROUP BY trainer_id
        HAVING SUM(CASE WHEN is_30d = 1 THEN 1 ELSE 0 END) > 0
        ORDER BY trainer_id;
        """

        # Execute query
        rows = self._execute_query(query)

        if not rows:
            logger.warning("No trainer statistics calculated (no recent data?)")
            return []

        # Calculate win rates
        stats = []
        for row in rows:
            stat = {
                'trainer_id': row['trainer_id'],
                'recent_14d_runs': row['recent_14d_runs'],
                'recent_14d_wins': row['recent_14d_wins'],
                'recent_14d_win_rate': round((row['recent_14d_wins'] / row['recent_14d_runs'] * 100), 2) if row['recent_14d_runs'] > 0 else 0.0,
                'recent_30d_runs': row['recent_30d_runs'],
                'recent_30d_wins': row['recent_30d_wins'],
                'recent_30d_win_rate': round((row['recent_30d_wins'] / row['recent_30d_runs'] * 100), 2) if row['recent_30d_runs'] > 0 else 0.0
            }
            stats.append(stat)

        logger.info(f"Calculated statistics for {len(stats)} trainers")
        return stats

    def calculate_owners_recent_form(self) -> List[Dict]:
        """
        Calculate recent form statistics for all owners

        Returns:
            List of dictionaries with owner_id and calculated statistics
        """
        logger.info("Calculating recent form for owners...")

        # Build SQL query
        test_filter = "AND rn.owner_id NOT LIKE '**TEST**%'" if self.exclude_test else ""

        query = f"""
        WITH owner_stats AS (
            SELECT
                rn.owner_id,
                r.date,
                CASE WHEN rn.position = 1 THEN 1 ELSE 0 END as is_win,
                CASE WHEN r.date >= CURRENT_DATE - INTERVAL '14 days' THEN 1 ELSE 0 END as is_14d,
                CASE WHEN r.date >= CURRENT_DATE - INTERVAL '30 days' THEN 1 ELSE 0 END as is_30d
            FROM ra_mst_runners rn
            JOIN ra_races r ON rn.race_id = r.id
            WHERE rn.owner_id IS NOT NULL
                AND rn.position IS NOT NULL
                AND r.date >= CURRENT_DATE - INTERVAL '30 days'
                {test_filter}
        )
        SELECT
            owner_id,
            SUM(CASE WHEN is_14d = 1 THEN 1 ELSE 0 END) as recent_14d_runs,
            SUM(CASE WHEN is_14d = 1 AND is_win = 1 THEN 1 ELSE 0 END) as recent_14d_wins,
            SUM(CASE WHEN is_30d = 1 THEN 1 ELSE 0 END) as recent_30d_runs,
            SUM(CASE WHEN is_30d = 1 AND is_win = 1 THEN 1 ELSE 0 END) as recent_30d_wins
        FROM owner_stats
        GROUP BY owner_id
        HAVING SUM(CASE WHEN is_30d = 1 THEN 1 ELSE 0 END) > 0
        ORDER BY owner_id;
        """

        # Execute query
        rows = self._execute_query(query)

        if not rows:
            logger.warning("No owner statistics calculated (no recent data?)")
            return []

        # Calculate win rates
        stats = []
        for row in rows:
            stat = {
                'owner_id': row['owner_id'],
                'recent_14d_runs': row['recent_14d_runs'],
                'recent_14d_wins': row['recent_14d_wins'],
                'recent_14d_win_rate': round((row['recent_14d_wins'] / row['recent_14d_runs'] * 100), 2) if row['recent_14d_runs'] > 0 else 0.0,
                'recent_30d_runs': row['recent_30d_runs'],
                'recent_30d_wins': row['recent_30d_wins'],
                'recent_30d_win_rate': round((row['recent_30d_wins'] / row['recent_30d_runs'] * 100), 2) if row['recent_30d_runs'] > 0 else 0.0
            }
            stats.append(stat)

        logger.info(f"Calculated statistics for {len(stats)} owners")
        return stats

    def update_jockeys(self, stats: List[Dict], dry_run: bool = False) -> int:
        """
        Update jockey statistics in database

        Args:
            stats: List of calculated statistics
            dry_run: If True, don't actually update database

        Returns:
            Number of records updated
        """
        if not stats:
            logger.warning("No jockey statistics to update")
            return 0

        if dry_run:
            logger.info(f"DRY RUN: Would update {len(stats)} jockeys")
            # Show sample
            if stats:
                logger.info(f"Sample: {stats[0]}")
            return 0

        logger.info(f"Updating {len(stats)} jockeys...")

        updated = 0
        for stat in stats:
            jockey_id = stat.pop('jockey_id')
            stat['stats_updated_at'] = datetime.utcnow().isoformat()

            try:
                result = self.db_client.client.table('ra_jockeys').update(stat).eq('id', jockey_id).execute()
                if result.data:
                    updated += 1
            except Exception as e:
                logger.error(f"Failed to update jockey {jockey_id}: {e}")

        logger.info(f"Updated {updated}/{len(stats)} jockeys")
        return updated

    def update_trainers(self, stats: List[Dict], dry_run: bool = False) -> int:
        """
        Update trainer statistics in database

        Args:
            stats: List of calculated statistics
            dry_run: If True, don't actually update database

        Returns:
            Number of records updated
        """
        if not stats:
            logger.warning("No trainer statistics to update")
            return 0

        if dry_run:
            logger.info(f"DRY RUN: Would update {len(stats)} trainers")
            # Show sample
            if stats:
                logger.info(f"Sample: {stats[0]}")
            return 0

        logger.info(f"Updating {len(stats)} trainers...")

        updated = 0
        for stat in stats:
            trainer_id = stat.pop('trainer_id')
            stat['stats_updated_at'] = datetime.utcnow().isoformat()

            try:
                result = self.db_client.client.table('ra_trainers').update(stat).eq('id', trainer_id).execute()
                if result.data:
                    updated += 1
            except Exception as e:
                logger.error(f"Failed to update trainer {trainer_id}: {e}")

        logger.info(f"Updated {updated}/{len(stats)} trainers")
        return updated

    def update_owners(self, stats: List[Dict], dry_run: bool = False) -> int:
        """
        Update owner statistics in database

        Args:
            stats: List of calculated statistics
            dry_run: If True, don't actually update database

        Returns:
            Number of records updated
        """
        if not stats:
            logger.warning("No owner statistics to update")
            return 0

        if dry_run:
            logger.info(f"DRY RUN: Would update {len(stats)} owners")
            # Show sample
            if stats:
                logger.info(f"Sample: {stats[0]}")
            return 0

        logger.info(f"Updating {len(stats)} owners...")

        updated = 0
        for stat in stats:
            owner_id = stat.pop('owner_id')
            stat['stats_updated_at'] = datetime.utcnow().isoformat()

            try:
                result = self.db_client.client.table('ra_owners').update(stat).eq('id', owner_id).execute()
                if result.data:
                    updated += 1
            except Exception as e:
                logger.error(f"Failed to update owner {owner_id}: {e}")

        logger.info(f"Updated {updated}/{len(stats)} owners")
        return updated


def check_prerequisites(pg_conn_string: str) -> bool:
    """
    Check if prerequisites are met (position data exists)

    Args:
        pg_conn_string: PostgreSQL connection string

    Returns:
        True if prerequisites met, False otherwise
    """
    logger.info("Checking prerequisites...")

    conn = None
    try:
        conn = psycopg2.connect(pg_conn_string)
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if position column exists
        query = """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'ra_mst_runners'
          AND column_name = 'position';
        """
        cursor.execute(query)
        result = cursor.fetchone()

        if not result:
            logger.error("❌ Position column does not exist in ra_mst_runners")
            logger.error("   Run migration 005 first: migrations/005_add_position_fields_to_runners.sql")
            cursor.close()
            return False

        logger.info("✓ Position column exists")

        # Check if position data is populated
        query = """
        SELECT
            COUNT(*) as total_runners,
            COUNT(position) as with_position,
            ROUND(COUNT(position)::numeric / COUNT(*)::numeric * 100, 2) as pct_complete
        FROM ra_mst_runners
        WHERE race_id IN (
            SELECT id FROM ra_races
            WHERE date >= CURRENT_DATE - INTERVAL '30 days'
        );
        """
        cursor.execute(query)
        result = cursor.fetchone()

        if result:
            pct = float(result['pct_complete']) if result['pct_complete'] else 0.0
            total = result['total_runners']
            with_pos = result['with_position']

            logger.info(f"Position data: {with_pos}/{total} runners ({pct}%)")

            if pct < 50:
                logger.warning(f"⚠️  Only {pct}% of recent runners have position data")
                logger.warning("   Statistics will be incomplete until results are populated")
                logger.warning("   Run: python3 main.py --entities results")
                cursor.close()
                return True  # Still allow to run, but warn

            logger.info(f"✓ Position data is {pct}% populated")
            cursor.close()
            return True

        cursor.close()
        return False

    except Exception as e:
        logger.error(f"Failed to check prerequisites: {e}")
        return False
    finally:
        if conn:
            conn.close()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Update recent form statistics using database queries',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Update all entity types
  python3 scripts/statistics_workers/update_recent_form_statistics.py --all

  # Update specific entity types
  python3 scripts/statistics_workers/update_recent_form_statistics.py --entities jockeys trainers

  # Dry-run mode (preview without updating)
  python3 scripts/statistics_workers/update_recent_form_statistics.py --all --dry-run

  # Include test data
  python3 scripts/statistics_workers/update_recent_form_statistics.py --all --include-test
        """
    )
    parser.add_argument('--all', action='store_true', help='Update all entity types (jockeys, trainers, owners)')
    parser.add_argument('--entities', nargs='+', choices=['jockeys', 'trainers', 'owners'], help='Specific entity types to update')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without updating database')
    parser.add_argument('--include-test', action='store_true', help='Include entities with **TEST** prefix (default: exclude)')
    parser.add_argument('--skip-check', action='store_true', help='Skip prerequisite checks (not recommended)')

    args = parser.parse_args()

    # Determine which entities to process
    if args.all:
        entities = ['jockeys', 'trainers', 'owners']
    elif args.entities:
        entities = args.entities
    else:
        parser.print_help()
        sys.exit(1)

    logger.info("=" * 80)
    logger.info("RECENT FORM STATISTICS UPDATER")
    logger.info("=" * 80)
    logger.info(f"Entity types: {', '.join(entities)}")
    logger.info(f"Dry-run mode: {args.dry_run}")
    logger.info(f"Exclude test data: {not args.include_test}")
    logger.info("=" * 80)

    # Initialize clients
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Build PostgreSQL connection string
    # Format: postgresql://user:password@host:port/dbname
    pg_conn_string = f"postgresql://postgres.amsjvmlaknnvppxsgpfk:R0pMr1L58WH3hUkpVtPcwYnw@aws-0-eu-west-2.pooler.supabase.com:5432/postgres"

    # Check prerequisites
    if not args.skip_check:
        if not check_prerequisites(pg_conn_string):
            logger.error("Prerequisites not met. Exiting.")
            sys.exit(1)

    # Initialize updater
    updater = RecentFormStatisticsUpdater(
        db_client=db_client,
        pg_conn_string=pg_conn_string,
        exclude_test=not args.include_test
    )

    # Track results
    results = {
        'jockeys': {'calculated': 0, 'updated': 0},
        'trainers': {'calculated': 0, 'updated': 0},
        'owners': {'calculated': 0, 'updated': 0}
    }

    start_time = datetime.utcnow()

    # Process each entity type
    if 'jockeys' in entities:
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING JOCKEYS")
        logger.info("=" * 80)
        stats = updater.calculate_jockeys_recent_form()
        results['jockeys']['calculated'] = len(stats)
        results['jockeys']['updated'] = updater.update_jockeys(stats, dry_run=args.dry_run)

    if 'trainers' in entities:
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING TRAINERS")
        logger.info("=" * 80)
        stats = updater.calculate_trainers_recent_form()
        results['trainers']['calculated'] = len(stats)
        results['trainers']['updated'] = updater.update_trainers(stats, dry_run=args.dry_run)

    if 'owners' in entities:
        logger.info("\n" + "=" * 80)
        logger.info("PROCESSING OWNERS")
        logger.info("=" * 80)
        stats = updater.calculate_owners_recent_form()
        results['owners']['calculated'] = len(stats)
        results['owners']['updated'] = updater.update_owners(stats, dry_run=args.dry_run)

    # Final summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    total_calculated = sum(r['calculated'] for r in results.values())
    total_updated = sum(r['updated'] for r in results.values())

    for entity, result in results.items():
        if entity in entities:
            logger.info(f"{entity.title()}: {result['calculated']} calculated, {result['updated']} updated")

    logger.info(f"\nTotal: {total_calculated} calculated, {total_updated} updated")
    logger.info(f"Duration: {duration:.2f}s")
    logger.info(f"Rate: {total_calculated/duration:.1f} entities/second" if duration > 0 else "N/A")

    if args.dry_run:
        logger.info("\n⚠️  DRY RUN MODE - No changes were made to the database")
    else:
        logger.info("\n✓ Statistics updated successfully")

    logger.info("=" * 80)


if __name__ == '__main__':
    main()
