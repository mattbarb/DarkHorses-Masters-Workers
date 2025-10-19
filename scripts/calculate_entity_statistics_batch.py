#!/usr/bin/env python3
"""
Calculate Entity Statistics (Batch Processing)
==============================================

Calculates statistics for jockeys, trainers, and owners using batch processing
to avoid timeout issues with large datasets.

Instead of calling the SQL function (which can timeout), this script:
1. Queries the statistics views in batches
2. Updates entity tables directly
3. Shows progress as it goes

Usage:
    python3 scripts/calculate_entity_statistics_batch.py
    python3 scripts/calculate_entity_statistics_batch.py --batch-size 100
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('calculate_entity_statistics_batch')


class BatchStatisticsCalculator:
    """Calculate entity statistics using batch processing"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key
        )

    def update_jockeys(self) -> int:
        """Update jockey statistics"""
        logger.info("Updating jockey statistics...")

        # Get all jockeys
        jockeys = self.db_client.client.table('ra_jockeys').select('jockey_id').execute()
        total = len(jockeys.data)
        logger.info(f"Found {total} jockeys to update")

        updated = 0
        for i in range(0, total, self.batch_size):
            batch_ids = [j['jockey_id'] for j in jockeys.data[i:i+self.batch_size]]

            # Get statistics for this batch
            stats = self.db_client.client.table('jockey_statistics').select('*').in_('jockey_id', batch_ids).execute()

            # Update each jockey
            for stat in stats.data:
                try:
                    self.db_client.client.table('ra_jockeys').update({
                        'total_rides': stat['calculated_total_rides'],
                        'total_wins': stat['calculated_total_wins'],
                        'total_places': stat['calculated_total_places'],
                        'total_seconds': stat['calculated_total_seconds'],
                        'total_thirds': stat['calculated_total_thirds'],
                        'win_rate': stat['calculated_win_rate'],
                        'place_rate': stat['calculated_place_rate'],
                        'stats_updated_at': datetime.now().isoformat()
                    }).eq('jockey_id', stat['jockey_id']).execute()
                    updated += 1
                except Exception as e:
                    logger.error(f"Error updating jockey {stat['jockey_id']}: {e}")

            logger.info(f"Progress: {min(i+self.batch_size, total)}/{total} jockeys")

        return updated

    def update_trainers(self) -> int:
        """Update trainer statistics"""
        logger.info("Updating trainer statistics...")

        trainers = self.db_client.client.table('ra_trainers').select('trainer_id').execute()
        total = len(trainers.data)
        logger.info(f"Found {total} trainers to update")

        updated = 0
        for i in range(0, total, self.batch_size):
            batch_ids = [t['trainer_id'] for t in trainers.data[i:i+self.batch_size]]

            stats = self.db_client.client.table('trainer_statistics').select('*').in_('trainer_id', batch_ids).execute()

            for stat in stats.data:
                try:
                    self.db_client.client.table('ra_trainers').update({
                        'total_runners': stat['calculated_total_runners'],
                        'total_wins': stat['calculated_total_wins'],
                        'total_places': stat['calculated_total_places'],
                        'total_seconds': stat['calculated_total_seconds'],
                        'total_thirds': stat['calculated_total_thirds'],
                        'win_rate': stat['calculated_win_rate'],
                        'place_rate': stat['calculated_place_rate'],
                        'recent_14d_runs': stat['calculated_recent_14d_runs'],
                        'recent_14d_wins': stat['calculated_recent_14d_wins'],
                        'recent_14d_win_rate': stat['calculated_recent_14d_win_rate'],
                        'stats_updated_at': datetime.now().isoformat()
                    }).eq('trainer_id', stat['trainer_id']).execute()
                    updated += 1
                except Exception as e:
                    logger.error(f"Error updating trainer {stat['trainer_id']}: {e}")

            logger.info(f"Progress: {min(i+self.batch_size, total)}/{total} trainers")

        return updated

    def update_owners(self) -> int:
        """Update owner statistics"""
        logger.info("Updating owner statistics...")

        owners = self.db_client.client.table('ra_owners').select('owner_id').execute()
        total = len(owners.data)
        logger.info(f"Found {total} owners to update")

        updated = 0
        for i in range(0, total, self.batch_size):
            batch_ids = [o['owner_id'] for o in owners.data[i:i+self.batch_size]]

            stats = self.db_client.client.table('owner_statistics').select('*').in_('owner_id', batch_ids).execute()

            for stat in stats.data:
                try:
                    self.db_client.client.table('ra_owners').update({
                        'total_horses': stat['calculated_total_horses'],
                        'total_runners': stat['calculated_total_runners'],
                        'total_wins': stat['calculated_total_wins'],
                        'total_places': stat['calculated_total_places'],
                        'total_seconds': stat['calculated_total_seconds'],
                        'total_thirds': stat['calculated_total_thirds'],
                        'win_rate': stat['calculated_win_rate'],
                        'place_rate': stat['calculated_place_rate'],
                        'active_last_30d': stat['calculated_active_last_30d'],
                        'stats_updated_at': datetime.now().isoformat()
                    }).eq('owner_id', stat['owner_id']).execute()
                    updated += 1
                except Exception as e:
                    logger.error(f"Error updating owner {stat['owner_id']}: {e}")

            logger.info(f"Progress: {min(i+self.batch_size, total)}/{total} owners")

        return updated

    def calculate_all(self) -> dict:
        """Calculate statistics for all entities"""
        logger.info("=" * 80)
        logger.info("CALCULATING ENTITY STATISTICS (BATCH MODE)")
        logger.info("=" * 80)

        start_time = datetime.now()

        try:
            jockeys_updated = self.update_jockeys()
            trainers_updated = self.update_trainers()
            owners_updated = self.update_owners()

            duration = (datetime.now() - start_time).total_seconds()

            logger.info("-" * 80)
            logger.info("✓ Statistics calculation complete")
            logger.info("-" * 80)
            logger.info(f"Jockeys updated:  {jockeys_updated:,}")
            logger.info(f"Trainers updated: {trainers_updated:,}")
            logger.info(f"Owners updated:   {owners_updated:,}")
            logger.info(f"Duration:         {duration:.2f} seconds")
            logger.info("-" * 80)

            return {
                'success': True,
                'jockeys_updated': jockeys_updated,
                'trainers_updated': trainers_updated,
                'owners_updated': owners_updated,
                'duration_seconds': duration
            }

        except Exception as e:
            logger.error(f"✗ Statistics calculation failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }


def main():
    parser = argparse.ArgumentParser(description='Calculate entity statistics (batch mode)')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    args = parser.parse_args()

    calculator = BatchStatisticsCalculator(batch_size=args.batch_size)
    result = calculator.calculate_all()

    sys.exit(0 if result['success'] else 1)


if __name__ == '__main__':
    main()
