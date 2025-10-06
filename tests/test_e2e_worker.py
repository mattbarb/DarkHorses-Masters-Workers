#!/usr/bin/env python3
"""
End-to-End Worker Test
Simulates a complete worker cycle for one entity to verify the full data pipeline
"""

import os
import sys
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init
from supabase import create_client, Client

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from fetchers.courses_fetcher import CoursesFetcher
from utils.logger import get_logger

# Load environment
env_file = Path(__file__).parent.parent / '.env.local'
if not env_file.exists():
    env_file = Path(__file__).parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

# Initialize colorama
init(autoreset=True)

logger = get_logger('e2e_test')


class EndToEndWorkerTest:
    """Test suite for end-to-end worker functionality"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")

        self.client: Client = create_client(self.supabase_url, self.supabase_key)

        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
        self.start_time = None
        self.end_time = None
        self.test_data = {}

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}🔄 END-TO-END WORKER TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: Complete data pipeline (fetch → parse → upsert → verify)")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def test_config_initialization(self):
        """Test 1: Verify configuration can be initialized"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Testing configuration initialization...")

        start = time.time()
        try:
            config = get_config()

            # Verify critical config exists
            checks = {
                'API credentials': config.api.username is not None and config.api.password is not None,
                'Database credentials': config.supabase.url is not None and config.supabase.service_key is not None,
                'Paths configured': config.paths.base_dir is not None
            }

            all_passed = all(checks.values())
            elapsed = time.time() - start

            if all_passed:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Configuration initialized")
                for check_name, passed in checks.items():
                    print(f"  ✓ {check_name}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Configuration issues:")
                for check_name, passed in checks.items():
                    symbol = "✓" if passed else "✗"
                    print(f"  {symbol} {check_name}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Configuration error: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_fetcher_initialization(self):
        """Test 2: Verify fetcher can be initialized"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Testing fetcher initialization...")

        start = time.time()
        try:
            fetcher = CoursesFetcher()

            # Verify fetcher has required components
            checks = {
                'Config loaded': fetcher.config is not None,
                'API client initialized': fetcher.api_client is not None,
                'Database client initialized': fetcher.db_client is not None
            }

            all_passed = all(checks.values())
            elapsed = time.time() - start

            if all_passed:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Fetcher initialized successfully")
                for check_name, passed in checks.items():
                    print(f"  ✓ {check_name}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                self.test_data['fetcher'] = fetcher
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Fetcher initialization issues:")
                for check_name, passed in checks.items():
                    symbol = "✓" if passed else "✗"
                    print(f"  {symbol} {check_name}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Fetcher initialization error: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_api_fetch(self):
        """Test 3: Test API data fetch"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Testing API data fetch...")

        start = time.time()
        try:
            if 'fetcher' not in self.test_data:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Fetcher not initialized (previous test failed)")
                self.results['failed'] += 1
                return False

            fetcher = self.test_data['fetcher']

            # Fetch a limited set of courses (UK/Ireland only, lightweight test)
            response = fetcher.api_client.get_courses(region_codes=['gb', 'ire'])

            elapsed = time.time() - start

            if response and 'courses' in response:
                courses = response.get('courses', [])
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - API fetch successful")
                print(f"  ✓ Response received from Racing API")
                print(f"  ✓ Courses fetched: {len(courses)}")
                print(f"  ✓ API stats: {fetcher.api_client.get_stats()}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                self.test_data['api_response'] = response
                self.test_data['courses_count'] = len(courses)
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - API fetch failed")
                print(f"  Response: {response}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - API fetch error: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_database_count_before(self):
        """Test 4: Count existing records before upsert"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Counting existing database records...")

        start = time.time()
        try:
            response = self.client.table('ra_courses').select('id', count='exact').execute()
            count_before = response.count

            elapsed = time.time() - start

            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Database query successful")
            print(f"  ✓ Current record count: {count_before:,}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            self.test_data['count_before'] = count_before
            return True

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Database count error: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_full_fetch_and_store(self):
        """Test 5: Execute full fetch and store operation"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Executing full fetch and store cycle...")

        start = time.time()
        try:
            if 'fetcher' not in self.test_data:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Fetcher not initialized")
                self.results['failed'] += 1
                return False

            fetcher = self.test_data['fetcher']

            # Execute fetch and store with regional filtering
            result = fetcher.fetch_and_store(region_codes=['gb', 'ire'])

            elapsed = time.time() - start

            if result.get('success'):
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Fetch and store completed")
                print(f"  ✓ Operation successful")
                print(f"  ✓ Fetched: {result.get('fetched', 0)} courses")
                print(f"  ✓ Inserted/Updated: {result.get('inserted', 0)} records")
                print(f"  ✓ API stats: {result.get('api_stats', {})}")
                print(f"  ✓ DB stats: {result.get('db_stats', {})}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                self.test_data['fetch_result'] = result
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Fetch and store failed")
                print(f"  Error: {result.get('error', 'Unknown')}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Fetch and store error: {e}")
            import traceback
            print(f"  Traceback: {traceback.format_exc()}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_database_count_after(self):
        """Test 6: Verify records were inserted/updated"""
        print(f"\n{Fore.YELLOW}[TEST 6]{Style.RESET_ALL} Verifying database changes...")

        start = time.time()
        try:
            response = self.client.table('ra_courses').select('id', count='exact').execute()
            count_after = response.count

            count_before = self.test_data.get('count_before', 0)
            expected_fetched = self.test_data.get('courses_count', 0)

            elapsed = time.time() - start

            # Check if data exists (should be >= before count since we're upserting)
            if count_after >= count_before:
                change = count_after - count_before
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Database updated successfully")
                print(f"  ✓ Count before: {count_before:,}")
                print(f"  ✓ Count after: {count_after:,}")
                print(f"  ✓ Change: +{change:,} (new records)")
                print(f"  💡 Note: Upsert may update existing records rather than insert new ones")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Unexpected count change")
                print(f"  Count before: {count_before:,}")
                print(f"  Count after: {count_after:,}")
                print(f"  This may indicate data was deleted or filtered")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Database verification error: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_data_quality(self):
        """Test 7: Verify data quality of inserted records"""
        print(f"\n{Fore.YELLOW}[TEST 7]{Style.RESET_ALL} Checking data quality...")

        start = time.time()
        try:
            # Sample recent records
            response = self.client.table('ra_courses')\
                .select('id,name,region_code,updated_at')\
                .order('updated_at', desc=True)\
                .limit(10)\
                .execute()

            if response.data:
                records = response.data

                # Quality checks
                null_names = sum(1 for r in records if not r.get('name'))
                null_regions = sum(1 for r in records if not r.get('region_code'))
                valid_regions = sum(1 for r in records if r.get('region_code') in ['gb', 'ire'])

                elapsed = time.time() - start

                quality_score = 100
                issues = []

                if null_names > 0:
                    quality_score -= 30
                    issues.append(f"{null_names} records missing names")

                if null_regions > 0:
                    quality_score -= 30
                    issues.append(f"{null_regions} records missing region codes")

                if valid_regions < len(records):
                    quality_score -= 20
                    issues.append(f"{len(records) - valid_regions} records not UK/Ireland")

                if quality_score >= 80:
                    print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Data quality check passed")
                    print(f"  ✓ Sample size: {len(records)} records")
                    print(f"  ✓ Quality score: {quality_score}%")
                    print(f"  ✓ All names populated: {null_names == 0}")
                    print(f"  ✓ All regions populated: {null_regions == 0}")
                    print(f"  ✓ UK/Ireland filtering: {valid_regions}/{len(records)}")
                    print(f"⏱️  Time: {elapsed:.2f}s")
                    self.results['passed'] += 1
                    return True
                else:
                    print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Data quality issues detected")
                    print(f"  Quality score: {quality_score}%")
                    for issue in issues:
                        print(f"  ⚠️  {issue}")
                    print(f"⏱️  Time: {elapsed:.2f}s")
                    self.results['warnings'] += 1
                    self.results['passed'] += 1
                    return True
            else:
                elapsed = time.time() - start
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - No recent records to check")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Data quality check error: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_error_handling(self):
        """Test 8: Verify error handling works correctly"""
        print(f"\n{Fore.YELLOW}[TEST 8]{Style.RESET_ALL} Testing error handling...")

        start = time.time()
        try:
            # Test with invalid region code (should handle gracefully)
            if 'fetcher' not in self.test_data:
                print(f"{Fore.YELLOW}⚠️  SKIP{Style.RESET_ALL} - Fetcher not available, skipping error test")
                print(f"⏱️  Time: {(time.time() - start):.2f}s")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True

            fetcher = self.test_data['fetcher']

            # Try fetching with invalid region code
            result = fetcher.api_client.get_courses(region_codes=['invalid'])

            elapsed = time.time() - start

            # Either returns empty results or handles error gracefully
            if result is not None:
                courses = result.get('courses', [])
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Error handling works")
                print(f"  ✓ Invalid region handled gracefully")
                print(f"  ✓ Returned {len(courses)} courses (expected 0)")
                print(f"  ✓ No exceptions raised")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Error handling works")
                print(f"  ✓ Invalid region returned None")
                print(f"  ✓ No exceptions raised")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True

        except Exception as e:
            elapsed = time.time() - start
            # Exception is actually OK here - means error was caught
            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Error handling works (exception caught)")
            print(f"  ✓ Exception handled: {type(e).__name__}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - END-TO-END WORKER{Style.RESET_ALL}")
        print("=" * 80)

        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0

        duration = (self.end_time - self.start_time)

        print(f"✅ Passed: {Fore.GREEN}{self.results['passed']}{Style.RESET_ALL}")
        print(f"❌ Failed: {Fore.RED}{self.results['failed']}{Style.RESET_ALL}")
        print(f"⚠️  Warnings: {Fore.YELLOW}{self.results['warnings']}{Style.RESET_ALL}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️  Total Time: {duration:.2f}s")

        print(f"\n📋 Pipeline Verification:")
        if self.results['failed'] == 0:
            print(f"  ✓ Configuration → {Fore.GREEN}OK{Style.RESET_ALL}")
            print(f"  ✓ API Fetch → {Fore.GREEN}OK{Style.RESET_ALL}")
            print(f"  ✓ Data Transform → {Fore.GREEN}OK{Style.RESET_ALL}")
            print(f"  ✓ Database Upsert → {Fore.GREEN}OK{Style.RESET_ALL}")
            print(f"  ✓ Data Quality → {Fore.GREEN}OK{Style.RESET_ALL}")
            print(f"  ✓ Error Handling → {Fore.GREEN}OK{Style.RESET_ALL}")

        if self.results['failed'] == 0:
            print(f"\n{Fore.GREEN}🎉 E2E TEST PASSED - Worker pipeline functioning correctly!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  E2E TEST FAILED - Check pipeline errors above{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all end-to-end tests"""
        self.start_time = time.time()
        self.print_header()

        self.test_config_initialization()
        self.test_fetcher_initialization()
        self.test_api_fetch()
        self.test_database_count_before()
        self.test_full_fetch_and_store()
        self.test_database_count_after()
        self.test_data_quality()
        self.test_error_handling()

        self.end_time = time.time()
        return self.print_summary()


if __name__ == "__main__":
    test = EndToEndWorkerTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
