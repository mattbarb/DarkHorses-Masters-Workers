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

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config.config import get_config
from utils.logger import get_logger
from main import ReferenceDataOrchestrator

logger = get_logger('initialize_data')


class InitializationOrchestrator:
    """Orchestrator for initial data backfill"""

    def __init__(self, start_date: str = '2015-01-01', skip_reference: bool = False, test_mode: bool = False):
        """
        Initialize orchestrator

        Args:
            start_date: Start date for historical data (YYYY-MM-DD)
            skip_reference: Skip reference data fetch (courses, bookmakers, people, horses)
            test_mode: Test mode with limited data
        """
        self.config = get_config()
        self.orchestrator = ReferenceDataOrchestrator()
        self.start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        self.end_date = datetime.utcnow().date()
        self.skip_reference = skip_reference
        self.test_mode = test_mode
        self.results = {}

        logger.info("=" * 80)
        logger.info("DARKHORSES MASTERS WORKER - INITIALIZATION")
        logger.info("=" * 80)
        logger.info(f"Start date: {self.start_date}")
        logger.info(f"End date: {self.end_date}")
        logger.info(f"Total days: {(self.end_date - self.start_date).days}")
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

        # Step 2: People & Horses
        if not self.test_mode:
            logger.info("\n" + "=" * 80)
            logger.info("STEP 2: JOCKEYS, TRAINERS, OWNERS & HORSES (Weekly data)")
            logger.info("=" * 80)

            people_entities = ['jockeys', 'trainers', 'owners', 'horses']
            result = self.orchestrator.run_fetch(entities=people_entities)
            self.results['reference_people_horses'] = result
        else:
            logger.info("\n⏭️  TEST MODE: Skipping people & horses")

    def _fetch_historical_data(self):
        """Fetch historical races and results from start_date to end_date"""

        # Calculate date ranges
        total_days = (self.end_date - self.start_date).days

        if self.test_mode:
            logger.info("🧪 TEST MODE: Limiting to last 7 days only")
            self.start_date = self.end_date - timedelta(days=7)
            total_days = 7

        logger.info(f"Backfilling {total_days} days of data")
        logger.info(f"Date range: {self.start_date} to {self.end_date}")

        # Strategy: Fetch in 90-day chunks to manage API load
        CHUNK_SIZE = 90  # days per batch

        if self.test_mode:
            CHUNK_SIZE = 7  # smaller chunks for test mode

        chunks = self._calculate_date_chunks(self.start_date, self.end_date, CHUNK_SIZE)

        logger.info(f"\nProcessing in {len(chunks)} chunks of ~{CHUNK_SIZE} days each")
        logger.info("=" * 80)

        chunk_results = []

        for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
            logger.info(f"\n{'=' * 80}")
            logger.info(f"CHUNK {i}/{len(chunks)}: {chunk_start} to {chunk_end}")
            logger.info(f"{'=' * 80}")

            chunk_result = self._fetch_date_range(chunk_start, chunk_end)
            chunk_results.append({
                'chunk': i,
                'start': str(chunk_start),
                'end': str(chunk_end),
                'races': chunk_result.get('races', {}),
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

        self.results['historical_data'] = {
            'total_chunks': len(chunks),
            'chunks': chunk_results,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
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

    def _fetch_date_range(self, start_date, end_date):
        """Fetch races and results for a specific date range"""

        custom_configs = {
            'races': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'region_codes': ['gb', 'ire']
            },
            'results': {
                'start_date': start_date.strftime('%Y-%m-%d'),
                'end_date': end_date.strftime('%Y-%m-%d'),
                'region_codes': ['gb', 'ire']
            }
        }

        result = self.orchestrator.run_fetch(
            entities=['races', 'results'],
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
        help='Start date for historical data (YYYY-MM-DD). Default: 2015-01-01'
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
            test_mode=args.test
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
