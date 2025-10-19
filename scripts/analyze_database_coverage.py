#!/usr/bin/env python3
"""
Database Coverage Analysis
Analyze what data exists in each table and date coverage
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from datetime import datetime

# ANSI colors
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
DIM = '\033[2m'
RESET = '\033[0m'


def format_number(num):
    """Format number with thousands separator"""
    return f"{num:,}"


def get_table_summary(db, table_name):
    """Get summary statistics for a table"""
    try:
        # Get total count
        result = db.client.table(table_name).select('*', count='exact').limit(1).execute()
        total = result.count or 0

        return {'total': total, 'error': None}
    except Exception as e:
        return {'total': 0, 'error': str(e)}


def get_date_range(db, table_name, date_column='race_date'):
    """Get date range for tables with date columns"""
    try:
        # Get min and max dates
        result = db.client.table(table_name).select(date_column).order(date_column, desc=False).limit(1).execute()
        min_date = result.data[0][date_column] if result.data else None

        result = db.client.table(table_name).select(date_column).order(date_column, desc=True).limit(1).execute()
        max_date = result.data[0][date_column] if result.data else None

        return {'min': min_date, 'max': max_date, 'error': None}
    except Exception as e:
        return {'min': None, 'max': None, 'error': str(e)}


def get_year_breakdown(db, table_name, date_column='race_date'):
    """Get row counts by year"""
    breakdown = {}

    for year in range(2015, 2026):
        try:
            result = db.client.table(table_name).select('*', count='exact') \
                .gte(date_column, f'{year}-01-01') \
                .lte(date_column, f'{year}-12-31') \
                .limit(1).execute()
            breakdown[year] = result.count or 0
        except:
            breakdown[year] = 0

    return breakdown


def get_sample_data(db, table_name, limit=3):
    """Get sample records from table"""
    try:
        result = db.client.table(table_name).select('*').limit(limit).execute()
        return {'data': result.data, 'error': None}
    except Exception as e:
        return {'data': [], 'error': str(e)}


def analyze_database(db):
    """Analyze all tables in database"""

    print(f"\n{BOLD}{CYAN}━━━ DATABASE COVERAGE ANALYSIS ━━━{RESET}")
    print(f"{DIM}Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{RESET}\n")

    # Define tables to analyze
    tables = {
        'Reference Data': [
            ('ra_courses', None, ['course_id', 'name', 'region']),
            ('ra_bookmakers', None, ['bookmaker_id', 'name'])
        ],
        'Entity Data': [
            ('ra_horses', None, ['horse_id', 'name', 'region']),
            ('ra_jockeys', None, ['jockey_id', 'name']),
            ('ra_trainers', None, ['trainer_id', 'name']),
            ('ra_owners', None, ['owner_id', 'name']),
            ('ra_horse_pedigree', None, ['horse_id', 'sire', 'dam'])
        ],
        'Racing Data': [
            ('ra_races', 'race_date', ['race_id', 'race_date', 'course_name', 'race_name']),
            ('ra_runners', 'race_date', ['runner_id', 'race_id', 'horse_name', 'jockey_name', 'position'])
        ]
    }

    overall_stats = {}

    for category, table_list in tables.items():
        print(f"{BOLD}{category}:{RESET}\n")

        for table_info in table_list:
            table_name = table_info[0]
            date_column = table_info[1]
            sample_cols = table_info[2]

            # Get summary
            summary = get_table_summary(db, table_name)

            if summary['error']:
                print(f"  {table_name}: {DIM}Error - {summary['error']}{RESET}")
                continue

            overall_stats[table_name] = summary

            # Basic info
            total = summary['total']
            if total > 0:
                status = f"{GREEN}●{RESET}"
            else:
                status = f"{DIM}○{RESET}"

            print(f"  {status} {table_name:<20} {format_number(total):>15} records")

            # Date range if applicable
            if date_column and total > 0:
                date_range = get_date_range(db, table_name, date_column)
                if date_range['min'] and date_range['max']:
                    print(f"     {DIM}Date Range: {date_range['min']} to {date_range['max']}{RESET}")

                    # Year breakdown
                    year_breakdown = get_year_breakdown(db, table_name, date_column)
                    years_with_data = [year for year, count in year_breakdown.items() if count > 0]
                    if years_with_data:
                        print(f"     {DIM}Years: {min(years_with_data)}-{max(years_with_data)} " +
                              f"({len(years_with_data)} years){RESET}")

            print()

        print()

    # Overall summary
    print(f"{BOLD}{CYAN}━━━ SUMMARY BY YEAR ━━━{RESET}\n")

    # Analyze ra_races by year (primary data table)
    if overall_stats.get('ra_races', {}).get('total', 0) > 0:
        print(f"{BOLD}Race Data Coverage:{RESET}\n")
        year_breakdown = get_year_breakdown(db, 'ra_races', 'race_date')

        print(f"{'Year':<8} {'Races':<15} {'Status':<20}")
        print("─" * 50)

        for year in range(2015, 2026):
            count = year_breakdown[year]
            if count > 0:
                status = f"{GREEN}✓ Has Data{RESET}"
                print(f"{year}     {format_number(count):<15} {status}")
            else:
                status = f"{DIM}○ No Data{RESET}"
                print(f"{year}     {format_number(count):<15} {status}")

        print("\n")

    # Data quality indicators
    print(f"{BOLD}{CYAN}━━━ DATA QUALITY INDICATORS ━━━{RESET}\n")

    # Check ratios
    races_count = overall_stats.get('ra_races', {}).get('total', 0)
    runners_count = overall_stats.get('ra_runners', {}).get('total', 0)
    horses_count = overall_stats.get('ra_horses', {}).get('total', 0)

    if races_count > 0:
        runners_per_race = runners_count / races_count
        print(f"  Average runners per race: {runners_per_race:.1f}")
        if runners_per_race < 5:
            print(f"    {YELLOW}⚠ Low - expected 8-12 runners per race{RESET}")
        elif runners_per_race >= 8:
            print(f"    {GREEN}✓ Good coverage{RESET}")

    if runners_count > 0 and horses_count > 0:
        unique_ratio = horses_count / runners_count
        print(f"  Unique horses ratio: {unique_ratio:.2%}")
        print(f"    {DIM}({format_number(horses_count)} unique horses in {format_number(runners_count)} runner entries){RESET}")

    print("\n")


def main():
    """Main execution"""
    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

    try:
        analyze_database(db)
    except Exception as e:
        print(f"Error analyzing database: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
