"""
Masters Data Fetcher
Consolidated fetcher for all master/reference data (ra_mst_* tables)

Handles:
- Reference data: bookmakers, courses, regions (monthly updates)
- People: jockeys, trainers, owners (weekly updates)
- Horses & Pedigree: horses, sires, dams, damsires (daily via entity extraction)

IMPORTANT: Coordinates are automatically assigned from the validated JSON file
(fetchers/ra_courses_final_validated.json) for UK and Ireland courses.
Coordinates should NOT be overwritten - they are static validated data.

This replaces individual fetchers:
- bookmakers_fetcher.py
- courses_fetcher.py
- jockeys_fetcher.py
- trainers_fetcher.py
- owners_fetcher.py
- horses_fetcher.py (for bulk fetching)
"""

from datetime import datetime
from typing import Dict, List, Optional
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.course_coordinates import assign_coordinates_to_course, get_coordinates_stats

logger = get_logger('masters_fetcher')


class MastersFetcher:
    """Consolidated fetcher for all master/reference data"""

    # Static list of major UK/Irish bookmakers
    BOOKMAKERS = [
        {'code': 'bet365', 'name': 'Bet365', 'type': 'online'},
        {'code': 'william_hill', 'name': 'William Hill', 'type': 'online'},
        {'code': 'ladbrokes', 'name': 'Ladbrokes', 'type': 'online'},
        {'code': 'coral', 'name': 'Coral', 'type': 'online'},
        {'code': 'paddy_power', 'name': 'Paddy Power', 'type': 'online'},
        {'code': 'betfair', 'name': 'Betfair', 'type': 'exchange'},
        {'code': 'betfair_sportsbook', 'name': 'Betfair Sportsbook', 'type': 'online'},
        {'code': 'skybet', 'name': 'Sky Bet', 'type': 'online'},
        {'code': 'betvictor', 'name': 'BetVictor', 'type': 'online'},
        {'code': 'betfred', 'name': 'Betfred', 'type': 'online'},
        {'code': '888sport', 'name': '888sport', 'type': 'online'},
        {'code': 'unibet', 'name': 'Unibet', 'type': 'online'},
        {'code': 'betway', 'name': 'Betway', 'type': 'online'},
        {'code': 'boylesports', 'name': 'BoyleSports', 'type': 'online'},
        {'code': 'betdaq', 'name': 'Betdaq', 'type': 'exchange'},
        {'code': 'matchbook', 'name': 'Matchbook', 'type': 'exchange'},
        {'code': 'smarkets', 'name': 'Smarkets', 'type': 'exchange'},
        {'code': 'spreadex', 'name': 'Spreadex', 'type': 'spread'},
        {'code': 'sporting_index', 'name': 'Sporting Index', 'type': 'spread'},
    ]

    def __init__(self):
        """Initialize fetcher with API and database clients"""
        self.config = get_config()
        self.api_client = RacingAPIClient(
            username=self.config.api.username,
            password=self.config.api.password,
            base_url=self.config.api.base_url,
            timeout=self.config.api.timeout,
            max_retries=self.config.api.max_retries
        )
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )

    # ========================================================================
    # REFERENCE DATA (Monthly Updates)
    # ========================================================================

    def fetch_bookmakers(self) -> Dict:
        """
        Insert static bookmakers list

        Note: Bookmakers are static reference data, not fetched from API

        Returns:
            Statistics dictionary
        """
        logger.info("Inserting static bookmakers list")

        # Transform for database
        bookmakers_transformed = []
        for bm in self.BOOKMAKERS:
            bookmaker_record = {
                'code': bm['code'],
                'name': bm['name'],
                'type': bm['type'],
                'is_active': True,
                'created_at': datetime.utcnow().isoformat()
            }
            bookmakers_transformed.append(bookmaker_record)

        logger.info(f"Preparing to insert {len(bookmakers_transformed)} bookmakers")

        # Store in database
        if bookmakers_transformed:
            db_stats = self.db_client.insert_bookmakers(bookmakers_transformed)
            logger.info(f"Stored {db_stats.get('inserted', 0)} bookmakers")

            return {
                'success': True,
                'fetched': len(bookmakers_transformed),
                'inserted': db_stats.get('inserted', 0),
                'db_stats': db_stats
            }
        else:
            return {'success': False, 'error': 'No bookmakers to insert'}

    def fetch_courses(self, region_codes: List[str] = None) -> Dict:
        """
        Fetch all courses/venues

        Automatically assigns coordinates from validated JSON file for UK/IRE courses.

        Args:
            region_codes: Optional filter (e.g., ['gb', 'ire']). Defaults to UK and Ireland only.

        Returns:
            Statistics dictionary
        """
        # Default to UK and Ireland only
        if region_codes is None:
            region_codes = ['gb', 'ire']
            logger.info("No region codes specified, defaulting to UK and Ireland")

        logger.info(f"Fetching courses from API (regions: {region_codes})")

        api_response = self.api_client.get_courses(region_codes=region_codes)

        if not api_response or 'courses' not in api_response:
            logger.error("Failed to fetch courses from API")
            return {'success': False, 'error': 'API fetch failed'}

        courses_raw = api_response.get('courses', [])
        logger.info(f"Fetched {len(courses_raw)} courses from API")

        # Log coordinate cache stats
        coord_stats = get_coordinates_stats()
        logger.info(f"Coordinate cache: {coord_stats['total_courses']} courses "
                   f"(GB: {coord_stats['gb_courses']}, IRE: {coord_stats['ire_courses']})")

        # Transform for database
        courses_transformed = []
        coords_assigned = 0
        coords_missing = 0

        for course in courses_raw:
            course_record = {
                'id': course.get('id'),
                'name': course.get('course'),
                'region_code': course.get('region_code'),
                'region': course.get('region'),
                'latitude': None,  # Will be assigned from validated file
                'longitude': None,  # Will be assigned from validated file
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            # Assign coordinates from validated file
            course_record = assign_coordinates_to_course(course_record)

            # Track coordinate assignment
            if course_record.get('latitude') is not None:
                coords_assigned += 1
            else:
                coords_missing += 1

            courses_transformed.append(course_record)

        logger.info(f"Coordinates: {coords_assigned} assigned, {coords_missing} missing")

        # Store in database
        if courses_transformed:
            db_stats = self.db_client.insert_courses(courses_transformed)
            logger.info(f"Stored {db_stats.get('inserted', 0)} courses")

            return {
                'success': True,
                'fetched': len(courses_raw),
                'inserted': db_stats.get('inserted', 0),
                'coordinates_assigned': coords_assigned,
                'coordinates_missing': coords_missing,
                'db_stats': db_stats
            }
        else:
            return {'success': False, 'error': 'No courses to insert'}

    def fetch_regions(self) -> Dict:
        """
        Fetch region reference data

        Note: Regions are typically static (GB, IRE)
        This method ensures they exist in the database

        Returns:
            Statistics dictionary
        """
        logger.info("Ensuring region reference data exists")

        # Standard regions for UK/Ireland racing
        regions = [
            {'code': 'gb', 'name': 'Great Britain', 'created_at': datetime.utcnow().isoformat()},
            {'code': 'ire', 'name': 'Ireland', 'created_at': datetime.utcnow().isoformat()}
        ]

        db_stats = self.db_client.insert_regions(regions)
        logger.info(f"Stored {db_stats.get('inserted', 0)} regions")

        return {
            'success': True,
            'fetched': len(regions),
            'inserted': db_stats.get('inserted', 0),
            'db_stats': db_stats
        }

    # ========================================================================
    # PEOPLE DATA (Weekly Updates)
    # ========================================================================

    def fetch_jockeys(self, limit_per_page: int = 500, max_pages: int = None) -> Dict:
        """
        Fetch all jockeys (bulk)

        Note: This uses the search endpoint which requires a name parameter.
        For production, jockeys should primarily be extracted from races/results.
        This method is for backfilling or specific lookups.

        Args:
            limit_per_page: Records per API page
            max_pages: Max pages to fetch (None = all)

        Returns:
            Statistics dictionary
        """
        logger.warning("Jockeys fetcher: This uses search API which requires name parameter")
        logger.warning("For production, use entity extraction from races/results instead")

        # For now, return empty stats and recommend entity extraction
        return {
            'success': True,
            'fetched': 0,
            'inserted': 0,
            'note': 'Jockeys should be extracted from races/results via EventsFetcher'
        }

    def fetch_trainers(self, limit_per_page: int = 500, max_pages: int = None) -> Dict:
        """
        Fetch all trainers (bulk)

        Note: Similar to jockeys, trainers are best extracted from races/results.

        Args:
            limit_per_page: Records per API page
            max_pages: Max pages to fetch (None = all)

        Returns:
            Statistics dictionary
        """
        logger.warning("Trainers fetcher: Similar to jockeys, best extracted from races/results")

        return {
            'success': True,
            'fetched': 0,
            'inserted': 0,
            'note': 'Trainers should be extracted from races/results via EventsFetcher'
        }

    def fetch_owners(self, limit_per_page: int = 500, max_pages: int = None) -> Dict:
        """
        Fetch all owners (bulk)

        Note: Similar to jockeys/trainers, owners are best extracted from races/results.

        Args:
            limit_per_page: Records per API page
            max_pages: Max pages to fetch (None = all)

        Returns:
            Statistics dictionary
        """
        logger.warning("Owners fetcher: Similar to jockeys, best extracted from races/results")

        return {
            'success': True,
            'fetched': 0,
            'inserted': 0,
            'note': 'Owners should be extracted from races/results via EventsFetcher'
        }

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def fetch_all_reference(self, region_codes: List[str] = None) -> Dict:
        """
        Fetch all reference data (bookmakers, courses, regions)

        Use this for monthly reference data updates.

        Args:
            region_codes: Optional region filter for courses

        Returns:
            Combined statistics dictionary
        """
        logger.info("=" * 60)
        logger.info("FETCHING ALL REFERENCE DATA (MONTHLY UPDATE)")
        logger.info("=" * 60)

        bookmakers = self.fetch_bookmakers()
        courses = self.fetch_courses(region_codes=region_codes)
        regions = self.fetch_regions()

        return {
            'success': True,
            'bookmakers': bookmakers,
            'courses': courses,
            'regions': regions,
            'total_fetched': (
                bookmakers.get('fetched', 0) +
                courses.get('fetched', 0) +
                regions.get('fetched', 0)
            ),
            'total_inserted': (
                bookmakers.get('inserted', 0) +
                courses.get('inserted', 0) +
                regions.get('inserted', 0)
            )
        }

    def fetch_all_people(self) -> Dict:
        """
        Fetch all people (jockeys, trainers, owners)

        Use this for weekly people updates.

        Note: Currently returns empty as people are best extracted from races/results.

        Returns:
            Combined statistics dictionary
        """
        logger.info("=" * 60)
        logger.info("FETCHING ALL PEOPLE DATA (WEEKLY UPDATE)")
        logger.info("=" * 60)
        logger.warning("People data is best extracted from races/results")
        logger.warning("Use EventsFetcher for automatic entity extraction")

        jockeys = self.fetch_jockeys()
        trainers = self.fetch_trainers()
        owners = self.fetch_owners()

        return {
            'success': True,
            'jockeys': jockeys,
            'trainers': trainers,
            'owners': owners,
            'note': 'People should be extracted from races/results via EventsFetcher'
        }

    def backfill(self, region_codes: List[str] = None) -> Dict:
        """
        Backfill all master reference data

        This ensures all reference tables have complete records:
        - ra_mst_bookmakers (static list)
        - ra_mst_courses (from API)
        - ra_mst_regions (static list)

        Note: People and horses are populated via entity extraction from events,
        not through this backfill method.

        Args:
            region_codes: Region filter (default: ['gb', 'ire'])

        Returns:
            Statistics dictionary
        """
        if region_codes is None:
            region_codes = ['gb', 'ire']

        logger.info("=" * 60)
        logger.info("BACKFILLING MASTER REFERENCE DATA")
        logger.info("=" * 60)

        # Fetch all reference data (bookmakers, courses, regions)
        return self.fetch_all_reference(region_codes=region_codes)

    def fetch_and_store(self, entity_type: str = 'all', **config) -> Dict:
        """
        Main entry point for fetching master data

        Args:
            entity_type: Type to fetch ('reference', 'people', 'all')
            **config: Additional configuration

        Returns:
            Statistics dictionary
        """
        region_codes = config.get('region_codes', ['gb', 'ire'])

        if entity_type == 'reference':
            return self.fetch_all_reference(region_codes=region_codes)
        elif entity_type == 'people':
            return self.fetch_all_people()
        elif entity_type == 'all':
            # Fetch both reference and people
            reference = self.fetch_all_reference(region_codes=region_codes)
            people = self.fetch_all_people()
            return {
                'success': True,
                'reference': reference,
                'people': people,
                'total_fetched': (
                    reference.get('total_fetched', 0) +
                    people.get('jockeys', {}).get('fetched', 0) +
                    people.get('trainers', {}).get('fetched', 0) +
                    people.get('owners', {}).get('fetched', 0)
                )
            }
        else:
            return {'success': False, 'error': f'Unknown entity type: {entity_type}'}


def main():
    """Main execution for testing"""
    logger.info("=" * 60)
    logger.info("MASTERS DATA FETCHER - TEST MODE")
    logger.info("=" * 60)

    fetcher = MastersFetcher()

    # Fetch reference data (monthly)
    result = fetcher.fetch_all_reference(region_codes=['gb', 'ire'])

    logger.info("\n" + "=" * 60)
    logger.info("RESULTS:")
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Total fetched: {result.get('total_fetched', 0)}")
    logger.info(f"Total inserted: {result.get('total_inserted', 0)}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
