"""
Owners Statistics Worker

Populates statistics fields in ra_owners table:
- last_runner_date, last_win_date
- days_since_last_runner, days_since_last_win
- recent_14d_runs, recent_14d_wins, recent_14d_win_rate
- recent_30d_runs, recent_30d_wins, recent_30d_win_rate

Uses Racing API results endpoints to calculate statistics from last 365 days of data.

Usage:
    python3 scripts/statistics_workers/owners_statistics_worker.py
    python3 scripts/statistics_workers/owners_statistics_worker.py --limit 10
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


def calculate_owner_statistics(owner_id: str, owner_name: str, api_client: RacingAPIClient) -> Optional[Dict]:
    """
    Calculate statistics for a single owner

    Args:
        owner_id: Owner ID
        owner_name: Owner name (for logging)
        api_client: Racing API client

    Returns:
        Dictionary with calculated statistics or None on error
    """
    try:
        # Fetch last year of results
        end_date = datetime.utcnow().strftime('%Y-%m-%d')
        start_date = (datetime.utcnow() - timedelta(days=365)).strftime('%Y-%m-%d')

        logger.debug(f"Fetching results for {owner_name} ({owner_id}) from {start_date} to {end_date}")

        # Fetch all results (pagination)
        all_results = []
        skip = 0
        limit = 50

        while True:
            results = api_client.get_owner_results(
                owner_id=owner_id,
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

        logger.debug(f"Fetched {len(all_results)} results for {owner_name}")

        # Initialize statistics
        stats = {
            'last_runner_date': None,
            'last_win_date': None,
            'days_since_last_runner': None,
            'days_since_last_win': None,
            'recent_14d_runs': 0,
            'recent_14d_wins': 0,
            'recent_14d_win_rate': None,
            'recent_30d_runs': 0,
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

            # Find this owner's runners
            owner_runners = [r for r in runners if r.get('owner_id') == owner_id]

            for runner in owner_runners:
                # Track last runner date
                if stats['last_runner_date'] is None or race_date > stats['last_runner_date']:
                    stats['last_runner_date'] = race_date

                # Count recent form
                if race_date >= fourteen_days_ago:
                    stats['recent_14d_runs'] += 1
                if race_date >= thirty_days_ago:
                    stats['recent_30d_runs'] += 1

                position = runner.get('position')

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
        if stats['recent_14d_runs'] > 0:
            stats['recent_14d_win_rate'] = round((stats['recent_14d_wins'] / stats['recent_14d_runs']) * 100, 2)
        if stats['recent_30d_runs'] > 0:
            stats['recent_30d_win_rate'] = round((stats['recent_30d_wins'] / stats['recent_30d_runs']) * 100, 2)

        # Calculate days since last runner/win
        if stats['last_runner_date']:
            stats['days_since_last_runner'] = (now - stats['last_runner_date']).days
            stats['last_runner_date'] = stats['last_runner_date'].strftime('%Y-%m-%d')

        if stats['last_win_date']:
            stats['days_since_last_win'] = (now - stats['last_win_date']).days
            stats['last_win_date'] = stats['last_win_date'].strftime('%Y-%m-%d')

        return stats

    except Exception as e:
        logger.error(f"Error calculating statistics for {owner_name} ({owner_id}): {e}")
        return None


def process_owners_batch(owners: List[Dict], api_client: RacingAPIClient, db_client: SupabaseReferenceClient) -> Dict:
    """
    Process a batch of owners

    Args:
        owners: List of owner records
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

    for owner in owners:
        owner_id = owner['id']
        owner_name = owner.get('name', 'Unknown')

        logger.info(f"Processing {owner_name} ({owner_id})...")

        # Calculate statistics
        stats = calculate_owner_statistics(owner_id, owner_name, api_client)

        if stats:
            # Add owner ID to update record
            stats['id'] = owner_id
            updates.append(stats)
            batch_stats['processed'] += 1
        else:
            batch_stats['errors'] += 1

    # Batch update database using UPDATE (not UPSERT)
    # We only want to update statistics for existing owners, not insert new ones
    if updates:
        try:
            for update in updates:
                owner_id = update.pop('id')  # Remove id from update data
                result = db_client.client.table('ra_owners').update(update).eq('id', owner_id).execute()
                if result.data:
                    batch_stats['updated'] += 1
            logger.info(f"Updated {batch_stats['updated']} owners in database")
        except Exception as e:
            logger.error(f"Error updating owners batch: {e}")
            batch_stats['errors'] += len(updates)

    return batch_stats


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Calculate and update owner statistics')
    parser.add_argument('--limit', type=int, help='Limit number of owners to process (for testing)')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("OWNERS STATISTICS WORKER")
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

    # Fetch owners (excluding test data)
    logger.info("Fetching owners from database...")
    try:
        query = db_client.client.table('ra_owners').select('id, name').not_.like('id', '**TEST**%')

        if args.limit:
            query = query.limit(args.limit)
            logger.info(f"Limiting to {args.limit} owners for testing")

        response = query.execute()
        owners = response.data

        if not owners:
            logger.warning("No owners found in database")
            return

        logger.info(f"Found {len(owners)} owners to process")

    except Exception as e:
        logger.error(f"Error fetching owners: {e}")
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

    for i in range(0, len(owners), batch_size):
        batch = owners[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (len(owners) + batch_size - 1) // batch_size

        logger.info(f"\nProcessing batch {batch_num}/{total_batches} ({len(batch)} owners)...")

        batch_stats = process_owners_batch(batch, api_client, db_client)

        # Accumulate stats
        for key in total_stats:
            total_stats[key] += batch_stats[key]

        logger.info(f"Batch {batch_num} complete: {batch_stats['updated']} updated, {batch_stats['errors']} errors")

    # Final summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("OWNERS STATISTICS WORKER COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total owners: {len(owners)}")
    logger.info(f"Processed: {total_stats['processed']}")
    logger.info(f"Updated: {total_stats['updated']}")
    logger.info(f"Errors: {total_stats['errors']}")
    logger.info(f"Duration: {duration:.2f}s")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
