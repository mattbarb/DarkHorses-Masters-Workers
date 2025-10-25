"""
Simple Automated Backfill Script
Uses psycopg2 for direct database connection
Automatically loops until all fields are populated
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from config.config import get_config

logger = get_logger('backfill_simple')

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import pool
except ImportError:
    logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Field mappings: (db_column, api_field, cast_type)
FIELD_MAPPINGS = [
    ('weight', 'weight_lbs', 'INTEGER'),
    ('weight_lbs', 'weight_lbs', 'INTEGER'),
    ('finishing_time', 'time', 'TEXT'),
    ('starting_price_decimal', 'sp_dec', 'DECIMAL'),
    ('overall_beaten_distance', 'ovr_btn', 'DECIMAL'),
    ('jockey_claim_lbs', 'jockey_claim_lbs', 'INTEGER'),
    ('weight_stones_lbs', 'weight', 'TEXT'),
    ('race_comment', 'comment', 'TEXT'),
    ('comment', 'comment', 'TEXT'),
    ('jockey_silk_url', 'silk_url', 'TEXT'),
    ('silk_url', 'silk_url', 'TEXT'),
]


def get_db_connection():
    """
    Get database connection using config

    Returns:
        psycopg2 connection or None
    """
    config = get_config()

    # Extract project ref from Supabase URL
    import re
    match = re.search(r'https://([a-z0-9]+)\.supabase\.co', config.supabase.url)
    if not match:
        logger.error("Cannot extract project ref from Supabase URL")
        return None

    project_ref = match.group(1)

    # Try direct connection first
    connection_params = {
        'host': f'db.{project_ref}.supabase.co',
        'port': 5432,
        'database': 'postgres',
        'user': 'postgres',
        'password': 'M8_yvHW9%p]d3Sg',  # Your database password
        'connect_timeout': 10
    }

    try:
        conn = psycopg2.connect(**connection_params)
        logger.info(f"✅ Connected to database: {connection_params['host']}")
        return conn
    except psycopg2.Error as e:
        logger.error(f"❌ Database connection failed: {e}")
        return None


def count_remaining(cursor, db_field: str, api_field: str) -> int:
    """
    Count how many NULL records remain for a field
    """
    sql = f"""
        SELECT COUNT(*)
        FROM ra_runners
        WHERE api_data IS NOT NULL
          AND api_data->>%s IS NOT NULL
          AND {db_field} IS NULL;
    """

    try:
        cursor.execute(sql, (api_field,))
        result = cursor.fetchone()
        return result[0] if result else 0
    except Exception as e:
        logger.error(f"Error counting {db_field}: {e}")
        return 0


def backfill_field_batch(cursor, db_field: str, api_field: str,
                        cast_type: str, batch_size: int) -> tuple:
    """
    Backfill one batch of records for a single field

    Returns:
        (success: bool, rows_updated: int, error_msg: str or None)
    """
    # Build SQL query
    if cast_type == 'TEXT':
        sql = f"""
            UPDATE ra_runners
            SET {db_field} = api_data->>%s, updated_at = NOW()
            WHERE runner_id IN (
                SELECT runner_id FROM ra_runners
                WHERE api_data IS NOT NULL
                  AND api_data->>%s IS NOT NULL
                  AND {db_field} IS NULL
                LIMIT %s
            );
        """
        params = (api_field, api_field, batch_size)
    else:
        sql = f"""
            UPDATE ra_runners
            SET {db_field} = (api_data->>%s)::{cast_type}, updated_at = NOW()
            WHERE runner_id IN (
                SELECT runner_id FROM ra_runners
                WHERE api_data IS NOT NULL
                  AND api_data->>%s IS NOT NULL
                  AND {db_field} IS NULL
                LIMIT %s
            );
        """
        params = (api_field, api_field, batch_size)

    try:
        cursor.execute(sql, params)
        rows_updated = cursor.rowcount
        return True, rows_updated, None
    except Exception as e:
        return False, 0, str(e)


def backfill_automated(batch_size: int = 1000, max_total_runs: int = 200):
    """
    Automatically backfill all fields until complete or max runs reached

    Args:
        batch_size: Records per batch
        max_total_runs: Maximum total batches to run (safety limit)
    """
    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL - Will run until complete")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max total runs: {max_total_runs}")

    # Get database connection
    conn = get_db_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return None

    stats = {
        'total_batches_run': 0,
        'total_updated': 0,
        'fields_completed': [],
        'errors': 0
    }

    try:
        logger.info("\nStarting backfill...\n")

        # Process fields in a loop until all are done or max runs reached
        run_number = 0

        while run_number < max_total_runs:
            run_number += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"RUN #{run_number}")
            logger.info(f"{'='*60}")

            any_work_done = False

            cursor = conn.cursor()

            try:
                # Track which fields to process in this run
                for db_field, api_field, cast_type in FIELD_MAPPINGS:
                    # Skip if already marked complete
                    if db_field in stats['fields_completed']:
                        continue

                    # Check how many records remain
                    remaining = count_remaining(cursor, db_field, api_field)

                    if remaining == 0:
                        logger.info(f"✅ {db_field}: COMPLETE")
                        stats['fields_completed'].append(db_field)
                        continue

                    # Process one batch
                    logger.info(f"  {db_field}: {remaining:,} remaining, processing batch...")

                    success, rows_updated, error = backfill_field_batch(
                        cursor, db_field, api_field, cast_type, batch_size
                    )

                    if success:
                        conn.commit()  # Commit after each field
                        stats['total_batches_run'] += 1
                        stats['total_updated'] += rows_updated
                        any_work_done = True
                        logger.info(f"  ✅ Updated {rows_updated:,} records")
                    else:
                        conn.rollback()
                        logger.error(f"  ❌ Error: {error}")
                        stats['errors'] += 1

                        # If timeout, pause longer
                        if 'timeout' in str(error).lower():
                            logger.warning(f"  ⚠️  Timeout detected, waiting 5 seconds...")
                            time.sleep(5)

                    # Small delay between fields
                    time.sleep(0.2)

            finally:
                cursor.close()

            # Check if all fields are done
            unique_fields = list(set([f[0] for f in FIELD_MAPPINGS]))
            if len(stats['fields_completed']) >= len(unique_fields):
                logger.info("\n" + "=" * 80)
                logger.info("🎉 ALL FIELDS COMPLETE!")
                logger.info("=" * 80)
                break

            # If no work was done this run, we're done
            if not any_work_done:
                logger.info("\nNo more work to do")
                break

            # Brief pause between runs
            time.sleep(0.3)

    finally:
        conn.close()

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total runs: {run_number}")
    logger.info(f"Total batches executed: {stats['total_batches_run']}")
    logger.info(f"Total records updated: {stats['total_updated']:,}")
    logger.info(f"Errors encountered: {stats['errors']}")
    logger.info(f"\nFields completed: {len(stats['fields_completed'])}/{len(set([f[0] for f in FIELD_MAPPINGS]))}")

    return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Automated backfill - runs until complete'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='Batch size per field (default: 1000)'
    )
    parser.add_argument(
        '--max-runs',
        type=int,
        default=200,
        help='Maximum total runs (default: 200)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL FOR ra_runners")
    logger.info("=" * 80)
    logger.info("This script will automatically run batches until all fields are populated")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Max runs: {args.max_runs}")
    logger.info(f"Estimated time: ~{args.max_runs * 2 / 60:.0f}-{args.max_runs * 5 / 60:.0f} minutes")
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    logger.info("=" * 80 + "\n")

    time.sleep(3)

    try:
        stats = backfill_automated(
            batch_size=args.batch_size,
            max_total_runs=args.max_runs
        )

        if stats is None:
            logger.error("\n❌ Backfill failed to start")
            return 1

        logger.info("\n✅ Backfill complete!")

        if stats['errors'] > 0:
            logger.warning(f"\n⚠️  {stats['errors']} errors encountered - some fields may need manual review")
            return 1

        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Interrupted by user")
        logger.info("Progress has been saved. Run again to resume.")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
