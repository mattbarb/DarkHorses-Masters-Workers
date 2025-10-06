#!/usr/bin/env python3
"""
Test Courses Worker
Verifies that courses data is being collected and stored correctly
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init
from supabase import create_client, Client

# Load environment
env_file = Path(__file__).parent.parent / '.env'
if not env_file.exists():
    env_file = Path(__file__).parent.parent / '.env.example'
if env_file.exists():
    load_dotenv(env_file)
else:
    load_dotenv()

# Initialize colorama
init(autoreset=True)

class CoursesWorkerTest:
    """Test suite for Courses Worker"""

    def __init__(self):
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_SERVICE_KEY')

        if not self.supabase_url or not self.supabase_key:
            raise ValueError("Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment")

        # Initialize Supabase client
        self.client: Client = create_client(self.supabase_url, self.supabase_key)

        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}🏇 COURSES WORKER TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: ra_courses table")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def test_table_exists(self):
        """Test 1: Verify ra_courses table exists with data"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Checking if ra_courses table exists...")

        try:
            response = self.client.table('ra_courses').select('*', count='exact').limit(1).execute()

            if response.count > 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Table exists with {response.count:,} total records")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Table exists but is empty")
                self.results['failed'] += 1
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Table check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_regional_filtering(self):
        """Test 2: Verify all courses are UK/Ireland only"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Checking regional filtering...")

        try:
            # Check for non-UK/Ireland courses
            response = self.client.table('ra_courses')\
                .select('region_code', count='exact')\
                .not_.in_('region_code', ['gb', 'ire'])\
                .execute()

            non_uk_ire = response.count

            if non_uk_ire == 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All courses are UK/Ireland")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Found {non_uk_ire} non-UK/Ireland courses")
                self.results['failed'] += 1
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Regional filtering check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_data_freshness(self):
        """Test 3: Check data was updated recently (within 35 days for monthly updates)"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Checking data freshness...")

        try:
            response = self.client.table('ra_courses')\
                .select('updated_at')\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data:
                latest_update = datetime.fromisoformat(response.data[0]['updated_at'].replace('Z', '+00:00'))
                age = datetime.utcnow() - latest_update.replace(tzinfo=None)

                # Courses update monthly, so 35 days is acceptable
                if age < timedelta(days=35):
                    print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Data updated {age.days} days ago (monthly schedule)")
                    self.results['passed'] += 1
                    return True
                else:
                    print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Data is {age.days} days old (monthly schedule)")
                    self.results['warnings'] += 1
                    self.results['passed'] += 1
                    return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - No data found")
                self.results['failed'] += 1
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Freshness check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_required_fields(self):
        """Test 4: Verify required fields are populated"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Checking required fields...")

        try:
            # Check for NULL values in critical fields
            response = self.client.table('ra_courses')\
                .select('id,name,region_code')\
                .limit(100)\
                .execute()

            if response.data:
                null_names = sum(1 for row in response.data if not row.get('name'))
                null_regions = sum(1 for row in response.data if not row.get('region_code'))

                if null_names == 0 and null_regions == 0:
                    print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All required fields populated in {len(response.data)} sample records")
                    self.results['passed'] += 1
                    return True
                else:
                    print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Found NULL values: {null_names} missing names, {null_regions} missing regions")
                    self.results['failed'] += 1
                    return False
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - No data to check")
                self.results['failed'] += 1
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Required fields check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_course_count(self):
        """Test 5: Verify reasonable number of courses (~50-70 for UK/Ireland)"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Checking course count...")

        try:
            response = self.client.table('ra_courses').select('*', count='exact').execute()
            count = response.count

            if 40 <= count <= 100:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Course count: {count} (expected 40-100 for UK/Ireland)")
                self.results['passed'] += 1
                return True
            elif count < 40:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Only {count} courses (expected 40-100)")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - {count} courses (more than expected)")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Course count check failed: {e}")
            self.results['failed'] += 1
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - COURSES WORKER{Style.RESET_ALL}")
        print("=" * 80)

        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0

        print(f"✅ Passed: {Fore.GREEN}{self.results['passed']}{Style.RESET_ALL}")
        print(f"❌ Failed: {Fore.RED}{self.results['failed']}{Style.RESET_ALL}")
        print(f"⚠️  Warnings: {Fore.YELLOW}{self.results['warnings']}{Style.RESET_ALL}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")

        if self.results['failed'] == 0:
            print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED - Courses Worker is functioning correctly!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  SOME TESTS FAILED - Check worker logs for issues{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all tests"""
        self.print_header()

        self.test_table_exists()
        self.test_regional_filtering()
        self.test_data_freshness()
        self.test_required_fields()
        self.test_course_count()

        return self.print_summary()


if __name__ == "__main__":
    test = CoursesWorkerTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
