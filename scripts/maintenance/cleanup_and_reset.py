#!/usr/bin/env python3
"""
Cleanup Script - Reset Database Tables for Fresh Start

This script truncates all data tables while preserving the schema,
allowing you to start the data collection process from scratch.

IMPORTANT: This will delete ALL existing data!

Usage:
    python3 cleanup_and_reset.py                    # Dry-run (shows what will be deleted)
    python3 cleanup_and_reset.py --confirm          # Actually delete data
    python3 cleanup_and_reset.py --tables races results  # Only specific tables
"""

import sys
import argparse
from pathlib import Path
from typing import List

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('cleanup')

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
RESET = '\033[0m'


class DatabaseCleanup:
    """Clean up database tables for fresh start"""

    # All data tables (in order - reference data last to preserve foreign keys)
    ALL_TABLES = [
        'ra_mst_runners',      # Delete first (has FK to races, horses, jockeys, etc.)
        'ra_races',        # Delete second (has FK to courses)
        'ra_horses',       # Entity tables
        'ra_jockeys',
        'ra_trainers',
        'ra_owners',
        'ra_courses',      # Reference tables (delete last)
        'ra_bookmakers',
    ]

    # Primary key mapping for each table
    TABLE_PRIMARY_KEYS = {
        'ra_mst_runners': 'runner_id',
        'ra_races': 'race_id',
        'ra_horses': 'horse_id',
        'ra_jockeys': 'jockey_id',
        'ra_trainers': 'trainer_id',
        'ra_owners': 'owner_id',
        'ra_courses': 'course_id',
        'ra_bookmakers': 'bookmaker_id',
    }

    def __init__(self):
        """Initialize cleanup"""
        self.config = get_config()
        self.db = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key
        )

    def get_table_count(self, table: str) -> int:
        """Get current record count for a table"""
        try:
            result = self.db.client.table(table).select('*', count='exact').limit(0).execute()
            return result.count if result.count else 0
        except Exception as e:
            logger.error(f"Error getting count for {table}: {e}")
            return -1

    def show_current_state(self, tables: List[str] = None):
        """Display current state of all tables"""
        if tables is None:
            tables = self.ALL_TABLES

        print(f"\n{BOLD}{BLUE}Current Database State{RESET}")
        print(f"{BLUE}{'=' * 60}{RESET}\n")

        total_records = 0
        for table in tables:
            count = self.get_table_count(table)
            if count >= 0:
                status = f"{GREEN}✓{RESET}" if count > 0 else f"{YELLOW}○{RESET}"
                print(f"{status} {table:<20} {count:>10,} records")
                total_records += count
            else:
                print(f"{RED}✗{RESET} {table:<20} {'ERROR':>10}")

        print(f"\n{BOLD}Total Records: {total_records:,}{RESET}\n")
        return total_records

    def truncate_table(self, table: str) -> bool:
        """Truncate a specific table"""
        try:
            logger.info(f"Truncating {table}...")

            # Delete all records (Supabase doesn't have TRUNCATE, so we delete)
            # Delete in batches by repeatedly deleting until table is empty
            deleted_total = 0

            # Get the primary key for this table
            primary_key = self.TABLE_PRIMARY_KEYS.get(table)
            if not primary_key:
                logger.error(f"No primary key defined for {table}")
                return False

            while True:
                # Delete batch - use neq filter on primary key to match all records
                # Supabase will apply its own internal limits
                result = self.db.client.table(table).delete().neq(primary_key, '').execute()

                # Check if any rows were deleted
                if not result.data or len(result.data) == 0:
                    break

                deleted_count = len(result.data)
                deleted_total += deleted_count
                logger.info(f"  Deleted {deleted_count} records from {table} (total: {deleted_total})")

            logger.info(f"✓ Truncated {table} ({deleted_total} records deleted)")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to truncate {table}: {e}")
            return False

    def cleanup(self, tables: List[str] = None, dry_run: bool = True):
        """Clean up specified tables"""
        if tables is None:
            tables = self.ALL_TABLES

        print(f"\n{BOLD}{RED}{'=' * 60}{RESET}")
        if dry_run:
            print(f"{BOLD}{YELLOW}DRY RUN - No data will be deleted{RESET}")
        else:
            print(f"{BOLD}{RED}LIVE RUN - Data WILL be deleted!{RESET}")
        print(f"{BOLD}{RED}{'=' * 60}{RESET}\n")

        # Show current state
        total_before = self.show_current_state(tables)

        if total_before == 0:
            print(f"\n{GREEN}✓ All tables are already empty. Nothing to clean up.{RESET}\n")
            return

        # Confirm before deletion
        if not dry_run:
            print(f"\n{BOLD}{RED}WARNING: You are about to delete {total_before:,} records!{RESET}")
            print(f"{YELLOW}This action cannot be undone.{RESET}\n")

            response = input(f"Type 'DELETE' to confirm deletion: ")
            if response != 'DELETE':
                print(f"\n{YELLOW}Cleanup cancelled.{RESET}\n")
                return
            print()

        # Perform cleanup
        success_count = 0
        fail_count = 0

        for table in tables:
            count = self.get_table_count(table)
            if count <= 0:
                logger.info(f"⊘ {table} is already empty, skipping")
                continue

            if dry_run:
                print(f"{YELLOW}[DRY RUN]{RESET} Would delete {count:,} records from {table}")
            else:
                if self.truncate_table(table):
                    success_count += 1
                else:
                    fail_count += 1

        # Show final state
        if not dry_run:
            print(f"\n{BOLD}{GREEN}Cleanup Complete{RESET}")
            print(f"{GREEN}{'=' * 60}{RESET}\n")

            total_after = self.show_current_state(tables)

            print(f"\n{BOLD}Summary:{RESET}")
            print(f"  Tables cleaned: {success_count}")
            print(f"  Tables failed: {fail_count}")
            print(f"  Records before: {total_before:,}")
            print(f"  Records after: {total_after:,}")
            print(f"  Records deleted: {total_before - total_after:,}\n")
        else:
            print(f"\n{BOLD}{YELLOW}This was a dry run. No data was deleted.{RESET}")
            print(f"{YELLOW}Run with --confirm to actually delete data.{RESET}\n")


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Clean up database tables for fresh start',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 cleanup_and_reset.py                    # Dry-run (safe, shows what will happen)
  python3 cleanup_and_reset.py --confirm          # Actually delete all data
  python3 cleanup_and_reset.py --confirm --tables ra_races ra_mst_runners  # Only specific tables
        """
    )

    parser.add_argument(
        '--confirm',
        action='store_true',
        help='Actually delete data (without this flag, only shows what would be deleted)'
    )

    parser.add_argument(
        '--tables',
        nargs='+',
        help='Specific tables to clean (space-separated). If not specified, cleans all tables.'
    )

    args = parser.parse_args()

    # Initialize cleanup
    cleanup = DatabaseCleanup()

    # Validate table names if specified
    if args.tables:
        invalid_tables = [t for t in args.tables if t not in cleanup.ALL_TABLES]
        if invalid_tables:
            print(f"{RED}Error: Invalid table names: {', '.join(invalid_tables)}{RESET}")
            print(f"\nValid tables: {', '.join(cleanup.ALL_TABLES)}")
            sys.exit(1)

    # Run cleanup
    cleanup.cleanup(
        tables=args.tables if args.tables else None,
        dry_run=not args.confirm
    )


if __name__ == '__main__':
    main()
