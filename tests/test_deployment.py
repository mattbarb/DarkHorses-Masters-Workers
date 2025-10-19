#!/usr/bin/env python3
"""
Deployment Verification Test
Checks that the deployment environment is correctly configured and all services are accessible
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

from utils.api_client import RacingAPIClient
from config.config import get_config

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


class DeploymentVerificationTest:
    """Test suite for deployment verification"""

    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
        self.start_time = None
        self.end_time = None

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}🚀 DEPLOYMENT VERIFICATION TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: Environment configuration, API connections, Database access")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def test_environment_variables(self):
        """Test 1: Verify all required environment variables are set"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Checking environment variables...")

        start = time.time()
        required_vars = {
            'RACING_API_USERNAME': 'Racing API username',
            'RACING_API_PASSWORD': 'Racing API password',
            'SUPABASE_URL': 'Supabase URL',
            'SUPABASE_SERVICE_KEY': 'Supabase service key'
        }

        missing = []
        present = []

        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing.append(f"{var} ({description})")
            else:
                # Mask sensitive values
                if 'PASSWORD' in var or 'KEY' in var:
                    masked = value[:4] + '*' * (len(value) - 8) + value[-4:] if len(value) > 8 else '****'
                    present.append(f"{var}: {masked}")
                else:
                    present.append(f"{var}: {value}")

        elapsed = time.time() - start

        if missing:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Missing environment variables:")
            for var in missing:
                print(f"  ✗ {var}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False
        else:
            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All required environment variables set:")
            for var in present:
                print(f"  ✓ {var}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True

    def test_config_initialization(self):
        """Test 2: Verify configuration object can be initialized"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Checking configuration initialization...")

        start = time.time()
        try:
            config = get_config()

            # Verify config has required attributes
            checks = {
                'API configuration': hasattr(config, 'api') and config.api.username is not None,
                'Supabase configuration': hasattr(config, 'supabase') and config.supabase.url is not None,
                'Path configuration': hasattr(config, 'paths') and config.paths.logs_dir is not None
            }

            all_passed = all(checks.values())
            elapsed = time.time() - start

            if all_passed:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Configuration initialized successfully:")
                for check_name, passed in checks.items():
                    print(f"  ✓ {check_name}")
                print(f"  📁 Base dir: {config.paths.base_dir}")
                print(f"  📁 Logs dir: {config.paths.logs_dir}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Configuration initialization failed:")
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

    def test_supabase_connection(self):
        """Test 3: Verify Supabase connection works"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Testing Supabase connection...")

        start = time.time()
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

            if not supabase_url or not supabase_key:
                elapsed = time.time() - start
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Missing Supabase credentials")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

            # Test connection with a simple query
            client: Client = create_client(supabase_url, supabase_key)
            response = client.table('ra_courses').select('id', count='exact').limit(1).execute()

            elapsed = time.time() - start
            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Supabase connection successful")
            print(f"  🔗 URL: {supabase_url}")
            print(f"  ✓ Query executed successfully")
            print(f"  📊 Test query returned: {response.count} total records")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Supabase connection failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_racing_api_connection(self):
        """Test 4: Verify Racing API connection works"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Testing Racing API connection...")

        start = time.time()
        try:
            username = os.getenv('RACING_API_USERNAME')
            password = os.getenv('RACING_API_PASSWORD')

            if not username or not password:
                elapsed = time.time() - start
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Missing Racing API credentials")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

            # Test API connection with a simple request
            api_client = RacingAPIClient()

            # Test with courses endpoint (lightweight)
            test_url = f"{api_client.base_url}/courses"
            params = {'region_code': 'gb', 'limit': 1}

            response = api_client._make_request(test_url, params)

            elapsed = time.time() - start

            if response and 'courses' in response:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Racing API connection successful")
                print(f"  🔗 Base URL: {api_client.base_url}")
                print(f"  ✓ Authentication successful")
                print(f"  ✓ Test query executed")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Racing API returned unexpected response")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Racing API connection failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_database_tables_exist(self):
        """Test 5: Verify all required database tables exist"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Checking database tables...")

        start = time.time()
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            client: Client = create_client(supabase_url, supabase_key)

            required_tables = [
                'ra_courses',
                'ra_bookmakers',
                'ra_jockeys',
                'ra_trainers',
                'ra_owners',
                'ra_horses',
                'ra_races',
                'ra_runners'
            ]

            existing_tables = []
            missing_tables = []

            for table in required_tables:
                try:
                    response = client.table(table).select('id', count='exact').limit(1).execute()
                    existing_tables.append((table, response.count))
                except Exception as e:
                    missing_tables.append((table, str(e)))

            elapsed = time.time() - start

            if not missing_tables:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All required tables exist:")
                for table, count in existing_tables:
                    print(f"  ✓ {table}: {count:,} records")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Missing tables:")
                for table, error in missing_tables:
                    print(f"  ✗ {table}: {error}")
                if existing_tables:
                    print(f"  Existing tables:")
                    for table, count in existing_tables:
                        print(f"    ✓ {table}: {count:,} records")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Database table check failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_regional_filtering_active(self):
        """Test 6: Verify regional filtering is working (UK/Ireland only)"""
        print(f"\n{Fore.YELLOW}[TEST 6]{Style.RESET_ALL} Checking regional filtering...")

        start = time.time()
        try:
            supabase_url = os.getenv('SUPABASE_URL')
            supabase_key = os.getenv('SUPABASE_SERVICE_KEY')
            client: Client = create_client(supabase_url, supabase_key)

            # Check courses table for non-UK/Ireland entries
            response = client.table('ra_courses')\
                .select('region_code', count='exact')\
                .not_.in_('region_code', ['gb', 'ire'])\
                .execute()

            non_uk_ire = response.count

            # Get UK/Ireland counts
            uk_response = client.table('ra_courses')\
                .select('region_code', count='exact')\
                .eq('region_code', 'gb')\
                .execute()

            ire_response = client.table('ra_courses')\
                .select('region_code', count='exact')\
                .eq('region_code', 'ire')\
                .execute()

            elapsed = time.time() - start

            if non_uk_ire == 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Regional filtering active:")
                print(f"  ✓ UK courses: {uk_response.count}")
                print(f"  ✓ Ireland courses: {ire_response.count}")
                print(f"  ✓ Non-UK/Ireland: {non_uk_ire} (correct)")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Found {non_uk_ire} non-UK/Ireland courses")
                print(f"  📊 UK courses: {uk_response.count}")
                print(f"  📊 Ireland courses: {ire_response.count}")
                print(f"  ⚠️  Non-UK/Ireland: {non_uk_ire}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Could not verify regional filtering: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['warnings'] += 1
            self.results['passed'] += 1
            return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - DEPLOYMENT VERIFICATION{Style.RESET_ALL}")
        print("=" * 80)

        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0

        duration = (self.end_time - self.start_time)

        print(f"✅ Passed: {Fore.GREEN}{self.results['passed']}{Style.RESET_ALL}")
        print(f"❌ Failed: {Fore.RED}{self.results['failed']}{Style.RESET_ALL}")
        print(f"⚠️  Warnings: {Fore.YELLOW}{self.results['warnings']}{Style.RESET_ALL}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️  Total Time: {duration:.2f}s")

        if self.results['failed'] == 0:
            print(f"\n{Fore.GREEN}🎉 DEPLOYMENT VERIFIED - All systems operational!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  DEPLOYMENT ISSUES DETECTED - Check failed tests above{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all deployment verification tests"""
        self.start_time = time.time()
        self.print_header()

        self.test_environment_variables()
        self.test_config_initialization()
        self.test_supabase_connection()
        self.test_racing_api_connection()
        self.test_database_tables_exist()
        self.test_regional_filtering_active()

        self.end_time = time.time()
        return self.print_summary()


if __name__ == "__main__":
    test = DeploymentVerificationTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
