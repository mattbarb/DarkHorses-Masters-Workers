"""
Test Results Endpoint - Validates runner count discrepancy
Tests: GET /v1/results
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.api_client import RacingAPIClient
from config.config import get_config
from datetime import datetime, timedelta
import json

def test_results_runners():
    """
    Test if results endpoint gives us all runners

    According to audit:
    - Database has 2.77 avg runners per race
    - Expected: 8-12 runners per race
    - Missing: 72% of expected runners

    This test will:
    1. Fetch sample races from results endpoint
    2. Count runners per race
    3. Compare with expected values
    """
    print("=" * 80)
    print("TESTING: GET /v1/results - Runner Count Analysis")
    print("=" * 80)
    print()

    # Initialize API client
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url
    )

    # Test with recent dates (last 30 days)
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=7)  # Last week

    print(f"Step 1: Fetching results from {start_date} to {end_date}...")
    print()

    all_results = []

    # Fetch results (max 50 per page)
    for skip in range(0, 200, 50):  # Get up to 200 results
        results_response = api_client.get_results(
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            region_codes=['gb', 'ire'],
            limit=50,
            skip=skip
        )

        if not results_response or 'results' not in results_response:
            break

        results = results_response.get('results', [])
        if not results:
            break

        all_results.extend(results)
        print(f"  Fetched {len(results)} results (total: {len(all_results)})")

        if len(results) < 50:  # Last page
            break

    print(f"\nTotal results fetched: {len(all_results)}")
    print()

    if not all_results:
        print("FAILED: Could not get any results from API")
        return False

    # Analyze runner counts
    print("Step 2: Analyzing runner counts per race...")
    print()

    runner_counts = []
    races_with_runners = []

    for result in all_results:
        runners = result.get('runners', [])
        runner_count = len(runners)
        runner_counts.append(runner_count)

        races_with_runners.append({
            'race_id': result.get('race_id'),
            'race_name': result.get('race_name'),
            'course': result.get('course'),
            'date': result.get('date'),
            'runner_count': runner_count,
            'runners': [{'horse': r.get('horse'), 'horse_id': r.get('horse_id')} for r in runners[:3]]  # First 3 only
        })

    # Calculate statistics
    total_races = len(runner_counts)
    total_runners = sum(runner_counts)
    avg_runners = total_runners / total_races if total_races > 0 else 0
    min_runners = min(runner_counts) if runner_counts else 0
    max_runners = max(runner_counts) if runner_counts else 0

    print("=" * 80)
    print("RUNNER COUNT STATISTICS")
    print("=" * 80)
    print(f"Total races analyzed: {total_races}")
    print(f"Total runners: {total_runners}")
    print(f"Average runners per race: {avg_runners:.2f}")
    print(f"Min runners: {min_runners}")
    print(f"Max runners: {max_runners}")
    print()

    # Distribution
    print("RUNNER COUNT DISTRIBUTION:")
    print("-" * 80)
    from collections import Counter
    distribution = Counter(runner_counts)
    for count in sorted(distribution.keys()):
        races = distribution[count]
        pct = races / total_races * 100
        bar = "#" * int(pct / 2)
        print(f"  {count:2d} runners: {races:3d} races ({pct:5.1f}%) {bar}")

    print()

    # Sample races
    print("SAMPLE RACES:")
    print("-" * 80)
    for race in races_with_runners[:5]:
        print(f"  {race['race_id']}: {race['race_name']} at {race['course']}")
        print(f"    Date: {race['date']}, Runners: {race['runner_count']}")
        if race['runners']:
            print(f"    Sample runners: {', '.join([r['horse'] for r in race['runners']])}")
        print()

    # Comparison with audit findings
    print("=" * 80)
    print("COMPARISON WITH AUDIT FINDINGS")
    print("=" * 80)
    print(f"Database (audit):     2.77 avg runners per race")
    print(f"API (this test):      {avg_runners:.2f} avg runners per race")
    print(f"Expected normal:      8-12 runners per race")
    print()

    if avg_runners >= 8:
        print("RESULT: CONFIRMED - API returns full runner data")
        print()
        print("CONCLUSION: The missing runners issue is likely due to:")
        print("  1. Data extraction logic skipping runners (line 284-286 in races_fetcher.py)")
        print("  2. Database filtering removing runners")
        print("  3. Historical data backfill incomplete")
        discrepancy = "API_HAS_DATA"
    elif avg_runners > 4:
        print("RESULT: PARTIAL - API returns more runners than database")
        print()
        print("CONCLUSION: Database has fewer runners than API.")
        print("  - API average: {:.2f}".format(avg_runners))
        print("  - Database average: 2.77")
        print("  - Likely cause: Extraction or storage issue")
        discrepancy = "PARTIAL_DATA"
    else:
        print("RESULT: INCONCLUSIVE - API also shows low runner counts")
        print()
        print("CONCLUSION: Either:")
        print("  1. Sample period has fewer races (e.g., off-season)")
        print("  2. API data is incomplete")
        print("  3. Regional filtering removing races")
        discrepancy = "API_ALSO_LOW"

    print()
    print("=" * 80)
    print("RECOMMENDATIONS:")
    print("-" * 80)
    if discrepancy == "API_HAS_DATA":
        print("1. Review races_fetcher.py line 284-286 - may be skipping runners")
        print("2. Check database for runner count vs API")
        print("3. Run backfill for historical data")
    elif discrepancy == "PARTIAL_DATA":
        print("1. Fix extraction logic to capture all runners")
        print("2. Verify no runners are being filtered out")
        print("3. Run data reconciliation")
    else:
        print("1. Test with different date ranges")
        print("2. Check if results endpoint is correct one to use")
        print("3. Consider using racecards endpoint for runner counts")

    print()

    return True

if __name__ == '__main__':
    try:
        success = test_results_runners()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
