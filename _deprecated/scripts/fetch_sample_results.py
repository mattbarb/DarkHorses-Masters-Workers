#!/usr/bin/env python3
"""
Fetch Sample Results with Position Data
========================================
Fetches a small sample of results (last 7 days) to populate position data for testing.
This is faster than fetching a full year of data.
"""

import os
import sys
import logging
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

# Add parent to path
sys.path.append(str(Path(__file__).parent))

from config.config import get_config
from fetchers.results_fetcher import ResultsFetcher
from utils.supabase_client import SupabaseReferenceClient

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_sample_results(days_back: int = 7):
    """
    Fetch sample results for testing position data extraction

    Args:
        days_back: Number of days back to fetch (default: 7)
    """
    print("=" * 80)
    print("SAMPLE RESULTS FETCHER - Position Data Test")
    print("=" * 80)
    print(f"\nFetching last {days_back} days of results...")
    print("This will populate position data for ML compilation testing.\n")

    # Initialize fetcher (gets config automatically)
    results_fetcher = ResultsFetcher()

    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    print(f"Date range: {start_date.date()} to {end_date.date()}")
    print(f"Regions: GB, IRE\n")

    # Fetch results
    try:
        results_fetcher.fetch_and_store(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            region_codes=['gb', 'ire']
        )

        print("\n" + "=" * 80)
        print("✓ Sample results fetch complete!")
        print("=" * 80)

        # Verify position data
        print("\nVerifying position data...")
        total = results_fetcher.db_client.client.table('ra_runners').select('runner_id', count='exact').execute()
        with_position = results_fetcher.db_client.client.table('ra_runners').select('runner_id', count='exact').not_.is_('position', 'null').execute()

        print(f"\nTotal runners: {total.count}")
        print(f"With position data: {with_position.count}")
        if total.count > 0:
            pct = (with_position.count / total.count) * 100
            print(f"Coverage: {pct:.1f}%")

        # Show sample
        if with_position.count > 0:
            print("\nSample runners with position data:")
            sample = results_fetcher.db_client.client.table('ra_runners').select(
                'horse_name, position, distance_beaten, prize_won, starting_price'
            ).not_.is_('position', 'null').limit(5).execute()

            for r in sample.data:
                print(f"  {r['horse_name']}: "
                      f"pos={r['position']}, "
                      f"beaten={r.get('distance_beaten', 'N/A')}, "
                      f"prize=£{r.get('prize_won', 0):.2f}, "
                      f"sp={r.get('starting_price', 'N/A')}")

        print("\n" + "=" * 80)

    except Exception as e:
        logger.error(f"Error fetching sample results: {e}")
        print("\n" + "=" * 80)
        print("✗ Sample results fetch failed!")
        print("=" * 80)
        sys.exit(1)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Fetch sample results with position data')
    parser.add_argument('--days-back', type=int, default=7,
                       help='Number of days back to fetch (default: 7)')

    args = parser.parse_args()

    fetch_sample_results(days_back=args.days_back)
