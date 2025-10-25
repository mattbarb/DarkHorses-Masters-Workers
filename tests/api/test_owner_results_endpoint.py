"""
Test script to verify owner results endpoint and available fields
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.logger import get_logger

logger = get_logger('test_owner_results')


def test_owner_results_endpoint():
    """Test owner results endpoint to verify available fields"""

    logger.info("=" * 80)
    logger.info("TESTING OWNER RESULTS ENDPOINT")
    logger.info("=" * 80)

    # Initialize API client
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        max_retries=config.api.max_retries
    )

    # Get owner_id from recent results
    logger.info("\n1. Fetching recent results to find owner_id...")
    yesterday = (datetime.utcnow().date() - timedelta(days=1)).strftime('%Y-%m-%d')

    results_response = api_client.get_results(date=yesterday, region_codes=['gb', 'ire'], limit=50)

    if not results_response or 'results' not in results_response:
        logger.error("Failed to fetch results")
        return False

    results = results_response.get('results', [])
    logger.info(f"✓ Fetched {len(results)} results")

    # Extract owner_id from first runner
    test_owner_id = None
    test_owner_name = None

    for result in results:
        runners = result.get('runners', [])
        for runner in runners:
            owner_id = runner.get('owner_id')
            owner_name = runner.get('owner')
            if owner_id:
                test_owner_id = owner_id
                test_owner_name = owner_name
                logger.info(f"✓ Found owner: {owner_name} ({owner_id})")
                break
        if test_owner_id:
            break

    if not test_owner_id:
        logger.error("No owner_id found in results")
        return False

    # Test owner results endpoint
    logger.info(f"\n2. Testing /owners/{test_owner_id}/results endpoint...")

    endpoint = f'/owners/{test_owner_id}/results'
    owner_results = api_client._make_request(endpoint, params={'limit': 50})

    if not owner_results or 'results' not in owner_results:
        logger.error(f"Failed to fetch owner results (endpoint may not exist or owner has no results)")
        logger.info("Note: This endpoint may not be available on all API tiers")
        return False

    owner_result_list = owner_results.get('results', [])
    logger.info(f"✓ Fetched {len(owner_result_list)} results for owner {test_owner_name}")

    # Analyze fields
    logger.info("\n3. Analyzing available fields in owner results...")

    all_fields = set()
    field_examples = {}
    field_counts = {}

    for result in owner_result_list:
        if 'runners' in result:
            for runner in result['runners']:
                for field, value in runner.items():
                    all_fields.add(field)

                    # Count non-null values
                    if field not in field_counts:
                        field_counts[field] = 0
                    if value is not None and value != '':
                        field_counts[field] += 1

                    # Store example value
                    if field not in field_examples and value is not None and value != '':
                        field_examples[field] = value

    # Sort fields alphabetically
    sorted_fields = sorted(all_fields)

    logger.info(f"\n4. Field Analysis ({len(sorted_fields)} total fields):")
    logger.info("-" * 80)

    total_runners = sum(len(r.get('runners', [])) for r in owner_result_list)

    for field in sorted_fields:
        count = field_counts.get(field, 0)
        percentage = (count / total_runners * 100) if total_runners > 0 else 0
        example = field_examples.get(field, 'N/A')

        # Format example value
        if isinstance(example, str) and len(str(example)) > 40:
            example = str(example)[:40] + "..."

        logger.info(f"{field:25} | {count:4}/{total_runners:4} ({percentage:5.1f}%) | Example: {example}")

    # Check for the 7 missing fields we identified
    logger.info("\n5. Checking for Previously Identified Missing Fields:")
    logger.info("-" * 80)

    target_fields = {
        'time': 'Finishing time',
        'sp_dec': 'Decimal odds format',
        'comment': 'Race commentary',
        'silk_url': 'Jockey silk image URL',
        'ovr_btn': 'Overall beaten distance',
        'jockey_claim_lbs': 'Jockey weight allowance',
        'weight': 'Weight in stones-lbs format'
    }

    for field, description in target_fields.items():
        if field in all_fields:
            count = field_counts.get(field, 0)
            percentage = (count / total_runners * 100) if total_runners > 0 else 0
            example = field_examples.get(field, 'N/A')
            logger.info(f"✓ {field:20} | {description:35} | {count}/{total_runners} ({percentage:.1f}%) | Example: {example}")
        else:
            logger.warning(f"✗ {field:20} | {description:35} | NOT FOUND")

    # Save sample response to file
    logger.info("\n6. Saving sample response to file...")

    logs_dir = Path(__file__).parent.parent / 'logs'
    logs_dir.mkdir(exist_ok=True)

    output_file = logs_dir / f'owner_results_sample_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'

    # Save first result with full details
    sample_data = {
        'owner_id': test_owner_id,
        'owner_name': test_owner_name,
        'results_count': len(owner_result_list),
        'total_runners': total_runners,
        'all_fields': sorted_fields,
        'field_statistics': {
            field: {
                'count': field_counts.get(field, 0),
                'percentage': (field_counts.get(field, 0) / total_runners * 100) if total_runners > 0 else 0,
                'example': field_examples.get(field, None)
            }
            for field in sorted_fields
        },
        'sample_result': owner_result_list[0] if owner_result_list else None
    }

    with open(output_file, 'w') as f:
        json.dump(sample_data, f, indent=2)

    logger.info(f"✓ Sample data saved to: {output_file}")

    # Compare with standard results endpoint
    logger.info("\n7. Comparing Owner Results vs Standard Results Endpoint...")

    standard_fields = set()
    for result in results:
        runners = result.get('runners', [])
        for runner in runners:
            standard_fields.update(runner.keys())

    owner_only = all_fields - standard_fields
    standard_only = standard_fields - all_fields
    common = all_fields & standard_fields

    logger.info(f"  Common fields: {len(common)}")
    logger.info(f"  Owner endpoint only: {len(owner_only)} - {sorted(owner_only) if owner_only else 'None'}")
    logger.info(f"  Standard endpoint only: {len(standard_only)} - {sorted(standard_only) if standard_only else 'None'}")

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)

    return True


if __name__ == '__main__':
    success = test_owner_results_endpoint()
    sys.exit(0 if success else 1)
