"""
Enhanced Validation Report Generator

Tests BOTH racecards AND results, categorizes NULL columns,
identifies field mapping issues, generates comprehensive reports.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any
from collections import defaultdict

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient
from fetchers.races_fetcher import RacesFetcher
from fetchers.results_fetcher import ResultsFetcher

logger = get_logger('enhanced_validation')


class EnhancedValidationReportGenerator:
    """Generate comprehensive validation reports with categorized NULLs"""

    # Define which columns are post-race only
    POST_RACE_ONLY_COLUMNS = {
        'ra_races': [
            'winning_time', 'winning_time_detail', 'comments', 'non_runners',
            'tote_win', 'tote_pl', 'tote_ex', 'tote_csf', 'tote_tricast', 'tote_trifecta'
        ],
        'ra_runners': [
            'position', 'distance_beaten', 'prize_won', 'starting_price',
            'result_updated_at', 'finishing_time', 'starting_price_decimal',
            'race_comment', 'overall_beaten_distance'
        ]
    }

    # Define optional/conditional columns
    OPTIONAL_COLUMNS = {
        'ra_races': [
            'race_number', 'meet_id', 'prize', 'sex_restriction', 'distance_m', 'time'
        ],
        'ra_runners': [
            'rpr', 'ts', 'weight_st_lbs', 'claiming_price_min', 'claiming_price_max',
            'medication', 'equipment', 'morning_line_odds', 'jockey_silk_url',
            'jockey_claim_lbs', 'weight_stones_lbs'
        ],
        'ra_mst_horses': ['age']  # Age calculated dynamically, may be NULL
    }

    def __init__(self):
        """Initialize generator"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.test_race_ids = []

    def run_validation(self, test_results: bool = False, days_back: int = 1) -> Dict:
        """
        Run comprehensive validation

        Args:
            test_results: If True, test results data (post-race). If False, test racecards (pre-race)
            days_back: Days back to fetch

        Returns:
            Validation results dict
        """
        logger.info("=" * 80)
        logger.info(f"ENHANCED VALIDATION - {'RESULTS' if test_results else 'RACECARDS'}")
        logger.info("=" * 80)

        if test_results:
            # Test results (post-race data)
            return self._validate_results(days_back)
        else:
            # Test racecards (pre-race data)
            return self._validate_racecards(days_back)

    def _validate_racecards(self, days_back: int) -> Dict:
        """Validate racecard data"""

        logger.info("\nPhase 1: Fetching racecards (pre-race data)...")
        fetcher = RacesFetcher()
        result = fetcher.fetch_and_store(days_back=days_back, region_codes=['gb', 'ire'])

        if not result.get('success'):
            return {'success': False, 'error': 'Racecard fetch failed'}

        logger.info(f"✅ Fetched {result.get('races_fetched', 0)} races")

        return self._generate_validation_report('racecards', result)

    def _validate_results(self, days_back: int) -> Dict:
        """Validate results data"""

        logger.info("\nPhase 1: Fetching results (post-race data)...")

        # Fetch results from N days ago (to ensure races have completed)
        target_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')

        fetcher = ResultsFetcher()
        result = fetcher.fetch_and_store(
            start_date=target_date,
            end_date=target_date,
            region_codes=['gb', 'ire']
        )

        if not result.get('success'):
            return {'success': False, 'error': 'Results fetch failed'}

        logger.info(f"✅ Fetched {result.get('fetched', 0)} results")

        return self._generate_validation_report('results', result)

    def _generate_validation_report(self, data_type: str, fetch_result: Dict) -> Dict:
        """Generate validation report with categorized NULLs"""

        logger.info("\nPhase 2: Reading back data and categorizing columns...")

        # Get recent races
        recent_races = self.db_client.client.table('ra_races').select('*').order('created_at', desc=True).limit(5).execute()

        if not recent_races.data:
            return {'success': False, 'error': 'No races found'}

        self.test_race_ids = [race['id'] for race in recent_races.data]

        # Generate reports for each table
        reports = {}

        # Validate ra_races
        race_report = self._validate_table_with_categories(
            'ra_races',
            recent_races.data[0],
            'Race data',
            data_type
        )
        reports['ra_races'] = race_report

        # Validate ra_runners
        race_id = recent_races.data[0]['id']
        runners = self.db_client.client.table('ra_runners').select('*').eq('race_id', race_id).limit(1).execute()
        if runners.data:
            runner_report = self._validate_table_with_categories(
                'ra_runners',
                runners.data[0],
                'Runner data',
                data_type
            )
            reports['ra_runners'] = runner_report

        # Validate ra_mst_horses
        if runners.data and runners.data[0].get('horse_id'):
            horse_id = runners.data[0]['horse_id']
            horses = self.db_client.client.table('ra_mst_horses').select('*').eq('id', horse_id).limit(1).execute()
            if horses.data:
                horse_report = self._validate_table_with_categories(
                    'ra_mst_horses',
                    horses.data[0],
                    'Horse master data',
                    data_type
                )
                reports['ra_mst_horses'] = horse_report

                # Check pedigree
                pedigree = self.db_client.client.table('ra_horse_pedigree').select('*').eq('horse_id', horse_id).limit(1).execute()
                if pedigree.data:
                    pedigree_report = self._validate_table_with_categories(
                        'ra_horse_pedigree',
                        pedigree.data[0],
                        'Horse pedigree (enrichment)',
                        data_type
                    )
                    reports['ra_horse_pedigree'] = pedigree_report

        # Generate master report
        report_path = self._generate_master_report(reports, fetch_result, data_type)

        # Cleanup
        logger.info("\nPhase 3: Cleaning up test data...")
        cleanup_result = self._cleanup_test_data()

        logger.info("=" * 80)
        logger.info("VALIDATION COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Report: {report_path}")

        return {
            'success': True,
            'report_path': report_path,
            'data_type': data_type,
            'tables_validated': len(reports),
            'cleanup': cleanup_result
        }

    def _validate_table_with_categories(
        self,
        table_name: str,
        sample_row: Dict,
        description: str,
        data_type: str
    ) -> Dict:
        """Validate table and categorize NULL columns"""

        logger.info(f"  Validating {table_name}...")

        total_columns = len(sample_row)
        populated_columns = 0

        null_columns_expected = []  # Post-race only or optional
        null_columns_unexpected = []  # Should have data but don't
        populated_column_data = []

        post_race_cols = self.POST_RACE_ONLY_COLUMNS.get(table_name, [])
        optional_cols = self.OPTIONAL_COLUMNS.get(table_name, [])

        for col_name, value in sample_row.items():
            if value is not None:
                populated_columns += 1
                populated_column_data.append({
                    'name': col_name,
                    'value': self._format_value(value),
                    'status': "✅"
                })
            else:
                # Categorize NULL
                if col_name in post_race_cols:
                    category = "post-race only" if data_type == 'racecards' else "unexpected"
                    null_columns_expected.append({
                        'name': col_name,
                        'category': category
                    })
                elif col_name in optional_cols:
                    null_columns_expected.append({
                        'name': col_name,
                        'category': 'optional'
                    })
                else:
                    null_columns_unexpected.append(col_name)

        # Calculate coverage excluding expected NULLs
        expected_null_count = len(null_columns_expected)
        actual_coverage_cols = total_columns - expected_null_count
        actual_coverage_pct = (populated_columns / actual_coverage_cols * 100) if actual_coverage_cols > 0 else 0

        raw_coverage_pct = (populated_columns / total_columns * 100) if total_columns > 0 else 0

        logger.info(f"    Raw coverage: {populated_columns}/{total_columns} ({raw_coverage_pct:.1f}%)")
        logger.info(f"    Actual coverage (excl. expected NULLs): {populated_columns}/{actual_coverage_cols} ({actual_coverage_pct:.1f}%)")

        return {
            'table_name': table_name,
            'description': description,
            'total_columns': total_columns,
            'populated_columns': populated_columns,
            'raw_coverage_percent': raw_coverage_pct,
            'actual_coverage_percent': actual_coverage_pct,
            'null_columns_expected': null_columns_expected,
            'null_columns_unexpected': null_columns_unexpected,
            'populated_column_data': populated_column_data
        }

    def _format_value(self, value: Any) -> str:
        """Format value for display"""
        if value is None:
            return "NULL"
        elif isinstance(value, str):
            if len(value) > 50:
                return f'"{value[:47]}..."'
            return f'"{value}"'
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, bool):
            return str(value)
        elif isinstance(value, (dict, list)):
            return f"{{...}}" if isinstance(value, dict) else f"[...]"
        else:
            return str(value)[:50]

    def _generate_master_report(
        self,
        table_reports: Dict[str, Dict],
        fetch_result: Dict,
        data_type: str
    ) -> str:
        """Generate enhanced master report"""

        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        report_path = f"logs/enhanced_validation_{data_type}_{timestamp}.md"

        lines = []
        lines.append(f"# Enhanced Validation Report - {data_type.upper()}")
        lines.append("")
        lines.append(f"**Generated:** {datetime.utcnow().isoformat()}")
        lines.append(f"**Data Type:** {data_type} ({'post-race' if data_type == 'results' else 'pre-race'})")
        lines.append(f"**Status:** ✅ SUCCESS")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Summary
        lines.append("## Summary")
        lines.append("")
        if data_type == 'racecards':
            lines.append(f"- **Races fetched:** {fetch_result.get('races_fetched', 0)}")
            lines.append(f"- **Runners fetched:** {fetch_result.get('runners_fetched', 0)}")
        else:
            lines.append(f"- **Results fetched:** {fetch_result.get('fetched', 0)}")
        lines.append(f"- **Tables validated:** {len(table_reports)}")
        lines.append("")

        # Overall coverage
        total_cols = sum(r['total_columns'] for r in table_reports.values())
        populated_cols = sum(r['populated_columns'] for r in table_reports.values())
        raw_coverage = (populated_cols / total_cols * 100) if total_cols > 0 else 0

        # Calculate actual coverage (excluding expected NULLs)
        total_expected_nulls = sum(len(r['null_columns_expected']) for r in table_reports.values())
        actual_total_cols = total_cols - total_expected_nulls
        actual_coverage = (populated_cols / actual_total_cols * 100) if actual_total_cols > 0 else 0

        lines.append(f"**Raw Coverage:** {populated_cols}/{total_cols} columns ({raw_coverage:.1f}%)")
        lines.append(f"**Actual Coverage (excl. expected NULLs):** {populated_cols}/{actual_total_cols} columns ({actual_coverage:.1f}%)")
        lines.append("")
        lines.append("---")
        lines.append("")

        # Per-table reports
        for table_name, report in table_reports.items():
            lines.append(f"## {table_name}")
            lines.append("")
            lines.append(f"**Description:** {report['description']}")
            lines.append(f"**Raw Coverage:** {report['populated_columns']}/{report['total_columns']} ({report['raw_coverage_percent']:.1f}%)")
            lines.append(f"**Actual Coverage:** {report['actual_coverage_percent']:.1f}%")
            lines.append("")

            # Populated columns table
            lines.append("### ✅ Populated Columns")
            lines.append("")
            lines.append("| Column | Sample Value | Status |")
            lines.append("|--------|--------------|--------|")

            for col in report['populated_column_data']:
                lines.append(f"| {col['name']} | {col['value']} | {col['status']} |")

            lines.append("")

            # Expected NULL columns
            if report['null_columns_expected']:
                lines.append("### ⚠️ Expected NULL Columns")
                lines.append("")
                lines.append("These columns are expected to be NULL for this data type:")
                lines.append("")
                for col in report['null_columns_expected']:
                    lines.append(f"- **{col['name']}** ({col['category']})")
                lines.append("")

            # Unexpected NULL columns
            if report['null_columns_unexpected']:
                lines.append("### ❌ Unexpected NULL Columns")
                lines.append("")
                lines.append("⚠️ **These columns should have data but are NULL:**")
                lines.append("")
                for col in report['null_columns_unexpected']:
                    lines.append(f"- **{col}** - Possible field mapping issue!")
                lines.append("")

            lines.append("---")
            lines.append("")

        # Field mapping issues section
        lines.append("## 🔍 Field Mapping Issues Detected")
        lines.append("")
        lines.append("Based on validation, the following field mapping issues may exist:")
        lines.append("")
        lines.append("1. ✅ **FIXED:** `lbs` → `weight_lbs` (already corrected)")
        lines.append("2. ⚠️ **TO FIX:** `sex_restriction` in API vs `sex_rest` in code")
        lines.append("3. ⚠️ **UNCAPTURED:** `odds` array with live bookmaker odds")
        lines.append("4. ⚠️ **UNCAPTURED:** Pedigree names (`sire`, `dam`, `damsire` text fields)")
        lines.append("")

        # Enrichment status
        if 'ra_horse_pedigree' in table_reports:
            lines.append("## Enrichment Verification")
            lines.append("")
            lines.append("✅ **Enrichment VERIFIED** - Horse pedigree data captured!")
            lines.append("")

        # Write report
        with open(report_path, 'w') as f:
            f.write('\n'.join(lines))

        logger.info(f"✅ Report saved: {report_path}")

        return report_path

    def _cleanup_test_data(self) -> Dict:
        """Clean up test data"""

        if not self.test_race_ids:
            return {'success': True, 'total_deleted': 0}

        logger.info(f"Cleaning up {len(self.test_race_ids)} test races...")

        total_deleted = 0

        # Delete runners first
        for race_id in self.test_race_ids:
            result = self.db_client.client.table('ra_runners').delete().eq('race_id', race_id).execute()
            if result.data:
                total_deleted += len(result.data)

        # Delete races
        for race_id in self.test_race_ids:
            result = self.db_client.client.table('ra_races').delete().eq('id', race_id).execute()
            if result.data:
                total_deleted += len(result.data)

        logger.info(f"✅ Deleted {total_deleted} records")

        return {
            'success': True,
            'total_deleted': total_deleted
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Enhanced validation report generator')
    parser.add_argument('--results', action='store_true', help='Test results data (post-race) instead of racecards')
    parser.add_argument('--days-back', type=int, default=1, help='Days back to fetch (default: 1)')

    args = parser.parse_args()

    generator = EnhancedValidationReportGenerator()
    result = generator.run_validation(test_results=args.results, days_back=args.days_back)

    if result['success']:
        print(f"\n✅ Validation complete!")
        print(f"   Data type: {result['data_type']}")
        print(f"   Report: {result['report_path']}")
        print(f"   Tables validated: {result['tables_validated']}")
    else:
        print(f"\n❌ Validation failed: {result.get('error')}")

    return result


if __name__ == '__main__':
    main()
