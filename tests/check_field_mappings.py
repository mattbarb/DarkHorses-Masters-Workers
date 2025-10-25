"""
Check for field name mismatches between API response and our database mapping
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.api_client import RacingAPIClient
import json

config = get_config()
client = RacingAPIClient(
    username=config.api.username,
    password=config.api.password
)

print("="*80)
print("CHECKING RACECARDS API FIELD MAPPINGS")
print("="*80)

# Fetch racecards
response = client.get_racecards_pro(date='2025-10-23', region_codes=['gb', 'ire'])

if response and 'racecards' in response and len(response['racecards']) > 0:
    race = response['racecards'][0]
    runner = race['runners'][0] if race.get('runners') else None

    # Race field mappings we use
    race_fields_we_expect = [
        'race_id', 'course_id', 'course', 'region', 'race_name', 'date', 'off_dt',
        'off_time', 'type', 'race_class', 'distance_f', 'distance', 'dist_m',
        'distance_round', 'age_band', 'surface', 'going', 'going_detailed', 'weather',
        'rail_movements', 'pattern', 'sex_rest', 'rating_band', 'stalls', 'jumps',
        'is_abandoned', 'prize', 'big_race', 'comments', 'non_runners', 'race_number',
        'tip', 'verdict', 'betting_forecast', 'meet_id'
    ]

    runner_fields_we_expect = [
        'horse_id', 'horse', 'jockey_id', 'jockey', 'trainer_id', 'trainer',
        'trainer_location', 'owner_id', 'owner', 'number', 'draw', 'sire_id',
        'dam_id', 'damsire_id', 'weight_lbs', 'weight', 'age', 'sex', 'sex_code',
        'colour', 'dob', 'headgear', 'headgear_run', 'wind_surgery',
        'wind_surgery_run', 'form', 'last_run', 'ofr', 'rpr', 'ts', 'comment',
        'spotlight', 'trainer_rtf', 'past_results_flags', 'claiming_price_min',
        'claiming_price_max', 'medication', 'equipment', 'morning_line_odds',
        'is_scratched', 'silk_url'
    ]

    print("\nRACE FIELDS:")
    print("  API provides:", set(race.keys()) - {'runners'})
    print("\n  We look for:", set(race_fields_we_expect))
    print("\n  MISSING in API:", set(race_fields_we_expect) - set(race.keys()))
    print("\n  EXTRA in API (not mapped):", (set(race.keys()) - {'runners'}) - set(race_fields_we_expect))

    if runner:
        print("\n" + "="*80)
        print("RUNNER FIELDS:")
        print("  API provides:", set(runner.keys()))
        print("\n  We look for:", set(runner_fields_we_expect))
        print("\n  MISSING in API:", set(runner_fields_we_expect) - set(runner.keys()))
        print("\n  EXTRA in API (not mapped):", set(runner.keys()) - set(runner_fields_we_expect))

        # Show the actual mappings
        print("\n" + "="*80)
        print("FIELD MAPPING ISSUES:")
        print("="*80)

        issues = []

        # Check specific known issues
        if 'lbs' in runner and 'weight_lbs' not in runner:
            issues.append("✅ FIXED: 'lbs' → 'weight_lbs' (already fixed in code)")

        if 'sex_rest' in race and 'sex_restriction' not in race:
            issues.append("⚠️  'sex_rest' in API should map to 'sex_restriction' in DB")

        if 'dist_m' in race and 'distance_m' not in race:
            issues.append("⚠️  'dist_m' in API should map to 'distance_m' in DB")

        if 'big_race' in race and 'is_big_race' not in race:
            issues.append("⚠️  'big_race' in API should map to 'is_big_race' in DB")

        # Check for extra useful fields in API we're not capturing
        extra_in_api = set(runner.keys()) - set(runner_fields_we_expect)
        if extra_in_api:
            print("\nUNCAPTURED fields that might be useful:")
            for field in sorted(extra_in_api):
                print(f"  - {field}: {runner.get(field)}")

        if issues:
            print("\nFOUND ISSUES:")
            for issue in issues:
                print(f"  {issue}")
        else:
            print("\n✅ No obvious mapping issues found!")

print("\n" + "="*80)
print("Now checking RESULTS API...")
print("="*80)

# Check results API
results = client.get_results_pro(date='2025-10-22', region_codes=['gb', 'ire'])

if results and 'results' in results and len(results['results']) > 0:
    result_race = results['results'][0]
    result_runner = result_race['runners'][0] if result_race.get('runners') else None

    print("\nRESULTS - Additional fields beyond racecards:")

    racecard_race_keys = set(race.keys()) - {'runners'}
    result_race_keys = set(result_race.keys()) - {'runners'}

    new_race_fields = result_race_keys - racecard_race_keys
    print(f"\n  New RACE fields in results: {new_race_fields}")

    if result_runner and runner:
        racecard_runner_keys = set(runner.keys())
        result_runner_keys = set(result_runner.keys())

        new_runner_fields = result_runner_keys - racecard_runner_keys
        print(f"\n  New RUNNER fields in results: {new_runner_fields}")

        if new_runner_fields:
            print("\n  Sample values:")
            for field in sorted(new_runner_fields):
                value = result_runner.get(field)
                if value is not None:
                    print(f"    {field}: {value}")
