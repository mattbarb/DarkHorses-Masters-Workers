#!/usr/bin/env python3
"""
Master Test Runner for DarkHorses Masters Workers
Runs all test suites and provides comprehensive summary
"""

import sys
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from test_courses_worker import CoursesWorkerTest
from test_races_worker import RacesWorkerTest
from test_people_horses_worker import PeopleHorsesWorkerTest

# Initialize colorama
init(autoreset=True)


def print_main_header():
    """Print main test suite header"""
    print("\n" + "=" * 80)
    print("=" * 80)
    print(f"{'DarkHorses Masters Workers - Integration Test Suite':^80}")
    print("=" * 80)
    print("=" * 80)
    print("Testing all reference data workers: Courses, Races, People & Horses")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80 + "\n")


def print_section_header(title):
    """Print section header"""
    print("\n" + "▶" * 40)
    print(f"{title}...")
    print("▶" * 40 + "\n")


def print_final_summary(results):
    """Print final summary of all tests"""
    print("\n" + "=" * 80)
    print("=" * 80)
    print(f"{'FINAL TEST SUMMARY':^80}")
    print("=" * 80)
    print("=" * 80)
    print()

    total_passed = sum(r['passed'] for r in results.values())
    total_failed = sum(r['failed'] for r in results.values())
    total_warnings = sum(r['warnings'] for r in results.values())

    print(f"{'Worker':<35} {'Passed':<10} {'Failed':<10} {'Warnings':<10} {'Status'}")
    print("-" * 80)

    for worker_name, result in results.items():
        passed = result['passed']
        failed = result['failed']
        warnings = result['warnings']

        if failed == 0:
            status = f"{Fore.GREEN}✅ PASS{Style.RESET_ALL}"
        else:
            status = f"{Fore.RED}❌ FAIL{Style.RESET_ALL}"

        print(f"{worker_name:<35} {passed:<10} {failed:<10} {warnings:<10} {status}")

    print("-" * 80)
    print(f"{'TOTAL':<35} {total_passed:<10} {total_failed:<10} {total_warnings:<10}")
    print()

    total_tests = total_passed + total_failed
    pass_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0

    print(f"📊 Overall Pass Rate: {pass_rate:.1f}% ({total_passed}/{total_tests} tests)")

    if total_warnings > 0:
        print(f"⚠️  Total Warnings: {total_warnings}")

    print()
    print("=" * 80)

    if total_failed == 0:
        print(f"{Fore.GREEN}🎉 ALL WORKERS FUNCTIONING CORRECTLY!{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}⚠️  SOME WORKERS HAVE ISSUES{Style.RESET_ALL}")

    print("=" * 80)
    print()

    if total_failed == 0:
        print(f"✅ Courses Worker: Collecting venue data")
        print(f"✅ Races Worker: Collecting race cards and results")
        print(f"✅ People & Horses Worker: Collecting jockeys, trainers, owners, horses")
    else:
        print(f"🔍 Check individual test outputs above for details")
        print(f"📋 Review worker logs on Render.com for error messages")

    print()
    print("=" * 80)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


def main():
    """Main test execution"""
    print_main_header()

    results = {}

    try:
        # Test 1: Courses Worker
        print_section_header("Running Courses Worker Tests")
        courses_test = CoursesWorkerTest()
        courses_test.run_all_tests()
        results['Courses Worker'] = courses_test.results

        # Test 2: Races Worker
        print_section_header("Running Races Worker Tests")
        races_test = RacesWorkerTest()
        races_test.run_all_tests()
        results['Races Worker'] = races_test.results

        # Test 3: People & Horses Worker
        print_section_header("Running People & Horses Worker Tests")
        people_horses_test = PeopleHorsesWorkerTest()
        people_horses_test.run_all_tests()
        results['People & Horses Worker'] = people_horses_test.results

        # Print final summary
        print_final_summary(results)

        # Determine exit code
        total_failed = sum(r['failed'] for r in results.values())
        sys.exit(0 if total_failed == 0 else 1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Tests interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Fore.RED}Fatal error running tests: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
