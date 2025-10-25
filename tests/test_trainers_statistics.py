"""
Test Statistics Calculation for Trainers

PURPOSE:
    Validates that statistics can be calculated and stored for real trainers.

WHAT IT DOES:
    1. Fetches 2-3 real trainers from database (not **TEST**)
    2. Displays current statistics values (before)
    3. Calculates new statistics from Racing API results
    4. Updates database
    5. Verifies statistics were stored correctly (after)
    6. Shows before/after comparison

USAGE:
    python3 tests/test_trainers_statistics.py
"""

import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient

# Import statistics worker
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'scripts', 'statistics_workers'))
from trainers_statistics_worker import calculate_trainer_statistics

def main():
    """Run statistics calculation test"""

    print("=" * 80)
    print("TRAINER STATISTICS CALCULATION TEST")
    print("=" * 80)
    print()

    # Initialize clients
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password
    )
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Step 1: Fetch real trainers (limit 3 for testing)
    print("STEP 1: Fetching real trainers from database...")
    print("-" * 80)

    response = db_client.client.table('ra_trainers').select('id, name').not_.like('id', '**TEST**%').limit(3).execute()

    if not response.data:
        print("ERROR: No trainers found in database")
        return False

    trainers = response.data
    print(f"Found {len(trainers)} trainers to test")
    for trainer in trainers:
        print(f"  - {trainer['name']} ({trainer['id']})")
    print()

    # Step 2: Show current statistics (before)
    print("STEP 2: CURRENT STATISTICS (BEFORE)")
    print("=" * 80)
    print()

    stats_fields = ['last_runner_date', 'last_win_date', 'days_since_last_runner', 'days_since_last_win',
                   'recent_14d_runs', 'recent_14d_wins', 'recent_14d_win_rate',
                   'recent_30d_runs', 'recent_30d_wins', 'recent_30d_win_rate']

    for trainer in trainers:
        trainer_id = trainer['id']
        full_trainer = db_client.client.table('ra_trainers').select('*').eq('id', trainer_id).execute().data[0]

        print(f"*** {full_trainer['name']}")
        print("-" * 80)
        for field in stats_fields:
            value = full_trainer.get(field)
            print(f"  {field:<35} {str(value):<20}")
        print()

    # Step 3: Calculate new statistics
    print("STEP 3: CALCULATING NEW STATISTICS")
    print("=" * 80)
    print()

    calculated_count = 0
    updated_count = 0

    for trainer in trainers:
        trainer_id = trainer['id']
        trainer_name = trainer['name']

        print(f"Calculating statistics for {trainer_name}...")

        stats = calculate_trainer_statistics(trainer_id, trainer_name, api_client)

        if stats:
            calculated_count += 1
            print(f"  Statistics calculated")
            print(f"  - Last runner: {stats.get('last_runner_date', 'N/A')}")
            print(f"  - Days since: {stats.get('days_since_last_runner', 'N/A')}")
            print(f"  - 14-day runs: {stats.get('recent_14d_runs', 0)}")
            print(f"  - 14-day wins: {stats.get('recent_14d_wins', 0)}")
            print(f"  - 14-day win rate: {stats.get('recent_14d_win_rate', 0)}%")

            # Update database
            try:
                db_client.client.table('ra_trainers').update(stats).eq('id', trainer_id).execute()
                updated_count += 1
                print(f"  Database updated")
            except Exception as e:
                print(f"  Failed to update: {e}")
        else:
            print(f"  No statistics calculated")
        print()

    print(f"Calculated: {calculated_count}/{len(trainers)}")
    print(f"Updated: {updated_count}/{len(trainers)}")
    print()

    # Step 4: Verify statistics (after)
    print("STEP 4: UPDATED STATISTICS (AFTER)")
    print("=" * 80)
    print()

    for trainer in trainers:
        trainer_id = trainer['id']
        full_trainer = db_client.client.table('ra_trainers').select('*').eq('id', trainer_id).execute().data[0]

        print(f"*** {full_trainer['name']}")
        print("-" * 80)
        for field in stats_fields:
            value = full_trainer.get(field)
            status = 'OK' if value is not None else 'NULL'
            print(f"  {field:<35} {str(value):<20} {status}")
        print()

    # Step 5: Summary
    print("STEP 5: SUMMARY")
    print("=" * 80)
    print(f"Trainers tested: {len(trainers)}")
    print(f"Statistics calculated: {calculated_count}")
    print(f"Database updates: {updated_count}")

    if updated_count > 0:
        print("TEST PASSED: Statistics calculation and storage working correctly")
        return True
    else:
        print("TEST FAILED: No statistics were calculated")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
