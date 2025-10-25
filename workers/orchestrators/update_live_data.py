#!/usr/bin/env python3
"""
Live Data Update Script
Runs every 5-15 minutes during racing hours to update:
- Current day's race information (status, going, weather)
- Runner changes (withdrawals, jockey changes)
- Results as they become official

This script is designed to be idempotent and safe to run multiple times.
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from main import ReferenceDataOrchestrator

logger = get_logger('update_live_data')


class LiveDataUpdater:
    """Updates time-sensitive racing data during racing hours"""

    def __init__(self, dry_run: bool = False):
        """
        Initialize live data updater

        Args:
            dry_run: If True, don't write to database (testing only)
        """
        self.config = get_config()
        self.orchestrator = ReferenceDataOrchestrator()
        self.dry_run = dry_run
        self.stats = {
            'start_time': datetime.utcnow(),
            'races_updated': 0,
            'runners_updated': 0,
            'results_updated': 0,
            'api_calls': 0,
            'errors': 0
        }

        if dry_run:
            logger.warning("DRY RUN MODE - No database writes will occur")

    def run(self, races_only: bool = False, results_only: bool = False) -> Dict:
        """
        Run live data update

        Args:
            races_only: Only update races (skip results)
            results_only: Only update results (skip races)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("LIVE DATA UPDATE - Running")
        logger.info(f"Time: {self.stats['start_time'].isoformat()}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 80)

        try:
            # Update today's races (unless results_only)
            if not results_only:
                self._update_todays_races()

            # Update results (unless races_only)
            if not races_only:
                self._update_todays_results()

            # Calculate execution time
            self.stats['end_time'] = datetime.utcnow()
            self.stats['duration_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()

            # Print summary
            self._print_summary()

            return self.stats

        except Exception as e:
            logger.error(f"Live update failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            self.stats['error'] = str(e)
            return self.stats

    def _update_todays_races(self):
        """Update current day's race information"""
        logger.info("\n" + "=" * 80)
        logger.info("UPDATING TODAY'S RACES")
        logger.info("=" * 80)

        today = datetime.utcnow().date()
        today_str = today.strftime('%Y-%m-%d')

        logger.info(f"Fetching racecards for: {today_str}")

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch racecards for today")
            return

        try:
            # Fetch today's racecards
            custom_configs = {
                'races': {
                    'start_date': today_str,
                    'end_date': today_str,
                    'region_codes': ['gb', 'ire']
                }
            }

            result = self.orchestrator.run_fetch(
                entities=['races'],
                custom_configs=custom_configs
            )

            # Update statistics
            if result.get('races', {}).get('success'):
                inserted = result['races'].get('inserted', 0)
                self.stats['races_updated'] += inserted
                self.stats['api_calls'] += 1
                logger.info(f"Successfully updated {inserted} races")
            else:
                logger.warning("Failed to update races")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error updating races: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _update_todays_results(self):
        """Update today's results (as they become official)"""
        logger.info("\n" + "=" * 80)
        logger.info("UPDATING TODAY'S RESULTS")
        logger.info("=" * 80)

        today = datetime.utcnow().date()
        today_str = today.strftime('%Y-%m-%d')

        logger.info(f"Fetching results for: {today_str}")

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch results for today")
            return

        try:
            # Fetch today's results
            custom_configs = {
                'results': {
                    'start_date': today_str,
                    'end_date': today_str,
                    'region_codes': ['gb', 'ire']
                }
            }

            result = self.orchestrator.run_fetch(
                entities=['results'],
                custom_configs=custom_configs
            )

            # Update statistics
            if result.get('results', {}).get('success'):
                inserted = result['results'].get('inserted', 0)
                self.stats['results_updated'] += inserted
                self.stats['api_calls'] += 1
                logger.info(f"Successfully updated {inserted} results")
            else:
                logger.warning("Failed to update results")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error updating results: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _print_summary(self):
        """Print execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info("LIVE UPDATE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time'].isoformat()}")
        logger.info(f"End time: {self.stats['end_time'].isoformat()}")
        logger.info(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        logger.info("")
        logger.info(f"Races updated: {self.stats['races_updated']}")
        logger.info(f"Results updated: {self.stats['results_updated']}")
        logger.info(f"API calls: {self.stats['api_calls']}")
        logger.info(f"Errors: {self.stats['errors']}")

        if self.dry_run:
            logger.info("")
            logger.info("[DRY RUN] No data was written to database")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Live data update script for racing data'
    )
    parser.add_argument(
        '--races-only',
        action='store_true',
        help='Only update races (skip results)'
    )
    parser.add_argument(
        '--results-only',
        action='store_true',
        help='Only update results (skip races)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - fetch data but do not write to database'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.races_only and args.results_only:
        logger.error("Cannot specify both --races-only and --results-only")
        sys.exit(1)

    try:
        updater = LiveDataUpdater(dry_run=args.dry_run)
        stats = updater.run(
            races_only=args.races_only,
            results_only=args.results_only
        )

        # Exit with appropriate code
        if stats.get('errors', 0) > 0:
            logger.warning("Live update completed with errors")
            sys.exit(1)
        else:
            logger.info("Live update completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
