#!/usr/bin/env python3
"""
Test ra_results Table Population
=================================

Tests that the new ra_results table is populated correctly when fetching results.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.append(str(Path(__file__).parent.parent))

from fetchers.results_fetcher import ResultsFetcher
from utils.logger import get_logger

logger = get_logger('test_results_table')


def test_results_table():
    """Test results table population"""
    logger.info("=" * 80)
    logger.info("TESTING RA_RESULTS TABLE POPULATION")
    logger.info("=" * 80)

    # Fetch last 3 days of results (small test)
    fetcher = ResultsFetcher()

    logger.info("\nFetching last 3 days of results...")
    result = fetcher.fetch_and_store(
        days_back=3,
        region_codes=['gb', 'ire']
    )

    logger.info("\n" + "=" * 80)
    logger.info("FETCH RESULTS")
    logger.info("=" * 80)
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"Total results fetched: {result.get('fetched', 0)}")
    logger.info(f"Days fetched: {result.get('days_fetched', 0)}")
    logger.info(f"Days with data: {result.get('days_with_data', 0)}")

    # Check database stats
    db_stats = result.get('db_stats', {})
    logger.info("\n" + "-" * 80)
    logger.info("DATABASE INSERTION STATS")
    logger.info("-" * 80)

    if 'races' in db_stats:
        logger.info(f"Races inserted: {db_stats['races']}")

    if 'results' in db_stats:
        logger.info(f"Results inserted: {db_stats['results']} ⭐ NEW TABLE")
    else:
        logger.warning("⚠️  No 'results' key in db_stats - table may not be populated")

    if 'runners' in db_stats:
        logger.info(f"Runners inserted: {db_stats['runners']}")

    logger.info("\n" + "=" * 80)
    logger.info("NEXT STEPS")
    logger.info("=" * 80)
    logger.info("Verify data in Supabase with these queries:")
    logger.info("")
    logger.info("1. Check results count:")
    logger.info("   SELECT COUNT(*) FROM ra_results;")
    logger.info("")
    logger.info("2. See sample results:")
    logger.info("   SELECT race_id, course_name, tote_win, tote_ex, comments")
    logger.info("   FROM ra_results")
    logger.info("   LIMIT 10;")
    logger.info("")
    logger.info("3. Check tote data coverage:")
    logger.info("   SELECT")
    logger.info("     COUNT(*) as total,")
    logger.info("     COUNT(tote_win) as with_tote,")
    logger.info("     ROUND(100.0 * COUNT(tote_win) / COUNT(*), 2) as coverage_pct")
    logger.info("   FROM ra_results;")
    logger.info("=" * 80)

    return result


if __name__ == '__main__':
    result = test_results_table()
    sys.exit(0 if result.get('success') else 1)
