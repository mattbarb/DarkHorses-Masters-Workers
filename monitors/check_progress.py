#!/usr/bin/env python3
"""
Simple Progress Checker - One-shot status check
Run this periodically to check progress without auto-refresh
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config
from datetime import datetime

# ANSI colors
RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'


def get_year_counts(db):
    """Get race counts per year"""
    counts = {}
    for year in range(2015, 2026):
        try:
            result = db.client.table('ra_mst_races').select('*', count='exact') \
                .gte('race_date', f'{year}-01-01') \
                .lte('race_date', f'{year}-12-31') \
                .limit(1).execute()
            counts[year] = result.count or 0
        except Exception as e:
            print(f"Warning: Failed to get count for {year}: {e}")
            counts[year] = 0
    return counts


def estimate_expected(year):
    """Estimate expected races per year"""
    from datetime import date
    if year == 2025:
        days = (date.today() - date(2025, 1, 1)).days + 1
        return int(days * 8.5)
    return 6500


def main():
    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

    print(f"\n{BOLD}{CYAN}━━━ RACING DATA PROGRESS ━━━{RESET}")
    print(f"{DIM}Checked at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")

    # Get counts
    year_counts = get_year_counts(db)

    # Overall totals
    total_actual = sum(year_counts.values())
    total_expected = sum(estimate_expected(y) for y in range(2015, 2026))
    overall_pct = (total_actual / total_expected * 100) if total_expected > 0 else 0

    print(f"{BOLD}Year-by-Year Status:{RESET}\n")
    print(f"{'Year':<8} {'Actual':<12} {'Expected':<12} {'Progress':<10}")
    print("─" * 50)

    for year in range(2015, 2026):
        actual = year_counts[year]
        expected = estimate_expected(year)
        pct = (actual / expected * 100) if expected > 0 else 0

        # Color based on progress
        if pct >= 90:
            color = GREEN
            status = "✓"
        elif pct >= 50:
            color = YELLOW
            status = "⟳"
        elif actual > 0:
            color = YELLOW
            status = "⋯"
        else:
            color = DIM
            status = "○"

        print(f"{year}     {actual:<12,} {expected:<12,} {color}{status} {pct:5.1f}%{RESET}")

    print("─" * 50)
    print(f"\n{BOLD}Overall Progress:{RESET} {total_actual:,} / {total_expected:,} races ({overall_pct:.1f}%)\n")

    # Database stats
    print(f"{BOLD}Database Totals:{RESET}")
    tables = [
        ('ra_courses', 'Courses'),
        ('ra_races', 'Races'),
        ('ra_mst_runners', 'Runners'),
        ('ra_horses', 'Horses'),
        ('ra_jockeys', 'Jockeys'),
        ('ra_trainers', 'Trainers'),
        ('ra_owners', 'Owners')
    ]

    for table, label in tables:
        try:
            result = db.client.table(table).select('*', count='exact').limit(1).execute()
            count = result.count or 0
            print(f"  {label:<15} {count:>12,}")
        except Exception as e:
            print(f"  {label:<15} {DIM}Error: {e}{RESET}")

    print()


if __name__ == '__main__':
    main()
