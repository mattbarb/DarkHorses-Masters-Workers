"""
Backfill Master/Reference Data

This script ensures all master reference tables (ra_mst_*) have complete data:
- ra_mst_bookmakers (static list of UK/Irish bookmakers)
- ra_mst_courses (venues from Racing API)
- ra_mst_regions (static list: GB, IRE)

Note: People and horses (jockeys, trainers, owners, horses, pedigree) are populated
via entity extraction from event data, not through this script.

Usage:
    python3 scripts/backfill_masters.py
    python3 scripts/backfill_masters.py --region-codes gb ire
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
from datetime import datetime
from utils.logger import get_logger
from fetchers.masters_fetcher import MastersFetcher

logger = get_logger('backfill_masters')


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(description='Backfill master/reference data')
    parser.add_argument(
        '--region-codes',
        nargs='+',
        default=['gb', 'ire'],
        help='Region codes to fetch (default: gb ire)'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("MASTER DATA BACKFILL")
    logger.info("=" * 80)
    logger.info(f"Region codes: {args.region_codes}")
    logger.info(f"Started at: {datetime.utcnow().isoformat()}")

    start_time = datetime.utcnow()

    # Initialize fetcher
    fetcher = MastersFetcher()

    # Run backfill
    result = fetcher.backfill(region_codes=args.region_codes)

    # Calculate duration
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    # Log results
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info("")
    logger.info("Results by table:")
    logger.info(f"  Bookmakers: {result.get('bookmakers', {}).get('inserted', 0)} records")
    logger.info(f"  Courses: {result.get('courses', {}).get('inserted', 0)} records")
    logger.info(f"  Regions: {result.get('regions', {}).get('inserted', 0)} records")
    logger.info(f"  Total: {result.get('total_inserted', 0)} records")
    logger.info("")
    logger.info("Note: People and horses are populated via entity extraction from events")
    logger.info("=" * 80)

    return 0 if result.get('success') else 1


if __name__ == '__main__':
    sys.exit(main())
