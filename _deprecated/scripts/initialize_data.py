#!/usr/bin/env python3
"""
Initial Data Collection Script
Backfills all reference data and historical races/results from 2015-01-01 to present
Run this once after deployment to populate the database

Usage:
    python3 initialize_data.py                    # Full initialization
    python3 initialize_data.py --from 2020-01-01  # Start from specific date
    python3 initialize_data.py --skip-reference   # Skip reference data, only races/results
    python3 initialize_data.py --test             # Test mode (limited data)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict
import time

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from main import ReferenceDataOrchestrator

logger = get_logger('initialize_data')


class InitializationOrchestrator:
    """Orchestrator for initial data backfill"""

    def __init__(self, start_date: str = '2015-01-01', skip_reference: bool = False, test_mode: bool = False, premium_results: bool = True):
        """
        Initialize orchestrator

        Args:
            start_date: Start date for historical data (YYYY-MM-DD) - for results
            skip_reference: Skip reference data fetch (courses, bookmakers, people, horses)
            test_mode: Test mode with limited data
            premium_results: Premium add-on enabled (30+ years of results), default True
        """
        self.config = get_config()
        self.orchestrator = ReferenceDataOrchestrator()

        # Results start date (can go back to 2015 with premium)
        self.results_start_date = datetime.strptime(start_date, '%Y-%m-%d').date()

        # Racecards only available from 2023-01-23 (API limitation)
        self.racecards_start_date = datetime.strptime('2023-01-23', '%Y-%m-%d').date()

        self.end_date = datetime.utcnow().date()
        self.skip_reference = skip_reference
        self.test_mode = test_mode
        self.premium_results = premium_results
        self.results = {}

        logger.info("=" * 80)
        logger.info("DARKHORSES MASTERS WORKER - INITIALIZATION")
        logger.info("=" * 80)
        logger.info(f"Results start date: {self.results_start_date} (Premium: {premium_results})")
        logger.info(f"Racecards start date: {self.racecards_start_date} (API limitation)")
        logger.info(f"End date: {self.end_date}")
        logger.info(f"Results period: {(self.end_date - self.results_start_date).days} days")
        logger.info(f"Racecards period: {(self.end_date - self.racecards_start_date).days} days")
        logger.info(f"Skip reference data: {skip_reference}")
        logger.info(f"Test mode: {test_mode}")
        logger.info("=" * 80)

    def run(self) -> Dict:
        """Run full initialization"""
        overall_start = time.time()

        # Phase 1: Reference Data
        if not self.skip_reference:
            logger.info("\n" + "▶" * 80)
            logger.info("PHASE 1: REFERENCE DATA COLLECTION")
            logger.info("▶" * 80 + "\n")

            self._fetch_reference_data()
        else:
            logger.info("\n⏭️  Skipping reference data (--skip-reference flag)")

        # Phase 2: Historical Races & Results
        logger.info("\n" + "▶" * 80)
        logger.info("PHASE 2: HISTORICAL RACES & RESULTS BACKFILL")
        logger.info("▶" * 80 + "\n")

        self._fetch_historical_data()

        # Summary
        overall_duration = time.time() - overall_start
        self._print_summary(overall_duration)

        return self.results

    def _fetch_reference_data(self):
        """Fetch all reference data (courses, bookmakers, people, horses)"""

        # Step 1: Courses & Bookmakers
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: COURSES & BOOKMAKERS (Monthly data)")
        logger.info("=" * 80)

        reference_entities = ['courses', 'bookmakers']

        if self.test_mode:
            logger.info("🧪 TEST MODE: Limiting to courses only")
            reference_entities = ['courses']

        result = self.orchestrator.run_fetch(entities=reference_entities)
        self.results['reference_static'] = result

        # Step 2: People & Horses - SKIPPED
        # These entities (jockeys, trainers, owners, horses) are now populated automatically
        # from race/runner data during historical data fetch, not from separate API endpoints
        logger.info("\n" + "=" * 80)
        logger.info("STEP 2: JOCKEYS, TRAINERS, OWNERS & HORSES")
        logger.info("=" * 80)
        logger.info("⏭️  Skipping separate entity fetch")
        logger.info("ℹ️   These entities will be populated from race data automatically")

    def _fetch_historical_data(self):
        """Fetch historical races and results from start_date to end_date"""

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2A: HISTORICAL RESULTS (2015-2025)")
        logger.info("=" * 80)
        logger.info("ℹ️  Premium add-on enabled - fetching 30+ years of results")

        # Results backfill (can go back to 2015 with premium)
        results_start = self.results_start_date
        if self.test_mode:
            logger.info("🧪 TEST MODE: Limiting results to last 7 days only")
            results_start = self.end_date - timedelta(days=7)

        total_results_days = (self.end_date - results_start).days
        logger.info(f"Results backfill: {total_results_days} days")
        logger.info(f"Results date range: {results_start} to {self.end_date}")

        self._fetch_results_historical(results_start, self.end_date)

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2B: HISTORICAL RACECARDS (2023-2025)")
        logger.info("=" * 80)
        logger.info("ℹ️  Racecards available from 2023-01-23 onwards (API limitation)")

        # Racecards backfill (only from 2023-01-23)
        racecards_start = self.racecards_start_date
        if self.test_mode:
            logger.info("🧪 TEST MODE: Limiting racecards to last 7 days only")
            racecards_start = self.end_date - timedelta(days=7)

        total_racecards_days = (self.end_date - racecards_start).days
        logger.info(f"Racecards backfill: {total_racecards_days} days")
        logger.info(f"Racecards date range: {racecards_start} to {self.end_date}")

        self._fetch_racecards_historical(racecards_start, self.end_date)

    def _fetch_results_historical(self, start_date, end_date):
        """Fetch historical results data"""

        total_days = (end_date - start_date).days
        logger.info(f"\nBackfilling {total_days} days of results data")

        # Strategy: Fetch in 90-day chunks to manage API load
        CHUNK_SIZE = 90  # days per batch

        if self.test_mode:
            CHUNK_SIZE = 7  # smaller chunks for test mode

        chunks = self._calculate_date_chunks(start_date, end_date, CHUNK_SIZE)

        logger.info(f"\nProcessing in {len(chunks)} chunks of ~{CHUNK_SIZE} days each")
        logger.info("=" * 80)

        chunk_results = []

        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"CHUNK {i}/{len(chunks)}: {chunk_start} to {chunk_end}")
            logger.info(f"{'=' * 80}")

            chunk_result = self._fetch_results_only(chunk_start, chunk_end)
            chunk_results.append({
                'chunk': i,
                'start': str(chunk_start),
                'end': str(chunk_end),
                'results': chunk_result.get('results', {})
            })

            # Progress update
            days_processed = sum((datetime.strptime(r['end'], '%Y-%m-%d').date() -
                                 datetime.strptime(r['start'], '%Y-%m-%d').date()).days + 1
                                for r in chunk_results)
            progress = (days_processed / total_days) * 100

            logger.info(f"\n📊 Progress: {days_processed}/{total_days} days ({progress:.1f}%)")
            logger.info(f"⏱️  Chunks completed: {i}/{len(chunks)}")

            # Brief pause between chunks to avoid overwhelming API
            if i < len(chunks):
                logger.info("⏸️  Pausing 5 seconds before next chunk...")
                time.sleep(5)

        self.results['historical_results'] = {
            'total_chunks': len(chunks),
            'chunks': chunk_results,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_days': total_days
        }

    def _fetch_racecards_historical(self, start_date, end_date):
        """Fetch historical racecards data"""

        total_days = (end_date - start_date).days
        logger.info(f"\nBackfilling {total_days} days of racecards data")

        # Strategy: Fetch in 90-day chunks to manage API load
        CHUNK_SIZE = 90  # days per batch

        if self.test_mode:
            CHUNK_SIZE = 7  # smaller chunks for test mode

        chunks = self._calculate_date_chunks(start_date, end_date, CHUNK_SIZE)

        logger.info(f"\nProcessing in {len(chunks)} chunks of ~{CHUNK_SIZE} days each")
        logger.info("=" * 80)

        chunk_results = []

        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"CHUNK {i}/{len(chunks)}: {chunk_start} to {chunk_end}")
            logger.info(f"{'=' * 80}")

            chunk_result = self._fetch_racecards_only(chunk_start, chunk_end)
            chunk_results.append({
                'chunk': i,
                'start': str(chunk_start),
                'end': str(chunk_end),
                'races': chunk_result.get('races', {})
            })

            # Progress update
            days_processed = sum((datetime.strptime(r['end'], '%Y-%m-%d').date() -
                                 datetime.strptime(r['start'], '%Y-%m-%d').date()).days + 1
                                for r in chunk_results)
            progress = (days_processed / total_days) * 100

            logger.info(f"\n📊 Progress: {days_processed}/{total_days} days ({progress:.1f}%)")
            logger.info(f"⏱️  Chunks completed: {i}/{len(chunks)}")

            # Brief pause between chunks to avoid overwhelming API
            if i < len(chunks):
                logger.info("⏸️  Pausing 5 seconds before next chunk...")
                time.sleep(5)

        self.results['historical_racecards'] = {
            'total_chunks': len(chunks),
            'chunks': chunk_results,
            'start_date': str(start_date),
            'end_date': str(end_date),
            'total_days': total_days
        }

    def _calculate_date_chunks(self, start_date, end_date, chunk_size):
        """Calculate date range chunks"""
        chunks = []
        current_start = start_date

        while current_start <= end_date:
            current_end = min(current_start + timedelta(days=chunk_size - 1), end_date)
            chunks.append((current_start, current_end))
            current_start = current_end + timedelta(days=1)

        return chunks

    def _fetch_results_only(self, start_date, end_date):
        """Fetch only results for a specific date range"""

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

        return result

    def _fetch_racecards_only(self, start_date, end_date):
        """Fetch only racecards for a specific date range"""

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

        return result

    def _print_summary(self, duration: float):
        """Print initialization summary"""
        logger.info("\n" + "=" * 80)
        logger.info("INITIALIZATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")

        # Reference data summary
        if not self.skip_reference:
            logger.info("\n📋 Reference Data:")

            if 'reference_static' in self.results:
                for entity, result in self.results['reference_static'].items():
                    status = "✅" if result.get('success') else "❌"
                    inserted = result.get('inserted', 0)
                    logger.info(f"   {status} {entity.capitalize()}: {inserted} records")

            if 'reference_people_horses' in self.results:
                for entity, result in self.results['reference_people_horses'].items():
                    status = "✅" if result.get('success') else "❌"
                    inserted = result.get('inserted', 0)
                    logger.info(f"   {status} {entity.capitalize()}: {inserted} records")

        # Historical data summary
        if 'historical_data' in self.results:
            hist = self.results['historical_data']
            logger.info(f"\n📊 Historical Data:")
            logger.info(f"   Date range: {hist['start_date']} to {hist['end_date']}")
            logger.info(f"   Total days: {hist['total_days']}")
            logger.info(f"   Chunks processed: {hist['total_chunks']}")

            # Aggregate totals
            total_races_inserted = sum(
                chunk['races'].get('inserted', 0)
                for chunk in hist['chunks']
            )
            total_results_inserted = sum(
                chunk['results'].get('inserted', 0)
                for chunk in hist['chunks']
            )

            logger.info(f"\n   Races: {total_races_inserted:,} records")
            logger.info(f"   Results: {total_results_inserted:,} records")

        logger.info("\n" + "=" * 80)
        logger.info("🎉 Initialization complete! Database is ready.")
        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Initialize DarkHorses Masters Worker database with historical data'
    )
    parser.add_argument(
        '--from',
        dest='start_date',
        default='2015-01-01',
        help='Start date for results data (YYYY-MM-DD). Default: 2015-01-01 (with premium add-on)'
    )
    parser.add_argument(
        '--premium',
        action='store_true',
        default=True,
        help='Premium add-on enabled (30+ years of results). Default: True'
    )
    parser.add_argument(
        '--skip-reference',
        action='store_true',
        help='Skip reference data fetch (courses, bookmakers, people, horses)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: only fetch limited data for testing'
    )

    args = parser.parse_args()

    try:
        orchestrator = InitializationOrchestrator(
            start_date=args.start_date,
            skip_reference=args.skip_reference,
            test_mode=args.test,
            premium_results=args.premium
        )

        result = orchestrator.run()

        # Exit code based on success
        if result:
            logger.info("✅ Initialization succeeded")
            sys.exit(0)
        else:
            logger.error("❌ Initialization had issues")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Fatal error during initialization: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
