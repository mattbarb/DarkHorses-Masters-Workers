#!/usr/bin/env python3
"""
Year-by-Year Progress Bar Monitor

Shows clean progress bars for each year (2015-2025) with:
- Percentage completion per year
- Overall database status
- Auto-refresh every 5 seconds
- Color-coded progress indicators
"""

import sys
from pathlib import Path
import time
import os
from datetime import datetime, date
from typing import Dict, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config

# ANSI color codes
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
MAGENTA = '\033[95m'
CYAN = '\033[96m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'


def get_progress_bar(current: int, expected: int, width: int = 40) -> Tuple[str, float]:
    """
    Generate a visual progress bar

    Args:
        current: Current count
        expected: Expected count
        width: Width of the bar in characters

    Returns:
        Tuple of (colored bar string, percentage)
    """
    if expected == 0:
        return f"[{' ' * width}]", 0.0

    progress = min(current / expected, 1.0)
    filled = int(width * progress)
    bar = '█' * filled + '░' * (width - filled)

    # Color based on progress
    if progress >= 0.9:
        color = GREEN
    elif progress >= 0.5:
        color = YELLOW
    else:
        color = RED

    return f"{color}[{bar}]{RESET}", progress * 100


def get_year_counts(db) -> Dict[int, int]:
    """Get race counts per year from database"""
    counts = {}

    for year in range(2015, 2026):  # 2015-2025
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        try:
            # Check ra_races table (primary source for all race data)
            result = db.client.table('ra_races') \
                .select('*', count='exact') \
                .gte('race_date', start_date) \
                .lte('race_date', end_date) \
                .limit(1) \
                .execute()
            counts[year] = result.count or 0
        except Exception as e:
            print(f"Warning: Failed to get count for {year}: {e}", file=sys.stderr)
            counts[year] = 0

    return counts


def estimate_expected_races(year: int) -> int:
    """
    Estimate expected number of races per year
    Based on typical UK/Ireland racing calendar
    """
    # Average races per day varies by year
    # Using conservative estimates
    if year == 2025:
        # Only partial year - estimate based on days elapsed
        days_in_year = (date.today() - date(2025, 1, 1)).days + 1
        return int(days_in_year * 8.5)  # ~8.5 races/day average
    else:
        # Full year - typical UK/Ireland has ~6000-7000 races/year
        return 6500


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def display_progress(db):
    """Display year-by-year progress bars"""
    clear_screen()

    print(f"\n{BOLD}{CYAN}━━━ RACING DATA COLLECTION PROGRESS ━━━{RESET}\n")
    print(f"{DIM}Data Range: 2015-2025 (Premium Historical Data){RESET}\n")

    # Get counts
    year_counts = get_year_counts(db)
    total_actual = sum(year_counts.values())
    total_expected = sum(estimate_expected_races(y) for y in range(2015, 2026))

    # Display each year
    print(f"{BOLD}Year-by-Year Progress:{RESET}\n")
    print(f"{'Year':<8} {'Progress':<45} {'Races':<20} {'Status':<10}")
    print("─" * 90)

    for year in range(2015, 2026):
        actual = year_counts[year]
        expected = estimate_expected_races(year)
        bar, pct = get_progress_bar(actual, expected, width=35)

        # Status indicator
        if pct >= 90:
            status = f"{GREEN}✓ Complete{RESET}"
        elif pct >= 50:
            status = f"{YELLOW}⟳ In Progress{RESET}"
        elif actual > 0:
            status = f"{YELLOW}⟳ Started{RESET}"
        else:
            status = f"{DIM}○ Not Started{RESET}"

        print(f"{year}     {bar}  {actual:,}/{expected:,} ({pct:5.1f}%)  {status}")

    # Overall summary
    print("\n" + "─" * 90)
    overall_bar, overall_pct = get_progress_bar(total_actual, total_expected, width=50)
    print(f"\n{BOLD}Overall:{RESET}    {overall_bar}  {overall_pct:5.1f}%")
    print(f"\n{BOLD}Total Races:{RESET} {total_actual:,} / {total_expected:,} (estimated)\n")

    # Database stats
    print(f"{BOLD}{CYAN}━━━ DATABASE STATUS ━━━{RESET}\n")

    # Get table counts
    tables = {
        'Courses': 'ra_courses',
        'Bookmakers': 'ra_bookmakers',
        'Horses': 'ra_horses',
        'Jockeys': 'ra_jockeys',
        'Trainers': 'ra_trainers',
        'Owners': 'ra_owners',
        'Races': 'ra_races',
        'Runners': 'ra_runners'
    }

    for name, table in tables.items():
        result = db.client.table(table).select('*', count='exact').limit(1).execute()
        count = result.count or 0
        print(f"  {name:<15} {count:>10,} records")

    # Footer
    print(f"\n{DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
    print(f"{DIM}Auto-refreshing every 5 seconds... (Press Ctrl+C to exit){RESET}\n")


def main():
    """Main function"""
    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

    try:
        while True:
            display_progress(db)
            time.sleep(5)
    except KeyboardInterrupt:
        print(f"\n\n{DIM}Monitor stopped.{RESET}\n")
        sys.exit(0)


if __name__ == '__main__':
    main()
