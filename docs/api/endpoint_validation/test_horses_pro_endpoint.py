"""
Test Horse Pro Endpoint - Validates pedigree data availability
Tests: GET /v1/horses/{id}/pro
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.api_client import RacingAPIClient
from config.config import get_config
import json

def test_horses_pro_endpoint():
    """
    Test if we can get pedigree data from /v1/horses/{id}/pro endpoint

    Expected fields:
    - sire_id, sire, sire_region
    - dam_id, dam, dam_region
    - damsire_id, damsire, damsire_region
    - dob, sex_code, colour, region
    - breeder
    """
    print("=" * 80)
    print("TESTING: GET /v1/horses/{id}/pro")
    print("=" * 80)
    print()

    # Initialize API client
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url
    )

    # Sample horse IDs to test (these should exist in the database)
    # We'll test with a few known horses
    test_horse_ids = []

    # First, get some horse IDs from racecards (search endpoint requires additional params)
    print("Step 1: Getting sample horse IDs from /v1/racecards/pro...")
    from datetime import datetime, timedelta

    # Try today
    today = datetime.now().strftime('%Y-%m-%d')
    racecards_response = api_client.get_racecards_pro(date=today, region_codes=['gb', 'ire'])

    if not racecards_response or 'racecards' not in racecards_response or not racecards_response['racecards']:
        # Try yesterday
        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        racecards_response = api_client.get_racecards_pro(date=yesterday, region_codes=['gb', 'ire'])

    if not racecards_response or 'racecards' not in racecards_response:
        print("FAILED: Could not get racecards to extract horse IDs")
        return False

    # Extract horse IDs from runners
    for racecard in racecards_response['racecards'][:3]:
        runners = racecard.get('runners', [])
        for runner in runners[:5]:
            if 'horse_id' in runner and len(test_horse_ids) < 10:
                test_horse_ids.append(runner['horse_id'])

    if not test_horse_ids:
        print("FAILED: Could not extract horse IDs from racecards")
        return False

    print(f"Found {len(test_horse_ids)} horse IDs to test")
    print(f"Test IDs: {test_horse_ids[:3]}...")
    print()

    # Test each horse ID
    print("Step 2: Testing /v1/horses/{id}/pro endpoint for pedigree data...")
    print()

    results = {
        'total_tested': 0,
        'success': 0,
        'has_pedigree': 0,
        'has_dob': 0,
        'has_sex_code': 0,
        'has_colour': 0,
        'has_region': 0,
        'has_breeder': 0,
        'sample_data': []
    }

    for horse_id in test_horse_ids:
        results['total_tested'] += 1

        # Get horse details from pro endpoint
        horse_data = api_client.get_horse_details(horse_id, tier='pro')

        if not horse_data:
            print(f"  Horse {horse_id}: FAILED - No data returned")
            continue

        results['success'] += 1

        # Check for pedigree fields
        has_pedigree_data = False
        pedigree_fields = []

        if horse_data.get('sire_id'):
            results['has_pedigree'] += 1
            has_pedigree_data = True
            pedigree_fields.append('sire_id')
        if horse_data.get('dam_id'):
            pedigree_fields.append('dam_id')
        if horse_data.get('damsire_id'):
            pedigree_fields.append('damsire_id')

        # Check for horse detail fields
        detail_fields = []
        if horse_data.get('dob'):
            results['has_dob'] += 1
            detail_fields.append('dob')
        if horse_data.get('sex_code'):
            results['has_sex_code'] += 1
            detail_fields.append('sex_code')
        if horse_data.get('colour'):
            results['has_colour'] += 1
            detail_fields.append('colour')
        if horse_data.get('region'):
            results['has_region'] += 1
            detail_fields.append('region')
        if horse_data.get('breeder'):
            results['has_breeder'] += 1
            detail_fields.append('breeder')

        print(f"  Horse {horse_id} ({horse_data.get('name', 'Unknown')}): SUCCESS")
        print(f"    Pedigree fields: {', '.join(pedigree_fields) if pedigree_fields else 'NONE'}")
        print(f"    Detail fields: {', '.join(detail_fields) if detail_fields else 'NONE'}")

        # Store sample data for first successful horse
        if len(results['sample_data']) < 2 and (pedigree_fields or detail_fields):
            results['sample_data'].append({
                'horse_id': horse_id,
                'name': horse_data.get('name'),
                'sire': horse_data.get('sire'),
                'dam': horse_data.get('dam'),
                'damsire': horse_data.get('damsire'),
                'dob': horse_data.get('dob'),
                'sex_code': horse_data.get('sex_code'),
                'colour': horse_data.get('colour'),
                'region': horse_data.get('region'),
                'breeder': horse_data.get('breeder')
            })

    print()
    print("=" * 80)
    print("TEST RESULTS")
    print("=" * 80)
    print(f"Total horses tested: {results['total_tested']}")
    print(f"Successful API calls: {results['success']}")
    print(f"Horses with pedigree data: {results['has_pedigree']} ({results['has_pedigree']/results['success']*100 if results['success'] > 0 else 0:.1f}%)")
    print(f"Horses with DOB: {results['has_dob']} ({results['has_dob']/results['success']*100 if results['success'] > 0 else 0:.1f}%)")
    print(f"Horses with sex_code: {results['has_sex_code']} ({results['has_sex_code']/results['success']*100 if results['success'] > 0 else 0:.1f}%)")
    print(f"Horses with colour: {results['has_colour']} ({results['has_colour']/results['success']*100 if results['success'] > 0 else 0:.1f}%)")
    print(f"Horses with region: {results['has_region']} ({results['has_region']/results['success']*100 if results['success'] > 0 else 0:.1f}%)")
    print(f"Horses with breeder: {results['has_breeder']} ({results['has_breeder']/results['success']*100 if results['success'] > 0 else 0:.1f}%)")
    print()

    if results['sample_data']:
        print("SAMPLE DATA (First successful horse):")
        print("-" * 80)
        print(json.dumps(results['sample_data'][0], indent=2))
        print()

    # Determine success
    endpoint_works = results['success'] > 0
    has_data = results['has_pedigree'] > 0 or results['has_dob'] > 0

    print("=" * 80)
    if endpoint_works and has_data:
        print("RESULT: CONFIRMED - Endpoint works and returns pedigree/detail data")
        print()
        print("This endpoint can be used to populate:")
        print("  - ra_horse_pedigree table (sire_id, dam_id, damsire_id, breeder)")
        print("  - ra_horses NULL columns (dob, sex_code, colour, region)")
        return True
    elif endpoint_works and not has_data:
        print("RESULT: PARTIAL - Endpoint works but data may be sparse")
        print("WARNING: Not all horses have complete pedigree data")
        return True
    else:
        print("RESULT: FAILED - Cannot access endpoint or retrieve data")
        return False

if __name__ == '__main__':
    try:
        success = test_horses_pro_endpoint()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
