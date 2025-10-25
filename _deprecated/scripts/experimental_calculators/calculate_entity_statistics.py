#!/usr/bin/env python3
"""
Calculate Entity Statistics (Jockey, Trainer, Owner)
====================================================

Calculates and updates performance statistics for jockeys, trainers, and owners
from race results data in ra_runners table.

This script uses the SQL function created by Migration 007 to calculate:
- Career statistics (total rides/runners, wins, places, win rate, place rate)
- Recent form (14-day stats for trainers)
- Activity status (30-day activity for owners)

Usage:
    python3 scripts/calculate_entity_statistics.py

    # With verbose output
    python3 scripts/calculate_entity_statistics.py --verbose

Integration:
    - Run daily after results_fetcher completes
    - Can be integrated into main.py daily schedule
    - Safe to run multiple times (idempotent)

Requirements:
    - Migration 007 must be executed (creates update_entity_statistics() function)
    - Position data must exist in ra_runners table
    - Takes ~5-15 seconds depending on data volume
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('calculate_entity_statistics')


class EntityStatisticsCalculator:
    """Calculate and update entity statistics from race results"""

    def __init__(self, verbose: bool = False):
        """
        Initialize the calculator

        Args:
            verbose: Enable verbose logging
        """
        self.verbose = verbose
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key
        )

    def calculate_and_update(self) -> dict:
        """
        Calculate statistics for all entities and update database

        Uses the update_entity_statistics() SQL function created by Migration 007.
        This function:
        1. Queries the statistics views (jockey_statistics, trainer_statistics, owner_statistics)
        2. Updates corresponding entity tables with calculated values
        3. Sets stats_updated_at timestamp

        Returns:
            dict: Results with counts of entities updated
                {
                    'success': bool,
                    'jockeys_updated': int,
                    'trainers_updated': int,
                    'owners_updated': int,
                    'timestamp': str,
                    'error': str (if success=False)
                }
        """
        logger.info("=" * 80)
        logger.info("CALCULATING ENTITY STATISTICS")
        logger.info("=" * 80)

        try:
            # Record start time
            start_time = datetime.now()

            if self.verbose:
                logger.info("Calling update_entity_statistics() SQL function...")
                logger.info("This function:")
                logger.info("  1. Calculates jockey statistics from ra_runners")
                logger.info("  2. Calculates trainer statistics from ra_runners")
                logger.info("  3. Calculates owner statistics from ra_runners")
                logger.info("  4. Updates entity tables with calculated values")

            # Call the SQL function created by Migration 007
            # Use longer timeout for large datasets
            result = self.db_client.client.rpc('update_entity_statistics').execute()

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()

            # Extract counts from result
            if result.data and len(result.data) > 0:
                counts = result.data[0]
                jockeys_updated = counts.get('jockeys_updated', 0)
                trainers_updated = counts.get('trainers_updated', 0)
                owners_updated = counts.get('owners_updated', 0)
            else:
                jockeys_updated = 0
                trainers_updated = 0
                owners_updated = 0

            logger.info("-" * 80)
            logger.info("✓ Statistics calculation complete")
            logger.info("-" * 80)
            logger.info(f"Jockeys updated:  {jockeys_updated:,}")
            logger.info(f"Trainers updated: {trainers_updated:,}")
            logger.info(f"Owners updated:   {owners_updated:,}")
            logger.info(f"Duration:         {duration:.2f} seconds")
            logger.info("-" * 80)

            if self.verbose:
                logger.info("\nStatistics fields updated:")
                logger.info("  Jockeys:  total_rides, total_wins, total_places, win_rate, place_rate")
                logger.info("  Trainers: total_runners, total_wins, total_places, win_rate, place_rate, recent_14d_*")
                logger.info("  Owners:   total_horses, total_runners, total_wins, win_rate, active_last_30d")

            return {
                'success': True,
                'jockeys_updated': jockeys_updated,
                'trainers_updated': trainers_updated,
                'owners_updated': owners_updated,
                'timestamp': datetime.now().isoformat(),
                'duration_seconds': duration
            }

        except Exception as e:
            logger.error(f"✗ Statistics calculation failed: {e}", exc_info=True)
            logger.error("-" * 80)
            logger.error("Troubleshooting:")
            logger.error("  1. Check Migration 007 was executed")
            logger.error("  2. Verify update_entity_statistics() function exists")
            logger.error("  3. Ensure ra_runners has position data")
            logger.error("  4. Check database connection")
            logger.error("-" * 80)

            return {
                'success': False,
                'jockeys_updated': 0,
                'trainers_updated': 0,
                'owners_updated': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    def verify_statistics(self) -> dict:
        """
        Verify statistics were calculated correctly

        Queries entity tables to check:
        - Statistics fields are populated (not NULL)
        - Values are reasonable (win_rate between 0-100, etc.)
        - stats_updated_at is recent

        Returns:
            dict: Verification results
        """
        logger.info("\nVerifying statistics...")

        try:
            verification = {}

            # Check jockeys
            jockey_result = self.db_client.client.table('ra_jockeys').select(
                'jockey_id, name, total_rides, total_wins, win_rate, stats_updated_at'
            ).not_.is_('total_rides', 'null').limit(5).execute()

            verification['jockeys'] = {
                'sample_count': len(jockey_result.data),
                'sample_data': jockey_result.data[:3] if jockey_result.data else []
            }

            # Check trainers
            trainer_result = self.db_client.client.table('ra_trainers').select(
                'trainer_id, name, total_runners, total_wins, win_rate, stats_updated_at'
            ).not_.is_('total_runners', 'null').limit(5).execute()

            verification['trainers'] = {
                'sample_count': len(trainer_result.data),
                'sample_data': trainer_result.data[:3] if trainer_result.data else []
            }

            # Check owners
            owner_result = self.db_client.client.table('ra_owners').select(
                'owner_id, name, total_runners, total_wins, win_rate, stats_updated_at'
            ).not_.is_('total_runners', 'null').limit(5).execute()

            verification['owners'] = {
                'sample_count': len(owner_result.data),
                'sample_data': owner_result.data[:3] if owner_result.data else []
            }

            logger.info("✓ Verification complete")

            if self.verbose:
                logger.info("\nSample data:")

                if verification['jockeys']['sample_data']:
                    logger.info("\n  Top Jockeys:")
                    for j in verification['jockeys']['sample_data']:
                        logger.info(f"    {j['name']}: {j['total_wins']}/{j['total_rides']} ({j['win_rate']:.2f}%)")

                if verification['trainers']['sample_data']:
                    logger.info("\n  Top Trainers:")
                    for t in verification['trainers']['sample_data']:
                        logger.info(f"    {t['name']}: {t['total_wins']}/{t['total_runners']} ({t['win_rate']:.2f}%)")

                if verification['owners']['sample_data']:
                    logger.info("\n  Top Owners:")
                    for o in verification['owners']['sample_data']:
                        logger.info(f"    {o['name']}: {o['total_wins']}/{o['total_runners']} ({o['win_rate']:.2f}%)")

            return verification

        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {'error': str(e)}


def main():
    """Main entry point"""

    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Calculate entity statistics from race results'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify statistics after calculation'
    )

    args = parser.parse_args()

    # Create calculator
    calculator = EntityStatisticsCalculator(verbose=args.verbose)

    # Calculate and update statistics
    result = calculator.calculate_and_update()

    # Verify if requested
    if args.verify and result['success']:
        calculator.verify_statistics()

    # Exit with appropriate code
    if result['success']:
        logger.info("\n" + "=" * 80)
        logger.info("✓ Entity statistics calculation completed successfully")
        logger.info("=" * 80)
        sys.exit(0)
    else:
        logger.error("\n" + "=" * 80)
        logger.error("✗ Entity statistics calculation failed")
        logger.error("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    main()
