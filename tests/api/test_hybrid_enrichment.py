#!/usr/bin/env python3
"""
Test Hybrid Enrichment Approach
Tests the new entity_extractor hybrid enrichment for horses with Pro endpoint
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.entity_extractor import EntityExtractor

logger = get_logger('test_hybrid_enrichment')


def test_enrichment():
    """Test hybrid enrichment with tomorrow's racecards"""

    logger.info("=" * 80)
    logger.info("HYBRID ENRICHMENT TEST")
    logger.info("=" * 80)

    # Initialize clients
    config = get_config()

    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url
    )

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Initialize entity extractor with API client (for enrichment)
    entity_extractor = EntityExtractor(db_client, api_client)

    # Fetch tomorrow's racecards (likely to have new horses)
    tomorrow = (datetime.utcnow() + timedelta(days=1)).strftime('%Y-%m-%d')

    logger.info(f"Fetching racecards for {tomorrow}...")

    api_response = api_client.get_racecards_pro(
        date=tomorrow,
        region_codes=['gb', 'ire']
    )

    if not api_response or 'racecards' not in api_response:
        logger.error("No racecards returned!")
        return

    racecards = api_response.get('racecards', [])
    logger.info(f"Found {len(racecards)} races")

    if not racecards:
        logger.warning("No races found for tomorrow - test cannot proceed")
        return

    # Extract runners from first race
    first_race = racecards[0]
    runners = first_race.get('runners', [])

    logger.info(f"\nTest race: {first_race.get('race_name')} at {first_race.get('course')}")
    logger.info(f"Runners: {len(runners)}")

    if not runners:
        logger.warning("No runners in first race - test cannot proceed")
        return

    # Transform runners into runner records
    runner_records = []
    for runner in runners:
        runner_record = {
            'horse_id': runner.get('horse_id'),
            'racing_api_horse_id': runner.get('horse_id'),
            'horse_name': runner.get('horse'),
            'sex': runner.get('sex'),
            'jockey_id': runner.get('jockey_id'),
            'jockey_name': runner.get('jockey'),
            'trainer_id': runner.get('trainer_id'),
            'trainer_name': runner.get('trainer'),
            'owner_id': runner.get('owner_id'),
            'owner_name': runner.get('owner'),
        }
        runner_records.append(runner_record)

    logger.info(f"\n{'-' * 80}")
    logger.info("TESTING ENTITY EXTRACTION WITH ENRICHMENT")
    logger.info(f"{'-' * 80}")

    # Extract and store entities
    result = entity_extractor.extract_and_store_from_runners(runner_records)

    # Get stats
    stats = entity_extractor.get_stats()

    logger.info("\n" + "=" * 80)
    logger.info("ENRICHMENT RESULTS")
    logger.info("=" * 80)
    logger.info(f"Jockeys stored: {stats.get('jockeys', 0)}")
    logger.info(f"Trainers stored: {stats.get('trainers', 0)}")
    logger.info(f"Owners stored: {stats.get('owners', 0)}")
    logger.info(f"Horses stored: {stats.get('horses', 0)}")
    logger.info(f"Horses enriched with Pro: {stats.get('horses_enriched', 0)}")
    logger.info(f"Pedigrees captured: {stats.get('pedigrees_captured', 0)}")
    logger.info("=" * 80)

    # Verify pedigree data in database
    if stats.get('horses_enriched', 0) > 0:
        logger.info("\nVerifying pedigree data in database...")

        # Get one of the enriched horses
        for runner in runner_records:
            horse_id = runner.get('horse_id')
            if horse_id:
                try:
                    # Check ra_horses table
                    horse_result = db_client.client.table('ra_horses').select('*').eq('horse_id', horse_id).execute()
                    if horse_result.data:
                        horse = horse_result.data[0]
                        logger.info(f"\n✓ Horse in database: {horse.get('name')}")
                        logger.info(f"  - DOB: {horse.get('dob')}")
                        logger.info(f"  - Sex Code: {horse.get('sex_code')}")
                        logger.info(f"  - Colour: {horse.get('colour')}")
                        logger.info(f"  - Region: {horse.get('region')}")

                    # Check ra_horse_pedigree table
                    pedigree_result = db_client.client.table('ra_horse_pedigree').select('*').eq('horse_id', horse_id).execute()
                    if pedigree_result.data:
                        pedigree = pedigree_result.data[0]
                        logger.info(f"  ✓ Pedigree data:")
                        logger.info(f"    - Sire: {pedigree.get('sire')} ({pedigree.get('sire_id')})")
                        logger.info(f"    - Dam: {pedigree.get('dam')} ({pedigree.get('dam_id')})")
                        logger.info(f"    - Damsire: {pedigree.get('damsire')} ({pedigree.get('damsire_id')})")
                        logger.info(f"    - Breeder: {pedigree.get('breeder')}")

                except Exception as e:
                    logger.error(f"Error verifying horse data: {e}")

                break  # Just check first horse

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

    if stats.get('horses_enriched', 0) > 0:
        logger.info("✓ SUCCESS: Hybrid enrichment is working!")
        logger.info(f"  - {stats.get('horses_enriched', 0)} new horses enriched with Pro endpoint")
        logger.info(f"  - {stats.get('pedigrees_captured', 0)} pedigree records captured")
    else:
        logger.info("ℹ INFO: No new horses found to enrich (all horses already in database)")
        logger.info("  This is normal if you've already fetched tomorrow's races")


if __name__ == '__main__':
    test_enrichment()
