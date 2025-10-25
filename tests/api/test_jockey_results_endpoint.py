"""
Test script for /v1/jockeys/{jockey_id}/results endpoint
Comprehensive analysis to understand data structure and richness
"""

import json
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('jockey_results_test')


def get_sample_jockeys(db_client, limit=5):
    """Get sample jockey IDs from database"""
    try:
        result = db_client.client.table('ra_jockeys').select('jockey_id, name').limit(limit).execute()
        return result.data
    except Exception as e:
        logger.error(f"Failed to get sample jockeys: {e}")
        return []


def test_jockey_results_endpoint(api_client, jockey_id, jockey_name, params=None):
    """
    Test the /v1/jockeys/{jockey_id}/results endpoint

    Args:
        api_client: RacingAPIClient instance
        jockey_id: Jockey ID to test
        jockey_name: Jockey name for logging
        params: Optional query parameters
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing jockey: {jockey_name} (ID: {jockey_id})")
    if params:
        logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    logger.info(f"{'='*80}")

    # Test standard endpoint
    endpoint = f'/jockeys/{jockey_id}/results'
    logger.info(f"Testing endpoint: {endpoint}")

    response = api_client._make_request(endpoint, params)

    if response:
        logger.info(f"✓ SUCCESS - Response received")

        # Analyze response structure
        logger.info(f"\n--- Response Structure ---")
        logger.info(f"Top-level keys: {list(response.keys())}")

        # Save full response to file
        filename = f"logs/jockey_results_{jockey_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(response, f, indent=2)
        logger.info(f"Full response saved to: {filename}")

        # Analyze structure
        analyze_response_structure(response, jockey_name)

        return response
    else:
        logger.warning(f"✗ FAILED - No response received")
        return None


def test_jockey_results_pro_endpoint(api_client, jockey_id, jockey_name, params=None):
    """Test the /v1/jockeys/{jockey_id}/results/pro endpoint"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Testing PRO endpoint for jockey: {jockey_name} (ID: {jockey_id})")
    if params:
        logger.info(f"Parameters: {json.dumps(params, indent=2)}")
    logger.info(f"{'='*80}")

    endpoint = f'/jockeys/{jockey_id}/results/pro'
    logger.info(f"Testing endpoint: {endpoint}")

    response = api_client._make_request(endpoint, params)

    if response:
        logger.info(f"✓ SUCCESS - Response received")

        # Save full response to file
        filename = f"logs/jockey_results_pro_{jockey_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(response, f, indent=2)
        logger.info(f"Full response saved to: {filename}")

        # Analyze structure
        analyze_response_structure(response, jockey_name, is_pro=True)

        return response
    else:
        logger.warning(f"✗ FAILED - No response received")
        return None


def analyze_response_structure(response, jockey_name, is_pro=False):
    """Analyze and log the response structure"""
    tier = "PRO" if is_pro else "STANDARD"
    logger.info(f"\n--- {tier} Response Analysis for {jockey_name} ---")

    # Check for jockey-level data
    if 'jockey' in response:
        logger.info(f"\n✓ Jockey-level data found:")
        jockey_data = response['jockey']
        for key, value in jockey_data.items():
            logger.info(f"  {key}: {value}")

    # Check for results
    if 'results' in response:
        results = response['results']
        logger.info(f"\n✓ Results array found: {len(results)} results")

        if results:
            # Analyze first result
            logger.info(f"\n--- Sample Result (First) ---")
            first_result = results[0]
            logger.info(f"Result keys: {list(first_result.keys())}")
            logger.info(f"\nSample result data:")
            for key, value in first_result.items():
                if isinstance(value, (dict, list)):
                    logger.info(f"  {key}: {type(value).__name__} ({len(value) if isinstance(value, (list, dict)) else 'N/A'})")
                else:
                    logger.info(f"  {key}: {value}")

            # Check for nested data
            if 'horse' in first_result and isinstance(first_result['horse'], dict):
                logger.info(f"\n--- Horse data in result ---")
                horse_data = first_result['horse']
                for key, value in horse_data.items():
                    logger.info(f"  {key}: {value}")

            if 'race' in first_result and isinstance(first_result['race'], dict):
                logger.info(f"\n--- Race data in result ---")
                race_data = first_result['race']
                for key, value in race_data.items():
                    logger.info(f"  {key}: {value}")

            # Analyze field coverage across all results
            logger.info(f"\n--- Field Coverage Analysis ---")
            analyze_field_coverage(results)

    # Check for statistics
    if 'statistics' in response:
        logger.info(f"\n✓ Statistics found:")
        stats = response['statistics']
        for key, value in stats.items():
            logger.info(f"  {key}: {value}")

    # Check for pagination
    pagination_keys = ['total', 'limit', 'skip', 'next', 'previous']
    pagination_data = {k: response.get(k) for k in pagination_keys if k in response}
    if pagination_data:
        logger.info(f"\n✓ Pagination data found:")
        for key, value in pagination_data.items():
            logger.info(f"  {key}: {value}")


def analyze_field_coverage(results):
    """Analyze which fields are present across results"""
    field_counts = {}
    total_results = len(results)

    for result in results:
        for key in result.keys():
            if key not in field_counts:
                field_counts[key] = 0
            if result[key] is not None and result[key] != '':
                field_counts[key] += 1

    logger.info(f"Field presence across {total_results} results:")
    for field, count in sorted(field_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_results) * 100
        logger.info(f"  {field}: {count}/{total_results} ({percentage:.1f}%)")


def test_various_parameters(api_client, jockey_id, jockey_name):
    """Test endpoint with various parameters"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING VARIOUS PARAMETERS FOR {jockey_name}")
    logger.info(f"{'='*80}")

    # Test 1: Basic call with limit
    logger.info(f"\n--- Test 1: Basic call with limit=10 ---")
    test_jockey_results_endpoint(api_client, jockey_id, jockey_name, {'limit': 10})

    # Test 2: Date range
    logger.info(f"\n--- Test 2: Date range (last 30 days) ---")
    from datetime import date, timedelta
    end_date = date.today().strftime('%Y-%m-%d')
    start_date = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
    test_jockey_results_endpoint(api_client, jockey_id, jockey_name, {
        'start_date': start_date,
        'end_date': end_date,
        'limit': 50
    })

    # Test 3: Pagination
    logger.info(f"\n--- Test 3: Pagination (skip=10, limit=5) ---")
    test_jockey_results_endpoint(api_client, jockey_id, jockey_name, {
        'skip': 10,
        'limit': 5
    })

    # Test 4: Region filter
    logger.info(f"\n--- Test 4: Region filter (GB only) ---")
    test_jockey_results_endpoint(api_client, jockey_id, jockey_name, {
        'region': ['gb'],
        'limit': 10
    })


def compare_with_other_entity_results(api_client, db_client):
    """Test if similar endpoints exist for other entities"""
    logger.info(f"\n{'='*80}")
    logger.info(f"TESTING OTHER ENTITY RESULTS ENDPOINTS")
    logger.info(f"{'='*80}")

    # Get sample IDs for other entities
    try:
        # Test trainer results
        logger.info(f"\n--- Testing /v1/trainers/{{id}}/results ---")
        trainer_result = db_client.client.table('ra_trainers').select('trainer_id, name').limit(1).execute()
        if trainer_result.data:
            trainer = trainer_result.data[0]
            endpoint = f"/trainers/{trainer['trainer_id']}/results"
            response = api_client._make_request(endpoint, {'limit': 5})
            if response:
                logger.info(f"✓ Trainer results endpoint EXISTS")
                logger.info(f"Response keys: {list(response.keys())}")
            else:
                logger.info(f"✗ Trainer results endpoint does NOT exist or failed")

        # Test horse results
        logger.info(f"\n--- Testing /v1/horses/{{id}}/results ---")
        horse_result = db_client.client.table('ra_horses').select('horse_id, name').limit(1).execute()
        if horse_result.data:
            horse = horse_result.data[0]
            endpoint = f"/horses/{horse['horse_id']}/results"
            response = api_client._make_request(endpoint, {'limit': 5})
            if response:
                logger.info(f"✓ Horse results endpoint EXISTS")
                logger.info(f"Response keys: {list(response.keys())}")
            else:
                logger.info(f"✗ Horse results endpoint does NOT exist or failed")

        # Test owner results
        logger.info(f"\n--- Testing /v1/owners/{{id}}/results ---")
        owner_result = db_client.client.table('ra_owners').select('owner_id, name').limit(1).execute()
        if owner_result.data:
            owner = owner_result.data[0]
            endpoint = f"/owners/{owner['owner_id']}/results"
            response = api_client._make_request(endpoint, {'limit': 5})
            if response:
                logger.info(f"✓ Owner results endpoint EXISTS")
                logger.info(f"Response keys: {list(response.keys())}")
            else:
                logger.info(f"✗ Owner results endpoint does NOT exist or failed")

    except Exception as e:
        logger.error(f"Error testing other entity endpoints: {e}")


def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("JOCKEY RESULTS ENDPOINT COMPREHENSIVE TEST")
    logger.info("=" * 80)

    # Initialize clients
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        max_retries=config.api.max_retries
    )

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    # Get sample jockeys
    logger.info("Fetching sample jockeys from database...")
    sample_jockeys = get_sample_jockeys(db_client, limit=3)

    if not sample_jockeys:
        logger.error("No jockeys found in database")
        return

    logger.info(f"Found {len(sample_jockeys)} sample jockeys")
    for jockey in sample_jockeys:
        logger.info(f"  - {jockey['name']} (ID: {jockey['jockey_id']})")

    # Test with first jockey
    test_jockey = sample_jockeys[0]
    logger.info(f"\n{'='*80}")
    logger.info(f"DETAILED TESTING WITH: {test_jockey['name']}")
    logger.info(f"{'='*80}")

    # Test 1: Standard endpoint
    response_standard = test_jockey_results_endpoint(
        api_client,
        test_jockey['jockey_id'],
        test_jockey['name']
    )

    # Test 2: Pro endpoint
    response_pro = test_jockey_results_pro_endpoint(
        api_client,
        test_jockey['jockey_id'],
        test_jockey['name']
    )

    # Test 3: Various parameters
    test_various_parameters(
        api_client,
        test_jockey['jockey_id'],
        test_jockey['name']
    )

    # Test 4: Other jockeys (quick test)
    logger.info(f"\n{'='*80}")
    logger.info(f"QUICK TESTS WITH OTHER JOCKEYS")
    logger.info(f"{'='*80}")

    for jockey in sample_jockeys[1:]:
        test_jockey_results_endpoint(
            api_client,
            jockey['jockey_id'],
            jockey['name'],
            {'limit': 5}
        )

    # Test 5: Compare with other entity results endpoints
    compare_with_other_entity_results(api_client, db_client)

    # Summary
    logger.info(f"\n{'='*80}")
    logger.info(f"TEST SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"API Statistics: {api_client.get_stats()}")
    logger.info(f"Check logs/ directory for full JSON responses")
    logger.info(f"{'='*80}")


if __name__ == '__main__':
    main()
