"""
Backfill Race Ratings Script
Re-fetches race results to update missing or incomplete ratings data in ra_runners table
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import time
from datetime import datetime, timedelta
from typing import Dict, List
from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.position_parser import parse_rating

logger = get_logger('backfill_race_ratings')


class RaceRatingsBackfill:
    """Backfill ratings data for runners in database"""

    def __init__(self):
        """Initialize backfill"""
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

    def get_races_needing_ratings(self, days_back: int = 365) -> List[str]:
        """
        Get list of race IDs where runners are missing ratings

        Args:
            days_back: How many days back to look (default: 365 = 1 year)

        Returns:
            List of race IDs
        """
        logger.info(f"Finding races from last {days_back} days with missing ratings...")

        cutoff_date = (datetime.utcnow() - timedelta(days=days_back)).date()

        # Query races where runners have NULL ratings
        # Note: We can't do complex joins in Supabase client, so we'll get all races
        # in the date range and then check their runners
        try:
            # Get all races in date range
            result = self.db_client.client.table('ra_races').select('race_id, race_date').gte('race_date', cutoff_date.isoformat()).execute()

            all_race_ids = [row['race_id'] for row in result.data]
            logger.info(f"Found {len(all_race_ids)} total races in date range")

            # For each race, check if it has runners with missing ratings
            races_needing_update = []

            logger.info("Checking which races have runners with missing ratings...")
            for i, race_id in enumerate(all_race_ids, 1):
                if i % 1000 == 0:
                    logger.info(f"Checked {i}/{len(all_race_ids)} races...")

                # Get runners for this race with NULL ratings
                runners_result = self.db_client.client.table('ra_runners').select('runner_id').eq('race_id', race_id).is_('official_rating', 'null').is_('rpr', 'null').is_('tsr', 'null').limit(1).execute()

                # If this race has any runners with ALL ratings NULL, add to list
                if runners_result.data:
                    races_needing_update.append(race_id)

            logger.info(f"Found {len(races_needing_update)} races with missing ratings data")
            return races_needing_update

        except Exception as e:
            logger.error(f"Error finding races needing ratings: {e}")
            raise

    def fetch_and_update_race(self, race_id: str) -> Dict:
        """
        Fetch race from API and update runners' ratings

        Args:
            race_id: Race ID to fetch

        Returns:
            Update statistics
        """
        try:
            # Fetch race from results API
            # Note: The results endpoint returns detailed race info with ratings
            # We'll need to parse the race_id to get the date
            # Race IDs are typically in format: rac_XXXXXXXX
            # We'll fetch by race_id directly if the API supports it

            # First, get the race date from database
            race_result = self.db_client.client.table('ra_races').select('race_date').eq('race_id', race_id).limit(1).execute()

            if not race_result.data:
                logger.warning(f"Race {race_id} not found in database")
                return {'success': False, 'error': 'Race not in database'}

            race_date = race_result.data[0]['race_date']

            # Fetch results for this date (will include multiple races)
            api_response = self.api_client.get_results(date=race_date)

            if not api_response or 'results' not in api_response:
                logger.warning(f"No results from API for date {race_date}")
                return {'success': False, 'error': 'No API response'}

            # Find this specific race in the results
            results = api_response.get('results', [])
            target_race = None
            for result in results:
                if result.get('race_id') == race_id:
                    target_race = result
                    break

            if not target_race:
                logger.warning(f"Race {race_id} not found in API results for {race_date}")
                return {'success': False, 'error': 'Race not in API response'}

            # Extract runners from race
            runners = target_race.get('runners', [])

            if not runners:
                logger.warning(f"No runners in race {race_id}")
                return {'success': False, 'error': 'No runners'}

            # Update each runner's ratings in database
            updated_count = 0
            for runner in runners:
                horse_id = runner.get('horse_id')
                if not horse_id:
                    continue

                runner_id = f"{race_id}_{horse_id}"

                # Extract ratings
                official_rating = parse_rating(runner.get('or'))
                rpr = parse_rating(runner.get('rpr'))
                tsr = parse_rating(runner.get('tsr'))

                # Update only if we have at least one rating
                if official_rating or rpr or tsr:
                    update_data = {
                        'official_rating': official_rating,
                        'rpr': rpr,
                        'tsr': tsr,
                        'updated_at': datetime.utcnow().isoformat()
                    }

                    try:
                        self.db_client.client.table('ra_runners').update(update_data).eq('runner_id', runner_id).execute()
                        updated_count += 1
                    except Exception as e:
                        logger.warning(f"Error updating runner {runner_id}: {e}")

            return {
                'success': True,
                'runners_updated': updated_count,
                'total_runners': len(runners)
            }

        except Exception as e:
            logger.error(f"Error fetching/updating race {race_id}: {e}")
            return {'success': False, 'error': str(e)}

    def run(self, days_back: int = 365, max_races: int = None, test_mode: bool = False) -> Dict:
        """
        Run backfill process

        Args:
            days_back: How many days back to look (default: 365)
            max_races: Maximum number of races to process (None = all)
            test_mode: If True, process only 10 races

        Returns:
            Statistics dictionary
        """
        logger.info("=" * 80)
        logger.info("RACE RATINGS BACKFILL")
        logger.info("=" * 80)

        if test_mode:
            logger.info("TEST MODE: Processing only 10 races")
            max_races = 10

        # Get races needing ratings update
        race_ids = self.get_races_needing_ratings(days_back=days_back)

        if not race_ids:
            logger.info("No races need ratings update!")
            return {'success': True, 'races_processed': 0}

        # Apply limit if specified
        if max_races:
            logger.info(f"Limiting to {max_races} races")
            race_ids = race_ids[:max_races]

        total_races = len(race_ids)
        logger.info(f"Processing {total_races} races")

        # Calculate estimated time (2 req/sec = 0.5s per race + processing)
        estimated_seconds = total_races * 0.6  # 0.5s rate limit + 0.1s processing
        estimated_minutes = estimated_seconds / 60
        logger.info(f"Estimated time: {estimated_minutes:.1f} minutes")

        # Confirm before starting
        if not test_mode:
            response = input(f"\nReady to process {total_races} races (est. {estimated_minutes:.1f} minutes)? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Backfill cancelled by user")
                return {'success': False, 'cancelled': True}

        # Process races
        stats = {
            'total': total_races,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'runners_updated': 0,
            'start_time': datetime.utcnow()
        }

        logger.info("\nStarting backfill...")
        logger.info("Progress will be reported every 10 races")

        for idx, race_id in enumerate(race_ids, 1):
            # Process race
            result = self.fetch_and_update_race(race_id)

            # Update stats
            stats['processed'] += 1
            if result.get('success'):
                stats['successful'] += 1
                stats['runners_updated'] += result.get('runners_updated', 0)
            else:
                stats['failed'] += 1

            # Progress logging every 10 races
            if idx % 10 == 0 or idx == total_races:
                elapsed = (datetime.utcnow() - stats['start_time']).total_seconds()
                rate = idx / elapsed if elapsed > 0 else 0
                remaining = (total_races - idx) / rate if rate > 0 else 0
                remaining_minutes = remaining / 60

                logger.info(f"Progress: {idx}/{total_races} ({idx/total_races*100:.1f}%) | "
                          f"Successful: {stats['successful']} | "
                          f"Failed: {stats['failed']} | "
                          f"Runners updated: {stats['runners_updated']} | "
                          f"Rate: {rate:.1f}/sec | "
                          f"ETA: {remaining_minutes:.1f}min")

            # Rate limiting (2 requests per second)
            time.sleep(0.5)

        # Final statistics
        stats['end_time'] = datetime.utcnow()
        stats['duration_seconds'] = (stats['end_time'] - stats['start_time']).total_seconds()
        stats['duration_minutes'] = stats['duration_seconds'] / 60

        logger.info("\n" + "=" * 80)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Total processed: {stats['processed']}")
        logger.info(f"Successful: {stats['successful']} ({stats['successful']/stats['processed']*100:.1f}%)")
        logger.info(f"Failed: {stats['failed']} ({stats['failed']/stats['processed']*100:.1f}%)")
        logger.info(f"Runners updated: {stats['runners_updated']}")
        logger.info(f"Duration: {stats['duration_minutes']:.2f} minutes")
        logger.info("=" * 80)

        return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill race ratings data')
    parser.add_argument('--days-back', type=int, default=365, help='Number of days to look back (default: 365)')
    parser.add_argument('--max', type=int, help='Maximum number of races to process')
    parser.add_argument('--test', action='store_true', help='Test mode: process only 10 races')

    args = parser.parse_args()

    backfill = RaceRatingsBackfill()

    result = backfill.run(
        days_back=args.days_back,
        max_races=args.max,
        test_mode=args.test
    )

    return result


if __name__ == '__main__':
    main()
