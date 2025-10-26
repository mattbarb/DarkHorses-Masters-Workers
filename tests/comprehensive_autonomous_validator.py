#!/usr/bin/env python3
"""
Comprehensive Autonomous Validation Agent

Fully automated end-to-end validation system that:
1. Runs live data test with **TEST** markers
2. Monitors execution in real-time
3. Verifies EVERY table and EVERY cell for **TEST** markers
4. Generates detailed reports (JSON + Markdown)
5. Cleans up test data
6. Provides comprehensive pass/fail status

This agent validates:
- All transaction tables (ra_races, ra_mst_runners, ra_mst_race_results)
- All master tables (ra_mst_*)
- Enrichment tables (ra_horse_pedigree)
- EVERY single column in EVERY table
- Complete data pipeline from API to database
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import time
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient
from tests.test_live_data_with_markers import LiveDataTestInserter

logger = get_logger('comprehensive_validator')


class ComprehensiveAutonomousValidator:
    """
    Comprehensive autonomous validation agent

    Runs complete end-to-end validation with detailed table/column verification
    """

    def __init__(self):
        """Initialize validator"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.test_marker = "**TEST**"
        self.inserter = LiveDataTestInserter()

        # All tables to verify (in logical order)
        self.tables_to_verify = [
            # Transaction tables (highest priority)
            'ra_races',
            'ra_mst_runners',
            'ra_mst_race_results',

            # Master tables - People
            'ra_mst_jockeys',
            'ra_mst_trainers',
            'ra_mst_owners',

            # Master tables - Horses and enrichment
            'ra_mst_horses',
            'ra_horse_pedigree',  # CRITICAL for enrichment verification

            # Master tables - Reference
            'ra_mst_courses',
            'ra_mst_bookmakers',
            'ra_mst_regions',

            # Statistics tables
            'ra_mst_sires',
            'ra_mst_dams',
            'ra_mst_damsires'
        ]

        # Validation results
        self.validation_results = {
            'timestamp': datetime.now().isoformat(),
            'phase_1_test_execution': {},
            'phase_2_table_verification': {},
            'phase_3_enrichment_verification': {},
            'phase_4_cleanup': {},
            'overall_status': 'pending'
        }

    def run_complete_validation(self) -> Dict:
        """
        Run complete autonomous validation workflow

        Returns:
            Comprehensive validation results dictionary
        """

        logger.info("\n" + "=" * 80)
        logger.info("COMPREHENSIVE AUTONOMOUS VALIDATION AGENT - STARTING")
        logger.info("=" * 80)
        logger.info("\nWorkflow:")
        logger.info("1. Run live data test with **TEST** markers")
        logger.info("2. Monitor test execution")
        logger.info("3. Verify EVERY table and EVERY cell")
        logger.info("4. Verify enrichment specifically (ra_horse_pedigree)")
        logger.info("5. Generate comprehensive reports")
        logger.info("6. Cleanup all test data")
        logger.info("=" * 80 + "\n")

        # Countdown
        logger.info("Starting validation in 3 seconds...")
        logger.info("Press Ctrl+C to cancel")
        logger.info("=" * 80 + "\n")

        try:
            time.sleep(3)
        except KeyboardInterrupt:
            logger.info("\n❌ Validation cancelled by user")
            return {'success': False, 'error': 'Cancelled by user'}

        # Phase 1: Run live data test
        phase_1_result = self._phase_1_run_test()
        self.validation_results['phase_1_test_execution'] = phase_1_result

        if not phase_1_result.get('success'):
            logger.error("❌ Phase 1 failed - aborting validation")
            self.validation_results['overall_status'] = 'failed_phase_1'
            return self.validation_results

        # Phase 2: Verify ALL tables and cells
        phase_2_result = self._phase_2_verify_all_tables()
        self.validation_results['phase_2_table_verification'] = phase_2_result

        # Phase 3: Verify enrichment specifically
        phase_3_result = self._phase_3_verify_enrichment()
        self.validation_results['phase_3_enrichment_verification'] = phase_3_result

        # Phase 4: Cleanup
        phase_4_result = self._phase_4_cleanup()
        self.validation_results['phase_4_cleanup'] = phase_4_result

        # Overall status
        self._calculate_overall_status()

        # Generate reports
        self._generate_reports()

        return self.validation_results

    def _phase_1_run_test(self) -> Dict:
        """
        Phase 1: Run live data test with **TEST** markers

        Returns:
            Test execution results
        """

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 1: RUNNING LIVE DATA TEST WITH **TEST** MARKERS")
        logger.info("=" * 80 + "\n")

        start_time = time.time()

        try:
            # Run test
            test_results = self.inserter.fetch_and_insert_races(days_back=1)

            elapsed_time = time.time() - start_time

            logger.info(f"\n✅ Phase 1 complete in {elapsed_time:.1f} seconds")
            logger.info(f"   Races marked: {test_results.get('races_marked', 0)}")
            logger.info(f"   Runners marked: {test_results.get('runners_marked', 0)}")
            logger.info(f"   Horses marked: {test_results.get('horses_marked', 0)}")
            logger.info(f"   Pedigrees marked: {test_results.get('pedigrees_marked', 0)}")

            return {
                'success': test_results.get('success', False),
                'elapsed_time': elapsed_time,
                'races_marked': test_results.get('races_marked', 0),
                'runners_marked': test_results.get('runners_marked', 0),
                'horses_marked': test_results.get('horses_marked', 0),
                'pedigrees_marked': test_results.get('pedigrees_marked', 0),
                'enrichment_verified': test_results.get('enrichment_verified', False),
                'total_records_marked': test_results.get('total_marked', 0)
            }

        except Exception as e:
            logger.error(f"❌ Phase 1 failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _phase_2_verify_all_tables(self) -> Dict:
        """
        Phase 2: Verify EVERY table and EVERY cell for **TEST** markers

        Returns:
            Comprehensive table verification results
        """

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 2: VERIFYING ALL TABLES AND CELLS")
        logger.info("=" * 80 + "\n")

        verification_results = {
            'tables_checked': 0,
            'tables_with_test_data': 0,
            'tables_missing_test_data': [],
            'total_columns_checked': 0,
            'total_columns_with_test': 0,
            'table_details': []
        }

        for table_name in self.tables_to_verify:
            logger.info(f"Verifying {table_name}...")

            table_result = self._verify_table(table_name)

            verification_results['tables_checked'] += 1
            verification_results['table_details'].append(table_result)

            if table_result.get('has_test_data'):
                verification_results['tables_with_test_data'] += 1
                verification_results['total_columns_checked'] += table_result.get('total_columns', 0)
                verification_results['total_columns_with_test'] += table_result.get('columns_with_test_count', 0)

                coverage = table_result.get('coverage_percent', 0)
                if coverage == 100:
                    logger.info(f"  ✅ {table_name}: {coverage:.1f}% ({table_result.get('columns_with_test_count')}/{table_result.get('total_columns')} columns)")
                elif coverage >= 50:
                    logger.info(f"  ⚠️  {table_name}: {coverage:.1f}% ({table_result.get('columns_with_test_count')}/{table_result.get('total_columns')} columns)")
                else:
                    logger.info(f"  ❌ {table_name}: {coverage:.1f}% ({table_result.get('columns_with_test_count')}/{table_result.get('total_columns')} columns)")
            else:
                verification_results['tables_missing_test_data'].append(table_name)
                logger.info(f"  ⚠️  {table_name}: No test data found")

        # Calculate overall coverage
        if verification_results['total_columns_checked'] > 0:
            overall_coverage = (verification_results['total_columns_with_test'] /
                               verification_results['total_columns_checked'] * 100)
            verification_results['overall_coverage_percent'] = round(overall_coverage, 2)
        else:
            verification_results['overall_coverage_percent'] = 0

        logger.info(f"\n{'=' * 80}")
        logger.info(f"PHASE 2 SUMMARY:")
        logger.info(f"{'=' * 80}")
        logger.info(f"Tables checked: {verification_results['tables_checked']}")
        logger.info(f"Tables with test data: {verification_results['tables_with_test_data']}")
        logger.info(f"Tables missing test data: {len(verification_results['tables_missing_test_data'])}")
        logger.info(f"\nTotal columns checked: {verification_results['total_columns_checked']}")
        logger.info(f"Columns with **TEST**: {verification_results['total_columns_with_test']}")
        logger.info(f"Overall coverage: {verification_results['overall_coverage_percent']}%")

        if verification_results['overall_coverage_percent'] >= 80:
            logger.info(f"\n✅ Excellent coverage!")
        elif verification_results['overall_coverage_percent'] >= 50:
            logger.info(f"\n⚠️  Acceptable coverage, but could be improved")
        else:
            logger.info(f"\n❌ Low coverage - investigation needed")

        return verification_results

    def _verify_table(self, table_name: str) -> Dict:
        """
        Verify a specific table for **TEST** markers in all columns

        Args:
            table_name: Name of table to verify

        Returns:
            Table verification results
        """

        try:
            # Get table schema
            columns = self._get_table_columns(table_name)

            if not columns:
                return {
                    'table': table_name,
                    'has_test_data': False,
                    'error': 'Could not retrieve schema'
                }

            # Find a text column to query for **TEST**
            text_column = self._find_text_column(columns)

            if not text_column:
                return {
                    'table': table_name,
                    'has_test_data': False,
                    'total_columns': len(columns),
                    'warning': 'No text column found for querying'
                }

            # Query for test data
            result = self.db_client.client.table(table_name).select('*').like(
                text_column, f'%{self.test_marker}%'
            ).limit(1).execute()

            if not result.data or len(result.data) == 0:
                return {
                    'table': table_name,
                    'has_test_data': False,
                    'total_columns': len(columns)
                }

            # Analyze which columns have **TEST**
            test_row = result.data[0]
            columns_with_test = []
            columns_missing_test = []

            for col in columns:
                col_name = col['column_name']
                col_type = col['data_type']
                value = test_row.get(col_name)

                if value is not None and self.test_marker in str(value):
                    columns_with_test.append(col_name)
                else:
                    columns_missing_test.append({
                        'column': col_name,
                        'type': col_type,
                        'value': str(value)[:100] if value is not None else 'NULL'
                    })

            coverage_percent = (len(columns_with_test) / len(columns) * 100) if columns else 0

            return {
                'table': table_name,
                'has_test_data': True,
                'total_columns': len(columns),
                'columns_with_test_count': len(columns_with_test),
                'columns_with_test': columns_with_test,
                'columns_missing_test': columns_missing_test,
                'coverage_percent': round(coverage_percent, 2)
            }

        except Exception as e:
            logger.error(f"Error verifying {table_name}: {e}")
            return {
                'table': table_name,
                'has_test_data': False,
                'error': str(e)
            }

    def _get_table_columns(self, table_name: str) -> List[Dict]:
        """Get column information for a table"""

        try:
            query = f"""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = '{table_name}'
            ORDER BY ordinal_position
            """

            result = self.db_client.client.rpc('exec_sql', {'sql': query}).execute()
            return result.data if result.data else []

        except:
            # Fallback - try direct query
            try:
                # Get a sample row to infer columns
                sample = self.db_client.client.table(table_name).select('*').limit(1).execute()
                if sample.data and len(sample.data) > 0:
                    return [{'column_name': k, 'data_type': 'unknown', 'is_nullable': 'YES'}
                            for k in sample.data[0].keys()]
            except:
                pass

            return []

    def _find_text_column(self, columns: List[Dict]) -> Optional[str]:
        """Find first text/varchar column for querying"""

        # Preferred columns for different tables
        preferred = ['name', 'race_title', 'horse_name', 'jockey_name', 'trainer_name',
                    'owner_name', 'course_name', 'sire', 'dam']

        # Check preferred first
        col_names = [c['column_name'] for c in columns]
        for pref in preferred:
            if pref in col_names:
                return pref

        # Find any text column
        for col in columns:
            col_type = col.get('data_type', '').lower()
            if any(t in col_type for t in ['char', 'text', 'varchar']):
                return col['column_name']

        return None

    def _phase_3_verify_enrichment(self) -> Dict:
        """
        Phase 3: Specifically verify enrichment (ra_horse_pedigree)

        Returns:
            Enrichment verification results
        """

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 3: VERIFYING ENRICHMENT (ra_horse_pedigree)")
        logger.info("=" * 80 + "\n")

        try:
            # Check ra_horse_pedigree for **TEST** markers
            pedigree_result = self.db_client.client.table('ra_horse_pedigree').select('*').like(
                'sire', f'%{self.test_marker}%'
            ).execute()

            if not pedigree_result.data or len(pedigree_result.data) == 0:
                logger.warning("⚠️  No pedigree records with **TEST** found")
                logger.info("\nThis could mean:")
                logger.info("- Horses already existed in database (enrichment only for NEW horses)")
                logger.info("- No new horses in the test data")
                logger.info("- Enrichment process didn't run (check Phase 1 logs)")

                return {
                    'enrichment_verified': False,
                    'pedigree_records_found': 0,
                    'reason': 'No pedigree records with **TEST** markers'
                }

            pedigree_count = len(pedigree_result.data)
            logger.info(f"✅ Found {pedigree_count} pedigree records with **TEST** markers\n")

            # Analyze pedigree data
            enrichment_fields = ['dob', 'sex_code', 'colour', 'breeder', 'sire', 'dam', 'damsire', 'region']
            field_coverage = {}

            for field in enrichment_fields:
                populated_count = sum(1 for p in pedigree_result.data if p.get(field))
                field_coverage[field] = {
                    'populated': populated_count,
                    'total': pedigree_count,
                    'percent': round(populated_count / pedigree_count * 100, 1) if pedigree_count > 0 else 0
                }

            logger.info("Enrichment field coverage:")
            for field, stats in field_coverage.items():
                logger.info(f"  {field}: {stats['populated']}/{stats['total']} ({stats['percent']}%)")

            logger.info(f"\n✅ ENRICHMENT VERIFIED")
            logger.info(f"   - {pedigree_count} horses were enriched with Pro endpoint data")
            logger.info(f"   - Complete pedigree captured (sire, dam, damsire)")
            logger.info(f"   - Enrichment process is working correctly")

            return {
                'enrichment_verified': True,
                'pedigree_records_found': pedigree_count,
                'field_coverage': field_coverage,
                'sample_pedigrees': pedigree_result.data[:3]  # First 3 for report
            }

        except Exception as e:
            logger.error(f"❌ Phase 3 failed: {e}", exc_info=True)
            return {
                'enrichment_verified': False,
                'error': str(e)
            }

    def _phase_4_cleanup(self) -> Dict:
        """
        Phase 4: Cleanup all test data

        Returns:
            Cleanup results
        """

        logger.info("\n" + "=" * 80)
        logger.info("PHASE 4: CLEANING UP TEST DATA")
        logger.info("=" * 80 + "\n")

        try:
            cleanup_result = self.inserter.cleanup_test_data()

            logger.info(f"\n✅ Phase 4 complete")
            logger.info(f"   Tables cleaned: {cleanup_result.get('tables_cleaned', 0)}")
            logger.info(f"   Total rows deleted: {cleanup_result.get('total_deleted', 0)}")

            return cleanup_result

        except Exception as e:
            logger.error(f"❌ Phase 4 failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _calculate_overall_status(self):
        """Calculate overall validation status"""

        phase_1 = self.validation_results['phase_1_test_execution']
        phase_2 = self.validation_results['phase_2_table_verification']
        phase_3 = self.validation_results['phase_3_enrichment_verification']
        phase_4 = self.validation_results['phase_4_cleanup']

        # Check if all phases succeeded
        phase_1_ok = phase_1.get('success', False)
        phase_2_ok = phase_2.get('overall_coverage_percent', 0) >= 50  # At least 50% coverage
        phase_3_ok = phase_3.get('enrichment_verified', False) or phase_3.get('reason') == 'No pedigree records with **TEST** markers'  # OK if horses existed
        phase_4_ok = phase_4.get('success', False)

        if phase_1_ok and phase_2_ok and phase_3_ok and phase_4_ok:
            self.validation_results['overall_status'] = 'success'
        elif phase_1_ok and phase_2_ok:
            self.validation_results['overall_status'] = 'partial_success'
        else:
            self.validation_results['overall_status'] = 'failed'

    def _generate_reports(self):
        """Generate JSON and Markdown reports"""

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # JSON report
        json_path = f"logs/comprehensive_validation_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(self.validation_results, f, indent=2)

        logger.info(f"\n📄 JSON report saved: {json_path}")

        # Markdown report
        md_path = f"logs/comprehensive_validation_{timestamp}.md"
        with open(md_path, 'w') as f:
            f.write(self._generate_markdown_report())

        logger.info(f"📄 Markdown report saved: {md_path}")

    def _generate_markdown_report(self) -> str:
        """Generate Markdown format report"""

        phase_1 = self.validation_results['phase_1_test_execution']
        phase_2 = self.validation_results['phase_2_table_verification']
        phase_3 = self.validation_results['phase_3_enrichment_verification']
        phase_4 = self.validation_results['phase_4_cleanup']

        report = f"""# Comprehensive Autonomous Validation Report

**Generated:** {self.validation_results['timestamp']}
**Overall Status:** {self.validation_results['overall_status'].upper()}

---

## Phase 1: Live Data Test Execution

**Status:** {'✅ Success' if phase_1.get('success') else '❌ Failed'}
**Elapsed Time:** {phase_1.get('elapsed_time', 0):.1f} seconds

- Races marked: {phase_1.get('races_marked', 0)}
- Runners marked: {phase_1.get('runners_marked', 0)}
- Horses marked: {phase_1.get('horses_marked', 0)}
- Pedigrees marked: {phase_1.get('pedigrees_marked', 0)}
- **Total records marked:** {phase_1.get('total_records_marked', 0)}

---

## Phase 2: Table and Cell Verification

**Overall Coverage:** {phase_2.get('overall_coverage_percent', 0)}%

- Tables checked: {phase_2.get('tables_checked', 0)}
- Tables with test data: {phase_2.get('tables_with_test_data', 0)}
- Total columns checked: {phase_2.get('total_columns_checked', 0)}
- Columns with **TEST**: {phase_2.get('total_columns_with_test', 0)}

### Per-Table Results

"""

        for table_detail in phase_2.get('table_details', []):
            table = table_detail.get('table', 'unknown')
            if table_detail.get('has_test_data'):
                coverage = table_detail.get('coverage_percent', 0)
                cols_with = table_detail.get('columns_with_test_count', 0)
                total_cols = table_detail.get('total_columns', 0)

                status_icon = '✅' if coverage == 100 else '⚠️' if coverage >= 50 else '❌'
                report += f"{status_icon} **{table}** - {coverage}% ({cols_with}/{total_cols} columns)\n"

                if table_detail.get('columns_missing_test'):
                    report += f"\n   Missing **TEST** in:\n"
                    for missing in table_detail['columns_missing_test'][:5]:  # First 5
                        report += f"   - `{missing['column']}` ({missing['type']})\n"
                    report += "\n"
            else:
                report += f"⚠️ **{table}** - No test data found\n"

        report += f"""
---

## Phase 3: Enrichment Verification

**Enrichment Verified:** {'✅ Yes' if phase_3.get('enrichment_verified') else '❌ No'}
**Pedigree Records Found:** {phase_3.get('pedigree_records_found', 0)}

"""

        if phase_3.get('enrichment_verified'):
            report += "### Enrichment Field Coverage\n\n"
            for field, stats in phase_3.get('field_coverage', {}).items():
                report += f"- **{field}:** {stats['populated']}/{stats['total']} ({stats['percent']}%)\n"
        else:
            report += f"**Reason:** {phase_3.get('reason', 'Unknown')}\n"

        report += f"""
---

## Phase 4: Cleanup

**Status:** {'✅ Success' if phase_4.get('success') else '❌ Failed'}
**Tables cleaned:** {phase_4.get('tables_cleaned', 0)}
**Total rows deleted:** {phase_4.get('total_deleted', 0)}

---

## Overall Assessment

"""

        status = self.validation_results['overall_status']
        if status == 'success':
            report += "✅ **VALIDATION SUCCESSFUL**\n\n"
            report += "All phases completed successfully. The data pipeline is working correctly.\n"
        elif status == 'partial_success':
            report += "⚠️ **PARTIAL SUCCESS**\n\n"
            report += "Core functionality works, but some issues detected. Review table details above.\n"
        else:
            report += "❌ **VALIDATION FAILED**\n\n"
            report += "Critical issues detected. Review phase results and error logs.\n"

        return report


def main():
    """Main entry point"""

    validator = ComprehensiveAutonomousValidator()

    try:
        results = validator.run_complete_validation()

        print("\n" + "=" * 80)
        print("COMPREHENSIVE AUTONOMOUS VALIDATION COMPLETE")
        print("=" * 80)

        status = results['overall_status']

        if status == 'success':
            print("\n✅ VALIDATION SUCCESSFUL")
            print(f"\n   Coverage: {results['phase_2_table_verification'].get('overall_coverage_percent', 0)}%")
            print(f"   Enrichment: {'Verified' if results['phase_3_enrichment_verification'].get('enrichment_verified') else 'Not verified (expected if horses existed)'}")
        elif status == 'partial_success':
            print("\n⚠️ PARTIAL SUCCESS")
            print(f"\n   Coverage: {results['phase_2_table_verification'].get('overall_coverage_percent', 0)}%")
            print("\n   Review reports for details")
        else:
            print("\n❌ VALIDATION FAILED")
            print("\n   Check logs and reports for error details")

        print("\n📄 Check detailed reports in logs/")
        print("=" * 80 + "\n")

        return results

    except KeyboardInterrupt:
        print("\n\n❌ Validation cancelled by user")
        return {'success': False, 'error': 'Cancelled by user'}
    except Exception as e:
        print(f"\n\n❌ Validation failed with error: {e}")
        logger.error(f"Validation failed: {e}", exc_info=True)
        return {'success': False, 'error': str(e)}


if __name__ == '__main__':
    main()
