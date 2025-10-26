"""
Comprehensive Historical Backfill for All RA Tables (2015-2025)

This script performs a complete backfill of all RA tables with historical data from
January 1, 2015 onwards, prioritizing the CRITICAL gap in ra_mst_runners coverage.

CURRENT DATABASE STATE:
- ra_races: 136,648 races (2015-2025) ✅ COMPLETE
- ra_mst_runners: Only 87 races worth of data (0.06% coverage) ❌ CRITICAL GAP
- ra_horses: 111,430 records
- ra_jockeys: 3,482 records
- ra_trainers: 2,780 records
- ra_owners: 48,132 records
- ra_horse_pedigree: 111,353 records
- ra_courses: 101 records ✅ COMPLETE
- ra_bookmakers: 19 records ✅ COMPLETE

CRITICAL ISSUE:
The ra_mst_runners table only has data for 87 races, not the full 136,648 races.
This means we're missing runner data for 99.94% of races.

STRATEGY:
1. Fetch racecards for all historical dates from 2015-01-01 onwards
2. Extract runner data and store in ra_mst_runners
3. Extract and enrich entities (horses, jockeys, trainers, owners)
4. Capture pedigree data for new horses
5. Respect Racing API rate limits (2 requests/second)
6. Checkpoint and resume capability

USAGE:
    # Full backfill from 2015
    python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date 2015-01-01

    # Analyze current coverage
    python3 scripts/backfill_all_ra_tables_2015_2025.py --analyze

    # Resume from checkpoint
    python3 scripts/backfill_all_ra_tables_2015_2025.py --resume

    # Test mode (7 days only)
    python3 scripts/backfill_all_ra_tables_2015_2025.py --test
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from fetchers.results_fetcher import ResultsFetcher

logger = get_logger('backfill_all_ra_tables')


class HistoricalBackfiller:
    """Comprehensive backfill for all RA tables from 2015 onwards"""

    def __init__(self, checkpoint_file: str = None):
        """Initialize backfiller with optional checkpoint file"""
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

        # Use ResultsFetcher for historical data (has complete race results with positions)
        self.results_fetcher = ResultsFetcher()

        # Checkpoint file for resume capability
        if checkpoint_file:
            self.checkpoint_file = Path(checkpoint_file)
        else:
            self.checkpoint_file = Path(__file__).parent.parent / 'logs' / 'backfill_all_tables_checkpoint.json'

        # Error log file
        self.error_log_file = Path(__file__).parent.parent / 'logs' / 'backfill_all_tables_errors.json'

        # Region codes for UK and Ireland
        self.region_codes = ['gb', 'ire']

    def analyze_coverage(self) -> Dict:
        """
        Analyze current coverage for each RA table by year

        Returns:
            Dictionary with coverage analysis
        """
        logger.info("=" * 80)
        logger.info("ANALYZING CURRENT RA TABLE COVERAGE")
        logger.info("=" * 80)

        analysis = {}

        # Define tables to analyze
        tables = [
            ('ra_races', 'race_date', 'race_id'),
            ('ra_mst_runners', 'fetched_at', 'runner_id'),  # Using fetched_at as date column
            ('ra_horses', 'created_at', 'horse_id'),
            ('ra_jockeys', 'created_at', 'jockey_id'),
            ('ra_trainers', 'created_at', 'trainer_id'),
            ('ra_owners', 'created_at', 'owner_id'),
            ('ra_horse_pedigree', 'created_at', 'horse_id'),
            ('ra_courses', None, 'course_id'),
            ('ra_bookmakers', None, 'bookmaker_id')
        ]

        for table_name, date_column, id_column in tables:
            try:
                logger.info(f"\nAnalyzing {table_name}...")

                # Get total count
                result = self.db_client.client.table(table_name).select('*', count='exact').limit(1).execute()
                total_count = result.count if hasattr(result, 'count') else 0

                analysis[table_name] = {
                    'total_records': total_count,
                    'by_year': {}
                }

                # Get counts by year if date column exists
                if date_column and total_count > 0:
                    for year in range(2015, 2026):
                        start_date = f"{year}-01-01"
                        end_date = f"{year}-12-31"

                        # For timestamp columns (created_at, fetched_at), use ISO format
                        if date_column in ['created_at', 'fetched_at']:
                            start_date = f"{year}-01-01T00:00:00"
                            end_date = f"{year}-12-31T23:59:59"

                        year_result = self.db_client.client.table(table_name)\
                            .select('*', count='exact')\
                            .gte(date_column, start_date)\
                            .lte(date_column, end_date)\
                            .limit(1)\
                            .execute()

                        year_count = year_result.count if hasattr(year_result, 'count') else 0
                        analysis[table_name]['by_year'][year] = year_count

                        logger.info(f"  {year}: {year_count:,} records")
                else:
                    logger.info(f"  Total: {total_count:,} records (no date breakdown)")

            except Exception as e:
                logger.error(f"Error analyzing {table_name}: {e}")
                analysis[table_name] = {'error': str(e)}

        return analysis

    def identify_gaps(self, start_date: str, end_date: str) -> Dict:
        """
        Identify date gaps that need backfilling

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Dictionary with gap analysis
        """
        logger.info(f"\nIdentifying gaps from {start_date} to {end_date}...")

        try:
            # Get dates that already have runner data
            result = self.db_client.client.table('ra_mst_races')\
                .select('race_date')\
                .gte('race_date', start_date)\
                .lte('race_date', end_date)\
                .execute()

            dates_with_races = set([row['race_date'] for row in result.data if row.get('race_date')])

            # Check which races have runners
            races_with_runners_result = self.db_client.client.table('ra_mst_runners')\
                .select('race_id')\
                .execute()

            race_ids_with_runners = set([row['race_id'] for row in races_with_runners_result.data])

            logger.info(f"Found {len(dates_with_races)} unique race dates")
            logger.info(f"Found {len(race_ids_with_runners)} races with runner data")

            return {
                'total_dates': len(dates_with_races),
                'dates_with_races': dates_with_races,
                'races_with_runners_count': len(race_ids_with_runners)
            }

        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")
            return {'error': str(e)}

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint data if exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: {checkpoint.get('dates_processed', 0)} dates processed")
                return checkpoint
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return None

    def save_checkpoint(self, stats: Dict, processed_dates: List[str]):
        """Save checkpoint for resume capability"""
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'stats': {
                'total_dates': stats.get('total_dates', 0),
                'dates_processed': len(processed_dates),
                'races_processed': stats.get('races_processed', 0),
                'runners_processed': stats.get('runners_processed', 0),
                'horses_enriched': stats.get('horses_enriched', 0),
                'errors': stats.get('errors', 0),
                'start_time': stats.get('start_time').isoformat() if isinstance(stats.get('start_time'), datetime) else stats.get('start_time'),
            },
            'processed_dates': processed_dates,
            'last_date': processed_dates[-1] if processed_dates else None
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {len(processed_dates)} dates")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def log_error(self, date: str, error: str):
        """Log error to error file"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'date': date,
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

    def backfill_date_range(
        self,
        start_date: str,
        end_date: str,
        resume: bool = False,
        non_interactive: bool = False,
        skip_enrichment: bool = False
    ) -> Dict:
        """
        Backfill all data for a date range

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            resume: Resume from checkpoint if available
            non_interactive: Don't prompt for confirmation
            skip_enrichment: Skip entity enrichment (24x faster, ~11 hours vs 11 days)

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE HISTORICAL BACKFILL: ALL RA TABLES")
        if skip_enrichment:
            logger.info("*** FAST MODE: Entity enrichment DISABLED ***")
        logger.info("=" * 80)
        logger.info(f"Date Range: {start_date} to {end_date}")
        logger.info(f"Region Codes: {self.region_codes}")
        logger.info(f"Skip Enrichment: {skip_enrichment}")

        # Check for existing checkpoint
        checkpoint = None
        processed_dates = []

        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                processed_dates = checkpoint.get('processed_dates', [])
                logger.info(f"Resuming from checkpoint: {len(processed_dates)} dates already processed")
                logger.info(f"Last processed date: {checkpoint.get('last_date')}")

        # Calculate date range
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Generate all dates in range
        all_dates = []
        current_dt = start_dt
        while current_dt <= end_dt:
            date_str = current_dt.strftime('%Y-%m-%d')
            if date_str not in processed_dates:
                all_dates.append(date_str)
            current_dt += timedelta(days=1)

        total_dates = len(all_dates)
        logger.info(f"Total dates to process: {total_dates:,}")

        # Calculate estimated time
        # Average ~12 races per day in UK/IRE
        estimated_races = total_dates * 12
        estimated_api_calls = total_dates  # 1 call per date for racecards
        estimated_seconds = estimated_api_calls * 0.5  # 2 requests/second = 0.5s per request
        estimated_hours = estimated_seconds / 3600
        estimated_days = estimated_hours / 24

        logger.info(f"Estimated races: ~{estimated_races:,}")
        logger.info(f"Estimated API calls: {estimated_api_calls:,}")
        logger.info(f"Estimated time: {estimated_hours:.1f} hours ({estimated_days:.1f} days)")

        # Calculate ETA
        eta = datetime.utcnow().timestamp() + estimated_seconds
        eta_str = datetime.fromtimestamp(eta).strftime('%Y-%m-%d %H:%M:%S')
        logger.info(f"Estimated completion: {eta_str}")

        # Confirm before starting (unless non-interactive)
        if not non_interactive and total_dates > 100:
            response = input(f"\nReady to process {total_dates:,} dates (est. {estimated_days:.1f} days)? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Backfill cancelled by user")
                return {'success': False, 'cancelled': True}

        # Initialize stats
        if checkpoint and 'stats' in checkpoint:
            stats = checkpoint['stats']
            stats['start_time'] = datetime.fromisoformat(stats['start_time']) if isinstance(stats['start_time'], str) else stats['start_time']
            stats['session_start'] = datetime.utcnow()
        else:
            stats = {
                'total_dates': total_dates,
                'dates_processed': 0,
                'dates_with_data': 0,
                'dates_no_data': 0,
                'races_processed': 0,
                'runners_processed': 0,
                'horses_enriched': 0,
                'jockeys_processed': 0,
                'trainers_processed': 0,
                'owners_processed': 0,
                'pedigrees_captured': 0,
                'errors': 0,
                'start_time': datetime.utcnow(),
                'session_start': datetime.utcnow()
            }

        logger.info("\nStarting backfill...")
        logger.info("Progress will be reported every 10 dates")
        logger.info("Checkpoint will be saved every 10 dates")
        logger.info(f"Checkpoint file: {self.checkpoint_file}")
        logger.info(f"Error log file: {self.error_log_file}")

        # Process dates
        for idx, date_str in enumerate(all_dates, 1):
            try:
                logger.info(f"\n[{idx}/{total_dates}] Processing {date_str}...")

                # Fetch historical results for this date using ResultsFetcher
                result = self.results_fetcher.fetch_and_store(
                    start_date=date_str,
                    end_date=date_str,
                    region_codes=self.region_codes,
                    skip_enrichment=skip_enrichment
                )

                # Update stats
                stats['dates_processed'] += 1

                if result.get('success'):
                    # ResultsFetcher returns 'fetched' (number of races), not 'races_fetched'
                    races_fetched = result.get('fetched', 0)
                    # Extract runner count from db_stats
                    runners_fetched = result.get('db_stats', {}).get('runners', {}).get('inserted', 0)

                    if races_fetched > 0:
                        stats['dates_with_data'] += 1
                        stats['races_processed'] += races_fetched
                        stats['runners_processed'] += runners_fetched

                        # Extract entity stats from result
                        entity_stats = result.get('db_stats', {}).get('entities', {})
                        if entity_stats:
                            stats['horses_enriched'] += entity_stats.get('horses', {}).get('inserted', 0)
                            stats['jockeys_processed'] += entity_stats.get('jockeys', {}).get('inserted', 0)
                            stats['trainers_processed'] += entity_stats.get('trainers', {}).get('inserted', 0)
                            stats['owners_processed'] += entity_stats.get('owners', {}).get('inserted', 0)
                            stats['pedigrees_captured'] += entity_stats.get('pedigrees', {}).get('inserted', 0)

                        logger.info(f"  ✓ {races_fetched} races, {runners_fetched} runners")
                    else:
                        stats['dates_no_data'] += 1
                        logger.info(f"  - No races on this date")
                else:
                    stats['errors'] += 1
                    error_msg = result.get('error', 'Unknown error')
                    logger.error(f"  ✗ Error: {error_msg}")
                    self.log_error(date_str, error_msg)

            except Exception as e:
                stats['errors'] += 1
                error_msg = str(e)
                logger.error(f"  ✗ Exception: {error_msg}")
                self.log_error(date_str, error_msg)

            # Track processed dates
            processed_dates.append(date_str)

            # Progress logging and checkpoint saving every 10 dates
            if idx % 10 == 0 or idx == total_dates:
                elapsed = (datetime.utcnow() - stats['session_start']).total_seconds()
                rate = stats['dates_processed'] / elapsed if elapsed > 0 else 0
                remaining_dates = total_dates - idx
                remaining_seconds = remaining_dates / rate if rate > 0 else 0
                remaining_hours = remaining_seconds / 3600
                remaining_days = remaining_hours / 24

                # Calculate new ETA
                eta_timestamp = datetime.utcnow().timestamp() + remaining_seconds
                eta_str = datetime.fromtimestamp(eta_timestamp).strftime('%Y-%m-%d %H:%M:%S')

                logger.info("\n" + "-" * 80)
                logger.info(f"PROGRESS: {idx}/{total_dates} dates ({idx/total_dates*100:.1f}%)")
                logger.info(f"  Dates with data: {stats['dates_with_data']:,}")
                logger.info(f"  Races processed: {stats['races_processed']:,}")
                logger.info(f"  Runners processed: {stats['runners_processed']:,}")
                logger.info(f"  Horses enriched: {stats['horses_enriched']:,}")
                logger.info(f"  Pedigrees captured: {stats['pedigrees_captured']:,}")
                logger.info(f"  Errors: {stats['errors']}")
                logger.info(f"  Rate: {rate:.2f} dates/sec")
                logger.info(f"  Remaining: {remaining_days:.1f} days ({remaining_hours:.1f}h)")
                logger.info(f"  ETA: {eta_str}")
                logger.info("-" * 80)

                # Save checkpoint
                self.save_checkpoint(stats, processed_dates)

        # Final statistics
        stats['end_time'] = datetime.utcnow()
        stats['duration_seconds'] = (stats['end_time'] - stats['session_start']).total_seconds()
        stats['duration_hours'] = stats['duration_seconds'] / 3600
        stats['duration_days'] = stats['duration_hours'] / 24

        logger.info("\n" + "=" * 80)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total dates processed: {stats['dates_processed']:,}")
        logger.info(f"Dates with data: {stats['dates_with_data']:,}")
        logger.info(f"Dates without data: {stats['dates_no_data']:,}")
        logger.info(f"Total races: {stats['races_processed']:,}")
        logger.info(f"Total runners: {stats['runners_processed']:,}")
        logger.info(f"Horses enriched: {stats['horses_enriched']:,}")
        logger.info(f"Jockeys: {stats['jockeys_processed']:,}")
        logger.info(f"Trainers: {stats['trainers_processed']:,}")
        logger.info(f"Owners: {stats['owners_processed']:,}")
        logger.info(f"Pedigrees captured: {stats['pedigrees_captured']:,}")
        logger.info(f"Errors: {stats['errors']}")
        logger.info(f"Duration: {stats['duration_days']:.2f} days ({stats['duration_hours']:.1f} hours)")
        logger.info("=" * 80)

        # Save final checkpoint
        self.save_checkpoint(stats, processed_dates)

        return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Comprehensive historical backfill for all RA tables (2015-2025)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze current coverage
  python3 scripts/backfill_all_ra_tables_2015_2025.py --analyze

  # Full backfill from 2015
  python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date 2015-01-01

  # Backfill specific year
  python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date 2020-01-01 --end-date 2020-12-31

  # Resume from checkpoint
  python3 scripts/backfill_all_ra_tables_2015_2025.py --resume

  # Test mode (7 days)
  python3 scripts/backfill_all_ra_tables_2015_2025.py --test
        """
    )

    parser.add_argument('--analyze', action='store_true',
                       help='Analyze current coverage and exit')
    parser.add_argument('--start-date', type=str, default='2015-01-01',
                       help='Start date (YYYY-MM-DD). Default: 2015-01-01')
    parser.add_argument('--end-date', type=str,
                       help='End date (YYYY-MM-DD). Default: today')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoint')
    parser.add_argument('--test', action='store_true',
                       help='Test mode: process only 7 days')
    parser.add_argument('--non-interactive', action='store_true',
                       help='Run without confirmation prompt (for background jobs)')
    parser.add_argument('--checkpoint-file', type=str,
                       help='Custom checkpoint file path')
    parser.add_argument('--fast', action='store_true',
                       help='Fast mode: skip entity enrichment (24x faster, ~11 hours vs 11 days)')

    args = parser.parse_args()

    backfiller = HistoricalBackfiller(checkpoint_file=args.checkpoint_file)

    # Analyze mode
    if args.analyze:
        analysis = backfiller.analyze_coverage()

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("COVERAGE ANALYSIS SUMMARY")
        logger.info("=" * 80)

        for table_name, data in analysis.items():
            if 'error' in data:
                logger.info(f"\n{table_name}: ERROR - {data['error']}")
            else:
                total = data.get('total_records', 0)
                logger.info(f"\n{table_name}: {total:,} total records")

                if data.get('by_year'):
                    for year in sorted(data['by_year'].keys()):
                        count = data['by_year'][year]
                        logger.info(f"  {year}: {count:,}")

        logger.info("=" * 80)
        return

    # Set end date
    if args.end_date:
        end_date = args.end_date
    else:
        end_date = datetime.utcnow().strftime('%Y-%m-%d')

    # Test mode
    if args.test:
        logger.info("TEST MODE: Processing only 7 days")
        end_date = (datetime.strptime(args.start_date, '%Y-%m-%d') + timedelta(days=6)).strftime('%Y-%m-%d')

    # Run backfill
    result = backfiller.backfill_date_range(
        start_date=args.start_date,
        end_date=end_date,
        resume=args.resume,
        non_interactive=args.non_interactive,
        skip_enrichment=args.fast
    )

    return result


if __name__ == '__main__':
    main()
