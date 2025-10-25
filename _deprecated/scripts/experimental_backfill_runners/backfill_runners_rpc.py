"""
Backfill using Supabase RPC (Remote Procedure Calls)
Calls PostgreSQL functions that run entirely server-side
Bypasses all client-side timeout issues
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from config.config import get_config
from supabase import create_client

logger = get_logger('backfill_rpc')

# RPC function names for each field
RPC_FUNCTIONS = [
    'backfill_weight_field',
    'backfill_finishing_time_field',
    'backfill_starting_price_decimal_field',
    'backfill_overall_beaten_distance_field',
    'backfill_jockey_claim_lbs_field',
    'backfill_weight_stones_lbs_field',
    'backfill_race_comment_field',
    'backfill_jockey_silk_url_field'
]


def call_rpc_function(supabase, function_name: str, batch_limit: int = 5000) -> dict:
    """
    Call a PostgreSQL function via Supabase RPC

    Args:
        supabase: Supabase client
        function_name: Name of the function to call
        batch_limit: Batch size for processing

    Returns:
        Result dict from the function
    """
    logger.info(f"\n{'='*60}")
    logger.info(f"Calling RPC function: {function_name}")
    logger.info(f"{'='*60}")

    try:
        # Call the RPC function
        # The function runs entirely on the server and returns JSON result
        result = supabase.rpc(function_name, {'batch_limit': batch_limit}).execute()

        if result.data:
            stats = result.data
            logger.info(f"  ✅ Complete:")
            logger.info(f"     Field: {stats.get('field')}")
            logger.info(f"     Batches: {stats.get('batches')}")
            logger.info(f"     Updated: {stats.get('updated'):,}")
            return stats
        else:
            logger.error(f"  ❌ No data returned from {function_name}")
            return {'field': function_name, 'batches': 0, 'updated': 0, 'error': 'No data returned'}

    except Exception as e:
        logger.error(f"  ❌ Error calling {function_name}: {e}", exc_info=True)
        return {'field': function_name, 'batches': 0, 'updated': 0, 'error': str(e)}


def backfill_all_via_rpc(batch_limit: int = 5000):
    """
    Call all RPC functions to backfill all fields

    Args:
        batch_limit: Batch size for processing (larger is faster)
    """
    logger.info("=" * 80)
    logger.info("BACKFILL VIA SUPABASE RPC")
    logger.info("=" * 80)
    logger.info(f"Batch limit: {batch_limit}")
    logger.info("Functions run entirely server-side (no client timeouts)")

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"✅ Connected to: {config.supabase.url}\n")

    all_stats = []
    start_time = time.time()

    for function_name in RPC_FUNCTIONS:
        try:
            stats = call_rpc_function(supabase, function_name, batch_limit)
            all_stats.append(stats)

            # Brief pause between functions
            time.sleep(1)

        except Exception as e:
            logger.error(f"Failed to call {function_name}: {e}", exc_info=True)
            all_stats.append({
                'field': function_name,
                'batches': 0,
                'updated': 0,
                'error': str(e)
            })

    # Final summary
    elapsed = time.time() - start_time

    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total time: {elapsed / 60:.1f} minutes")
    logger.info("\nResults by field:")

    total_updated = 0
    total_errors = 0

    for stats in all_stats:
        if 'error' in stats:
            logger.error(f"  ❌ {stats['field']:40s}: ERROR - {stats['error']}")
            total_errors += 1
        else:
            logger.info(f"  ✅ {stats['field']:40s}: {stats['updated']:,} updated")
            total_updated += stats['updated']

    logger.info(f"\nOverall:")
    logger.info(f"  Total updated: {total_updated:,}")
    logger.info(f"  Functions with errors: {total_errors}")

    return all_stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Backfill via Supabase RPC (server-side functions)'
    )
    parser.add_argument(
        '--batch-limit',
        type=int,
        default=5000,
        help='Batch size for each function (default: 5000, larger = faster)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("SUPABASE RPC BACKFILL FOR ra_runners")
    logger.info("=" * 80)
    logger.info("This approach uses server-side PostgreSQL functions")
    logger.info("Each function processes its field completely")
    logger.info(f"Batch limit: {args.batch_limit}")
    logger.info("\nNOTE: You must first run migration 015_backfill_using_functions.sql")
    logger.info("      in Supabase SQL Editor to create the functions")
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    logger.info("=" * 80 + "\n")

    time.sleep(3)

    try:
        stats = backfill_all_via_rpc(batch_limit=args.batch_limit)

        if any('error' in s for s in stats):
            logger.warning("\n⚠️  Some functions encountered errors - check logs")
            return 1

        logger.info("\n✅ Backfill complete!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
