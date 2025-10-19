"""
Test Racecards Pro Endpoint - Validates available fields
Tests: GET /v1/racecards/pro
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from utils.api_client import RacingAPIClient
from config.config import get_config
from datetime import datetime, timedelta
import json

def test_racecards_fields():
    """
    Test if racecards endpoint has fields we're not currently extracting

    Missing race fields (from audit):
    - pattern, sex_restriction, rating_band
    - jumps, stalls, tip, verdict, betting_forecast

    Missing runner fields (from audit):
    - spotlight (premium content)
    - quotes, stable_tour, medical (arrays)
    - odds (historical odds array)
    - wind_surgery info
    - prev_trainers, prev_owners (arrays)
    - trainer_location, trainer_rtf
    """
    print("=" * 80)
    print("TESTING: GET /v1/racecards/pro - Available Fields")
    print("=" * 80)
    print()

    # Initialize API client
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url
    )

    # Test with today's date
    test_date = datetime.now().strftime('%Y-%m-%d')
    print(f"Step 1: Fetching racecards for {test_date}...")

    racecards_response = api_client.get_racecards_pro(
        date=test_date,
        region_codes=['gb', 'ire']
    )

    if not racecards_response or 'racecards' not in racecards_response:
        # Try yesterday if no races today
        test_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        print(f"No races today, trying {test_date}...")
        racecards_response = api_client.get_racecards_pro(
            date=test_date,
            region_codes=['gb', 'ire']
        )

    if not racecards_response or 'racecards' not in racecards_response:
        print("FAILED: Could not get racecards from API")
        return False

    racecards = racecards_response.get('racecards', [])
    print(f"Found {len(racecards)} racecards")
    print()

    if not racecards:
        print("FAILED: No racecards available for testing")
        return False

    # Analyze first racecard
    print("Step 2: Analyzing race and runner fields...")
    print()

    sample_race = racecards[0]
    sample_runners = sample_race.get('runners', [])

    # Race-level fields we're looking for
    target_race_fields = [
        'pattern', 'sex_restriction', 'rating_band', 'jumps', 'stalls',
        'tip', 'verdict', 'betting_forecast', 'spotlight'
    ]

    # Runner-level fields we're looking for
    target_runner_fields = [
        'spotlight', 'quotes', 'stable_tour', 'medical', 'odds',
        'wind_surgery', 'prev_trainers', 'prev_owners',
        'trainer_location', 'trainer_rtf', 'dob', 'sex_code', 'colour',
        'region', 'breeder'
    ]

    # Check race fields
    print("RACE-LEVEL FIELDS:")
    print("-" * 80)
    race_results = {}
    for field in target_race_fields:
        value = sample_race.get(field)
        race_results[field] = {
            'present': field in sample_race,
            'has_value': value is not None and value != '',
            'sample': value
        }
        status = "PRESENT" if race_results[field]['present'] and race_results[field]['has_value'] else \
                 "NULL/EMPTY" if race_results[field]['present'] else "MISSING"
        print(f"  {field:25s}: {status:12s} | {str(value)[:50]}")

    print()
    print("RUNNER-LEVEL FIELDS (from first runner):")
    print("-" * 80)

    if not sample_runners:
        print("  No runners in sample race")
        runner_results = {}
    else:
        sample_runner = sample_runners[0]
        runner_results = {}
        for field in target_runner_fields:
            value = sample_runner.get(field)
            runner_results[field] = {
                'present': field in sample_runner,
                'has_value': value is not None and value != '' and value != [],
                'sample': value
            }
            status = "PRESENT" if runner_results[field]['present'] and runner_results[field]['has_value'] else \
                     "NULL/EMPTY" if runner_results[field]['present'] else "MISSING"
            print(f"  {field:25s}: {status:12s} | {str(value)[:50]}")

    print()
    print("=" * 80)
    print("ALL AVAILABLE FIELDS IN SAMPLE RACE:")
    print("-" * 80)
    print("Race fields:", list(sample_race.keys()))
    print()
    if sample_runners:
        print("Runner fields:", list(sample_runners[0].keys()))
    print()

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    race_available = sum(1 for f in race_results.values() if f['present'] and f['has_value'])
    runner_available = sum(1 for f in runner_results.values() if f['present'] and f['has_value'])

    print(f"Target race fields with data: {race_available}/{len(target_race_fields)}")
    print(f"Target runner fields with data: {runner_available}/{len(target_runner_fields)}")
    print()

    # Fields we're not extracting but are available
    print("FIELDS AVAILABLE BUT NOT CURRENTLY EXTRACTED:")
    print("-" * 80)

    available_race_fields = [f for f, v in race_results.items() if v['present'] and v['has_value']]
    available_runner_fields = [f for f, v in runner_results.items() if v['present'] and v['has_value']]

    if available_race_fields:
        print("Race fields:")
        for field in available_race_fields:
            print(f"  - {field}")
    else:
        print("Race fields: None found with sample data")

    print()

    if available_runner_fields:
        print("Runner fields:")
        for field in available_runner_fields:
            print(f"  - {field}")
    else:
        print("Runner fields: None found with sample data")

    print()
    print("=" * 80)

    # Save sample data
    print("SAMPLE DATA (first race):")
    print("-" * 80)
    sample_output = {
        'race_id': sample_race.get('race_id'),
        'race_name': sample_race.get('race_name'),
        'course': sample_race.get('course'),
        'available_fields': {
            'race': available_race_fields,
            'runner': available_runner_fields
        },
        'runner_count': len(sample_runners)
    }
    print(json.dumps(sample_output, indent=2))
    print()

    print("=" * 80)
    print("RESULT: CONFIRMED - Endpoint accessible")
    print()
    print(f"Confirmed {race_available + runner_available} additional fields available")
    return True

if __name__ == '__main__':
    try:
        success = test_racecards_fields()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
