"""
Course Coordinates Helper

Provides coordinate lookup functionality for courses from the validated JSON file.
Ensures coordinates are assigned to new courses when they are fetched.
"""

import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

# Path to validated coordinates file
COORDINATES_FILE = Path(__file__).parent.parent / "fetchers" / "ra_courses_final_validated.json"

# Cache for coordinates data
_coordinates_cache = None


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
    for suffix in ['-rh', '-lh', '-left', '-right', '-gb', '-ire']:
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


def load_coordinates_data() -> Dict:
    """
    Load coordinates from JSON file and cache them.

    Returns:
        Dict mapping normalized course names to coordinate data
    """
    global _coordinates_cache

    if _coordinates_cache is not None:
        return _coordinates_cache

    logger.info(f"Loading course coordinates from: {COORDINATES_FILE}")

    if not COORDINATES_FILE.exists():
        logger.error(f"Coordinates file not found: {COORDINATES_FILE}")
        return {}

    try:
        with open(COORDINATES_FILE, 'r') as f:
            data = json.load(f)

        # Build lookup cache by normalized name + region
        cache = {}
        for course in data:
            name = course.get('course', '')
            region = course.get('country', '')
            lat = course.get('latitude')
            lon = course.get('longitude')

            if name and lat is not None and lon is not None:
                normalized_name = normalize_course_name(name)
                key = f"{normalized_name}|{region.upper()}"
                cache[key] = {
                    'latitude': lat,
                    'longitude': lon,
                    'original_name': name,
                    'code': course.get('code', '')
                }

        _coordinates_cache = cache
        logger.info(f"Loaded {len(cache)} course coordinates into cache")
        return cache

    except Exception as e:
        logger.error(f"Error loading coordinates: {e}")
        return {}


def get_course_coordinates(course_name: str, region_code: str) -> Optional[Tuple[float, float]]:
    """
    Get coordinates for a course by name and region.

    Args:
        course_name: Name of the course (e.g., "Aintree", "Bangor-on-Dee")
        region_code: Region code (e.g., "GB", "IRE")

    Returns:
        Tuple of (latitude, longitude) or None if not found
    """
    coords_data = load_coordinates_data()

    if not coords_data:
        return None

    # Normalize the course name and region
    normalized_name = normalize_course_name(course_name)
    region_upper = region_code.upper()

    # Try exact match with region
    key = f"{normalized_name}|{region_upper}"
    if key in coords_data:
        coord_info = coords_data[key]
        logger.debug(f"Found coordinates for '{course_name}' -> '{coord_info['original_name']}': "
                    f"{coord_info['latitude']}, {coord_info['longitude']}")
        return (coord_info['latitude'], coord_info['longitude'])

    logger.warning(f"No coordinates found for course: {course_name} ({region_code})")
    return None


def assign_coordinates_to_course(course_record: Dict) -> Dict:
    """
    Assign coordinates to a course record if available.

    Args:
        course_record: Course record dict with 'name' and 'region_code' fields

    Returns:
        Updated course record with latitude/longitude if found
    """
    course_name = course_record.get('name')
    region_code = course_record.get('region_code')

    if not course_name or not region_code:
        return course_record

    # Skip if already has coordinates
    if course_record.get('latitude') is not None and course_record.get('longitude') is not None:
        return course_record

    # Get coordinates
    coords = get_course_coordinates(course_name, region_code)
    if coords:
        course_record['latitude'] = coords[0]
        course_record['longitude'] = coords[1]

    return course_record


def get_coordinates_stats() -> Dict:
    """
    Get statistics about the coordinates cache.

    Returns:
        Dict with cache statistics
    """
    coords_data = load_coordinates_data()

    gb_count = sum(1 for key in coords_data.keys() if '|GB' in key)
    ire_count = sum(1 for key in coords_data.keys() if '|IRE' in key)

    return {
        'total_courses': len(coords_data),
        'gb_courses': gb_count,
        'ire_courses': ire_count,
        'cache_loaded': _coordinates_cache is not None
    }
