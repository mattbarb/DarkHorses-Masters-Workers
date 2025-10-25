#!/usr/bin/env python3
"""
Production Orchestrator for Racing API Reference Data Fetching
Coordinates fetching of all reference data in the correct order

This is the production-ready version optimized for deployment.
Use command-line arguments to control which entities to fetch.
"""

import sys
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional

from config.config import get_config
from utils.logger import get_logger

# New consolidated fetchers (not yet in production - kept for future use)
# from fetchers.masters_fetcher import MastersFetcher
# from fetchers.events_fetcher import EventsFetcher

# Legacy fetchers (currently in production)
from fetchers.courses_fetcher import CoursesFetcher
from fetchers.bookmakers_fetcher import BookmakersFetcher
# Note: jockeys, trainers, owners are now extracted automatically via EntityExtractor during race/result fetching
from fetchers.horses_fetcher import HorsesFetcher
from fetchers.races_fetcher import RacesFetcher
from fetchers.results_fetcher import ResultsFetcher
# from fetchers.statistics_fetcher import StatisticsFetcher  # Not yet committed to repo

logger = get_logger('main')


class ReferenceDataOrchestrator:
    """Production orchestrator for racing reference data fetching"""

    # Default production configurations for each entity
    PRODUCTION_CONFIGS = {
        # NEW: Consolidated fetchers
        'masters': {
            'entity_type': 'reference',  # or 'people', 'all'
            'region_codes': ['gb', 'ire'],
            'description': 'All master/reference data (bookmakers, courses, regions)'
        },
        'events': {
            'event_type': 'racecards',  # or 'results', 'both'
            'days_back': 1,
            'region_codes': ['gb', 'ire'],
            'description': 'Event data (races, runners)'
        },

        # LEGACY: Individual fetchers (deprecated)
        'courses': {
            'region_codes': ['gb', 'ire'],  # UK & Ireland courses only
            'description': 'UK and Ireland racing courses'
        },
        'bookmakers': {
            'description': 'Static UK/Ireland bookmakers list'
        },
        # Note: jockeys, trainers, owners automatically extracted during races/results fetching
        'horses': {
            'limit_per_page': 500,
            'filter_uk_ireland': True,
            'description': 'UK and Ireland horses (filtered post-fetch)'
        },
        'races': {
            'days_back': 30,
            'region_codes': ['gb', 'ire'],
            'description': 'Last 30 days UK/Ireland races with runners'
        },
        'results': {
            'days_back': 365,
            'region_codes': ['gb', 'ire'],
            'description': 'Last 12 months UK/Ireland race results'
        },
        'statistics': {
            'recent_only': True,
            'entities': ['jockeys', 'trainers', 'owners'],
            'description': 'Daily statistics update (incremental)'
        }
    }

    # Fetcher registry
    FETCHERS = {
        # NEW: Consolidated fetchers (not yet in production)
        # 'masters': MastersFetcher,
        # 'events': EventsFetcher,

        # LEGACY: Individual fetchers (currently in production)
        'courses': CoursesFetcher,
        'bookmakers': BookmakersFetcher,
        # jockeys, trainers, owners removed - now extracted automatically via EntityExtractor
        'horses': HorsesFetcher,
        'races': RacesFetcher,
        'results': ResultsFetcher,
        # 'statistics': StatisticsFetcher  # Not yet committed to repo
    }

    def __init__(self):
        """Initialize orchestrator"""
        self.config = get_config()
        self.results = {}
        self.start_time = None
        self.end_time = None

    def run_fetch(self, entities: Optional[List[str]] = None, custom_configs: Optional[Dict] = None) -> Dict:
        """
        Run reference data fetch for specified entities

        Args:
            entities: List of entity names to fetch (None = all entities)
            custom_configs: Optional custom configuration overrides

        Returns:
            Complete results dictionary
        """
        self.start_time = datetime.utcnow()

        # Determine which entities to fetch
        if entities is None:
            entities = list(self.FETCHERS.keys())

        logger.info("=" * 80)
        logger.info("RACING API REFERENCE DATA FETCHER - PRODUCTION")
        logger.info("REGIONAL FILTERING: UK AND IRELAND ONLY")
        logger.info(f"Started at: {self.start_time.isoformat()}")
        logger.info(f"Entities to fetch: {', '.join(entities)}")
        logger.info("=" * 80)

        # Execute fetchers in order
        for entity_name in entities:
            if entity_name not in self.FETCHERS:
                logger.warning(f"Unknown entity: {entity_name}, skipping")
                continue

            logger.info("\n" + "=" * 80)
            logger.info(f"FETCHING: {entity_name.upper()}")
            logger.info(f"Description: {self.PRODUCTION_CONFIGS[entity_name].get('description', 'N/A')}")
            logger.info("=" * 80)

            try:
                # Get configuration
                config = self.PRODUCTION_CONFIGS[entity_name].copy()
                config.pop('description', None)  # Remove description from config

                # Apply custom overrides
                if custom_configs and entity_name in custom_configs:
                    config.update(custom_configs[entity_name])

                # Initialize fetcher and run
                fetcher = self.FETCHERS[entity_name]()
                result = fetcher.fetch_and_store(**config)

                self.results[entity_name] = {
                    'success': result.get('success', False),
                    'fetched': result.get('fetched', 0),
                    'inserted': result.get('inserted', 0),
                    'error': result.get('error'),
                    'timestamp': datetime.utcnow().isoformat()
                }

                if result.get('success'):
                    logger.info(f"SUCCESS - {entity_name.upper()}")
                    logger.info(f"   Fetched: {result.get('fetched', 0)}")
                    logger.info(f"   Inserted: {result.get('inserted', 0)}")
                else:
                    logger.error(f"FAILED - {entity_name.upper()}")
                    logger.error(f"   Error: {result.get('error', 'Unknown')}")

            except Exception as e:
                logger.error(f"EXCEPTION - {entity_name.upper()}: {e}", exc_info=True)
                self.results[entity_name] = {
                    'success': False,
                    'error': str(e),
                    'timestamp': datetime.utcnow().isoformat()
                }

        self.end_time = datetime.utcnow()
        duration = (self.end_time - self.start_time).total_seconds()

        # Generate summary
        self._print_summary(duration)

        # Save results
        self._save_results()

        return self.results

    def _print_summary(self, duration: float):
        """Print execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info("EXECUTION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
        logger.info(f"Start: {self.start_time.isoformat()}")
        logger.info(f"End: {self.end_time.isoformat()}")
        logger.info("\nResults by Entity:")

        total_fetched = 0
        total_inserted = 0
        success_count = 0
        fail_count = 0

        for entity, result in self.results.items():
            status = "SUCCESS" if result.get('success') else "FAILED"
            fetched = result.get('fetched', 0)
            inserted = result.get('inserted', 0)

            logger.info(f"  [{status}] {entity.ljust(15)} - Fetched: {fetched:6}, Inserted: {inserted:6}")

            total_fetched += fetched
            total_inserted += inserted
            if result.get('success'):
                success_count += 1
            else:
                fail_count += 1
                if result.get('error'):
                    logger.info(f"           Error: {result['error']}")

        logger.info(f"\nTotals:")
        logger.info(f"  Total Fetched: {total_fetched}")
        logger.info(f"  Total Inserted: {total_inserted}")
        logger.info(f"  Successful: {success_count}/{len(self.results)}")
        logger.info(f"  Failed: {fail_count}/{len(self.results)}")
        logger.info("=" * 80)

    def _save_results(self):
        """Save results to JSON file"""
        results_file = self.config.paths.logs_dir / f"fetch_results_{self.start_time.strftime('%Y%m%d_%H%M%S')}.json"

        results_summary = {
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': (self.end_time - self.start_time).total_seconds(),
            'results': self.results
        }

        with open(results_file, 'w') as f:
            json.dump(results_summary, f, indent=2)

        logger.info(f"\nResults saved to: {results_file}")


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Racing API Reference Data Fetcher - Production',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # Fetch all entities (full sync)
  python main.py --all

  # Fetch specific entities
  python main.py --entities courses bookmakers

  # Daily update (races and results)
  python main.py --daily

  # Weekly update (people and horses)
  python main.py --weekly

  # Test mode (limited data)
  python main.py --test --entities horses
        '''
    )

    parser.add_argument(
        '--all',
        action='store_true',
        help='Fetch all entities (complete sync)'
    )

    parser.add_argument(
        '--daily',
        action='store_true',
        help='Daily update: races and results'
    )

    parser.add_argument(
        '--weekly',
        action='store_true',
        help='Weekly update: horses (jockeys/trainers/owners auto-extracted from races)'
    )

    parser.add_argument(
        '--monthly',
        action='store_true',
        help='Monthly update: courses and bookmakers'
    )

    parser.add_argument(
        '--entities',
        nargs='+',
        choices=list(ReferenceDataOrchestrator.FETCHERS.keys()),
        help='Specific entities to fetch'
    )

    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode with limited data (for testing)'
    )

    return parser.parse_args()


def main():
    """Main execution function"""
    args = parse_args()

    # Determine which entities to fetch
    entities = None
    custom_configs = None

    if args.all:
        entities = None  # Fetch all
    elif args.daily:
        entities = ['races', 'results']
    elif args.weekly:
        entities = ['horses']  # jockeys, trainers, owners auto-extracted from daily races
    elif args.monthly:
        entities = ['courses', 'bookmakers']
    elif args.entities:
        entities = args.entities
    else:
        # Default: fetch all
        entities = None

    # Test mode configurations
    if args.test:
        logger.warning("TEST MODE: Limiting data fetch for testing")
        custom_configs = {
            'horses': {'max_pages': 5},
            'races': {'days_back': 7},
            'results': {'days_back': 30}
        }

    # Initialize and run orchestrator
    try:
        orchestrator = ReferenceDataOrchestrator()
        results = orchestrator.run_fetch(entities=entities, custom_configs=custom_configs)

        # Exit with appropriate code
        all_success = all(r.get('success', False) for r in results.values())
        sys.exit(0 if all_success else 1)

    except Exception as e:
        logger.error(f"FATAL ERROR: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
