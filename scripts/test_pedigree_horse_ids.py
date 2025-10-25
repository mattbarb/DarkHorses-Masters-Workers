#!/usr/bin/env python3
"""
Test script to verify pedigree horse_id fields in Racing API
Critical for linking sires/dams/damsires to their horse records
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.logger import get_logger
import json

logger = get_logger('test_pedigree_horse_ids')

def test_horse_pedigree_fields():
    """Test a sample horse to see what pedigree horse_id fields are available"""

    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password
    )

    # Test with a known horse ID (from recent results)
    test_horse_id = "hrs_39698890"

    logger.info("=" * 80)
    logger.info("TESTING RACING API PEDIGREE HORSE_ID FIELDS")
    logger.info("=" * 80)
    logger.info(f"Test horse ID: {test_horse_id}")
    logger.info("")

    # Fetch from Pro endpoint
    logger.info("Fetching from /v1/horses/{id}/pro endpoint...")
    horse_data = api_client._make_request(f'/horses/{test_horse_id}/pro')

    if not horse_data:
        logger.error("❌ Failed to fetch horse data")
        return False

    logger.info(f"✅ Successfully fetched data for: {horse_data.get('name')}")
    logger.info("")

    # Check all pedigree-related fields
    logger.info("PEDIGREE FIELDS AVAILABLE:")
    logger.info("-" * 80)

    pedigree_fields = [
        'sire_id', 'sire', 'sire_horse_id',
        'dam_id', 'dam', 'dam_horse_id',
        'damsire_id', 'damsire', 'damsire_horse_id',
        'breeder', 'region'
    ]

    found_fields = {}
    missing_fields = []

    for field in pedigree_fields:
        value = horse_data.get(field)
        if value is not None:
            found_fields[field] = value
            logger.info(f"✅ {field:20s} = {value}")
        else:
            missing_fields.append(field)
            logger.info(f"❌ {field:20s} = NULL")

    logger.info("")
    logger.info("=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Found fields: {len(found_fields)}/{len(pedigree_fields)}")
    logger.info(f"Missing fields: {missing_fields}")
    logger.info("")

    # Check for alternative field names
    if 'sire_horse_id' not in found_fields:
        logger.info("CHECKING FOR ALTERNATIVE FIELD NAMES:")
        logger.info("-" * 80)

        alternative_patterns = [
            'sire_hrs_id', 'sireHorseId', 'sire.horse_id',
            'dam_hrs_id', 'damHorseId', 'dam.horse_id',
            'damsire_hrs_id', 'damsireHorseId', 'damsire.horse_id'
        ]

        for alt_field in alternative_patterns:
            if alt_field in horse_data:
                logger.info(f"✅ FOUND: {alt_field} = {horse_data[alt_field]}")
            else:
                logger.info(f"❌ NOT FOUND: {alt_field}")

        logger.info("")

        # Check if pedigree data is nested
        logger.info("CHECKING FOR NESTED PEDIGREE STRUCTURE:")
        logger.info("-" * 80)

        nested_fields = ['sire', 'dam', 'damsire']
        for field in nested_fields:
            if isinstance(horse_data.get(field), dict):
                logger.info(f"✅ {field} is a nested object:")
                for key, val in horse_data[field].items():
                    logger.info(f"   - {key}: {val}")
            else:
                logger.info(f"❌ {field} is not nested (type: {type(horse_data.get(field))})")

        logger.info("")

    # Save complete response for manual inspection
    output_file = Path(__file__).parent.parent / 'logs' / 'pedigree_api_response_sample.json'
    with open(output_file, 'w') as f:
        json.dump(horse_data, f, indent=2)

    logger.info(f"📝 Complete API response saved to: {output_file}")
    logger.info("")

    # Critical assessment
    logger.info("=" * 80)
    logger.info("CRITICAL ASSESSMENT")
    logger.info("=" * 80)

    if all(field in found_fields for field in ['sire_horse_id', 'dam_horse_id', 'damsire_horse_id']):
        logger.info("✅ ✅ ✅ ALL HORSE_ID FIELDS AVAILABLE!")
        logger.info("We can proceed with implementation immediately.")
        return True
    else:
        logger.warning("⚠️  HORSE_ID FIELDS NOT DIRECTLY AVAILABLE")
        logger.warning("Need to investigate alternative approaches:")
        logger.warning("1. Check if fields exist in different endpoint")
        logger.warning("2. Check if we need to fetch sire/dam/damsire separately")
        logger.warning("3. Check if there's a different API structure")
        return False

if __name__ == '__main__':
    try:
        success = test_horse_pedigree_fields()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Test failed with error: {e}", exc_info=True)
        sys.exit(1)
