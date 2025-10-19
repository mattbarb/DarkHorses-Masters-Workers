#!/usr/bin/env python3
"""
Test script for hybrid horses_fetcher.py
Tests Pro enrichment with small batch
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from fetchers.horses_fetcher import HorsesFetcher
from utils.logger import get_logger

logger = get_logger('test_hybrid_horses_fetcher')

def main():
    """Test hybrid horses fetcher with small batch"""
    logger.info("=" * 60)
    logger.info("TESTING HYBRID HORSES FETCHER")
    logger.info("=" * 60)

    fetcher = HorsesFetcher()

    # Test with just 1 page (500 horses)
    # This should identify new horses and enrich them with Pro data
    logger.info("Fetching 1 page (500 horses) to test hybrid approach...")

    result = fetcher.fetch_and_store(
        limit_per_page=500,
        max_pages=1,  # Only 1 page for testing
        filter_uk_ireland=True
    )

    logger.info("\n" + "=" * 60)
    logger.info("TEST RESULTS")
    logger.info("=" * 60)
    logger.info(f"Success: {result.get('success')}")
    logger.info(f"\nFetch Statistics:")
    logger.info(f"  Total fetched: {result.get('fetched', 0)} horses")
    logger.info(f"  New horses: {result.get('new_horses', 0)}")
    logger.info(f"  Existing horses: {result.get('existing_horses', 0)}")

    logger.info(f"\nDatabase Statistics:")
    logger.info(f"  Horses inserted/updated: {result.get('horses_inserted', 0)}")
    logger.info(f"  Pedigrees inserted: {result.get('pedigrees_inserted', 0)}")

    pro_stats = result.get('pro_enrichment', {})
    logger.info(f"\nPro Enrichment Statistics:")
    logger.info(f"  Successfully enriched: {pro_stats.get('success', 0)}")
    logger.info(f"  Failed enrichments: {pro_stats.get('failed', 0)}")
    logger.info(f"  Pedigrees captured: {pro_stats.get('pedigrees_captured', 0)}")

    if result.get('new_horses', 0) > 0:
        success_rate = (pro_stats.get('success', 0) / result.get('new_horses', 0) * 100)
        pedigree_rate = (pro_stats.get('pedigrees_captured', 0) / result.get('new_horses', 0) * 100)
        logger.info(f"  Success rate: {success_rate:.1f}%")
        logger.info(f"  Pedigree capture rate: {pedigree_rate:.1f}%")
    else:
        logger.info("  No new horses found (all existing)")

    logger.info("\n" + "=" * 60)
    logger.info("TEST COMPLETE")
    logger.info("=" * 60)

    return result


if __name__ == '__main__':
    result = main()
    sys.exit(0 if result.get('success') else 1)
