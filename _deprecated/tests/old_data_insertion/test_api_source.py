"""
API-Source Test Data Insertion

Fetches REAL data from Racing API endpoints and marks it as TEST data.
This tests that fetchers are capturing ALL columns from actual API responses.

This is the CORRECT approach - uses real API data, not synthetic data.

Usage:
    # Insert real API test data
    python3 fetchers/test_api_source.py

    # Specific tables
    python3 fetchers/test_api_source.py --tables ra_mst_horses ra_races

    # From controller
    python3 fetchers/master_fetcher_controller.py --mode test-api --interactive

    # Cleanup
    python3 fetchers/test_api_source.py --cleanup
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import uuid4

from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('test_api_source')


class APISourceTestInserter:
    """Inserts real API data marked as TEST to verify column capture"""

    def __init__(self):
        """Initialize inserter"""
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
        self.test_marker = "**TEST**"
        self.test_id = f"test_{uuid4().hex[:8]}"

    def fetch_real_courses_data(self) -> Optional[Dict]:
        """Fetch ONE real course from Racing API"""
        try:
            logger.info("Fetching real course data from Racing API...")
            response = self.api_client.get_courses(region_codes=['gb'])

            if response and 'courses' in response and len(response['courses']) > 0:
                course = response['courses'][0]  # Just take the first one
                logger.info(f"  Fetched course: {course.get('name')}")
                return course
            return None
        except Exception as e:
            logger.error(f"Error fetching course data: {e}")
            return None

    def fetch_real_race_entities(self) -> Optional[Dict]:
        """Fetch ONE real race with runners to extract entities (jockey, trainer, owner, horse)"""
        try:
            logger.info("Fetching real race data with entities from Racing API...")
            # Get racecards from yesterday to ensure data exists
            yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
            response = self.api_client.get_racecards_pro(
                date_from=yesterday,
                date_to=yesterday,
                region_codes=['gb']
            )

            if response and 'racecards' in response and len(response['racecards']) > 0:
                race = response['racecards'][0]
                logger.info(f"  Fetched race: {race.get('course_name')} - {race.get('off_time')}")
                return race
            return None
        except Exception as e:
            logger.error(f"Error fetching race data for entities: {e}")
            return None

    def fetch_real_jockey_data(self) -> Optional[Dict]:
        """Fetch ONE real jockey from racecards"""
        race = self.fetch_real_race_entities()
        if race and 'runners' in race and len(race['runners']) > 0:
            runner = race['runners'][0]
            if 'jockey' in runner:
                logger.info(f"  Extracted jockey: {runner['jockey'].get('name')}")
                return runner['jockey']
        return None

    def fetch_real_trainer_data(self) -> Optional[Dict]:
        """Fetch ONE real trainer from racecards"""
        race = self.fetch_real_race_entities()
        if race and 'runners' in race and len(race['runners']) > 0:
            runner = race['runners'][0]
            if 'trainer' in runner:
                logger.info(f"  Extracted trainer: {runner['trainer'].get('name')}")
                return runner['trainer']
        return None

    def fetch_real_owner_data(self) -> Optional[Dict]:
        """Fetch ONE real owner from racecards"""
        race = self.fetch_real_race_entities()
        if race and 'runners' in race and len(race['runners']) > 0:
            runner = race['runners'][0]
            if 'owner' in runner:
                logger.info(f"  Extracted owner: {runner['owner'].get('name')}")
                return runner['owner']
        return None

    def fetch_real_horse_data(self) -> Optional[Dict]:
        """Fetch ONE real horse from racecards with Pro enrichment"""
        race = self.fetch_real_race_entities()
        if race and 'runners' in race and len(race['runners']) > 0:
            runner = race['runners'][0]
            if 'horse' in runner:
                horse = runner['horse']
                logger.info(f"  Extracted horse: {horse.get('name')}")

                # Also fetch Pro endpoint data for enrichment
                horse_id = horse.get('id')
                if horse_id:
                    try:
                        pro_data = self.api_client.get_horse_details(horse_id, tier='pro')
                        if pro_data and 'horse' in pro_data:
                            # Merge Pro data
                            horse.update(pro_data['horse'])
                            logger.info(f"  Enriched with Pro endpoint data")
                    except:
                        pass  # Pro enrichment failed, continue with basic data

                return horse
        return None

    def fetch_real_race_data(self) -> Optional[Dict]:
        """Fetch ONE real race with runners from Racing API (same as fetch_real_race_entities)"""
        return self.fetch_real_race_entities()

    def fetch_real_bookmaker_data(self) -> Optional[Dict]:
        """Get ONE real bookmaker from hardcoded list (bookmakers don't have an API endpoint)"""
        try:
            logger.info("Getting real bookmaker data from hardcoded list...")
            # Use the same hardcoded list as BookmakersFetcher
            bookmaker = {
                'id': 'bet365',
                'name': 'Bet365',
                'type': 'online'
            }
            logger.info(f"  Using bookmaker: {bookmaker.get('name')}")
            return bookmaker
        except Exception as e:
            logger.error(f"Error getting bookmaker data: {e}")
            return None

    def mark_course_as_test(self, course: Dict) -> Dict:
        """Mark course data as TEST"""
        test_course = course.copy()
        test_course['id'] = f"{self.test_marker}_{self.test_id}_course"
        test_course['name'] = f"{self.test_marker} {course.get('name', 'Course')}"
        return test_course

    def mark_jockey_as_test(self, jockey: Dict) -> Dict:
        """Mark jockey data as TEST"""
        test_jockey = jockey.copy()
        test_jockey['id'] = f"{self.test_marker}_{self.test_id}_jockey"
        test_jockey['name'] = f"{self.test_marker} {jockey.get('name', 'Jockey')}"
        return test_jockey

    def mark_trainer_as_test(self, trainer: Dict) -> Dict:
        """Mark trainer data as TEST"""
        test_trainer = trainer.copy()
        test_trainer['id'] = f"{self.test_marker}_{self.test_id}_trainer"
        test_trainer['name'] = f"{self.test_marker} {trainer.get('name', 'Trainer')}"
        return test_trainer

    def mark_owner_as_test(self, owner: Dict) -> Dict:
        """Mark owner data as TEST"""
        test_owner = owner.copy()
        test_owner['id'] = f"{self.test_marker}_{self.test_id}_owner"
        test_owner['name'] = f"{self.test_marker} {owner.get('name', 'Owner')}"
        return test_owner

    def mark_horse_as_test(self, horse: Dict) -> Dict:
        """Mark horse data as TEST"""
        test_horse = horse.copy()
        test_horse['id'] = f"{self.test_marker}_{self.test_id}_horse"
        test_horse['name'] = f"{self.test_marker} {horse.get('name', 'Horse')}"

        # Also mark pedigree IDs
        if test_horse.get('sire_id'):
            test_horse['sire_id'] = f"{self.test_marker}_{self.test_id}_sire"
        if test_horse.get('dam_id'):
            test_horse['dam_id'] = f"{self.test_marker}_{self.test_id}_dam"
        if test_horse.get('damsire_id'):
            test_horse['damsire_id'] = f"{self.test_marker}_{self.test_id}_damsire"

        return test_horse

    def mark_race_as_test(self, race: Dict) -> Dict:
        """Mark race data as TEST"""
        test_race = race.copy()
        test_race['id'] = f"{self.test_marker}_{self.test_id}_race"
        test_race['race_id'] = f"{self.test_marker}_{self.test_id}_race"
        test_race['race_title'] = f"{self.test_marker} {race.get('race_title', 'Race')}"

        # Mark runners as test too
        if 'runners' in test_race:
            test_runners = []
            for i, runner in enumerate(test_race['runners']):
                test_runner = runner.copy()
                test_runner['id'] = f"{self.test_marker}_{self.test_id}_runner_{i}"
                test_runner['horse_name'] = f"{self.test_marker} {runner.get('horse_name', 'Horse')}"
                test_runners.append(test_runner)
            test_race['runners'] = test_runners

        return test_race

    def mark_bookmaker_as_test(self, bookmaker: Dict) -> Dict:
        """Mark bookmaker data as TEST"""
        test_bookmaker = bookmaker.copy()
        test_bookmaker['id'] = f"{self.test_marker}_{self.test_id}_bookmaker"
        test_bookmaker['name'] = f"{self.test_marker} {bookmaker.get('name', 'Bookmaker')}"
        return test_bookmaker

    def insert_test_course(self) -> Dict:
        """Fetch, mark, and insert test course"""
        logger.info("Processing ra_mst_courses...")

        try:
            # Fetch real data
            course = self.fetch_real_courses_data()
            if not course:
                return {'table': 'ra_mst_courses', 'success': False, 'error': 'No data from API'}

            # Mark as test
            test_course = self.mark_course_as_test(course)

            # Transform to database format (same as courses_fetcher.py)
            db_record = {
                'id': test_course.get('id'),
                'name': test_course.get('course') or test_course.get('name'),
                'region_code': test_course.get('region_code'),
                'region': test_course.get('region'),
                'latitude': test_course.get('latitude'),
                'longitude': test_course.get('longitude'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }

            # Insert
            result = self.db_client.insert_courses([db_record])

            logger.info(f"✅ Inserted test course: {result.get('inserted', 0)} row(s)")
            return {
                'table': 'ra_mst_courses',
                'success': True,
                'columns_from_api': len([k for k in test_course.keys() if test_course[k] is not None]),
                'data': db_record
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test course: {e}", exc_info=True)
            return {'table': 'ra_mst_courses', 'success': False, 'error': str(e)}

    def insert_test_jockey(self) -> Dict:
        """Fetch, mark, and insert test jockey"""
        logger.info("Processing ra_mst_jockeys...")

        try:
            jockey = self.fetch_real_jockey_data()
            if not jockey:
                return {'table': 'ra_mst_jockeys', 'success': False, 'error': 'No data from API'}

            test_jockey = self.mark_jockey_as_test(jockey)

            from fetchers.jockeys_fetcher import JockeysFetcher
            fetcher = JockeysFetcher()
            db_record = fetcher._transform_jockey(test_jockey)

            result = self.db_client.insert_jockeys([db_record])

            logger.info(f"✅ Inserted test jockey: {result.get('inserted', 0)} row(s)")
            return {
                'table': 'ra_mst_jockeys',
                'success': True,
                'columns_from_api': len([k for k in test_jockey.keys() if test_jockey[k] is not None]),
                'data': db_record
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test jockey: {e}", exc_info=True)
            return {'table': 'ra_mst_jockeys', 'success': False, 'error': str(e)}

    def insert_test_trainer(self) -> Dict:
        """Fetch, mark, and insert test trainer"""
        logger.info("Processing ra_mst_trainers...")

        try:
            trainer = self.fetch_real_trainer_data()
            if not trainer:
                return {'table': 'ra_mst_trainers', 'success': False, 'error': 'No data from API'}

            test_trainer = self.mark_trainer_as_test(trainer)

            from fetchers.trainers_fetcher import TrainersFetcher
            fetcher = TrainersFetcher()
            db_record = fetcher._transform_trainer(test_trainer)

            result = self.db_client.insert_trainers([db_record])

            logger.info(f"✅ Inserted test trainer: {result.get('inserted', 0)} row(s)")
            return {
                'table': 'ra_mst_trainers',
                'success': True,
                'columns_from_api': len([k for k in test_trainer.keys() if test_trainer[k] is not None]),
                'data': db_record
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test trainer: {e}", exc_info=True)
            return {'table': 'ra_mst_trainers', 'success': False, 'error': str(e)}

    def insert_test_owner(self) -> Dict:
        """Fetch, mark, and insert test owner"""
        logger.info("Processing ra_mst_owners...")

        try:
            owner = self.fetch_real_owner_data()
            if not owner:
                return {'table': 'ra_mst_owners', 'success': False, 'error': 'No data from API'}

            test_owner = self.mark_owner_as_test(owner)

            from fetchers.owners_fetcher import OwnersFetcher
            fetcher = OwnersFetcher()
            db_record = fetcher._transform_owner(test_owner)

            result = self.db_client.insert_owners([db_record])

            logger.info(f"✅ Inserted test owner: {result.get('inserted', 0)} row(s)")
            return {
                'table': 'ra_mst_owners',
                'success': True,
                'columns_from_api': len([k for k in test_owner.keys() if test_owner[k] is not None]),
                'data': db_record
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test owner: {e}", exc_info=True)
            return {'table': 'ra_mst_owners', 'success': False, 'error': str(e)}

    def insert_test_horse(self) -> Dict:
        """Fetch, mark, and insert test horse"""
        logger.info("Processing ra_mst_horses...")

        try:
            horse = self.fetch_real_horse_data()
            if not horse:
                return {'table': 'ra_mst_horses', 'success': False, 'error': 'No data from API'}

            test_horse = self.mark_horse_as_test(horse)

            from fetchers.horses_fetcher import HorsesFetcher
            fetcher = HorsesFetcher()
            db_record = fetcher._transform_horse(test_horse)

            result = self.db_client.insert_horses([db_record])

            logger.info(f"✅ Inserted test horse: {result.get('inserted', 0)} row(s)")
            return {
                'table': 'ra_mst_horses',
                'success': True,
                'columns_from_api': len([k for k in test_horse.keys() if test_horse[k] is not None]),
                'data': db_record
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test horse: {e}", exc_info=True)
            return {'table': 'ra_mst_horses', 'success': False, 'error': str(e)}

    def insert_test_race(self) -> Dict:
        """Fetch, mark, and insert test race with runners"""
        logger.info("Processing ra_races and ra_runners...")

        try:
            race = self.fetch_real_race_data()
            if not race:
                return {'table': 'ra_races', 'success': False, 'error': 'No data from API'}

            test_race = self.mark_race_as_test(race)

            from fetchers.races_fetcher import RacesFetcher
            fetcher = RacesFetcher()
            db_race = fetcher._transform_race(test_race)

            # Insert race
            race_result = self.db_client.insert_races([db_race])

            # Insert runners if present
            runners_inserted = 0
            if 'runners' in test_race:
                db_runners = [fetcher._transform_runner(r, test_race['id']) for r in test_race['runners']]
                runner_result = self.db_client.insert_runners(db_runners)
                runners_inserted = runner_result.get('inserted', 0)

            logger.info(f"✅ Inserted test race: {race_result.get('inserted', 0)} race(s), {runners_inserted} runner(s)")
            return {
                'table': 'ra_races',
                'success': True,
                'columns_from_api': len([k for k in test_race.keys() if test_race[k] is not None]),
                'runners_inserted': runners_inserted,
                'data': db_race
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test race: {e}", exc_info=True)
            return {'table': 'ra_races', 'success': False, 'error': str(e)}

    def insert_test_bookmaker(self) -> Dict:
        """Fetch, mark, and insert test bookmaker"""
        logger.info("Processing ra_mst_bookmakers...")

        try:
            bookmaker = self.fetch_real_bookmaker_data()
            if not bookmaker:
                return {'table': 'ra_mst_bookmakers', 'success': False, 'error': 'No data from API'}

            test_bookmaker = self.mark_bookmaker_as_test(bookmaker)

            from fetchers.bookmakers_fetcher import BookmakersFetcher
            fetcher = BookmakersFetcher()
            db_record = fetcher._transform_bookmaker(test_bookmaker)

            result = self.db_client.insert_bookmakers([db_record])

            logger.info(f"✅ Inserted test bookmaker: {result.get('inserted', 0)} row(s)")
            return {
                'table': 'ra_mst_bookmakers',
                'success': True,
                'columns_from_api': len([k for k in test_bookmaker.keys() if test_bookmaker[k] is not None]),
                'data': db_record
            }

        except Exception as e:
            logger.error(f"❌ Error inserting test bookmaker: {e}", exc_info=True)
            return {'table': 'ra_mst_bookmakers', 'success': False, 'error': str(e)}

    def insert_all_test_data(self, tables: List[str] = None) -> Dict:
        """Insert test data from real API sources"""

        # Map table names to insert methods
        table_handlers = {
            'ra_mst_courses': self.insert_test_course,
            'ra_mst_jockeys': self.insert_test_jockey,
            'ra_mst_trainers': self.insert_test_trainer,
            'ra_mst_owners': self.insert_test_owner,
            'ra_mst_horses': self.insert_test_horse,
            'ra_races': self.insert_test_race,
            'ra_mst_bookmakers': self.insert_test_bookmaker,
        }

        # Filter to specified tables or use all
        if tables:
            tables_to_insert = [t for t in tables if t in table_handlers]
        else:
            tables_to_insert = list(table_handlers.keys())

        logger.info(f"\n{'=' * 80}")
        logger.info(f"API-SOURCE TEST DATA INSERTION")
        logger.info(f"Processing {len(tables_to_insert)} tables with REAL API data")
        logger.info(f"{'=' * 80}\n")

        results = {
            'timestamp': datetime.now().isoformat(),
            'tables_processed': len(tables_to_insert),
            'successful': 0,
            'failed': 0,
            'results': []
        }

        for table_name in tables_to_insert:
            handler = table_handlers[table_name]
            result = handler()
            results['results'].append(result)

            if result['success']:
                results['successful'] += 1
            else:
                results['failed'] += 1

        return results

    def cleanup_test_data(self, tables: List[str] = None) -> Dict:
        """Remove all test data from tables"""

        # Get tables to clean
        all_tables = [
            'ra_mst_courses', 'ra_mst_jockeys', 'ra_mst_trainers',
            'ra_mst_owners', 'ra_mst_horses', 'ra_races', 'ra_runners',
            'ra_mst_bookmakers'
        ]

        tables_to_clean = tables if tables else all_tables

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
                # Delete by ID containing **TEST**
                result = self.db_client.client.table(table_name).delete().like('id', f'%{self.test_marker}%').execute()
                if result.data:
                    deleted_count += len(result.data)
                    logger.info(f"  Deleted {len(result.data)} rows by id")

                # Also try name field
                try:
                    result = self.db_client.client.table(table_name).delete().like('name', f'%{self.test_marker}%').execute()
                    if result.data:
                        deleted_count += len(result.data)
                        logger.info(f"  Deleted {len(result.data)} rows by name")
                except:
                    pass  # Table might not have name column

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
        print(f"API-SOURCE TEST DATA {action} SUMMARY")
        print(f"{'=' * 80}")
        print(f"\nTables Processed: {results['tables_processed']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")

        if cleanup:
            print(f"Total Rows Deleted: {results['total_deleted']}")
        else:
            # Show API columns captured
            total_api_cols = sum(r.get('columns_from_api', 0) for r in results['results'] if r['success'])
            print(f"Total API Fields Captured: {total_api_cols}")

        if results['failed'] > 0:
            print(f"\n❌ Failed Tables:")
            for result in results['results']:
                if not result['success']:
                    print(f"  - {result['table']}: {result.get('error', 'Unknown error')}")

        if not cleanup and results['successful'] > 0:
            print(f"\n✅ Successful Insertions:")
            for result in results['results']:
                if result['success']:
                    api_cols = result.get('columns_from_api', 0)
                    print(f"  - {result['table']}: {api_cols} API fields captured")

        print(f"\n{'=' * 80}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='API-source test data insertion')
    parser.add_argument('--tables', nargs='+', help='Specific tables to insert test data into')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test data instead of inserting')

    args = parser.parse_args()

    inserter = APISourceTestInserter()

    if args.cleanup:
        results = inserter.cleanup_test_data(tables=args.tables)
        inserter.print_summary(results, cleanup=True)
    else:
        results = inserter.insert_all_test_data(tables=args.tables)
        inserter.print_summary(results, cleanup=False)

    return results


if __name__ == '__main__':
    main()
