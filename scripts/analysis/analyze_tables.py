"""
Comprehensive Table Analysis Script

Analyzes all 23 ra_ tables to understand:
1. Missing data (columns with NULL values)
2. Partial data (columns partially populated)
3. Data coverage from 2015 to present
4. Population statistics by year
5. Data quality metrics

Can be run standalone or from master_fetcher_controller.py

Usage:
    # Run analysis for all tables
    python3 fetchers/analyze_tables.py

    # Run analysis for specific tables
    python3 fetchers/analyze_tables.py --tables ra_races ra_runners

    # Export results to JSON
    python3 fetchers/analyze_tables.py --output json

    # From controller
    python3 fetchers/master_fetcher_controller.py --mode analyze
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('table_analyzer')


class TableAnalyzer:
    """Comprehensive table analysis for all ra_ tables"""

    # Tables to analyze (all current ra_ tables)
    TABLES = [
        # Master/Reference Tables
        'ra_mst_courses',
        'ra_mst_bookmakers',
        'ra_mst_regions',
        'ra_mst_jockeys',
        'ra_mst_trainers',
        'ra_mst_owners',
        'ra_mst_horses',
        'ra_mst_sires',
        'ra_mst_dams',
        'ra_mst_damsires',
        'ra_horse_pedigree',
        # Transaction Tables
        'ra_races',
        'ra_runners',
        'ra_race_results',
        # Future/Partial Tables
        'ra_entity_combinations',
        'ra_performance_by_distance',
        'ra_performance_by_venue',
        'ra_runner_statistics',
        'ra_runner_supplementary',
        'ra_odds_live',
        'ra_odds_historical',
        'ra_odds_statistics',
        'ra_runner_odds',
    ]

    # Tables with date fields for temporal analysis
    TEMPORAL_TABLES = {
        'ra_races': 'off_dt',
        'ra_runners': 'created_at',  # Use created_at as proxy
        'ra_race_results': 'created_at',
        'ra_mst_horses': 'created_at',
        'ra_horse_pedigree': 'created_at',
    }

    def __init__(self):
        """Initialize analyzer"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.results = {}

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get schema (columns) for a table"""
        try:
            query = f"""
            SELECT
                column_name,
                data_type,
                is_nullable,
                column_default
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name = '{table_name}'
            ORDER BY ordinal_position;
            """

            # Use raw SQL query via Supabase
            result = self.db_client.client.rpc('exec_sql', {'sql': query}).execute()

            if result.data:
                return result.data
            else:
                # Fallback: Get columns from first row
                sample = self.db_client.client.table(table_name).select('*').limit(1).execute()
                if sample.data and len(sample.data) > 0:
                    return [{'column_name': col, 'data_type': 'unknown', 'is_nullable': 'YES', 'column_default': None}
                            for col in sample.data[0].keys()]
                return []

        except Exception as e:
            logger.warning(f"Could not get schema for {table_name}, using fallback: {e}")
            # Fallback: Get columns from first row
            try:
                sample = self.db_client.client.table(table_name).select('*').limit(1).execute()
                if sample.data and len(sample.data) > 0:
                    return [{'column_name': col, 'data_type': 'unknown', 'is_nullable': 'YES', 'column_default': None}
                            for col in sample.data[0].keys()]
            except:
                pass
            return []

    def analyze_column_population(self, table_name: str, column_name: str, total_rows: int) -> Dict:
        """Analyze population statistics for a single column"""
        try:
            # Count non-null values
            result = self.db_client.client.table(table_name).select(column_name, count='exact').not_.is_(column_name, 'null').limit(0).execute()
            populated = result.count if result.count is not None else 0

            # Count null values
            null_count = total_rows - populated

            # Calculate percentage
            pct_populated = (populated / total_rows * 100) if total_rows > 0 else 0

            # Determine status
            if pct_populated == 0:
                status = 'empty'
            elif pct_populated == 100:
                status = 'complete'
            elif pct_populated >= 80:
                status = 'good'
            elif pct_populated >= 50:
                status = 'partial'
            else:
                status = 'sparse'

            return {
                'column': column_name,
                'populated': populated,
                'null_count': null_count,
                'total': total_rows,
                'pct_populated': round(pct_populated, 2),
                'status': status
            }

        except Exception as e:
            logger.error(f"Error analyzing column {table_name}.{column_name}: {e}")
            return {
                'column': column_name,
                'populated': 0,
                'null_count': total_rows,
                'total': total_rows,
                'pct_populated': 0,
                'status': 'error',
                'error': str(e)
            }

    def analyze_temporal_coverage(self, table_name: str, date_column: str) -> Dict:
        """Analyze data coverage by year from 2015 to present"""
        try:
            # Get min and max dates
            result = self.db_client.client.table(table_name).select(date_column).order(date_column, desc=False).limit(1).execute()
            min_date = result.data[0][date_column] if result.data else None

            result = self.db_client.client.table(table_name).select(date_column).order(date_column, desc=True).limit(1).execute()
            max_date = result.data[0][date_column] if result.data else None

            if not min_date or not max_date:
                return {'error': 'No date data available'}

            # Parse dates
            min_date = datetime.fromisoformat(min_date.replace('Z', '+00:00')) if isinstance(min_date, str) else min_date
            max_date = datetime.fromisoformat(max_date.replace('Z', '+00:00')) if isinstance(max_date, str) else max_date

            # Count records by year
            yearly_counts = {}
            start_year = 2015
            end_year = datetime.now().year

            for year in range(start_year, end_year + 1):
                year_start = f"{year}-01-01"
                year_end = f"{year}-12-31"

                try:
                    result = self.db_client.client.table(table_name).select('*', count='exact').gte(date_column, year_start).lte(date_column, year_end).limit(0).execute()
                    yearly_counts[year] = result.count if result.count is not None else 0
                except Exception as e:
                    logger.warning(f"Could not get count for {table_name} year {year}: {e}")
                    yearly_counts[year] = 0

            return {
                'min_date': min_date.isoformat() if hasattr(min_date, 'isoformat') else str(min_date),
                'max_date': max_date.isoformat() if hasattr(max_date, 'isoformat') else str(max_date),
                'yearly_counts': yearly_counts,
                'total_years': len([y for y in yearly_counts.values() if y > 0]),
                'coverage_years': [y for y, count in yearly_counts.items() if count > 0]
            }

        except Exception as e:
            logger.error(f"Error analyzing temporal coverage for {table_name}: {e}")
            return {'error': str(e)}

    def analyze_table(self, table_name: str) -> Dict:
        """Comprehensive analysis of a single table"""
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Analyzing: {table_name}")
        logger.info(f"{'=' * 80}")

        try:
            # Get total row count
            result = self.db_client.client.table(table_name).select('*', count='exact').limit(0).execute()
            total_rows = result.count if result.count is not None else 0

            logger.info(f"Total rows: {total_rows:,}")

            if total_rows == 0:
                return {
                    'table': table_name,
                    'total_rows': 0,
                    'status': 'empty',
                    'columns': [],
                    'temporal_coverage': None
                }

            # Get table schema
            schema = self.get_table_schema(table_name)
            logger.info(f"Total columns: {len(schema)}")

            # Analyze each column
            column_analysis = []
            for col_info in schema:
                col_name = col_info['column_name']
                logger.info(f"  Analyzing column: {col_name}")

                analysis = self.analyze_column_population(table_name, col_name, total_rows)
                analysis['data_type'] = col_info.get('data_type', 'unknown')
                column_analysis.append(analysis)

            # Temporal analysis if applicable
            temporal_coverage = None
            if table_name in self.TEMPORAL_TABLES:
                date_column = self.TEMPORAL_TABLES[table_name]
                logger.info(f"  Performing temporal analysis on column: {date_column}")
                temporal_coverage = self.analyze_temporal_coverage(table_name, date_column)

            # Categorize columns
            complete_cols = [c for c in column_analysis if c['status'] == 'complete']
            good_cols = [c for c in column_analysis if c['status'] == 'good']
            partial_cols = [c for c in column_analysis if c['status'] == 'partial']
            sparse_cols = [c for c in column_analysis if c['status'] == 'sparse']
            empty_cols = [c for c in column_analysis if c['status'] == 'empty']

            # Overall table status
            if len(empty_cols) == len(column_analysis):
                table_status = 'empty'
            elif len(complete_cols) + len(good_cols) >= len(column_analysis) * 0.8:
                table_status = 'good'
            elif len(complete_cols) + len(good_cols) >= len(column_analysis) * 0.5:
                table_status = 'partial'
            else:
                table_status = 'needs_attention'

            return {
                'table': table_name,
                'total_rows': total_rows,
                'total_columns': len(column_analysis),
                'status': table_status,
                'columns': column_analysis,
                'summary': {
                    'complete_columns': len(complete_cols),
                    'good_columns': len(good_cols),
                    'partial_columns': len(partial_cols),
                    'sparse_columns': len(sparse_cols),
                    'empty_columns': len(empty_cols)
                },
                'temporal_coverage': temporal_coverage,
                'analyzed_at': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error analyzing table {table_name}: {e}", exc_info=True)
            return {
                'table': table_name,
                'status': 'error',
                'error': str(e)
            }

    def analyze_all(self, tables: Optional[List[str]] = None) -> Dict:
        """Analyze all tables or specified list"""
        tables_to_analyze = tables if tables else self.TABLES

        logger.info(f"\n{'=' * 80}")
        logger.info(f"COMPREHENSIVE TABLE ANALYSIS")
        logger.info(f"Analyzing {len(tables_to_analyze)} tables")
        logger.info(f"{'=' * 80}\n")

        results = {
            'analysis_date': datetime.now().isoformat(),
            'tables_analyzed': len(tables_to_analyze),
            'tables': []
        }

        for table_name in tables_to_analyze:
            analysis = self.analyze_table(table_name)
            results['tables'].append(analysis)
            self.results[table_name] = analysis

        # Generate summary
        results['summary'] = self.generate_summary(results['tables'])

        return results

    def generate_summary(self, table_results: List[Dict]) -> Dict:
        """Generate overall summary"""
        summary = {
            'total_tables': len(table_results),
            'tables_by_status': defaultdict(int),
            'total_rows': 0,
            'total_columns': 0,
            'column_status_totals': defaultdict(int)
        }

        for table in table_results:
            if 'error' in table:
                summary['tables_by_status']['error'] += 1
                continue

            summary['tables_by_status'][table['status']] += 1
            summary['total_rows'] += table.get('total_rows', 0)
            summary['total_columns'] += table.get('total_columns', 0)

            if 'summary' in table:
                for key, value in table['summary'].items():
                    summary['column_status_totals'][key] += value

        # Convert defaultdict to regular dict
        summary['tables_by_status'] = dict(summary['tables_by_status'])
        summary['column_status_totals'] = dict(summary['column_status_totals'])

        return summary

    def print_summary(self, results: Dict):
        """Print human-readable summary"""
        print("\n" + "=" * 80)
        print("ANALYSIS SUMMARY")
        print("=" * 80)

        summary = results['summary']

        print(f"\nTotal Tables Analyzed: {summary['total_tables']}")
        print(f"Total Rows: {summary['total_rows']:,}")
        print(f"Total Columns: {summary['total_columns']:,}")

        print("\nTables by Status:")
        for status, count in summary['tables_by_status'].items():
            emoji = {'good': '✅', 'partial': '⚠️', 'needs_attention': '❌', 'empty': '📭', 'error': '🔥'}.get(status, '❓')
            print(f"  {emoji} {status.upper()}: {count}")

        print("\nColumn Status Totals:")
        for status, count in summary['column_status_totals'].items():
            print(f"  {status.replace('_', ' ').title()}: {count}")

        print("\n" + "=" * 80)
        print("DETAILED TABLE RESULTS")
        print("=" * 80)

        for table in results['tables']:
            self.print_table_summary(table)

    def print_table_summary(self, table: Dict):
        """Print summary for a single table"""
        print(f"\n📊 {table['table']}")
        print(f"   Status: {table['status'].upper()}")
        print(f"   Rows: {table.get('total_rows', 0):,}")
        print(f"   Columns: {table.get('total_columns', 0)}")

        if 'summary' in table:
            s = table['summary']
            print(f"   Complete: {s.get('complete_columns', 0)}, Good: {s.get('good_columns', 0)}, " +
                  f"Partial: {s.get('partial_columns', 0)}, Sparse: {s.get('sparse_columns', 0)}, " +
                  f"Empty: {s.get('empty_columns', 0)}")

        if 'temporal_coverage' in table and table['temporal_coverage'] and 'error' not in table['temporal_coverage']:
            tc = table['temporal_coverage']
            print(f"   Date Range: {tc.get('min_date', 'N/A')} to {tc.get('max_date', 'N/A')}")
            print(f"   Coverage Years: {tc.get('total_years', 0)} years ({', '.join(map(str, tc.get('coverage_years', [])))})")

        # Show problematic columns
        if 'columns' in table:
            sparse_cols = [c for c in table['columns'] if c['status'] in ['sparse', 'empty']]
            if sparse_cols and len(sparse_cols) <= 10:  # Only show if not too many
                print(f"   ⚠️  Sparse/Empty Columns: {', '.join([c['column'] for c in sparse_cols])}")

    def export_json(self, results: Dict, filename: str = None):
        """Export results to JSON file"""
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"logs/table_analysis_{timestamp}.json"

        # Ensure logs directory exists
        os.makedirs('logs', exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\nResults exported to: {filename}")
        return filename


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Comprehensive table analysis')
    parser.add_argument('--tables', nargs='+', help='Specific tables to analyze')
    parser.add_argument('--output', choices=['console', 'json', 'both'], default='both',
                       help='Output format')
    parser.add_argument('--output-file', help='Output JSON filename')

    args = parser.parse_args()

    analyzer = TableAnalyzer()
    results = analyzer.analyze_all(tables=args.tables)

    if args.output in ['console', 'both']:
        analyzer.print_summary(results)

    if args.output in ['json', 'both']:
        filename = analyzer.export_json(results, filename=args.output_file)
        print(f"\n✅ Analysis complete. Results saved to: {filename}")

    return results


if __name__ == '__main__':
    main()
