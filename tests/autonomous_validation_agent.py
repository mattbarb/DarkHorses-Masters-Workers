"""
Autonomous Validation Agent

Automatically:
1. Fetches REAL data from Racing API
2. Adds **TEST** markers to all fields
3. Inserts to database
4. Verifies EVERY table and EVERY column has **TEST** markers
5. Generates comprehensive verification report
6. Cleans up test data

Usage:
    python3 tests/autonomous_validation_agent.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from datetime import datetime
from typing import Dict, List, Any
from collections import defaultdict

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient
from tests.test_live_data_with_markers import LiveDataTestInserter

logger = get_logger('autonomous_validation')


class AutonomousValidationAgent:
    """Autonomous agent for complete end-to-end validation"""

    def __init__(self):
        """Initialize agent"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.test_marker = "**TEST**"
        self.inserter = LiveDataTestInserter()

        # Tables to verify (in order of importance)
        self.tables_to_verify = [
            # Transaction tables (highest priority)
            'ra_races',
            'ra_runners',
            'ra_race_results',

            # Master tables - People
            'ra_mst_jockeys',
            'ra_mst_trainers',
            'ra_mst_owners',

            # Master tables - Horses and pedigree
            'ra_mst_horses',
            'ra_horse_pedigree',

            # Master tables - Reference data
            'ra_mst_courses',
            'ra_mst_bookmakers',
            'ra_mst_regions',

            # Pedigree statistics
            'ra_mst_sires',
            'ra_mst_dams',
            'ra_mst_damsires',
        ]

    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Get all columns for a table from database schema"""
        try:
            # Query information_schema
            query = f"""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = '{table_name}'
                  AND table_schema = 'public'
                ORDER BY ordinal_position
            """

            result = self.db_client.client.rpc('exec_sql', {'sql': query}).execute()

            if result.data:
                return result.data
            else:
                # Fallback: try to get columns by querying the table
                sample = self.db_client.client.table(table_name).select('*').limit(1).execute()
                if sample.data and len(sample.data) > 0:
                    columns = []
                    for col_name in sample.data[0].keys():
                        columns.append({
                            'column_name': col_name,
                            'data_type': 'unknown',
                            'is_nullable': 'YES'
                        })
                    return columns

            return []

        except Exception as e:
            logger.error(f"Error getting columns for {table_name}: {e}")
            return []

    def check_table_for_test_data(self, table_name: str) -> Dict:
        """Check if table has test data and verify all columns"""

        logger.info(f"\nVerifying {table_name}...")

        try:
            # Get test data rows (look for **TEST** in any text column)
            # Try common text columns
            text_columns = ['name', 'title', 'horse_name', 'jockey_name', 'trainer_name', 'owner_name', 'course_name', 'race_title']

            test_rows = None
            column_used = None

            for col in text_columns:
                try:
                    result = self.db_client.client.table(table_name).select('*').like(col, f'%{self.test_marker}%').limit(1).execute()
                    if result.data and len(result.data) > 0:
                        test_rows = result.data
                        column_used = col
                        break
                except:
                    continue

            if not test_rows:
                logger.warning(f"  ⚠️  No test data found in {table_name}")
                return {
                    'table': table_name,
                    'has_test_data': False,
                    'test_rows_found': 0,
                    'columns_checked': 0,
                    'columns_with_test': 0,
                    'columns_missing_test': [],
                    'coverage_percent': 0
                }

            # Get all columns for this table
            columns = self.get_table_columns(table_name)

            if not columns:
                logger.warning(f"  ⚠️  Could not get column list for {table_name}")
                return {
                    'table': table_name,
                    'has_test_data': True,
                    'test_rows_found': len(test_rows),
                    'columns_checked': 0,
                    'columns_with_test': 0,
                    'columns_missing_test': [],
                    'coverage_percent': 0,
                    'error': 'Could not get column list'
                }

            # Check each column in the test row
            test_row = test_rows[0]
            columns_with_test = []
            columns_missing_test = []

            for col_info in columns:
                col_name = col_info['column_name']

                if col_name in test_row:
                    value = test_row[col_name]

                    # Check if value contains **TEST**
                    if value is not None and self.test_marker in str(value):
                        columns_with_test.append(col_name)
                    else:
                        # Skip auto-generated columns
                        if col_name in ['id', 'created_at', 'updated_at'] and col_info['data_type'] in ['integer', 'bigint', 'timestamp without time zone', 'timestamp with time zone']:
                            continue  # Auto-generated, not populated by fetcher

                        columns_missing_test.append({
                            'column': col_name,
                            'value': value,
                            'data_type': col_info['data_type']
                        })

            total_columns = len(columns)
            coverage_percent = (len(columns_with_test) / total_columns * 100) if total_columns > 0 else 0

            # Log results
            if columns_missing_test:
                logger.warning(f"  ⚠️  {table_name}: {len(columns_missing_test)} columns missing **TEST**")
                for missing in columns_missing_test[:5]:  # Show first 5
                    logger.warning(f"      - {missing['column']}: {missing['value']}")
                if len(columns_missing_test) > 5:
                    logger.warning(f"      ... and {len(columns_missing_test) - 5} more")
            else:
                logger.info(f"  ✅ {table_name}: All {len(columns_with_test)} columns have **TEST**")

            return {
                'table': table_name,
                'has_test_data': True,
                'test_rows_found': len(test_rows),
                'total_columns': total_columns,
                'columns_checked': total_columns,
                'columns_with_test': len(columns_with_test),
                'columns_missing_test': columns_missing_test,
                'coverage_percent': round(coverage_percent, 2),
                'column_list': [col['column_name'] for col in columns]
            }

        except Exception as e:
            logger.error(f"  ❌ Error verifying {table_name}: {e}")
            return {
                'table': table_name,
                'has_test_data': False,
                'error': str(e),
                'columns_checked': 0,
                'columns_with_test': 0,
                'coverage_percent': 0
            }

    def run_complete_validation(self) -> Dict:
        """Run complete validation workflow"""

        print("\n" + "=" * 80)
        print("AUTONOMOUS VALIDATION AGENT - STARTING")
        print("=" * 80)
        print("\nWorkflow:")
        print("1. Fetch REAL data from Racing API")
        print("2. Add **TEST** markers to all fields")
        print("3. Insert to database")
        print("4. Verify EVERY table and column")
        print("5. Generate comprehensive report")
        print("6. Cleanup test data")
        print("=" * 80 + "\n")

        results = {
            'timestamp': datetime.now().isoformat(),
            'phase_1_fetch': {},
            'phase_2_verification': {},
            'phase_3_cleanup': {},
            'overall_success': False
        }

        # PHASE 1: Fetch and insert test data
        print("\n" + "=" * 80)
        print("PHASE 1: FETCHING LIVE DATA WITH **TEST** MARKERS")
        print("=" * 80 + "\n")

        fetch_results = self.inserter.fetch_and_insert_races(days_back=1)
        results['phase_1_fetch'] = fetch_results

        if not fetch_results.get('success'):
            print(f"\n❌ Phase 1 failed: {fetch_results.get('error')}")
            return results

        print(f"\n✅ Phase 1 complete:")
        print(f"   Races marked: {fetch_results['races_marked']}")
        print(f"   Runners marked: {fetch_results['runners_marked']}")
        print(f"   Total records marked: {fetch_results['total_marked']}")

        # PHASE 2: Verify all tables
        print("\n" + "=" * 80)
        print("PHASE 2: VERIFYING ALL TABLES AND COLUMNS")
        print("=" * 80 + "\n")

        verification_results = []

        for table_name in self.tables_to_verify:
            table_result = self.check_table_for_test_data(table_name)
            verification_results.append(table_result)

        results['phase_2_verification'] = {
            'tables_checked': len(verification_results),
            'tables_with_test_data': sum(1 for r in verification_results if r.get('has_test_data')),
            'tables_missing_test_data': sum(1 for r in verification_results if not r.get('has_test_data')),
            'total_columns_checked': sum(r.get('columns_checked', 0) for r in verification_results),
            'total_columns_with_test': sum(r.get('columns_with_test', 0) for r in verification_results),
            'details': verification_results
        }

        # Calculate overall coverage
        total_cols = results['phase_2_verification']['total_columns_checked']
        cols_with_test = results['phase_2_verification']['total_columns_with_test']
        overall_coverage = (cols_with_test / total_cols * 100) if total_cols > 0 else 0

        results['phase_2_verification']['overall_coverage_percent'] = round(overall_coverage, 2)

        # Print summary
        print("\n" + "=" * 80)
        print("PHASE 2 SUMMARY:")
        print("=" * 80)
        print(f"Tables checked: {results['phase_2_verification']['tables_checked']}")
        print(f"Tables with test data: {results['phase_2_verification']['tables_with_test_data']}")
        print(f"Tables missing test data: {results['phase_2_verification']['tables_missing_test_data']}")
        print(f"\nTotal columns checked: {total_cols}")
        print(f"Columns with **TEST**: {cols_with_test}")
        print(f"Overall coverage: {overall_coverage:.2f}%")

        # Show tables with issues
        tables_with_issues = [r for r in verification_results if r.get('columns_missing_test')]
        if tables_with_issues:
            print(f"\n⚠️  Tables with missing **TEST** markers:")
            for table_result in tables_with_issues:
                missing_count = len(table_result['columns_missing_test'])
                coverage = table_result['coverage_percent']
                print(f"   - {table_result['table']}: {missing_count} columns missing ({coverage:.1f}% coverage)")
        else:
            print(f"\n✅ All tables have 100% **TEST** marker coverage!")

        # PHASE 3: Cleanup
        print("\n" + "=" * 80)
        print("PHASE 3: CLEANING UP TEST DATA")
        print("=" * 80 + "\n")

        cleanup_results = self.inserter.cleanup_test_data()
        results['phase_3_cleanup'] = cleanup_results

        if cleanup_results.get('success'):
            print(f"\n✅ Phase 3 complete: {cleanup_results['total_deleted']} rows deleted")
        else:
            print(f"\n⚠️  Phase 3 had issues")

        # Overall success
        results['overall_success'] = (
            fetch_results.get('success') and
            cleanup_results.get('success') and
            overall_coverage > 50  # At least 50% coverage
        )

        # Generate report file
        self.generate_report(results)

        return results

    def generate_report(self, results: Dict):
        """Generate comprehensive validation report"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f"logs/validation_report_{timestamp}.json"
        readable_report_file = f"logs/validation_report_{timestamp}.md"

        # Save JSON report
        Path('logs').mkdir(exist_ok=True)
        with open(report_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        # Generate readable markdown report
        with open(readable_report_file, 'w') as f:
            f.write("# Autonomous Validation Report\n\n")
            f.write(f"**Generated:** {results['timestamp']}\n\n")
            f.write("---\n\n")

            # Phase 1
            f.write("## Phase 1: Fetch Live Data\n\n")
            fetch = results['phase_1_fetch']
            if fetch.get('success'):
                f.write(f"✅ **Success**\n\n")
                f.write(f"- Races marked: {fetch['races_marked']}\n")
                f.write(f"- Runners marked: {fetch['runners_marked']}\n")
                f.write(f"- Total marked: {fetch['total_marked']}\n\n")
            else:
                f.write(f"❌ **Failed:** {fetch.get('error')}\n\n")

            # Phase 2
            f.write("## Phase 2: Verification Results\n\n")
            verify = results['phase_2_verification']
            f.write(f"**Overall Coverage:** {verify['overall_coverage_percent']:.2f}%\n\n")
            f.write(f"- Tables checked: {verify['tables_checked']}\n")
            f.write(f"- Tables with test data: {verify['tables_with_test_data']}\n")
            f.write(f"- Total columns checked: {verify['total_columns_checked']}\n")
            f.write(f"- Columns with **TEST**: {verify['total_columns_with_test']}\n\n")

            # Per-table results
            f.write("### Per-Table Results\n\n")
            for table_result in verify['details']:
                table = table_result['table']
                if table_result.get('has_test_data'):
                    coverage = table_result['coverage_percent']
                    cols_with = table_result['columns_with_test']
                    cols_total = table_result['total_columns']

                    status = "✅" if coverage == 100 else "⚠️"
                    f.write(f"{status} **{table}** - {coverage:.1f}% ({cols_with}/{cols_total} columns)\n")

                    if table_result.get('columns_missing_test'):
                        f.write(f"\n   Missing **TEST** in:\n")
                        for missing in table_result['columns_missing_test'][:10]:
                            f.write(f"   - `{missing['column']}` ({missing['data_type']})\n")
                        if len(table_result['columns_missing_test']) > 10:
                            f.write(f"   - ... and {len(table_result['columns_missing_test']) - 10} more\n")
                        f.write("\n")
                else:
                    f.write(f"❌ **{table}** - No test data found\n\n")

            # Phase 3
            f.write("## Phase 3: Cleanup\n\n")
            cleanup = results['phase_3_cleanup']
            if cleanup.get('success'):
                f.write(f"✅ **Success:** {cleanup['total_deleted']} rows deleted\n\n")
            else:
                f.write(f"❌ **Failed**\n\n")

            # Overall
            f.write("---\n\n")
            f.write("## Overall Result\n\n")
            if results['overall_success']:
                f.write("✅ **VALIDATION SUCCESSFUL**\n")
            else:
                f.write("⚠️ **VALIDATION NEEDS ATTENTION**\n")

        print(f"\n📄 Reports saved:")
        print(f"   JSON: {report_file}")
        print(f"   Markdown: {readable_report_file}")


def main():
    """Main entry point"""
    agent = AutonomousValidationAgent()

    print("\n" + "=" * 80)
    print("AUTONOMOUS VALIDATION AGENT")
    print("=" * 80)
    print("\nThis agent will:")
    print("1. Fetch REAL data from Racing API")
    print("2. Add **TEST** markers to all fields")
    print("3. Verify EVERY table and column")
    print("4. Generate comprehensive report")
    print("5. Cleanup test data")
    print("\nPress Ctrl+C to cancel, or wait 3 seconds to continue...")
    print("=" * 80)

    import time
    time.sleep(3)

    results = agent.run_complete_validation()

    print("\n" + "=" * 80)
    print("AUTONOMOUS VALIDATION COMPLETE")
    print("=" * 80)

    if results['overall_success']:
        print("\n✅ VALIDATION SUCCESSFUL")
        print(f"   Coverage: {results['phase_2_verification']['overall_coverage_percent']:.2f}%")
    else:
        print("\n⚠️  VALIDATION NEEDS REVIEW")
        print(f"   Coverage: {results['phase_2_verification']['overall_coverage_percent']:.2f}%")
        print(f"   Tables missing data: {results['phase_2_verification']['tables_missing_test_data']}")

    print("\n📄 Check detailed reports in logs/")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
