"""
Automated Backfill Script using Supabase REST API
Executes raw SQL queries via PostgREST
Automatically loops until all fields are populated
"""

import os
import sys
import time
import requests
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from config.config import get_config

logger = get_logger('backfill_rest_api')

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


def execute_sql(sql: str, config) -> tuple:
    """
    Execute raw SQL via Supabase REST API

    Returns:
        (success: bool, data: any, error: str or None)
    """
    # Supabase has an RPC endpoint for executing SQL
    # We'll use their  REST API with the service key

    url = f"{config.supabase.url}/rest/v1/rpc/exec_sql"
    headers = {
        'apikey': config.supabase.service_key,
        'Authorization': f'Bearer {config.supabase.service_key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
    }

    payload = {
        'query': sql
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)

        if response.status_code == 200:
            return True, response.json() if response.text else None, None
        else:
            error_msg = response.text or f"HTTP {response.status_code}"
            return False, None, error_msg

    except requests.exceptions.Timeout:
        return False, None, "Request timeout (25s)"
    except Exception as e:
        return False, None, str(e)


def count_remaining_supabase_client(db_field: str, api_field: str, supabase_client) -> int:
    """
    Count remaining NULL records using Supabase client (PostgREST query)
    """
    try:
        # Use a different approach - select and count
        result = supabase_client.table('ra_runners') \
            .select('runner_id', count='exact') \
            .is_(db_field, 'null') \
            .limit(1) \
            .execute()

        return result.count if result.count else 0
    except Exception as e:
        logger.error(f"Error counting {db_field}: {e}")
        return -1  # Return -1 to indicate we should try to process anyway


def backfill_field_batch_direct(db_field: str, api_field: str, cast_type: str,
                                batch_size: int, supabase_client) -> tuple:
    """
    Backfill using Supabase client's direct query method

    Returns:
        (success: bool, rows_updated: int, error: str or None)
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
            )
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
            )
        """

    try:
        # Execute via rpc if available
        result = supabase_client.rpc('exec_sql', {'query': sql}).execute()

        # We can't easily get row count, so return batch_size as estimate
        return True, batch_size, None

    except Exception as e:
        error_msg = str(e)

        # Check if it's a timeout
        if 'timeout' in error_msg.lower() or 'timed out' in error_msg.lower():
            return False, 0, "Timeout"

        return False, 0, error_msg


def backfill_automated(batch_size: int = 500, max_total_runs: int = 300):
    """
    Automatically backfill all fields until complete or max runs reached

    Args:
        batch_size: Records per batch (keep small to avoid timeouts)
        max_total_runs: Maximum total batches to run
    """
    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL - Uses Supabase Client")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size} (smaller batches to avoid timeouts)")
    logger.info(f"Max total runs: {max_total_runs}")

    config = get_config()

    # Use Supabase client
    from supabase import create_client
    supabase_client = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"✅ Connected to: {config.supabase.url}")

    stats = {
        'total_batches_run': 0,
        'total_updated': 0,
        'fields_completed': [],
        'errors': 0,
        'timeouts': 0
    }

    logger.info("\nStarting backfill...\n")

    # Process fields in a loop
    run_number = 0

    while run_number < max_total_runs:
        run_number += 1
        logger.info(f"\n{'='*60}")
        logger.info(f"RUN #{run_number}/{max_total_runs}")
        logger.info(f"{'='*60}")

        any_work_done = False

        # Track unique fields (skip duplicates)
        processed_fields = set()

        for db_field, api_field, cast_type in FIELD_MAPPINGS:
            # Skip duplicates
            if db_field in processed_fields:
                continue
            processed_fields.add(db_field)

            # Skip if already marked complete
            if db_field in stats['fields_completed']:
                continue

            # Check how many records remain
            remaining = count_remaining_supabase_client(db_field, api_field, supabase_client)

            if remaining == 0:
                logger.info(f"✅ {db_field}: COMPLETE")
                stats['fields_completed'].append(db_field)
                continue

            # Process one batch
            if remaining > 0:
                logger.info(f"  {db_field}: {remaining:,} remaining, processing batch...")
            else:
                logger.info(f"  {db_field}: processing batch (count unavailable)...")

            success, rows_updated, error = backfill_field_batch_direct(
                db_field, api_field, cast_type, batch_size, supabase_client
            )

            if success:
                stats['total_batches_run'] += 1
                stats['total_updated'] += rows_updated
                any_work_done = True
                logger.info(f"  ✅ Batch complete (~{rows_updated} records)")
            else:
                logger.error(f"  ❌ Error: {error}")
                stats['errors'] += 1

                # Track timeouts
                if error == "Timeout":
                    stats['timeouts'] += 1
                    logger.warning(f"  ⚠️  Timeout #{stats['timeouts']} - will wait 3 seconds")
                    time.sleep(3)

                    # If we're getting too many timeouts, suggest reducing batch size
                    if stats['timeouts'] > 10:
                        logger.error(f"\n⚠️  TOO MANY TIMEOUTS ({stats['timeouts']})")
                        logger.error("Try running with smaller --batch-size (e.g., 250)")
                        return stats

            # Small delay between fields
            time.sleep(0.4)

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
    logger.info(f"Errors: {stats['errors']} (timeouts: {stats['timeouts']})")
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
        default=500,
        help='Batch size per field (default: 500, reduce if timeouts occur)'
    )
    parser.add_argument(
        '--max-runs',
        type=int,
        default=300,
        help='Maximum total runs (default: 300)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL FOR ra_runners")
    logger.info("=" * 80)
    logger.info("This script will automatically run batches until all fields are populated")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Max runs: {args.max_runs}")
    logger.info(f"Estimated time: ~{args.max_runs * 3 / 60:.0f}-{args.max_runs * 6 / 60:.0f} minutes")
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
            logger.warning(f"\n⚠️  {stats['errors']} errors encountered")
            if stats['timeouts'] > 20:
                logger.warning("Many timeouts - try reducing --batch-size to 250 or 100")
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
