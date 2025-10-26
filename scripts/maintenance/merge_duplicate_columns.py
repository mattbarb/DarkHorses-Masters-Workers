"""
Merge Duplicate Columns in ra_mst_runners
Consolidates data from duplicate columns into primary columns before dropping duplicates
Uses small batches to avoid Supabase timeout constraints
"""

import os
import sys
import time
import json
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config.config import get_config
from supabase import create_client
from utils.logger import get_logger

logger = get_logger('merge_duplicates')

# Checkpoint file for resume capability
CHECKPOINT_FILE = 'logs/merge_duplicates_checkpoint.json'

# Duplicate column mappings: (primary_column, duplicate_column)
DUPLICATE_PAIRS = [
    {
        'name': 'Weight (lbs)',
        'primary': 'weight_lbs',
        'duplicate': 'weight',
        'description': 'Merge weight into weight_lbs'
    },
    {
        'name': 'Comment',
        'primary': 'comment',
        'duplicate': 'race_comment',
        'description': 'Merge race_comment into comment'
    },
    {
        'name': 'Silk URL',
        'primary': 'silk_url',
        'duplicate': 'jockey_silk_url',
        'description': 'Merge jockey_silk_url into silk_url'
    }
]


def load_checkpoint():
    """Load checkpoint from file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {'completed_pairs': [], 'pair_stats': {}}


def save_checkpoint(checkpoint):
    """Save checkpoint to file"""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def fetch_records_to_merge(supabase, primary_col: str, duplicate_col: str, batch_size: int, max_retries: int = 3):
    """
    Fetch records where primary is NULL but duplicate has value

    Returns:
        List of records to merge
    """
    for attempt in range(max_retries):
        try:
            result = supabase.table('ra_mst_runners') \
                .select(f'runner_id,{duplicate_col}') \
                .is_(primary_col, 'null') \
                .not_.is_(duplicate_col, 'null') \
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


def update_record_with_retry(supabase, runner_id: str, primary_col: str, value, max_retries: int = 3) -> bool:
    """
    Update a single record's primary column

    Returns:
        True if successful, False otherwise
    """
    for attempt in range(max_retries):
        try:
            supabase.table('ra_mst_runners') \
                .update({
                    primary_col: value,
                    'updated_at': datetime.utcnow().isoformat()
                }) \
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


def merge_duplicate_pair(supabase, pair_config: dict, batch_size: int = 25) -> dict:
    """
    Merge data from duplicate column into primary column

    Args:
        supabase: Supabase client
        pair_config: Pair configuration dict
        batch_size: Records per batch (small to avoid timeouts)

    Returns:
        Stats dict
    """
    name = pair_config['name']
    primary_col = pair_config['primary']
    duplicate_col = pair_config['duplicate']
    description = pair_config['description']

    logger.info(f"\n{'='*60}")
    logger.info(f"Merging: {name}")
    logger.info(f"Description: {description}")
    logger.info(f"Primary column: {primary_col}")
    logger.info(f"Duplicate column: {duplicate_col}")
    logger.info(f"{'='*60}")

    total_success = 0
    total_error = 0
    batch_num = 0
    consecutive_empty_batches = 0

    while consecutive_empty_batches < 3:  # Stop after 3 empty batches
        batch_num += 1

        # Fetch records to merge
        logger.info(f"  Batch {batch_num}: Fetching {batch_size} records...")
        records = fetch_records_to_merge(supabase, primary_col, duplicate_col, batch_size)

        if not records:
            consecutive_empty_batches += 1
            if consecutive_empty_batches >= 3:
                logger.info(f"  ✅ No more records to merge (3 consecutive empty batches)")
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
                value = record.get(duplicate_col)

                if value is None:
                    continue

                # Update primary column with duplicate's value
                if update_record_with_retry(supabase, runner_id, primary_col, value):
                    success_in_batch += 1
                    total_success += 1
                else:
                    total_error += 1

            except Exception as e:
                logger.error(f"  Error processing runner_id {record.get('runner_id')}: {e}")
                total_error += 1

        logger.info(f"  Batch {batch_num}: {success_in_batch} merged, {total_error} errors")

        # Brief pause between batches
        time.sleep(0.5)

    stats = {
        'pair': name,
        'primary_column': primary_col,
        'duplicate_column': duplicate_col,
        'batches': batch_num,
        'merged': total_success,
        'errors': total_error
    }

    logger.info(f"\n✅ {name} complete:")
    logger.info(f"   Merged: {total_success:,}")
    logger.info(f"   Errors: {total_error}")

    return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Merge duplicate columns in ra_mst_runners before dropping'
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
    logger.info("MERGE DUPLICATE COLUMNS IN ra_mst_runners")
    logger.info("=" * 80)
    logger.info("This script merges data from duplicate columns into primary columns")
    logger.info(f"Batch size: {args.batch_size}")
    logger.info(f"Resume: {not args.no_resume}")
    logger.info("\nPairs to merge:")
    for pair in DUPLICATE_PAIRS:
        logger.info(f"  • {pair['name']}: {pair['duplicate']} → {pair['primary']}")
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    logger.info("=" * 80 + "\n")

    time.sleep(3)

    # Load checkpoint
    checkpoint = load_checkpoint() if not args.no_resume else {'completed_pairs': [], 'pair_stats': {}}
    completed_pairs = checkpoint.get('completed_pairs', [])

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    logger.info(f"✅ Connected to: {config.supabase.url}\n")

    all_stats = []
    start_time = time.time()

    try:
        for pair in DUPLICATE_PAIRS:
            pair_name = pair['name']

            # Skip if already completed (resume)
            if pair_name in completed_pairs:
                logger.info(f"Skipping completed pair: {pair_name}")
                # Load stats from checkpoint
                if pair_name in checkpoint.get('pair_stats', {}):
                    all_stats.append(checkpoint['pair_stats'][pair_name])
                continue

            try:
                stats = merge_duplicate_pair(supabase, pair, args.batch_size)
                all_stats.append(stats)

                # Mark as completed
                completed_pairs.append(pair_name)
                checkpoint['completed_pairs'] = completed_pairs
                checkpoint['pair_stats'][pair_name] = stats
                checkpoint['last_updated'] = datetime.utcnow().isoformat()
                save_checkpoint(checkpoint)

            except Exception as e:
                logger.error(f"Failed to process {pair_name}: {e}", exc_info=True)
                checkpoint['last_error'] = {
                    'pair': pair_name,
                    'error': str(e),
                    'time': datetime.utcnow().isoformat()
                }
                save_checkpoint(checkpoint)

        # Final summary
        elapsed = time.time() - start_time

        logger.info("\n" + "=" * 80)
        logger.info("MERGE COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total time: {elapsed / 60:.1f} minutes")
        logger.info("\nResults by pair:")

        total_merged = 0
        total_errors = 0

        for stats in all_stats:
            logger.info(f"  {stats['pair']:20s}: {stats['merged']:,} merged, {stats['errors']} errors")
            total_merged += stats['merged']
            total_errors += stats['errors']

        logger.info(f"\nOverall:")
        logger.info(f"  Total merged: {total_merged:,}")
        logger.info(f"  Total errors: {total_errors}")

        # Clear checkpoint on successful completion
        if os.path.exists(CHECKPOINT_FILE):
            os.remove(CHECKPOINT_FILE)
            logger.info(f"\nCheckpoint file removed (merge complete)")

        logger.info("\n" + "=" * 80)
        logger.info("NEXT STEPS:")
        logger.info("1. Verify merge: Check that primary columns have all data")
        logger.info("2. Run migration 016 to drop duplicate columns")
        logger.info("3. Update fetchers to remove duplicate field assignments")
        logger.info("4. Update backfill script field mappings")
        logger.info("=" * 80)

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
