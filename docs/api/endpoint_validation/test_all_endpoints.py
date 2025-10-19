"""
Master Test Script - Run all endpoint validation tests
"""

import sys
from pathlib import Path
import subprocess
import json
from datetime import datetime

def run_test(script_name, description):
    """Run a test script and return results"""
    print()
    print("=" * 80)
    print(f"Running: {description}")
    print("=" * 80)
    print()

    script_path = Path(__file__).parent / script_name

    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Print output
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        success = result.returncode == 0
        return {
            'test': script_name,
            'description': description,
            'success': success,
            'exit_code': result.returncode,
            'output': result.stdout,
            'error': result.stderr
        }

    except subprocess.TimeoutExpired:
        print(f"ERROR: Test timed out after 120 seconds")
        return {
            'test': script_name,
            'description': description,
            'success': False,
            'exit_code': -1,
            'output': '',
            'error': 'Timeout after 120 seconds'
        }
    except Exception as e:
        print(f"ERROR: {e}")
        return {
            'test': script_name,
            'description': description,
            'success': False,
            'exit_code': -1,
            'output': '',
            'error': str(e)
        }

def main():
    """Run all endpoint validation tests"""
    print("=" * 80)
    print("RACING API ENDPOINT VALIDATION SUITE")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Define tests
    tests = [
        ('test_horses_pro_endpoint.py', 'Horse Pro Endpoint - Pedigree Data'),
        ('test_racecards_fields.py', 'Racecards Pro - Available Fields'),
        ('test_results_runners.py', 'Results Endpoint - Runner Count Analysis'),
    ]

    results = []

    # Run each test
    for script, description in tests:
        result = run_test(script, description)
        results.append(result)

    # Summary
    print()
    print("=" * 80)
    print("VALIDATION SUITE SUMMARY")
    print("=" * 80)
    print()

    passed = sum(1 for r in results if r['success'])
    failed = len(results) - passed

    print(f"Total tests: {len(results)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print()

    print("TEST RESULTS:")
    print("-" * 80)
    for result in results:
        status = "PASS" if result['success'] else "FAIL"
        icon = "✓" if result['success'] else "✗"
        print(f"{icon} {status:6s} | {result['description']}")
        if not result['success'] and result['error']:
            print(f"         Error: {result['error'][:100]}")

    print()
    print("=" * 80)
    print("ENDPOINT VALIDATION STATUS")
    print("=" * 80)
    print()

    # Parse results for key findings
    endpoint_status = {
        '/v1/horses/{id}/pro': 'NOT_TESTED',
        '/v1/racecards/pro': 'NOT_TESTED',
        '/v1/results': 'NOT_TESTED'
    }

    for result in results:
        if 'horses_pro' in result['test']:
            if result['success'] and 'CONFIRMED' in result['output']:
                endpoint_status['/v1/horses/{id}/pro'] = 'CONFIRMED'
            elif result['success'] and 'PARTIAL' in result['output']:
                endpoint_status['/v1/horses/{id}/pro'] = 'PARTIAL'
            else:
                endpoint_status['/v1/horses/{id}/pro'] = 'FAILED'

        elif 'racecards_fields' in result['test']:
            if result['success']:
                endpoint_status['/v1/racecards/pro'] = 'CONFIRMED'
            else:
                endpoint_status['/v1/racecards/pro'] = 'FAILED'

        elif 'results_runners' in result['test']:
            if result['success']:
                endpoint_status['/v1/results'] = 'CONFIRMED'
            else:
                endpoint_status['/v1/results'] = 'FAILED'

    for endpoint, status in endpoint_status.items():
        icon = "✅" if status == 'CONFIRMED' else "⚠️" if status == 'PARTIAL' else "❌" if status == 'FAILED' else "⏳"
        print(f"{icon} {endpoint:30s}: {status}")

    print()
    print("=" * 80)
    print("OVERALL RESULT")
    print("=" * 80)
    print()

    if failed == 0:
        print("SUCCESS: All endpoint validation tests passed")
        print()
        print("You can proceed with confidence that:")
        print("  - All critical endpoints are accessible")
        print("  - Required data fields are available")
        print("  - Data quality meets expectations")
        exit_code = 0
    else:
        print("PARTIAL SUCCESS: Some tests failed")
        print()
        print("Review failed tests above and:")
        print("  - Check API credentials")
        print("  - Verify network connectivity")
        print("  - Check API plan/subscription status")
        exit_code = 1

    print()
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Save results to file
    report_path = Path(__file__).parent / 'validation_report.json'
    with open(report_path, 'w') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total': len(results),
                'passed': passed,
                'failed': failed
            },
            'endpoint_status': endpoint_status,
            'detailed_results': results
        }, f, indent=2)

    print(f"\nDetailed report saved to: {report_path}")

    return exit_code

if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
