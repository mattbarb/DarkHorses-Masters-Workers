"""
Optimized Backfill Script for ra_runners
Works within Supabase REST API timeout constraints (8 seconds)
Uses small batches with retry logic and checkpoint/resume capability
"""

import os
import sys
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from config.config import get_config
from supabase import create_client

logger = get_logger('backfill_optimized')

# Checkpoint file for resume capability
CHECKPOINT_FILE = 'logs/backfill_optimized_checkpoint.json'

# Field mappings with validation rules
FIELD_MAPPINGS = [
    {
        'db_field': 'weight',
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
        'db_field': 'jockey_silk_url',
        'api_field': 'silk_url',
        'data_type': 'text',
        'validate': lambda v: v and str(v).strip() != ''
    },
]


def load_checkpoint():
    """Load checkpoint from file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'completed_fields': [], 'field_stats': {}}


def save_checkpoint(checkpoint):
    """Save checkpoint to file"""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def fetch_records_with_retry(supabase, db_field: str, batch_size: int, max_retries: int = 3) -> list:
    """
    Fetch records with retry logic for timeouts
    """
    for attempt in range(max_retries):
        try:
            result = supabase.table('ra_runners') \
                .select('runner_id, api_data') \
                .is_(db_field, 'null') \
                .not_.is_('api_data', 'null') \
                .limit(batch_size) \
                .execute()

            return result.data if result.data else []

        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower() or '57014' in error_msg:
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"  Timeout on SELECT, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"  Failed after {max_retries} attempts")
                    return []
            else:
                logger.error(f"  Error fetching records: {e}")
                return []

    return []


def update_record_with_retry(supabase, runner_id: str, update_data: dict, max_retries: int = 3) -> bool:
    """
    Update a single record with retry logic
    """
    for attempt in range(max_retries):
        try:
            supabase.table('ra_runners') \
                .update(update_data) \
                .eq('runner_id', runner_id) \
                .execute()
            return True

        except Exception as e:
            error_msg = str(e)
            if 'timeout' in error_msg.lower() or '57014' in error_msg:
                if attempt < max_retries - 1:
                    time.sleep(1)
                else:
                    return False
            else:
                logger.error(f"  Error updating {runner_id}: {e}")
                return False

    return False


def backfill_field(supabase, field_config: dict, batch_size: int = 25) -> dict:
    """
    Backfill a single field with small batches and retry logic

    Args:
        supabase: Supabase client
        field_config: Field configuration dict
        batch_size: Records per batch (small to avoid timeouts)

    Returns:
        Stats dict
    """
    db_field = field_config['db_field']
    api_field = field_config['api_field']
    validate_func = field_config['validate']
    data_type = field_config['data_type']

    logger.info(f"\n{'='*60}")
    logger.info(f"Processing field: {db_field}")
    logger.info(f"{'='*60}")

    total_success = 0
    total_skip = 0
    total_error = 0
    batch_num = 0
    consecutive_empty_batches = 0

    while consecutive_empty_batches < 3:  # Stop after 3 empty batches
        batch_num += 1

        # Fetch records to update
        logger.info(f"  Batch {batch_num}: Fetching {batch_size} records...")
        records = fetch_records_with_retry(supabase, db_field, batch_size)

        if not records:
            consecutive_empty_batches += 1
            if consecutive_empty_batches >= 3:
                logger.info(f"  ✅ No more records to update (3 consecutive empty batches)")
                break
            else:
                logger.warning(f"  Empty batch, will retry ({consecutive_empty_batches}/3)...")
                time.sleep(2)
                continue
        else:
            consecutive_empty_batches = 0  # Reset counter

        logger.info(f"  Processing {len(records)} records...")

        # Update records one by one
        success_in_batch = 0
        for record in records:
            try:
                runner_id = record['runner_id']
                api_data = record['api_data']

                if not api_data or api_field not in api_data:
                    total_skip += 1
                    continue

                value = api_data[api_field]

                # Validate value
                if not validate_func(value):
                    total_skip += 1
                    continue

                # Convert data type
                if data_type == 'integer':
                    value = int(value)
                elif data_type == 'decimal':
                    value = float(value)
                # text stays as string

                # Update record with retry
                update_data = {
                    db_field: value,
                    'updated_at': datetime.utcnow().isoformat()
                }

                if update_record_with_retry(supabase, runner_id, update_data):
                    success_in_batch += 1
                    total_success += 1
                else:
                    total_error += 1

            except Exception as e:
                logger.error(f"  Error processing runner_id {record.get('runner_id')}: {e}")
                total_error += 1

        logger.info(f"  Batch {batch_num}: {success_in_batch} updated, {total_skip} skipped, {total_error} errors")

        # Brief pause between batches
        time.sleep(0.5)

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


def backfill_all_fields(batch_size: int = 25, resume: bool = True):
    """
    Backfill all fields with checkpointing

    Args:
        batch_size: Records per batch (default: 25, small to avoid timeouts)
        resume: Resume from checkpoint if available
    """
    logger.info("=" * 80)
    logger.info("OPTIMIZED BACKFILL - Works within Supabase timeout constraints")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Resume mode: {resume}")

    # Load checkpoint
    checkpoint = load_checkpoint() if resume else {'completed_fields': [], 'field_stats': {}}
    completed_fields = checkpoint.get('completed_fields', [])

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"✅ Connected to: {config.supabase.url}\n")

    all_stats = []
    start_time = time.time()

    # Process unique fields only
    processed_fields = set()

    for field_config in FIELD_MAPPINGS:
        db_field = field_config['db_field']

        # Skip duplicates
        if db_field in processed_fields:
            logger.info(f"Skipping duplicate field: {db_field}")
            continue

        processed_fields.add(db_field)

        # Skip if already completed (resume)
        if db_field in completed_fields:
            logger.info(f"Skipping completed field: {db_field}")
            # Load stats from checkpoint
            if db_field in checkpoint.get('field_stats', {}):
                all_stats.append(checkpoint['field_stats'][db_field])
            continue

        try:
            stats = backfill_field(supabase, field_config, batch_size)
            all_stats.append(stats)

            # Mark as completed
            completed_fields.append(db_field)
            checkpoint['completed_fields'] = completed_fields
            checkpoint['field_stats'][db_field] = stats
            checkpoint['last_updated'] = datetime.utcnow().isoformat()
            save_checkpoint(checkpoint)

        except Exception as e:
            logger.error(f"Failed to process {db_field}: {e}", exc_info=True)
            checkpoint['last_error'] = {
                'field': db_field,
                'error': str(e),
                'time': datetime.utcnow().isoformat()
            }
            save_checkpoint(checkpoint)

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

    # Clear checkpoint on successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info(f"\nCheckpoint file removed (backfill complete)")

    return all_stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Optimized backfill that works within Supabase timeout constraints'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=25,
        help='Records per batch (default: 25, small to avoid timeouts)'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start fresh (ignore checkpoint)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("OPTIMIZED BACKFILL FOR ra_runners")
    logger.info("=" * 80)
    logger.info("This script processes small batches to work within Supabase timeouts")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Resume: {not args.no_resume}")
    logger.info("\nThis may take several hours to complete all 1.3M records")
    logger.info("You can stop and resume anytime - progress is checkpointed")
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    logger.info("=" * 80 + "\n")

    time.sleep(3)

    try:
        stats = backfill_all_fields(
            batch_size=args.batch_size,
            resume=not args.no_resume
        )

        if stats is None:
            logger.error("\n❌ Backfill failed to start")
            return 1

        logger.info("\n✅ Backfill complete!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Interrupted by user")
        logger.info("Progress saved in checkpoint. Run again to resume.")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
