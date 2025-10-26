#!/usr/bin/env python3
"""
View Update History - Display data collection metadata and update history

Shows:
- Last update time for each table
- Number of records created/updated
- Update history
- Success rates
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.metadata_tracker import MetadataTracker

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'
DIM = '\033[2m'


def format_timestamp(ts_string: str) -> str:
    """Format ISO timestamp to readable format"""
    if not ts_string:
        return f"{DIM}Never{RESET}"

    try:
        dt = datetime.fromisoformat(ts_string.replace('Z', '+00:00'))
        now = datetime.now(dt.tzinfo)
        diff = now - dt

        # Handle negative differences (future timestamps or clock skew)
        if diff.total_seconds() < 0:
            time_ago = "just now"
        elif diff.days > 0:
            time_ago = f"{diff.days}d ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            time_ago = f"{hours}h ago"
        elif diff.seconds >= 60:
            minutes = diff.seconds // 60
            time_ago = f"{minutes}m ago"
        else:
            time_ago = f"{diff.seconds}s ago"

        # Return compact format with update indicator
        return f"{CYAN}⟳{RESET} Updated: {DIM}{time_ago}{RESET}"
    except Exception:
        return ts_string


def format_status(status: str) -> str:
    """Format status with color"""
    if status == 'success':
        return f"{GREEN}✓ Success{RESET}"
    elif status == 'partial':
        return f"{YELLOW}⚠ Partial{RESET}"
    elif status == 'failed':
        return f"{RED}✗ Failed{RESET}"
    elif status == 'never_updated':
        return f"{DIM}○ Never Updated{RESET}"
    else:
        return f"{YELLOW}{status}{RESET}"


def display_table_summary(tracker: MetadataTracker):
    """Display summary of last updates for all tables"""
    print(f"\n{BOLD}{CYAN}{'═' * 100}{RESET}")
    print(f"{BOLD}{CYAN}DATA COLLECTION UPDATE HISTORY{RESET}")
    print(f"{BOLD}{CYAN}{'═' * 100}{RESET}\n")

    summary = tracker.get_table_summary()

    print(f"{BOLD}{BLUE}━━━ TABLE UPDATE SUMMARY ━━━{RESET}\n")
    print(f"{BOLD}{'Table':<20} {'Last Updated':<45} {'Inserted':<12} {'Updated':<12} {'Status':<15}{RESET}")
    print(f"{DIM}{'─' * 110}{RESET}")

    for table, info in sorted(summary.items()):
        table_display = table.replace('ra_', '')
        last_updated = format_timestamp(info['last_updated'])
        inserted = f"{info['records_inserted']:,}" if info['records_inserted'] else '0'
        updated = f"{info['records_updated']:,}" if info['records_updated'] else '0'
        status = format_status(info['status'])

        print(f"{table_display:<20} {last_updated:<60} {CYAN}{inserted:<12}{RESET} {CYAN}{updated:<12}{RESET} {status}")

    print()


def display_recent_updates(tracker: MetadataTracker, limit: int = 20):
    """Display recent update history"""
    print(f"{BOLD}{BLUE}━━━ RECENT UPDATE HISTORY (Last {limit}) ━━━{RESET}\n")

    history = tracker.get_update_history(limit=limit)

    if not history:
        print(f"{DIM}No update history found.{RESET}\n")
        return

    print(f"{BOLD}{'Time':<22} {'Table':<15} {'Operation':<20} {'Inserted':<10} {'Status':<15}{RESET}")
    print(f"{DIM}{'─' * 90}{RESET}")

    for record in history:
        timestamp = record.get('created_at', '')
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
        except Exception:
            time_str = timestamp[:19] if len(timestamp) >= 19 else timestamp

        table = record.get('table_name', '').replace('ra_', '')
        operation = record.get('operation', '')
        inserted = record.get('records_inserted', 0)
        status = format_status(record.get('status', ''))

        print(f"{time_str:<22} {table:<15} {operation:<20} {CYAN}{inserted:>9,}{RESET} {status}")

    print()


def display_table_statistics(tracker: MetadataTracker, table_name: str, days: int = 30):
    """Display statistics for a specific table"""
    print(f"{BOLD}{BLUE}━━━ STATISTICS FOR {table_name.upper()} (Last {days} days) ━━━{RESET}\n")

    stats = tracker.get_statistics(table_name, days)

    print(f"  Total Updates:     {CYAN}{stats['total_updates']:,}{RESET}")
    print(f"  Records Inserted:  {CYAN}{stats['total_inserted']:,}{RESET}")
    print(f"  Records Updated:   {CYAN}{stats['total_updated']:,}{RESET}")

    success_rate = stats['success_rate']
    if success_rate >= 95:
        rate_color = GREEN
    elif success_rate >= 75:
        rate_color = YELLOW
    else:
        rate_color = RED

    print(f"  Success Rate:      {rate_color}{success_rate:.1f}%{RESET}")
    print()

    # Show recent history for this table
    print(f"{BOLD}Recent Updates:{RESET}\n")

    history = tracker.get_update_history(table_name=table_name, limit=10)

    if history:
        print(f"{BOLD}{'Time':<22} {'Operation':<25} {'Inserted':<10} {'Updated':<10} {'Status':<15}{RESET}")
        print(f"{DIM}{'─' * 90}{RESET}")

        for record in history:
            timestamp = record.get('created_at', '')
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                time_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            except Exception:
                time_str = timestamp[:19] if len(timestamp) >= 19 else timestamp

            operation = record.get('operation', '')
            inserted = record.get('records_inserted', 0)
            updated = record.get('records_updated', 0)
            status = format_status(record.get('status', ''))

            print(f"{time_str:<22} {operation:<25} {CYAN}{inserted:>9,}{RESET} {CYAN}{updated:>9,}{RESET} {status}")
    else:
        print(f"{DIM}No updates found for this table.{RESET}")

    print()


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='View data collection update history and metadata'
    )
    parser.add_argument(
        '--table',
        help='Show detailed statistics for a specific table (e.g., ra_mst_runners)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days for statistics (default: 30)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=20,
        help='Number of recent updates to show (default: 20)'
    )

    args = parser.parse_args()

    # Initialize
    config = get_config()
    db = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )
    tracker = MetadataTracker(db.client)

    if args.table:
        # Show detailed view for specific table
        display_table_statistics(tracker, args.table, args.days)
    else:
        # Show overview
        display_table_summary(tracker)
        display_recent_updates(tracker, args.limit)

    print(f"{BOLD}{CYAN}{'─' * 100}{RESET}")
    print(f"{DIM}Tip: Use --table <table_name> for detailed statistics{RESET}")
    print(f"{BOLD}{CYAN}{'─' * 100}{RESET}\n")


if __name__ == '__main__':
    main()
