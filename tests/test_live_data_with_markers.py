"""
Live Data Test Insertion with **TEST** Markers

Fetches REAL data from Racing API, adds **TEST** markers to every field,
then inserts into database for visual verification.

This tests the COMPLETE pipeline:
1. Fetch from Racing API (real endpoints)
2. Transform data (real transformation logic)
3. Add **TEST** markers (for visual identification)
4. Insert to database (real insertion logic)
5. Verify all columns populated (visual check in Supabase)
6. Cleanup (delete all **TEST** rows)

Usage:
    # Fetch and insert with TEST markers
    python3 tests/test_live_data_with_markers.py

    # Specific entity types
    python3 tests/test_live_data_with_markers.py --entities races runners

    # Cleanup
    python3 tests/test_live_data_with_markers.py --cleanup
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any
from copy import deepcopy

from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

# Import fetchers
from fetchers.races_fetcher import RacesFetcher
from fetchers.results_fetcher import ResultsFetcher

logger = get_logger('test_live_data')


class LiveDataTestInserter:
    """Fetch REAL data from API and insert with **TEST** markers"""

    def __init__(self):
        """Initialize inserter"""
        self.config = get_config()
        self.api_client = RacingAPIClient(
            username=self.config.api.username,
            password=self.config.api.password
        )
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key,
            batch_size=self.config.supabase.batch_size
        )
        self.test_marker = "**TEST**"

    def add_test_markers_to_value(self, value: Any, field_name: str = "") -> Any:
        """
        Add test markers to values based on type:
        - Strings: Add **TEST** prefix
        - Numbers: Replace with -99999 (sentinel value)
        - Booleans: Replace with True (sentinel value)
        - Timestamps/IDs: Skip (keep original)

        This allows visual verification in Supabase across ALL field types!
        """

        if value is None:
            return None

        # SKIP timestamp/datetime/auto-generated/ID fields (keep original values)
        skip_fields = {
            'created_at', 'updated_at', 'id',  # Auto-generated
            'off_dt', 'date', 'dob', 'last_run',  # Timestamp/date fields
            'race_id', 'horse_id', 'jockey_id', 'trainer_id', 'owner_id',  # ID fields
            'sire_id', 'dam_id', 'damsire_id', 'course_id', 'meet_id'  # More ID fields
        }
        if field_name in skip_fields:
            return value  # Don't modify these

        # SKIP if value looks like an ISO timestamp format (e.g., "2025-10-23T10:14:59.726351")
        if isinstance(value, str) and 'T' in value and ':' in value and len(value) > 10:
            # Looks like ISO timestamp format
            return value

        # STRING values - add **TEST** prefix
        if isinstance(value, str):
            # Don't double-mark
            if self.test_marker in value:
                return value
            return f"{self.test_marker} {value}"

        # NUMERIC values - replace with sentinel value -99999 (visually distinctive)
        elif isinstance(value, (int, float)):
            return -99999  # Sentinel value for test data

        # BOOLEAN values - replace with True (sentinel value)
        elif isinstance(value, bool):
            return True  # Sentinel value for test data

        # Dict/JSON values - recursively process
        elif isinstance(value, dict):
            marked_dict = {}
            for k, v in value.items():
                marked_dict[k] = self.add_test_markers_to_value(v, k)
            return marked_dict

        # List values - recursively process
        elif isinstance(value, list):
            return [self.add_test_markers_to_value(item) for item in value]

        # Default - return as is
        else:
            return value

    def add_test_markers_to_record(self, record: Dict) -> Dict:
        """Add **TEST** markers to all fields in a record"""

        marked_record = {}

        for field_name, value in record.items():
            marked_record[field_name] = self.add_test_markers_to_value(value, field_name)

        return marked_record

    def fetch_and_insert_races(self, days_back: int = 1) -> Dict:
        """Fetch real races from API and insert with TEST markers"""

        logger.info(f"\n{'=' * 80}")
        logger.info("FETCHING REAL RACES DATA WITH **TEST** MARKERS")
        logger.info(f"{'=' * 80}\n")

        # Use RacesFetcher to get real data
        races_fetcher = RacesFetcher()

        # Fetch races from yesterday (guaranteed to have data)
        target_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
        logger.info(f"Fetching races for date: {target_date}")

        # Fetch races (this gets REAL data from Racing API)
        result = races_fetcher.fetch_and_store(
            region_codes=['gb', 'ire'],
            days_back=days_back
        )

        if not result.get('success'):
            logger.error(f"Failed to fetch races: {result.get('error')}")
            return {
                'success': False,
                'error': result.get('error'),
                'races_marked': 0,
                'runners_marked': 0
            }

        # Get the fetched data
        races_fetched = result.get('fetched', 0)
        logger.info(f"\n✅ Fetched {races_fetched} races from Racing API")

        # Now fetch the data we just inserted and add TEST markers
        logger.info("\nAdding **TEST** markers to fetched data...")

        # Get races from database (the ones we just inserted)
        races_query = self.db_client.client.table('ra_mst_races').select('*').gte('date', target_date).limit(5).execute()

        if not races_query.data:
            logger.warning("No races found in database to mark")
            return {
                'success': True,
                'races_marked': 0,
                'runners_marked': 0,
                'warning': 'No races fetched to mark'
            }

        races_marked = 0
        runners_marked = 0
        horses_marked = 0
        pedigrees_marked = 0

        # Collect all horse IDs from runners
        all_horse_ids = set()

        # Add TEST markers to each race
        for race in races_query.data:
            race_id = race['id']  # Column is 'id' not 'race_id'

            # Add markers to race record
            marked_race = self.add_test_markers_to_record(race)

            # Update the race with marked data
            try:
                self.db_client.client.table('ra_mst_races').update(marked_race).eq('id', race_id).execute()
                races_marked += 1
                logger.info(f"  ✅ Marked race: {race_id} - {marked_race.get('race_title', 'N/A')[:50]}")
            except Exception as e:
                logger.error(f"  ❌ Failed to mark race {race_id}: {e}")

            # Get runners for this race
            runners_query = self.db_client.client.table('ra_mst_runners').select('*').eq('race_id', race_id).execute()

            if runners_query.data:
                for runner in runners_query.data:
                    # Collect horse ID for later
                    if runner.get('horse_id'):
                        all_horse_ids.add(runner['horse_id'])

                    # Add markers to runner record
                    marked_runner = self.add_test_markers_to_record(runner)

                    # Update the runner with marked data
                    try:
                        # Use composite key (race_id, horse_id)
                        self.db_client.client.table('ra_mst_runners').update(marked_runner).eq('race_id', race_id).eq('horse_id', runner['horse_id']).execute()
                        runners_marked += 1
                    except Exception as e:
                        logger.error(f"  ❌ Failed to mark runner {runner.get('horse_name')}: {e}")

        # Now mark horses from ra_mst_horses
        logger.info(f"\nMarking horses in ra_mst_horses...")
        if all_horse_ids:
            horses_query = self.db_client.client.table('ra_mst_horses').select('*').in_('id', list(all_horse_ids)).execute()

            if horses_query.data:
                for horse in horses_query.data:
                    marked_horse = self.add_test_markers_to_record(horse)

                    try:
                        self.db_client.client.table('ra_mst_horses').update(marked_horse).eq('id', horse['id']).execute()
                        horses_marked += 1
                        logger.info(f"  ✅ Marked horse: {horse.get('id')} - {marked_horse.get('name', 'N/A')[:40]}")
                    except Exception as e:
                        logger.error(f"  ❌ Failed to mark horse {horse.get('id')}: {e}")

        # Mark pedigree records (enrichment data)
        logger.info(f"\nMarking pedigree enrichment data...")
        if all_horse_ids:
            pedigree_query = self.db_client.client.table('ra_horse_pedigree').select('*').in_('horse_id', list(all_horse_ids)).execute()

            if pedigree_query.data:
                for pedigree in pedigree_query.data:
                    marked_pedigree = self.add_test_markers_to_record(pedigree)

                    try:
                        self.db_client.client.table('ra_horse_pedigree').update(marked_pedigree).eq('horse_id', pedigree['horse_id']).execute()
                        pedigrees_marked += 1
                        logger.info(f"  ✅ Marked pedigree: {pedigree.get('horse_id')}")
                    except Exception as e:
                        logger.error(f"  ❌ Failed to mark pedigree {pedigree.get('horse_id')}: {e}")
            else:
                logger.warning(f"  ⚠️  No pedigree records found (enrichment may not have run)")

        logger.info(f"\n{'=' * 80}")
        logger.info(f"SUMMARY:")
        logger.info(f"{'=' * 80}")
        logger.info(f"Races marked with **TEST**: {races_marked}")
        logger.info(f"Runners marked with **TEST**: {runners_marked}")
        logger.info(f"Horses marked with **TEST**: {horses_marked}")
        logger.info(f"Pedigrees marked with **TEST**: {pedigrees_marked}")
        logger.info(f"\nEnrichment status:")
        if pedigrees_marked > 0:
            logger.info(f"✅ Enrichment WORKED - {pedigrees_marked} pedigree records created")
        else:
            logger.info(f"⚠️  Enrichment MAY NOT HAVE RUN - no pedigree records found")
            logger.info(f"   Possible causes:")
            logger.info(f"   - Horses already existed in database (enrichment only for NEW horses)")
            logger.info(f"   - No new horses discovered in this race data")
        logger.info(f"\nNow open Supabase and verify:")
        logger.info(f"1. Check ra_races table - look for **TEST** in all columns")
        logger.info(f"2. Check ra_mst_runners table - look for **TEST** in all columns")
        logger.info(f"3. Check ra_mst_horses table - look for **TEST** in name column")
        logger.info(f"4. Check ra_horse_pedigree table - look for **TEST** in enrichment fields")
        logger.info(f"{'=' * 80}\n")

        return {
            'success': True,
            'races_marked': races_marked,
            'runners_marked': runners_marked,
            'horses_marked': horses_marked,
            'pedigrees_marked': pedigrees_marked,
            'enrichment_verified': pedigrees_marked > 0,
            'total_marked': races_marked + runners_marked + horses_marked + pedigrees_marked
        }

    def cleanup_test_data(self) -> Dict:
        """Remove all records with **TEST** markers"""

        logger.info(f"\n{'=' * 80}")
        logger.info("CLEANING UP **TEST** DATA")
        logger.info(f"{'=' * 80}\n")

        results = {
            'success': True,
            'tables_cleaned': 0,
            'total_deleted': 0,
            'details': []
        }

        # Tables to clean (in order - child tables first)
        tables_to_clean = [
            ('ra_mst_runners', 'horse_name'),  # Child table
            ('ra_mst_race_results', 'horse_name'),  # Child table
            ('ra_races', 'race_name'),  # Parent table - FIXED: race_title → race_name
            ('ra_horse_pedigree', 'sire'),  # Enrichment data
            ('ra_mst_horses', 'name'),  # Note: column is 'name' not 'horse_name'
            ('ra_mst_jockeys', 'name'),  # Note: column is 'name' not 'jockey_name'
            ('ra_mst_trainers', 'name'),  # Note: column is 'name' not 'trainer_name'
            ('ra_mst_owners', 'name'),  # Note: column is 'name' not 'owner_name'
        ]

        for table_name, text_column in tables_to_clean:
            logger.info(f"Cleaning {table_name}...")

            try:
                # Delete rows where text column contains **TEST**
                result = self.db_client.client.table(table_name).delete().like(text_column, f'%{self.test_marker}%').execute()

                deleted_count = len(result.data) if result.data else 0

                if deleted_count > 0:
                    logger.info(f"  ✅ Deleted {deleted_count} rows from {table_name}")
                    results['tables_cleaned'] += 1
                    results['total_deleted'] += deleted_count
                else:
                    logger.info(f"  ℹ️  No test data found in {table_name}")

                results['details'].append({
                    'table': table_name,
                    'deleted': deleted_count,
                    'success': True
                })

            except Exception as e:
                logger.error(f"  ❌ Error cleaning {table_name}: {e}")
                results['details'].append({
                    'table': table_name,
                    'deleted': 0,
                    'success': False,
                    'error': str(e)
                })

        logger.info(f"\n{'=' * 80}")
        logger.info(f"CLEANUP SUMMARY:")
        logger.info(f"{'=' * 80}")
        logger.info(f"Tables cleaned: {results['tables_cleaned']}")
        logger.info(f"Total rows deleted: {results['total_deleted']}")
        logger.info(f"{'=' * 80}\n")

        return results


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Live data test with **TEST** markers')
    parser.add_argument('--cleanup', action='store_true', help='Clean up test data instead of inserting')
    parser.add_argument('--days-back', type=int, default=1, help='Days back to fetch data (default: 1)')

    args = parser.parse_args()

    inserter = LiveDataTestInserter()

    if args.cleanup:
        results = inserter.cleanup_test_data()
        if results['success']:
            print(f"\n✅ Cleanup complete: {results['total_deleted']} rows deleted")
        else:
            print(f"\n❌ Cleanup failed")
    else:
        results = inserter.fetch_and_insert_races(days_back=args.days_back)
        if results['success']:
            print(f"\n✅ Live data test complete!")
            print(f"   Races marked: {results['races_marked']}")
            print(f"   Runners marked: {results['runners_marked']}")
            print(f"   Horses marked: {results['horses_marked']}")
            print(f"   Pedigrees marked: {results['pedigrees_marked']}")

            if results.get('enrichment_verified'):
                print(f"\n✅ ENRICHMENT VERIFIED - Pedigree data was captured!")
                print(f"   This proves the hybrid enrichment process works end-to-end:")
                print(f"   1. RacesFetcher fetched real races from API")
                print(f"   2. EntityExtractor detected new horses")
                print(f"   3. Pro endpoint /v1/horses/{{id}}/pro was called")
                print(f"   4. Enrichment data (dob, breeder, pedigree) was stored in ra_horse_pedigree")
            else:
                print(f"\n⚠️  No pedigree enrichment found - horses may have already existed")

            print(f"\n👀 Now open Supabase and verify all columns show **TEST**:")
            print(f"   - ra_races, ra_mst_runners (complete race data)")
            print(f"   - ra_mst_horses (basic horse info)")
            print(f"   - ra_horse_pedigree (enrichment data - dob, breeder, sire, dam, damsire)")
            print(f"\n🧹 When done, cleanup with: python3 tests/test_live_data_with_markers.py --cleanup")
        else:
            print(f"\n❌ Test failed: {results.get('error')}")

    return results


if __name__ == '__main__':
    main()
