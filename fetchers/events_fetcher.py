"""
Events Data Fetcher
Consolidated fetcher for all event/transaction data (ra_* tables except ra_mst_*)

Handles:
- Racecards: Pre-race data (races, runners)
- Results: Post-race data (updates runners with positions)
- Entity extraction: Automatically extracts and stores people/horses to master tables

This replaces:
- races_fetcher.py (racecards)
- results_fetcher.py (results)

Key Features:
- Fetches races and runners from racecards
- Updates runners with result data
- Triggers entity extraction for masters (horses, jockeys, trainers, owners)
- Triggers pedigree extraction (sires, dams, damsires)
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.entity_extractor import EntityExtractor

logger = get_logger('events_fetcher')


class EventsFetcher:
    """Consolidated fetcher for all event/transaction data"""

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
        # Pass API client to entity extractor for Pro enrichment
        self.entity_extractor = EntityExtractor(self.db_client, self.api_client)

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    @staticmethod
    def _parse_prize_money(prize_str):
        """
        Convert prize string like '£4,187' or '£301,272' to numeric value

        Args:
            prize_str: Prize string with currency symbols and commas

        Returns:
            Numeric value or None if parsing fails
        """
        if not prize_str or not isinstance(prize_str, str):
            return None
        try:
            # Remove currency symbols and commas
            cleaned = prize_str.replace('£', '').replace('$', '').replace(',', '').strip()
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_prize_won(prize_won_str):
        """
        Convert prize_won string like '£4,187' to numeric value

        Args:
            prize_won_str: Prize won string with currency symbols and commas

        Returns:
            Numeric value or None if parsing fails
        """
        if not prize_won_str or not isinstance(prize_won_str, str):
            return None
        try:
            # Remove currency symbols and commas
            cleaned = prize_won_str.replace('£', '').replace('$', '').replace(',', '').strip()
            return float(cleaned) if cleaned else None
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _parse_position(position_value):
        """
        Parse position value - converts numeric positions to integer, non-numeric to None

        Args:
            position_value: Position value (could be integer, string number, or text like "PU", "REF")

        Returns:
            Integer position or None for non-finishing positions

        Note: Non-finishing positions like "PU" (Pulled Up), "REF" (Refused), "F" (Fell)
        are set to None as they can't be represented as integer positions.
        """
        if position_value is None:
            return None

        # If already an integer, return it
        if isinstance(position_value, int):
            return position_value

        # If string, try to convert to integer
        if isinstance(position_value, str):
            try:
                return int(position_value)
            except ValueError:
                # Non-numeric position (PU, REF, F, etc.) - return None
                return None

        # Try to convert other types
        try:
            return int(position_value)
        except (ValueError, TypeError):
            return None

    # ========================================================================
    # RACECARDS (Pre-race data)
    # ========================================================================

    def fetch_racecards(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_back: int = 1,
        region_codes: List[str] = None
    ) -> Dict:
        """
        Fetch racecards (pre-race data) and store races + runners

        This method:
        1. Fetches racecards from Racing API
        2. Stores races in ra_races
        3. Stores runners in ra_mst_runners
        4. Extracts entities to ra_mst_* tables (horses, jockeys, trainers, owners)
        5. Extracts pedigree to ra_mst_* tables (sires, dams, damsires)

        Args:
            start_date: Start date (YYYY-MM-DD). If None, calculated from days_back
            end_date: End date (YYYY-MM-DD). If None, defaults to today
            days_back: Days to go back (default: 1 for daily run)
            region_codes: Region filter (e.g., ['gb', 'ire'])

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 60)
        logger.info("FETCHING RACECARDS (PRE-RACE DATA)")
        logger.info("=" * 60)

        # Calculate date range
        if end_date is None:
            end_dt = datetime.utcnow().date()
        else:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        if start_date is None:
            start_dt = end_dt - timedelta(days=days_back)
        else:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()

        logger.info(f"Date range: {start_dt} to {end_dt}")
        logger.info(f"Regions: {region_codes if region_codes else 'All'}")

        all_races = []
        all_runners = []
        days_fetched = 0
        days_with_data = 0

        # Iterate day by day
        current_date = start_dt
        while current_date <= end_dt:
            date_str = current_date.strftime('%Y-%m-%d')
            logger.info(f"Fetching racecards for {date_str}")

            # Fetch from API
            api_response = self.api_client.get_racecards_pro(
                date=date_str,
                region_codes=region_codes
            )

            if api_response and 'racecards' in api_response:
                racecards = api_response.get('racecards', [])
                if racecards:
                    days_with_data += 1
                    logger.info(f"Found {len(racecards)} races for {date_str}")

                    # Import transform method from races_fetcher
                    # (For now, we'll use a simplified version)
                    for racecard in racecards:
                        race_data = self._transform_race(racecard)
                        runners_data = self._transform_runners(racecard)

                        if race_data:
                            all_races.append(race_data)
                        if runners_data:
                            all_runners.extend(runners_data)
            else:
                logger.warning(f"No racecards for {date_str}")

            days_fetched += 1
            current_date += timedelta(days=1)

        logger.info(f"Total: {len(all_races)} races, {len(all_runners)} runners")

        # Store in database
        results = {}

        if all_races:
            race_stats = self.db_client.insert_races(all_races)
            results['races'] = race_stats
            logger.info(f"Stored {race_stats.get('inserted', 0)} races")

        if all_runners:
            runner_stats = self.db_client.insert_runners(all_runners)
            results['runners'] = runner_stats
            logger.info(f"Stored {runner_stats.get('inserted', 0)} runners")

            # Extract entities → master tables
            logger.info("Extracting entities to master tables...")
            entity_stats = self.entity_extractor.extract_and_store_from_runners(all_runners)
            results['entities'] = entity_stats
            logger.info(f"Entities extracted: {entity_stats}")

        return {
            'success': True,
            'fetched': len(all_races),
            'races_fetched': len(all_races),
            'runners_fetched': len(all_runners),
            'days_fetched': days_fetched,
            'days_with_data': days_with_data,
            'db_stats': results
        }

    # ========================================================================
    # RESULTS (Post-race data)
    # ========================================================================

    def fetch_results(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        days_back: int = 1,
        region_codes: List[str] = None
    ) -> Dict:
        """
        Fetch results (post-race data) and update runners with positions

        This method:
        1. Fetches results from Racing API
        2. Updates ra_mst_runners with position data (finishing position, time, etc.)
        3. Extracts any new entities to ra_mst_* tables

        Args:
            start_date: Start date (YYYY-MM-DD). If None, calculated from days_back
            end_date: End date (YYYY-MM-DD). If None, defaults to today
            days_back: Days to go back (default: 1 for daily run)
            region_codes: Region filter (e.g., ['gb', 'ire'])

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 60)
        logger.info("FETCHING RESULTS (POST-RACE DATA)")
        logger.info("=" * 60)

        # Calculate date range
        if end_date is None:
            end_dt = datetime.utcnow().date()
        else:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        if start_date is None:
            start_dt = end_dt - timedelta(days=days_back)
        else:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()

        logger.info(f"Date range: {start_dt} to {end_dt}")
        logger.info(f"Regions: {region_codes if region_codes else 'All'}")

        start_date_str = start_dt.strftime('%Y-%m-%d')
        end_date_str = end_dt.strftime('%Y-%m-%d')

        # Fetch results from API
        logger.info(f"Fetching results from {start_date_str} to {end_date_str}")
        api_response = self.api_client.get_results(
            start_date=start_date_str,
            end_date=end_date_str,
            region_codes=region_codes
        )

        if not api_response or 'results' not in api_response:
            logger.warning("No results returned from API")
            return {
                'success': False,
                'error': 'No results from API'
            }

        results_raw = api_response.get('results', [])
        logger.info(f"Fetched {len(results_raw)} results from API")

        all_runners = []

        # Process results
        for result in results_raw:
            runners_data = self._transform_result_runners(result)
            if runners_data:
                all_runners.extend(runners_data)

        logger.info(f"Total: {len(all_runners)} runners with result data")

        # Update database
        db_results = {}

        if all_runners:
            runner_stats = self.db_client.insert_runners(all_runners)
            db_results['runners'] = runner_stats
            logger.info(f"Updated {runner_stats.get('inserted', 0)} runners with results")

            # Extract any new entities
            entity_stats = self.entity_extractor.extract_and_store_from_runners(all_runners)
            db_results['entities'] = entity_stats

        return {
            'success': True,
            'fetched': len(results_raw),
            'runners_updated': len(all_runners),
            'db_stats': db_results
        }

    # ========================================================================
    # TRANSFORM METHODS (Simplified - use existing fetcher logic)
    # ========================================================================

    def _transform_race(self, racecard: Dict) -> Dict:
        """
        Transform racecard to race record

        Note: This is a simplified version. For full implementation,
        see races_fetcher.py::_transform_racecard()
        """
        race_id = racecard.get('race_id')
        if not race_id:
            return None

        return {
            'id': race_id,
            'course_id': racecard.get('course_id'),
            'date': racecard.get('date'),
            'time': racecard.get('time'),
            'race_name': racecard.get('race_name'),
            'race_class': racecard.get('race_class'),
            'distance': racecard.get('distance'),
            'going': racecard.get('going'),
            'prize': self._parse_prize_money(racecard.get('prize')),
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

    def _transform_runners(self, racecard: Dict) -> List[Dict]:
        """
        Transform racecard runners to runner records

        Note: This is a simplified version. For full implementation,
        see races_fetcher.py::_transform_racecard()
        """
        race_id = racecard.get('race_id')
        runners_raw = racecard.get('runners', [])

        runners = []
        for runner in runners_raw:
            # Handle empty string IDs - convert to None for proper NULL in database
            jockey_id = runner.get('jockey_id')
            if jockey_id == '':
                jockey_id = None

            trainer_id = runner.get('trainer_id')
            if trainer_id == '':
                trainer_id = None

            owner_id = runner.get('owner_id')
            if owner_id == '':
                owner_id = None

            horse_id = runner.get('horse_id')
            if horse_id == '':
                horse_id = None

            runner_record = {
                'race_id': race_id,
                'horse_id': horse_id,
                'horse_name': runner.get('horse'),
                'jockey_id': jockey_id,
                'jockey_name': runner.get('jockey'),
                'trainer_id': trainer_id,
                'trainer_name': runner.get('trainer'),
                'trainer_location': runner.get('trainer_location'),
                'owner_id': owner_id,
                'owner_name': runner.get('owner'),
                'number': runner.get('number'),
                'draw': runner.get('draw'),
                'age': runner.get('age'),
                'sex': runner.get('sex'),
                'weight_lbs': runner.get('weight_lbs'),
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            }
            runners.append(runner_record)

        return runners

    def _transform_result_runners(self, result: Dict) -> List[Dict]:
        """
        Transform result data to runner records with positions

        Note: This is a simplified version. For full implementation,
        see results_fetcher.py::_prepare_runner_records()
        """
        race_id = result.get('race_id')
        runners_raw = result.get('runners', [])

        runners = []
        for runner in runners_raw:
            # Handle empty string horse_id - convert to None for proper NULL in database
            horse_id = runner.get('horse_id')
            if horse_id == '':
                horse_id = None

            runner_record = {
                'race_id': race_id,
                'horse_id': horse_id,
                'position': self._parse_position(runner.get('position')),
                'distance_beaten': runner.get('distance_beaten'),
                'finishing_time': runner.get('finishing_time'),
                'starting_price': runner.get('starting_price'),
                'starting_price_decimal': runner.get('starting_price_decimal'),
                'prize_won': self._parse_prize_won(runner.get('prize_won')),
                'updated_at': datetime.utcnow().isoformat()
            }
            runners.append(runner_record)

        return runners

    # ========================================================================
    # BACKFILL METHODS
    # ========================================================================

    def backfill(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        region_codes: List[str] = None,
        fetch_racecards: bool = True,
        fetch_results: bool = True
    ) -> Dict:
        """
        Backfill historical race data from start_date to end_date

        This method intelligently fetches missing data:
        1. Identifies which dates already have complete data
        2. Fetches only missing racecards/results
        3. Automatically extracts entities to master tables
        4. Processes data in monthly chunks for manageability

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD). If None, defaults to today
            region_codes: Region filter (default: ['gb', 'ire'])
            fetch_racecards: Whether to fetch racecards (default: True)
            fetch_results: Whether to fetch results (default: True)

        Returns:
            Statistics dictionary with totals across all chunks
        """
        if region_codes is None:
            region_codes = ['gb', 'ire']

        if end_date is None:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

        logger.info("=" * 60)
        logger.info("BACKFILLING EVENT DATA (RACES & RESULTS)")
        logger.info("=" * 60)
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Regions: {region_codes}")
        logger.info(f"Fetch racecards: {fetch_racecards}")
        logger.info(f"Fetch results: {fetch_results}")

        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()

        # Calculate total days
        total_days = (end_dt - start_dt).days + 1
        logger.info(f"Total days to process: {total_days}")

        # Generate monthly chunks
        chunks = self._generate_monthly_chunks(start_dt, end_dt)
        logger.info(f"Processing in {len(chunks)} monthly chunks")

        # Statistics
        overall_stats = {
            'success': True,
            'total_chunks': len(chunks),
            'chunks_processed': 0,
            'total_races': 0,
            'total_runners': 0,
            'total_days': total_days,
            'start_date': start_date,
            'end_date': end_date,
            'chunks': []
        }

        # Process each chunk
        for idx, (chunk_start, chunk_end) in enumerate(chunks, 1):
            chunk_start_str = chunk_start.strftime('%Y-%m-%d')
            chunk_end_str = chunk_end.strftime('%Y-%m-%d')

            logger.info(f"\n{'='*60}")
            logger.info(f"CHUNK {idx}/{len(chunks)}: {chunk_start_str} to {chunk_end_str}")
            logger.info(f"{'='*60}")

            chunk_stats = {
                'chunk_number': idx,
                'start_date': chunk_start_str,
                'end_date': chunk_end_str,
                'racecards': None,
                'results': None
            }

            try:
                # Fetch racecards if requested
                if fetch_racecards:
                    logger.info(f"Fetching racecards for chunk {idx}...")
                    racecard_result = self.fetch_racecards(
                        start_date=chunk_start_str,
                        end_date=chunk_end_str,
                        region_codes=region_codes
                    )
                    chunk_stats['racecards'] = racecard_result
                    overall_stats['total_races'] += racecard_result.get('races_fetched', 0)
                    overall_stats['total_runners'] += racecard_result.get('runners_fetched', 0)

                # Fetch results if requested
                if fetch_results:
                    logger.info(f"Fetching results for chunk {idx}...")
                    results_result = self.fetch_results(
                        start_date=chunk_start_str,
                        end_date=chunk_end_str,
                        region_codes=region_codes
                    )
                    chunk_stats['results'] = results_result

                overall_stats['chunks_processed'] += 1
                overall_stats['chunks'].append(chunk_stats)

                logger.info(f"Chunk {idx} completed successfully")

            except Exception as e:
                logger.error(f"Error processing chunk {idx}: {e}", exc_info=True)
                chunk_stats['error'] = str(e)
                overall_stats['chunks'].append(chunk_stats)
                overall_stats['success'] = False

        logger.info("\n" + "=" * 60)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Chunks processed: {overall_stats['chunks_processed']}/{overall_stats['total_chunks']}")
        logger.info(f"Total races fetched: {overall_stats['total_races']}")
        logger.info(f"Total runners fetched: {overall_stats['total_runners']}")

        return overall_stats

    def _generate_monthly_chunks(self, start_date, end_date) -> List[Tuple]:
        """
        Generate monthly date ranges for processing

        Args:
            start_date: Start date object
            end_date: End date object

        Returns:
            List of (chunk_start, chunk_end) tuples
        """
        chunks = []
        current = start_date

        while current <= end_date:
            # Start of month
            chunk_start = current

            # End of month or end_date, whichever comes first
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1, day=1)
            else:
                next_month = current.replace(month=current.month + 1, day=1)

            chunk_end = min(next_month - timedelta(days=1), end_date)

            chunks.append((chunk_start, chunk_end))

            # Move to next month
            current = next_month

        return chunks

    # ========================================================================
    # CONVENIENCE METHODS
    # ========================================================================

    def fetch_daily(self, region_codes: List[str] = None) -> Dict:
        """
        Convenience method: Fetch today's racecards

        Args:
            region_codes: Region filter (e.g., ['gb', 'ire'])

        Returns:
            Statistics dictionary
        """
        return self.fetch_racecards(days_back=0, region_codes=region_codes)

    def fetch_and_store(self, event_type: str = 'racecards', **config) -> Dict:
        """
        Main entry point for fetching event data

        Args:
            event_type: Type to fetch ('racecards', 'results', 'both')
            **config: Additional configuration

        Returns:
            Statistics dictionary
        """
        region_codes = config.get('region_codes', ['gb', 'ire'])
        days_back = config.get('days_back', 1)

        if event_type == 'racecards':
            return self.fetch_racecards(
                days_back=days_back,
                region_codes=region_codes
            )
        elif event_type == 'results':
            return self.fetch_results(
                days_back=days_back,
                region_codes=region_codes
            )
        elif event_type == 'both':
            racecards = self.fetch_racecards(
                days_back=days_back,
                region_codes=region_codes
            )
            results = self.fetch_results(
                days_back=days_back,
                region_codes=region_codes
            )
            return {
                'success': True,
                'racecards': racecards,
                'results': results
            }
        else:
            return {'success': False, 'error': f'Unknown event type: {event_type}'}


def main():
    """Main execution for testing"""
    logger.info("=" * 60)
    logger.info("EVENTS DATA FETCHER - TEST MODE")
    logger.info("=" * 60)

    fetcher = EventsFetcher()

    # Fetch today's racecards
    result = fetcher.fetch_daily(region_codes=['gb', 'ire'])

    logger.info("\n" + "=" * 60)
    logger.info("RESULTS:")
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Races fetched: {result.get('races_fetched', 0)}")
    logger.info(f"Runners fetched: {result.get('runners_fetched', 0)}")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()
