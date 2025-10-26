"""
Entity Enrichment Backfill Script

This script enriches entities (horses, jockeys, trainers, owners, pedigrees) that were
skipped during the fast backfill process.

It reads all runners from ra_mst_runners table and extracts entities, enriching horses
with complete pedigree data from the Racing API Pro endpoint.

USAGE:
    # Enrich all entities
    python3 scripts/enrich_entities_backfill.py

    # Resume from checkpoint
    python3 scripts/enrich_entities_backfill.py --resume

    # Test mode (1000 runners only)
    python3 scripts/enrich_entities_backfill.py --test
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import json
from datetime import datetime
from typing import Dict, List, Optional
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.entity_extractor import EntityExtractor

logger = get_logger('enrich_entities_backfill')


class EntityEnrichmentBackfiller:
    """Backfill entity enrichment for runners collected in fast mode"""

    def __init__(self, checkpoint_file: str = None):
        """Initialize enrichment backfiller"""
        self.config = get_config()
        self.api_client = RacingAPIClient(
            username=self.config.api.username,
            password=self.config.api.password,
            base_url=self.config.api.base_url,
            timeout=self.config.api.timeout,
            max_retries=self.config.api.max_retries
        )
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

        # Entity extractor for enrichment
        self.entity_extractor = EntityExtractor(self.db_client, self.api_client)

        # Checkpoint file for resume capability
        if checkpoint_file:
            self.checkpoint_file = Path(checkpoint_file)
        else:
            self.checkpoint_file = Path(__file__).parent.parent / 'logs' / 'enrichment_checkpoint.json'

        # Error log file
        self.error_log_file = Path(__file__).parent.parent / 'logs' / 'enrichment_errors.json'

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint data if exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: {checkpoint.get('runners_processed', 0)} runners processed")
                return checkpoint
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return None

    def save_checkpoint(self, stats: Dict, last_race_id: str):
        """Save checkpoint for resume capability"""
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'stats': {
                'runners_processed': stats.get('runners_processed', 0),
                'horses_enriched': stats.get('horses_enriched', 0),
                'jockeys_processed': stats.get('jockeys_processed', 0),
                'trainers_processed': stats.get('trainers_processed', 0),
                'owners_processed': stats.get('owners_processed', 0),
                'pedigrees_captured': stats.get('pedigrees_captured', 0),
                'errors': stats.get('errors', 0),
                'start_time': stats.get('start_time').isoformat() if isinstance(stats.get('start_time'), datetime) else stats.get('start_time'),
            },
            'last_race_id': last_race_id
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {stats.get('runners_processed')} runners processed")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def log_error(self, race_id: str, error: str):
        """Log error to error file"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'race_id': race_id,
            'error': str(error)
        }

        try:
            errors = []
            if self.error_log_file.exists():
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)

            errors.append(error_entry)

            with open(self.error_log_file, 'w') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging to error file: {e}")

    def fetch_runners_batch(self, batch_size: int = 1000, last_race_id: Optional[str] = None) -> List[Dict]:
        """
        Fetch a batch of runners from database

        Args:
            batch_size: Number of runners to fetch
            last_race_id: Last race_id processed (for pagination)

        Returns:
            List of runner records
        """
        try:
            query = self.db_client.client.table('ra_mst_runners')\
                .select('race_id,horse_id,horse_name,jockey_id,jockey_name,trainer_id,trainer_name,owner_id,owner_name,sex')\
                .order('race_id')

            if last_race_id:
                query = query.gt('race_id', last_race_id)

            query = query.limit(batch_size)
            result = query.execute()

            return result.data if result.data else []

        except Exception as e:
            logger.error(f"Error fetching runners batch: {e}")
            return []

    def enrich_entities(
        self,
        resume: bool = False,
        batch_size: int = 1000,
        test_mode: bool = False
    ) -> Dict:
        """
        Enrich all entities from runners

        Args:
            resume: Resume from checkpoint if available
            batch_size: Number of runners to process per batch
            test_mode: Process only 1 batch for testing

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("ENTITY ENRICHMENT BACKFILL")
        logger.info("=" * 80)

        # Check for existing checkpoint
        checkpoint = None
        last_race_id = None

        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                last_race_id = checkpoint.get('last_race_id')
                logger.info(f"Resuming from checkpoint: {checkpoint.get('stats', {}).get('runners_processed', 0)} runners processed")
                logger.info(f"Last race_id: {last_race_id}")

        # Initialize stats
        if checkpoint and 'stats' in checkpoint:
            stats = checkpoint['stats']
            stats['start_time'] = datetime.fromisoformat(stats['start_time']) if isinstance(stats['start_time'], str) else stats['start_time']
            stats['session_start'] = datetime.utcnow()
        else:
            stats = {
                'runners_processed': 0,
                'horses_enriched': 0,
                'jockeys_processed': 0,
                'trainers_processed': 0,
                'owners_processed': 0,
                'pedigrees_captured': 0,
                'errors': 0,
                'start_time': datetime.utcnow(),
                'session_start': datetime.utcnow()
            }

        logger.info("\nStarting entity enrichment...")
        logger.info(f"Batch size: {batch_size}")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Checkpoint file: {self.checkpoint_file}")
        logger.info(f"Error log file: {self.error_log_file}")

        batch_count = 0
        total_runners = 0

        while True:
            batch_count += 1
            logger.info(f"\n{'='*80}")
            logger.info(f"BATCH {batch_count}")
            logger.info(f"{'='*80}")

            # Fetch next batch of runners
            runners = self.fetch_runners_batch(batch_size=batch_size, last_race_id=last_race_id)

            if not runners:
                logger.info("No more runners to process")
                break

            logger.info(f"Fetched {len(runners)} runners")
            total_runners += len(runners)

            # Transform runners to expected format
            runner_data = []
            for runner in runners:
                runner_record = {
                    'horse_id': runner.get('horse_id'),
                    'racing_api_horse_id': runner.get('horse_id'),
                    'horse_name': runner.get('horse_name'),
                    'sex': runner.get('sex'),
                    'jockey_id': runner.get('jockey_id'),
                    'racing_api_jockey_id': runner.get('jockey_id'),
                    'jockey_name': runner.get('jockey_name'),
                    'trainer_id': runner.get('trainer_id'),
                    'racing_api_trainer_id': runner.get('trainer_id'),
                    'trainer_name': runner.get('trainer_name'),
                    'owner_id': runner.get('owner_id'),
                    'racing_api_owner_id': runner.get('owner_id'),
                    'owner_name': runner.get('owner_name')
                }
                if runner_record.get('horse_id') and runner_record.get('horse_name'):
                    runner_data.append(runner_record)

            # Extract and enrich entities
            try:
                logger.info(f"Extracting and enriching entities from {len(runner_data)} runners...")
                entity_stats = self.entity_extractor.extract_and_store_from_runners(runner_data)

                # Update stats
                stats['runners_processed'] += len(runners)
                stats['horses_enriched'] += entity_stats.get('horses', {}).get('inserted', 0)
                stats['jockeys_processed'] += entity_stats.get('jockeys', {}).get('inserted', 0)
                stats['trainers_processed'] += entity_stats.get('trainers', {}).get('inserted', 0)
                stats['owners_processed'] += entity_stats.get('owners', {}).get('inserted', 0)
                stats['pedigrees_captured'] += entity_stats.get('pedigrees', {}).get('inserted', 0)

                logger.info(f"Entity stats: {entity_stats}")

            except Exception as e:
                stats['errors'] += 1
                error_msg = str(e)
                logger.error(f"Error enriching entities: {error_msg}")
                self.log_error(runners[-1].get('race_id', 'unknown'), error_msg)

            # Update checkpoint
            last_race_id = runners[-1].get('race_id')
            self.save_checkpoint(stats, last_race_id)

            # Progress logging
            elapsed = (datetime.utcnow() - stats['session_start']).total_seconds()
            rate = stats['runners_processed'] / elapsed if elapsed > 0 else 0

            logger.info("\n" + "-" * 80)
            logger.info(f"BATCH {batch_count} COMPLETE")
            logger.info(f"  Runners processed: {stats['runners_processed']:,}")
            logger.info(f"  Horses enriched: {stats['horses_enriched']:,}")
            logger.info(f"  Jockeys: {stats['jockeys_processed']:,}")
            logger.info(f"  Trainers: {stats['trainers_processed']:,}")
            logger.info(f"  Owners: {stats['owners_processed']:,}")
            logger.info(f"  Pedigrees: {stats['pedigrees_captured']:,}")
            logger.info(f"  Errors: {stats['errors']}")
            logger.info(f"  Rate: {rate:.2f} runners/sec")
            logger.info("-" * 80)

            # Test mode: process only 1 batch
            if test_mode:
                logger.info("\nTest mode: stopping after 1 batch")
                break

        # Final statistics
        stats['end_time'] = datetime.utcnow()
        stats['duration_seconds'] = (stats['end_time'] - stats['session_start']).total_seconds()
        stats['duration_hours'] = stats['duration_seconds'] / 3600
        stats['duration_days'] = stats['duration_hours'] / 24

        logger.info("\n" + "=" * 80)
        logger.info("ENRICHMENT COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total runners processed: {stats['runners_processed']:,}")
        logger.info(f"Horses enriched: {stats['horses_enriched']:,}")
        logger.info(f"Jockeys: {stats['jockeys_processed']:,}")
        logger.info(f"Trainers: {stats['trainers_processed']:,}")
        logger.info(f"Owners: {stats['owners_processed']:,}")
        logger.info(f"Pedigrees captured: {stats['pedigrees_captured']:,}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Duration: {stats['duration_days']:.2f} days ({stats['duration_hours']:.1f} hours)")
        logger.info("=" * 80)

        # Save final checkpoint
        if last_race_id:
            self.save_checkpoint(stats, last_race_id)

        return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Entity enrichment backfill for fast-mode collected data',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Enrich all entities
  python3 scripts/enrich_entities_backfill.py

  # Resume from checkpoint
  python3 scripts/enrich_entities_backfill.py --resume

  # Test mode (1 batch = 1000 runners)
  python3 scripts/enrich_entities_backfill.py --test
        """
    )

    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoint')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only 1000 runners')
    parser.add_argument('--batch-size', type=int, default=1000,
                       help='Number of runners to process per batch (default: 1000)')
    parser.add_argument('--checkpoint-file', type=str,
                       help='Custom checkpoint file path')

    args = parser.parse_args()

    backfiller = EntityEnrichmentBackfiller(checkpoint_file=args.checkpoint_file)

    # Run enrichment
    result = backfiller.enrich_entities(
        resume=args.resume,
        batch_size=args.batch_size,
        test_mode=args.test
    )

    return result


if __name__ == '__main__':
    main()
