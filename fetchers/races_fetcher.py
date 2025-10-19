"""
Races Reference Data Fetcher
Fetches race and runner data from Racing API racecards endpoint
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.entity_extractor import EntityExtractor
from utils.position_parser import (
    parse_int_field,
    parse_rating,
    parse_decimal_field,
    parse_text_field
)

logger = get_logger('races_fetcher')


class RacesFetcher:
    """Fetcher for race and runner reference data from racecards"""

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
        days_back: int = 30,
        region_codes: List[str] = None
    ) -> Dict:
        """
        Fetch racecards from API and store races and runners in database

        Args:
            start_date: Start date (YYYY-MM-DD format). If None, calculated from days_back
            end_date: End date (YYYY-MM-DD format). If None, defaults to today
            days_back: Number of days to go back (default: 30). Ignored if start_date provided
            region_codes: Optional list of region codes to filter (e.g., ['gb', 'ire'])

        Returns:
            Statistics dictionary
        """
        logger.info("Starting races and runners fetch from racecards")
        logger.info(f"Region filtering: {region_codes if region_codes else 'None (all regions)'}")

        # Calculate date range
        if end_date is None:
            end_dt = datetime.utcnow().date()
        else:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        if start_date is None:
            start_dt = end_dt - timedelta(days=days_back)
        else:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()

        logger.info(f"Fetching racecards from {start_dt} to {end_dt}")

        all_races = []
        all_runners = []
        days_fetched = 0
        days_with_data = 0

        # Iterate day by day (most efficient per API docs)
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Fetching racecards for {date_str}")

            # Fetch racecards for this date
            api_response = self.api_client.get_racecards_pro(
                date=date_str,
                region_codes=region_codes
            )

            if not api_response or 'racecards' not in api_response:
                logger.warning(f"No racecards returned for {date_str}")
                current_date += timedelta(days=1)
                days_fetched += 1
                continue

            racecards = api_response.get('racecards', [])
            if racecards:
                days_with_data += 1
                logger.info(f"Fetched {len(racecards)} races for {date_str}")

                # Process each race
                for racecard in racecards:
                    race_data, runners_data = self._transform_racecard(racecard)
                    if race_data:
                        all_races.append(race_data)
                    if runners_data:
                        all_runners.extend(runners_data)

            days_fetched += 1
            current_date += timedelta(days=1)

        logger.info(f"Total races fetched: {len(all_races)}")
        logger.info(f"Total runners fetched: {len(all_runners)}")
        logger.info(f"Days fetched: {days_fetched}, Days with data: {days_with_data}")

        # Store in database
        results = {}
        if all_races:
            race_stats = self.db_client.insert_races(all_races)
            results['races'] = race_stats
            logger.info(f"Races inserted: {race_stats}")

        if all_runners:
            runner_stats = self.db_client.insert_runners(all_runners)
            results['runners'] = runner_stats
            logger.info(f"Runners inserted: {runner_stats}")

            # Extract and store entities (jockeys, trainers, owners, horses) from runners
            logger.info("Extracting entities from runner data...")
            entity_stats = self.entity_extractor.extract_and_store_from_runners(all_runners)
            results['entities'] = entity_stats

        return {
            'success': True,
            'fetched': len(all_races),
            'inserted': len(all_races),  # For consistency with other fetchers
            'races_fetched': len(all_races),
            'runners_fetched': len(all_runners),
            'races_inserted': results.get('races', {}).get('inserted', 0),
            'runners_inserted': results.get('runners', {}).get('inserted', 0),
            'days_fetched': days_fetched,
            'days_with_data': days_with_data,
            'api_stats': self.api_client.get_stats(),
            'db_stats': results
        }

    def _transform_racecard(self, racecard: Dict) -> tuple:
        """
        Transform API racecard data into database format

        Args:
            racecard: Raw racecard data from API

        Returns:
            Tuple of (race_dict, list_of_runner_dicts)
        """
        # Extract race data - API uses 'race_id' not 'id'
        race_id = racecard.get('race_id')
        if not race_id:
            logger.warning("Racecard missing race_id, skipping")
            return None, None

        # Helper function to convert distance strings to meters
        def parse_distance_meters(dist_str):
            """Convert distance string like '1m', '6f', '2m4f' to meters (approximate)"""
            if not dist_str or not isinstance(dist_str, str):
                return None
            try:
                # Try direct integer conversion first
                return int(dist_str)
            except (ValueError, TypeError):
                # Parse string like "1m", "6f", "2m4f", etc.
                # Note: This is approximate. 1 furlong ≈ 201 meters, 1 mile ≈ 1609 meters
                dist_str = dist_str.lower().strip()
                meters = 0

                # Extract miles
                if 'm' in dist_str:
                    parts = dist_str.split('m')
                    if parts[0]:
                        try:
                            miles = int(parts[0])
                            meters += miles * 1609  # 1 mile ≈ 1609 meters
                            dist_str = parts[1] if len(parts) > 1 else ''
                        except ValueError:
                            pass

                # Extract furlongs
                if 'f' in dist_str:
                    parts = dist_str.split('f')
                    if parts[0]:
                        try:
                            furlongs = int(parts[0])
                            meters += furlongs * 201  # 1 furlong ≈ 201 meters
                        except ValueError:
                            pass

                return meters if meters > 0 else None

        # Helper function to parse prize money
        def parse_prize_money(prize_str):
            """Convert prize string like '£4,187' to numeric"""
            if not prize_str or not isinstance(prize_str, str):
                return None
            try:
                # Remove currency symbols and commas
                cleaned = prize_str.replace('£', '').replace('$', '').replace(',', '').strip()
                return float(cleaned)
            except (ValueError, AttributeError):
                return None

        # Note: Using imported parse_int_field() and parse_rating() functions from utils.position_parser
        # These handle en-dash "–", empty strings, and other edge cases properly

        # Build race record
        race_record = {
            'id': race_id,
            'is_from_api': True,
            'course_id': racecard.get('course_id'),
            'course_name': racecard.get('course'),
            'region': racecard.get('region'),
            'race_name': racecard.get('race_name'),
            'date': racecard.get('date'),  # RENAMED: race_date → date
            'off_dt': racecard.get('off_dt'),  # RENAMED: off_datetime → off_dt
            'off_time': racecard.get('off_time'),
            # Note: start_time field doesn't exist in ra_races schema
            'type': racecard.get('type'),  # RENAMED: race_type → type
            'race_class': racecard.get('race_class'),
            'distance': racecard.get('distance_f'),  # Numeric furlong value
            'distance_f': racecard.get('distance'),  # String like "1m"
            'distance_m': racecard.get('dist_m'),  # RENAMED: distance_meters → distance_m
            'distance_round': racecard.get('distance_round'),  # Rounded distance
            'age_band': racecard.get('age_band'),
            'surface': racecard.get('surface'),
            'going': racecard.get('going'),
            'going_detailed': racecard.get('going_detailed'),  # Detailed going description
            'track_condition': racecard.get('going_detailed'),  # DEPRECATED - keeping for backwards compat
            'weather_conditions': racecard.get('weather'),  # DEPRECATED - keeping for backwards compat
            'rail_movements': racecard.get('rail_movements'),
            'pattern': racecard.get('pattern'),  # Pattern race designation (Group 1/2/3)
            'sex_restriction': racecard.get('sex_rest'),  # Sex restrictions (colts/fillies)
            'rating_band': racecard.get('rating_band'),  # Rating band (e.g., "0-60")
            'stalls': racecard.get('stalls'),  # Stall information
            'jumps': racecard.get('jumps'),  # Number of jumps (NH racing)
            'betting_enabled': racecard.get('betting_status') == 'enabled',  # Map betting_status to betting_enabled boolean
            'is_abandoned': racecard.get('is_abandoned', False),
            'currency': 'GBP',  # Default currency for UK/IRE races
            'prize': parse_prize_money(racecard.get('prize')),  # RENAMED: prize_money → prize
            # Note: total_prize_money field doesn't exist in ra_races schema
            'is_big_race': racecard.get('big_race', False),  # RENAMED: big_race → is_big_race
            'field_size': len(racecard.get('runners', [])),
            # Result-specific fields (only available in results endpoint, NULL in racecards)
            'has_result': False,  # Racecards don't have results yet
            'winning_time': None,  # Available in results only
            'winning_time_detail': None,  # Available in results only
            'comments': racecard.get('comments'),  # Race comments/verdict
            'non_runners': racecard.get('non_runners'),  # Non-runners list
            # Tote dividends (available in results only)
            'tote_win': None,
            'tote_pl': None,
            'tote_ex': None,
            'tote_csf': None,
            'tote_tricast': None,
            'tote_trifecta': None,
            # Additional metadata
            'race_number': racecard.get('race_number'),  # Race number on card
            'tip': racecard.get('tip'),  # Racing Post tip
            'verdict': racecard.get('verdict'),  # Race verdict
            'betting_forecast': racecard.get('betting_forecast'),  # Pre-race forecast
            'meet_id': racecard.get('meet_id'),  # Meeting ID
            # Note: live_stream_url and replay_url fields don't exist in ra_races schema
            'api_data': racecard,  # Store full API response
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        # Extract runners data
        runners = racecard.get('runners', [])
        runner_records = []

        for idx, runner in enumerate(runners, 1):
            # Generate runner_id from race_id and horse_id (API doesn't provide runner ID)
            horse_id = runner.get('horse_id')
            if not horse_id:
                logger.warning(f"Runner in race {race_id} missing horse_id, skipping")
                continue

            # Create unique runner_id: race_id + horse_id (or use index as fallback)
            runner_id = f"{race_id}_{horse_id}"

            runner_record = {
                'id': runner_id,  # RENAMED: runner_id → id (auto-increment primary key)
                'is_from_api': True,
                'race_id': race_id,
                'horse_id': runner.get('horse_id'),
                'horse_name': runner.get('horse'),
                # Integer fields - use parse_int_field() to handle empty strings and edge cases
                'horse_age': parse_int_field(runner.get('age')),  # Renamed: age → horse_age
                'horse_sex': runner.get('sex'),  # Renamed: sex → horse_sex
                'number': parse_int_field(runner.get('number')),
                'draw': parse_int_field(runner.get('draw')),
                # Note: 'stall' field doesn't exist in ra_runners schema - using 'draw' instead
                'jockey_id': runner.get('jockey_id'),
                'jockey_name': runner.get('jockey'),
                'jockey_claim': runner.get('jockey_claim'),
                'apprentice_allowance': runner.get('jockey_allowance'),
                'trainer_id': runner.get('trainer_id'),
                'trainer_name': runner.get('trainer'),
                'owner_id': runner.get('owner_id'),
                'owner_name': runner.get('owner'),
                'weight_lbs': runner.get('weight_lbs'),  # Numeric weight in lbs
                'headgear': runner.get('headgear'),
                # Parse headgear_run string for boolean flags (but don't store headgear_run itself)
                'blinkers': 'b' in (runner.get('headgear_run') or '').lower(),
                'cheekpieces': 'c' in (runner.get('headgear_run') or '').lower(),
                'visor': 'v' in (runner.get('headgear_run') or '').lower(),
                'tongue_tie': 't' in (runner.get('headgear_run') or '').lower(),
                'sire_id': runner.get('sire_id'),
                'sire_name': runner.get('sire'),  # Will be filtered by supabase_client.py
                'dam_id': runner.get('dam_id'),
                'dam_name': runner.get('dam'),  # Will be filtered by supabase_client.py
                'damsire_id': runner.get('damsire_id'),
                'damsire_name': runner.get('damsire'),  # Will be filtered by supabase_client.py
                'form': runner.get('form'),  # API field is 'form' (e.g., '8', single character)
                # Note: form_string doesn't exist in racecards API - only in results (and is NULL there too)
                'days_since_last_run': parse_int_field(runner.get('days_since_last_run')),
                'last_run_performance': runner.get('last_run'),
                'career_runs': parse_int_field(runner.get('career_total', {}).get('runs')) if isinstance(runner.get('career_total'), dict) else None,
                'career_wins': parse_int_field(runner.get('career_total', {}).get('wins')) if isinstance(runner.get('career_total'), dict) else None,
                'career_places': parse_int_field(runner.get('career_total', {}).get('places')) if isinstance(runner.get('career_total'), dict) else None,
                'prize_money_won': runner.get('prize'),  # API: 'prize' (e.g., "28012.50" or "€400")
                # Rating fields - use parse_rating() to handle en-dash "–" and missing values
                'ofr': parse_rating(runner.get('ofr')),  # RENAMED: official_rating → ofr
                'racing_post_rating': parse_rating(runner.get('rpr')),
                'rpr': parse_rating(runner.get('rpr')),
                # Note: timeform_rating field doesn't exist in ra_runners schema
                'ts': parse_rating(runner.get('ts')),  # RENAMED: tsr → ts
                'silk_url': runner.get('silk_url'),
                # NEW FIELDS - Additional data from Migration 011
                'jockey_claim_lbs': parse_int_field(runner.get('jockey_claim_lbs')),  # API: 'jockey_claim_lbs' (numeric)
                'weight_st_lbs': parse_text_field(runner.get('weight')),  # RENAMED: weight_stones_lbs → weight_st_lbs
                'comment': parse_text_field(runner.get('comment')),  # FIXED: Use 'comment' not 'race_comment' (dropped column!)
                'starting_price_decimal': parse_decimal_field(runner.get('sp_dec')),  # API: 'sp_dec' (decimal odds)
                'overall_beaten_distance': parse_decimal_field(runner.get('ovr_btn')),  # API: 'ovr_btn' (distance in lengths)
                'finishing_time': parse_text_field(runner.get('time')),  # API: 'time' (e.g., "1:15.23")
                # MIGRATION 018 REVISED FIELDS - Standardized naming
                # Horse metadata (existing columns from Migration 003, renamed in Migration 018 REVISED)
                'horse_dob': runner.get('dob'),  # Horse date of birth (renamed from dob)
                'horse_colour': runner.get('colour'),  # Bay, Chestnut, etc. (renamed from colour)
                'breeder': runner.get('breeder'),  # Breeder name (existing from Migration 003)
                # Pedigree regions (existing from Migration 003)
                'sire_region': runner.get('sire_region'),
                'dam_region': runner.get('dam_region'),
                'damsire_region': runner.get('damsire_region'),
                # Trainer data (existing from Migration 003, renamed in Migration 018 REVISED)
                'trainer_location': runner.get('trainer_location'),  # Existing from Migration 003
                'trainer_14_days': runner.get('trainer_14_days'),  # Renamed from trainer_14_days_data
                'trainer_rtf': runner.get('trainer_rtf'),  # Existing from Migration 003
                # Medical/Equipment (existing from Migration 003)
                'wind_surgery': runner.get('wind_surgery'),
                'wind_surgery_run': runner.get('wind_surgery_run'),
                # Expert analysis (existing from Migration 003, renamed in Migration 018 REVISED)
                'spotlight': runner.get('spotlight'),  # Existing from Migration 003
                'quotes': runner.get('quotes'),  # Renamed from quotes_data
                'stable_tour': runner.get('stable_tour'),  # Renamed from stable_tour_data
                'medical': runner.get('medical'),  # Renamed from medical_data
                'past_results_flags': runner.get('past_results_flags'),  # Existing from Migration 003
                # NEW FIELDS from Migration 018 REVISED (truly new, not duplicates)
                'horse_sex_code': runner.get('sex_code'),  # NEW: M/F/G/C (more precise than horse_sex)
                'horse_region': runner.get('region'),  # NEW: GB/IRE/FR/USA
                'headgear_run': runner.get('headgear_run'),  # NEW: "First time", "2nd time", etc.
                'last_run_date': runner.get('last_run'),  # NEW: Date of last run
                'prev_trainers': runner.get('prev_trainers'),  # NEW: Previous trainers (JSONB array)
                'prev_owners': runner.get('prev_owners'),  # NEW: Previous owners (JSONB array)
                'odds': runner.get('odds'),  # NEW: Live bookmaker odds (JSONB array)
                'api_data': runner,  # Store full runner API response
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            runner_records.append(runner_record)

        return race_record, runner_records


def main():
    """Main execution"""
    logger.info("=" * 60)
    logger.info("RACES REFERENCE DATA FETCHER")
    logger.info("=" * 60)

    fetcher = RacesFetcher()

    # Fetch last 30 days of UK and Irish races
    result = fetcher.fetch_and_store(
        days_back=30,
        region_codes=['gb', 'ire']
    )

    logger.info("\n" + "=" * 60)
    logger.info("FETCH COMPLETE")
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Races fetched: {result.get('races_fetched', 0)}")
    logger.info(f"Runners fetched: {result.get('runners_fetched', 0)}")
    logger.info(f"Races inserted: {result.get('races_inserted', 0)}")
    logger.info(f"Runners inserted: {result.get('runners_inserted', 0)}")
    logger.info(f"Days fetched: {result.get('days_fetched', 0)}")
    logger.info(f"Days with data: {result.get('days_with_data', 0)}")
    logger.info("=" * 60)

    return result


if __name__ == '__main__':
    main()
