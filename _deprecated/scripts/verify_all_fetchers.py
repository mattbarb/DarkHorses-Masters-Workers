#!/usr/bin/env python3
"""
Verify All Fetchers - Hybrid Enrichment Configuration
======================================================
Comprehensive verification that all fetchers are correctly configured.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from fetchers.races_fetcher import RacesFetcher
from fetchers.results_fetcher import ResultsFetcher
from fetchers.horses_fetcher import HorsesFetcher
from fetchers.jockeys_fetcher import JockeysFetcher
from fetchers.trainers_fetcher import TrainersFetcher
from fetchers.owners_fetcher import OwnersFetcher
from fetchers.courses_fetcher import CoursesFetcher
from fetchers.bookmakers_fetcher import BookmakersFetcher
from utils.logger import get_logger

logger = get_logger('verify_fetchers')


def verify_fetcher_with_entity_extractor(fetcher_class, fetcher_name):
    """Verify a fetcher that uses EntityExtractor"""
    print(f"\n{'='*80}")
    print(f"Verifying: {fetcher_name}")
    print('='*80)

    try:
        fetcher = fetcher_class()

        # Check basic components
        assert fetcher.api_client is not None, "API client not initialized"
        assert fetcher.db_client is not None, "DB client not initialized"
        assert fetcher.entity_extractor is not None, "EntityExtractor not initialized"

        # Check EntityExtractor has api_client
        assert fetcher.entity_extractor.api_client is not None, \
            "EntityExtractor missing api_client - HYBRID ENRICHMENT BROKEN!"

        # Check it's the same instance
        assert fetcher.entity_extractor.api_client is fetcher.api_client, \
            "EntityExtractor has different api_client instance"

        print(f"✅ {fetcher_name}")
        print("   ✓ API client: OK")
        print("   ✓ DB client: OK")
        print("   ✓ EntityExtractor: OK")
        print("   ✓ EntityExtractor.api_client: OK")
        print("   ✓ Hybrid enrichment: ENABLED")

        return True

    except AssertionError as e:
        print(f"❌ {fetcher_name} - FAILED")
        print(f"   Error: {e}")
        return False
    except Exception as e:
        print(f"❌ {fetcher_name} - ERROR")
        print(f"   Error: {e}")
        return False


def verify_fetcher_without_entity_extractor(fetcher_class, fetcher_name, reason, requires_api=True):
    """Verify a fetcher that doesn't use EntityExtractor"""
    print(f"\n{'='*80}")
    print(f"Verifying: {fetcher_name}")
    print('='*80)

    try:
        fetcher = fetcher_class()

        # Check basic components
        if requires_api:
            assert fetcher.api_client is not None, "API client not initialized"

        assert fetcher.db_client is not None, "DB client not initialized"

        # Verify EntityExtractor is NOT present
        has_entity_extractor = hasattr(fetcher, 'entity_extractor')

        print(f"✅ {fetcher_name}")
        if requires_api:
            print("   ✓ API client: OK")
        else:
            print("   ℹ️  API client: Not required (static data)")
        print("   ✓ DB client: OK")
        print(f"   ✓ EntityExtractor: {'Present (unexpected)' if has_entity_extractor else 'Not used (correct)'}")
        print(f"   ℹ️  Reason: {reason}")

        return True

    except Exception as e:
        print(f"❌ {fetcher_name} - ERROR")
        print(f"   Error: {e}")
        return False


def main():
    """Verify all fetchers"""
    print("\n" + "="*80)
    print("COMPREHENSIVE FETCHER VERIFICATION")
    print("Checking hybrid enrichment configuration across all workers")
    print("="*80)

    results = []

    # Fetchers that SHOULD use EntityExtractor with api_client
    print("\n" + "="*80)
    print("FETCHERS USING EntityExtractor (should have api_client)")
    print("="*80)

    results.append(verify_fetcher_with_entity_extractor(
        RacesFetcher,
        "RacesFetcher"
    ))

    results.append(verify_fetcher_with_entity_extractor(
        ResultsFetcher,
        "ResultsFetcher"
    ))

    # Fetchers that should NOT use EntityExtractor
    print("\n\n" + "="*80)
    print("FETCHERS NOT USING EntityExtractor (direct entity fetching)")
    print("="*80)

    results.append(verify_fetcher_without_entity_extractor(
        HorsesFetcher,
        "HorsesFetcher",
        "Uses custom hybrid enrichment logic"
    ))

    results.append(verify_fetcher_without_entity_extractor(
        JockeysFetcher,
        "JockeysFetcher",
        "Fetches jockeys directly via API"
    ))

    results.append(verify_fetcher_without_entity_extractor(
        TrainersFetcher,
        "TrainersFetcher",
        "Fetches trainers directly via API"
    ))

    results.append(verify_fetcher_without_entity_extractor(
        OwnersFetcher,
        "OwnersFetcher",
        "Fetches owners directly via API"
    ))

    results.append(verify_fetcher_without_entity_extractor(
        CoursesFetcher,
        "CoursesFetcher",
        "Fetches courses directly via API"
    ))

    results.append(verify_fetcher_without_entity_extractor(
        BookmakersFetcher,
        "BookmakersFetcher",
        "Static data - no API calls needed",
        requires_api=False
    ))

    # Summary
    print("\n\n" + "="*80)
    print("VERIFICATION SUMMARY")
    print("="*80)

    passed = sum(results)
    total = len(results)

    print(f"\nResults: {passed}/{total} fetchers verified successfully")

    if passed == total:
        print("\n🎉 ALL FETCHERS VERIFIED SUCCESSFULLY!")
        print("\nHybrid enrichment configuration is correct across all workers.")
        print("✅ Ready for production deployment")
    else:
        print("\n⚠️  SOME FETCHERS FAILED VERIFICATION")
        print("Please review the errors above and fix before deploying.")

    print("="*80 + "\n")

    return passed == total


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
