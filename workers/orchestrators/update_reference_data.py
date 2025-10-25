#!/usr/bin/env python3
"""
Reference Data Update Script
Runs periodically (weekly/monthly) to update:
- Courses (monthly - low volatility)
- Bookmakers (monthly - low volatility)

This script is designed to be idempotent and safe to run multiple times.
"""

import sys
import argparse
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from main import ReferenceDataOrchestrator

logger = get_logger('update_reference_data')


class ReferenceDataUpdater:
    """Updates low-volatility reference data"""

    def __init__(self, dry_run: bool = False):
        """
        Initialize reference data updater

        Args:
            dry_run: If True, don't write to database (testing only)
        """
        self.config = get_config()
        self.orchestrator = ReferenceDataOrchestrator()
        self.dry_run = dry_run
        self.stats = {
            'start_time': datetime.utcnow(),
            'courses_updated': 0,
            'bookmakers_updated': 0,
            'api_calls': 0,
            'errors': 0
        }

        if dry_run:
            logger.warning("DRY RUN MODE - No database writes will occur")

    def run(
        self,
        courses_only: bool = False,
        bookmakers_only: bool = False
    ) -> Dict:
        """
        Run reference data update

        Args:
            courses_only: Only update courses (skip bookmakers)
            bookmakers_only: Only update bookmakers (skip courses)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("REFERENCE DATA UPDATE - Running")
        logger.info(f"Time: {self.stats['start_time'].isoformat()}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 80)

        # Determine which entities to update
        entities_to_update = []

        if courses_only:
            entities_to_update = ['courses']
        elif bookmakers_only:
            entities_to_update = ['bookmakers']
        else:
            # Update both by default
            entities_to_update = ['courses', 'bookmakers']

        logger.info(f"Updating entities: {', '.join(entities_to_update)}")

        try:
            # Update courses
            if 'courses' in entities_to_update:
                self._update_courses()

            # Update bookmakers
            if 'bookmakers' in entities_to_update:
                self._update_bookmakers()

            # Calculate execution time
            self.stats['end_time'] = datetime.utcnow()
            self.stats['duration_seconds'] = (
                self.stats['end_time'] - self.stats['start_time']
            ).total_seconds()

            # Print summary
            self._print_summary()

            return self.stats

        except Exception as e:
            logger.error(f"Reference data update failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            self.stats['error'] = str(e)
            return self.stats

    def _update_courses(self):
        """Update courses reference data"""
        logger.info("\n" + "=" * 80)
        logger.info("UPDATING COURSES")
        logger.info("=" * 80)

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch courses data")
            return

        try:
            # Fetch courses (filtered to GB and Ireland)
            custom_configs = {
                'courses': {
                    'region_codes': ['gb', 'ire']
                }
            }

            result = self.orchestrator.run_fetch(
                entities=['courses'],
                custom_configs=custom_configs
            )

            # Update statistics
            if result.get('courses', {}).get('success'):
                self.stats['courses_updated'] = result['courses'].get('inserted', 0)
                self.stats['api_calls'] += 1
                logger.info(f"Successfully updated {self.stats['courses_updated']} courses")
            else:
                logger.warning("Failed to update courses")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error updating courses: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _update_bookmakers(self):
        """Update bookmakers reference data"""
        logger.info("\n" + "=" * 80)
        logger.info("UPDATING BOOKMAKERS")
        logger.info("=" * 80)

        if self.dry_run:
            logger.info("[DRY RUN] Would fetch bookmakers data")
            return

        try:
            # Fetch bookmakers
            result = self.orchestrator.run_fetch(
                entities=['bookmakers']
            )

            # Update statistics
            if result.get('bookmakers', {}).get('success'):
                self.stats['bookmakers_updated'] = result['bookmakers'].get('inserted', 0)
                self.stats['api_calls'] += 1
                logger.info(f"Successfully updated {self.stats['bookmakers_updated']} bookmakers")
            else:
                logger.warning("Failed to update bookmakers")
                self.stats['errors'] += 1

        except Exception as e:
            logger.error(f"Error updating bookmakers: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _print_summary(self):
        """Print execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info("REFERENCE DATA UPDATE SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time'].isoformat()}")
        logger.info(f"End time: {self.stats['end_time'].isoformat()}")
        logger.info(f"Duration: {self.stats['duration_seconds']:.2f} seconds")
        logger.info("")
        logger.info(f"Courses updated: {self.stats['courses_updated']}")
        logger.info(f"Bookmakers updated: {self.stats['bookmakers_updated']}")
        logger.info(f"API calls: {self.stats['api_calls']}")
        logger.info(f"Errors: {self.stats['errors']}")

        if self.dry_run:
            logger.info("")
            logger.info("[DRY RUN] No data was written to database")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Reference data update script for racing data'
    )
    parser.add_argument(
        '--courses-only',
        action='store_true',
        help='Only update courses (skip bookmakers)'
    )
    parser.add_argument(
        '--bookmakers-only',
        action='store_true',
        help='Only update bookmakers (skip courses)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test mode - fetch data but do not write to database'
    )

    args = parser.parse_args()

    # Validate arguments
    if args.courses_only and args.bookmakers_only:
        logger.error("Cannot specify both --courses-only and --bookmakers-only")
        sys.exit(1)

    try:
        updater = ReferenceDataUpdater(dry_run=args.dry_run)
        stats = updater.run(
            courses_only=args.courses_only,
            bookmakers_only=args.bookmakers_only
        )

        # Exit with appropriate code
        if stats.get('errors', 0) > 0:
            logger.warning("Reference data update completed with errors")
            sys.exit(1)
        else:
            logger.info("Reference data update completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
