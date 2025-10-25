"""
Results Reference Data Fetcher
Fetches race results from Racing API results endpoint
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.entity_extractor import EntityExtractor
from utils.position_parser import (
    extract_position_data,
    parse_rating,
    parse_int_field,
    parse_decimal_field,
    parse_text_field
)

logger = get_logger('results_fetcher')


class ResultsFetcher:
    """Fetcher for race results reference data"""

    def __init__(self):
        """Initialize fetcher"""
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
        # Pass API client to entity extractor for Pro enrichment
        self.entity_extractor = EntityExtractor(self.db_client, self.api_client)

    def fetch_and_store(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_back: int = 365,
        region_codes: List[str] = None,
        skip_enrichment: bool = False
    ) -> Dict:
        """
        Fetch results from API and store in database

        Args:
            start_date: Start date (YYYY-MM-DD format). If None, calculated from days_back
            end_date: End date (YYYY-MM-DD format). If None, defaults to today
            days_back: Number of days to go back (default: 365 = ~12 months, API limit)
            region_codes: Optional list of region codes to filter (e.g., ['gb', 'ire'])
            skip_enrichment: If True, skip entity enrichment (faster backfills)

        Returns:
            Statistics dictionary
        """
        logger.info("Starting results fetch")
        logger.info(f"Region filtering: {region_codes if region_codes else 'None (all regions)'}")
        logger.warning("Note: Results API on Standard plan is limited to last 12 months")

        # Calculate date range
        if end_date is None:
            end_dt = datetime.utcnow().date()
        else:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        if start_date is None:
            start_dt = end_dt - timedelta(days=days_back)
        else:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()

        # Warn if date range exceeds 12 months
        date_diff = (end_dt - start_dt).days
        if date_diff > 365:
            logger.warning(f"Date range ({date_diff} days) exceeds 12 months. API may limit results.")

        logger.info(f"Fetching results from {start_dt} to {end_dt}")

        all_results = []
        days_fetched = 0
        days_with_data = 0

        # Iterate day by day
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Fetching results for {date_str}")

            # Fetch results for this date
            api_response = self.api_client.get_results(
                date=date_str,
                region_codes=region_codes
            )

            if not api_response or 'results' not in api_response:
                logger.warning(f"No results returned for {date_str}")
                current_date += timedelta(days=1)
                days_fetched += 1
                continue

            results = api_response.get('results', [])
            if results:
                days_with_data += 1
                logger.info(f"Fetched {len(results)} results for {date_str}")

                # Transform and store results
                for result in results:
                    result_data = self._transform_result(result)
                    if result_data:
                        all_results.append(result_data)

            days_fetched += 1
            current_date += timedelta(days=1)

        logger.info(f"Total results fetched: {len(all_results)}")
        logger.info(f"Days fetched: {days_fetched}, Days with data: {days_with_data}")

        # Store in database
        results_dict = {}
        if all_results:
            # Insert race data into ra_races table
            # Note: Runner results go in ra_race_results (denormalized), full runner data goes in ra_runners
            logger.info(f"Inserting {len(all_results)} races into ra_races...")
            races_to_insert = []
            results_to_insert = []
            all_runners = []

            for result in all_results:
                # Prepare race record for ra_races table
                race_data = result.get('api_data', {})

                # Helper function to get winning time from runners
                def get_winning_time(runners_list):
                    """Extract winning time from position 1 runner"""
                    if not runners_list:
                        return None
                    for runner in runners_list:
                        if runner.get('position') == '1' or runner.get('position') == 1:
                            return runner.get('time')
                    return None

                race_record = {
                    'id': race_data.get('race_id'),  # RENAMED: race_id → id
                    'course_id': race_data.get('course_id'),
                    'course_name': race_data.get('course'),
                    'race_name': race_data.get('race_name'),
                    'date': race_data.get('date'),  # RENAMED: race_date → date
                    'off_time': race_data.get('off'),  # API uses 'off' not 'off_time'
                    'off_dt': race_data.get('off_dt'),  # RENAMED: off_datetime → off_dt
                    'type': race_data.get('type'),  # RENAMED: race_type → type
                    'race_class': race_data.get('class'),  # API uses 'class' not 'race_class'
                    'distance': race_data.get('dist_m'),  # Distance in meters
                    'distance_f': race_data.get('dist_f'),
                    'distance_round': race_data.get('dist'),  # Rounded distance (e.g., "1m")
                    'age_band': race_data.get('age_band'),
                    'surface': race_data.get('surface'),
                    'going': race_data.get('going'),
                    'going_detailed': None,  # Not in results API (racecards only)
                    'pattern': race_data.get('pattern'),  # Pattern race (Group 1/2/3)
                    'sex_restriction': race_data.get('sex_rest'),  # Sex restrictions
                    'rating_band': race_data.get('rating_band'),  # Rating band
                    'jumps': race_data.get('jumps'),  # Number of jumps
                    'prize': race_data.get('prize'),  # RENAMED: prize_money → prize
                    'region': race_data.get('region'),
                    'field_size': len(race_data.get('runners', [])),
                    # Result-specific fields (only available in results, not racecards)
                    'has_result': True,  # Results endpoint always has results
                    'winning_time': get_winning_time(race_data.get('runners', [])),
                    'winning_time_detail': race_data.get('winning_time_detail'),
                    'comments': race_data.get('comments'),  # Race comments/verdict
                    'non_runners': race_data.get('non_runners'),  # Non-runners list
                    # Tote dividends
                    'tote_win': race_data.get('tote_win'),
                    'tote_pl': race_data.get('tote_pl'),
                    'tote_ex': race_data.get('tote_ex'),
                    'tote_csf': race_data.get('tote_csf'),
                    'tote_tricast': race_data.get('tote_tricast'),
                    'tote_trifecta': race_data.get('tote_trifecta'),
                    # Note: results_status field doesn't exist in ra_races schema
                    'is_abandoned': race_data.get('is_abandoned', False),
                    'is_big_race': race_data.get('big_race', False),
                    'race_number': race_data.get('race_number'),
                    'meet_id': race_data.get('meet_id')
                }
                if race_record['id']:
                    races_to_insert.append(race_record)

                # Prepare runner result records for ra_race_results table
                # This table stores individual runner results with race context
                runners = race_data.get('runners', [])
                for runner in runners:
                    position_data = extract_position_data(runner)

                    # Build runner result record matching ra_race_results schema
                    runner_result = {
                        'race_id': race_data.get('race_id'),
                        'race_date': race_data.get('date'),
                        # Runner identification
                        'horse_id': runner.get('horse_id'),
                        'horse_name': runner.get('horse'),
                        'jockey_id': runner.get('jockey_id'),
                        'jockey_name': runner.get('jockey'),
                        'trainer_id': runner.get('trainer_id'),
                        'trainer_name': runner.get('trainer'),
                        'owner_id': runner.get('owner_id'),
                        'owner_name': runner.get('owner'),
                        # Runner details
                        'number': str(runner.get('number')) if runner.get('number') is not None else None,
                        'draw': str(runner.get('draw')) if runner.get('draw') is not None else None,
                        'age': parse_int_field(runner.get('age')),
                        'sex': runner.get('sex'),
                        'weight_lbs': parse_int_field(runner.get('weight_lbs')),
                        'weight_st_lbs': parse_text_field(runner.get('weight')),
                        'headgear': runner.get('headgear'),
                        'official_rating': parse_rating(runner.get('or')),
                        'rpr': parse_rating(runner.get('rpr')),
                        'tsr': parse_rating(runner.get('tsr')),
                        # Pedigree (with names and regions for entity extraction)
                        'sire_id': runner.get('sire_id'),
                        'sire_name': runner.get('sire'),
                        'sire_region': runner.get('sire_region'),
                        'dam_id': runner.get('dam_id'),
                        'dam_name': runner.get('dam'),
                        'dam_region': runner.get('dam_region'),
                        'damsire_id': runner.get('damsire_id'),
                        'damsire_name': runner.get('damsire'),
                        'damsire_region': runner.get('damsire_region'),
                        # Result data (from position_data parser)
                        'position': position_data.get('position'),
                        'position_str': str(position_data.get('position')) if position_data.get('position') else None,
                        'btn': parse_decimal_field(position_data.get('distance_beaten')),  # "beaten" distance
                        'ovr_btn': parse_decimal_field(runner.get('ovr_btn')),  # overall beaten distance
                        'margin': parse_decimal_field(runner.get('margin')),  # margin can be "1L", "0.5L", etc.
                        'prize_won': position_data.get('prize_won'),
                        'sp': position_data.get('starting_price'),  # fractional
                        'sp_decimal': position_data.get('starting_price_decimal'),  # decimal
                        'time_seconds': parse_decimal_field(runner.get('time')),
                        'time_display': runner.get('time'),
                        'comment': parse_text_field(runner.get('comment')),
                        'jockey_claim_lbs': parse_int_field(runner.get('jockey_claim')),
                        'silk_url': runner.get('silk_url')
                    }

                    # Only add if we have required fields
                    if runner_result.get('race_id') and runner_result.get('horse_id'):
                        results_to_insert.append(runner_result)

                        # Also collect for entity extraction
                        runner_data = {
                            'horse_id': runner.get('horse_id'),
                            'horse_name': runner.get('horse'),
                            'sex': runner.get('sex'),
                            'jockey_id': runner.get('jockey_id'),
                            'jockey_name': runner.get('jockey'),
                            'trainer_id': runner.get('trainer_id'),
                            'trainer_name': runner.get('trainer'),
                            'owner_id': runner.get('owner_id'),
                            'owner_name': runner.get('owner')
                        }
                        if runner_data.get('horse_id') and runner_data.get('horse_name'):
                            all_runners.append(runner_data)

            # Insert races into ra_races table
            if races_to_insert:
                logger.info(f"Sample race before insert: {races_to_insert[0] if races_to_insert else 'NONE'}")
                logger.info(f"Total races_to_insert: {len(races_to_insert)}")
                race_stats = self.db_client.insert_races(races_to_insert)
                results_dict['races'] = race_stats
                logger.info(f"Races inserted: {race_stats}")
            else:
                logger.warning(f"No races to insert! all_results count: {len(all_results)}")

            # Insert runner results into ra_race_results table
            # This table stores individual runner results (flattened/denormalized view)
            # It combines runner finishing data with race context for easier querying
            if results_to_insert:
                logger.info(f"Inserting {len(results_to_insert)} runner results into ra_race_results...")
                result_stats = self.db_client.insert_race_results(results_to_insert)
                results_dict['race_results'] = result_stats
                logger.info(f"Runner results inserted: {result_stats}")

            # Insert runner records with position data into ra_runners
            if all_runners:
                logger.info(f"Inserting {len(all_runners)} runner records with position data...")
                runner_records = self._prepare_runner_records(all_results)
                if runner_records:
                    # Validate pedigree IDs to prevent foreign key violations
                    runner_records = self._validate_pedigree_ids(runner_records)
                    runner_stats = self.db_client.insert_runners(runner_records)
                    results_dict['runners'] = runner_stats
                    logger.info(f"Runners inserted: {runner_stats}")
                else:
                    logger.warning("No runner records prepared for insertion")

                # Extract and store entities (jockeys, trainers, owners, horses)
                if skip_enrichment:
                    logger.info(f"SKIPPING entity enrichment for {len(all_runners)} runners (fast mode)")
                    entity_stats = {'skipped': True, 'message': 'Enrichment skipped for fast backfill'}
                    results_dict['entities'] = entity_stats
                else:
                    logger.info(f"Extracting entities from {len(all_runners)} runners...")
                    entity_stats = self.entity_extractor.extract_and_store_from_runners(all_runners)
                    results_dict['entities'] = entity_stats
            else:
                logger.info("No runners found for entity extraction")

        return {
            'success': True,
            'fetched': len(all_results),
            'inserted': results_dict.get('races', {}).get('inserted', 0),
            'days_fetched': days_fetched,
            'days_with_data': days_with_data,
            'api_stats': self.api_client.get_stats(),
            'db_stats': results_dict
        }

    def _transform_result(self, result: Dict) -> Optional[Dict]:
        """
        Transform API result data into database format

        Args:
            result: Raw result data from API

        Returns:
            Transformed result dictionary or None if invalid
        """
        race_id = result.get('race_id')
        if not race_id:
            logger.warning("Result missing race ID, skipping")
            return None

        # Build result record for ra_races table
        # Note: Results data (positions) is stored in ra_runners table
        result_record = {
            'id': race_id,  # RENAMED: race_id → id
            'course_id': result.get('course_id'),
            'course_name': result.get('course'),
            'race_name': result.get('race_name'),
            'date': result.get('race_date'),  # RENAMED: race_date → date
            'off_dt': result.get('off_dt'),  # RENAMED: off_datetime → off_dt
            'off_time': result.get('off_time'),
            'type': result.get('type'),  # RENAMED: race_type → type
            'race_class': result.get('race_class'),
            'distance': result.get('distance'),
            'distance_f': result.get('distance_f'),
            'surface': result.get('surface'),
            'going': result.get('going'),
            'prize': result.get('prize'),  # RENAMED: prize_money → prize
            'region': result.get('region'),
            # Note: results_status field doesn't exist in ra_races schema
            'is_abandoned': result.get('is_abandoned', False),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Extract finishing positions if available
        # The API results endpoint includes runner results with positions
        runners = result.get('runners', [])
        if runners:
            result_record['field_size'] = len(runners)
            # You might want to store runner results separately
            # in a ra_runner_results table - that's optional

        # IMPORTANT: Store raw API data so _prepare_runner_records() can access runners
        result_record['api_data'] = result

        return result_record

    def _validate_pedigree_ids(self, runner_records: List[Dict]) -> List[Dict]:
        """
        Validate pedigree IDs exist in database, set to NULL if not found.
        This prevents foreign key constraint violations.

        Args:
            runner_records: List of runner records with pedigree IDs

        Returns:
            List of runner records with validated pedigree IDs
        """
        if not runner_records:
            return runner_records

        # Get all unique pedigree IDs from runners
        sire_ids = {r.get('sire_id') for r in runner_records if r.get('sire_id')}
        dam_ids = {r.get('dam_id') for r in runner_records if r.get('dam_id')}
        damsire_ids = {r.get('damsire_id') for r in runner_records if r.get('damsire_id')}

        # Query database for existing IDs
        existing_sires = set()
        existing_dams = set()
        existing_damsires = set()

        try:
            if sire_ids:
                result = self.db_client.client.table('ra_mst_sires').select('id').in_('id', list(sire_ids)).execute()
                existing_sires = {row['id'] for row in result.data}

            if dam_ids:
                result = self.db_client.client.table('ra_mst_dams').select('id').in_('id', list(dam_ids)).execute()
                existing_dams = {row['id'] for row in result.data}

            if damsire_ids:
                result = self.db_client.client.table('ra_mst_damsires').select('id').in_('id', list(damsire_ids)).execute()
                existing_damsires = {row['id'] for row in result.data}

        except Exception as e:
            logger.warning(f"Error validating pedigree IDs: {e}")
            # If validation fails, set all to NULL to be safe
            for record in runner_records:
                record['sire_id'] = None
                record['dam_id'] = None
                record['damsire_id'] = None
            return runner_records

        # Update records - set to NULL if ID doesn't exist
        nullified_count = {'sires': 0, 'dams': 0, 'damsires': 0}

        for record in runner_records:
            if record.get('sire_id') and record['sire_id'] not in existing_sires:
                record['sire_id'] = None
                nullified_count['sires'] += 1

            if record.get('dam_id') and record['dam_id'] not in existing_dams:
                record['dam_id'] = None
                nullified_count['dams'] += 1

            if record.get('damsire_id') and record['damsire_id'] not in existing_damsires:
                record['damsire_id'] = None
                nullified_count['damsires'] += 1

        if sum(nullified_count.values()) > 0:
            logger.info(f"Nullified pedigree IDs for missing references: {nullified_count}")

        return runner_records

    def _prepare_runner_records(self, results: List[Dict]) -> List[Dict]:
        """
        Prepare runner records with position data for insertion into ra_runners

        Args:
            results: List of result dictionaries (raw API responses)

        Returns:
            List of runner records ready for database insertion
        """
        runner_records = []

        for result in results:
            race_data = result.get('api_data', {})
            race_id = race_data.get('race_id')
            race_date = race_data.get('date')

            if not race_id:
                continue

            runners = race_data.get('runners', [])

            for runner in runners:
                # Extract position data using our parsing utility
                position_data = extract_position_data(runner)

                # Build runner record
                # Generate runner_id as composite key: race_id + horse_id
                horse_id = runner.get('horse_id')
                if not horse_id:
                    continue

                runner_record = {
                    # DO NOT SET 'id' - it's auto-increment bigint primary key
                    'race_id': race_id,
                    'horse_id': horse_id,
                    'horse_name': runner.get('horse'),
                    'jockey_id': runner.get('jockey_id'),
                    'jockey_name': runner.get('jockey'),
                    'trainer_id': runner.get('trainer_id'),
                    'trainer_name': runner.get('trainer'),
                    'owner_id': runner.get('owner_id'),
                    'owner_name': runner.get('owner'),
                    # Number and draw fields (schema: character varying, not integer)
                    'number': str(runner.get('number')) if runner.get('number') is not None else None,
                    'draw': str(runner.get('draw')) if runner.get('draw') is not None else None,
                    # Pedigree fields
                    'sire_id': runner.get('sire_id'),
                    'dam_id': runner.get('dam_id'),
                    'damsire_id': runner.get('damsire_id'),
                    # Weight fields
                    'weight_lbs': parse_int_field(runner.get('weight_lbs')),  # integer in schema
                    'weight_st_lbs': parse_text_field(runner.get('weight')),  # character varying
                    # Horse metadata - CORRECT field names (age, sex, sex_code, colour, dob)
                    'age': parse_int_field(runner.get('age')),
                    'sex': runner.get('sex'),
                    'sex_code': runner.get('sex_code'),
                    'colour': runner.get('colour'),
                    'dob': runner.get('dob'),
                    # Headgear and equipment
                    'headgear': runner.get('headgear'),
                    'headgear_run': runner.get('headgear_run'),
                    'wind_surgery': runner.get('wind_surgery'),
                    'wind_surgery_run': runner.get('wind_surgery_run'),
                    # Form and performance
                    'form': runner.get('form'),
                    'last_run': runner.get('last_run'),
                    # Rating fields - API may return "–" for missing values, parse safely
                    'ofr': parse_rating(runner.get('or')),
                    'rpr': parse_rating(runner.get('rpr')),
                    'ts': parse_rating(runner.get('tsr')),
                    # Comment and analysis
                    'comment': parse_text_field(runner.get('comment')),
                    'spotlight': runner.get('spotlight'),
                    'trainer_rtf': runner.get('trainer_rtf'),
                    'past_results_flags': runner.get('past_results_flags'),
                    # Claiming prices
                    'claiming_price_min': parse_int_field(runner.get('claiming_price_min')),
                    'claiming_price_max': parse_int_field(runner.get('claiming_price_max')),
                    # Medication and equipment
                    'medication': runner.get('medication'),
                    'equipment': runner.get('equipment'),
                    # Odds
                    'morning_line_odds': runner.get('morning_line_odds'),
                    # Status
                    'is_scratched': runner.get('is_scratched', False),
                    # Silk URL
                    'silk_url': runner.get('silk_url'),
                    # Position and result data (extracted above) - from Migration 005
                    'position': position_data.get('position'),
                    'distance_beaten': position_data.get('distance_beaten'),
                    'prize_won': position_data.get('prize_won'),
                    'starting_price': position_data.get('starting_price'),
                    # Timestamps
                    'created_at': datetime.utcnow().isoformat(),
                    'updated_at': datetime.utcnow().isoformat(),
                    'result_updated_at': datetime.utcnow().isoformat() if position_data.get('position') else None
                }

                runner_records.append(runner_record)

        logger.info(f"Prepared {len(runner_records)} runner records with position data")

        # Log sample of position data for verification
        if runner_records:
            sample = runner_records[0]
            logger.info(f"Sample runner record:")
            logger.info(f"  Horse: {sample.get('horse_name')}")
            logger.info(f"  Position: {sample.get('position')}")
            logger.info(f"  Distance beaten: {sample.get('distance_beaten')}")
            logger.info(f"  Prize: {sample.get('prize_won')}")
            logger.info(f"  SP: {sample.get('starting_price')}")

        return runner_records


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("RESULTS REFERENCE DATA FETCHER")
    logger.info("=" * 60)

    fetcher = ResultsFetcher()

    # Fetch last 365 days (12 months) of UK and Irish results
    # Note: Standard plan API limits to last 12 months
    result = fetcher.fetch_and_store(
        days_back=365,
        region_codes=['gb', 'ire']
    )

    logger.info("\n" + "=" * 60)
    logger.info("FETCH COMPLETE")
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Results fetched: {result.get('fetched', 0)}")
    logger.info(f"Results inserted: {result.get('inserted', 0)}")
    logger.info(f"Days fetched: {result.get('days_fetched', 0)}")
    logger.info(f"Days with data: {result.get('days_with_data', 0)}")
    logger.info("=" * 60)

    return result


if __name__ == '__main__':
    main()
