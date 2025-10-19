#!/usr/bin/env python3
"""
Critical Data Quality Audit for DarkHorses Reference Tables
Analyzes 5 tables: ra_jockeys, ra_trainers, ra_owners, ra_courses, ra_bookmakers
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from utils.supabase_client import SupabaseReferenceClient


class DataQualityAuditor:
    """Comprehensive data quality audit"""

    def __init__(self):
        self.config = get_config()
        self.db = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key
        )
        self.results = {
            'audit_timestamp': datetime.now().isoformat(),
            'tables': {}
        }

    def get_table_schema(self, table_name: str) -> List[Dict]:
        """Get actual table schema from database"""
        # Use a sample query to infer schema from the actual table
        # This is a workaround since we can't execute arbitrary SQL
        try:
            result = self.db.client.from_(table_name).select('*').limit(1).execute()

            # Get column names from the first row (if exists) or from the response structure
            if result.data and len(result.data) > 0:
                columns = list(result.data[0].keys())
            else:
                # Even with no data, we can still get column structure
                # by making a request and checking what fields are available
                columns = []

            # Return simplified schema (we'll get more details from actual queries)
            return [{'column_name': col, 'data_type': 'unknown', 'is_nullable': 'YES'} for col in columns]
        except Exception as e:
            print(f"Error getting schema for {table_name}: {e}")
            return []

    def get_column_population_stats(self, table_name: str, columns: List[str]) -> Dict:
        """Get population statistics for each column"""
        stats = {}

        # First get total row count
        result = self.db.client.from_(table_name).select('*', count='exact').limit(0).execute()
        total_rows = result.count

        if total_rows == 0:
            return {'total_rows': 0, 'columns': {}}

        # For each column, get null count
        for col in columns:
            try:
                # Count non-null values
                non_null = self.db.client.from_(table_name).select(col, count='exact').not_.is_(col, 'null').limit(0).execute()
                non_null_count = non_null.count
                null_count = total_rows - non_null_count
                population_pct = round((non_null_count / total_rows) * 100, 2) if total_rows > 0 else 0

                stats[col] = {
                    'non_null_count': non_null_count,
                    'null_count': null_count,
                    'population_pct': population_pct
                }
            except Exception as e:
                stats[col] = {'error': str(e)}

        return {
            'total_rows': total_rows,
            'columns': stats
        }

    def check_empty_strings(self, table_name: str, text_columns: List[str]) -> Dict:
        """Check for empty strings vs NULL"""
        empty_string_stats = {}

        for col in text_columns:
            try:
                # Count empty strings
                empty_result = self.db.client.from_(table_name).select(col, count='exact').eq(col, '').limit(0).execute()
                empty_count = empty_result.count

                if empty_count > 0:
                    empty_string_stats[col] = empty_count
            except:
                pass

        return empty_string_stats

    def check_statistics_fields(self, table_name: str) -> Dict:
        """Check if statistics fields exist and are populated"""
        stats_fields = {
            'ra_jockeys': ['total_rides', 'total_wins', 'win_rate', 'stats_updated_at'],
            'ra_trainers': ['total_runners', 'total_wins', 'win_rate', 'recent_14d_runs', 'stats_updated_at'],
            'ra_owners': ['total_horses', 'total_runners', 'total_wins', 'win_rate', 'stats_updated_at']
        }

        if table_name not in stats_fields:
            return {'has_statistics_fields': False}

        expected_fields = stats_fields[table_name]
        result = {
            'has_statistics_fields': True,
            'expected_fields': expected_fields,
            'field_status': {}
        }

        # Check if fields exist
        schema = self.get_table_schema(table_name)
        existing_columns = [col['column_name'] for col in schema]

        for field in expected_fields:
            if field not in existing_columns:
                result['field_status'][field] = 'MISSING'
            else:
                # Check if populated
                try:
                    non_null = self.db.client.from_(table_name).select(field, count='exact').not_.is_(field, 'null').limit(0).execute()
                    if non_null.count > 0:
                        result['field_status'][field] = f'EXISTS_POPULATED ({non_null.count} rows)'
                    else:
                        result['field_status'][field] = 'EXISTS_EMPTY (all NULL)'
                except:
                    result['field_status'][field] = 'EXISTS_UNKNOWN'

        return result

    def audit_table(self, table_name: str) -> Dict:
        """Comprehensive audit of a single table"""
        print(f"\n{'='*80}")
        print(f"Auditing: {table_name}")
        print(f"{'='*80}")

        audit_result = {
            'table_name': table_name,
            'schema': [],
            'population_stats': {},
            'empty_strings': {},
            'statistics_fields': {}
        }

        # 1. Get schema
        print("  [1/4] Getting table schema...")
        schema = self.get_table_schema(table_name)
        audit_result['schema'] = schema
        column_names = [col['column_name'] for col in schema]
        print(f"        Found {len(column_names)} columns")

        # 2. Get population stats
        print("  [2/4] Analyzing column population...")
        population_stats = self.get_column_population_stats(table_name, column_names)
        audit_result['population_stats'] = population_stats
        print(f"        Total rows: {population_stats.get('total_rows', 0)}")

        # 3. Check for empty strings
        print("  [3/4] Checking for empty strings...")
        text_columns = [col['column_name'] for col in schema if 'char' in col['data_type'].lower() or col['data_type'].lower() == 'text']
        empty_strings = self.check_empty_strings(table_name, text_columns)
        audit_result['empty_strings'] = empty_strings
        if empty_strings:
            print(f"        Found empty strings in {len(empty_strings)} columns")
        else:
            print(f"        No empty strings found")

        # 4. Check statistics fields (for jockeys/trainers/owners)
        print("  [4/4] Checking statistics fields...")
        stats_check = self.check_statistics_fields(table_name)
        audit_result['statistics_fields'] = stats_check
        if stats_check.get('has_statistics_fields'):
            print(f"        Statistics fields: {len(stats_check['expected_fields'])} expected")

        return audit_result

    def generate_report(self) -> Dict:
        """Generate comprehensive audit report"""
        tables_to_audit = [
            'ra_jockeys',
            'ra_trainers',
            'ra_owners',
            'ra_courses',
            'ra_bookmakers'
        ]

        print("="*80)
        print("CRITICAL DATA QUALITY AUDIT - DarkHorses Reference Tables")
        print("="*80)
        print(f"Timestamp: {self.results['audit_timestamp']}")
        print(f"Tables: {', '.join(tables_to_audit)}")

        for table in tables_to_audit:
            audit_result = self.audit_table(table)
            self.results['tables'][table] = audit_result

        # Generate summary
        self.results['summary'] = self.generate_summary()

        return self.results

    def generate_summary(self) -> Dict:
        """Generate executive summary"""
        summary = {
            'total_tables_audited': len(self.results['tables']),
            'critical_issues': [],
            'recommendations': []
        }

        for table_name, audit in self.results['tables'].items():
            total_rows = audit['population_stats'].get('total_rows', 0)

            # Check for low population columns
            for col, stats in audit['population_stats'].get('columns', {}).items():
                if isinstance(stats, dict) and 'population_pct' in stats:
                    if stats['population_pct'] < 10 and stats['population_pct'] > 0:
                        summary['critical_issues'].append({
                            'table': table_name,
                            'column': col,
                            'issue': f"Low population: {stats['population_pct']}%",
                            'severity': 'MEDIUM'
                        })
                    elif stats['population_pct'] == 0 and total_rows > 0:
                        summary['critical_issues'].append({
                            'table': table_name,
                            'column': col,
                            'issue': 'Completely empty (100% NULL)',
                            'severity': 'HIGH'
                        })

            # Check statistics fields
            stats_fields = audit.get('statistics_fields', {})
            if stats_fields.get('has_statistics_fields'):
                for field, status in stats_fields.get('field_status', {}).items():
                    if status == 'MISSING':
                        summary['critical_issues'].append({
                            'table': table_name,
                            'column': field,
                            'issue': 'Statistics field missing from schema',
                            'severity': 'CRITICAL'
                        })
                    elif 'EXISTS_EMPTY' in status:
                        summary['critical_issues'].append({
                            'table': table_name,
                            'column': field,
                            'issue': 'Statistics field never calculated (all NULL)',
                            'severity': 'HIGH'
                        })

        # Generate recommendations
        if any(issue['severity'] == 'CRITICAL' for issue in summary['critical_issues']):
            summary['recommendations'].append('RUN MIGRATION 007 IMMEDIATELY - Critical statistics fields missing')

        if any('never calculated' in issue['issue'] for issue in summary['critical_issues']):
            summary['recommendations'].append('RUN statistics calculation script - Fields exist but unpopulated')

        return summary

    def save_results(self, filename: str = 'data_quality_audit_results.json'):
        """Save audit results to JSON file"""
        filepath = os.path.join(os.path.dirname(__file__), filename)
        with open(filepath, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        print(f"\n{'='*80}")
        print(f"Results saved to: {filepath}")
        print(f"{'='*80}")
        return filepath


def main():
    """Run the audit"""
    auditor = DataQualityAuditor()
    results = auditor.generate_report()

    # Print summary
    print("\n" + "="*80)
    print("EXECUTIVE SUMMARY")
    print("="*80)
    summary = results['summary']
    print(f"\nTables Audited: {summary['total_tables_audited']}")
    print(f"Critical Issues Found: {len(summary['critical_issues'])}")

    if summary['critical_issues']:
        print("\nISSUES BY SEVERITY:")
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            issues = [i for i in summary['critical_issues'] if i['severity'] == severity]
            if issues:
                print(f"\n  {severity} ({len(issues)} issues):")
                for issue in issues[:5]:  # Show first 5
                    print(f"    - {issue['table']}.{issue['column']}: {issue['issue']}")
                if len(issues) > 5:
                    print(f"    ... and {len(issues) - 5} more")

    if summary['recommendations']:
        print("\nRECOMMENDATIONS:")
        for rec in summary['recommendations']:
            print(f"  • {rec}")

    # Save results
    auditor.save_results()

    print("\n" + "="*80)
    print("AUDIT COMPLETE")
    print("="*80)


if __name__ == '__main__':
    main()
