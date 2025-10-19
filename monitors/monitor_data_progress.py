#!/usr/bin/env python3
"""
Comprehensive Data Progress Monitor

Real-time monitoring dashboard with:
- Live table counts across all 9 tables
- Year-by-year breakdown (2015-2025)
- Collection progress metrics
- Data quality indicators
- Entity extraction rates
- Recommendations
- Auto-refreshes every 2 seconds
"""

import sys
from pathlib import Path
import time
import os
import argparse
from datetime import datetime, date
from typing import Dict, Tuple, Optional

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


def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


def format_number(num: int) -> str:
    """Format number with thousands separator"""
    return f"{num:,}"


def get_table_count(db, table: str) -> int:
    """Get total count for a table"""
    try:
        result = db.client.table(table).select('*', count='exact').limit(1).execute()
        return result.count or 0
    except Exception as e:
        logger.warning(f"Failed to get count for table {table}: {e}")
        return 0


def get_year_breakdown(db) -> Dict[int, Dict]:
    """Get race counts per year"""
    breakdown = {}

    for year in range(2015, 2026):  # 2015-2025
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"

        # Get races count (primary source)
        try:
            races_result = db.client.table('ra_races') \
                .select('*', count='exact') \
                .gte('race_date', start_date) \
                .lte('race_date', end_date) \
                .limit(1) \
                .execute()
            races_count = races_result.count or 0
        except Exception as e:
            logger.warning(f"Failed to get races count for {year}: {e}")
            races_count = 0

        # Get runners count (shows how many horses/runners we have)
        try:
            runners_result = db.client.table('ra_runners') \
                .select('*', count='exact') \
                .gte('race_date', start_date) \
                .lte('race_date', end_date) \
                .limit(1) \
                .execute()
            runners_count = runners_result.count or 0
        except Exception as e:
            logger.warning(f"Failed to get runners count for {year}: {e}")
            runners_count = 0

        breakdown[year] = {
            'races': races_count,
            'runners': runners_count
        }

    return breakdown


def estimate_expected_races(year: int) -> int:
    """Estimate expected number of races per year"""
    if year == 2025:
        # Partial year - estimate based on days elapsed
        days_in_year = (date.today() - date(2025, 1, 1)).days + 1
        return int(days_in_year * 8.5)  # ~8.5 races/day average
    else:
        # Full year - typical UK/Ireland has ~6000-7000 races/year
        return 6500


def get_entity_extraction_rate(db) -> Dict[str, float]:
    """Calculate entity extraction rates from race data"""
    rates = {}

    # Get total races count (primary data source)
    total_races = get_table_count(db, 'ra_races')

    if total_races == 0:
        return {
            'horses': 0.0,
            'jockeys': 0.0,
            'trainers': 0.0,
            'owners': 0.0
        }

    # Get entity counts
    horses = get_table_count(db, 'ra_horses')
    jockeys = get_table_count(db, 'ra_jockeys')
    trainers = get_table_count(db, 'ra_trainers')
    owners = get_table_count(db, 'ra_owners')

    # Calculate extraction rate (entities per race - typically ~10-12 horses per race)
    rates['horses'] = (horses / total_races) if total_races > 0 else 0
    rates['jockeys'] = (jockeys / total_races) if total_races > 0 else 0
    rates['trainers'] = (trainers / total_races) if total_races > 0 else 0
    rates['owners'] = (owners / total_races) if total_races > 0 else 0

    return rates


def get_data_quality_indicators(db) -> Dict[str, any]:
    """Get data quality indicators"""
    quality = {}

    # Check races and runners data
    races_count = get_table_count(db, 'ra_races')
    runners_count = get_table_count(db, 'ra_runners')

    quality['races_loaded'] = races_count > 0
    quality['races_runners_ratio'] = runners_count / races_count if races_count > 0 else 0

    # Check if reference data is loaded
    quality['courses_loaded'] = get_table_count(db, 'ra_courses') > 0
    quality['bookmakers_loaded'] = get_table_count(db, 'ra_bookmakers') > 0

    # Check entity extraction
    quality['entities_extracted'] = (
        get_table_count(db, 'ra_horses') > 0 and
        get_table_count(db, 'ra_jockeys') > 0
    )

    return quality


def get_recommendations(db, quality: Dict) -> list:
    """Generate recommendations based on current state"""
    recommendations = []

    if not quality['courses_loaded']:
        recommendations.append(f"{YELLOW}⚠{RESET} Load reference data first (courses, bookmakers)")

    if not quality['races_loaded']:
        recommendations.append(f"{YELLOW}⚠{RESET} No race data found - run historical backfill")

    if quality['races_runners_ratio'] < 5:  # Typical race has 8-12 runners
        recommendations.append(f"{YELLOW}⚠{RESET} Low runners/race ratio - data collection may be incomplete")

    if not quality['entities_extracted']:
        recommendations.append(f"{YELLOW}⚠{RESET} Entities not extracted - check extraction process")

    races_count = get_table_count(db, 'ra_races')
    if races_count > 0 and races_count < 10000:
        recommendations.append(f"{CYAN}ℹ{RESET} Data collection in progress - keep monitoring")

    if not recommendations:
        recommendations.append(f"{GREEN}✓{RESET} All systems operational")

    return recommendations


class DataProgressMonitor:
    """Comprehensive data progress monitoring dashboard"""

    def __init__(self, refresh_interval: int = 2, focus_year: Optional[int] = None):
        """Initialize monitor"""
        self.config = get_config()
        self.db = SupabaseReferenceClient(self.config.supabase.url, self.config.supabase.service_key)
        self.refresh_interval = refresh_interval
        self.focus_year = focus_year

    def display_dashboard(self):
        """Display comprehensive monitoring dashboard"""
        clear_screen()

        print(f"\n{BOLD}{CYAN}━━━ DARKHORSES DATA COLLECTION DASHBOARD ━━━{RESET}\n")

        # Overall table counts
        print(f"{BOLD}📊 Database Tables:{RESET}\n")

        tables = {
            'Reference Data': [
                ('ra_courses', 'Courses'),
                ('ra_bookmakers', 'Bookmakers'),
            ],
            'Racing Entities': [
                ('ra_horses', 'Horses'),
                ('ra_jockeys', 'Jockeys'),
                ('ra_trainers', 'Trainers'),
                ('ra_owners', 'Owners'),
            ],
            'Racing Data': [
                ('ra_races', 'Races'),
                ('ra_runners', 'Runners'),
            ]
        }

        for category, table_list in tables.items():
            print(f"{DIM}{category}:{RESET}")
            for table, label in table_list:
                count = get_table_count(self.db, table)
                status = f"{GREEN}●{RESET}" if count > 0 else f"{DIM}○{RESET}"
                print(f"  {status} {label:<15} {format_number(count):>12} records")
            print()

        # Year-by-year breakdown
        print(f"{BOLD}{CYAN}━━━ YEAR-BY-YEAR PROGRESS ━━━{RESET}\n")

        year_data = get_year_breakdown(self.db)

        print(f"{'Year':<8} {'Races':<15} {'Runners':<15} {'Expected':<15} {'Status':<10}")
        print("─" * 75)

        for year in range(2015, 2026):
            data = year_data[year]
            expected = estimate_expected_races(year)
            pct = (data['races'] / expected * 100) if expected > 0 else 0

            # Status based on percentage
            if pct >= 90:
                status = f"{GREEN}✓ Complete{RESET}"
            elif pct >= 50:
                status = f"{YELLOW}⟳ In Progress{RESET}"
            elif data['races'] > 0:
                status = f"{YELLOW}⟳ Started{RESET}"
            else:
                status = f"{DIM}○ Not Started{RESET}"

            print(
                f"{year}     "
                f"{format_number(data['races']):<15} "
                f"{format_number(data['runners']):<15} "
                f"{format_number(expected):<15} "
                f"{status}"
            )

        # Entity extraction rates
        print(f"\n{BOLD}{CYAN}━━━ ENTITY EXTRACTION RATES ━━━{RESET}\n")

        extraction_rates = get_entity_extraction_rate(self.db)

        for entity, rate in extraction_rates.items():
            bar_width = 30
            filled = int(bar_width * (rate / 100))
            bar = '█' * filled + '░' * (bar_width - filled)

            color = GREEN if rate > 50 else YELLOW if rate > 20 else RED
            print(f"  {entity.capitalize():<12} {color}[{bar}]{RESET} {rate:5.1f}%")

        # Data quality indicators
        print(f"\n{BOLD}{CYAN}━━━ DATA QUALITY ━━━{RESET}\n")

        quality = get_data_quality_indicators(self.db)

        indicators = [
            ('Reference Data', quality['courses_loaded']),
            ('Race Data Loaded', quality['races_loaded']),
            ('Entity Extraction', quality['entities_extracted']),
        ]

        for label, status in indicators:
            icon = f"{GREEN}✓{RESET}" if status else f"{RED}✗{RESET}"
            print(f"  {icon} {label}")

        # Recommendations
        print(f"\n{BOLD}{CYAN}━━━ RECOMMENDATIONS ━━━{RESET}\n")

        recommendations = get_recommendations(self.db, quality)
        for rec in recommendations:
            print(f"  {rec}")

        # Footer
        print(f"\n{DIM}Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}")
        print(f"{DIM}Refreshing every {self.refresh_interval} seconds... (Press Ctrl+C to exit){RESET}\n")

    def run(self):
        """Run monitoring loop"""
        try:
            while True:
                self.display_dashboard()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print(f"\n\n{DIM}Monitor stopped.{RESET}\n")
            sys.exit(0)


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Monitor data collection progress')
    parser.add_argument('--refresh', type=int, default=2, help='Refresh interval in seconds (default: 2)')
    parser.add_argument('--year', type=int, help='Focus on specific year')

    args = parser.parse_args()

    monitor = DataProgressMonitor(refresh_interval=args.refresh, focus_year=args.year)
    monitor.run()


if __name__ == '__main__':
    main()
