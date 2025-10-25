"""
Supabase Database Client for Reference Data
Handles database operations with batching, upserts, and error handling
"""

import logging
from typing import Dict, List, Optional, Any
from supabase import create_client, Client
from datetime import datetime

logger = logging.getLogger(__name__)


class SupabaseReferenceClient:
    """Client for managing reference data in Supabase"""

    def __init__(self, url: str, service_key: str, batch_size: int = 100):
        """
        Initialize Supabase client

        Args:
            url: Supabase project URL
            service_key: Supabase service role key
            batch_size: Number of records per batch insert
        """
        self.url = url
        self.batch_size = batch_size

        try:
            # Create client without proxy option (compatibility fix for supabase-py 2.3.4+)
            from supabase.lib.client_options import ClientOptions
            options = ClientOptions()
            self.client: Client = create_client(url, service_key, options)
            logger.info(f"Connected to Supabase at {url}")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise

        # Statistics
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

    def verify_connection(self, table: str = 'ra_mst_courses') -> bool:
        """Verify database connection"""
        try:
            result = self.client.table(table).select('*').limit(1).execute()
            logger.info(f"Database connection verified (test table: {table})")
            return True
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            return False

    def upsert_batch(self, table: str, records: List[Dict], unique_key: str = 'id') -> Dict:
        """
        Upsert batch of records

        Args:
            table: Table name
            records: List of record dictionaries
            unique_key: Column name for uniqueness check

        Returns:
            Statistics dictionary
        """
        if not records:
            logger.warning(f"No records to upsert for {table}")
            return {'inserted': 0, 'updated': 0, 'errors': 0}

        # Filter out dropped columns for ra_runners (Migration 016a cleanup)
        # These columns were dropped but may still be in fetcher code during transition
        DROPPED_RUNNER_COLUMNS = {
            'fetched_at',  # Use created_at instead
            'racing_api_race_id',  # Use race_id instead
            'racing_api_horse_id',  # Use horse_id instead
            'racing_api_jockey_id',  # Use jockey_id instead
            'racing_api_trainer_id',  # Use trainer_id instead
            'racing_api_owner_id',  # Use owner_id instead
            'weight',  # Use weight_lbs instead
            'jockey_silk_url',  # Use silk_url instead
            'sire_name',  # Now in ra_sires table
            'dam_name',  # Now in ra_dams table
            'damsire_name',  # Now in ra_damsires table
        }

        # Clean records if table is ra_runners
        if table == 'ra_runners':
            cleaned_records = []
            for record in records:
                # Remove dropped columns from this record
                cleaned_record = {k: v for k, v in record.items() if k not in DROPPED_RUNNER_COLUMNS}
                cleaned_records.append(cleaned_record)
            records = cleaned_records

        batch_stats = {'inserted': 0, 'updated': 0, 'errors': 0}

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]

            try:
                # Upsert with on_conflict handling
                result = self.client.table(table).upsert(
                    batch,
                    on_conflict=unique_key
                ).execute()

                # Count as successful
                batch_stats['inserted'] += len(batch)
                logger.debug(f"Upserted {len(batch)} records to {table}")

            except Exception as e:
                batch_stats['errors'] += len(batch)
                logger.error(f"Error upserting batch to {table}: {e}")

        return batch_stats

    def insert_batch_no_conflict(self, table: str, records: List[Dict]) -> Dict:
        """
        Insert batch of records without ON CONFLICT clause

        Use this for tables with auto-increment primary key and no unique constraints.
        This performs simple INSERT, allowing duplicate race_id/horse_id combinations.

        Args:
            table: Table name
            records: List of record dictionaries

        Returns:
            Statistics dictionary
        """
        if not records:
            logger.warning(f"No records to insert for {table}")
            return {'inserted': 0, 'updated': 0, 'errors': 0}

        batch_stats = {'inserted': 0, 'updated': 0, 'errors': 0}

        # Process in batches
        for i in range(0, len(records), self.batch_size):
            batch = records[i:i + self.batch_size]

            try:
                # Simple insert without ON CONFLICT
                result = self.client.table(table).insert(batch).execute()

                # Count as successful
                batch_stats['inserted'] += len(batch)
                logger.debug(f"Inserted {len(batch)} records to {table}")

            except Exception as e:
                batch_stats['errors'] += len(batch)
                logger.error(f"Error inserting batch to {table}: {e}")

        return batch_stats

    def insert_courses(self, courses: List[Dict]) -> Dict:
        """
        Insert/update courses with coordinate preservation

        IMPORTANT: Coordinates are preserved for existing courses.
        Only new courses or courses with NULL coordinates will have them updated.
        """
        logger.info(f"Inserting {len(courses)} courses")

        # Fetch existing courses to check for coordinates
        try:
            course_ids = [c.get('id') for c in courses if c.get('id')]
            existing_response = self.client.table('ra_mst_courses').select(
                'id, latitude, longitude'
            ).in_('id', course_ids).execute()

            # Build map of courses with existing coordinates
            existing_coords = {}
            for existing in existing_response.data:
                if existing.get('latitude') is not None and existing.get('longitude') is not None:
                    existing_coords[existing['id']] = True

            logger.info(f"Found {len(existing_coords)} courses with existing coordinates")

            # Remove coordinates from records that already have them
            preserved_count = 0
            for course in courses:
                course_id = course.get('id')
                if course_id in existing_coords:
                    # Remove lat/lon to prevent overwrite
                    if 'latitude' in course:
                        del course['latitude']
                    if 'longitude' in course:
                        del course['longitude']
                    preserved_count += 1

            if preserved_count > 0:
                logger.info(f"Preserved coordinates for {preserved_count} existing courses")

        except Exception as e:
            logger.warning(f"Could not check existing coordinates: {e}")
            # Continue with upsert anyway

        return self.upsert_batch('ra_mst_courses', courses, 'id')

    def insert_horses(self, horses: List[Dict]) -> Dict:
        """Insert/update horses"""
        logger.info(f"Inserting {len(horses)} horses")
        return self.upsert_batch('ra_mst_horses', horses, 'id')

    def insert_jockeys(self, jockeys: List[Dict]) -> Dict:
        """Insert/update jockeys"""
        logger.info(f"Inserting {len(jockeys)} jockeys")
        return self.upsert_batch('ra_mst_jockeys', jockeys, 'id')

    def insert_trainers(self, trainers: List[Dict]) -> Dict:
        """Insert/update trainers"""
        logger.info(f"Inserting {len(trainers)} trainers")
        return self.upsert_batch('ra_mst_trainers', trainers, 'id')

    def insert_owners(self, owners: List[Dict]) -> Dict:
        """Insert/update owners"""
        logger.info(f"Inserting {len(owners)} owners")
        return self.upsert_batch('ra_mst_owners', owners, 'id')

    def insert_sires(self, sires: List[Dict]) -> Dict:
        """Insert/update sires"""
        logger.info(f"Inserting {len(sires)} sires")
        return self.upsert_batch('ra_mst_sires', sires, 'id')

    def insert_dams(self, dams: List[Dict]) -> Dict:
        """Insert/update dams"""
        logger.info(f"Inserting {len(dams)} dams")
        return self.upsert_batch('ra_mst_dams', dams, 'id')

    def insert_damsires(self, damsires: List[Dict]) -> Dict:
        """Insert/update damsires"""
        logger.info(f"Inserting {len(damsires)} damsires")
        return self.upsert_batch('ra_mst_damsires', damsires, 'id')

    def insert_pedigree(self, pedigrees: List[Dict]) -> Dict:
        """Insert/update horse pedigree data"""
        logger.info(f"Inserting {len(pedigrees)} pedigree records")
        return self.upsert_batch('ra_horse_pedigree', pedigrees, 'horse_id')

    def insert_races(self, races: List[Dict]) -> Dict:
        """Insert/update races (unified table)"""
        logger.info(f"Inserting {len(races)} races")
        return self.upsert_batch('ra_races', races, 'id')

    def insert_results(self, results: List[Dict]) -> Dict:
        """
        Insert/update race results (ra_results table)

        This stores race-level result data including tote pools, winning time,
        comments, and non-runners. Runner-level results are stored in ra_runners.
        """
        logger.info(f"Inserting {len(results)} results")
        return self.upsert_batch('ra_results', results, 'id')

    def insert_race_results(self, results: List[Dict]) -> Dict:
        """
        Insert/update runner race results (ra_race_results table)

        Note: This table stores individual runner results.
        Uses auto-increment 'id' as primary key, no unique constraint on race_id/horse_id.
        So we use insert-only (no upsert) to avoid conflicts.
        """
        logger.info(f"Inserting {len(results)} runner race results")
        # Use insert without ON CONFLICT since table has no unique constraint
        return self.insert_batch_no_conflict('ra_race_results', results)

    def insert_runners(self, runners: List[Dict]) -> Dict:
        """
        Insert/update runners (unified table)

        Note: This includes race results data (position, distance_beaten, prize_won, starting_price)
        The ra_results table was removed - all results data is stored in ra_runners.
        See: docs/RESULTS_DATA_ARCHITECTURE.md

        IMPORTANT: ra_runners uses composite unique key (race_id, horse_id) not 'id'
        """
        logger.info(f"Inserting {len(runners)} runners")
        return self.upsert_batch('ra_runners', runners, 'race_id,horse_id')

    def insert_bookmakers(self, bookmakers: List[Dict]) -> Dict:
        """Insert/update bookmakers"""
        logger.info(f"Inserting {len(bookmakers)} bookmakers")
        return self.upsert_batch('ra_mst_bookmakers', bookmakers, 'code')

    def insert_regions(self, regions: List[Dict]) -> Dict:
        """Insert/update regions"""
        logger.info(f"Inserting {len(regions)} regions")
        return self.upsert_batch('ra_mst_regions', regions, 'code')

    def get_existing_ids(self, table: str, id_column: str) -> set:
        """
        Get set of existing IDs from a table

        Args:
            table: Table name
            id_column: ID column name

        Returns:
            Set of existing IDs
        """
        try:
            result = self.client.table(table).select(id_column).execute()
            return {row[id_column] for row in result.data}
        except Exception as e:
            logger.error(f"Error getting existing IDs from {table}: {e}")
            return set()

    def get_table_count(self, table: str) -> int:
        """Get row count for a table"""
        try:
            result = self.client.table(table).select('*', count='exact').limit(1).execute()
            return result.count if hasattr(result, 'count') else 0
        except Exception as e:
            logger.error(f"Error getting count for {table}: {e}")
            return 0

    def get_stats(self) -> Dict:
        """Get client statistics"""
        return self.stats.copy()

    def reset_stats(self):
        """Reset statistics"""
        self.stats = {
            'inserted': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
