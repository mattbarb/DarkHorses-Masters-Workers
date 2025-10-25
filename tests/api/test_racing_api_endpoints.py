#!/usr/bin/env python3
"""
Racing API Endpoint Discovery Test

Tests all possible endpoint patterns to discover what's actually available
for jockeys, trainers, owners, and horses.

Purpose: Determine if we can use direct ID-based endpoints instead of
extracting entities from nested racecard data.

Usage:
    python3 scripts/test_racing_api_endpoints.py
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient
from datetime import datetime, timedelta

logger = get_logger('test_endpoints')


class EndpointTester:
    """Test Racing API endpoints to discover what's available"""

    def __init__(self):
        config = get_config()
        self.api_client = RacingAPIClient(
            username=config.api.username,
            password=config.api.password,
            base_url=config.api.base_url,
            timeout=config.api.timeout,
            max_retries=config.api.max_retries,
            rate_limit=config.api.rate_limit_per_second
        )
        self.test_results = {}

    def get_test_ids(self):
        """Get real IDs from a recent racecard for testing"""
        logger.info("Fetching recent racecard to get test IDs...")

        yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        racecards = self.api_client.get_racecards_pro(
            date=yesterday,
            region_codes=['gb', 'ire']
        )

        if not racecards or 'racecards' not in racecards:
            logger.error("Failed to get racecards")
            return None

        # Extract IDs from first race
        first_race = racecards['racecards'][0]
        first_runner = first_race['runners'][0] if first_race.get('runners') else {}

        test_ids = {
            'jockey_id': first_runner.get('jockey_id'),
            'jockey_name': first_runner.get('jockey'),
            'trainer_id': first_runner.get('trainer_id'),
            'trainer_name': first_runner.get('trainer'),
            'owner_id': first_runner.get('owner_id'),
            'owner_name': first_runner.get('owner'),
            'horse_id': first_runner.get('horse_id'),
            'horse_name': first_runner.get('horse'),
            'course_id': first_race.get('course_id'),
            'course_name': first_race.get('course')
        }

        logger.info(f"Test IDs extracted:")
        for key, value in test_ids.items():
            logger.info(f"  {key}: {value}")

        return test_ids

    def test_endpoint(self, endpoint_url, description):
        """Test a single endpoint and record results"""
        logger.info(f"\nTesting: {description}")
        logger.info(f"  URL: {endpoint_url}")

        try:
            response = self.api_client._make_request(endpoint_url)

            if response:
                logger.info(f"  ✅ SUCCESS - Endpoint exists!")

                # Show sample of response structure
                if isinstance(response, dict):
                    top_level_keys = list(response.keys())
                    logger.info(f"  Response keys: {top_level_keys}")

                    # Show nested structure
                    for key in top_level_keys[:3]:  # First 3 keys
                        value = response[key]
                        if isinstance(value, dict):
                            logger.info(f"    {key}: {list(value.keys())[:5]}...")
                        elif isinstance(value, list) and value:
                            logger.info(f"    {key}: [{len(value)} items]")
                            if isinstance(value[0], dict):
                                logger.info(f"      Item keys: {list(value[0].keys())[:10]}")
                        else:
                            logger.info(f"    {key}: {type(value).__name__}")

                return {
                    'exists': True,
                    'status': 'SUCCESS',
                    'response_sample': str(response)[:500],  # First 500 chars
                    'response_keys': list(response.keys()) if isinstance(response, dict) else None
                }
            else:
                logger.warning(f"  ❌ NOT FOUND - Endpoint doesn't exist or returned empty")
                return {
                    'exists': False,
                    'status': 'NOT_FOUND',
                    'error': 'No response data'
                }

        except Exception as e:
            logger.error(f"  ❌ ERROR - {str(e)}")
            return {
                'exists': False,
                'status': 'ERROR',
                'error': str(e)
            }

    def test_jockey_endpoints(self, test_ids):
        """Test all possible jockey endpoint patterns"""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING JOCKEY ENDPOINTS")
        logger.info("=" * 80)

        jockey_id = test_ids['jockey_id']
        jockey_name = test_ids['jockey_name']

        endpoints = {
            'jockey_by_id': f'/jockeys/{jockey_id}',
            'jockey_by_id_standard': f'/jockeys/{jockey_id}/standard',
            'jockey_by_id_pro': f'/jockeys/{jockey_id}/pro',
            'jockey_search_with_name': f'/jockeys/search?name={jockey_name}',
            'jockey_search_no_name': f'/jockeys/search',
            'jockeys_list': f'/jockeys',
            'jockey_results': f'/jockeys/{jockey_id}/results'
        }

        results = {}
        for name, endpoint in endpoints.items():
            results[name] = self.test_endpoint(endpoint, f"Jockey endpoint: {name}")

        self.test_results['jockeys'] = results
        return results

    def test_trainer_endpoints(self, test_ids):
        """Test all possible trainer endpoint patterns"""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING TRAINER ENDPOINTS")
        logger.info("=" * 80)

        trainer_id = test_ids['trainer_id']
        trainer_name = test_ids['trainer_name']

        endpoints = {
            'trainer_by_id': f'/trainers/{trainer_id}',
            'trainer_by_id_standard': f'/trainers/{trainer_id}/standard',
            'trainer_by_id_pro': f'/trainers/{trainer_id}/pro',
            'trainer_search_with_name': f'/trainers/search?name={trainer_name}',
            'trainer_search_no_name': f'/trainers/search',
            'trainers_list': f'/trainers',
            'trainer_results': f'/trainers/{trainer_id}/results'
        }

        results = {}
        for name, endpoint in endpoints.items():
            results[name] = self.test_endpoint(endpoint, f"Trainer endpoint: {name}")

        self.test_results['trainers'] = results
        return results

    def test_owner_endpoints(self, test_ids):
        """Test all possible owner endpoint patterns"""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING OWNER ENDPOINTS")
        logger.info("=" * 80)

        owner_id = test_ids['owner_id']
        owner_name = test_ids['owner_name']

        endpoints = {
            'owner_by_id': f'/owners/{owner_id}',
            'owner_by_id_standard': f'/owners/{owner_id}/standard',
            'owner_by_id_pro': f'/owners/{owner_id}/pro',
            'owner_search_with_name': f'/owners/search?name={owner_name}',
            'owner_search_no_name': f'/owners/search',
            'owners_list': f'/owners',
            'owner_results': f'/owners/{owner_id}/results'
        }

        results = {}
        for name, endpoint in endpoints.items():
            results[name] = self.test_endpoint(endpoint, f"Owner endpoint: {name}")

        self.test_results['owners'] = results
        return results

    def test_horse_endpoints(self, test_ids):
        """Test horse endpoints (for comparison with existing knowledge)"""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING HORSE ENDPOINTS (BASELINE)")
        logger.info("=" * 80)

        horse_id = test_ids['horse_id']
        horse_name = test_ids['horse_name']

        endpoints = {
            'horse_by_id': f'/horses/{horse_id}',
            'horse_by_id_standard': f'/horses/{horse_id}/standard',
            'horse_by_id_pro': f'/horses/{horse_id}/pro',
            'horse_search_with_name': f'/horses/search?name={horse_name}',
            'horse_search_no_name': f'/horses/search',
            'horses_list': f'/horses'
        }

        results = {}
        for name, endpoint in endpoints.items():
            results[name] = self.test_endpoint(endpoint, f"Horse endpoint: {name}")

        self.test_results['horses'] = results
        return results

    def test_course_endpoints(self, test_ids):
        """Test course endpoints (for comparison)"""
        logger.info("\n" + "=" * 80)
        logger.info("TESTING COURSE ENDPOINTS (BASELINE)")
        logger.info("=" * 80)

        course_id = test_ids['course_id']

        endpoints = {
            'course_by_id': f'/courses/{course_id}',
            'courses_list': f'/courses',
            'courses_with_region': f'/courses?region_codes=gb,ire'
        }

        results = {}
        for name, endpoint in endpoints.items():
            results[name] = self.test_endpoint(endpoint, f"Course endpoint: {name}")

        self.test_results['courses'] = results
        return results

    def print_summary(self):
        """Print comprehensive summary of findings"""
        logger.info("\n" + "=" * 80)
        logger.info("ENDPOINT DISCOVERY SUMMARY")
        logger.info("=" * 80)

        for entity_type, endpoints in self.test_results.items():
            logger.info(f"\n{entity_type.upper()}:")

            exists_count = sum(1 for result in endpoints.values() if result['exists'])
            total_count = len(endpoints)

            logger.info(f"  Total endpoints tested: {total_count}")
            logger.info(f"  Available endpoints: {exists_count}")
            logger.info(f"  Coverage: {exists_count}/{total_count} ({exists_count/total_count*100:.1f}%)")

            logger.info(f"\n  Detailed Results:")
            for endpoint_name, result in endpoints.items():
                status_icon = "✅" if result['exists'] else "❌"
                logger.info(f"    {status_icon} {endpoint_name}: {result['status']}")

    def generate_report(self):
        """Generate detailed JSON report"""
        report = {
            'timestamp': datetime.now().isoformat(),
            'test_results': self.test_results,
            'summary': {}
        }

        # Generate summary statistics
        for entity_type, endpoints in self.test_results.items():
            available = [name for name, result in endpoints.items() if result['exists']]
            not_available = [name for name, result in endpoints.items() if not result['exists']]

            report['summary'][entity_type] = {
                'total_tested': len(endpoints),
                'available': len(available),
                'not_available': len(not_available),
                'available_endpoints': available,
                'not_available_endpoints': not_available
            }

        # Save to file
        output_file = 'logs/racing_api_endpoint_discovery.json'
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)

        logger.info(f"\n\nDetailed report saved to: {output_file}")
        return report


def main():
    """Main execution"""
    logger.info("=" * 80)
    logger.info("RACING API ENDPOINT DISCOVERY TEST")
    logger.info("=" * 80)
    logger.info("\nPurpose: Discover what ID-based endpoints are available")
    logger.info("Goal: Determine if we can use clean direct endpoints instead of extraction\n")

    tester = EndpointTester()

    # Get test IDs from real racecard
    test_ids = tester.get_test_ids()
    if not test_ids:
        logger.error("Failed to get test IDs - cannot proceed")
        return

    # Test all entity types
    tester.test_jockey_endpoints(test_ids)
    tester.test_trainer_endpoints(test_ids)
    tester.test_owner_endpoints(test_ids)
    tester.test_horse_endpoints(test_ids)
    tester.test_course_endpoints(test_ids)

    # Print summary
    tester.print_summary()

    # Generate report
    report = tester.generate_report()

    # Final recommendation
    logger.info("\n" + "=" * 80)
    logger.info("RECOMMENDATION")
    logger.info("=" * 80)

    # Check if ID-based endpoints exist for jockeys/trainers/owners
    jockey_id_exists = report['summary']['jockeys']['available']
    trainer_id_exists = report['summary']['trainers']['available']
    owner_id_exists = report['summary']['owners']['available']

    if any(['by_id' in ep for ep in report['summary']['jockeys']['available_endpoints']]):
        logger.info("\n✅ ID-based endpoints EXIST for jockeys!")
        logger.info("   → RECOMMENDATION: Implement hybrid approach (like horses)")
    else:
        logger.info("\n❌ ID-based endpoints DO NOT exist for jockeys")
        logger.info("   → RECOMMENDATION: Keep extraction approach")

    if any(['by_id' in ep for ep in report['summary']['trainers']['available_endpoints']]):
        logger.info("\n✅ ID-based endpoints EXIST for trainers!")
        logger.info("   → RECOMMENDATION: Implement hybrid approach (like horses)")
    else:
        logger.info("\n❌ ID-based endpoints DO NOT exist for trainers")
        logger.info("   → RECOMMENDATION: Keep extraction approach")

    if any(['by_id' in ep for ep in report['summary']['owners']['available_endpoints']]):
        logger.info("\n✅ ID-based endpoints EXIST for owners!")
        logger.info("   → RECOMMENDATION: Implement hybrid approach (like horses)")
    else:
        logger.info("\n❌ ID-based endpoints DO NOT exist for owners")
        logger.info("   → RECOMMENDATION: Keep extraction approach")

    logger.info("\n" + "=" * 80)
    logger.info("See detailed results in: logs/racing_api_endpoint_discovery.json")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
