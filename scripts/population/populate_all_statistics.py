#!/usr/bin/env python3
"""
Populate All Statistics - Unified Production-Ready Script

Populates statistics for jockeys, trainers, and owners in a single unified process.
Handles pagination, progress tracking, checkpoints, and error recovery.

Features:
- Unified execution for all three entity types
- Pagination support (handles Supabase 1000-row limit)
- Real-time progress tracking with completion percentages
- Resume capability with checkpoint files
- Comprehensive error handling and logging
- Skip entities that already have statistics
- Dry-run mode for testing
- Detailed statistics (entities/second, ETA)

Usage:
    # Process all three entity types
    python3 scripts/populate_all_statistics.py --all

    # Process specific entity types
    python3 scripts/populate_all_statistics.py --entities jockeys trainers
    python3 scripts/populate_all_statistics.py --entities owners

    # Limit processing (for testing)
    python3 scripts/populate_all_statistics.py --all --limit 100

    # Resume from checkpoint (if interrupted)
    python3 scripts/populate_all_statistics.py --all --resume

    # Dry run (show what would be processed without executing)
    python3 scripts/populate_all_statistics.py --all --dry-run

    # Skip entities that already have statistics
    python3 scripts/populate_all_statistics.py --all --skip-existing

    # Combine options
    python3 scripts/populate_all_statistics.py --all --skip-existing --resume --limit 500
"""

import sys
import os
import argparse
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
import logging
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

# Import statistics calculation functions
from scripts.statistics_workers.jockeys_statistics_worker import calculate_jockey_statistics
from scripts.statistics_workers.trainers_statistics_worker import calculate_trainer_statistics
from scripts.statistics_workers.owners_statistics_worker import calculate_owner_statistics

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProgressTracker:
    """Tracks progress for entity processing with real-time statistics"""

    def __init__(self, total: int, entity_type: str):
        """
        Initialize progress tracker

        Args:
            total: Total number of entities to process
            entity_type: Type of entity (Jockeys, Trainers, Owners)
        """
        self.total = total
        self.processed = 0
        self.successful = 0
        self.failed = 0
        self.skipped = 0
        self.entity_type = entity_type
        self.start_time = time.time()
        self.last_print_time = time.time()

    def update(self, success: bool = True, skipped: bool = False):
        """
        Update progress counters

        Args:
            success: Whether processing was successful
            skipped: Whether entity was skipped
        """
        self.processed += 1

        if skipped:
            self.skipped += 1
        elif success:
            self.successful += 1
        else:
            self.failed += 1

        # Print progress every 10 entities or every 5 seconds
        current_time = time.time()
        if self.processed % 10 == 0 or (current_time - self.last_print_time) >= 5:
            self.print_progress()
            self.last_print_time = current_time

    def print_progress(self):
        """Print current progress with statistics"""
        elapsed = time.time() - self.start_time
        rate = self.processed / elapsed if elapsed > 0 else 0
        remaining = self.total - self.processed
        eta_seconds = remaining / rate if rate > 0 else 0

        percentage = (self.processed / self.total * 100) if self.total > 0 else 0

        logger.info(
            f"{self.entity_type}: {self.processed}/{self.total} "
            f"({percentage:.1f}%) | "
            f"Rate: {rate:.2f}/s | "
            f"ETA: {eta_seconds/60:.1f}m | "
            f"Success: {self.successful} | "
            f"Failed: {self.failed} | "
            f"Skipped: {self.skipped}"
        )

    def print_final(self):
        """Print final summary"""
        elapsed = time.time() - self.start_time
        rate = self.processed / elapsed if elapsed > 0 else 0

        logger.info(f"\n{'-' * 80}")
        logger.info(f"{self.entity_type} Processing Complete:")
        logger.info(f"  Total: {self.total}")
        logger.info(f"  Processed: {self.processed}")
        logger.info(f"  Successful: {self.successful}")
        logger.info(f"  Failed: {self.failed}")
        logger.info(f"  Skipped: {self.skipped}")
        logger.info(f"  Duration: {elapsed:.2f}s ({elapsed/60:.2f}m)")
        logger.info(f"  Rate: {rate:.2f}/s")
        logger.info(f"{'-' * 80}\n")

        return {
            'total': self.total,
            'processed': self.processed,
            'successful': self.successful,
            'failed': self.failed,
            'skipped': self.skipped,
            'duration': elapsed,
            'rate': rate
        }


class CheckpointManager:
    """Manages checkpoint files for resume capability"""

    def __init__(self, checkpoint_dir: str = 'logs'):
        """
        Initialize checkpoint manager

        Args:
            checkpoint_dir: Directory to store checkpoint files
        """
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(exist_ok=True)

    def save_checkpoint(self, entity_type: str, processed_ids: Set[str]):
        """
        Save checkpoint to file

        Args:
            entity_type: Type of entity (jockeys, trainers, owners)
            processed_ids: Set of processed entity IDs
        """
        checkpoint_file = self.checkpoint_dir / f'checkpoint_{entity_type}.json'
        checkpoint = {
            'entity_type': entity_type,
            'processed_ids': list(processed_ids),
            'count': len(processed_ids),
            'timestamp': datetime.utcnow().isoformat()
        }

        try:
            with open(checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {len(processed_ids)} {entity_type} processed")
        except Exception as e:
            logger.error(f"Error saving checkpoint for {entity_type}: {e}")

    def load_checkpoint(self, entity_type: str) -> Optional[Set[str]]:
        """
        Load checkpoint from file

        Args:
            entity_type: Type of entity (jockeys, trainers, owners)

        Returns:
            Set of processed entity IDs or None if no checkpoint exists
        """
        checkpoint_file = self.checkpoint_dir / f'checkpoint_{entity_type}.json'

        if not checkpoint_file.exists():
            return None

        try:
            with open(checkpoint_file, 'r') as f:
                checkpoint = json.load(f)

            processed_ids = set(checkpoint.get('processed_ids', []))
            timestamp = checkpoint.get('timestamp', 'unknown')
            logger.info(f"Loaded checkpoint: {len(processed_ids)} {entity_type} already processed (from {timestamp})")
            return processed_ids
        except Exception as e:
            logger.error(f"Error loading checkpoint for {entity_type}: {e}")
            return None

    def clear_checkpoint(self, entity_type: str):
        """
        Clear checkpoint file

        Args:
            entity_type: Type of entity (jockeys, trainers, owners)
        """
        checkpoint_file = self.checkpoint_dir / f'checkpoint_{entity_type}.json'

        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                logger.info(f"Checkpoint cleared for {entity_type}")
            except Exception as e:
                logger.error(f"Error clearing checkpoint for {entity_type}: {e}")


def fetch_all_entities(
    db_client: SupabaseReferenceClient,
    table_name: str,
    batch_size: int = 1000
) -> List[Dict]:
    """
    Fetch all entities from table with pagination

    Args:
        db_client: Supabase client
        table_name: Name of table to fetch from
        batch_size: Number of records per batch (max 1000 for Supabase)

    Returns:
        List of all entity records
    """
    all_entities = []
    offset = 0

    logger.info(f"Fetching entities from {table_name}...")

    while True:
        try:
            response = db_client.client.table(table_name)\
                .select('id, name')\
                .not_.like('id', '**TEST**%')\
                .range(offset, offset + batch_size - 1)\
                .execute()

            if not response.data:
                break

            all_entities.extend(response.data)
            logger.debug(f"Fetched {len(response.data)} entities (offset {offset})")

            # If we got fewer than batch_size, we're done
            if len(response.data) < batch_size:
                break

            offset += batch_size

        except Exception as e:
            logger.error(f"Error fetching entities from {table_name} at offset {offset}: {e}")
            break

    logger.info(f"Total entities fetched from {table_name}: {len(all_entities)}")
    return all_entities


def fetch_entities_needing_statistics(
    db_client: SupabaseReferenceClient,
    table_name: str,
    date_field: str,
    batch_size: int = 1000
) -> List[Dict]:
    """
    Fetch only entities that don't have statistics yet

    Args:
        db_client: Supabase client
        table_name: Name of table to fetch from
        date_field: Name of date field to check (last_ride_date or last_runner_date)
        batch_size: Number of records per batch

    Returns:
        List of entity records needing statistics
    """
    all_entities = []
    offset = 0

    logger.info(f"Fetching entities from {table_name} where {date_field} is NULL...")

    while True:
        try:
            response = db_client.client.table(table_name)\
                .select('id, name')\
                .is_(date_field, 'null')\
                .not_.like('id', '**TEST**%')\
                .range(offset, offset + batch_size - 1)\
                .execute()

            if not response.data:
                break

            all_entities.extend(response.data)
            logger.debug(f"Fetched {len(response.data)} entities needing statistics (offset {offset})")

            if len(response.data) < batch_size:
                break

            offset += batch_size

        except Exception as e:
            logger.error(f"Error fetching entities needing statistics from {table_name} at offset {offset}: {e}")
            break

    logger.info(f"Total entities needing statistics: {len(all_entities)}")
    return all_entities


def process_entity_type(
    entity_type: str,
    api_client: RacingAPIClient,
    db_client: SupabaseReferenceClient,
    checkpoint_manager: CheckpointManager,
    args
) -> Dict:
    """
    Process one entity type (jockeys, trainers, or owners)

    Args:
        entity_type: Type of entity to process
        api_client: Racing API client
        db_client: Supabase client
        checkpoint_manager: Checkpoint manager
        args: Command-line arguments

    Returns:
        Processing statistics dictionary
    """
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Processing {entity_type.upper()}")
    logger.info(f"{'=' * 80}\n")

    # Configure based on entity type
    if entity_type == 'jockeys':
        table_name = 'ra_jockeys'
        date_field = 'last_ride_date'
        worker_func = calculate_jockey_statistics
    elif entity_type == 'trainers':
        table_name = 'ra_trainers'
        date_field = 'last_runner_date'
        worker_func = calculate_trainer_statistics
    else:  # owners
        table_name = 'ra_owners'
        date_field = 'last_runner_date'
        worker_func = calculate_owner_statistics

    # Fetch entities
    if args.skip_existing:
        entities = fetch_entities_needing_statistics(db_client, table_name, date_field)
    else:
        entities = fetch_all_entities(db_client, table_name)

    if not entities:
        logger.warning(f"No {entity_type} found to process")
        return {
            'total': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'duration': 0,
            'rate': 0
        }

    # Apply limit if specified
    if args.limit:
        original_count = len(entities)
        entities = entities[:args.limit]
        logger.info(f"Limited to {len(entities)} {entity_type} (from {original_count} total)")

    # Load checkpoint if resuming
    processed_ids: Set[str] = set()
    if args.resume:
        checkpoint_ids = checkpoint_manager.load_checkpoint(entity_type)
        if checkpoint_ids:
            processed_ids = checkpoint_ids
            # Filter out already processed entities
            original_count = len(entities)
            entities = [e for e in entities if e['id'] not in processed_ids]
            logger.info(f"Resuming: {len(entities)} {entity_type} remaining (skipping {original_count - len(entities)} already processed)")

    if not entities:
        logger.info(f"All {entity_type} already processed, nothing to do")
        return {
            'total': len(processed_ids),
            'processed': len(processed_ids),
            'successful': len(processed_ids),
            'failed': 0,
            'skipped': 0,
            'duration': 0,
            'rate': 0
        }

    # Dry run mode - just show what would be processed
    if args.dry_run:
        logger.info(f"\n{'=' * 80}")
        logger.info(f"DRY RUN: Would process {len(entities)} {entity_type}")
        logger.info(f"{'=' * 80}")
        logger.info(f"Sample entities (first 5):")
        for i, entity in enumerate(entities[:5]):
            logger.info(f"  {i+1}. {entity.get('name', 'Unknown')} ({entity['id']})")
        if len(entities) > 5:
            logger.info(f"  ... and {len(entities) - 5} more")
        logger.info(f"{'=' * 80}\n")

        return {
            'total': len(entities),
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'duration': 0,
            'rate': 0
        }

    # Process entities
    tracker = ProgressTracker(len(entities), entity_type.capitalize())
    checkpoint_save_interval = 100  # Save checkpoint every 100 entities

    for idx, entity in enumerate(entities):
        entity_id = entity['id']
        entity_name = entity.get('name', 'Unknown')

        try:
            # Calculate statistics
            stats = worker_func(entity_id, entity_name, api_client)

            if stats:
                # Update database
                result = db_client.client.table(table_name).update(stats).eq('id', entity_id).execute()

                if result.data:
                    tracker.update(success=True)
                    processed_ids.add(entity_id)
                else:
                    logger.warning(f"Failed to update {entity_name} ({entity_id}): No data returned")
                    tracker.update(success=False)
            else:
                logger.warning(f"Failed to calculate statistics for {entity_name} ({entity_id})")
                tracker.update(success=False)

        except Exception as e:
            logger.error(f"Error processing {entity_name} ({entity_id}): {e}")
            tracker.update(success=False)

        # Save checkpoint periodically
        if (idx + 1) % checkpoint_save_interval == 0:
            checkpoint_manager.save_checkpoint(entity_type, processed_ids)

    # Print final progress
    tracker.print_progress()

    # Save final checkpoint
    checkpoint_manager.save_checkpoint(entity_type, processed_ids)

    # Return final statistics
    return tracker.print_final()


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Populate statistics for all entity types',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process all entity types
  python3 scripts/populate_all_statistics.py --all

  # Process specific entity types
  python3 scripts/populate_all_statistics.py --entities jockeys trainers

  # Test with limited entities
  python3 scripts/populate_all_statistics.py --all --limit 100

  # Resume from checkpoint
  python3 scripts/populate_all_statistics.py --all --resume

  # Skip entities that already have statistics
  python3 scripts/populate_all_statistics.py --all --skip-existing

  # Dry run (show what would be processed)
  python3 scripts/populate_all_statistics.py --all --dry-run
        """
    )

    # Entity selection
    parser.add_argument('--all', action='store_true',
                       help='Process all entity types (jockeys, trainers, owners)')
    parser.add_argument('--entities', nargs='+',
                       choices=['jockeys', 'trainers', 'owners'],
                       help='Specific entity types to process')

    # Processing options
    parser.add_argument('--limit', type=int,
                       help='Limit number of entities per type (for testing)')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip entities that already have statistics')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoint (if interrupted)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be processed without executing')

    # Checkpoint management
    parser.add_argument('--clear-checkpoints', action='store_true',
                       help='Clear all checkpoints before starting')

    args = parser.parse_args()

    # Determine which entities to process
    if args.all:
        entity_types = ['jockeys', 'trainers', 'owners']
    elif args.entities:
        entity_types = args.entities
    else:
        parser.error('Must specify --all or --entities')

    # Print header
    logger.info(f"\n{'=' * 80}")
    logger.info("POPULATE ALL STATISTICS - UNIFIED SCRIPT")
    logger.info(f"{'=' * 80}")
    logger.info(f"Entity types: {', '.join(entity_types)}")
    logger.info(f"Mode: {'DRY RUN' if args.dry_run else 'PRODUCTION'}")
    logger.info(f"Skip existing: {args.skip_existing}")
    logger.info(f"Resume: {args.resume}")
    logger.info(f"Limit: {args.limit if args.limit else 'None (all entities)'}")
    logger.info(f"{'=' * 80}\n")

    # Initialize clients
    logger.info("Initializing clients...")
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password
    )
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )
    checkpoint_manager = CheckpointManager()

    # Clear checkpoints if requested
    if args.clear_checkpoints:
        logger.info("Clearing all checkpoints...")
        for entity_type in ['jockeys', 'trainers', 'owners']:
            checkpoint_manager.clear_checkpoint(entity_type)

    # Process each entity type
    overall_start = time.time()
    all_stats = {}

    for entity_type in entity_types:
        try:
            stats = process_entity_type(
                entity_type=entity_type,
                api_client=api_client,
                db_client=db_client,
                checkpoint_manager=checkpoint_manager,
                args=args
            )
            all_stats[entity_type] = stats
        except Exception as e:
            logger.error(f"Fatal error processing {entity_type}: {e}", exc_info=True)
            all_stats[entity_type] = {
                'total': 0,
                'processed': 0,
                'successful': 0,
                'failed': 0,
                'skipped': 0,
                'duration': 0,
                'rate': 0,
                'error': str(e)
            }

    # Final summary
    overall_duration = time.time() - overall_start

    logger.info(f"\n{'=' * 80}")
    logger.info("FINAL SUMMARY")
    logger.info(f"{'=' * 80}\n")

    total_entities = 0
    total_processed = 0
    total_successful = 0
    total_failed = 0
    total_skipped = 0

    for entity_type, stats in all_stats.items():
        logger.info(f"{entity_type.capitalize()}:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  Processed: {stats['processed']}")
        logger.info(f"  Successful: {stats['successful']}")
        logger.info(f"  Failed: {stats['failed']}")
        logger.info(f"  Skipped: {stats['skipped']}")
        logger.info(f"  Duration: {stats['duration']:.2f}s")
        logger.info(f"  Rate: {stats['rate']:.2f}/s")
        if 'error' in stats:
            logger.info(f"  Error: {stats['error']}")
        logger.info("")

        total_entities += stats['total']
        total_processed += stats['processed']
        total_successful += stats['successful']
        total_failed += stats['failed']
        total_skipped += stats['skipped']

    logger.info(f"Overall Totals:")
    logger.info(f"  Total entities: {total_entities}")
    logger.info(f"  Processed: {total_processed}")
    logger.info(f"  Successful: {total_successful}")
    logger.info(f"  Failed: {total_failed}")
    logger.info(f"  Skipped: {total_skipped}")
    logger.info(f"  Total duration: {overall_duration:.2f}s ({overall_duration/60:.2f}m)")
    logger.info(f"  Overall rate: {total_processed/overall_duration:.2f}/s" if overall_duration > 0 else "  Overall rate: N/A")
    logger.info(f"\n{'=' * 80}")
    logger.info("COMPLETE")
    logger.info(f"{'=' * 80}\n")

    # Save final report
    report_file = Path('logs') / f'statistics_population_report_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
    try:
        with open(report_file, 'w') as f:
            json.dump({
                'timestamp': datetime.utcnow().isoformat(),
                'entity_types': entity_types,
                'mode': 'dry_run' if args.dry_run else 'production',
                'options': {
                    'skip_existing': args.skip_existing,
                    'resume': args.resume,
                    'limit': args.limit
                },
                'statistics': all_stats,
                'overall': {
                    'total_entities': total_entities,
                    'total_processed': total_processed,
                    'total_successful': total_successful,
                    'total_failed': total_failed,
                    'total_skipped': total_skipped,
                    'duration': overall_duration
                }
            }, f, indent=2)
        logger.info(f"Report saved to: {report_file}")
    except Exception as e:
        logger.error(f"Error saving report: {e}")


if __name__ == '__main__':
    main()
