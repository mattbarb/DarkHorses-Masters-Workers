#!/usr/bin/env python3
"""
Master Fetcher Controller
==========================

Central controller for ALL Racing API data fetching operations.

Modes:
1. BACKFILL - Fetch all historical data from 01/01/2015 to present
2. DAILY - Fetch today's data + recent updates (scheduled for 1am UK)
3. MANUAL - Run specific fetchers on-demand
4. SCHEDULED - Check schedule and run appropriate tasks (for cron)
5. ANALYZE - Comprehensive data analysis of all tables
6. TEST-INSERT - Insert test data into all tables (hardcoded templates)
7. TEST-CLEANUP - Remove all test data from tables
8. TEST-AUTO - Schema-aware test insertion (uses actual column inventory)
9. TEST-FULL - Complete test workflow (insert → analyze → cleanup)
10. TEST-API - Real API-source test insertion (fetches real data and marks as TEST)

Features:
- Coordinates all fetchers
- Handles Racing API data (10 master tables + races/runners/results)
- Built-in scheduling logic (daily/weekly/monthly)
- Real-time progress monitoring (interactive mode)
- Automated JSON logging (server mode)
- Manual override capability
- Comprehensive error handling

Tables Managed (API Data):
- ra_mst_courses
- ra_mst_bookmakers
- ra_mst_jockeys
- ra_mst_trainers
- ra_mst_owners
- ra_mst_horses (with pedigree)
- ra_races
- ra_runners
- ra_race_results
- ra_horse_pedigree

Usage:
    # Backfill all data from 2015 (interactive with progress)
    python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

    # Daily sync (for 1am cron - automated)
    python3 fetchers/master_fetcher_controller.py --mode daily

    # Scheduled mode (checks what needs to run based on schedule)
    python3 fetchers/master_fetcher_controller.py --mode scheduled

    # Manual run with progress
    python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races --days-back 7 --interactive

    # Analyze all tables (comprehensive data analysis)
    python3 fetchers/master_fetcher_controller.py --mode analyze --interactive

    # Insert test data into all tables
    python3 fetchers/master_fetcher_controller.py --mode test-insert --interactive

    # Clean up test data
    python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive

    # Insert real API-source test data (RECOMMENDED for verifying column capture)
    python3 fetchers/master_fetcher_controller.py --mode test-api --interactive

    # Clean up API-source test data
    python3 fetchers/master_fetcher_controller.py --mode test-api-cleanup --interactive

    # Test mode (limited data for verification)
    python3 fetchers/master_fetcher_controller.py --mode daily --test --interactive

    # Show schedule
    python3 fetchers/master_fetcher_controller.py --show-schedule
"""

import sys
import os
import argparse
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# Try to import tqdm for progress bars (optional)
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("Note: Install tqdm for progress bars: pip install tqdm")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.logger import get_logger

# Import fetchers
from fetchers.courses_fetcher import CoursesFetcher
from fetchers.bookmakers_fetcher import BookmakersFetcher
from fetchers.jockeys_fetcher import JockeysFetcher
from fetchers.trainers_fetcher import TrainersFetcher
from fetchers.owners_fetcher import OwnersFetcher
from fetchers.races_fetcher import RacesFetcher
from fetchers.results_fetcher import ResultsFetcher

logger = get_logger('master_fetcher_controller')

# Backfill start date
BACKFILL_START_DATE = '2015-01-01'

# Built-in Scheduling Configuration
# This allows the controller to determine what to run based on schedule
SCHEDULE_CONFIG = {
    'daily': {
        'description': 'Daily sync - runs every day at 1am UK time',
        'tables': ['ra_races', 'ra_race_results'],  # Transaction tables
        'time': '01:00',  # UK time
        'timezone': 'Europe/London',
        'enabled': True
    },
    'weekly': {
        'description': 'Weekly people data refresh - runs Sunday at 2am UK time',
        'tables': ['ra_mst_jockeys', 'ra_mst_trainers', 'ra_mst_owners'],
        'day': 'sunday',  # Day of week
        'time': '02:00',  # UK time
        'timezone': 'Europe/London',
        'enabled': True
    },
    'monthly': {
        'description': 'Monthly reference data refresh - runs 1st of month at 3am UK time',
        'tables': ['ra_mst_courses', 'ra_mst_bookmakers'],
        'day_of_month': 1,  # 1st of month
        'time': '03:00',  # UK time
        'timezone': 'Europe/London',
        'enabled': True
    }
}

# Fetcher table mapping
FETCHER_MAPPING = {
    # Master tables (reference data)
    'ra_mst_courses': {
        'fetcher': CoursesFetcher,
        'method': 'fetch_and_store',
        'type': 'bulk',
        'params': {},
        'description': 'UK & Ireland racing courses',
        'api_endpoint': '/v1/courses',
        'columns': ['id', 'name', 'code', 'region', 'country', 'type', 'surface', 'latitude', 'longitude']
    },
    'ra_mst_bookmakers': {
        'fetcher': BookmakersFetcher,
        'method': 'fetch_and_store',
        'type': 'bulk',
        'params': {},
        'description': 'Bookmakers list',
        'api_endpoint': '/v1/bookmakers',
        'columns': ['id', 'name', 'url']
    },
    'ra_mst_jockeys': {
        'fetcher': JockeysFetcher,
        'method': 'fetch_and_store',
        'type': 'bulk',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Active jockeys (GB & IRE)',
        'api_endpoint': '/v1/jockeys',
        'columns': ['id', 'name', 'region', 'nationality', 'dob', 'statistics...']
    },
    'ra_mst_trainers': {
        'fetcher': TrainersFetcher,
        'method': 'fetch_and_store',
        'type': 'bulk',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Active trainers (GB & IRE)',
        'api_endpoint': '/v1/trainers',
        'columns': ['id', 'name', 'region', 'location', 'statistics...']
    },
    'ra_mst_owners': {
        'fetcher': OwnersFetcher,
        'method': 'fetch_and_store',
        'type': 'bulk',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Active owners (GB & IRE)',
        'api_endpoint': '/v1/owners',
        'columns': ['id', 'name', 'region', 'statistics...']
    },

    # Transaction tables (date-based)
    'ra_races': {
        'fetcher': RacesFetcher,
        'method': 'fetch_and_store',
        'type': 'date_range',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Race metadata from racecards',
        'api_endpoint': '/v1/racecards/pro',
        'columns': ['id', 'date', 'time', 'course_id', 'race_class', 'distance_f', 'going', 'prize_money...']
    },
    'ra_runners': {
        'fetcher': RacesFetcher,  # Same fetcher as races
        'method': 'fetch_and_store',
        'type': 'date_range',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Race runners/entries from racecards',
        'api_endpoint': '/v1/racecards/pro',
        'columns': ['id', 'race_id', 'horse_id', 'jockey_id', 'trainer_id', 'draw', 'weight', 'odds...']
    },
    'ra_mst_horses': {
        'fetcher': RacesFetcher,  # Extracted during races fetch
        'method': 'fetch_and_store',
        'type': 'date_range',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Horses (extracted from racecards with Pro enrichment)',
        'api_endpoint': '/v1/racecards/pro + /v1/horses/{id}/pro',
        'columns': ['id', 'name', 'sex', 'dob', 'colour', 'region', 'sire_id', 'dam_id', 'damsire_id...']
    },
    'ra_horse_pedigree': {
        'fetcher': RacesFetcher,  # Captured during horse enrichment
        'method': 'fetch_and_store',
        'type': 'date_range',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Horse pedigree (captured during Pro enrichment)',
        'api_endpoint': '/v1/horses/{id}/pro',
        'columns': ['horse_id', 'sire', 'sire_id', 'dam', 'dam_id', 'damsire', 'damsire_id', 'breeder...']
    },
    'ra_race_results': {
        'fetcher': ResultsFetcher,
        'method': 'fetch_and_store',
        'type': 'date_range',
        'params': {'region_codes': ['gb', 'ire']},
        'description': 'Historical race results',
        'api_endpoint': '/v1/results',
        'columns': ['race_id', 'position', 'distance_beaten', 'finishing_time', 'starting_price...']
    }
}


class MasterFetcherController:
    """Master controller for all fetcher operations"""

    def __init__(self, test_mode: bool = False, interactive: bool = False):
        """
        Initialize controller

        Args:
            test_mode: If True, run with limited data for testing
            interactive: If True, show progress bars and real-time updates (for local runs)
                        If False, use JSON logging (for automated/server runs)
        """
        self.config = get_config()
        self.test_mode = test_mode
        self.interactive = interactive and TQDM_AVAILABLE  # Only enable if tqdm available
        self.results = {}
        self.stats = {
            'total_tables': 0,
            'successful': 0,
            'failed': 0,
            'start_time': None,
            'end_time': None
        }

    def run_fetcher(self, table: str, mode: str, **kwargs) -> Dict:
        """
        Run a specific fetcher

        Args:
            table: Table name (e.g., 'ra_mst_courses')
            mode: 'backfill', 'daily', or 'manual'
            **kwargs: Additional parameters for fetcher

        Returns:
            Result dictionary
        """
        if table not in FETCHER_MAPPING:
            logger.error(f"Unknown table: {table}")
            return {'success': False, 'error': f'Unknown table: {table}'}

        mapping = FETCHER_MAPPING[table]
        fetcher_class = mapping['fetcher']
        method_name = mapping['method']
        fetcher_type = mapping['type']
        base_params = mapping['params'].copy()

        logger.info("=" * 80)
        logger.info(f"FETCHER: {table}")
        logger.info(f"Type: {fetcher_type}")
        logger.info(f"Description: {mapping['description']}")
        logger.info(f"Endpoint: {mapping['api_endpoint']}")
        logger.info(f"Mode: {mode}")
        logger.info("=" * 80)

        try:
            # Initialize fetcher
            fetcher = fetcher_class()
            method = getattr(fetcher, method_name)

            # Prepare parameters based on type and mode
            params = base_params.copy()
            params.update(kwargs)

            if fetcher_type == 'date_range':
                if mode == 'backfill':
                    # Backfill from 2015 to today
                    params['start_date'] = BACKFILL_START_DATE
                    params['end_date'] = datetime.now().strftime('%Y-%m-%d')
                    logger.info(f"Backfill range: {params['start_date']} to {params['end_date']}")

                elif mode == 'daily':
                    # Fetch last 3 days (to catch late updates)
                    if self.test_mode:
                        params['days_back'] = 3
                    else:
                        params['days_back'] = 3
                    logger.info(f"Daily mode: Last {params['days_back']} days")

            elif fetcher_type == 'bulk':
                if mode == 'daily':
                    logger.info("Bulk fetcher - fetching all current data")
                elif mode == 'backfill':
                    logger.info("Bulk fetcher - backfill not applicable (always fetches current)")

            # Test mode limits
            if self.test_mode and fetcher_type == 'date_range':
                params['days_back'] = min(params.get('days_back', 7), 7)
                logger.info(f"Test mode: Limited to {params['days_back']} days")

            # Execute
            logger.info(f"Calling {fetcher_class.__name__}.{method_name}() with params: {params}")

            # Interactive mode: Show progress indicator
            if self.interactive:
                print(f"\n🔄 Fetching {table}...")
                print(f"   Type: {fetcher_type}")
                print(f"   Mode: {mode}")
                if fetcher_type == 'date_range' and 'start_date' in params:
                    print(f"   Range: {params.get('start_date')} to {params.get('end_date')}")
                elif 'days_back' in params:
                    print(f"   Days: Last {params['days_back']} days")
                print(f"   Starting: {datetime.now().strftime('%H:%M:%S')}")

            start_time = datetime.now()
            result = method(**params)
            duration = datetime.now() - start_time

            # Update stats
            if result.get('success'):
                self.stats['successful'] += 1
            else:
                self.stats['failed'] += 1

            # Log result
            if result.get('success'):
                logger.info(f"✅ Success: {table}")
                logger.info(f"   Duration: {duration}")
                if 'fetched' in result:
                    logger.info(f"   Fetched: {result['fetched']}")
                if 'inserted' in result:
                    logger.info(f"   Inserted: {result['inserted']}")

                # Interactive mode: Show success
                if self.interactive:
                    print(f"✅ Success: {table}")
                    print(f"   Duration: {duration}")
                    print(f"   Fetched: {result.get('fetched', 'N/A')}")
                    print(f"   Inserted: {result.get('inserted', 'N/A')}")
            else:
                logger.error(f"❌ Failed: {table}")
                logger.error(f"   Error: {result.get('error', 'Unknown')}")

                # Interactive mode: Show error
                if self.interactive:
                    print(f"❌ Failed: {table}")
                    print(f"   Error: {result.get('error', 'Unknown')}")

            result['duration'] = str(duration)
            result['table'] = table
            return result

        except Exception as e:
            logger.error(f"❌ Error running fetcher for {table}: {e}", exc_info=True)
            self.stats['failed'] += 1

            if self.interactive:
                print(f"❌ Error: {table}")
                print(f"   {str(e)}")

            return {
                'success': False,
                'table': table,
                'error': str(e)
            }

    def _print_progress_header(self, mode: str, tables: List[str]):
        """Print interactive progress header"""
        if not self.interactive:
            return

        print("\n" + "=" * 80)
        print(f"FETCHER CONTROLLER - {mode.upper()} MODE")
        print("=" * 80)
        print(f"Tables to process: {len(tables)}")
        for i, table in enumerate(tables, 1):
            print(f"  {i}. {table}")
        print(f"\nStart time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def _print_progress_summary(self, tables: List[str]):
        """Print interactive progress summary during execution"""
        if not self.interactive:
            return

        completed = self.stats['successful'] + self.stats['failed']
        total = len(tables)
        pct = (completed / total * 100) if total > 0 else 0

        print(f"\n📊 Progress: {completed}/{total} ({pct:.1f}%)")
        print(f"   ✅ Successful: {self.stats['successful']}")
        print(f"   ❌ Failed: {self.stats['failed']}")
        print()

    def check_schedule(self) -> Dict[str, List[str]]:
        """
        Check schedule and determine what needs to run

        Returns:
            Dictionary with tasks to run: {'daily': [...], 'weekly': [...], 'monthly': [...]}
        """
        now = datetime.now()
        tasks_to_run = {}

        for schedule_name, config in SCHEDULE_CONFIG.items():
            if not config.get('enabled', True):
                continue

            should_run = False

            if schedule_name == 'daily':
                # Daily always runs (when called at scheduled time)
                should_run = True

            elif schedule_name == 'weekly':
                # Check if today is the scheduled day
                day_of_week = now.strftime('%A').lower()
                if day_of_week == config.get('day', 'sunday').lower():
                    should_run = True

            elif schedule_name == 'monthly':
                # Check if today is the scheduled day of month
                if now.day == config.get('day_of_month', 1):
                    should_run = True

            if should_run:
                tasks_to_run[schedule_name] = config['tables']

        return tasks_to_run

    def run_scheduled(self):
        """
        Run scheduled tasks based on current date/time

        This method checks the schedule and runs appropriate tasks.
        Designed to be called from cron at a regular interval (e.g., hourly).
        """
        logger.info("=" * 80)
        logger.info("SCHEDULED MODE - Checking schedule")
        logger.info("=" * 80)

        if self.interactive:
            print("\n" + "=" * 80)
            print("SCHEDULED MODE")
            print("=" * 80)
            print(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        tasks_to_run = self.check_schedule()

        if not tasks_to_run:
            logger.info("No tasks scheduled to run at this time")
            if self.interactive:
                print("\n✓ No tasks scheduled to run at this time")
            return

        logger.info(f"Tasks to run: {list(tasks_to_run.keys())}")
        if self.interactive:
            print(f"\nTasks to run: {list(tasks_to_run.keys())}")

        # Collect all unique tables to run
        all_tables = []
        for schedule_name, tables in tasks_to_run.items():
            logger.info(f"\n{schedule_name.upper()} schedule:")
            for table in tables:
                if table not in all_tables:
                    all_tables.append(table)
                    logger.info(f"  - {table}")

        # Run daily mode for all scheduled tables
        self.run_daily(tables=all_tables)

    def show_schedule(self):
        """Display the built-in schedule configuration"""
        print("\n" + "=" * 80)
        print("FETCHER SCHEDULE CONFIGURATION")
        print("=" * 80)

        for schedule_name, config in SCHEDULE_CONFIG.items():
            status = "✅ ENABLED" if config.get('enabled', True) else "❌ DISABLED"
            print(f"\n{schedule_name.upper()} - {status}")
            print(f"  Description: {config['description']}")
            print(f"  Time: {config['time']} {config['timezone']}")

            if 'day' in config:
                print(f"  Day: {config['day'].title()}")
            elif 'day_of_month' in config:
                print(f"  Day of month: {config['day_of_month']}")

            print(f"  Tables:")
            for table in config['tables']:
                print(f"    - {table}")

        print("\n" + "=" * 80)
        print("\nCRON CONFIGURATION EXAMPLES:")
        print("=" * 80)
        print("\n# Run scheduled mode every hour (checks schedule automatically)")
        print("0 * * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode scheduled >> logs/cron_scheduled.log 2>&1")
        print("\n# Or run specific schedules manually:")
        print("# Daily (1am)")
        print("0 1 * * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily >> logs/cron_daily.log 2>&1")
        print("\n# Weekly (Sunday 2am)")
        print("0 2 * * 0 cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_jockeys ra_mst_trainers ra_mst_owners >> logs/cron_weekly.log 2>&1")
        print("\n# Monthly (1st of month 3am)")
        print("0 3 1 * * cd /path/to/project && python3 fetchers/master_fetcher_controller.py --mode daily --tables ra_mst_courses ra_mst_bookmakers >> logs/cron_monthly.log 2>&1")
        print("\n" + "=" * 80)

    def run_backfill(self, tables: Optional[List[str]] = None):
        """
        Run backfill for all or specific tables

        Args:
            tables: Optional list of table names. If None, runs all.
        """
        logger.info("=" * 80)
        logger.info("BACKFILL MODE - Fetching from 2015-01-01 to present")
        logger.info("=" * 80)

        if tables is None:
            tables = list(FETCHER_MAPPING.keys())

        logger.info(f"Tables to backfill: {len(tables)}")
        for table in tables:
            logger.info(f"  - {table}")

        # Run in recommended order
        # 1. Master tables first (reference data)
        master_tables = [t for t in tables if t.startswith('ra_mst_') and t != 'ra_mst_horses']
        # 2. Races (creates horses, pedigree, runners)
        race_tables = ['ra_races', 'ra_runners', 'ra_mst_horses', 'ra_horse_pedigree']
        race_tables = [t for t in race_tables if t in tables]
        # 3. Results (updates runners)
        result_tables = [t for t in tables if t == 'ra_race_results']

        execution_order = master_tables + race_tables + result_tables

        # Initialize stats
        self.stats['total_tables'] = len(execution_order)
        self.stats['start_time'] = datetime.now()

        # Show progress header in interactive mode
        self._print_progress_header('backfill', execution_order)

        # Execute each fetcher
        for i, table in enumerate(execution_order, 1):
            result = self.run_fetcher(table, mode='backfill')
            self.results[table] = result

            # Show progress summary after each table in interactive mode
            if self.interactive and i < len(execution_order):
                self._print_progress_summary(execution_order)

            # Small delay between fetchers
            time.sleep(2)

        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        self._print_summary(mode='backfill', duration=duration)

    def run_daily(self, tables: Optional[List[str]] = None):
        """
        Run daily sync for all or specific tables

        Args:
            tables: Optional list of table names. If None, runs all.
        """
        logger.info("=" * 80)
        logger.info("DAILY SYNC MODE - Last 3 days + current data")
        logger.info("=" * 80)

        if tables is None:
            tables = list(FETCHER_MAPPING.keys())

        logger.info(f"Tables to sync: {len(tables)}")

        # Run in same order as backfill
        master_tables = [t for t in tables if t.startswith('ra_mst_') and t != 'ra_mst_horses']
        race_tables = ['ra_races', 'ra_runners', 'ra_mst_horses', 'ra_horse_pedigree']
        race_tables = [t for t in race_tables if t in tables]
        result_tables = [t for t in tables if t == 'ra_race_results']

        execution_order = master_tables + race_tables + result_tables

        # Initialize stats
        self.stats['total_tables'] = len(execution_order)
        self.stats['start_time'] = datetime.now()

        # Show progress header in interactive mode
        self._print_progress_header('daily', execution_order)

        # Execute each fetcher
        for i, table in enumerate(execution_order, 1):
            result = self.run_fetcher(table, mode='daily')
            self.results[table] = result

            # Show progress summary after each table in interactive mode
            if self.interactive and i < len(execution_order):
                self._print_progress_summary(execution_order)

            time.sleep(1)

        self.stats['end_time'] = datetime.now()
        duration = self.stats['end_time'] - self.stats['start_time']
        self._print_summary(mode='daily', duration=duration)

    def run_manual(self, table: str, **kwargs):
        """
        Run specific fetcher manually with custom parameters

        Args:
            table: Table name
            **kwargs: Custom parameters for fetcher
        """
        logger.info("=" * 80)
        logger.info("MANUAL MODE - Custom execution")
        logger.info("=" * 80)

        result = self.run_fetcher(table, mode='manual', **kwargs)
        self.results[table] = result
        self._print_summary(mode='manual', duration=None)

    def _print_summary(self, mode: str, duration: Optional[timedelta]):
        """Print execution summary"""
        logger.info("\n" + "=" * 80)
        logger.info(f"SUMMARY - {mode.upper()} MODE")
        logger.info("=" * 80)

        success_count = sum(1 for r in self.results.values() if r.get('success'))
        fail_count = len(self.results) - success_count

        logger.info(f"Total tables: {len(self.results)}")
        logger.info(f"Success: {success_count}")
        logger.info(f"Failed: {fail_count}")

        if duration:
            logger.info(f"Total duration: {duration}")

        # Failed tables
        if fail_count > 0:
            logger.warning("\nFailed tables:")
            for table, result in self.results.items():
                if not result.get('success'):
                    logger.warning(f"  {table}: {result.get('error', 'Unknown error')}")

        # Interactive mode: Show detailed summary
        if self.interactive:
            print("\n" + "=" * 80)
            print(f"FINAL SUMMARY - {mode.upper()} MODE")
            print("=" * 80)
            print(f"\n📊 Overall Statistics:")
            print(f"   Total tables: {len(self.results)}")
            print(f"   ✅ Successful: {success_count}")
            print(f"   ❌ Failed: {fail_count}")

            if duration:
                print(f"   ⏱️  Total duration: {duration}")
                print(f"   Start time: {self.stats['start_time'].strftime('%Y-%m-%d %H:%M:%S')}")
                print(f"   End time: {self.stats['end_time'].strftime('%Y-%m-%d %H:%M:%S')}")

            # Show successful tables
            if success_count > 0:
                print(f"\n✅ Successful tables:")
                for table, result in self.results.items():
                    if result.get('success'):
                        fetched = result.get('fetched', 'N/A')
                        inserted = result.get('inserted', 'N/A')
                        print(f"   {table}: {fetched} fetched, {inserted} inserted")

            # Show failed tables
            if fail_count > 0:
                print(f"\n❌ Failed tables:")
                for table, result in self.results.items():
                    if not result.get('success'):
                        error = result.get('error', 'Unknown error')
                        print(f"   {table}: {error}")

        # Save results
        results_file = f"logs/fetcher_{mode}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        os.makedirs('logs', exist_ok=True)
        with open(results_file, 'w') as f:
            json.dump({
                'mode': mode,
                'timestamp': datetime.now().isoformat(),
                'duration': str(duration) if duration else None,
                'stats': self.stats,
                'results': self.results
            }, f, indent=2)

        logger.info(f"\nResults saved to: {results_file}")

        if self.interactive:
            print(f"\n💾 Results saved to: {results_file}")
            print("=" * 80 + "\n")

        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(
        description='Master Fetcher Controller - Manage all Racing API data fetching',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive backfill with progress (local run)
  python3 fetchers/master_fetcher_controller.py --mode backfill --interactive

  # Automated daily sync (server/cron run)
  python3 fetchers/master_fetcher_controller.py --mode daily

  # Scheduled mode (checks schedule and runs appropriate tasks)
  python3 fetchers/master_fetcher_controller.py --mode scheduled --interactive

  # Manual run with progress
  python3 fetchers/master_fetcher_controller.py --mode manual --table ra_races --days-back 7 --interactive

  # Analyze all tables (comprehensive data analysis)
  python3 fetchers/master_fetcher_controller.py --mode analyze --interactive

  # Analyze specific tables
  python3 fetchers/master_fetcher_controller.py --mode analyze --tables ra_races ra_runners --interactive

  # Insert test data into all tables
  python3 fetchers/master_fetcher_controller.py --mode test-insert --interactive

  # Clean up test data
  python3 fetchers/master_fetcher_controller.py --mode test-cleanup --interactive

  # Show schedule configuration
  python3 fetchers/master_fetcher_controller.py --show-schedule

  # List all tables
  python3 fetchers/master_fetcher_controller.py --list
        """
    )
    parser.add_argument(
        '--mode',
        choices=['backfill', 'daily', 'manual', 'scheduled', 'analyze', 'test-live', 'test-live-cleanup'],
        default='daily',
        help='Execution mode (default: daily)'
    )
    parser.add_argument(
        '--table',
        help='Specific table to fetch (for manual mode)'
    )
    parser.add_argument(
        '--tables',
        nargs='+',
        help='List of tables to fetch'
    )
    parser.add_argument(
        '--start-date',
        help='Start date for manual mode (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        help='End date for manual mode (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        help='Number of days back for manual mode'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode (limited data)'
    )
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Interactive mode (show progress bars and real-time updates for local runs)'
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help='List all available tables and exit'
    )
    parser.add_argument(
        '--show-schedule',
        action='store_true',
        help='Show schedule configuration and exit'
    )

    args = parser.parse_args()

    # Show schedule mode
    if args.show_schedule:
        controller = MasterFetcherController()
        controller.show_schedule()
        return

    # List mode
    if args.list:
        print("\n" + "=" * 80)
        print("AVAILABLE TABLES")
        print("=" * 80)
        for table, mapping in FETCHER_MAPPING.items():
            print(f"\n{table}")
            print(f"  Type: {mapping['type']}")
            print(f"  Description: {mapping['description']}")
            print(f"  Endpoint: {mapping['api_endpoint']}")
            print(f"  Columns: {', '.join(mapping['columns'][:5])}...")
        print("\n" + "=" * 80)
        return

    # Initialize controller
    controller = MasterFetcherController(test_mode=args.test, interactive=args.interactive)

    # Interactive mode message
    if args.interactive:
        if not TQDM_AVAILABLE:
            print("\n⚠️  WARNING: tqdm not installed. Install with: pip install tqdm")
            print("   Running without progress bars.\n")
        else:
            print("\n✓ Interactive mode enabled (progress monitoring active)\n")

    # Execute based on mode
    if args.mode == 'backfill':
        controller.run_backfill(tables=args.tables)

    elif args.mode == 'daily':
        controller.run_daily(tables=args.tables)

    elif args.mode == 'scheduled':
        controller.run_scheduled()

    elif args.mode == 'manual':
        if not args.table:
            print("ERROR: --table required for manual mode")
            parser.print_help()
            return

        kwargs = {}
        if args.start_date:
            kwargs['start_date'] = args.start_date
        if args.end_date:
            kwargs['end_date'] = args.end_date
        if args.days_back:
            kwargs['days_back'] = args.days_back

        controller.run_manual(args.table, **kwargs)

    elif args.mode == 'analyze':
        # Import and run table analyzer
        from fetchers.analyze_tables import TableAnalyzer

        if controller.interactive:
            print("\n" + "=" * 80)
            print("COMPREHENSIVE TABLE ANALYSIS")
            print("=" * 80)
            print(f"\nAnalyzing {len(args.tables) if args.tables else 'all'} tables...")
            print("This may take several minutes depending on table sizes.\n")

        analyzer = TableAnalyzer()
        results = analyzer.analyze_all(tables=args.tables)

        if controller.interactive:
            analyzer.print_summary(results)

        # Always export to JSON
        filename = analyzer.export_json(results)

        if controller.interactive:
            print(f"\n✅ Analysis complete!")
            print(f"📊 Results saved to: {filename}")
            print(f"\nKey Findings:")
            print(f"  - Total tables analyzed: {results['summary']['total_tables']}")
            print(f"  - Total rows: {results['summary']['total_rows']:,}")
            print(f"  - Total columns: {results['summary']['total_columns']:,}")
        else:
            logger.info(f"Analysis complete. Results saved to: {filename}")

    elif args.mode == 'test-live':
        # Fetch REAL data from Racing API and add **TEST** markers
        from tests.test_live_data_with_markers import LiveDataTestInserter

        if controller.interactive:
            print("\n" + "=" * 80)
            print("LIVE DATA TEST WITH **TEST** MARKERS")
            print("=" * 80)
            print("\nFetching REAL data from Racing API...")
            print("Adding **TEST** markers to all fields...")
            print("Inserting to database for visual verification...\n")

        inserter = LiveDataTestInserter()
        results = inserter.fetch_and_insert_races(days_back=args.days_back or 1)

        if controller.interactive:
            if results['success']:
                print(f"\n✅ Live data test complete!")
                print(f"   Races marked: {results['races_marked']}")
                print(f"   Runners marked: {results['runners_marked']}")
                print(f"\n👀 Now open Supabase and verify all columns show **TEST**")
                print(f"\n🧹 When done, cleanup with: --mode test-live-cleanup")
            else:
                print(f"\n❌ Test failed: {results.get('error')}")
        else:
            logger.info(f"Live data test complete. Marked {results['total_marked']} records")

    elif args.mode == 'test-live-cleanup':
        # Cleanup live data test records
        from tests.test_live_data_with_markers import LiveDataTestInserter

        if controller.interactive:
            print("\n" + "=" * 80)
            print("CLEANUP LIVE DATA TEST")
            print("=" * 80)
            print("\nRemoving all records with **TEST** markers...\n")

        inserter = LiveDataTestInserter()
        results = inserter.cleanup_test_data()

        if controller.interactive:
            if results['success']:
                print(f"\n✅ Cleanup complete: {results['total_deleted']} rows deleted")
            else:
                print(f"\n❌ Cleanup failed")
        else:
            logger.info(f"Test data cleanup complete. Deleted {results['total_deleted']} rows")

    elif args.mode == 'deprecated-test-full':
        # Complete test workflow: insert → analyze → cleanup
        from tests.test_schema_auto import SchemaAwareTestInserter
        from scripts.analysis.analyze_tables import TableAnalyzer

        if controller.interactive:
            print("\n" + "=" * 80)
            print("COMPLETE TEST WORKFLOW")
            print("=" * 80)
            print("\nThis will:")
            print("  1. Insert test data (schema-aware)")
            print("  2. Run comprehensive analysis")
            print("  3. Clean up test data")
            print("\n" + "=" * 80 + "\n")

        # Step 1: Insert test data
        if controller.interactive:
            print("\n📝 STEP 1: Inserting test data...\n")

        inserter = SchemaAwareTestInserter()
        insert_results = inserter.insert_all_test_data(tables=args.tables)

        if controller.interactive:
            inserter.print_summary(insert_results, cleanup=False)

        # Step 2: Run analysis
        if controller.interactive:
            print("\n📊 STEP 2: Running analysis...\n")

        analyzer = TableAnalyzer()
        analysis_results = analyzer.analyze_all(tables=args.tables)

        if controller.interactive:
            analyzer.print_summary(analysis_results)

        # Export analysis
        analysis_file = analyzer.export_json(analysis_results)

        # Step 3: Cleanup
        if controller.interactive:
            print("\n🧹 STEP 3: Cleaning up test data...\n")

        cleanup_results = inserter.cleanup_test_data(tables=args.tables)

        if controller.interactive:
            inserter.print_summary(cleanup_results, cleanup=True)

        # Final summary
        if controller.interactive:
            print("\n" + "=" * 80)
            print("COMPLETE TEST WORKFLOW - SUMMARY")
            print("=" * 80)
            print(f"\n✅ Test data inserted: {insert_results['successful']} tables")
            print(f"📊 Analysis completed: {analysis_results['summary']['total_tables']} tables")
            print(f"🧹 Test data cleaned: {cleanup_results['successful']} tables ({cleanup_results['total_deleted']} rows)")
            print(f"\n📄 Analysis saved to: {analysis_file}")
            print("\n" + "=" * 80)
        else:
            logger.info(f"Complete test workflow finished. Analysis saved to: {analysis_file}")

    elif args.mode == 'test-api':
        # Import and run API-source test data inserter
        from fetchers.test_api_source import APISourceTestInserter

        if controller.interactive:
            print("\n" + "=" * 80)
            print("API-SOURCE TEST DATA INSERTION")
            print("=" * 80)
            print("\nFetching REAL data from Racing API endpoints...")
            print("Data will be marked with **TEST** identifiers.")
            print(f"Tables: {len(args.tables) if args.tables else 'supported API tables'}\n")

        inserter = APISourceTestInserter()
        results = inserter.insert_all_test_data(tables=args.tables)

        if controller.interactive:
            inserter.print_summary(results, cleanup=False)
        else:
            logger.info(f"API-source test insertion complete. Success: {results['successful']}, Failed: {results['failed']}")

    elif args.mode == 'test-api-cleanup':
        # Import and run API-source test data cleanup
        from fetchers.test_api_source import APISourceTestInserter

        if controller.interactive:
            print("\n" + "=" * 80)
            print("CLEANUP API-SOURCE TEST DATA")
            print("=" * 80)
            print(f"\nRemoving test data from {len(args.tables) if args.tables else 'all supported'} tables...")
            print("All rows with **TEST** markers will be deleted.\n")

        inserter = APISourceTestInserter()
        results = inserter.cleanup_test_data(tables=args.tables)

        if controller.interactive:
            inserter.print_summary(results, cleanup=True)
        else:
            logger.info(f"API-source test data cleanup complete. Deleted {results['total_deleted']} rows from {results['successful']} tables")


if __name__ == '__main__':
    main()
