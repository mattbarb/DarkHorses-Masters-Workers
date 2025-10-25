#!/usr/bin/env python3
"""
Update Master Courses Coordinates

This script updates the ra_mst_courses table with latitude and longitude coordinates
from the validated coordinates JSON file.

The script matches courses by name, handling common variations like:
- "Bangor-on-Dee" (DB) vs "Bangor" (JSON)
- "Wexford-RH" (DB) vs "Wexford" (JSON)

Data source: fetchers/ra_courses_final_validated.json

Usage:
    python3 scripts/update_mst_courses_coordinates.py [--dry-run]

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

# Path to coordinates JSON file (now in the project)
COORDINATES_FILE = Path(__file__).parent.parent / "fetchers" / "ra_courses_final_validated.json"


def normalize_course_name(name: str) -> str:
    """
    Normalize course name for matching.

    Handles variations like:
    - "Bangor-on-Dee" -> "bangor"
    - "Wexford-RH" -> "wexford"
    - "Wolverhampton-AW" -> "wolverhampton"
    - "Newmarket-July" -> "newmarket"
    - "Limerick Junction" -> "limerick"
    """
    if not name:
        return ""

    # Convert to lowercase
    name = name.lower()

    # Remove all-weather suffix
    if name.endswith('-aw'):
        name = name[:-3]

    # Remove suffixes like "-rh", "-lh", "-gb"
    for suffix in ['-rh', '-lh', '-left', '-right', '-gb']:
        if name.endswith(suffix):
            name = name[:-len(suffix)]
            break

    # Handle "Newmarket-July" or "Newmarket-Rowley" -> "Newmarket"
    if name.startswith('newmarket-'):
        name = 'newmarket'

    # Handle "Limerick Junction" -> "Limerick"
    if 'limerick' in name:
        name = 'limerick'

    # For "Bangor-on-Dee", extract "Bangor"
    if '-on-' in name or '-upon-' in name:
        name = name.split('-')[0]

    # Remove extra whitespace
    name = name.strip()

    return name


def load_coordinates() -> List[Dict]:
    """Load coordinates from JSON file."""
    logger.info(f"Loading coordinates from: {COORDINATES_FILE}")

    if not COORDINATES_FILE.exists():
        raise FileNotFoundError(f"Coordinates file not found: {COORDINATES_FILE}")

    with open(COORDINATES_FILE, 'r') as f:
        data = json.load(f)

    logger.info(f"Loaded {len(data)} course records with coordinates")
    return data


def match_course_by_name(db_name: str, region_code: str, courses_data: List[Dict]) -> Optional[Dict]:
    """
    Match a course by name in the JSON data.

    Uses normalized name matching to handle variations.
    Also filters by region (GB/IRE).
    """
    normalized_db_name = normalize_course_name(db_name)

    # Convert region code to JSON format
    json_region = 'GB' if region_code.upper() == 'GB' else 'IRE'

    for course in courses_data:
        json_name = course.get('course', '')
        json_country = course.get('country', '')

        # Only match within same region
        if json_country != json_region:
            continue

        normalized_json_name = normalize_course_name(json_name)

        if normalized_json_name == normalized_db_name:
            return course

    return None


def get_database_courses(db_client: SupabaseReferenceClient) -> List[Dict]:
    """Fetch all UK and Ireland courses from the database."""
    logger.info("Fetching UK and Ireland courses from database...")

    # Only get GB and IRE courses since that's what we have coordinates for
    response = db_client.client.table('ra_mst_courses').select(
        'id, name, region_code, latitude, longitude'
    ).in_('region_code', ['GB', 'IRE', 'gb', 'ire']).execute()

    if not response.data:
        logger.warning("No UK/Ireland courses found in database")
        return []

    logger.info(f"Found {len(response.data)} UK/Ireland courses in database")
    return response.data


def prepare_updates(db_courses: List[Dict], coordinates_data: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
    """
    Prepare coordinate updates by matching database courses with JSON data.

    Returns:
        Tuple of (updates, unmatched_courses)
        - updates: List of dicts with id, latitude, longitude
        - unmatched_courses: List of course dicts that couldn't be matched
    """
    updates = []
    unmatched = []

    for db_course in db_courses:
        db_id = db_course['id']
        db_name = db_course.get('name', 'Unknown')
        db_region = db_course.get('region_code', 'unknown')

        # Skip if already has coordinates
        if db_course.get('latitude') is not None and db_course.get('longitude') is not None:
            logger.debug(f"Skipping {db_name} - already has coordinates")
            continue

        # Try matching by name
        match = match_course_by_name(db_name, db_region, coordinates_data)

        if match:
            lat = match.get('latitude')
            lon = match.get('longitude')

            if lat is not None and lon is not None:
                updates.append({
                    'id': db_id,
                    'latitude': lat,
                    'longitude': lon,
                    'course_name': db_name,
                    'matched_with': match.get('course', ''),
                    'code': match.get('code', '')
                })
                logger.debug(f"Matched '{db_name}' -> '{match.get('course')}': {lat}, {lon}")
            else:
                logger.warning(f"Course {db_id} ({db_name}) matched but missing coordinates")
                unmatched.append({'id': db_id, 'name': db_name, 'reason': 'missing_coordinates'})
        else:
            logger.warning(f"No coordinate match found for {db_id} ({db_name})")
            unmatched.append({'id': db_id, 'name': db_name, 'reason': 'no_match'})

    logger.info(f"Prepared {len(updates)} coordinate updates")
    if unmatched:
        logger.warning(f"{len(unmatched)} courses could not be matched")

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
        for update in updates[:20]:  # Show first 20
            logger.info(f"  {update['course_name']} -> {update['matched_with']}: "
                       f"lat={update['latitude']}, lon={update['longitude']}")
        if len(updates) > 20:
            logger.info(f"  ... and {len(updates) - 20} more")
        return {'dry_run': True, 'would_update': len(updates)}

    logger.info(f"Updating {len(updates)} course coordinates...")

    success_count = 0
    error_count = 0

    # Update one by one with error handling
    for update in updates:
        try:
            response = db_client.client.table('ra_mst_courses').update({
                'latitude': update['latitude'],
                'longitude': update['longitude']
            }).eq('id', update['id']).execute()

            if response.data:
                success_count += 1
                if success_count % 10 == 0:
                    logger.info(f"Progress: {success_count}/{len(updates)} updated")
            else:
                error_count += 1
                logger.error(f"Failed to update {update['id']} ({update['course_name']})")

        except Exception as e:
            error_count += 1
            logger.error(f"Error updating {update['id']} ({update['course_name']}): {e}")

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

    # Count UK/Ireland courses with coordinates
    response = db_client.client.table('ra_mst_courses').select(
        'id, name, latitude, longitude, region_code'
    ).in_('region_code', ['GB', 'IRE', 'gb', 'ire']).execute()

    total = len(response.data)
    with_coords = sum(1 for course in response.data
                     if course.get('latitude') is not None and course.get('longitude') is not None)

    coverage_pct = (with_coords / total * 100) if total > 0 else 0

    logger.info(f"Coordinate coverage for UK/Ireland: {with_coords}/{total} courses ({coverage_pct:.1f}%)")

    # Show sample of updated courses
    logger.info("Sample of courses with coordinates:")
    count = 0
    for course in response.data:
        if course.get('latitude') and course.get('longitude') and count < 5:
            logger.info(f"  {course['name']}: {course['latitude']}, {course['longitude']}")
            count += 1

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
        logger.info("=== Master Courses Coordinates Update ===")
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
            logger.error("No UK/Ireland courses found in database. Exiting.")
            return

        # Prepare updates
        updates, unmatched = prepare_updates(db_courses, coordinates_data)

        if not updates:
            logger.warning("No updates to perform. All courses may already have coordinates.")

            # Still show unmatched courses
            if unmatched:
                logger.warning(f"\nUnmatched courses ({len(unmatched)}):")
                for course in unmatched[:10]:
                    logger.warning(f"  {course['name']} - {course['reason']}")
            return

        # Perform updates
        result = update_coordinates(db_client, updates, dry_run=args.dry_run)

        if not args.dry_run:
            # Verify updates
            verification = verify_update(db_client)

            logger.info("\n=== Update Complete ===")
            logger.info(f"Updated: {result['success']} courses")
            logger.info(f"Errors: {result['errors']}")
            logger.info(f"Coverage: {verification['coverage_percentage']}%")

            if unmatched:
                logger.warning(f"\nUnmatched courses ({len(unmatched)}):")
                for course in unmatched[:10]:
                    logger.warning(f"  {course['name']} - {course['reason']}")
                if len(unmatched) > 10:
                    logger.warning(f"  ... and {len(unmatched) - 10} more")
        else:
            logger.info("\n=== Dry Run Complete ===")
            logger.info(f"Would update: {result['would_update']} courses")

    except Exception as e:
        logger.error(f"Error during coordinate update: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
