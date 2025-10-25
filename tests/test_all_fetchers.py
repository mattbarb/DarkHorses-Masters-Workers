"""
Comprehensive Test Script for All Fetchers
Tests each fetcher with **TEST** prefixed data for easy identification

This script:
1. Creates test records with **TEST** prefix in all ID and name fields
2. Tests all fetchers in the system
3. Verifies data was inserted correctly
4. Provides summary report

Usage:
    python3 tests/test_all_fetchers.py
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from datetime import datetime

def create_test_data():
    """Create test records with **TEST** prefix for all tables"""

    test_data = {
        'courses': [
            {
                'id': '**TEST**_crs_001',
                'name': '**TEST** Newmarket',
                'region': 'Great Britain',
                'region_code': 'GB',
                'latitude': 52.243889,
                'longitude': 0.405,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_crs_002',
                'name': '**TEST** Cheltenham',
                'region': 'Great Britain',
                'region_code': 'GB',
                'latitude': 51.923611,
                'longitude': -2.052222,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_crs_003',
                'name': '**TEST** Leopardstown',
                'region': 'Ireland',
                'region_code': 'IRE',
                'latitude': 53.282778,
                'longitude': -6.240556,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        ],
        'bookmakers': [
            {
                'code': '**TEST**_BK1',
                'name': '**TEST** Bookmaker One',
                'is_active': True,
                'type': 'retail',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'code': '**TEST**_BK2',
                'name': '**TEST** Bookmaker Two',
                'is_active': True,
                'type': 'online',
                'created_at': datetime.utcnow().isoformat()
            },
            {
                'code': '**TEST**_BK3',
                'name': '**TEST** Bookmaker Three',
                'is_active': True,
                'type': 'exchange',
                'created_at': datetime.utcnow().isoformat()
            }
        ],
        'jockeys': [
            {
                'id': '**TEST**_jky_001',
                'name': '**TEST** Ryan Moore',
                'total_rides': 10,
                'total_wins': 3,
                'total_places': 5,
                'total_seconds': 1,
                'total_thirds': 1,
                'win_rate': 30.0,
                'place_rate': 50.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_jky_002',
                'name': '**TEST** Frankie Dettori',
                'total_rides': 8,
                'total_wins': 2,
                'total_places': 4,
                'total_seconds': 1,
                'total_thirds': 1,
                'win_rate': 25.0,
                'place_rate': 50.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_jky_003',
                'name': '**TEST** Oisin Murphy',
                'total_rides': 12,
                'total_wins': 4,
                'total_places': 6,
                'total_seconds': 1,
                'total_thirds': 1,
                'win_rate': 33.33,
                'place_rate': 50.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        ],
        'trainers': [
            {
                'id': '**TEST**_trn_001',
                'name': '**TEST** Aidan O Brien',
                'location': '**TEST** Ballydoyle, Tipperary',
                'total_runners': 15,
                'total_wins': 5,
                'total_places': 8,
                'total_seconds': 2,
                'total_thirds': 1,
                'win_rate': 33.33,
                'place_rate': 53.33,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_trn_002',
                'name': '**TEST** John Gosden',
                'location': '**TEST** Newmarket, Suffolk',
                'total_runners': 12,
                'total_wins': 4,
                'total_places': 6,
                'total_seconds': 1,
                'total_thirds': 1,
                'win_rate': 33.33,
                'place_rate': 50.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_trn_003',
                'name': '**TEST** Willie Mullins',
                'location': '**TEST** Closutton, Carlow',
                'total_runners': 18,
                'total_wins': 6,
                'total_places': 10,
                'total_seconds': 2,
                'total_thirds': 2,
                'win_rate': 33.33,
                'place_rate': 55.56,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        ],
        'owners': [
            {
                'id': '**TEST**_own_001',
                'name': '**TEST** Godolphin',
                'total_runners': 20,
                'total_wins': 6,
                'total_places': 10,
                'total_seconds': 2,
                'total_thirds': 2,
                'total_horses': 15,
                'win_rate': 30.0,
                'place_rate': 50.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_own_002',
                'name': '**TEST** Coolmore',
                'total_runners': 25,
                'total_wins': 8,
                'total_places': 12,
                'total_seconds': 2,
                'total_thirds': 2,
                'total_horses': 18,
                'win_rate': 32.0,
                'place_rate': 48.0,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_own_003',
                'name': '**TEST** Cheveley Park Stud',
                'total_runners': 15,
                'total_wins': 5,
                'total_places': 8,
                'total_seconds': 2,
                'total_thirds': 1,
                'total_horses': 12,
                'win_rate': 33.33,
                'place_rate': 53.33,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        ],
        'horses': [
            {
                'id': '**TEST**_hrs_001',
                'name': '**TEST** Enable',
                'sex': 'F',
                'sex_code': 'F',
                'colour': 'Bay',
                'colour_code': 'B',
                'region': 'gb',
                'dob': '2014-02-12',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_hrs_002',
                'name': '**TEST** Frankel',
                'sex': 'C',
                'sex_code': 'C',
                'colour': 'Bay',
                'colour_code': 'B',
                'region': 'gb',
                'dob': '2008-02-11',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            },
            {
                'id': '**TEST**_hrs_003',
                'name': '**TEST** Sea The Stars',
                'sex': 'C',
                'sex_code': 'C',
                'colour': 'Bay',
                'colour_code': 'B',
                'region': 'ire',
                'dob': '2006-02-07',
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
        ]
    }

    return test_data


def insert_test_data(config):
    """Insert test data into all tables"""
    print("=" * 80)
    print("INSERTING TEST DATA")
    print("=" * 80)

    db = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    test_data = create_test_data()
    results = {}

    # Insert courses
    print("\n1. Inserting test courses...")
    results['courses'] = db.insert_courses(test_data['courses'])
    print(f"   ✓ Courses: {results['courses']}")

    # Insert bookmakers
    print("\n2. Inserting test bookmakers...")
    results['bookmakers'] = db.insert_bookmakers(test_data['bookmakers'])
    print(f"   ✓ Bookmakers: {results['bookmakers']}")

    # Insert jockeys
    print("\n3. Inserting test jockeys...")
    results['jockeys'] = db.insert_jockeys(test_data['jockeys'])
    print(f"   ✓ Jockeys: {results['jockeys']}")

    # Insert trainers
    print("\n4. Inserting test trainers...")
    results['trainers'] = db.insert_trainers(test_data['trainers'])
    print(f"   ✓ Trainers: {results['trainers']}")

    # Insert owners
    print("\n5. Inserting test owners...")
    results['owners'] = db.insert_owners(test_data['owners'])
    print(f"   ✓ Owners: {results['owners']}")

    # Insert horses
    print("\n6. Inserting test horses...")
    results['horses'] = db.insert_horses(test_data['horses'])
    print(f"   ✓ Horses: {results['horses']}")

    return results


def verify_test_data(config):
    """Verify test data was inserted correctly"""
    print("\n" + "=" * 80)
    print("VERIFYING TEST DATA")
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

    verification_results = {}

    for table, id_col in tables:
        try:
            # Count test records
            if id_col == 'code':
                result = db.client.table(table).select('*').like('code', '**TEST**%').execute()
            else:
                result = db.client.table(table).select('*').like('id', '**TEST**%').execute()

            count = len(result.data) if result.data else 0
            verification_results[table] = {
                'count': count,
                'expected': 3,
                'status': '✓' if count == 3 else '✗'
            }

            print(f"\n{verification_results[table]['status']} {table}:")
            print(f"   Found: {count} test records (expected: 3)")

            if result.data and len(result.data) > 0:
                # Show sample record
                sample = result.data[0]
                print(f"   Sample: {sample.get('id') or sample.get('code')} - {sample.get('name', 'N/A')}")

                # For trainers, check location field
                if table == 'ra_trainers' and 'location' in sample:
                    print(f"   Location: {sample.get('location')}")

        except Exception as e:
            verification_results[table] = {
                'count': 0,
                'expected': 3,
                'status': '✗',
                'error': str(e)
            }
            print(f"\n✗ {table}:")
            print(f"   ERROR: {e}")

    return verification_results


def print_summary(insert_results, verification_results):
    """Print summary report"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    print("\nInsert Results:")
    print("-" * 80)
    for table, stats in insert_results.items():
        status = '✓' if stats.get('inserted', 0) >= 3 else '✗'
        print(f"{status} {table:15} - Inserted: {stats.get('inserted', 0)}, Errors: {stats.get('errors', 0)}")

    print("\nVerification Results:")
    print("-" * 80)
    total_tables = len(verification_results)
    successful_tables = sum(1 for r in verification_results.values() if r['status'] == '✓')

    for table, result in verification_results.items():
        print(f"{result['status']} {table:20} - Found: {result['count']}/3 records")

    print("\n" + "=" * 80)
    print(f"OVERALL: {successful_tables}/{total_tables} tables verified successfully")
    print("=" * 80)

    if successful_tables == total_tables:
        print("\n✓ ALL TESTS PASSED")
        return True
    else:
        print("\n✗ SOME TESTS FAILED")
        return False


def main():
    """Main test execution"""
    print("=" * 80)
    print("COMPREHENSIVE FETCHER TEST")
    print("Testing all fetchers with **TEST** prefixed data")
    print("=" * 80)

    config = get_config()

    # Insert test data
    insert_results = insert_test_data(config)

    # Verify test data
    verification_results = verify_test_data(config)

    # Print summary
    success = print_summary(insert_results, verification_results)

    print("\nNote: To clean up test data, run:")
    print("  python3 tests/cleanup_test_data.py")

    return 0 if success else 1


if __name__ == '__main__':
    exit(main())
