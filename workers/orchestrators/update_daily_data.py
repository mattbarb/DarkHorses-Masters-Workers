#!/usr/bin/env python3
"""
Daily Data Update Script
Runs once per day (06:00 UTC) to update:
- Tomorrow's racecards (and optionally day after)
- Yesterday's results (reconciliation)
- Entity extraction from new runners

This script is designed to be idempotent and safe to run multiple times.
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from main import ReferenceDataOrchestrator

logger = get_logger('update_daily_data')


class DailyDataUpdater:
    """Updates racecards and results on a daily basis"""

    def __init__(self, dry_run: bool = False):
        """
        Initialize daily data updater

        Args:
            dry_run: If True, don't write to database (testing only)
        """
        self.config = get_config()
        self.orchestrator = ReferenceDataOrchestrator()
        self.dry_run = dry_run
        self.stats = {
            'start_time': datetime.utcnow(),
            'racecards_fetched': 0,
            'races_inserted': 0,
            'runners_inserted': 0,
            'results_fetched': 0,
            'entities_extracted': 0,
            'api_calls': 0,
            'errors': 0
        }

        if dry_run:
            logger.warning("DRY RUN MODE - No database writes will occur")

    def run(
        self,
        racecards_only: bool = False,
        results_only: bool = False,
        days_ahead: int = 2,
        days_back: int = 1,
        weekly: bool = False
    ) -> Dict:
        """
        Run daily data update

        Args:
            racecards_only: Only update racecards (skip results)
            results_only: Only update results (skip racecards)
            days_ahead: Number of days ahead to fetch racecards (default: 2)
            days_back: Number of days back to fetch results (default: 1)
            weekly: Weekly reconciliation mode (fetch last 7 days)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("DAILY DATA UPDATE - Running")
        logger.info(f"Time: {self.stats['start_time'].isoformat()}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info(f"Weekly mode: {weekly}")
        logger.info("=" * 80)

        try:
            # Weekly reconciliation overrides other settings
            if weekly:
                days_back = 7
                logger.info("WEEKLY RECONCILIATION MODE - Fetching last 7 days")

            # Update racecards (unless results_only)
            if not results_only:
                self._update_racecards(days_ahead=days_ahead)

            # Update results (unless racecards_only)
            if not racecards_only:
                self._update_results(days_back=days_back)

            # Calculate execution time
            self.stats['end_time'] = datetime.utcnow()
            self.stats['duration_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()

            # Print summary
            self._print_summary()

            return self.stats

        except Exception as e:
            logger.error(f"Daily update failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            self.stats['error'] = str(e)
            return self.stats

    def _update_racecards(self, days_ahead: int = 2):
        """
        Update future racecards

        Args:
            days_ahead: Number of days ahead to fetch
        """
        logger.info("\n" + "=" * 80)
        logger.info("UPDATING FUTURE RACECARDS")
        logger.info("=" * 80)

        # Calculate date range (tomorrow to N days ahead)
        today = datetime.utcnow().date()
        start_date = today + timedelta(days=1)  # Tomorrow
        end_date = today + timedelta(days=days_ahead)

        logger.info(f"Fetching racecards from {start_date} to {end_date}")
        logger.info(f"Total days: {(end_date - start_date).days + 1}")

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch racecards for this date range")
            return

        try:
            # Fetch racecards
            custom_configs = {
                'races': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'region_codes': ['gb', 'ire']
                }
            }

            result = self.orchestrator.run_fetch(
                entities=['races'],
                custom_configs=custom_configs
            )

            # Update statistics
            if result.get('races', {}).get('success'):
                self.stats['racecards_fetched'] += result['races'].get('fetched', 0)
                self.stats['races_inserted'] += result['races'].get('races_inserted', 0)
                self.stats['runners_inserted'] += result['races'].get('runners_inserted', 0)
                self.stats['api_calls'] += (end_date - start_date).days + 1
                logger.info(f"Successfully fetched {self.stats['racecards_fetched']} racecards")
                logger.info(f"  Races: {self.stats['races_inserted']}")
                logger.info(f"  Runners: {self.stats['runners_inserted']}")
            else:
                logger.warning("Failed to update racecards")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error updating racecards: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _update_results(self, days_back: int = 1):
        """
        Update historical results

        Args:
            days_back: Number of days back to fetch
        """
        logger.info("\n" + "=" * 80)
        logger.info("UPDATING HISTORICAL RESULTS")
        logger.info("=" * 80)

        # Calculate date range (yesterday to N days back)
        today = datetime.utcnow().date()
        end_date = today - timedelta(days=1)  # Yesterday
        start_date = end_date - timedelta(days=days_back - 1)

        logger.info(f"Fetching results from {start_date} to {end_date}")
        logger.info(f"Total days: {(end_date - start_date).days + 1}")

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch results for this date range")
            return

        try:
            # Fetch results
            custom_configs = {
                'results': {
                    'start_date': start_date.strftime('%Y-%m-%d'),
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'region_codes': ['gb', 'ire']
                }
            }

            result = self.orchestrator.run_fetch(
                entities=['results'],
                custom_configs=custom_configs
            )

            # Update statistics
            if result.get('results', {}).get('success'):
                self.stats['results_fetched'] += result['results'].get('fetched', 0)
                self.stats['api_calls'] += (end_date - start_date).days + 1
                logger.info(f"Successfully fetched {self.stats['results_fetched']} results")
            else:
                logger.warning("Failed to update results")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error updating results: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _print_summary(self):
        """Print execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info("DAILY UPDATE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time'].isoformat()}")
        logger.info(f"End time: {self.stats['end_time'].isoformat()}")
        logger.info(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        logger.info("")
        logger.info("Racecards:")
        logger.info(f"  Fetched: {self.stats['racecards_fetched']}")
        logger.info(f"  Races inserted: {self.stats['races_inserted']}")
        logger.info(f"  Runners inserted: {self.stats['runners_inserted']}")
        logger.info("")
        logger.info("Results:")
        logger.info(f"  Fetched: {self.stats['results_fetched']}")
        logger.info("")
        logger.info(f"API calls: {self.stats['api_calls']}")
        logger.info(f"Errors: {self.stats['errors']}")

        if self.dry_run:
            logger.info("")
            logger.info("[DRY RUN] No data was written to database")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Daily data update script for racing data'
    )
    parser.add_argument(
        '--racecards-only',
        action='store_true',
        help='Only update racecards (skip results)'
    )
    parser.add_argument(
        '--results-only',
        action='store_true',
        help='Only update results (skip racecards)'
    )
    parser.add_argument(
        '--days-ahead',
        type=int,
        default=2,
        help='Number of days ahead to fetch racecards (default: 2)'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=1,
        help='Number of days back to fetch results (default: 1)'
    )
    parser.add_argument(
        '--weekly',
        action='store_true',
        help='Weekly reconciliation mode (fetch last 7 days of results)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - fetch data but do not write to database'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.racecards_only and args.results_only:
        logger.error("Cannot specify both --racecards-only and --results-only")
        sys.exit(1)

    try:
        updater = DailyDataUpdater(dry_run=args.dry_run)
        stats = updater.run(
            racecards_only=args.racecards_only,
            results_only=args.results_only,
            days_ahead=args.days_ahead,
            days_back=args.days_back,
            weekly=args.weekly
        )

        # Exit with appropriate code
        if stats.get('errors', 0) > 0:
            logger.warning("Daily update completed with errors")
            sys.exit(1)
        else:
            logger.info("Daily update completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
