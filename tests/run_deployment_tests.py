#!/usr/bin/env python3
"""
Master Deployment Test Runner
Runs all deployment verification tests and generates comprehensive report
"""

import sys
import time
import os
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_deployment import DeploymentVerificationTest
from test_schedule import ScheduleVerificationTest
from test_data_freshness import DataFreshnessTest
from test_e2e_worker import EndToEndWorkerTest

# Also import existing worker tests
from test_courses_worker import CoursesWorkerTest
from test_races_worker import RacesWorkerTest
from test_people_horses_worker import PeopleHorsesWorkerTest

# Initialize colorama
init(autoreset=True)


class DeploymentTestOrchestrator:
    """Orchestrates all deployment tests and generates comprehensive report"""

    def __init__(self):
        self.start_time = None
        self.end_time = None
        self.test_results = {}
        self.critical_failures = []
        self.warnings = []

    def print_master_header(self):
        """Print master test suite header"""
        print("\n" + "=" * 80)
        print("=" * 80)
        print(f"{Fore.CYAN}{'DARKHORSES MASTERS WORKER - DEPLOYMENT VERIFICATION':^80}{Style.RESET_ALL}")
        print("=" * 80)
        print("=" * 80)
        print(f"{'Comprehensive deployment health check':^80}")
        print(f"{'Started: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^80}")
        print("=" * 80)
        print("\n")

    def print_section_separator(self, title: str):
        """Print section separator"""
        print("\n")
        print("▶" * 80)
        print(f"{Fore.CYAN}{title:^80}{Style.RESET_ALL}")
        print("▶" * 80)
        print("\n")

    def run_deployment_verification(self):
        """Phase 1: Deployment Environment Verification"""
        self.print_section_separator("PHASE 1: DEPLOYMENT ENVIRONMENT VERIFICATION")

        try:
            test = DeploymentVerificationTest()
            success = test.run_all_tests()

            self.test_results['deployment_verification'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings'],
                'critical': not success
            }

            if not success:
                self.critical_failures.append("Deployment environment verification failed")

            return success

        except Exception as e:
            print(f"\n{Fore.RED}CRITICAL ERROR in deployment verification: {e}{Style.RESET_ALL}\n")
            self.critical_failures.append(f"Deployment verification crashed: {e}")
            self.test_results['deployment_verification'] = {
                'success': False,
                'passed': 0,
                'failed': 1,
                'warnings': 0,
                'critical': True,
                'error': str(e)
            }
            return False

    def run_schedule_verification(self):
        """Phase 2: Scheduler Configuration Verification"""
        self.print_section_separator("PHASE 2: SCHEDULER CONFIGURATION VERIFICATION")

        try:
            test = ScheduleVerificationTest()
            success = test.run_all_tests()

            self.test_results['schedule_verification'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings'],
                'critical': not success
            }

            if not success:
                self.critical_failures.append("Scheduler verification failed")

            return success

        except Exception as e:
            print(f"\n{Fore.RED}CRITICAL ERROR in schedule verification: {e}{Style.RESET_ALL}\n")
            self.critical_failures.append(f"Schedule verification crashed: {e}")
            self.test_results['schedule_verification'] = {
                'success': False,
                'passed': 0,
                'failed': 1,
                'warnings': 0,
                'critical': True,
                'error': str(e)
            }
            return False

    def run_data_freshness_check(self):
        """Phase 3: Data Freshness Monitoring"""
        self.print_section_separator("PHASE 3: DATA FRESHNESS MONITORING")

        try:
            test = DataFreshnessTest()
            success = test.run_all_tests()

            self.test_results['data_freshness'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings'],
                'critical': False  # Stale data is warning, not critical
            }

            if not success:
                self.warnings.append("Some data tables are stale")

            return success

        except Exception as e:
            print(f"\n{Fore.YELLOW}WARNING in data freshness check: {e}{Style.RESET_ALL}\n")
            self.warnings.append(f"Data freshness check had errors: {e}")
            self.test_results['data_freshness'] = {
                'success': False,
                'passed': 0,
                'failed': 1,
                'warnings': 1,
                'critical': False,
                'error': str(e)
            }
            return False

    def run_e2e_test(self):
        """Phase 4: End-to-End Pipeline Test"""
        self.print_section_separator("PHASE 4: END-TO-END PIPELINE TEST")

        try:
            test = EndToEndWorkerTest()
            success = test.run_all_tests()

            self.test_results['e2e_pipeline'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings'],
                'critical': not success
            }

            if not success:
                self.critical_failures.append("E2E pipeline test failed")

            return success

        except Exception as e:
            print(f"\n{Fore.RED}CRITICAL ERROR in E2E test: {e}{Style.RESET_ALL}\n")
            self.critical_failures.append(f"E2E test crashed: {e}")
            self.test_results['e2e_pipeline'] = {
                'success': False,
                'passed': 0,
                'failed': 1,
                'warnings': 0,
                'critical': True,
                'error': str(e)
            }
            return False

    def run_worker_data_tests(self):
        """Phase 5: Worker Data Verification"""
        self.print_section_separator("PHASE 5: WORKER DATA VERIFICATION")

        worker_results = {}

        # Test 1: Courses Worker
        try:
            print(f"\n{Fore.YELLOW}Running Courses Worker Test...{Style.RESET_ALL}\n")
            test = CoursesWorkerTest()
            success = test.run_all_tests()
            worker_results['courses'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings']
            }
        except Exception as e:
            print(f"{Fore.RED}Courses worker test error: {e}{Style.RESET_ALL}")
            worker_results['courses'] = {'success': False, 'error': str(e)}

        # Test 2: Races Worker
        try:
            print(f"\n{Fore.YELLOW}Running Races Worker Test...{Style.RESET_ALL}\n")
            test = RacesWorkerTest()
            success = test.run_all_tests()
            worker_results['races'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings']
            }
        except Exception as e:
            print(f"{Fore.RED}Races worker test error: {e}{Style.RESET_ALL}")
            worker_results['races'] = {'success': False, 'error': str(e)}

        # Test 3: People & Horses Worker
        try:
            print(f"\n{Fore.YELLOW}Running People & Horses Worker Test...{Style.RESET_ALL}\n")
            test = PeopleHorsesWorkerTest()
            success = test.run_all_tests()
            worker_results['people_horses'] = {
                'success': success,
                'passed': test.results['passed'],
                'failed': test.results['failed'],
                'warnings': test.results['warnings']
            }
        except Exception as e:
            print(f"{Fore.RED}People & Horses worker test error: {e}{Style.RESET_ALL}")
            worker_results['people_horses'] = {'success': False, 'error': str(e)}

        self.test_results['worker_data'] = worker_results

        all_success = all(r.get('success', False) for r in worker_results.values())
        if not all_success:
            self.warnings.append("Some worker data tests had issues")

        return all_success

    def print_comprehensive_report(self):
        """Print comprehensive deployment report"""
        self.print_section_separator("COMPREHENSIVE DEPLOYMENT REPORT")

        total_duration = self.end_time - self.start_time

        print(f"{'=' * 80}")
        print(f"{Fore.CYAN}EXECUTIVE SUMMARY{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        # Calculate overall statistics
        total_passed = sum(
            r.get('passed', 0) for r in self.test_results.values()
            if isinstance(r, dict) and 'passed' in r
        )

        # Handle nested worker_data structure
        if 'worker_data' in self.test_results:
            for worker_result in self.test_results['worker_data'].values():
                total_passed += worker_result.get('passed', 0)

        total_failed = sum(
            r.get('failed', 0) for r in self.test_results.values()
            if isinstance(r, dict) and 'failed' in r
        )

        if 'worker_data' in self.test_results:
            for worker_result in self.test_results['worker_data'].values():
                total_failed += worker_result.get('failed', 0)

        total_warnings = sum(
            r.get('warnings', 0) for r in self.test_results.values()
            if isinstance(r, dict) and 'warnings' in r
        )

        if 'worker_data' in self.test_results:
            for worker_result in self.test_results['worker_data'].values():
                total_warnings += worker_result.get('warnings', 0)

        total_tests = total_passed + total_failed
        pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

        # Overall Status
        critical_failures_count = len(self.critical_failures)
        warnings_count = len(self.warnings)

        if critical_failures_count == 0:
            overall_status = f"{Fore.GREEN}✅ OPERATIONAL{Style.RESET_ALL}"
        else:
            overall_status = f"{Fore.RED}❌ CRITICAL ISSUES{Style.RESET_ALL}"

        print(f"🎯 Overall Status: {overall_status}")
        print(f"📊 Test Pass Rate: {Fore.CYAN}{pass_rate:.1f}%{Style.RESET_ALL} ({total_passed}/{total_tests})")
        print(f"⏱️  Total Duration: {total_duration:.2f}s ({total_duration/60:.2f} minutes)")
        print(f"🗓️  Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Test Phase Results
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}TEST PHASE RESULTS{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        phase_names = {
            'deployment_verification': 'Deployment Environment',
            'schedule_verification': 'Scheduler Configuration',
            'data_freshness': 'Data Freshness',
            'e2e_pipeline': 'End-to-End Pipeline',
            'worker_data': 'Worker Data Verification'
        }

        for phase_key, phase_name in phase_names.items():
            if phase_key in self.test_results:
                result = self.test_results[phase_key]

                if phase_key == 'worker_data':
                    # Handle nested worker data
                    all_success = all(r.get('success', False) for r in result.values())
                    status = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}" if all_success else f"{Fore.YELLOW}⚠️  ISSUES{Style.RESET_ALL}"
                    print(f"📋 {phase_name}: {status}")

                    for worker_name, worker_result in result.items():
                        worker_status = f"{Fore.GREEN}✓{Style.RESET_ALL}" if worker_result.get('success') else f"{Fore.RED}✗{Style.RESET_ALL}"
                        print(f"   {worker_status} {worker_name.replace('_', ' ').title()}")
                else:
                    success = result.get('success', False)
                    critical = result.get('critical', False)

                    if success:
                        status = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}"
                    elif critical:
                        status = f"{Fore.RED}❌ CRITICAL{Style.RESET_ALL}"
                    else:
                        status = f"{Fore.YELLOW}⚠️  WARNING{Style.RESET_ALL}"

                    passed = result.get('passed', 0)
                    failed = result.get('failed', 0)
                    warnings = result.get('warnings', 0)

                    print(f"📋 {phase_name}: {status}")
                    print(f"   Passed: {passed}, Failed: {failed}, Warnings: {warnings}")

        # Critical Failures
        if self.critical_failures:
            print(f"\n{'=' * 80}")
            print(f"{Fore.RED}🚨 CRITICAL FAILURES{Style.RESET_ALL}")
            print(f"{'=' * 80}\n")

            for i, failure in enumerate(self.critical_failures, 1):
                print(f"{i}. {Fore.RED}{failure}{Style.RESET_ALL}")

        # Warnings
        if self.warnings:
            print(f"\n{'=' * 80}")
            print(f"{Fore.YELLOW}⚠️  WARNINGS{Style.RESET_ALL}")
            print(f"{'=' * 80}\n")

            for i, warning in enumerate(self.warnings, 1):
                print(f"{i}. {Fore.YELLOW}{warning}{Style.RESET_ALL}")

        # Service Health Dashboard
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}SERVICE HEALTH DASHBOARD{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        health_items = [
            ("Environment Configuration", self.test_results.get('deployment_verification', {}).get('success', False)),
            ("Scheduler Configuration", self.test_results.get('schedule_verification', {}).get('success', False)),
            ("Data Freshness", self.test_results.get('data_freshness', {}).get('success', False)),
            ("Pipeline Integrity", self.test_results.get('e2e_pipeline', {}).get('success', False)),
            ("Worker Data Quality", all(r.get('success', False) for r in self.test_results.get('worker_data', {}).values()))
        ]

        for item, status in health_items:
            icon = f"{Fore.GREEN}●{Style.RESET_ALL}" if status else f"{Fore.RED}●{Style.RESET_ALL}"
            status_text = f"{Fore.GREEN}Healthy{Style.RESET_ALL}" if status else f"{Fore.RED}Issues{Style.RESET_ALL}"
            print(f"{icon} {item:<30} {status_text}")

        # Recommendations
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}RECOMMENDATIONS{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        if critical_failures_count == 0 and warnings_count == 0:
            print(f"{Fore.GREEN}✅ No issues detected - deployment is healthy{Style.RESET_ALL}")
            print(f"   • All systems operational")
            print(f"   • Continue monitoring with scheduled health checks")
            print(f"   • Review logs periodically for optimization opportunities")
        else:
            if critical_failures_count > 0:
                print(f"{Fore.RED}🚨 IMMEDIATE ACTION REQUIRED:{Style.RESET_ALL}")
                print(f"   1. Review critical failures above")
                print(f"   2. Check Render.com service logs")
                print(f"   3. Verify environment variables")
                print(f"   4. Test API credentials")
                print(f"   5. Check database connectivity")

            if warnings_count > 0:
                print(f"\n{Fore.YELLOW}⚠️  ATTENTION NEEDED:{Style.RESET_ALL}")
                print(f"   1. Review warnings above")
                print(f"   2. Check data freshness thresholds")
                print(f"   3. Monitor worker execution logs")
                print(f"   4. Verify scheduler is running (not free tier)")

        # Monitoring Info
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}MONITORING INFORMATION{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        print(f"📍 Service: darkhorses-masters-worker on Render.com")
        print(f"📍 Region: UK/Ireland data only")
        print(f"📍 Update Schedules:")
        print(f"   • Daily (1:00 AM UTC): Races & Results")
        print(f"   • Weekly (Sunday 2:00 AM UTC): Jockeys, Trainers, Owners, Horses")
        print(f"   • Monthly (First Monday 3:00 AM UTC): Courses, Bookmakers")
        print(f"\n📍 Database Tables: 8 (ra_courses, ra_bookmakers, ra_jockeys,")
        print(f"                        ra_trainers, ra_owners, ra_horses,")
        print(f"                        ra_races, ra_runners)")

        # Next Steps
        print(f"\n{'=' * 80}")
        print(f"{Fore.CYAN}NEXT STEPS{Style.RESET_ALL}")
        print(f"{'=' * 80}\n")

        if critical_failures_count == 0:
            print("1. Run this test suite daily to monitor deployment health")
            print("2. Set up automated alerts for critical failures")
            print("3. Review data freshness weekly")
            print("4. Monitor Render.com service logs for errors")
            print("5. Check Racing API usage and rate limits")
        else:
            print("1. Fix critical issues immediately")
            print("2. Re-run deployment tests after fixes")
            print("3. Monitor service closely for 24 hours")
            print("4. Document any configuration changes made")

        print(f"\n{'=' * 80}")
        print(f"{'=' * 80}\n")

    def run_all_tests(self):
        """Run all deployment tests"""
        self.start_time = time.time()
        self.print_master_header()

        # Phase 1: Deployment Verification (Critical)
        deployment_ok = self.run_deployment_verification()

        # Phase 2: Schedule Verification (Critical)
        schedule_ok = self.run_schedule_verification()

        # Phase 3: Data Freshness (Warning only)
        data_fresh = self.run_data_freshness_check()

        # Phase 4: E2E Pipeline (Critical)
        e2e_ok = self.run_e2e_test()

        # Phase 5: Worker Data (Warning only)
        workers_ok = self.run_worker_data_tests()

        self.end_time = time.time()

        # Generate comprehensive report
        self.print_comprehensive_report()

        # Determine exit code
        # Only critical failures should cause non-zero exit
        has_critical_failures = len(self.critical_failures) > 0

        return not has_critical_failures


def main():
    """Main execution"""
    try:
        orchestrator = DeploymentTestOrchestrator()
        success = orchestrator.run_all_tests()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error running deployment tests: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
