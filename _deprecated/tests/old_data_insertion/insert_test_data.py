"""
Insert Test Data Script

Inserts one test row into each of the 23 ra_ tables with **TEST** markers
in each column. This helps verify that:
1. All columns are accessible
2. Fetchers are capturing all fields
3. Data types are correct
4. No columns are being missed

Usage:
    # Insert test data into all tables
    python3 fetchers/insert_test_data.py

    # Insert test data into specific tables
    python3 fetchers/insert_test_data.py --tables ra_races ra_runners

    # From controller
    python3 fetchers/master_fetcher_controller.py --mode test-insert

    # Clean up test data
    python3 fetchers/insert_test_data.py --cleanup
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime, timedelta
from typing import Dict, List
from uuid import uuid4

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('test_data_inserter')


class TestDataInserter:
    """Insert test data into all ra_ tables"""

    def __init__(self):
        """Initialize inserter"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.test_id_suffix = "**TEST**"
        self.test_timestamp = datetime.now().isoformat()

    def get_test_data_for_table(self, table_name: str) -> Dict:
        """Generate test data for a specific table"""

        # Common test values
        test_date = "2099-12-31"
        test_datetime = "2099-12-31T23:59:59"
        test_id = f"test_{uuid4().hex[:8]}"

        # Table-specific test data
        if table_name == 'ra_mst_courses':
            return {
                'course_id': f"{test_id}_course",
                'name': f"**TEST** Course Name {test_id}",
                'region': '**TEST**',
                'country_code': 'GB',
                'type': '**TEST**',
                'surface': '**TEST**',
                'latitude': 99.9999,
                'longitude': 99.9999,
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_bookmakers':
            return {
                'bookmaker_id': f"{test_id}_bookmaker",
                'name': f"**TEST** Bookmaker {test_id}",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_regions':
            return {
                'region_code': f"**TEST**_{uuid4().hex[:4]}",
                'name': f"**TEST** Region {test_id}",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_jockeys':
            return {
                'jockey_id': f"{test_id}_jockey",
                'name': f"**TEST** Jockey Name {test_id}",
                'first_name': f"**TEST** First",
                'last_name': f"**TEST** Last",
                'title': '**TEST**',
                'short_name': '**TEST**',
                'jockey_name': f"**TEST** Jockey {test_id}",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_trainers':
            return {
                'trainer_id': f"{test_id}_trainer",
                'name': f"**TEST** Trainer Name {test_id}",
                'first_name': f"**TEST** First",
                'last_name': f"**TEST** Last",
                'title': '**TEST**',
                'short_name': '**TEST**',
                'location': '**TEST**',
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_owners':
            return {
                'owner_id': f"{test_id}_owner",
                'name': f"**TEST** Owner Name {test_id}",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_horses':
            return {
                'horse_id': f"{test_id}_horse",
                'name': f"**TEST** Horse Name {test_id}",
                'sex': '**TEST**',
                'sex_code': 'T',
                'dob': test_date,
                'colour': '**TEST**',
                'colour_code': 'T',
                'region': '**TEST**',
                'sire_id': f"{test_id}_sire",
                'dam_id': f"{test_id}_dam",
                'damsire_id': f"{test_id}_damsire",
                'sire_name': f"**TEST** Sire",
                'dam_name': f"**TEST** Dam",
                'damsire_name': f"**TEST** Damsire",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_horse_pedigree':
            return {
                'horse_id': f"{test_id}_horse_ped",
                'sire_id': f"{test_id}_sire",
                'sire_name': f"**TEST** Sire",
                'dam_id': f"{test_id}_dam",
                'dam_name': f"**TEST** Dam",
                'damsire_id': f"{test_id}_damsire",
                'damsire_name': f"**TEST** Damsire",
                'breeder_id': f"{test_id}_breeder",
                'breeder': f"**TEST** Breeder",
                'region': '**TEST**',
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_races':
            return {
                'race_id': f"{test_id}_race",
                'course_id': f"{test_id}_course",
                'course_name': f"**TEST** Course",
                'off_dt': test_datetime,
                'race_date': test_date,
                'race_time': '23:59',
                'race_name': f"**TEST** Race {test_id}",
                'distance_f': 9999,
                'distance_y': 999,
                'distance_m': 9999,
                'race_class': '**TEST**',
                'pattern': '**TEST**',
                'rating_band': '**TEST**',
                'age_band': '**TEST**',
                'sex_restriction': '**TEST**',
                'going': '**TEST**',
                'surface': '**TEST**',
                'prize': 999999,
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_runners':
            return {
                'race_id': f"{test_id}_race",
                'horse_id': f"{test_id}_horse",
                'horse_name': f"**TEST** Horse",
                'jockey_id': f"{test_id}_jockey",
                'jockey_name': f"**TEST** Jockey",
                'trainer_id': f"{test_id}_trainer",
                'trainer_name': f"**TEST** Trainer",
                'owner_id': f"{test_id}_owner",
                'owner_name': f"**TEST** Owner",
                'draw': 99,
                'weight_st': 99,
                'weight_lbs': 99,
                'weight_stones_lbs': '**TEST**',
                'jockey_claim_lbs': 99,
                'age': 99,
                'headgear': '**TEST**',
                'position': 99,
                'distance_beaten': 999.99,
                'prize_won': 999999,
                'starting_price': '**TEST**',
                'starting_price_decimal': 999.99,
                'finishing_time': '**TEST**',
                'race_comment': '**TEST** Comment',
                'jockey_silk_url': '**TEST** URL',
                'overall_beaten_distance': 999.99,
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_race_results':
            return {
                'race_id': f"{test_id}_race_result",
                'course_id': f"{test_id}_course",
                'course_name': f"**TEST** Course",
                'off_dt': test_datetime,
                'race_date': test_date,
                'race_time': '23:59',
                'race_name': f"**TEST** Race Result",
                'distance_f': 9999,
                'going': '**TEST**',
                'surface': '**TEST**',
                'race_class': '**TEST**',
                'pattern': '**TEST**',
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_sires':
            return {
                'sire_id': f"{test_id}_sire_stats",
                'name': f"**TEST** Sire Stats",
                'total_runners': 9999,
                'wins': 9999,
                'places_2nd': 999,
                'places_3rd': 999,
                'win_rate': 99.99,
                'place_rate': 99.99,
                'earnings': 9999999,
                'avg_prize': 99999,
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_dams':
            return {
                'dam_id': f"{test_id}_dam_stats",
                'name': f"**TEST** Dam Stats",
                'total_runners': 9999,
                'wins': 9999,
                'places_2nd': 999,
                'places_3rd': 999,
                'win_rate': 99.99,
                'place_rate': 99.99,
                'earnings': 9999999,
                'avg_prize': 99999,
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        elif table_name == 'ra_mst_damsires':
            return {
                'damsire_id': f"{test_id}_damsire_stats",
                'name': f"**TEST** Damsire Stats",
                'total_runners': 9999,
                'wins': 9999,
                'places_2nd': 999,
                'places_3rd': 999,
                'win_rate': 99.99,
                'place_rate': 99.99,
                'earnings': 9999999,
                'avg_prize': 99999,
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        # Future/empty tables - minimal test data
        elif table_name in ['ra_entity_combinations', 'ra_performance_by_distance',
                           'ra_performance_by_venue', 'ra_runner_statistics',
                           'ra_runner_supplementary', 'ra_odds_live',
                           'ra_odds_historical', 'ra_odds_statistics', 'ra_runner_odds']:
            return {
                'id': f"**TEST**_{uuid4().hex[:8]}",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

        else:
            # Generic fallback
            return {
                'id': f"**TEST**_{uuid4().hex[:8]}",
                'name': f"**TEST** {table_name} {test_id}",
                'created_at': test_datetime,
                'updated_at': test_datetime
            }

    def insert_test_row(self, table_name: str) -> Dict:
        """Insert one test row into a table"""
        logger.info(f"Inserting test data into: {table_name}")

        try:
            test_data = self.get_test_data_for_table(table_name)

            # Insert into table
            result = self.db_client.client.table(table_name).insert(test_data).execute()

            if result.data:
                logger.info(f"✅ Successfully inserted test row into {table_name}")
                return {
                    'table': table_name,
                    'success': True,
                    'data': result.data[0] if result.data else test_data
                }
            else:
                logger.error(f"❌ No data returned after insert for {table_name}")
                return {
                    'table': table_name,
                    'success': False,
                    'error': 'No data returned'
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

        default_tables = [
            'ra_mst_courses',
            'ra_mst_bookmakers',
            'ra_mst_regions',
            'ra_mst_jockeys',
            'ra_mst_trainers',
            'ra_mst_owners',
            'ra_mst_horses',
            'ra_horse_pedigree',
            'ra_races',
            'ra_runners',
            'ra_race_results',
            'ra_mst_sires',
            'ra_mst_dams',
            'ra_mst_damsires',
            # Future/partial tables
            'ra_entity_combinations',
            'ra_performance_by_distance',
            'ra_performance_by_venue',
            'ra_runner_statistics',
            'ra_runner_supplementary',
            'ra_odds_live',
            'ra_odds_historical',
            'ra_odds_statistics',
            'ra_runner_odds'
        ]

        tables_to_insert = tables if tables else default_tables

        logger.info(f"\n{'=' * 80}")
        logger.info(f"INSERTING TEST DATA INTO {len(tables_to_insert)} TABLES")
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
        """Remove all test data (rows containing **TEST**) from tables"""

        default_tables = [
            'ra_mst_courses', 'ra_mst_bookmakers', 'ra_mst_regions',
            'ra_mst_jockeys', 'ra_mst_trainers', 'ra_mst_owners',
            'ra_mst_horses', 'ra_horse_pedigree', 'ra_races',
            'ra_runners', 'ra_race_results', 'ra_mst_sires',
            'ra_mst_dams', 'ra_mst_damsires',
            'ra_entity_combinations', 'ra_performance_by_distance',
            'ra_performance_by_venue', 'ra_runner_statistics',
            'ra_runner_supplementary', 'ra_odds_live',
            'ra_odds_historical', 'ra_odds_statistics', 'ra_runner_odds'
        ]

        tables_to_clean = tables if tables else default_tables

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

            try:
                # Try to delete by name field containing **TEST**
                try:
                    result = self.db_client.client.table(table_name).delete().like('name', '%**TEST**%').execute()
                    deleted = len(result.data) if result.data else 0
                    logger.info(f"  Deleted {deleted} rows by name field")
                    results['total_deleted'] += deleted
                except:
                    pass

                # Try to delete by id field containing **TEST**
                try:
                    result = self.db_client.client.table(table_name).delete().like('id', '%**TEST**%').execute()
                    deleted = len(result.data) if result.data else 0
                    logger.info(f"  Deleted {deleted} rows by id field")
                    results['total_deleted'] += deleted
                except:
                    pass

                # Try other common ID fields
                for id_field in ['course_id', 'bookmaker_id', 'jockey_id', 'trainer_id',
                                'owner_id', 'horse_id', 'race_id', 'sire_id', 'dam_id', 'damsire_id']:
                    try:
                        result = self.db_client.client.table(table_name).delete().like(id_field, '%test_%').execute()
                        deleted = len(result.data) if result.data else 0
                        if deleted > 0:
                            logger.info(f"  Deleted {deleted} rows by {id_field} field")
                            results['total_deleted'] += deleted
                    except:
                        pass

                results['successful'] += 1
                results['results'].append({
                    'table': table_name,
                    'success': True
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
        print(f"TEST DATA {action} SUMMARY")
        print(f"{'=' * 80}")
        print(f"\nTables Processed: {results['tables_processed']}")
        print(f"Successful: {results['successful']}")
        print(f"Failed: {results['failed']}")

        if cleanup:
            print(f"Total Rows Deleted: {results['total_deleted']}")

        if results['failed'] > 0:
            print(f"\n❌ Failed Tables:")
            for result in results['results']:
                if not result['success']:
                    print(f"  - {result['table']}: {result.get('error', 'Unknown error')}")

        print(f"\n{'=' * 80}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Insert test data into ra_ tables')
    parser.add_argument('--tables', nargs='+', help='Specific tables to insert test data into')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test data instead of inserting')

    args = parser.parse_args()

    inserter = TestDataInserter()

    if args.cleanup:
        results = inserter.cleanup_test_data(tables=args.tables)
        inserter.print_summary(results, cleanup=True)
    else:
        results = inserter.insert_all_test_data(tables=args.tables)
        inserter.print_summary(results, cleanup=False)

    return results


if __name__ == '__main__':
    main()
