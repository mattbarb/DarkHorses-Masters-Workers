"""
Automated Backfill Script: Updates NULL fields in ra_runners from api_data
Uses direct psql connection to bypass Supabase Python client issues
Automatically loops until all fields are populated
"""

import os
import sys
import time
import subprocess
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from config.config import get_config

logger = get_logger('backfill_automated')

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


def run_psql_query(sql: str, database_url: str) -> tuple:
    """
    Execute SQL query via psql command

    Returns:
        (success: bool, output: str)
    """
    try:
        # Run psql with the SQL
        result = subprocess.run(
            ['psql', database_url, '-c', sql],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            return True, result.stdout
        else:
            return False, result.stderr

    except subprocess.TimeoutExpired:
        return False, "Query timeout"
    except Exception as e:
        return False, str(e)


def count_remaining(db_field: str, api_field: str, database_url: str) -> int:
    """
    Count how many NULL records remain for a field
    """
    sql = f"""
        SELECT COUNT(*)
        FROM ra_runners
        WHERE api_data IS NOT NULL
          AND api_data->>'{api_field}' IS NOT NULL
          AND {db_field} IS NULL;
    """

    success, output = run_psql_query(sql, database_url)

    if success:
        try:
            # Parse count from output
            lines = output.strip().split('\n')
            for line in lines:
                if line.strip().isdigit():
                    return int(line.strip())
        except:
            pass

    return 0


def backfill_field_batch(db_field: str, api_field: str, cast_type: str,
                        batch_size: int, database_url: str) -> tuple:
    """
    Backfill one batch of records for a single field

    Returns:
        (success: bool, error_msg: str or None)
    """
    # Build SQL query
    if cast_type == 'TEXT':
        sql = f"""
            UPDATE ra_runners
            SET {db_field} = api_data->>'{api_field}', updated_at = NOW()
            WHERE runner_id IN (
                SELECT runner_id FROM ra_runners
                WHERE api_data IS NOT NULL
                  AND api_data->>'{api_field}' IS NOT NULL
                  AND {db_field} IS NULL
                LIMIT {batch_size}
            );
        """
    else:
        sql = f"""
            UPDATE ra_runners
            SET {db_field} = (api_data->>'{api_field}')::{cast_type}, updated_at = NOW()
            WHERE runner_id IN (
                SELECT runner_id FROM ra_runners
                WHERE api_data IS NOT NULL
                  AND api_data->>'{api_field}' IS NOT NULL
                  AND {db_field} IS NULL
                LIMIT {batch_size}
            );
        """

    success, output = run_psql_query(sql, database_url)

    if not success:
        return False, output

    return True, None


def backfill_automated(batch_size: int = 1000, max_total_runs: int = 200):
    """
    Automatically backfill all fields until complete or max runs reached

    Args:
        batch_size: Records per batch (smaller = less likely to timeout)
        max_total_runs: Maximum total batches to run (safety limit)
    """
    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL - Will run until complete")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max total runs: {max_total_runs}")

    config = get_config()

    # Build database URL for psql
    # Format: postgresql://user:password@host:port/database
    database_url = config.supabase.url.replace('https://', 'postgresql://postgres:')
    # Extract host from URL
    host = config.supabase.url.replace('https://', '').replace('http://', '')
    database_url = f"postgresql://postgres.{host.split('.')[0]}:M8_yvHW9%p]d3Sg@{host}:5432/postgres"

    logger.info(f"\nDatabase: {config.supabase.url}")
    logger.info("Starting backfill...\n")

    stats = {
        'total_batches_run': 0,
        'total_updated': 0,
        'fields_completed': [],
        'errors': 0
    }

    # Process fields in a loop until all are done or max runs reached
    run_number = 0

    while run_number < max_total_runs:
        run_number += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"RUN #{run_number}")
        logger.info(f"{'='*60}")

        any_work_done = False

        # Track which fields to process in this run
        for db_field, api_field, cast_type in FIELD_MAPPINGS:
            # Skip if already marked complete
            if db_field in stats['fields_completed']:
                continue

            # Check how many records remain
            remaining = count_remaining(db_field, api_field, database_url)

            if remaining == 0:
                logger.info(f"✅ {db_field}: COMPLETE (no more NULL records)")
                stats['fields_completed'].append(db_field)
                continue

            # Process one batch
            logger.info(f"  {db_field}: {remaining:,} records remaining, processing batch of {batch_size}...")

            success, error = backfill_field_batch(
                db_field, api_field, cast_type, batch_size, database_url
            )

            if success:
                stats['total_batches_run'] += 1
                stats['total_updated'] += min(batch_size, remaining)
                any_work_done = True
                logger.info(f"  ✅ Batch complete")
            else:
                logger.error(f"  ❌ Error: {error}")
                stats['errors'] += 1

                # If timeout, pause longer
                if 'timeout' in str(error).lower():
                    logger.warning(f"  ⚠️  Timeout detected, waiting 5 seconds...")
                    time.sleep(5)

            # Small delay between fields to avoid overwhelming database
            time.sleep(0.3)

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
        time.sleep(0.5)

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total runs: {run_number}")
    logger.info(f"Total batches executed: {stats['total_batches_run']}")
    logger.info(f"Total records updated (est.): ~{stats['total_updated']:,}")
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
        help='Maximum total runs (default: 200, enough for 1.3M records)'
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
    logger.info("=" * 80)

    time.sleep(3)

    try:
        stats = backfill_automated(
            batch_size=args.batch_size,
            max_total_runs=args.max_runs
        )

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
