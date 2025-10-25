"""
Test All Entity Endpoints
Comprehensive test of individual Pro/Standard endpoints for all entity types
"""

import os
import json
import time
import requests
from requests.auth import HTTPBasicAuth
from datetime import datetime

# API Credentials
API_USERNAME = 'l2fC3sZFIZmvpiMt6DdUCpEv'
API_PASSWORD = 'R0pMr1L58WH3hUkpVtPcwYnw'
BASE_URL = 'https://api.theracingapi.com'

# Test IDs from database
TEST_IDS = {
    'horse_id': 'hrs_6181308',  # Flaggan (IRE)
    'jockey_id': 'jky_41100',   # Shane Kelly
    'trainer_id': 'trn_116136', # Phil McEntee
    'owner_id': 'own_1432844',  # Dkf Partnership
    'course_id': 'crs_104',     # Bangor-on-Dee
    'race_id': 'rac_10975861'   # Sample race
}


def test_endpoint(endpoint, params=None, tier='pro'):
    """Test an API endpoint"""
    url = f"{BASE_URL}{endpoint}"

    print(f"\n{'='*80}")
    print(f"Testing: {endpoint}")
    print(f"Tier: {tier}")
    if params:
        print(f"Params: {params}")
    print(f"{'='*80}")

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(API_USERNAME, API_PASSWORD),
            params=params,
            timeout=30
        )

        print(f"Status Code: {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ SUCCESS")
            print(f"\nResponse Keys: {list(data.keys()) if isinstance(data, dict) else 'array'}")
            print(f"\nSample Response (first 2000 chars):")
            print(json.dumps(data, indent=2)[:2000])

            return {
                'success': True,
                'status_code': 200,
                'data': data,
                'endpoint': endpoint,
                'tier': tier
            }
        else:
            print(f"\n❌ FAILED")
            print(f"Response: {response.text[:500]}")

            return {
                'success': False,
                'status_code': response.status_code,
                'error': response.text[:500],
                'endpoint': endpoint,
                'tier': tier
            }

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        return {
            'success': False,
            'error': str(e),
            'endpoint': endpoint,
            'tier': tier
        }
    finally:
        # Rate limiting
        time.sleep(0.6)


def main():
    """Test all entity endpoints"""

    results = {
        'test_timestamp': datetime.utcnow().isoformat(),
        'test_ids': TEST_IDS,
        'endpoints': {}
    }

    # 1. HORSES
    print("\n" + "="*80)
    print("TESTING HORSE ENDPOINTS")
    print("="*80)

    horse_id = TEST_IDS['horse_id']

    # Horse Pro endpoint
    results['endpoints']['horse_pro'] = test_endpoint(
        f"/v1/horses/{horse_id}/pro",
        tier='pro'
    )

    # Horse Standard endpoint
    results['endpoints']['horse_standard'] = test_endpoint(
        f"/v1/horses/{horse_id}/standard",
        tier='standard'
    )

    # Horse Results
    results['endpoints']['horse_results'] = test_endpoint(
        f"/v1/horses/{horse_id}/results",
        params={'limit': 10}
    )

    # Horse Analysis - Distance Times
    results['endpoints']['horse_analysis_distance'] = test_endpoint(
        f"/v1/horses/{horse_id}/analysis/distance-times"
    )

    # 2. JOCKEYS
    print("\n" + "="*80)
    print("TESTING JOCKEY ENDPOINTS")
    print("="*80)

    jockey_id = TEST_IDS['jockey_id']

    # Jockey Results
    results['endpoints']['jockey_results'] = test_endpoint(
        f"/v1/jockeys/{jockey_id}/results",
        params={'limit': 10}
    )

    # Jockey Analysis - Courses
    results['endpoints']['jockey_analysis_courses'] = test_endpoint(
        f"/v1/jockeys/{jockey_id}/analysis/courses"
    )

    # Jockey Analysis - Distances
    results['endpoints']['jockey_analysis_distances'] = test_endpoint(
        f"/v1/jockeys/{jockey_id}/analysis/distances"
    )

    # Jockey Analysis - Trainers
    results['endpoints']['jockey_analysis_trainers'] = test_endpoint(
        f"/v1/jockeys/{jockey_id}/analysis/trainers"
    )

    # Jockey Analysis - Owners
    results['endpoints']['jockey_analysis_owners'] = test_endpoint(
        f"/v1/jockeys/{jockey_id}/analysis/owners"
    )

    # 3. TRAINERS
    print("\n" + "="*80)
    print("TESTING TRAINER ENDPOINTS")
    print("="*80)

    trainer_id = TEST_IDS['trainer_id']

    # Trainer Results
    results['endpoints']['trainer_results'] = test_endpoint(
        f"/v1/trainers/{trainer_id}/results",
        params={'limit': 10}
    )

    # Trainer Analysis - Courses
    results['endpoints']['trainer_analysis_courses'] = test_endpoint(
        f"/v1/trainers/{trainer_id}/analysis/courses"
    )

    # Trainer Analysis - Distances
    results['endpoints']['trainer_analysis_distances'] = test_endpoint(
        f"/v1/trainers/{trainer_id}/analysis/distances"
    )

    # Trainer Analysis - Jockeys
    results['endpoints']['trainer_analysis_jockeys'] = test_endpoint(
        f"/v1/trainers/{trainer_id}/analysis/jockeys"
    )

    # Trainer Analysis - Owners
    results['endpoints']['trainer_analysis_owners'] = test_endpoint(
        f"/v1/trainers/{trainer_id}/analysis/owners"
    )

    # Trainer Analysis - Horse Age
    results['endpoints']['trainer_analysis_horse_age'] = test_endpoint(
        f"/v1/trainers/{trainer_id}/analysis/horse-age"
    )

    # 4. OWNERS
    print("\n" + "="*80)
    print("TESTING OWNER ENDPOINTS")
    print("="*80)

    owner_id = TEST_IDS['owner_id']

    # Owner Results
    results['endpoints']['owner_results'] = test_endpoint(
        f"/v1/owners/{owner_id}/results",
        params={'limit': 10}
    )

    # Owner Analysis - Courses
    results['endpoints']['owner_analysis_courses'] = test_endpoint(
        f"/v1/owners/{owner_id}/analysis/courses"
    )

    # Owner Analysis - Distances
    results['endpoints']['owner_analysis_distances'] = test_endpoint(
        f"/v1/owners/{owner_id}/analysis/distances"
    )

    # Owner Analysis - Jockeys
    results['endpoints']['owner_analysis_jockeys'] = test_endpoint(
        f"/v1/owners/{owner_id}/analysis/jockeys"
    )

    # Owner Analysis - Trainers
    results['endpoints']['owner_analysis_trainers'] = test_endpoint(
        f"/v1/owners/{owner_id}/analysis/trainers"
    )

    # 5. RACES
    print("\n" + "="*80)
    print("TESTING RACE ENDPOINTS")
    print("="*80)

    race_id = TEST_IDS['race_id']

    # Race Pro endpoint
    results['endpoints']['race_pro'] = test_endpoint(
        f"/v1/racecards/{race_id}/pro",
        tier='pro'
    )

    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)

    total = len(results['endpoints'])
    successful = sum(1 for r in results['endpoints'].values() if r.get('success'))
    failed = total - successful

    print(f"\nTotal Endpoints Tested: {total}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")

    print("\n✅ Successful Endpoints:")
    for name, result in results['endpoints'].items():
        if result.get('success'):
            print(f"  - {name}: {result['endpoint']}")

    print("\n❌ Failed Endpoints:")
    for name, result in results['endpoints'].items():
        if not result.get('success'):
            print(f"  - {name}: {result['endpoint']}")
            if 'status_code' in result:
                print(f"    Status: {result['status_code']}")

    # Save results
    output_file = '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/entity_endpoint_test_results.json'
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n✅ Results saved to: {output_file}")

    return results


if __name__ == '__main__':
    main()
