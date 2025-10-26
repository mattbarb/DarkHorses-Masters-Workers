"""
Analyze Backfill Requirements for RA Tables

This script analyzes the current state of all RA tables and provides detailed
estimates for backfilling from 2015 onwards.

USAGE:
    python3 scripts/analyze_backfill_requirements.py
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
from datetime import datetime, timedelta
from typing import Dict, List
from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('analyze_backfill')


class BackfillAnalyzer:
    """Analyze backfill requirements for all RA tables"""

    def __init__(self):
        """Initialize analyzer"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

    def get_table_stats(self, table_name: str, id_column: str, date_column: str = None) -> Dict:
        """
        Get comprehensive statistics for a table

        Args:
            table_name: Name of the table
            id_column: Primary key column
            date_column: Date column for temporal analysis

        Returns:
            Statistics dictionary
        """
        stats = {
            'table': table_name,
            'total_records': 0,
            'by_year': {},
            'earliest_date': None,
            'latest_date': None,
            'date_range_days': 0
        }

        try:
            # Get total count
            result = self.db_client.client.table(table_name).select('*', count='exact').limit(1).execute()
            stats['total_records'] = result.count if hasattr(result, 'count') else 0

            if date_column and stats['total_records'] > 0:
                # Get earliest and latest dates
                earliest = self.db_client.client.table(table_name)\
                    .select(date_column)\
                    .order(date_column)\
                    .limit(1)\
                    .execute()

                latest = self.db_client.client.table(table_name)\
                    .select(date_column)\
                    .order(date_column, desc=True)\
                    .limit(1)\
                    .execute()

                if earliest.data and latest.data:
                    stats['earliest_date'] = earliest.data[0].get(date_column)
                    stats['latest_date'] = latest.data[0].get(date_column)

                    # Calculate date range
                    if stats['earliest_date'] and stats['latest_date']:
                        try:
                            # Handle both date and timestamp formats
                            earliest_str = stats['earliest_date'].split('T')[0]
                            latest_str = stats['latest_date'].split('T')[0]

                            earliest_dt = datetime.strptime(earliest_str, '%Y-%m-%d')
                            latest_dt = datetime.strptime(latest_str, '%Y-%m-%d')

                            stats['date_range_days'] = (latest_dt - earliest_dt).days
                        except:
                            pass

                # Get counts by year (2015-2025)
                for year in range(2015, 2026):
                    start_date = f"{year}-01-01"
                    end_date = f"{year}-12-31"

                    # For timestamp columns
                    if date_column in ['created_at', 'fetched_at', 'updated_at']:
                        start_date = f"{year}-01-01T00:00:00"
                        end_date = f"{year}-12-31T23:59:59"

                    year_result = self.db_client.client.table(table_name)\
                        .select('*', count='exact')\
                        .gte(date_column, start_date)\
                        .lte(date_column, end_date)\
                        .limit(1)\
                        .execute()

                    year_count = year_result.count if hasattr(year_result, 'count') else 0
                    stats['by_year'][year] = year_count

        except Exception as e:
            logger.error(f"Error analyzing {table_name}: {e}")
            stats['error'] = str(e)

        return stats

    def analyze_runner_coverage(self) -> Dict:
        """
        Analyze runner coverage - critical for understanding the gap

        Returns:
            Coverage analysis
        """
        logger.info("Analyzing runner coverage...")

        try:
            # Get all races
            races_result = self.db_client.client.table('ra_mst_races')\
                .select('race_id, race_date')\
                .execute()

            total_races = len(races_result.data)
            race_ids = set([row['race_id'] for row in races_result.data])

            # Get races with runners
            runners_result = self.db_client.client.table('ra_mst_runners')\
                .select('race_id')\
                .execute()

            race_ids_with_runners = set([row['race_id'] for row in runners_result.data])
            races_with_runners_count = len(race_ids_with_runners)

            # Calculate gap
            races_without_runners = race_ids - race_ids_with_runners
            races_without_runners_count = len(races_without_runners)

            # Get runner count
            total_runners = len(runners_result.data)

            # Estimate expected runners (avg ~10 per race)
            expected_runners = total_races * 10
            runner_deficit = expected_runners - total_runners

            coverage = {
                'total_races': total_races,
                'races_with_runners': races_with_runners_count,
                'races_without_runners': races_without_runners_count,
                'coverage_percentage': (races_with_runners_count / total_races * 100) if total_races > 0 else 0,
                'total_runners': total_runners,
                'expected_runners': expected_runners,
                'runner_deficit': runner_deficit
            }

            return coverage

        except Exception as e:
            logger.error(f"Error analyzing runner coverage: {e}")
            return {'error': str(e)}

    def estimate_backfill_requirements(self, start_date: str = '2015-01-01', end_date: str = None) -> Dict:
        """
        Estimate API calls and time required for backfill

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today

        Returns:
            Estimation dictionary
        """
        if not end_date:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

        # Calculate date range
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        total_days = (end_dt - start_dt).days + 1

        # Estimate races per day (UK + IRE)
        avg_races_per_day = 12  # Conservative estimate

        # Calculate estimates
        total_races_estimated = total_days * avg_races_per_day
        total_runners_estimated = total_races_estimated * 10  # Avg 10 runners per race

        # API calls required
        api_calls_racecards = total_days  # 1 call per day for racecards

        # Estimate new horses (horses not yet in database)
        # Assume 30% of runners are new horses (conservative)
        new_horses_estimated = int(total_runners_estimated * 0.3)

        # Pro endpoint calls for horse enrichment
        api_calls_enrichment = new_horses_estimated

        # Total API calls
        total_api_calls = api_calls_racecards + api_calls_enrichment

        # Time estimates (2 requests/second = 0.5s per request)
        time_seconds = total_api_calls * 0.5
        time_hours = time_seconds / 3600
        time_days = time_hours / 24

        # Storage estimates
        races_storage_mb = (total_races_estimated * 5) / 1024  # ~5KB per race
        runners_storage_mb = (total_runners_estimated * 3) / 1024  # ~3KB per runner
        total_storage_mb = races_storage_mb + runners_storage_mb
        total_storage_gb = total_storage_mb / 1024

        estimates = {
            'date_range': {
                'start_date': start_date,
                'end_date': end_date,
                'total_days': total_days
            },
            'data_estimates': {
                'races': total_races_estimated,
                'runners': total_runners_estimated,
                'new_horses': new_horses_estimated
            },
            'api_calls': {
                'racecards': api_calls_racecards,
                'enrichment': api_calls_enrichment,
                'total': total_api_calls
            },
            'time_estimates': {
                'seconds': int(time_seconds),
                'minutes': int(time_seconds / 60),
                'hours': round(time_hours, 1),
                'days': round(time_days, 1)
            },
            'storage_estimates': {
                'races_mb': round(races_storage_mb, 1),
                'runners_mb': round(runners_storage_mb, 1),
                'total_mb': round(total_storage_mb, 1),
                'total_gb': round(total_storage_gb, 2)
            }
        }

        return estimates

    def run_full_analysis(self) -> Dict:
        """
        Run complete analysis of all tables and backfill requirements

        Returns:
            Complete analysis dictionary
        """
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE RA TABLES BACKFILL ANALYSIS")
        logger.info("=" * 80)

        analysis = {
            'timestamp': datetime.utcnow().isoformat(),
            'tables': {},
            'runner_coverage': {},
            'backfill_estimates': {}
        }

        # Define tables to analyze
        tables = [
            ('ra_races', 'race_id', 'race_date'),
            ('ra_mst_runners', 'runner_id', 'fetched_at'),
            ('ra_horses', 'horse_id', 'created_at'),
            ('ra_jockeys', 'jockey_id', 'created_at'),
            ('ra_trainers', 'trainer_id', 'created_at'),
            ('ra_owners', 'owner_id', 'created_at'),
            ('ra_horse_pedigree', 'horse_id', 'created_at'),
            ('ra_courses', 'course_id', None),
            ('ra_bookmakers', 'bookmaker_id', None)
        ]

        # Analyze each table
        for table_name, id_column, date_column in tables:
            logger.info(f"\nAnalyzing {table_name}...")
            stats = self.get_table_stats(table_name, id_column, date_column)
            analysis['tables'][table_name] = stats

            # Print summary
            total = stats.get('total_records', 0)
            logger.info(f"  Total records: {total:,}")

            if stats.get('earliest_date'):
                logger.info(f"  Date range: {stats['earliest_date']} to {stats['latest_date']}")
                logger.info(f"  Span: {stats['date_range_days']} days")

        # Analyze runner coverage (CRITICAL)
        logger.info("\nAnalyzing runner coverage...")
        runner_coverage = self.analyze_runner_coverage()
        analysis['runner_coverage'] = runner_coverage

        if 'error' not in runner_coverage:
            logger.info(f"  Total races: {runner_coverage['total_races']:,}")
            logger.info(f"  Races with runners: {runner_coverage['races_with_runners']:,}")
            logger.info(f"  Races WITHOUT runners: {runner_coverage['races_without_runners']:,}")
            logger.info(f"  Coverage: {runner_coverage['coverage_percentage']:.2f}%")
            logger.info(f"  Total runners: {runner_coverage['total_runners']:,}")
            logger.info(f"  Expected runners: {runner_coverage['expected_runners']:,}")
            logger.info(f"  Runner deficit: {runner_coverage['runner_deficit']:,}")

        # Estimate backfill requirements
        logger.info("\nEstimating backfill requirements...")
        estimates = self.estimate_backfill_requirements()
        analysis['backfill_estimates'] = estimates

        logger.info(f"  Date range: {estimates['date_range']['start_date']} to {estimates['date_range']['end_date']}")
        logger.info(f"  Total days: {estimates['date_range']['total_days']:,}")
        logger.info(f"  Estimated races: {estimates['data_estimates']['races']:,}")
        logger.info(f"  Estimated runners: {estimates['data_estimates']['runners']:,}")
        logger.info(f"  Estimated new horses: {estimates['data_estimates']['new_horses']:,}")
        logger.info(f"  Total API calls: {estimates['api_calls']['total']:,}")
        logger.info(f"  Estimated time: {estimates['time_estimates']['days']:.1f} days ({estimates['time_estimates']['hours']:.1f} hours)")
        logger.info(f"  Storage required: {estimates['storage_estimates']['total_gb']:.2f} GB")

        # Save analysis to file
        output_file = Path(__file__).parent.parent / 'logs' / 'backfill_analysis.json'
        try:
            with open(output_file, 'w') as f:
                json.dump(analysis, f, indent=2)
            logger.info(f"\nAnalysis saved to: {output_file}")
        except Exception as e:
            logger.error(f"Error saving analysis: {e}")

        return analysis

    def print_recommendations(self, analysis: Dict):
        """
        Print recommendations based on analysis

        Args:
            analysis: Analysis dictionary from run_full_analysis
        """
        logger.info("\n" + "=" * 80)
        logger.info("RECOMMENDATIONS")
        logger.info("=" * 80)

        runner_coverage = analysis.get('runner_coverage', {})
        estimates = analysis.get('backfill_estimates', {})

        if runner_coverage.get('coverage_percentage', 100) < 50:
            logger.info("\n🚨 CRITICAL: Runner coverage is extremely low!")
            logger.info("   Priority: Backfill ra_mst_runners table immediately")
            logger.info("   This is blocking downstream analysis and AI model training")

        logger.info("\n📋 EXECUTION STRATEGY:")
        logger.info("   1. Run backfill in chunks (e.g., by year) to manage risk")
        logger.info("   2. Start with most recent year and work backwards")
        logger.info("   3. Use checkpoint/resume feature for long-running backfills")
        logger.info("   4. Monitor progress with monitor_backfill.py script")

        time_days = estimates.get('time_estimates', {}).get('days', 0)
        if time_days > 7:
            logger.info("\n⏰ TIMING RECOMMENDATIONS:")
            logger.info(f"   Estimated duration: {time_days:.1f} days")
            logger.info("   Recommended: Run on dedicated server/instance")
            logger.info("   Alternative: Split into yearly chunks (process in parallel if possible)")
            logger.info("   Schedule: Run overnight/weekends to minimize impact")

        storage_gb = estimates.get('storage_estimates', {}).get('total_gb', 0)
        if storage_gb > 1:
            logger.info("\n💾 STORAGE RECOMMENDATIONS:")
            logger.info(f"   Estimated storage: {storage_gb:.2f} GB")
            logger.info("   Verify Supabase plan has sufficient storage")
            logger.info("   Monitor database size during backfill")

        logger.info("\n🛠️ EXAMPLE COMMANDS:")
        logger.info("\n   # Analyze current state")
        logger.info("   python3 scripts/backfill_all_ra_tables_2015_2025.py --analyze")

        logger.info("\n   # Test with 7 days")
        logger.info("   python3 scripts/backfill_all_ra_tables_2015_2025.py --test")

        logger.info("\n   # Backfill 2024 only")
        logger.info("   python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date 2024-01-01 --end-date 2024-12-31")

        logger.info("\n   # Full backfill from 2015 (use with caution!)")
        logger.info("   python3 scripts/backfill_all_ra_tables_2015_2025.py --start-date 2015-01-01")

        logger.info("\n   # Resume from checkpoint")
        logger.info("   python3 scripts/backfill_all_ra_tables_2015_2025.py --resume")

        logger.info("\n⚠️ IMPORTANT NOTES:")
        logger.info("   - Racing API rate limit: 2 requests/second (strictly enforced)")
        logger.info("   - Racecards endpoint goes back to 2015 (confirmed)")
        logger.info("   - Results endpoint only goes back 12 months (can't use for historical)")
        logger.info("   - Enrichment happens automatically for new horses")
        logger.info("   - All operations are UPSERT-safe (can re-run without duplicates)")

        logger.info("\n" + "=" * 80)


def main():
    """Main execution"""
    analyzer = BackfillAnalyzer()

    # Run full analysis
    analysis = analyzer.run_full_analysis()

    # Print recommendations
    analyzer.print_recommendations(analysis)

    logger.info("\n✅ Analysis complete!")
    logger.info("   Review recommendations above before starting backfill")


if __name__ == '__main__':
    main()
