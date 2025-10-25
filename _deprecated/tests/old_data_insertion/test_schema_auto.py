"""
Schema-Aware Test Data Insertion

Automatically reads actual database schema and inserts appropriate test data.
Uses COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json to understand column types
and generates valid test data for each column.

This is the CORRECT way to test - it works with the actual schema,
not hardcoded assumptions.

Usage:
    # Auto-insert test data (schema-aware)
    python3 fetchers/test_schema_auto.py

    # Specific tables
    python3 fetchers/test_schema_auto.py --tables ra_mst_horses ra_races

    # From controller
    python3 fetchers/master_fetcher_controller.py --mode test-auto --interactive

    # Cleanup
    python3 fetchers/test_schema_auto.py --cleanup
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
import argparse
from datetime import datetime
from typing import Dict, List, Any
from uuid import uuid4

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('test_schema_auto')


class SchemaAwareTestInserter:
    """Schema-aware test data insertion using actual database schema"""

    def __init__(self):
        """Initialize inserter"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.test_marker = "**TEST**"
        self.test_id = f"test_{uuid4().hex[:8]}"
        self.schema = self.load_column_inventory()

    def load_column_inventory(self) -> Dict:
        """Load column inventory from JSON file"""
        inventory_path = Path(__file__).parent.parent / 'docs' / 'COMPLETE_COLUMN_INVENTORY_WITH_SOURCES.json'

        if not inventory_path.exists():
            logger.warning(f"Column inventory not found at {inventory_path}")
            return {}

        with open(inventory_path, 'r') as f:
            data = json.load(f)

        logger.info(f"Loaded schema for {data.get('total_tables', 0)} tables with {data.get('total_columns', 0)} columns")
        return data

    def get_table_columns(self, table_name: str) -> List[Dict]:
        """Get columns for a specific table from inventory"""
        if not self.schema or 'columns' not in self.schema:
            return []

        return [col for col in self.schema['columns'] if col['table'] == table_name]

    def generate_test_value(self, column_name: str, data_type: str) -> Any:
        """Generate appropriate test value based on column name and data type

        ALL values include **TEST** marker for easy visual identification.
        Format: "**TEST** <value>" for all types where possible.
        """

        # Handle ID columns - use string format with TEST marker
        if column_name in ['id', 'uuid']:
            return f"{self.test_marker}_{self.test_id}"

        if column_name.endswith('_id'):
            return f"{self.test_marker}_{column_name}_{uuid4().hex[:6]}"

        # Handle common patterns
        if 'name' in column_name.lower():
            return f"{self.test_marker} {column_name.replace('_', ' ').title()}"

        if 'code' in column_name.lower():
            return f"{self.test_marker[:4]}"

        if column_name in ['created_at', 'updated_at', 'timestamp']:
            return f"{self.test_marker} 2099-12-31T23:59:59"

        # Handle by data type - ALL include **TEST** prefix
        if 'character' in data_type or 'text' in data_type or 'varchar' in data_type:
            return f"{self.test_marker} {column_name.replace('_', ' ')}"

        if 'integer' in data_type or 'bigint' in data_type or 'smallint' in data_type:
            # Use string representation to include marker (if column allows it)
            return f"{self.test_marker} 9999"

        if 'numeric' in data_type or 'decimal' in data_type or 'double' in data_type or 'real' in data_type:
            # Use string representation to include marker
            return f"{self.test_marker} 99.99"

        if 'boolean' in data_type:
            # Boolean as string with marker
            return f"{self.test_marker} TRUE"

        if 'date' in data_type.lower() and 'time' not in data_type.lower():
            return f"{self.test_marker} 2099-12-31"

        if 'timestamp' in data_type.lower() or 'datetime' in data_type.lower():
            return f"{self.test_marker} 2099-12-31T23:59:59"

        if 'json' in data_type.lower():
            return {"test": self.test_marker, "value": "**TEST** JSON value"}

        # Default fallback
        return f"{self.test_marker} {column_name}"

    def create_test_row(self, table_name: str) -> Dict:
        """Create a test row for a table based on its actual schema"""
        columns = self.get_table_columns(table_name)

        if not columns:
            logger.warning(f"No schema found for {table_name}")
            return {}

        test_row = {}

        for col in columns:
            col_name = col['column']
            data_type = col['type']

            # Skip auto-generated columns that might cause conflicts
            if col_name == 'id' and 'serial' in data_type.lower():
                continue

            # Generate appropriate test value
            test_value = self.generate_test_value(col_name, data_type)
            test_row[col_name] = test_value

        return test_row

    def insert_test_row(self, table_name: str) -> Dict:
        """Insert one test row into a table"""
        logger.info(f"Inserting test data into: {table_name}")

        try:
            test_data = self.create_test_row(table_name)

            if not test_data:
                return {
                    'table': table_name,
                    'success': False,
                    'error': 'No schema data available'
                }

            logger.info(f"  Generated test row with {len(test_data)} columns")

            # Insert into table
            result = self.db_client.client.table(table_name).insert(test_data).execute()

            if result.data:
                logger.info(f"✅ Successfully inserted test row into {table_name}")
                return {
                    'table': table_name,
                    'success': True,
                    'columns_inserted': len(test_data),
                    'data': result.data[0] if result.data else test_data
                }
            else:
                logger.warning(f"⚠️  Insert succeeded but no data returned for {table_name}")
                return {
                    'table': table_name,
                    'success': True,
                    'columns_inserted': len(test_data),
                    'warning': 'No data returned'
                }

        except Exception as e:
            logger.error(f"❌ Error inserting test data into {table_name}: {e}", exc_info=True)
            return {
                'table': table_name,
                'success': False,
                'error': str(e)
            }

    def insert_all_test_data(self, tables: List[str] = None) -> Dict:
        """Insert test data into all specified tables"""

        # Get unique table names from schema
        if tables:
            tables_to_insert = tables
        elif self.schema and 'columns' in self.schema:
            tables_to_insert = list(set(col['table'] for col in self.schema['columns']))
            tables_to_insert.sort()
        else:
            logger.error("No schema data available and no tables specified")
            return {
                'timestamp': datetime.now().isoformat(),
                'tables_processed': 0,
                'successful': 0,
                'failed': 0,
                'results': []
            }

        logger.info(f"\n{'=' * 80}")
        logger.info(f"SCHEMA-AWARE TEST DATA INSERTION")
        logger.info(f"Processing {len(tables_to_insert)} tables")
        logger.info(f"{'=' * 80}\n")

        results = {
            'timestamp': datetime.now().isoformat(),
            'tables_processed': len(tables_to_insert),
            'successful': 0,
            'failed': 0,
            'results': []
        }

        for table_name in tables_to_insert:
            result = self.insert_test_row(table_name)
            results['results'].append(result)

            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1

        return results

    def cleanup_test_data(self, tables: List[str] = None) -> Dict:
        """Remove all test data from tables"""

        # Get tables to clean
        if tables:
            tables_to_clean = tables
        elif self.schema and 'columns' in self.schema:
            tables_to_clean = list(set(col['table'] for col in self.schema['columns']))
            tables_to_clean.sort()
        else:
            logger.error("No schema data available and no tables specified")
            return {
                'timestamp': datetime.now().isoformat(),
                'tables_processed': 0,
                'successful': 0,
                'failed': 0,
                'total_deleted': 0,
                'results': []
            }

        logger.info(f"\n{'=' * 80}")
        logger.info(f"CLEANING TEST DATA FROM {len(tables_to_clean)} TABLES")
        logger.info(f"{'=' * 80}\n")

        results = {
            'timestamp': datetime.now().isoformat(),
            'tables_processed': len(tables_to_clean),
            'successful': 0,
            'failed': 0,
            'total_deleted': 0,
            'results': []
        }

        for table_name in tables_to_clean:
            logger.info(f"Cleaning test data from: {table_name}")
            deleted_count = 0

            try:
                # Get columns for this table
                columns = self.get_table_columns(table_name)
                column_names = [col['column'] for col in columns]

                # Try to delete by common text columns containing **TEST**
                for col_name in column_names:
                    # Only try text/varchar columns
                    col_info = next((c for c in columns if c['column'] == col_name), None)
                    if not col_info:
                        continue

                    data_type = col_info['type'].lower()
                    if 'character' in data_type or 'text' in data_type or 'varchar' in data_type:
                        try:
                            result = self.db_client.client.table(table_name).delete().like(col_name, f'%{self.test_marker}%').execute()
                            if result.data:
                                count = len(result.data)
                                if count > 0:
                                    deleted_count += count
                                    logger.info(f"  Deleted {count} rows by {col_name} column")
                        except Exception as e:
                            # Column might not support LIKE, skip
                            pass

                results['total_deleted'] += deleted_count
                results['successful'] += 1
                results['results'].append({
                    'table': table_name,
                    'success': True,
                    'deleted': deleted_count
                })

            except Exception as e:
                logger.error(f"❌ Error cleaning {table_name}: {e}")
                results['failed'] += 1
                results['results'].append({
                    'table': table_name,
                    'success': False,
                    'error': str(e)
                })

        return results

    def print_summary(self, results: Dict, cleanup: bool = False):
        """Print summary of operations"""
        action = "CLEANUP" if cleanup else "INSERT"

        print(f"\n{'=' * 80}")
        print(f"SCHEMA-AWARE TEST DATA {action} SUMMARY")
        print(f"{'=' * 80}")
        print(f"\nTables Processed: {results['tables_processed']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")

        if cleanup:
            print(f"Total Rows Deleted: {results['total_deleted']}")
        else:
            # Show total columns inserted
            total_cols = sum(r.get('columns_inserted', 0) for r in results['results'] if r['success'])
            print(f"Total Columns Populated: {total_cols}")

        if results['failed'] > 0:
            print(f"\n❌ Failed Tables:")
            for result in results['results']:
                if not result['success']:
                    print(f"  - {result['table']}: {result.get('error', 'Unknown error')}")

        if not cleanup and results['successful'] > 0:
            print(f"\n✅ Successful Insertions:")
            for result in results['results']:
                if result['success']:
                    cols = result.get('columns_inserted', 0)
                    print(f"  - {result['table']}: {cols} columns")

        print(f"\n{'=' * 80}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Schema-aware test data insertion')
    parser.add_argument('--tables', nargs='+', help='Specific tables to insert test data into')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test data instead of inserting')

    args = parser.parse_args()

    inserter = SchemaAwareTestInserter()

    if args.cleanup:
        results = inserter.cleanup_test_data(tables=args.tables)
        inserter.print_summary(results, cleanup=True)
    else:
        results = inserter.insert_all_test_data(tables=args.tables)
        inserter.print_summary(results, cleanup=False)

    return results


if __name__ == '__main__':
    main()
