"""
Jockeys Statistics Worker

Populates statistics fields in ra_jockeys table:
- last_ride_date, last_win_date
- days_since_last_ride, days_since_last_win
- recent_14d_rides, recent_14d_wins, recent_14d_win_rate
- recent_30d_rides, recent_30d_wins, recent_30d_win_rate

Uses Racing API results endpoints to calculate statistics from last 365 days of data.

Usage:
    python3 scripts/statistics_workers/jockeys_statistics_worker.py
    python3 scripts/statistics_workers/jockeys_statistics_worker.py --limit 10
"""

import sys
import os
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_jockey_statistics(jockey_id: str, jockey_name: str, api_client: RacingAPIClient) -> Optional[Dict]:
    """
    Calculate statistics for a single jockey

    Args:
        jockey_id: Jockey ID
        jockey_name: Jockey name (for logging)
        api_client: Racing API client

    Returns:
        Dictionary with calculated statistics or None on error
    """
    try:
        # Fetch last year of results
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')

        logger.debug(f"Fetching results for {jockey_name} ({jockey_id}) from {start_date} to {end_date}")

        # Fetch all results (pagination)
        all_results = []
        skip = 0
        limit = 50

        while True:
            results = api_client.get_jockey_results(
                jockey_id=jockey_id,
                start_date=start_date,
                end_date=end_date,
                region=['gb', 'ire'],
                limit=limit,
                skip=skip
            )

            if not results or 'results' not in results or not results['results']:
                break

            all_results.extend(results['results'])

            if len(results['results']) < limit:
                break

            skip += limit

        logger.debug(f"Fetched {len(all_results)} results for {jockey_name}")

        # Initialize statistics
        stats = {
            'last_ride_date': None,
            'last_win_date': None,
            'days_since_last_ride': None,
            'days_since_last_win': None,
            'recent_14d_rides': 0,
            'recent_14d_wins': 0,
            'recent_14d_win_rate': None,
            'recent_30d_rides': 0,
            'recent_30d_wins': 0,
            'recent_30d_win_rate': None,
            'stats_updated_at': datetime.utcnow().isoformat()
        }

        now = datetime.utcnow()
        fourteen_days_ago = now - timedelta(days=14)
        thirty_days_ago = now - timedelta(days=30)

        # Process results
        for race in all_results:
            runners = race.get('runners', [])
            race_date = datetime.strptime(race.get('date'), '%Y-%m-%d')

            # Find this jockey's runner
            jockey_runner = None
            for runner in runners:
                if runner.get('jockey_id') == jockey_id:
                    jockey_runner = runner
                    break

            if jockey_runner:
                # Track last ride date
                if stats['last_ride_date'] is None or race_date > stats['last_ride_date']:
                    stats['last_ride_date'] = race_date

                # Count recent form
                if race_date >= fourteen_days_ago:
                    stats['recent_14d_rides'] += 1
                if race_date >= thirty_days_ago:
                    stats['recent_30d_rides'] += 1

                position = jockey_runner.get('position')

                # Handle position (could be "1", 1, "WON", etc.)
                if position:
                    position_str = str(position).strip()

                    if position_str in ['1', 'WON']:
                        # Track last win date
                        if stats['last_win_date'] is None or race_date > stats['last_win_date']:
                            stats['last_win_date'] = race_date

                        # Count recent wins
                        if race_date >= fourteen_days_ago:
                            stats['recent_14d_wins'] += 1
                        if race_date >= thirty_days_ago:
                            stats['recent_30d_wins'] += 1

        # Calculate recent form rates
        if stats['recent_14d_rides'] > 0:
            stats['recent_14d_win_rate'] = round((stats['recent_14d_wins'] / stats['recent_14d_rides']) * 100, 2)
        if stats['recent_30d_rides'] > 0:
            stats['recent_30d_win_rate'] = round((stats['recent_30d_wins'] / stats['recent_30d_rides']) * 100, 2)

        # Calculate days since last ride/win
        if stats['last_ride_date']:
            stats['days_since_last_ride'] = (now - stats['last_ride_date']).days
            stats['last_ride_date'] = stats['last_ride_date'].strftime('%Y-%m-%d')

        if stats['last_win_date']:
            stats['days_since_last_win'] = (now - stats['last_win_date']).days
            stats['last_win_date'] = stats['last_win_date'].strftime('%Y-%m-%d')

        return stats

    except Exception as e:
        logger.error(f"Error calculating statistics for {jockey_name} ({jockey_id}): {e}")
        return None


def process_jockeys_batch(jockeys: List[Dict], api_client: RacingAPIClient, db_client: SupabaseReferenceClient) -> Dict:
    """
    Process a batch of jockeys

    Args:
        jockeys: List of jockey records
        api_client: Racing API client
        db_client: Supabase client

    Returns:
        Statistics dictionary
    """
    batch_stats = {
        'processed': 0,
        'updated': 0,
        'errors': 0,
        'skipped': 0
    }

    updates = []

    for jockey in jockeys:
        jockey_id = jockey['id']
        jockey_name = jockey.get('name', 'Unknown')

        logger.info(f"Processing {jockey_name} ({jockey_id})...")

        # Calculate statistics
        stats = calculate_jockey_statistics(jockey_id, jockey_name, api_client)

        if stats:
            # Add jockey ID to update record
            stats['id'] = jockey_id
            updates.append(stats)
            batch_stats['processed'] += 1
        else:
            batch_stats['errors'] += 1

    # Batch update database using UPDATE (not UPSERT)
    # We only want to update statistics for existing jockeys, not insert new ones
    if updates:
        try:
            for update in updates:
                jockey_id = update.pop('id')  # Remove id from update data
                result = db_client.client.table('ra_jockeys').update(update).eq('id', jockey_id).execute()
                if result.data:
                    batch_stats['updated'] += 1
            logger.info(f"Updated {batch_stats['updated']} jockeys in database")
        except Exception as e:
            logger.error(f"Error updating jockeys batch: {e}")
            batch_stats['errors'] += len(updates)

    return batch_stats


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Calculate and update jockey statistics')
    parser.add_argument('--limit', type=int, help='Limit number of jockeys to process (for testing)')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("JOCKEYS STATISTICS WORKER")
    logger.info("=" * 80)

    # Initialize clients
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password
    )
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Fetch jockeys (excluding test data)
    logger.info("Fetching jockeys from database...")
    try:
        query = db_client.client.table('ra_jockeys').select('id, name').not_.like('id', '**TEST**%')

        if args.limit:
            query = query.limit(args.limit)
            logger.info(f"Limiting to {args.limit} jockeys for testing")

        response = query.execute()
        jockeys = response.data

        if not jockeys:
            logger.warning("No jockeys found in database")
            return

        logger.info(f"Found {len(jockeys)} jockeys to process")

    except Exception as e:
        logger.error(f"Error fetching jockeys: {e}")
        return

    # Process in batches
    batch_size = 100
    total_stats = {
        'processed': 0,
        'updated': 0,
        'errors': 0,
        'skipped': 0
    }

    start_time = datetime.utcnow()

    for i in range(0, len(jockeys), batch_size):
        batch = jockeys[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(jockeys) + batch_size - 1) // batch_size

        logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} jockeys)...")

        batch_stats = process_jockeys_batch(batch, api_client, db_client)

        # Accumulate stats
        for key in total_stats:
            total_stats[key] += batch_stats[key]

        logger.info(f"Batch {batch_num} complete: {batch_stats['updated']} updated, {batch_stats['errors']} errors")

    # Final summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("JOCKEYS STATISTICS WORKER COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total jockeys: {len(jockeys)}")
    logger.info(f"Processed: {total_stats['processed']}")
    logger.info(f"Updated: {total_stats['updated']}")
    logger.info(f"Errors: {total_stats['errors']}")
    logger.info(f"Duration: {duration:.2f}s")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
