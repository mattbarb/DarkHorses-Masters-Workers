"""
Cleanup Test Data Script
Removes all **TEST** prefixed records from all tables

Usage:
    python3 tests/cleanup_test_data.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient


def cleanup_test_data(config):
    """Remove all test records from all tables"""
    print("=" * 80)
    print("CLEANING UP TEST DATA")
    print("=" * 80)

    db = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    tables = [
        ('ra_courses', 'id'),
        ('ra_bookmakers', 'code'),
        ('ra_jockeys', 'id'),
        ('ra_trainers', 'id'),
        ('ra_owners', 'id'),
        ('ra_horses', 'id')
    ]

    cleanup_results = {}

    for table, id_col in tables:
        try:
            # Delete test records
            if id_col == 'code':
                result = db.client.table(table).delete().like('code', '**TEST**%').execute()
            else:
                result = db.client.table(table).delete().like('id', '**TEST**%').execute()

            count = len(result.data) if result.data else 0
            cleanup_results[table] = {
                'deleted': count,
                'status': '✓'
            }

            print(f"✓ {table:20} - Deleted: {count} test records")

        except Exception as e:
            cleanup_results[table] = {
                'deleted': 0,
                'status': '✗',
                'error': str(e)
            }
            print(f"✗ {table:20} - ERROR: {e}")

    print("\n" + "=" * 80)
    print("CLEANUP COMPLETE")
    print("=" * 80)

    total_deleted = sum(r['deleted'] for r in cleanup_results.values())
    print(f"\nTotal records deleted: {total_deleted}")

    return cleanup_results


def main():
    """Main execution"""
    config = get_config()
    cleanup_results = cleanup_test_data(config)

    # Check if any errors occurred
    errors = [table for table, result in cleanup_results.items() if result['status'] == '✗']

    if errors:
        print(f"\n✗ Errors occurred in: {', '.join(errors)}")
        return 1
    else:
        print("\n✓ All test data cleaned up successfully")
        return 0


if __name__ == '__main__':
    exit(main())
