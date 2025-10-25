#!/usr/bin/env python3
"""
Test Breeder Field Capture

Verifies that the breeder field is being captured from Racing API
and stored in ra_mst_horses table.

Usage:
    python3 scripts/test_breeder_field_capture.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.entity_extractor import EntityExtractor
from datetime import datetime, timedelta

logger = get_logger('test_breeder_capture')


def test_breeder_field_capture():
    """Test that breeder field is captured from Racing API"""

    logger.info("=" * 80)
    logger.info("TESTING BREEDER FIELD CAPTURE")
    logger.info("=" * 80)

    # Initialize clients
    config = get_config()

    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        max_retries=config.api.max_retries,
        rate_limit=config.api.rate_limit_per_second
    )

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    # Step 1: Fetch a recent racecard to get horse IDs
    logger.info("\nStep 1: Fetching recent racecard...")
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')

    racecards = api_client.get_racecards_pro(
        date=yesterday,
        region_codes=['gb', 'ire']
    )

    if not racecards or 'racecards' not in racecards:
        logger.error("No racecards found")
        return False

    # Extract a few horse IDs
    test_horse_ids = []
    for racecard in racecards['racecards'][:3]:  # First 3 races
        for runner in racecard.get('runners', [])[:2]:  # First 2 runners
            horse_id = runner.get('horse_id')
            horse_name = runner.get('horse')
            if horse_id:
                test_horse_ids.append({'id': horse_id, 'name': horse_name})

    if not test_horse_ids:
        logger.error("No horse IDs found in racecards")
        return False

    logger.info(f"Found {len(test_horse_ids)} test horses")

    # Step 2: Test API endpoint directly
    logger.info("\nStep 2: Testing Racing API /horses/{id}/pro endpoint...")

    api_has_breeder = 0
    for horse in test_horse_ids[:3]:  # Test first 3
        horse_id = horse['id']
        horse_name = horse['name']

        logger.info(f"\n  Testing {horse_id} ({horse_name})...")

        horse_pro = api_client.get_horse_details(horse_id, tier='pro')

        if horse_pro:
            breeder = horse_pro.get('breeder')
            if breeder:
                logger.info(f"    ✓ Breeder field FOUND in API: {breeder}")
                api_has_breeder += 1
            else:
                logger.warning(f"    ✗ Breeder field NOT found in API response")
        else:
            logger.error(f"    ✗ Failed to fetch Pro data for {horse_id}")

    logger.info(f"\n  API Test Summary: {api_has_breeder}/{len(test_horse_ids[:3])} horses have breeder data")

    # Step 3: Test EntityExtractor with a NEW horse
    logger.info("\nStep 3: Testing EntityExtractor enrichment...")

    # Find a horse NOT in database
    existing_ids = set()
    try:
        result = db_client.client.table('ra_mst_horses').select('id').execute()
        existing_ids = {row['id'] for row in result.data}
        logger.info(f"  Found {len(existing_ids)} existing horses in database")
    except Exception as e:
        logger.error(f"  Error fetching existing horses: {e}")

    # Find a new horse
    new_horse = None
    for horse in test_horse_ids:
        if horse['id'] not in existing_ids:
            new_horse = horse
            break

    if not new_horse:
        logger.warning("  No NEW horses found for testing - all test horses already in DB")
        logger.info("  Skipping EntityExtractor test (would not enrich existing horses)")
    else:
        logger.info(f"  Testing with NEW horse: {new_horse['id']} ({new_horse['name']})")

        # Create entity extractor
        entity_extractor = EntityExtractor(db_client, api_client)

        # Create test horse record
        test_horse_records = [{
            'id': new_horse['id'],
            'name': new_horse['name'],
            'sex': 'Unknown'
        }]

        # Extract and store
        entities = {'horses': test_horse_records}
        result = entity_extractor.store_entities(entities)

        logger.info(f"  EntityExtractor result: {result}")

        # Verify in database
        try:
            db_result = db_client.client.table('ra_mst_horses').select('id', 'name', 'breeder').eq('id', new_horse['id']).execute()

            if db_result.data:
                db_horse = db_result.data[0]
                if db_horse.get('breeder'):
                    logger.info(f"  ✓ SUCCESS: Breeder field captured in database: {db_horse['breeder']}")
                    return True
                else:
                    logger.error(f"  ✗ FAILED: Breeder field is NULL in database")
                    return False
            else:
                logger.error(f"  ✗ Horse not found in database")
                return False
        except Exception as e:
            logger.error(f"  ✗ Error verifying database: {e}")
            return False

    # Step 4: Check overall database population
    logger.info("\nStep 4: Checking overall breeder field population...")

    try:
        result = db_client.client.table('ra_mst_horses').select('id', 'breeder').not_.is_('breeder', 'null').limit(10).execute()

        with_breeder = len(result.data)
        logger.info(f"  Found {with_breeder} horses with breeder data (sample of 10)")

        if with_breeder > 0:
            logger.info(f"  Sample breeders:")
            for horse in result.data[:5]:
                logger.info(f"    - {horse.get('breeder')}")

    except Exception as e:
        logger.error(f"  Error checking database: {e}")

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

    return True


if __name__ == '__main__':
    success = test_breeder_field_capture()
    sys.exit(0 if success else 1)
