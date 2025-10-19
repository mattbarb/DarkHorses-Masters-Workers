#!/usr/bin/env python3
"""
Comprehensive Racing API Endpoint Testing
Tests ALL endpoints from OpenAPI spec and documents responses
"""

import sys
import os
import json
import time
import requests
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import base64

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from utils.logger import get_logger

logger = get_logger('comprehensive_api_test')


class RacingAPITester:
    """Comprehensive API endpoint tester"""

    def __init__(self, username: str, password: str, base_url: str = "https://api.theracingapi.com"):
        """Initialize tester"""
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password

        # Create auth headers
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json"
        }

        self.results = {}
        self.test_data = {
            'sample_horse_id': None,
            'sample_jockey_id': None,
            'sample_trainer_id': None,
            'sample_owner_id': None,
            'sample_race_id': None,
            'sample_course_id': None,
            'today': datetime.now().strftime('%Y-%m-%d'),
            'yesterday': (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'),
            'tomorrow': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d'),
        }

    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict:
        """Make API request with error handling"""
        url = f"{self.base_url}{endpoint}"

        try:
            time.sleep(0.5)  # Rate limiting
            response = requests.get(url, headers=self.headers, params=params, timeout=30)

            result = {
                'endpoint': endpoint,
                'params': params or {},
                'status_code': response.status_code,
                'success': response.status_code == 200,
                'timestamp': datetime.utcnow().isoformat()
            }

            if response.status_code == 200:
                try:
                    data = response.json()
                    result['response_keys'] = list(data.keys()) if isinstance(data, dict) else ['array']
                    result['sample_response'] = self._sample_response(data)
                    result['data_fields'] = self._extract_fields(data)
                except:
                    result['response_text'] = response.text[:500]
            else:
                result['error'] = response.text[:500]

            return result

        except Exception as e:
            return {
                'endpoint': endpoint,
                'params': params or {},
                'status_code': None,
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def _sample_response(self, data: Any, max_items: int = 2) -> Any:
        """Get sample of response data"""
        if isinstance(data, dict):
            sample = {}
            for key, value in list(data.items())[:5]:
                if isinstance(value, list) and len(value) > max_items:
                    sample[key] = value[:max_items]
                elif isinstance(value, dict):
                    sample[key] = self._sample_response(value, max_items=1)
                else:
                    sample[key] = value
            return sample
        elif isinstance(data, list) and len(data) > max_items:
            return [self._sample_response(item, max_items=1) for item in data[:max_items]]
        return data

    def _extract_fields(self, data: Any, prefix: str = '') -> List[str]:
        """Extract all field names from response"""
        fields = []

        if isinstance(data, dict):
            for key, value in data.items():
                field_name = f"{prefix}.{key}" if prefix else key
                fields.append(field_name)
                if isinstance(value, dict):
                    fields.extend(self._extract_fields(value, field_name))
                elif isinstance(value, list) and value and isinstance(value[0], dict):
                    fields.extend(self._extract_fields(value[0], field_name))

        return fields

    def test_courses(self):
        """Test course endpoints"""
        logger.info("Testing course endpoints...")

        # List all courses
        self.results['courses_all'] = self._make_request('/v1/courses')

        # Get regions
        self.results['courses_regions'] = self._make_request('/v1/courses/regions')

        # Filter by region
        self.results['courses_gb'] = self._make_request('/v1/courses', {'region_codes': ['gb']})
        self.results['courses_ire'] = self._make_request('/v1/courses', {'region_codes': ['ire']})

        # Extract sample course ID
        if self.results['courses_all']['success']:
            try:
                courses = self.results['courses_all'].get('sample_response', {}).get('courses', [])
                if courses:
                    self.test_data['sample_course_id'] = courses[0].get('id')
            except:
                pass

    def test_horses(self):
        """Test horse endpoints - COMPREHENSIVE"""
        logger.info("Testing horse endpoints...")

        # Try all possible horse endpoint variations
        endpoints_to_test = [
            ('/v1/horses', {}),
            ('/v1/horses/search', {}),
            ('/v1/horses/search', {'limit': 10}),
            ('/v1/horses/search', {'limit': 10, 'skip': 0}),
            ('/v1/horses/search', {'name': 'test'}),
            ('/v1/horses/list', {}),
            ('/v1/horses/all', {}),
        ]

        for endpoint, params in endpoints_to_test:
            key = f"horses_{endpoint.replace('/', '_')}_{len(params)}"
            logger.info(f"Testing: {endpoint} with params: {params}")
            self.results[key] = self._make_request(endpoint, params)

        # Test individual horse endpoint (need a real horse ID first)
        # Get horse ID from racecard
        racecard_result = self._make_request('/v1/racecards/pro', {'date': self.test_data['yesterday']})
        if racecard_result['success']:
            try:
                races = racecard_result.get('sample_response', {}).get('races', [])
                if races and 'runners' in races[0]:
                    runners = races[0]['runners']
                    if runners:
                        horse_id = runners[0].get('horse', {}).get('id')
                        if horse_id:
                            self.test_data['sample_horse_id'] = horse_id

                            # Test all horse detail tiers
                            self.results['horse_standard'] = self._make_request(f'/v1/horses/{horse_id}/standard')
                            self.results['horse_pro'] = self._make_request(f'/v1/horses/{horse_id}/pro')
                            self.results['horse_basic'] = self._make_request(f'/v1/horses/{horse_id}/basic')
                            self.results['horse_free'] = self._make_request(f'/v1/horses/{horse_id}/free')
            except Exception as e:
                logger.error(f"Error extracting horse ID: {e}")

    def test_jockeys(self):
        """Test jockey endpoints"""
        logger.info("Testing jockey endpoints...")

        # Search endpoints
        self.results['jockeys_search'] = self._make_request('/v1/jockeys/search', {'limit': 10})
        self.results['jockeys_search_name'] = self._make_request('/v1/jockeys/search', {'name': 'Murphy'})

        # Try list endpoint
        self.results['jockeys_list'] = self._make_request('/v1/jockeys', {'limit': 10})

        # Extract sample jockey ID
        if self.results['jockeys_search']['success']:
            try:
                jockeys = self.results['jockeys_search'].get('sample_response', {}).get('jockeys', [])
                if jockeys:
                    self.test_data['sample_jockey_id'] = jockeys[0].get('id')

                    # Test individual jockey
                    self.results['jockey_detail'] = self._make_request(
                        f"/v1/jockeys/{self.test_data['sample_jockey_id']}"
                    )
            except:
                pass

    def test_trainers(self):
        """Test trainer endpoints"""
        logger.info("Testing trainer endpoints...")

        # Search endpoints
        self.results['trainers_search'] = self._make_request('/v1/trainers/search', {'limit': 10})
        self.results['trainers_search_name'] = self._make_request('/v1/trainers/search', {'name': 'Henderson'})

        # Try list endpoint
        self.results['trainers_list'] = self._make_request('/v1/trainers', {'limit': 10})

        # Extract sample trainer ID
        if self.results['trainers_search']['success']:
            try:
                trainers = self.results['trainers_search'].get('sample_response', {}).get('trainers', [])
                if trainers:
                    self.test_data['sample_trainer_id'] = trainers[0].get('id')

                    # Test individual trainer
                    self.results['trainer_detail'] = self._make_request(
                        f"/v1/trainers/{self.test_data['sample_trainer_id']}"
                    )
            except:
                pass

    def test_owners(self):
        """Test owner endpoints"""
        logger.info("Testing owner endpoints...")

        # Search endpoints
        self.results['owners_search'] = self._make_request('/v1/owners/search', {'limit': 10})
        self.results['owners_search_name'] = self._make_request('/v1/owners/search', {'name': 'Qatar'})

        # Try list endpoint
        self.results['owners_list'] = self._make_request('/v1/owners', {'limit': 10})

        # Extract sample owner ID
        if self.results['owners_search']['success']:
            try:
                owners = self.results['owners_search'].get('sample_response', {}).get('owners', [])
                if owners:
                    self.test_data['sample_owner_id'] = owners[0].get('id')

                    # Test individual owner
                    self.results['owner_detail'] = self._make_request(
                        f"/v1/owners/{self.test_data['sample_owner_id']}"
                    )
            except:
                pass

    def test_racecards(self):
        """Test racecard endpoints"""
        logger.info("Testing racecard endpoints...")

        # Free tier
        self.results['racecards_free_today'] = self._make_request('/v1/racecards/free', {'day': 'today'})
        self.results['racecards_free_tomorrow'] = self._make_request('/v1/racecards/free', {'day': 'tomorrow'})

        # Basic tier
        self.results['racecards_basic_today'] = self._make_request('/v1/racecards/basic', {'day': 'today'})

        # Standard tier
        self.results['racecards_standard_today'] = self._make_request('/v1/racecards/standard', {'day': 'today'})

        # Pro tier (historical and future)
        self.results['racecards_pro_today'] = self._make_request('/v1/racecards/pro', {'date': self.test_data['today']})
        self.results['racecards_pro_yesterday'] = self._make_request('/v1/racecards/pro', {'date': self.test_data['yesterday']})
        self.results['racecards_pro_gb'] = self._make_request('/v1/racecards/pro', {
            'date': self.test_data['yesterday'],
            'region_codes': ['gb']
        })

        # Big races
        self.results['racecards_big_races'] = self._make_request('/v1/racecards/big-races')

        # Summaries
        self.results['racecards_summaries'] = self._make_request('/v1/racecards/summaries', {
            'date': self.test_data['today']
        })

    def test_results(self):
        """Test results endpoints"""
        logger.info("Testing results endpoints...")

        # Results with different parameters
        self.results['results_yesterday'] = self._make_request('/v1/results', {
            'start_date': self.test_data['yesterday'],
            'end_date': self.test_data['yesterday']
        })

        self.results['results_gb'] = self._make_request('/v1/results', {
            'start_date': self.test_data['yesterday'],
            'end_date': self.test_data['yesterday'],
            'region': ['gb']
        })

        self.results['results_with_limit'] = self._make_request('/v1/results', {
            'start_date': self.test_data['yesterday'],
            'end_date': self.test_data['yesterday'],
            'limit': 10
        })

    def test_pedigree(self):
        """Test pedigree-related endpoints"""
        logger.info("Testing pedigree endpoints...")

        # These might exist
        endpoints_to_test = [
            '/v1/pedigree',
            '/v1/horses/pedigree',
            '/v1/sires',
            '/v1/dams',
            '/v1/breeders',
        ]

        for endpoint in endpoints_to_test:
            key = f"pedigree_{endpoint.replace('/', '_')}"
            self.results[key] = self._make_request(endpoint)

    def test_statistics(self):
        """Test statistics endpoints"""
        logger.info("Testing statistics endpoints...")

        endpoints_to_test = [
            '/v1/statistics',
            '/v1/stats',
            '/v1/horses/statistics',
            '/v1/jockeys/statistics',
            '/v1/trainers/statistics',
        ]

        for endpoint in endpoints_to_test:
            key = f"stats_{endpoint.replace('/', '_')}"
            self.results[key] = self._make_request(endpoint)

    def run_comprehensive_test(self) -> Dict:
        """Run all tests"""
        logger.info("=" * 80)
        logger.info("COMPREHENSIVE RACING API ENDPOINT TESTING")
        logger.info("=" * 80)

        # Test all endpoint categories
        self.test_courses()
        self.test_horses()
        self.test_jockeys()
        self.test_trainers()
        self.test_owners()
        self.test_racecards()
        self.test_results()
        self.test_pedigree()
        self.test_statistics()

        # Compile summary
        summary = {
            'test_timestamp': datetime.utcnow().isoformat(),
            'total_endpoints_tested': len(self.results),
            'successful_endpoints': sum(1 for r in self.results.values() if r.get('success')),
            'failed_endpoints': sum(1 for r in self.results.values() if not r.get('success')),
            'test_data_collected': self.test_data,
            'results': self.results
        }

        return summary

    def save_results(self, output_file: str):
        """Save test results to JSON file"""
        summary = self.run_comprehensive_test()

        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2)

        logger.info(f"\nResults saved to: {output_file}")
        logger.info(f"Total endpoints tested: {summary['total_endpoints_tested']}")
        logger.info(f"Successful: {summary['successful_endpoints']}")
        logger.info(f"Failed: {summary['failed_endpoints']}")

        # Print successful endpoints
        logger.info("\n" + "=" * 80)
        logger.info("SUCCESSFUL ENDPOINTS:")
        logger.info("=" * 80)
        for name, result in summary['results'].items():
            if result.get('success'):
                logger.info(f"✓ {name}: {result['endpoint']}")
                if result.get('data_fields'):
                    logger.info(f"  Fields: {len(result['data_fields'])} fields found")

        # Print failed endpoints
        logger.info("\n" + "=" * 80)
        logger.info("FAILED ENDPOINTS:")
        logger.info("=" * 80)
        for name, result in summary['results'].items():
            if not result.get('success'):
                logger.info(f"✗ {name}: {result['endpoint']}")
                logger.info(f"  Status: {result.get('status_code', 'N/A')}")
                if result.get('error'):
                    logger.info(f"  Error: {result['error'][:100]}")


def main():
    """Main execution"""
    # Get credentials from environment
    username = os.getenv('RACING_API_USERNAME')
    password = os.getenv('RACING_API_PASSWORD')

    if not username or not password:
        logger.error("Missing RACING_API_USERNAME or RACING_API_PASSWORD environment variables")
        sys.exit(1)

    # Run tests
    tester = RacingAPITester(username, password)

    # Save results
    output_file = '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/docs/api_endpoint_test_results.json'
    tester.save_results(output_file)

    logger.info("\n" + "=" * 80)
    logger.info("TEST COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Full results available in: {output_file}")


if __name__ == '__main__':
    main()
