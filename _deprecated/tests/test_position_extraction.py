#!/usr/bin/env python3
"""
Test script to inspect Racing API results response structure
and identify position data fields
"""

import sys
import json
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.append(str(Path(__file__).parent))

from config.config import get_config
from utils.logger import get_logger
from utils.api_client import RacingAPIClient

# Set environment variables if not already set
if not os.getenv('SUPABASE_URL'):
    os.environ['SUPABASE_URL'] = 'https://amsjvmlaknnvppxsgpfk.supabase.co'
if not os.getenv('SUPABASE_SERVICE_KEY'):
    os.environ['SUPABASE_SERVICE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtc2p2bWxha25udnBweHNncGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDAxNjQxNSwiZXhwIjoyMDY1NTkyNDE1fQ.8JiQWlaTBH18o8PvElYC5aBAKGw8cfdMBe8KbXTAukI'
if not os.getenv('RACING_API_USERNAME'):
    os.environ['RACING_API_USERNAME'] = 'l2fC3sZFIZmvpiMt6DdUCpEv'
if not os.getenv('RACING_API_PASSWORD'):
    os.environ['RACING_API_PASSWORD'] = 'R0pMr1L58WH3hUkpVtPcwYnw'

logger = get_logger('test_position_extraction')


def inspect_api_response():
    """Fetch and inspect a sample results response"""

    print("=" * 80)
    print("TESTING RACING API RESULTS ENDPOINT - POSITION DATA INSPECTION")
    print("=" * 80)

    # Initialize API client
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password,
        base_url=config.api.base_url,
        timeout=config.api.timeout,
        max_retries=config.api.max_retries
    )

    # Test with a recent past date (7 days ago to ensure results are available)
    test_date = (datetime.utcnow() - timedelta(days=7)).strftime('%Y-%m-%d')

    print(f"\n1. Fetching results for date: {test_date}")
    print(f"   (Using past date to ensure results with positions are available)")

    # Fetch results for UK/Ireland
    response = api_client.get_results(
        date=test_date,
        region_codes=['gb', 'ire'],
        limit=5  # Just get a few results for testing
    )

    if not response:
        print("\n✗ ERROR: No response from API")
        return False

    print(f"\n2. API Response structure:")
    print(f"   - Top-level keys: {list(response.keys())}")

    results = response.get('results', [])
    if not results:
        print("\n✗ No results found for this date")
        print("   Try a different date or check API availability")
        return False

    print(f"\n3. Found {len(results)} race results")

    # Inspect first result in detail
    first_result = results[0]
    print(f"\n4. First result structure:")
    print(f"   - Race ID: {first_result.get('race_id')}")
    print(f"   - Course: {first_result.get('course')}")
    print(f"   - Race name: {first_result.get('race_name')}")
    print(f"   - Date: {first_result.get('date')}")
    print(f"   - Off time: {first_result.get('off')}")
    print(f"   - Results status: {first_result.get('results_status')}")

    # Check for runners
    runners = first_result.get('runners', [])
    print(f"\n5. Runners in first result: {len(runners)}")

    if not runners:
        print("\n✗ No runners found in result")
        return False

    # Inspect first runner in detail
    first_runner = runners[0]
    print(f"\n6. First runner complete data structure:")
    print("   " + "=" * 76)
    print(json.dumps(first_runner, indent=4))
    print("   " + "=" * 76)

    # Look for position-related fields
    print(f"\n7. Position-related fields analysis:")
    print(f"   All runner keys: {list(first_runner.keys())}")

    position_fields = [
        'position', 'pos', 'place', 'finishing_position', 'finish_position',
        'distance_beaten', 'distanceBeatten', 'beaten_distance', 'dist_beaten',
        'prize', 'prize_won', 'winnings', 'prize_money',
        'sp', 'starting_price', 'odds', 'price', 'bsp',
        'result', 'outcome'
    ]

    found_fields = {}
    for field in position_fields:
        if field in first_runner:
            found_fields[field] = first_runner[field]
            print(f"   ✓ Found: {field} = {first_runner[field]}")

    if not found_fields:
        print("   ✗ None of the expected position fields found!")
        print("   The API response may use different field names")

    # Check all runners for position data
    print(f"\n8. Checking position data across all runners in first race:")
    positions_found = []
    for i, runner in enumerate(runners[:10]):  # Check first 10 runners
        pos = None
        for field in ['position', 'pos', 'place', 'finishing_position']:
            if field in runner:
                pos = runner[field]
                break

        horse_name = runner.get('horse', runner.get('horse_name', 'Unknown'))
        if pos:
            positions_found.append(pos)
            print(f"   Runner {i+1}: {horse_name} - Position: {pos}")
        else:
            print(f"   Runner {i+1}: {horse_name} - Position: NOT FOUND")

    # Summary
    print(f"\n" + "=" * 80)
    print("SUMMARY:")
    print("=" * 80)

    if found_fields:
        print("✓ Position data IS available in API response")
        print(f"\nFound fields:")
        for field, value in found_fields.items():
            print(f"  - {field}: {value}")

        print(f"\nPositions found in first race: {positions_found}")

        if positions_found:
            print(f"\n✓ SUCCESS: Position data extraction is possible!")
            print(f"\nRecommended field names to use:")
            for field in found_fields.keys():
                print(f"  - {field}")
        else:
            print(f"\n⚠ WARNING: Fields exist but may be empty for this race")
            print(f"  This might be a void race or results not yet declared")
    else:
        print("✗ Position data NOT found in expected fields")
        print("  Manual inspection of runner structure needed")

    print("=" * 80)

    # Save full response to file for reference
    output_file = Path(__file__).parent / 'test_api_response.json'
    with open(output_file, 'w') as f:
        json.dump(response, f, indent=2)
    print(f"\nFull API response saved to: {output_file}")

    return bool(found_fields)


if __name__ == '__main__':
    try:
        success = inspect_api_response()
        sys.exit(0 if success else 1)
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
        print(f"\n✗ ERROR: {e}")
        sys.exit(1)
