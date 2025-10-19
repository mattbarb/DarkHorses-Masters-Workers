#!/usr/bin/env python3
"""
Test Results Fetcher Hybrid Enrichment
========================================
Verifies that results_fetcher.py correctly passes api_client to EntityExtractor
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from fetchers.results_fetcher import ResultsFetcher
from utils.logger import get_logger

logger = get_logger('test_results_enrichment')


def test_results_fetcher_initialization():
    """Test that ResultsFetcher initializes EntityExtractor with api_client"""
    print("=" * 80)
    print("TESTING RESULTS FETCHER HYBRID ENRICHMENT")
    print("=" * 80)

    try:
        # Initialize fetcher
        logger.info("Initializing ResultsFetcher...")
        fetcher = ResultsFetcher()

        # Verify components exist
        assert fetcher.api_client is not None, "API client not initialized"
        assert fetcher.db_client is not None, "DB client not initialized"
        assert fetcher.entity_extractor is not None, "Entity extractor not initialized"

        # Verify entity extractor has api_client
        assert fetcher.entity_extractor.api_client is not None, \
            "EntityExtractor missing api_client - hybrid enrichment will NOT work!"

        # Verify it's the same api_client instance
        assert fetcher.entity_extractor.api_client is fetcher.api_client, \
            "EntityExtractor has different api_client instance"

        print("\n✅ SUCCESS - All checks passed!")
        print("\nVerified:")
        print("  ✓ ResultsFetcher initialized correctly")
        print("  ✓ API client exists and is valid")
        print("  ✓ DB client exists and is valid")
        print("  ✓ EntityExtractor exists and is valid")
        print("  ✓ EntityExtractor has api_client reference")
        print("  ✓ EntityExtractor.api_client is same instance as fetcher.api_client")
        print("\n🎉 Hybrid enrichment is properly configured!")
        print("=" * 80)

        return True

    except AssertionError as e:
        print(f"\n❌ FAILURE - {e}")
        print("=" * 80)
        return False

    except Exception as e:
        print(f"\n❌ ERROR - {e}")
        import traceback
        traceback.print_exc()
        print("=" * 80)
        return False


if __name__ == '__main__':
    success = test_results_fetcher_initialization()
    sys.exit(0 if success else 1)
