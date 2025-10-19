"""
Direct Batch Backfill Script
Uses Supabase client with intelligent batching to avoid timeouts
Runs automatically until completion
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

logger = get_logger('backfill_direct_batch')

# Field mappings with validation rules
FIELD_MAPPINGS = [
    {
        'db_field': 'weight',
        'api_field': 'weight_lbs',
        'data_type': 'integer',
        'validate': lambda v: v and str(v).isdigit()
    },
    {
        'db_field': 'weight_lbs',
        'api_field': 'weight_lbs',
        'data_type': 'integer',
        'validate': lambda v: v and str(v).isdigit()
    },
    {
        'db_field': 'finishing_time',
        'api_field': 'time',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
    {
        'db_field': 'starting_price_decimal',
        'api_field': 'sp_dec',
        'data_type': 'decimal',
        'validate': lambda v: v and str(v) != '-' and str(v).replace('.', '').isdigit()
    },
    {
        'db_field': 'overall_beaten_distance',
        'api_field': 'ovr_btn',
        'data_type': 'decimal',
        'validate': lambda v: v and str(v) != '-' and str(v).replace('.', '').isdigit()
    },
    {
        'db_field': 'jockey_claim_lbs',
        'api_field': 'jockey_claim_lbs',
        'data_type': 'integer',
        'validate': lambda v: v and str(v).isdigit()
    },
    {
        'db_field': 'weight_stones_lbs',
        'api_field': 'weight',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
    {
        'db_field': 'race_comment',
        'api_field': 'comment',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
    {
        'db_field': 'comment',
        'api_field': 'comment',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
    {
        'db_field': 'jockey_silk_url',
        'api_field': 'silk_url',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
    {
        'db_field': 'silk_url',
        'api_field': 'silk_url',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
]


def fetch_records_to_update(supabase, db_field: str, batch_size: int) -> list:
    """
    Fetch records that need updating for a specific field

    Returns:
        List of records with runner_id and api_data
    """
    try:
        result = supabase.table('ra_runners') \
            .select('runner_id, api_data') \
            .is_(db_field, 'null') \
            .not_.is_('api_data', 'null') \
            .limit(batch_size) \
            .execute()

        return result.data if result.data else []

    except Exception as e:
        logger.error(f"Error fetching records for {db_field}: {e}")
        return []


def update_records_batch(supabase, field_config: dict, records: list) -> tuple:
    """
    Update a batch of records for a specific field

    Returns:
        (success_count, skip_count, error_count)
    """
    db_field = field_config['db_field']
    api_field = field_config['api_field']
    validate_func = field_config['validate']
    data_type = field_config['data_type']

    success_count = 0
    skip_count = 0
    error_count = 0

    # Process records one by one (slow but reliable)
    for record in records:
        try:
            runner_id = record['runner_id']
            api_data = record['api_data']

            if not api_data or api_field not in api_data:
                skip_count += 1
                continue

            value = api_data[api_field]

            # Validate value
            if not validate_func(value):
                skip_count += 1
                continue

            # Convert data type
            if data_type == 'integer':
                value = int(value)
            elif data_type == 'decimal':
                value = float(value)
            # text stays as string

            # Update record
            update_data = {
                db_field: value,
                'updated_at': datetime.utcnow().isoformat()
            }

            supabase.table('ra_runners') \
                .update(update_data) \
                .eq('runner_id', runner_id) \
                .execute()

            success_count += 1

        except Exception as e:
            logger.error(f"Error updating runner_id {record.get('runner_id')}: {e}")
            error_count += 1

    return success_count, skip_count, error_count


def backfill_field(supabase, field_config: dict, batch_size: int = 100, max_batches: int = None) -> dict:
    """
    Backfill a single field completely

    Returns:
        Stats dict
    """
    db_field = field_config['db_field']

    logger.info(f"\n{'='*60}")
    logger.info(f"Processing field: {db_field}")
    logger.info(f"{'='*60}")

    total_success = 0
    total_skip = 0
    total_error = 0
    batch_num = 0

    while True:
        batch_num += 1

        # Check if we hit max batches
        if max_batches and batch_num > max_batches:
            logger.info(f"  Reached max batches ({max_batches})")
            break

        # Fetch records to update
        logger.info(f"  Batch {batch_num}: Fetching {batch_size} records...")
        records = fetch_records_to_update(supabase, db_field, batch_size)

        if not records:
            logger.info(f"  ✅ No more records to update")
            break

        logger.info(f"  Processing {len(records)} records...")

        # Update records
        success, skip, error = update_records_batch(supabase, field_config, records)

        total_success += success
        total_skip += skip
        total_error += error

        logger.info(f"  Batch {batch_num}: {success} updated, {skip} skipped, {error} errors")

        # If we got fewer records than batch size, we're done
        if len(records) < batch_size:
            logger.info(f"  ✅ Completed (last batch)")
            break

        # Brief pause to avoid rate limiting
        time.sleep(0.2)

    stats = {
        'field': db_field,
        'batches': batch_num,
        'updated': total_success,
        'skipped': total_skip,
        'errors': total_error
    }

    logger.info(f"\n✅ {db_field} complete:")
    logger.info(f"   Updated: {total_success:,}")
    logger.info(f"   Skipped: {total_skip:,}")
    logger.info(f"   Errors: {total_error}")

    return stats


def backfill_all_fields(batch_size: int = 100, max_batches_per_field: int = None):
    """
    Backfill all fields automatically

    Args:
        batch_size: Records per batch (smaller = more reliable, slower)
        max_batches_per_field: Limit batches per field (None = unlimited)
    """
    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL - Direct Batch Processing")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max batches per field: {max_batches_per_field or 'unlimited'}")

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"✅ Connected to: {config.supabase.url}\n")

    all_stats = []
    start_time = time.time()

    # Process unique fields only (skip duplicates)
    processed_fields = set()

    for field_config in FIELD_MAPPINGS:
        db_field = field_config['db_field']

        if db_field in processed_fields:
            logger.info(f"Skipping duplicate field: {db_field}")
            continue

        processed_fields.add(db_field)

        try:
            stats = backfill_field(supabase, field_config, batch_size, max_batches_per_field)
            all_stats.append(stats)
        except Exception as e:
            logger.error(f"Failed to process {db_field}: {e}", exc_info=True)

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
        logger.info(f"  {stats['field']:30s}: {stats['updated']:,} updated, {stats['errors']} errors")
        total_updated += stats['updated']
        total_errors += stats['errors']

    logger.info(f"\nOverall:")
    logger.info(f"  Total updated: {total_updated:,}")
    logger.info(f"  Total errors: {total_errors}")

    return all_stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Automated backfill with direct batch processing'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Records per batch (default: 100, smaller = more reliable)'
    )
    parser.add_argument(
        '--max-batches',
        type=int,
        default=None,
        help='Max batches per field (default: unlimited)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: limit to 5 batches per field'
    )

    args = parser.parse_args()

    if args.test:
        logger.info("🧪 TEST MODE: Limited to 5 batches per field")
        max_batches = 5
    else:
        max_batches = args.max_batches

    logger.info("=" * 80)
    logger.info("AUTOMATED BACKFILL FOR ra_runners")
    logger.info("=" * 80)
    logger.info("This script will process all fields until complete")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Processing method: Individual record updates (slow but reliable)")
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    logger.info("=" * 80 + "\n")

    time.sleep(3)

    try:
        stats = backfill_all_fields(
            batch_size=args.batch_size,
            max_batches_per_field=max_batches
        )

        logger.info("\n✅ Backfill complete!")

        if any(s['errors'] > 0 for s in stats):
            logger.warning("\n⚠️  Some errors encountered - check logs")
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
