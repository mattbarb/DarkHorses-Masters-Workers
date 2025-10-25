#!/usr/bin/env python3
"""
Update Course Coordinates

This script updates the ra_courses table with latitude and longitude coordinates
from the validated coordinates JSON file.

Data source: DarkHorses-Course-Cordinates-Fetcher/ra_courses_final_validated.json

Usage:
    python3 scripts/update_course_coordinates.py [--dry-run]

Options:
    --dry-run    Print what would be updated without making changes
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger(__name__)

# Path to coordinates JSON file
COORDINATES_FILE = Path(__file__).parent.parent.parent / "DarkHorses-Local-Development-Workspace" / "DarkHorses-Course-Cordinates-Fetcher" / "ra_courses_final_validated.json"


def load_coordinates() -> List[Dict]:
    """Load coordinates from JSON file."""
    logger.info(f"Loading coordinates from: {COORDINATES_FILE}")

    if not COORDINATES_FILE.exists():
        raise FileNotFoundError(f"Coordinates file not found: {COORDINATES_FILE}")

    with open(COORDINATES_FILE, 'r') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} course records with coordinates")
    return data


def match_course_by_id(course_id: str, courses_data: List[Dict]) -> Optional[Dict]:
    """Match a course by course_id in the JSON data."""
    for course in courses_data:
        if course.get('course_id') == course_id:
            return course
    return None


def match_course_by_code(code: str, courses_data: List[Dict]) -> Optional[Dict]:
    """Match a course by code in the JSON data."""
    for course in courses_data:
        if course.get('code') == code:
            return course
    return None


def get_database_courses(db_client: SupabaseReferenceClient) -> List[Dict]:
    """Fetch all courses from the database."""
    logger.info("Fetching courses from database...")

    response = db_client.client.table('ra_courses').select('id, name, region_code').execute()

    if not response.data:
        logger.warning("No courses found in database")
        return []

    logger.info(f"Found {len(response.data)} courses in database")
    return response.data


def prepare_updates(db_courses: List[Dict], coordinates_data: List[Dict]) -> Tuple[List[Dict], List[str]]:
    """
    Prepare coordinate updates by matching database courses with JSON data.

    Returns:
        Tuple of (updates, unmatched_course_ids)
        - updates: List of dicts with id, latitude, longitude
        - unmatched_course_ids: List of IDs that couldn't be matched
    """
    updates = []
    unmatched = []

    for db_course in db_courses:
        db_id = db_course['id']
        db_name = db_course.get('name', 'Unknown')

        # Try matching by course_id in JSON (which corresponds to db 'id')
        match = match_course_by_id(db_id, coordinates_data)

        # If no match by ID, try matching by name
        if not match:
            for course in coordinates_data:
                if course.get('course', '').lower() == db_name.lower():
                    match = course
                    break

        if match:
            lat = match.get('latitude')
            lon = match.get('longitude')

            if lat is not None and lon is not None:
                updates.append({
                    'id': db_id,
                    'latitude': lat,
                    'longitude': lon,
                    'course_name': db_name,
                    'code': match.get('code', '')
                })
                logger.debug(f"Matched {db_id} ({db_name}): {lat}, {lon}")
            else:
                logger.warning(f"Course {db_id} matched but missing coordinates")
                unmatched.append(db_id)
        else:
            logger.warning(f"No coordinate match found for {db_id} ({db_name})")
            unmatched.append(db_id)

    logger.info(f"Prepared {len(updates)} coordinate updates")
    if unmatched:
        logger.warning(f"{len(unmatched)} courses could not be matched: {unmatched}")

    return updates, unmatched


def update_coordinates(db_client: SupabaseReferenceClient, updates: List[Dict], dry_run: bool = False) -> Dict:
    """
    Update course coordinates in the database.

    Args:
        db_client: Supabase client
        updates: List of update records
        dry_run: If True, only print what would be updated

    Returns:
        Dict with statistics
    """
    if dry_run:
        logger.info("DRY RUN - No changes will be made")
        logger.info(f"Would update {len(updates)} courses:")
        for update in updates[:10]:  # Show first 10
            logger.info(f"  {update['id']} ({update['course_name']}): "
                       f"lat={update['latitude']}, lon={update['longitude']}")
        if len(updates) > 10:
            logger.info(f"  ... and {len(updates) - 10} more")
        return {'dry_run': True, 'would_update': len(updates)}

    logger.info(f"Updating {len(updates)} course coordinates...")

    success_count = 0
    error_count = 0

    # Update in batches
    batch_size = 50
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i + batch_size]

        try:
            # Perform upsert
            for update in batch:
                response = db_client.client.table('ra_courses').update({
                    'latitude': update['latitude'],
                    'longitude': update['longitude']
                }).eq('id', update['id']).execute()

                if response.data:
                    success_count += 1
                else:
                    error_count += 1
                    logger.error(f"Failed to update {update['course_id']}")

            logger.info(f"Updated batch {i // batch_size + 1}/{(len(updates) + batch_size - 1) // batch_size}")

        except Exception as e:
            error_count += len(batch)
            logger.error(f"Error updating batch: {e}")

    logger.info(f"✅ Successfully updated {success_count} courses")
    if error_count > 0:
        logger.warning(f"⚠️  Failed to update {error_count} courses")

    return {
        'success': success_count,
        'errors': error_count,
        'total': len(updates)
    }


def verify_update(db_client: SupabaseReferenceClient) -> Dict:
    """Verify that coordinates were updated successfully."""
    logger.info("Verifying coordinate updates...")

    # Count courses with coordinates
    response = db_client.client.table('ra_courses').select(
        'id, name, latitude, longitude'
    ).execute()

    total = len(response.data)
    with_coords = sum(1 for course in response.data
                     if course.get('latitude') is not None and course.get('longitude') is not None)

    coverage_pct = (with_coords / total * 100) if total > 0 else 0

    logger.info(f"Coordinate coverage: {with_coords}/{total} courses ({coverage_pct:.1f}%)")

    # Show sample of updated courses
    logger.info("Sample of courses with coordinates:")
    for course in response.data[:5]:
        if course.get('latitude') and course.get('longitude'):
            logger.info(f"  {course['name']}: {course['latitude']}, {course['longitude']}")

    return {
        'total_courses': total,
        'with_coordinates': with_coords,
        'coverage_percentage': round(coverage_pct, 2)
    }


def main():
    """Main execution function."""
    import argparse

    parser = argparse.ArgumentParser(description='Update course coordinates from JSON file')
    parser.add_argument('--dry-run', action='store_true',
                       help='Print what would be updated without making changes')
    args = parser.parse_args()

    try:
        # Initialize
        logger.info("=== Course Coordinates Update ===")
        config = get_config()
        db_client = SupabaseReferenceClient(
            url=config.supabase.url,
            service_key=config.supabase.service_key,
            batch_size=100
        )

        # Load coordinates from JSON
        coordinates_data = load_coordinates()

        # Get database courses
        db_courses = get_database_courses(db_client)

        if not db_courses:
            logger.error("No courses found in database. Exiting.")
            return

        # Prepare updates
        updates, unmatched = prepare_updates(db_courses, coordinates_data)

        if not updates:
            logger.warning("No updates to perform. Check that course IDs/codes match.")
            return

        # Perform updates
        result = update_coordinates(db_client, updates, dry_run=args.dry_run)

        if not args.dry_run:
            # Verify updates
            verification = verify_update(db_client)

            logger.info("=== Update Complete ===")
            logger.info(f"Updated: {result['success']} courses")
            logger.info(f"Errors: {result['errors']}")
            logger.info(f"Coverage: {verification['coverage_percentage']}%")

            if unmatched:
                logger.warning(f"Unmatched courses ({len(unmatched)}): {', '.join(unmatched[:10])}")
        else:
            logger.info("=== Dry Run Complete ===")
            logger.info(f"Would update: {result['would_update']} courses")

    except Exception as e:
        logger.error(f"Error during coordinate update: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
