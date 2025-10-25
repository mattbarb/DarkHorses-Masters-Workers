#!/usr/bin/env python3
"""
Validate Racing API Column Capture

Checks if all Racing API-sourced columns are being populated with data.
Goal: 100% capture of all available Racing API fields.

Usage:
    python3 scripts/validate_api_column_capture.py
"""

import sys
import os
import json
from pathlib import Path
from typing import Dict, List
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('validate_api_capture')


class APIColumnValidator:
    """Validates that all Racing API columns are being captured"""

    def __init__(self):
        """Initialize validator"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

        # Load column inventory
        inventory_path = Path(__file__).parent.parent / 'fetchers' / 'docs' / 'COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json'
        with open(inventory_path, 'r') as f:
            self.inventory = json.load(f)

    def get_racing_api_columns(self) -> Dict[str, List[Dict]]:
        """Get all columns that should be sourced from Racing API"""
        api_columns_by_table = {}

        for col in self.inventory['columns']:
            data_source = col.get('data_source', '')

            # Only Racing API sourced columns (not calculated, not system, not odds worker)
            if 'Racing API' in data_source:
                table = col['table']
                if table not in api_columns_by_table:
                    api_columns_by_table[table] = []

                api_columns_by_table[table].append({
                    'column': col['column'],
                    'type': col['type'],
                    'data_source': data_source,
                    'api_endpoint': col.get('api_endpoint', 'N/A'),
                    'field_path': col.get('field_path', 'N/A'),
                    'populated': col.get('populated', 0),
                    'total': col.get('total', 0),
                    'pct_populated': col.get('pct_populated', 0)
                })

        return api_columns_by_table

    def check_column_population(self, table_name: str, column_name: str) -> Dict:
        """Check how many rows have data for a specific column"""
        try:
            # Get total rows
            total_result = self.db_client.client.table(table_name).select('id', count='exact').limit(1).execute()
            total_rows = total_result.count if hasattr(total_result, 'count') else 0

            # Get populated rows (non-null)
            populated_result = self.db_client.client.table(table_name).select(column_name, count='exact').not_.is_(column_name, 'null').limit(1).execute()
            populated_rows = populated_result.count if hasattr(populated_result, 'count') else 0

            pct = (populated_rows / total_rows * 100) if total_rows > 0 else 0

            return {
                'total': total_rows,
                'populated': populated_rows,
                'null': total_rows - populated_rows,
                'pct_populated': round(pct, 2)
            }

        except Exception as e:
            logger.error(f"Error checking {table_name}.{column_name}: {e}")
            return {
                'total': 0,
                'populated': 0,
                'null': 0,
                'pct_populated': 0,
                'error': str(e)
            }

    def validate_all_api_columns(self) -> Dict:
        """Validate all Racing API columns across all tables"""
        logger.info("=" * 80)
        logger.info("VALIDATING RACING API COLUMN CAPTURE")
        logger.info("=" * 80)

        api_columns = self.get_racing_api_columns()

        results = {
            'timestamp': datetime.now().isoformat(),
            'total_tables': len(api_columns),
            'total_columns': sum(len(cols) for cols in api_columns.values()),
            'tables': {}
        }

        for table_name in sorted(api_columns.keys()):
            logger.info(f"\nValidating {table_name}...")

            columns = api_columns[table_name]
            table_results = {
                'total_columns': len(columns),
                'columns_100pct': 0,
                'columns_partial': 0,
                'columns_empty': 0,
                'columns': []
            }

            for col in columns:
                # Check actual population from database
                stats = self.check_column_population(table_name, col['column'])

                col_result = {
                    'column': col['column'],
                    'data_source': col['data_source'],
                    'api_endpoint': col['api_endpoint'],
                    'populated': stats['populated'],
                    'total': stats['total'],
                    'pct_populated': stats['pct_populated']
                }

                if 'error' in stats:
                    col_result['error'] = stats['error']

                # Categorize
                if stats['pct_populated'] == 100:
                    table_results['columns_100pct'] += 1
                    col_result['status'] = '✅ 100%'
                elif stats['pct_populated'] > 0:
                    table_results['columns_partial'] += 1
                    col_result['status'] = f"⚠️  {stats['pct_populated']}%"
                else:
                    table_results['columns_empty'] += 1
                    col_result['status'] = '❌ 0%'

                table_results['columns'].append(col_result)

                # Log if not 100%
                if stats['pct_populated'] < 100:
                    logger.warning(f"  {col['column']}: {stats['pct_populated']}% populated ({stats['populated']}/{stats['total']})")

            results['tables'][table_name] = table_results

        return results

    def print_summary(self, results: Dict):
        """Print summary of validation"""
        print("\n" + "=" * 80)
        print("RACING API COLUMN CAPTURE VALIDATION SUMMARY")
        print("=" * 80)

        total_cols = results['total_columns']
        total_100 = sum(t['columns_100pct'] for t in results['tables'].values())
        total_partial = sum(t['columns_partial'] for t in results['tables'].values())
        total_empty = sum(t['columns_empty'] for t in results['tables'].values())

        print(f"\nTotal Racing API Columns: {total_cols}")
        print(f"  ✅ 100% Populated: {total_100} ({total_100/total_cols*100:.1f}%)")
        print(f"  ⚠️  Partially Populated: {total_partial} ({total_partial/total_cols*100:.1f}%)")
        print(f"  ❌ Empty (0%): {total_empty} ({total_empty/total_cols*100:.1f}%)")

        print(f"\n{'-' * 80}")
        print("BY TABLE:")
        print(f"{'-' * 80}")

        for table_name in sorted(results['tables'].keys()):
            table = results['tables'][table_name]
            print(f"\n{table_name}:")
            print(f"  Total: {table['total_columns']} | ✅ {table['columns_100pct']} | ⚠️  {table['columns_partial']} | ❌ {table['columns_empty']}")

            # Show problematic columns
            problematic = [c for c in table['columns'] if c['pct_populated'] < 100]
            if problematic:
                print(f"  NEEDS ATTENTION:")
                for col in problematic:
                    print(f"    - {col['column']}: {col['status']} (Source: {col['data_source']})")

        print(f"\n{'=' * 80}")

        # Overall status
        if total_empty > 0 or total_partial > 0:
            print(f"\n⚠️  ACTION REQUIRED: {total_empty + total_partial} columns need attention")
            print("   Review the columns marked with ⚠️  or ❌ above")
        else:
            print(f"\n✅ ALL RACING API COLUMNS ARE 100% POPULATED!")

        print(f"\n{'=' * 80}")

    def export_json(self, results: Dict) -> str:
        """Export results to JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"logs/api_column_validation_{timestamp}.json"

        os.makedirs('logs', exist_ok=True)

        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"Results exported to: {filename}")
        return filename


def main():
    """Main execution"""
    validator = APIColumnValidator()
    results = validator.validate_all_api_columns()
    validator.print_summary(results)
    filename = validator.export_json(results)

    print(f"\nDetailed results saved to: {filename}")

    return results


if __name__ == '__main__':
    main()
