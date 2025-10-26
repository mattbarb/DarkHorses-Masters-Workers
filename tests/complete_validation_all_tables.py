"""
Complete Validation - ALL 18 Tables

Validates every single table in the database with categorized NULLs.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient
from fetchers.races_fetcher import RacesFetcher
from fetchers.results_fetcher import ResultsFetcher

logger = get_logger('complete_validation')


class CompleteValidationAllTables:
    """Validate ALL 18 tables in the database"""

    # All 18 tables in the database
    ALL_TABLES = [
        # Master/Reference Tables (10)
        'ra_mst_bookmakers',
        'ra_mst_courses',
        'ra_mst_dams',
        'ra_mst_damsires',
        'ra_mst_horses',
        'ra_mst_jockeys',
        'ra_mst_owners',
        'ra_mst_regions',
        'ra_mst_sires',
        'ra_mst_trainers',
        # Transaction Tables (4)
        'ra_races',
        'ra_mst_runners',
        'ra_mst_race_results',
        'ra_horse_pedigree',
        # Statistics/Analytics Tables (4)
        'ra_entity_combinations',
        'ra_performance_by_distance',
        'ra_performance_by_venue',
        'ra_runner_statistics',
    ]

    # Text columns to search for data in each table
    TEXT_COLUMNS_BY_TABLE = {
        'ra_mst_bookmakers': 'name',
        'ra_mst_courses': 'name',
        'ra_mst_dams': 'name',
        'ra_mst_damsires': 'name',
        'ra_mst_horses': 'name',
        'ra_mst_jockeys': 'name',
        'ra_mst_owners': 'name',
        'ra_mst_regions': 'name',
        'ra_mst_sires': 'name',
        'ra_mst_trainers': 'name',
        'ra_races': 'race_name',
        'ra_mst_runners': 'horse_name',
        'ra_mst_race_results': 'horse_name',
        'ra_horse_pedigree': 'sire',
        'ra_entity_combinations': 'combination_type',
        'ra_performance_by_distance': 'entity_id',
        'ra_performance_by_venue': 'entity_id',
        'ra_runner_statistics': 'horse_id',
    }

    def __init__(self):
        """Initialize validator"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

    def run_complete_validation(self) -> Dict:
        """Validate all 18 tables"""

        logger.info("=" * 80)
        logger.info("COMPLETE VALIDATION - ALL 18 TABLES")
        logger.info("=" * 80)

        # First, populate data by running fetchers
        logger.info("\nPhase 1: Populating data...")
        self._populate_data()

        # Validate each table
        logger.info("\nPhase 2: Validating all tables...")

        table_reports = {}
        tables_with_data = 0
        tables_without_data = 0

        for table_name in self.ALL_TABLES:
            logger.info(f"\n  Checking {table_name}...")

            # Try to get a sample row
            try:
                text_col = self.TEXT_COLUMNS_BY_TABLE.get(table_name, 'id')
                result = self.db_client.client.table(table_name).select('*').order('created_at', desc=True).limit(1).execute()

                if result.data and len(result.data) > 0:
                    sample_row = result.data[0]
                    report = self._validate_table(table_name, sample_row)
                    table_reports[table_name] = report
                    tables_with_data += 1

                    logger.info(f"    ✅ {len(sample_row)} columns, {report['populated_columns']} populated ({report['raw_coverage_percent']:.1f}%)")
                else:
                    table_reports[table_name] = {
                        'table_name': table_name,
                        'has_data': False,
                        'reason': 'No rows in table'
                    }
                    tables_without_data += 1
                    logger.info(f"    ⚠️  No data")

            except Exception as e:
                table_reports[table_name] = {
                    'table_name': table_name,
                    'has_data': False,
                    'error': str(e)
                }
                tables_without_data += 1
                logger.info(f"    ❌ Error: {e}")

        # Generate report
        logger.info("\nPhase 3: Generating comprehensive report...")
        report_path = self._generate_master_report(table_reports, tables_with_data, tables_without_data)

        logger.info("=" * 80)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Report: {report_path}")
        logger.info(f"Tables with data: {tables_with_data}/18")
        logger.info(f"Tables without data: {tables_without_data}/18")

        return {
            'success': True,
            'report_path': report_path,
            'total_tables': 18,
            'tables_with_data': tables_with_data,
            'tables_without_data': tables_without_data,
            'table_reports': table_reports
        }

    def _populate_data(self):
        """Populate some sample data by running fetchers"""

        logger.info("  Running RacesFetcher to populate data...")
        races_fetcher = RacesFetcher()
        result = races_fetcher.fetch_and_store(days_back=1, region_codes=['gb', 'ire'])

        if result.get('success'):
            logger.info(f"  ✅ Fetched {result.get('races_fetched', 0)} races")
        else:
            logger.warning(f"  ⚠️  RacesFetcher had issues")

    def _validate_table(self, table_name: str, sample_row: Dict) -> Dict:
        """Validate a single table"""

        total_columns = len(sample_row)
        populated_columns = 0
        null_columns = []
        column_data = []

        for col_name, value in sample_row.items():
            if value is not None:
                populated_columns += 1
                column_data.append({
                    'name': col_name,
                    'value': self._format_value(value),
                    'has_data': True
                })
            else:
                null_columns.append(col_name)
                column_data.append({
                    'name': col_name,
                    'value': 'NULL',
                    'has_data': False
                })

        coverage_pct = (populated_columns / total_columns * 100) if total_columns > 0 else 0

        return {
            'table_name': table_name,
            'has_data': True,
            'total_columns': total_columns,
            'populated_columns': populated_columns,
            'null_columns': null_columns,
            'raw_coverage_percent': coverage_pct,
            'column_data': column_data
        }

    def _format_value(self, value: Any) -> str:
        """Format value for display"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            return f'"{value[:50]}..."' if len(value) > 50 else f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (dict, list)):
            return "{...}" if isinstance(value, dict) else "[...]"
        else:
            return str(value)[:50]

    def _generate_master_report(
        self,
        table_reports: Dict[str, Dict],
        tables_with_data: int,
        tables_without_data: int
    ) -> str:
        """Generate master validation report"""

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_path = f"logs/complete_validation_all_tables_{timestamp}.md"

        lines = []
        lines.append("# Complete Validation Report - ALL 18 TABLES")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append(f"**Status:** ✅ COMPLETE")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        lines.append(f"- **Total tables:** 18")
        lines.append(f"- **Tables with data:** {tables_with_data}")
        lines.append(f"- **Tables without data:** {tables_without_data}")
        lines.append("")

        # Calculate overall coverage
        tables_with_coverage = [r for r in table_reports.values() if r.get('has_data')]
        if tables_with_coverage:
            total_cols = sum(r['total_columns'] for r in tables_with_coverage)
            populated_cols = sum(r['populated_columns'] for r in tables_with_coverage)
            overall_coverage = (populated_cols / total_cols * 100) if total_cols > 0 else 0

            lines.append(f"**Overall Coverage:** {populated_cols}/{total_cols} columns ({overall_coverage:.1f}%)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Tables with data
        lines.append("## Tables WITH Data")
        lines.append("")
        lines.append("| Table | Columns | Populated | Coverage |")
        lines.append("|-------|---------|-----------|----------|")

        for table_name in self.ALL_TABLES:
            report = table_reports.get(table_name, {})
            if report.get('has_data'):
                lines.append(f"| {table_name} | {report['total_columns']} | {report['populated_columns']} | {report['raw_coverage_percent']:.1f}% |")

        lines.append("")
        lines.append("---")
        lines.append("")

        # Tables without data
        if tables_without_data > 0:
            lines.append("## Tables WITHOUT Data")
            lines.append("")

            for table_name in self.ALL_TABLES:
                report = table_reports.get(table_name, {})
                if not report.get('has_data'):
                    reason = report.get('reason', report.get('error', 'Unknown'))
                    lines.append(f"- **{table_name}** - {reason}")

            lines.append("")
            lines.append("---")
            lines.append("")

        # Detailed per-table reports
        lines.append("## Detailed Table Reports")
        lines.append("")

        for table_name in self.ALL_TABLES:
            report = table_reports.get(table_name, {})

            if not report.get('has_data'):
                continue

            lines.append(f"### {table_name}")
            lines.append("")
            lines.append(f"**Coverage:** {report['populated_columns']}/{report['total_columns']} ({report['raw_coverage_percent']:.1f}%)")
            lines.append("")

            # Show sample of populated columns
            populated = [c for c in report['column_data'] if c['has_data']]
            if populated:
                lines.append("**Sample Populated Columns:**")
                lines.append("")
                lines.append("| Column | Sample Value |")
                lines.append("|--------|--------------|")
                for col in populated[:10]:  # Show first 10
                    lines.append(f"| {col['name']} | {col['value']} |")
                lines.append("")

            # Show NULL columns
            null_cols = report.get('null_columns', [])
            if null_cols:
                lines.append(f"**NULL Columns ({len(null_cols)}):**")
                lines.append("")
                for col in null_cols[:20]:  # Show first 20
                    lines.append(f"- {col}")
                if len(null_cols) > 20:
                    lines.append(f"- ... and {len(null_cols) - 20} more")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Write report
        with open(report_path, 'w') as f:
            f.write('\n'.join(lines))

        logger.info(f"✅ Report saved: {report_path}")

        return report_path


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Complete validation of all 18 tables')

    args = parser.parse_args()

    validator = CompleteValidationAllTables()
    result = validator.run_complete_validation()

    if result['success']:
        print(f"\n✅ Validation complete!")
        print(f"   Report: {result['report_path']}")
        print(f"   Tables with data: {result['tables_with_data']}/18")
        print(f"   Tables without data: {result['tables_without_data']}/18")

        # Show which tables need data
        if result['tables_without_data'] > 0:
            print(f"\n⚠️  Tables without data:")
            for table_name, report in result['table_reports'].items():
                if not report.get('has_data'):
                    print(f"   - {table_name}")
    else:
        print(f"\n❌ Validation failed: {result.get('error')}")

    return result


if __name__ == '__main__':
    main()
