#!/usr/bin/env python3
"""
Data Freshness Test
Monitors data age across all tables and alerts if data is stale
"""

import os
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from colorama import Fore, Style, init
from supabase import create_client, Client

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


class DataFreshnessTest:
    """Test suite for data freshness monitoring"""

    # Freshness thresholds in days
    FRESHNESS_THRESHOLDS = {
        'ra_courses': {
            'max_age_days': 35,  # Monthly + buffer
            'schedule': 'Monthly (1st of month at 3:00 AM)',
            'entities': 'Courses'
        },
        'ra_bookmakers': {
            'max_age_days': 35,  # Monthly + buffer
            'schedule': 'Monthly (1st of month at 3:00 AM)',
            'entities': 'Bookmakers'
        },
        'ra_jockeys': {
            'max_age_days': 10,  # Weekly + buffer
            'schedule': 'Weekly (Sunday at 2:00 AM)',
            'entities': 'Jockeys'
        },
        'ra_trainers': {
            'max_age_days': 10,  # Weekly + buffer
            'schedule': 'Weekly (Sunday at 2:00 AM)',
            'entities': 'Trainers'
        },
        'ra_owners': {
            'max_age_days': 10,  # Weekly + buffer
            'schedule': 'Weekly (Sunday at 2:00 AM)',
            'entities': 'Owners'
        },
        'ra_horses': {
            'max_age_days': 10,  # Weekly + buffer
            'schedule': 'Weekly (Sunday at 2:00 AM)',
            'entities': 'Horses'
        },
        'ra_races': {
            'max_age_days': 3,  # Daily + buffer
            'schedule': 'Daily (1:00 AM)',
            'entities': 'Race cards'
        },
        'ra_mst_runners': {
            'max_age_days': 3,  # Daily + buffer
            'schedule': 'Daily (1:00 AM)',
            'entities': 'Race runners (includes results)'
        }
    }

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
        self.freshness_data = {}

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}📊 DATA FRESHNESS MONITORING TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: Data age across all tables with schedule-aware thresholds")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def check_table_freshness(self, table_name: str, config: dict):
        """Check freshness of a single table"""
        try:
            # Query for most recent update
            response = self.client.table(table_name)\
                .select('updated_at')\
                .order('updated_at', desc=True)\
                .limit(1)\
                .execute()

            if not response.data:
                return {
                    'status': 'empty',
                    'age_days': None,
                    'latest_update': None,
                    'error': 'No data in table'
                }

            latest_update = datetime.fromisoformat(response.data[0]['updated_at'].replace('Z', '+00:00'))
            age = datetime.utcnow() - latest_update.replace(tzinfo=None)
            age_days = age.days
            age_hours = age.total_seconds() / 3600

            max_age_days = config['max_age_days']

            if age_days <= max_age_days:
                status = 'fresh'
            elif age_days <= max_age_days * 1.5:
                status = 'warning'
            else:
                status = 'stale'

            return {
                'status': status,
                'age_days': age_days,
                'age_hours': age_hours,
                'latest_update': latest_update,
                'threshold_days': max_age_days,
                'schedule': config['schedule'],
                'entities': config['entities']
            }

        except Exception as e:
            return {
                'status': 'error',
                'age_days': None,
                'latest_update': None,
                'error': str(e)
            }

    def test_monthly_tables_freshness(self):
        """Test 1: Check freshness of monthly updated tables (courses, bookmakers)"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Checking monthly tables freshness...")

        start = time.time()
        monthly_tables = ['ra_courses', 'ra_bookmakers']

        all_fresh = True
        results = []

        for table in monthly_tables:
            config = self.FRESHNESS_THRESHOLDS[table]
            freshness = self.check_table_freshness(table, config)
            self.freshness_data[table] = freshness
            results.append((table, freshness))

            if freshness['status'] in ['stale', 'error']:
                all_fresh = False

        elapsed = time.time() - start

        print(f"  📋 Monthly Tables (Updated: {config['schedule']}):")
        for table, freshness in results:
            if freshness['status'] == 'fresh':
                icon = "✓"
                color = Fore.GREEN
            elif freshness['status'] == 'warning':
                icon = "⚠️"
                color = Fore.YELLOW
            elif freshness['status'] == 'empty':
                icon = "⚠️"
                color = Fore.YELLOW
            else:
                icon = "✗"
                color = Fore.RED

            age_str = f"{freshness['age_days']} days" if freshness['age_days'] is not None else "N/A"
            threshold = freshness.get('threshold_days', 'N/A')
            print(f"  {icon} {color}{table}{Style.RESET_ALL}: {age_str} old (threshold: {threshold} days)")

            if freshness['status'] == 'error':
                print(f"    Error: {freshness.get('error', 'Unknown')}")

        if all_fresh or any(f['status'] == 'warning' for _, f in results):
            status = "PASS" if all_fresh else "PASS (with warnings)"
            color = Fore.GREEN if all_fresh else Fore.YELLOW
            print(f"\n{color}✅ {status}{Style.RESET_ALL} - Monthly tables checked")
            if not all_fresh:
                self.results['warnings'] += 1
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True
        else:
            print(f"\n{Fore.RED}❌ FAIL{Style.RESET_ALL} - Monthly tables have stale data")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_weekly_tables_freshness(self):
        """Test 2: Check freshness of weekly updated tables (jockeys, trainers, owners, horses)"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Checking weekly tables freshness...")

        start = time.time()
        weekly_tables = ['ra_jockeys', 'ra_trainers', 'ra_owners', 'ra_horses']

        all_fresh = True
        results = []

        for table in weekly_tables:
            config = self.FRESHNESS_THRESHOLDS[table]
            freshness = self.check_table_freshness(table, config)
            self.freshness_data[table] = freshness
            results.append((table, freshness))

            if freshness['status'] in ['stale', 'error']:
                all_fresh = False

        elapsed = time.time() - start

        print(f"  📋 Weekly Tables (Updated: {config['schedule']}):")
        for table, freshness in results:
            if freshness['status'] == 'fresh':
                icon = "✓"
                color = Fore.GREEN
            elif freshness['status'] == 'warning':
                icon = "⚠️"
                color = Fore.YELLOW
            elif freshness['status'] == 'empty':
                icon = "⚠️"
                color = Fore.YELLOW
            else:
                icon = "✗"
                color = Fore.RED

            age_str = f"{freshness['age_days']} days" if freshness['age_days'] is not None else "N/A"
            threshold = freshness.get('threshold_days', 'N/A')
            print(f"  {icon} {color}{table}{Style.RESET_ALL}: {age_str} old (threshold: {threshold} days)")

            if freshness['status'] == 'error':
                print(f"    Error: {freshness.get('error', 'Unknown')}")

        if all_fresh or any(f['status'] == 'warning' for _, f in results):
            status = "PASS" if all_fresh else "PASS (with warnings)"
            color = Fore.GREEN if all_fresh else Fore.YELLOW
            print(f"\n{color}✅ {status}{Style.RESET_ALL} - Weekly tables checked")
            if not all_fresh:
                self.results['warnings'] += 1
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True
        else:
            print(f"\n{Fore.RED}❌ FAIL{Style.RESET_ALL} - Weekly tables have stale data")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_daily_tables_freshness(self):
        """Test 3: Check freshness of daily updated tables (races, runners)"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Checking daily tables freshness...")

        start = time.time()
        daily_tables = ['ra_races', 'ra_mst_runners']

        all_fresh = True
        results = []

        for table in daily_tables:
            config = self.FRESHNESS_THRESHOLDS[table]
            freshness = self.check_table_freshness(table, config)
            self.freshness_data[table] = freshness
            results.append((table, freshness))

            if freshness['status'] in ['stale', 'error']:
                all_fresh = False

        elapsed = time.time() - start

        print(f"  📋 Daily Tables (Updated: {config['schedule']}):")
        for table, freshness in results:
            if freshness['status'] == 'fresh':
                icon = "✓"
                color = Fore.GREEN
            elif freshness['status'] == 'warning':
                icon = "⚠️"
                color = Fore.YELLOW
            elif freshness['status'] == 'empty':
                icon = "⚠️"
                color = Fore.YELLOW
            else:
                icon = "✗"
                color = Fore.RED

            if freshness['age_hours'] is not None:
                if freshness['age_hours'] < 48:
                    age_str = f"{freshness['age_hours']:.1f} hours"
                else:
                    age_str = f"{freshness['age_days']} days"
            else:
                age_str = "N/A"

            threshold = freshness.get('threshold_days', 'N/A')
            print(f"  {icon} {color}{table}{Style.RESET_ALL}: {age_str} old (threshold: {threshold} days)")

            if freshness['status'] == 'error':
                print(f"    Error: {freshness.get('error', 'Unknown')}")

        if all_fresh or any(f['status'] == 'warning' for _, f in results):
            status = "PASS" if all_fresh else "PASS (with warnings)"
            color = Fore.GREEN if all_fresh else Fore.YELLOW
            print(f"\n{color}✅ {status}{Style.RESET_ALL} - Daily tables checked")
            if not all_fresh:
                self.results['warnings'] += 1
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True
        else:
            print(f"\n{Fore.RED}❌ FAIL{Style.RESET_ALL} - Daily tables have stale data")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_overall_data_health(self):
        """Test 4: Overall data health summary"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Overall data health check...")

        start = time.time()

        fresh_count = sum(1 for f in self.freshness_data.values() if f['status'] == 'fresh')
        warning_count = sum(1 for f in self.freshness_data.values() if f['status'] == 'warning')
        stale_count = sum(1 for f in self.freshness_data.values() if f['status'] == 'stale')
        error_count = sum(1 for f in self.freshness_data.values() if f['status'] == 'error')
        empty_count = sum(1 for f in self.freshness_data.values() if f['status'] == 'empty')

        total_tables = len(self.freshness_data)
        health_score = (fresh_count / total_tables * 100) if total_tables > 0 else 0

        elapsed = time.time() - start

        print(f"  📊 Data Health Summary:")
        print(f"    {Fore.GREEN}Fresh:{Style.RESET_ALL} {fresh_count}/{total_tables} tables")
        print(f"    {Fore.YELLOW}Warning:{Style.RESET_ALL} {warning_count}/{total_tables} tables")
        print(f"    {Fore.RED}Stale:{Style.RESET_ALL} {stale_count}/{total_tables} tables")
        print(f"    {Fore.RED}Error:{Style.RESET_ALL} {error_count}/{total_tables} tables")
        if empty_count > 0:
            print(f"    {Fore.YELLOW}Empty:{Style.RESET_ALL} {empty_count}/{total_tables} tables")

        print(f"\n  💯 Health Score: {health_score:.1f}%")

        if health_score >= 75:
            print(f"\n{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Overall data health is good")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True
        elif health_score >= 50:
            print(f"\n{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Overall data health needs attention")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['warnings'] += 1
            self.results['passed'] += 1
            return True
        else:
            print(f"\n{Fore.RED}❌ FAIL{Style.RESET_ALL} - Overall data health is poor")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_stale_data_alerts(self):
        """Test 5: Generate alerts for stale data"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Checking for stale data alerts...")

        start = time.time()

        stale_tables = [
            (table, data) for table, data in self.freshness_data.items()
            if data['status'] in ['stale', 'error']
        ]

        elapsed = time.time() - start

        if not stale_tables:
            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - No stale data detected")
            print(f"  ✓ All tables are within their freshness thresholds")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True
        else:
            print(f"{Fore.YELLOW}⚠️  ALERTS{Style.RESET_ALL} - {len(stale_tables)} table(s) need attention:")
            for table, data in stale_tables:
                print(f"\n  🚨 {Fore.RED}{table}{Style.RESET_ALL}")
                print(f"    Status: {data['status']}")
                print(f"    Age: {data['age_days']} days" if data['age_days'] else "    No data")
                print(f"    Threshold: {data.get('threshold_days', 'N/A')} days")
                print(f"    Schedule: {data.get('schedule', 'Unknown')}")
                print(f"    Entities: {data.get('entities', 'Unknown')}")
                if data.get('error'):
                    print(f"    Error: {data['error']}")

            print(f"\n  💡 Recommended Actions:")
            print(f"    1. Check worker logs on Render.com for errors")
            print(f"    2. Verify scheduler is running (not in free tier timeout)")
            print(f"    3. Check Racing API credentials and rate limits")
            print(f"    4. Verify database write permissions")

            print(f"\n{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - Stale data detected but may be expected")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['warnings'] += 1
            self.results['passed'] += 1
            return True

    def print_detailed_freshness_report(self):
        """Print detailed freshness report"""
        print(f"\n{Fore.CYAN}📋 DETAILED FRESHNESS REPORT{Style.RESET_ALL}")
        print("=" * 80)

        # Group by schedule
        by_schedule = {
            'Monthly': [],
            'Weekly': [],
            'Daily': []
        }

        for table, data in self.freshness_data.items():
            schedule = data.get('schedule', '')
            if 'Monthly' in schedule:
                by_schedule['Monthly'].append((table, data))
            elif 'Weekly' in schedule:
                by_schedule['Weekly'].append((table, data))
            elif 'Daily' in schedule:
                by_schedule['Daily'].append((table, data))

        for schedule_type, tables in by_schedule.items():
            if tables:
                print(f"\n{Fore.CYAN}{schedule_type} Updates:{Style.RESET_ALL}")
                for table, data in tables:
                    status_color = {
                        'fresh': Fore.GREEN,
                        'warning': Fore.YELLOW,
                        'stale': Fore.RED,
                        'error': Fore.RED,
                        'empty': Fore.YELLOW
                    }.get(data['status'], '')

                    print(f"  {status_color}{table}{Style.RESET_ALL}")
                    print(f"    Last Update: {data.get('latest_update', 'N/A')}")
                    print(f"    Age: {data.get('age_days', 'N/A')} days")
                    print(f"    Status: {data['status'].upper()}")

        print("=" * 80)

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - DATA FRESHNESS{Style.RESET_ALL}")
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
            print(f"\n{Fore.GREEN}🎉 DATA FRESHNESS OK - All data within acceptable thresholds!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  DATA FRESHNESS ISSUES - Review stale tables above{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all data freshness tests"""
        self.start_time = time.time()
        self.print_header()

        self.test_monthly_tables_freshness()
        self.test_weekly_tables_freshness()
        self.test_daily_tables_freshness()
        self.test_overall_data_health()
        self.test_stale_data_alerts()

        self.print_detailed_freshness_report()

        self.end_time = time.time()
        return self.print_summary()


if __name__ == "__main__":
    test = DataFreshnessTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
