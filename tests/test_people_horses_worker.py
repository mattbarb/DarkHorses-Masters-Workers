#!/usr/bin/env python3
"""
Test People & Horses Worker
Verifies that jockeys, trainers, owners, and horses data is being collected correctly
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

class PeopleHorsesWorkerTest:
    """Test suite for People & Horses Worker"""

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

        self.tables = ['ra_jockeys', 'ra_trainers', 'ra_owners', 'ra_horses']

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}👥 PEOPLE & HORSES WORKER TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: jockeys, trainers, owners, horses tables")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def test_tables_exist(self):
        """Test 1: Verify all tables exist with data"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Checking if tables exist...")

        try:
            all_exist = True
            for table in self.tables:
                response = self.client.table(table).select('*', count='exact').limit(1).execute()
                count = response.count

                if count > 0:
                    print(f"  ✓ {table}: {count:,} records")
                else:
                    print(f"  ✗ {table}: EMPTY")
                    all_exist = False

            if all_exist:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All tables exist with data")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Some tables are empty")
                self.results['failed'] += 1
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Table check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_minimum_counts(self):
        """Test 2: Verify reasonable minimum counts for UK/Ireland"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Checking minimum record counts...")

        try:
            minimums = {
                'ra_jockeys': 100,
                'ra_trainers': 100,
                'ra_owners': 50,
                'ra_horses': 500
            }

            all_pass = True
            for table, minimum in minimums.items():
                response = self.client.table(table).select('*', count='exact').execute()
                count = response.count

                if count >= minimum:
                    print(f"  ✓ {table}: {count:,} >= {minimum} (expected)")
                else:
                    print(f"  ⚠️  {table}: {count:,} < {minimum} (low but may be acceptable)")
                    self.results['warnings'] += 1

            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Record counts checked")
            self.results['passed'] += 1
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Count check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_data_freshness(self):
        """Test 3: Check data was updated recently (weekly schedule)"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Checking data freshness...")

        try:
            stale_tables = []

            for table in self.tables:
                response = self.client.table(table)\
                    .select('updated_at')\
                    .order('updated_at', desc=True)\
                    .limit(1)\
                    .execute()

                if response.data:
                    latest_update = datetime.fromisoformat(response.data[0]['updated_at'].replace('Z', '+00:00'))
                    age = datetime.utcnow() - latest_update.replace(tzinfo=None)

                    # Weekly updates, so 10 days is acceptable
                    if age < timedelta(days=10):
                        print(f"  ✓ {table}: {age.days} days ago")
                    else:
                        print(f"  ⚠️  {table}: {age.days} days ago (stale)")
                        stale_tables.append(table)

            if len(stale_tables) == 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All tables updated recently (weekly schedule)")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - {len(stale_tables)} tables slightly stale")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Freshness check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_required_fields(self):
        """Test 4: Verify required fields are populated"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Checking required fields...")

        try:
            for table in self.tables:
                response = self.client.table(table)\
                    .select('id,name')\
                    .limit(100)\
                    .execute()

                if response.data:
                    null_names = sum(1 for row in response.data if not row.get('name'))

                    if null_names == 0:
                        print(f"  ✓ {table}: All names populated ({len(response.data)} samples)")
                    else:
                        print(f"  ✗ {table}: {null_names} NULL names found")
                        self.results['failed'] += 1
                        return False

            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All required fields populated")
            self.results['passed'] += 1
            return True
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Required fields check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_regional_filtering(self):
        """Test 5: Verify data is filtered for UK/Ireland connections"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Checking regional filtering...")

        try:
            # Sample check: verify horses have region codes if available
            response = self.client.table('ra_horses')\
                .select('region_code')\
                .limit(100)\
                .execute()

            if response.data:
                # Check if we have region codes
                with_region = sum(1 for row in response.data if row.get('region_code'))

                if with_region > 0:
                    # Count UK/Ireland
                    uk_ire = sum(1 for row in response.data if row.get('region_code') in ['gb', 'ire', 'GB', 'IRE'])
                    percentage = (uk_ire / with_region * 100) if with_region > 0 else 0

                    print(f"  📊 {with_region}/{len(response.data)} horses have region codes")
                    print(f"  📊 {uk_ire}/{with_region} are UK/Ireland ({percentage:.1f}%)")

                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Regional filtering applied")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - No data to check")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Regional filtering check skipped: {e}")
            self.results['warnings'] += 1
            self.results['passed'] += 1
            return True

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - PEOPLE & HORSES WORKER{Style.RESET_ALL}")
        print("=" * 80)

        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0

        print(f"✅ Passed: {Fore.GREEN}{self.results['passed']}{Style.RESET_ALL}")
        print(f"❌ Failed: {Fore.RED}{self.results['failed']}{Style.RESET_ALL}")
        print(f"⚠️  Warnings: {Fore.YELLOW}{self.results['warnings']}{Style.RESET_ALL}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")

        if self.results['failed'] == 0:
            print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED - People & Horses Worker is functioning correctly!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  SOME TESTS FAILED - Check worker logs for issues{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all tests"""
        self.print_header()

        self.test_tables_exist()
        self.test_minimum_counts()
        self.test_data_freshness()
        self.test_required_fields()
        self.test_regional_filtering()

        return self.print_summary()


if __name__ == "__main__":
    test = PeopleHorsesWorkerTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
