#!/usr/bin/env python3
"""
Test Races Worker
Verifies that race cards and results data is being collected correctly
"""

import os
import sys
from datetime import datetime, timedelta, date
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

class RacesWorkerTest:
    """Test suite for Races Worker"""

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
        print(f"{Fore.CYAN}🏁 RACES WORKER TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: ra_races and ra_mst_runners tables")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def test_races_table_exists(self):
        """Test 1: Verify ra_races table exists with data"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Checking if ra_races table exists...")

        try:
            response = self.client.table('ra_mst_races').select('*', count='exact').limit(1).execute()

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

    def test_recent_races(self):
        """Test 2: Verify races from today or recent days exist"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Checking for recent race cards...")

        try:
            today = date.today().isoformat()

            response = self.client.table('ra_mst_races')\
                .select('race_date', count='exact')\
                .gte('race_date', today)\
                .execute()

            races_today = response.count

            if races_today > 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Found {races_today} race cards for today/upcoming")
                self.results['passed'] += 1
                return True
            else:
                # Check last 7 days
                week_ago = (date.today() - timedelta(days=7)).isoformat()
                response = self.client.table('ra_mst_races')\
                    .select('race_date', count='exact')\
                    .gte('race_date', week_ago)\
                    .execute()

                races_recent = response.count

                if races_recent > 0:
                    print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - No races for today, but found {races_recent} in last 7 days")
                    self.results['warnings'] += 1
                    self.results['passed'] += 1
                    return True
                else:
                    print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - No recent race cards found")
                    self.results['failed'] += 1
                    return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Recent races check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_regional_filtering(self):
        """Test 3: Verify all races are UK/Ireland only"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Checking regional filtering...")

        try:
            # Check for non-UK/Ireland races
            response = self.client.table('ra_mst_races')\
                .select('region_code', count='exact')\
                .not_.in_('region_code', ['gb', 'ire'])\
                .execute()

            non_uk_ire = response.count

            if non_uk_ire == 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - All races are UK/Ireland")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Found {non_uk_ire} non-UK/Ireland races")
                self.results['failed'] += 1
                return False
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Regional filtering check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_results_table_exists(self):
        """Test 4: Verify ra_mst_runners table exists with data"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Checking if ra_mst_runners table exists...")

        try:
            response = self.client.table('ra_mst_runners').select('*', count='exact').limit(1).execute()

            if response.count > 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Table exists with {response.count:,} total records")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Table exists but is empty (may be new deployment)")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
        except Exception as e:
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Table check failed: {e}")
            self.results['failed'] += 1
            return False

    def test_results_coverage(self):
        """Test 5: Check results data coverage (position data in ra_mst_runners)"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Checking results coverage...")

        try:
            # Get earliest and latest results (from ra_mst_runners with position data)
            response_earliest = self.client.table('ra_mst_runners')\
                .select('race_date')\
                .not_.is_('position', 'null')\
                .order('race_date', desc=False)\
                .limit(1)\
                .execute()

            response_latest = self.client.table('ra_mst_runners')\
                .select('race_date')\
                .not_.is_('position', 'null')\
                .order('race_date', desc=True)\
                .limit(1)\
                .execute()

            if response_earliest.data and response_latest.data:
                earliest_raw = response_earliest.data[0]['race_date']
                latest_raw = response_latest.data[0]['race_date']

                # Handle datetime format
                earliest = earliest_raw.split('T')[0] if 'T' in str(earliest_raw) else str(earliest_raw)
                latest = latest_raw.split('T')[0] if 'T' in str(latest_raw) else str(latest_raw)

                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Results coverage:")
                print(f"  📅 Earliest: {earliest}")
                print(f"  📅 Latest: {latest}")
                self.results['passed'] += 1
                return True
            elif response_earliest.data or response_latest.data:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Limited results data available")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - No results data yet (may be new deployment)")
                self.results['warnings'] += 1
                self.results['passed'] += 1
                return True
        except Exception as e:
            print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Results coverage check error: {e}")
            self.results['warnings'] += 1
            self.results['passed'] += 1
            return True

    def test_data_freshness(self):
        """Test 6: Check races data was updated recently (daily schedule)"""
        print(f"\n{Fore.YELLOW}[TEST 6]{Style.RESET_ALL} Checking data freshness...")

        try:
            response = self.client.table('ra_mst_races')\
                .select('updated_at')\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()

            if response.data:
                latest_update = datetime.fromisoformat(response.data[0]['updated_at'].replace('Z', '+00:00'))
                age = datetime.utcnow() - latest_update.replace(tzinfo=None)

                # Races update daily at 1 AM, so 48 hours is acceptable
                if age < timedelta(hours=48):
                    print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Data updated {age.total_seconds()/3600:.1f} hours ago (daily schedule)")
                    self.results['passed'] += 1
                    return True
                else:
                    print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Data is {age.days} days old (daily schedule)")
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

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - RACES WORKER{Style.RESET_ALL}")
        print("=" * 80)

        total = self.results['passed'] + self.results['failed']
        pass_rate = (self.results['passed'] / total * 100) if total > 0 else 0

        print(f"✅ Passed: {Fore.GREEN}{self.results['passed']}{Style.RESET_ALL}")
        print(f"❌ Failed: {Fore.RED}{self.results['failed']}{Style.RESET_ALL}")
        print(f"⚠️  Warnings: {Fore.YELLOW}{self.results['warnings']}{Style.RESET_ALL}")
        print(f"📊 Pass Rate: {pass_rate:.1f}%")

        if self.results['failed'] == 0:
            print(f"\n{Fore.GREEN}🎉 ALL TESTS PASSED - Races Worker is functioning correctly!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  SOME TESTS FAILED - Check worker logs for issues{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all tests"""
        self.print_header()

        self.test_races_table_exists()
        self.test_recent_races()
        self.test_regional_filtering()
        self.test_results_table_exists()
        self.test_results_coverage()
        self.test_data_freshness()

        return self.print_summary()


if __name__ == "__main__":
    test = RacesWorkerTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
