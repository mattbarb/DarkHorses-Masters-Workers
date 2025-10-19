"""
Backfill Horse Pedigree Data
Fetches detailed horse data including pedigree from Racing API HorsePro endpoint
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
from datetime import datetime
from typing import Dict, List
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('backfill_horse_pedigree')


class HorsePedigreeBackfill:
    """Backfill pedigree data for all horses in database"""

    def __init__(self):
        """Initialize backfill"""
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

    def get_all_horse_ids(self) -> List[str]:
        """Get all horse IDs from ra_horses table"""
        logger.info("Fetching all horse IDs from database...")

        try:
            result = self.db_client.client.table('ra_horses').select('horse_id').execute()
            horse_ids = [row['horse_id'] for row in result.data]
            logger.info(f"Found {len(horse_ids)} horses in database")
            return horse_ids
        except Exception as e:
            logger.error(f"Error fetching horse IDs: {e}")
            raise

    def fetch_horse_pro(self, horse_id: str) -> Dict:
        """
        Fetch detailed horse data from HorsePro endpoint

        Args:
            horse_id: Horse ID to fetch

        Returns:
            Horse data dictionary
        """
        try:
            response = self.api_client.get_horse_details(horse_id, tier='pro')
            return response
        except Exception as e:
            logger.error(f"Error fetching horse {horse_id}: {e}")
            return None

    def process_horse(self, horse_id: str) -> Dict:
        """
        Process single horse: fetch from API and update database

        Args:
            horse_id: Horse ID to process

        Returns:
            Status dictionary
        """
        # Fetch horse data from API
        horse_data = self.fetch_horse_pro(horse_id)

        if not horse_data:
            return {'success': False, 'error': 'API fetch failed'}

        # Update ra_horses with additional fields
        horse_update = {
            'horse_id': horse_id,
            'dob': horse_data.get('dob'),
            'sex_code': horse_data.get('sex_code'),
            'colour': horse_data.get('colour'),
            'colour_code': horse_data.get('colour_code'),
            'region': horse_data.get('region'),
            'updated_at': datetime.utcnow().isoformat()
        }

        try:
            self.db_client.client.table('ra_horses').update(horse_update).eq('horse_id', horse_id).execute()
        except Exception as e:
            logger.error(f"Error updating ra_horses for {horse_id}: {e}")

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
                'breeder': horse_data.get('breeder'),  # NEW FIELD
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            try:
                # Upsert pedigree
                self.db_client.insert_pedigree([pedigree_record])
                return {'success': True, 'has_pedigree': True}
            except Exception as e:
                logger.error(f"Error inserting pedigree for {horse_id}: {e}")
                return {'success': False, 'error': str(e)}
        else:
            return {'success': True, 'has_pedigree': False}

    def run(self, max_horses: int = None, skip_horses: int = 0):
        """
        Run backfill process

        Args:
            max_horses: Maximum number of horses to process (None = all)
            skip_horses: Number of horses to skip (for resuming)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("HORSE PEDIGREE BACKFILL")
        logger.info("=" * 80)

        # Get all horse IDs
        horse_ids = self.get_all_horse_ids()

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

        # Confirm before starting
        response = input(f"\nReady to process {total_horses} horses (est. {estimated_hours:.1f} hours)? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Backfill cancelled by user")
            return {'success': False, 'cancelled': True}

        # Process horses
        stats = {
            'total': total_horses,
            'processed': 0,
            'with_pedigree': 0,
            'without_pedigree': 0,
            'errors': 0,
            'start_time': datetime.utcnow()
        }

        logger.info("\nStarting backfill...")
        logger.info("Progress will be reported every 100 horses")

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

            # Progress logging every 100 horses
            if idx % 100 == 0:
                elapsed = (datetime.utcnow() - stats['start_time']).total_seconds()
                rate = idx / elapsed if elapsed > 0 else 0
                remaining = (total_horses - idx) / rate if rate > 0 else 0
                remaining_hours = remaining / 3600

                logger.info(f"Progress: {idx}/{total_horses} ({idx/total_horses*100:.1f}%) | "
                          f"Pedigrees: {stats['with_pedigree']} | "
                          f"Errors: {stats['errors']} | "
                          f"Rate: {rate:.1f}/sec | "
                          f"ETA: {remaining_hours:.1f}h")

            # Rate limiting: 2 requests per second
            time.sleep(0.5)

        # Final statistics
        stats['end_time'] = datetime.utcnow()
        stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
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

        return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill horse pedigree data')
    parser.add_argument('--max', type=int, help='Maximum number of horses to process')
    parser.add_argument('--skip', type=int, default=0, help='Number of horses to skip (for resuming)')
    parser.add_argument('--test', action='store_true', help='Test mode: process only 10 horses')

    args = parser.parse_args()

    backfill = HorsePedigreeBackfill()

    if args.test:
        logger.info("TEST MODE: Processing only 10 horses")
        result = backfill.run(max_horses=10)
    else:
        result = backfill.run(max_horses=args.max, skip_horses=args.skip)

    return result


if __name__ == '__main__':
    main()
