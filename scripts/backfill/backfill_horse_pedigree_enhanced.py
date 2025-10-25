"""
Enhanced Backfill Horse Pedigree Data
Fetches detailed horse data including pedigree from Racing API HorsePro endpoint
Includes: Resume capability, error handling, progress tracking, and monitoring
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
from utils.region_extractor import extract_region_from_name

logger = get_logger('backfill_horse_pedigree')


class HorsePedigreeBackfillEnhanced:
    """Enhanced backfill with resume capability and better monitoring"""

    def __init__(self, checkpoint_file: str = None):
        """Initialize backfill with optional checkpoint file"""
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

        # Checkpoint file for resume capability
        if checkpoint_file:
            self.checkpoint_file = Path(checkpoint_file)
        else:
            self.checkpoint_file = Path(__file__).parent.parent / 'logs' / 'backfill_checkpoint.json'

        # Error log file
        self.error_log_file = Path(__file__).parent.parent / 'logs' / 'backfill_errors.json'

    def get_all_horse_ids(self) -> List[str]:
        """Get all horse IDs from ra_horses table that need enrichment"""
        logger.info("Fetching horse IDs from database...")

        try:
            # Get horses without dob (not yet enriched)
            # Paginate through all results to avoid 1000 record limit
            all_horse_ids = []
            page_size = 1000
            offset = 0

            while True:
                result = self.db_client.client.table('ra_horses')\
                    .select('horse_id')\
                    .is_('dob', 'null')\
                    .order('horse_id')\
                    .range(offset, offset + page_size - 1)\
                    .execute()

                if not result.data:
                    break

                all_horse_ids.extend([row['horse_id'] for row in result.data])
                logger.debug(f"Fetched {len(result.data)} horses (total: {len(all_horse_ids)})")

                if len(result.data) < page_size:
                    break

                offset += page_size

            logger.info(f"Found {len(all_horse_ids)} horses needing enrichment")
            return all_horse_ids
        except Exception as e:
            logger.error(f"Error fetching horse IDs: {e}")
            raise

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint data if exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: {checkpoint['processed']} horses processed")
                return checkpoint
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return None

    def save_checkpoint(self, stats: Dict, processed_ids: List[str]):
        """Save checkpoint for resume capability"""
        # Convert datetime objects to ISO format strings for JSON serialization
        stats_serializable = {}
        for key, value in stats.items():
            if isinstance(value, datetime):
                stats_serializable[key] = value.isoformat()
            else:
                stats_serializable[key] = value

        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'stats': stats_serializable,
            'processed_ids': processed_ids,
            'processed': len(processed_ids)
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {len(processed_ids)} horses")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def log_error(self, horse_id: str, error: str):
        """Log error to error file"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'horse_id': horse_id,
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

    def fetch_horse_pro(self, horse_id: str, retries: int = 3) -> Optional[Dict]:
        """
        Fetch detailed horse data from HorsePro endpoint with retry logic

        Args:
            horse_id: Horse ID to fetch
            retries: Number of retries on failure

        Returns:
            Horse data dictionary or None
        """
        for attempt in range(retries):
            try:
                response = self.api_client.get_horse_details(horse_id, tier='pro')
                return response
            except Exception as e:
                error_msg = str(e)

                # Handle specific error types
                if '404' in error_msg:
                    logger.debug(f"Horse {horse_id} not found in Pro API (404)")
                    return None
                elif '429' in error_msg:
                    # Rate limit hit - wait longer
                    wait_time = 5 * (attempt + 1)
                    logger.warning(f"Rate limit hit for horse {horse_id}, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                elif attempt < retries - 1:
                    # Retry on other errors
                    wait_time = 2 * (attempt + 1)
                    logger.warning(f"Error fetching horse {horse_id} (attempt {attempt+1}/{retries}): {e}")
                    time.sleep(wait_time)
                    continue
                else:
                    # Final retry failed
                    logger.error(f"Failed to fetch horse {horse_id} after {retries} attempts: {e}")
                    self.log_error(horse_id, error_msg)
                    return None

        return None

    def process_horse(self, horse_id: str) -> Dict:
        """
        Process single horse: fetch from API and update database

        Args:
            horse_id: Horse ID to process

        Returns:
            Status dictionary with success, has_pedigree, and error info
        """
        # Fetch horse data from API
        horse_data = self.fetch_horse_pro(horse_id)

        if not horse_data:
            return {'success': False, 'error': 'API fetch failed', 'has_pedigree': False}

        # Extract region from horse name (breeding origin)
        horse_name = horse_data.get('name', '')
        region = extract_region_from_name(horse_name)

        # Update ra_horses with additional fields
        horse_update = {
            'horse_id': horse_id,
            'dob': horse_data.get('dob'),
            'sex_code': horse_data.get('sex_code'),
            'colour': horse_data.get('colour'),
            'colour_code': horse_data.get('colour_code'),
            'region': region,  # Extracted from name
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            self.db_client.client.table('ra_horses').update(horse_update).eq('horse_id', horse_id).execute()
        except Exception as e:
            error_msg = f"Error updating ra_horses for {horse_id}: {e}"
            logger.error(error_msg)
            self.log_error(horse_id, error_msg)
            return {'success': False, 'error': error_msg, 'has_pedigree': False}

        # Insert/update pedigree data if available
        has_pedigree = any([
            horse_data.get('sire_id'),
            horse_data.get('dam_id'),
            horse_data.get('damsire_id')
        ])

        if has_pedigree:
            pedigree_record = {
                'horse_id': horse_id,
                'sire_id': horse_data.get('sire_id'),
                'sire': horse_data.get('sire'),
                'dam_id': horse_data.get('dam_id'),
                'dam': horse_data.get('dam'),
                'damsire_id': horse_data.get('damsire_id'),
                'damsire': horse_data.get('damsire'),
                'breeder': horse_data.get('breeder'),
                'region': region,  # Extracted from horse name
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            try:
                # Upsert pedigree
                self.db_client.insert_pedigree([pedigree_record])
                return {'success': True, 'has_pedigree': True}
            except Exception as e:
                error_msg = f"Error inserting pedigree for {horse_id}: {e}"
                logger.error(error_msg)
                self.log_error(horse_id, error_msg)
                return {'success': False, 'error': error_msg, 'has_pedigree': False}
        else:
            return {'success': True, 'has_pedigree': False}

    def run(self, max_horses: int = None, skip_horses: int = 0, resume: bool = False,
            non_interactive: bool = False):
        """
        Run backfill process

        Args:
            max_horses: Maximum number of horses to process (None = all)
            skip_horses: Number of horses to skip (for resuming)
            resume: Resume from checkpoint if available
            non_interactive: Don't prompt for confirmation (for background jobs)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("ENHANCED HORSE PEDIGREE BACKFILL")
        logger.info("=" * 80)

        # Check for existing checkpoint
        checkpoint = None
        processed_ids = []

        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                processed_ids = checkpoint.get('processed_ids', [])
                logger.info(f"Resuming from checkpoint: {len(processed_ids)} horses already processed")

        # Get all horse IDs that need enrichment
        horse_ids = self.get_all_horse_ids()

        # Remove already processed IDs if resuming
        if processed_ids:
            horse_ids = [hid for hid in horse_ids if hid not in processed_ids]
            logger.info(f"Remaining horses to process: {len(horse_ids)}")

        # Apply skip and limit
        if skip_horses > 0:
            logger.info(f"Skipping first {skip_horses} horses")
            horse_ids = horse_ids[skip_horses:]

        if max_horses:
            logger.info(f"Limiting to {max_horses} horses")
            horse_ids = horse_ids[:max_horses]

        total_horses = len(horse_ids)
        logger.info(f"Processing {total_horses} horses")

        # Calculate estimated time
        estimated_seconds = total_horses * 0.5  # 2 requests/second = 0.5s per request
        estimated_hours = estimated_seconds / 3600
        logger.info(f"Estimated time: {estimated_hours:.1f} hours ({estimated_seconds/60:.0f} minutes)")

        # Calculate ETA
        eta = datetime.utcnow().timestamp() + estimated_seconds
        eta_str = datetime.fromtimestamp(eta).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Estimated completion: {eta_str}")

        # Confirm before starting (unless non-interactive)
        if not non_interactive:
            response = input(f"\nReady to process {total_horses} horses (est. {estimated_hours:.1f} hours)? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Backfill cancelled by user")
                return {'success': False, 'cancelled': True}

        # Initialize stats
        if checkpoint and 'stats' in checkpoint:
            stats = checkpoint['stats']
            # Convert string timestamps back to datetime objects
            if isinstance(stats.get('start_time'), str):
                stats['start_time'] = datetime.fromisoformat(stats['start_time'].replace('Z', '+00:00'))
            if isinstance(stats.get('session_start'), str):
                stats['session_start'] = datetime.fromisoformat(stats['session_start'].replace('Z', '+00:00'))
            # Reset session_start for new session
            stats['session_start'] = datetime.utcnow()
        else:
            stats = {
                'total': total_horses,
                'processed': 0,
                'with_pedigree': 0,
                'without_pedigree': 0,
                'errors': 0,
                'start_time': datetime.utcnow(),
                'session_start': datetime.utcnow()
            }

        logger.info("\nStarting backfill...")
        logger.info("Progress will be reported every 100 horses")
        logger.info("Checkpoint will be saved every 100 horses")
        logger.info(f"Checkpoint file: {self.checkpoint_file}")
        logger.info(f"Error log file: {self.error_log_file}")

        # Process horses
        for idx, horse_id in enumerate(horse_ids, 1):
            # Process horse
            result = self.process_horse(horse_id)

            # Update stats
            stats['processed'] += 1
            if result.get('success'):
                if result.get('has_pedigree'):
                    stats['with_pedigree'] += 1
                else:
                    stats['without_pedigree'] += 1
            else:
                stats['errors'] += 1

            # Track processed IDs
            processed_ids.append(horse_id)

            # Progress logging and checkpoint saving every 100 horses
            if idx % 100 == 0:
                elapsed = (datetime.utcnow() - stats['session_start']).total_seconds()
                rate = idx / elapsed if elapsed > 0 else 0
                remaining = (total_horses - idx) / rate if rate > 0 else 0
                remaining_hours = remaining / 3600

                # Calculate new ETA
                eta_timestamp = datetime.utcnow().timestamp() + remaining
                eta_str = datetime.fromtimestamp(eta_timestamp).strftime('%Y-%m-%d %H:%M:%S')

                logger.info(f"Progress: {idx}/{total_horses} ({idx/total_horses*100:.1f}%) | "
                          f"Pedigrees: {stats['with_pedigree']} | "
                          f"Errors: {stats['errors']} | "
                          f"Rate: {rate:.1f}/sec | "
                          f"ETA: {remaining_hours:.1f}h ({eta_str})")

                # Save checkpoint
                self.save_checkpoint(stats, processed_ids)

            # Rate limiting: 2 requests per second
            time.sleep(0.5)

        # Final statistics
        stats['end_time'] = datetime.utcnow()
        stats['duration_seconds'] = (stats['end_time'] - stats['session_start']).total_seconds()
        stats['duration_hours'] = stats['duration_seconds'] / 3600

        logger.info("\n" + "=" * 80)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total processed: {stats['processed']}")
        logger.info(f"With pedigree: {stats['with_pedigree']} ({stats['with_pedigree']/stats['processed']*100:.1f}%)")
        logger.info(f"Without pedigree: {stats['without_pedigree']} ({stats['without_pedigree']/stats['processed']*100:.1f}%)")
        logger.info(f"Errors: {stats['errors']} ({stats['errors']/stats['processed']*100:.1f}%)")
        logger.info(f"Duration: {stats['duration_hours']:.2f} hours ({stats['duration_seconds']/60:.0f} minutes)")
        logger.info("=" * 80)

        # Save final checkpoint
        self.save_checkpoint(stats, processed_ids)

        return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Enhanced backfill horse pedigree data')
    parser.add_argument('--max', type=int, help='Maximum number of horses to process')
    parser.add_argument('--skip', type=int, default=0, help='Number of horses to skip')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--test', action='store_true', help='Test mode: process only 10 horses')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run without confirmation prompt (for background jobs)')
    parser.add_argument('--checkpoint-file', type=str, help='Custom checkpoint file path')

    args = parser.parse_args()

    backfill = HorsePedigreeBackfillEnhanced(checkpoint_file=args.checkpoint_file)

    if args.test:
        logger.info("TEST MODE: Processing only 10 horses")
        result = backfill.run(max_horses=10, non_interactive=args.non_interactive)
    else:
        result = backfill.run(
            max_horses=args.max,
            skip_horses=args.skip,
            resume=args.resume,
            non_interactive=args.non_interactive
        )

    return result


if __name__ == '__main__':
    main()
