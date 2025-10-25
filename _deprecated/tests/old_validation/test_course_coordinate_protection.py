#!/usr/bin/env python3
"""
Test Course Coordinate Protection

This test verifies that:
1. New courses get coordinates assigned from the validated JSON file
2. Existing courses with coordinates have them preserved (not overwritten)
3. The coordinate helper works correctly
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.course_coordinates import get_course_coordinates, get_coordinates_stats, assign_coordinates_to_course
from utils.logger import get_logger
from datetime import datetime

logger = get_logger(__name__)


def test_coordinate_helper():
    """Test the coordinate helper functions"""
    print("\n" + "=" * 60)
    print("TEST 1: Coordinate Helper")
    print("=" * 60)

    # Get stats
    stats = get_coordinates_stats()
    print(f"✓ Cache loaded: {stats['cache_loaded']}")
    print(f"✓ Total courses: {stats['total_courses']}")
    print(f"✓ GB courses: {stats['gb_courses']}")
    print(f"✓ IRE courses: {stats['ire_courses']}")

    # Test coordinate lookup
    test_coords = get_course_coordinates('Aintree', 'GB')
    assert test_coords is not None, "Aintree coordinates should be found"
    print(f"✓ Aintree coordinates: {test_coords}")

    # Test assignment
    course_record = {
        'id': 'test_001',
        'name': 'Cheltenham',
        'region_code': 'gb',
        'latitude': None,
        'longitude': None
    }
    updated_record = assign_coordinates_to_course(course_record)
    assert updated_record.get('latitude') is not None, "Cheltenham should have coordinates assigned"
    print(f"✓ Cheltenham assigned: {updated_record['latitude']}, {updated_record['longitude']}")

    print("\n✅ Coordinate helper test PASSED\n")


def test_coordinate_preservation():
    """Test that existing coordinates are preserved"""
    print("=" * 60)
    print("TEST 2: Coordinate Preservation")
    print("=" * 60)

    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=100
    )

    # Get current coordinates for a known course
    response = db_client.client.table('ra_mst_courses').select(
        'id, name, latitude, longitude'
    ).eq('name', 'Aintree').execute()

    if not response.data:
        print("⚠️  Aintree not found in database - skipping preservation test")
        return

    aintree_before = response.data[0]
    original_lat = aintree_before.get('latitude')
    original_lon = aintree_before.get('longitude')

    print(f"Aintree current coordinates: {original_lat}, {original_lon}")

    # Simulate a course update (this would happen during a fetch)
    test_courses = [{
        'id': aintree_before['id'],
        'name': 'Aintree',
        'region_code': 'gb',
        'region': 'Great Britain',
        'latitude': 99.99999,  # Deliberately wrong - should be ignored
        'longitude': 99.99999,  # Deliberately wrong - should be ignored
        'created_at': datetime.utcnow().isoformat(),
        'updated_at': datetime.utcnow().isoformat()
    }]

    # The insert_courses method should preserve existing coordinates
    result = db_client.insert_courses(test_courses)
    print(f"Update result: {result}")

    # Check that coordinates were NOT overwritten
    response_after = db_client.client.table('ra_mst_courses').select(
        'id, name, latitude, longitude'
    ).eq('name', 'Aintree').execute()

    aintree_after = response_after.data[0]
    final_lat = aintree_after.get('latitude')
    final_lon = aintree_after.get('longitude')

    print(f"Aintree after update: {final_lat}, {final_lon}")

    # Verify coordinates were preserved
    assert abs(final_lat - original_lat) < 0.0001, "Latitude should be preserved"
    assert abs(final_lon - original_lon) < 0.0001, "Longitude should be preserved"

    print("\n✅ Coordinate preservation test PASSED")
    print("   Coordinates were successfully protected from overwrite\n")


def test_new_course_assignment():
    """Test that new courses get coordinates assigned"""
    print("=" * 60)
    print("TEST 3: New Course Coordinate Assignment")
    print("=" * 60)

    # Simulate a new course being fetched
    new_course = {
        'id': 'test_new_course',
        'name': 'Ascot',
        'region_code': 'gb',
        'latitude': None,
        'longitude': None
    }

    # Should get coordinates assigned
    updated_course = assign_coordinates_to_course(new_course)

    assert updated_course.get('latitude') is not None, "New course should get coordinates"
    assert updated_course.get('longitude') is not None, "New course should get coordinates"

    print(f"✓ New course 'Ascot' assigned: {updated_course['latitude']}, {updated_course['longitude']}")
    print("\n✅ New course assignment test PASSED\n")


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("COURSE COORDINATE PROTECTION TESTS")
    print("=" * 60)

    try:
        test_coordinate_helper()
        test_new_course_assignment()
        test_coordinate_preservation()

        print("=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nSummary:")
        print("  ✓ Coordinate helper works correctly")
        print("  ✓ New courses get coordinates assigned")
        print("  ✓ Existing coordinates are preserved")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
