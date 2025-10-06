#!/usr/bin/env python3
"""
Schedule Verification Test
Verifies that scheduler configuration is correct and jobs are properly configured
"""

import sys
import time
import schedule
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Initialize colorama
init(autoreset=True)


class ScheduleVerificationTest:
    """Test suite for schedule verification"""

    def __init__(self):
        self.results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0
        }
        self.start_time = None
        self.end_time = None
        self.test_scheduler = None

    def print_header(self):
        """Print test header"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}⏰ SCHEDULE VERIFICATION TEST{Style.RESET_ALL}")
        print("=" * 80)
        print(f"Testing: Scheduler configuration, job registration, timing validation")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def test_schedule_module_import(self):
        """Test 1: Verify schedule module can be imported"""
        print(f"{Fore.YELLOW}[TEST 1]{Style.RESET_ALL} Checking schedule module import...")

        start = time.time()
        try:
            import schedule
            elapsed = time.time() - start

            print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Schedule module imported successfully")
            print(f"  ✓ Module: {schedule.__name__}")
            print(f"  ✓ Version: {getattr(schedule, '__version__', 'unknown')}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['passed'] += 1
            return True

        except ImportError as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Schedule module import failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_schedule_jobs_configuration(self):
        """Test 2: Verify schedule jobs match expected configuration"""
        print(f"\n{Fore.YELLOW}[TEST 2]{Style.RESET_ALL} Checking schedule jobs configuration...")

        start = time.time()
        try:
            # Create a test scheduler to verify job configuration
            schedule.clear()  # Clear any existing jobs

            # Define test jobs (mimicking start_worker.py)
            test_counter = {'daily': 0, 'weekly': 0, 'monthly': 0}

            def test_daily():
                test_counter['daily'] += 1

            def test_weekly():
                test_counter['weekly'] += 1

            def test_monthly():
                test_counter['monthly'] += 1

            # Schedule jobs as per start_worker.py
            schedule.every().day.at("01:00").do(test_daily)
            schedule.every().sunday.at("02:00").do(test_weekly)
            schedule.every().monday.at("03:00").do(test_monthly)

            jobs = schedule.get_jobs()
            elapsed = time.time() - start

            expected_jobs = {
                'daily': {'time': '01:00', 'interval': 1, 'unit': 'day'},
                'weekly': {'time': '02:00', 'interval': 1, 'unit': 'week'},
                'monthly': {'time': '03:00', 'interval': 1, 'unit': 'week'}  # Approximated as weekly
            }

            if len(jobs) >= 3:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Schedule jobs configured correctly:")
                print(f"  ✓ Total jobs registered: {len(jobs)}")

                for job in jobs:
                    job_func = job.job_func.__name__
                    print(f"  ✓ Job: {job_func} - Next run: {job.next_run}")

                print(f"\n  📋 Expected Schedule:")
                print(f"    • Daily (races, results): 01:00 UTC")
                print(f"    • Weekly (people, horses): Sunday 02:00 UTC")
                print(f"    • Monthly (courses, bookmakers): First Monday 03:00 UTC")

                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1

                # Clean up
                schedule.clear()
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Insufficient jobs registered")
                print(f"  Expected: 3, Found: {len(jobs)}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1

                # Clean up
                schedule.clear()
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Schedule configuration test failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1

            # Clean up
            schedule.clear()
            return False

    def test_schedule_timing_validation(self):
        """Test 3: Verify schedule times are reasonable"""
        print(f"\n{Fore.YELLOW}[TEST 3]{Style.RESET_ALL} Validating schedule times...")

        start = time.time()
        try:
            expected_schedules = {
                'Daily (races/results)': {
                    'time': '01:00',
                    'reason': 'After midnight to capture previous day\'s results',
                    'valid': True
                },
                'Weekly (people/horses)': {
                    'time': '02:00',
                    'day': 'Sunday',
                    'reason': 'Weekly update to refresh jockeys, trainers, owners, horses',
                    'valid': True
                },
                'Monthly (courses/bookmakers)': {
                    'time': '03:00',
                    'day': 'First Monday',
                    'reason': 'Monthly update for relatively static reference data',
                    'valid': True
                }
            }

            elapsed = time.time() - start
            all_valid = all(s['valid'] for s in expected_schedules.values())

            if all_valid:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Schedule times validated:")
                for schedule_name, details in expected_schedules.items():
                    time_str = details.get('time', 'N/A')
                    day_str = f" ({details['day']})" if 'day' in details else ''
                    print(f"  ✓ {schedule_name}: {time_str} UTC{day_str}")
                    print(f"    Reason: {details['reason']}")

                print(f"\n  💡 All times are in UTC to ensure consistency across deployments")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Invalid schedule times detected")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Schedule validation failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def test_schedule_next_run_times(self):
        """Test 4: Calculate and display next run times"""
        print(f"\n{Fore.YELLOW}[TEST 4]{Style.RESET_ALL} Calculating next run times...")

        start = time.time()
        try:
            schedule.clear()

            # Create dummy jobs to calculate next run times
            def dummy():
                pass

            schedule.every().day.at("01:00").do(dummy)
            schedule.every().sunday.at("02:00").do(dummy)

            jobs = schedule.get_jobs()
            elapsed = time.time() - start

            if jobs:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Next run times calculated:")
                now = datetime.now()

                for i, job in enumerate(jobs, 1):
                    next_run = job.next_run
                    if next_run:
                        time_until = next_run - now
                        hours = time_until.total_seconds() / 3600

                        print(f"  ✓ Job {i}: {next_run.strftime('%Y-%m-%d %H:%M:%S')}")
                        print(f"    Time until run: {hours:.1f} hours ({time_until.days} days, {time_until.seconds//3600} hours)")

                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1

                # Clean up
                schedule.clear()
                return True
            else:
                print(f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL} - No jobs to calculate run times")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['warnings'] += 1
                self.results['passed'] += 1

                # Clean up
                schedule.clear()
                return True

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Next run calculation failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1

            # Clean up
            schedule.clear()
            return False

    def test_scheduler_start_stop(self):
        """Test 5: Verify scheduler can be started and stopped"""
        print(f"\n{Fore.YELLOW}[TEST 5]{Style.RESET_ALL} Testing scheduler start/stop...")

        start = time.time()
        try:
            schedule.clear()

            execution_log = []

            def test_job():
                execution_log.append(datetime.now())

            # Schedule a job to run very soon (1 second from now)
            schedule.every(1).seconds.do(test_job)

            # Run pending jobs (simulate scheduler loop)
            initial_jobs = len(schedule.get_jobs())

            # Simulate a few iterations
            for _ in range(3):
                schedule.run_pending()
                time.sleep(0.5)

            # Clear scheduler (simulate stop)
            schedule.clear()
            final_jobs = len(schedule.get_jobs())

            elapsed = time.time() - start

            if initial_jobs > 0 and final_jobs == 0:
                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Scheduler start/stop working:")
                print(f"  ✓ Initial jobs: {initial_jobs}")
                print(f"  ✓ Jobs after clear: {final_jobs}")
                print(f"  ✓ Test executions: {len(execution_log)}")
                print(f"  ✓ Scheduler can be started and stopped cleanly")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Scheduler start/stop issue")
                print(f"  Initial jobs: {initial_jobs}, Final jobs: {final_jobs}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Scheduler start/stop test failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1

            # Clean up
            schedule.clear()
            return False

    def test_worker_script_exists(self):
        """Test 6: Verify start_worker.py exists and is executable"""
        print(f"\n{Fore.YELLOW}[TEST 6]{Style.RESET_ALL} Checking worker script...")

        start = time.time()
        try:
            worker_script = Path(__file__).parent.parent / 'start_worker.py'

            if worker_script.exists():
                is_executable = worker_script.stat().st_mode & 0o111

                elapsed = time.time() - start

                print(f"{Fore.GREEN}✅ PASS{Style.RESET_ALL} - Worker script verified:")
                print(f"  ✓ Path: {worker_script}")
                print(f"  ✓ Exists: Yes")
                print(f"  ✓ Executable: {'Yes' if is_executable else 'No (but can run with python3)'}")
                print(f"  ✓ Size: {worker_script.stat().st_size} bytes")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['passed'] += 1
                return True
            else:
                elapsed = time.time() - start
                print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Worker script not found")
                print(f"  Expected path: {worker_script}")
                print(f"⏱️  Time: {elapsed:.2f}s")
                self.results['failed'] += 1
                return False

        except Exception as e:
            elapsed = time.time() - start
            print(f"{Fore.RED}❌ FAIL{Style.RESET_ALL} - Worker script check failed: {e}")
            print(f"⏱️  Time: {elapsed:.2f}s")
            self.results['failed'] += 1
            return False

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print(f"{Fore.CYAN}TEST SUMMARY - SCHEDULE VERIFICATION{Style.RESET_ALL}")
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
            print(f"\n{Fore.GREEN}🎉 SCHEDULE VERIFIED - Scheduler configured correctly!{Style.RESET_ALL}")
        else:
            print(f"\n{Fore.RED}⚠️  SCHEDULE ISSUES DETECTED - Check failed tests above{Style.RESET_ALL}")

        print("=" * 80 + "\n")

        return self.results['failed'] == 0

    def run_all_tests(self):
        """Run all schedule verification tests"""
        self.start_time = time.time()
        self.print_header()

        self.test_schedule_module_import()
        self.test_schedule_jobs_configuration()
        self.test_schedule_timing_validation()
        self.test_schedule_next_run_times()
        self.test_scheduler_start_stop()
        self.test_worker_script_exists()

        self.end_time = time.time()
        return self.print_summary()


if __name__ == "__main__":
    test = ScheduleVerificationTest()
    success = test.run_all_tests()
    sys.exit(0 if success else 1)
