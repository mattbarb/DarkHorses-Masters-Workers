#!/usr/bin/env python3
"""
Backfill starting_price_decimal for Historical Results
Fetches results from 2015 to present and populates starting_price_decimal field

This script re-fetches historical results to populate the starting_price_decimal field
which was missing from the position_parser.py extract_position_data() function.

Target: ~162K runners with position data but NULL starting_price_decimal
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient
from fetchers.results_fetcher import ResultsFetcher

logger = get_logger('backfill_sp_decimal')


def check_current_coverage():
    """Check current coverage of starting_price_decimal field"""
    logger.info("Checking current starting_price_decimal coverage...")

    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

    # Total runners
    total = db.client.from_('ra_mst_runners').select('id', count='exact').execute().count

    # Runners with position data (completed races)
    with_position = db.client.from_('ra_mst_runners').select('id', count='exact')\
        .not_.is_('position', 'null').execute().count

    # Runners with starting_price_decimal
    with_sp_dec = db.client.from_('ra_mst_runners').select('id', count='exact')\
        .not_.is_('starting_price_decimal', 'null').execute().count

    logger.info(f"Total runners: {total:,}")
    logger.info(f"Runners with position: {with_position:,} ({with_position/total*100:.2f}%)")
    logger.info(f"Runners with starting_price_decimal: {with_sp_dec:,} ({with_sp_dec/total*100:.2f}%)")

    gap = with_position - with_sp_dec
    logger.info(f"Gap to fill: {gap:,} runners")

    return gap


def backfill_year(year: int, fetcher: ResultsFetcher) -> dict:
    """Backfill results for a specific year"""
    logger.info(f"\n{'=' * 80}")
    logger.info(f"BACKFILLING YEAR: {year}")
    logger.info(f"{'=' * 80}")

    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"

    logger.info(f"Date range: {start_date} to {end_date}")

    result = fetcher.fetch_and_store(
        start_date=start_date,
        end_date=end_date,
        region_codes=['gb', 'ire']
    )

    logger.info(f"Year {year} results:")
    logger.info(f"  Success: {result.get('success')}")
    logger.info(f"  Races fetched: {result.get('fetched', 0):,}")
    logger.info(f"  Days with data: {result.get('days_with_data', 0)}")

    db_stats = result.get('db_stats', {})
    runners_updated = db_stats.get('runners', {}).get('updated', 0)
    logger.info(f"  Runners updated: {runners_updated:,}")

    return result


def main():
    """Main backfill execution"""
    logger.info("=" * 80)
    logger.info("STARTING STARTING_PRICE_DECIMAL BACKFILL")
    logger.info(f"Started at: {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)

    # Check current coverage
    gap = check_current_coverage()

    if gap == 0:
        logger.info("\n✓ No gap to fill! All runners with positions have starting_price_decimal")
        return

    logger.info(f"\nWill backfill {gap:,} runners with missing starting_price_decimal")
    input("\nPress ENTER to continue or Ctrl+C to cancel...")

    # Initialize fetcher
    fetcher = ResultsFetcher()

    # Backfill from 2015 to current year
    current_year = datetime.utcnow().year
    start_year = 2015

    logger.info(f"\nBackfilling results from {start_year} to {current_year}...")

    total_races = 0
    total_runners = 0

    for year in range(start_year, current_year + 1):
        try:
            result = backfill_year(year, fetcher)

            if result.get('success'):
                total_races += result.get('fetched', 0)
                db_stats = result.get('db_stats', {})
                total_runners += db_stats.get('runners', {}).get('updated', 0)
            else:
                logger.error(f"Failed to backfill year {year}")

        except Exception as e:
            logger.error(f"Error backfilling year {year}: {e}", exc_info=True)
            continue

    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total races processed: {total_races:,}")
    logger.info(f"Total runners updated: {total_runners:,}")

    # Final coverage check
    logger.info("\nFinal coverage check:")
    check_current_coverage()

    logger.info(f"\nCompleted at: {datetime.utcnow().isoformat()}")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n\nBackfill cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
