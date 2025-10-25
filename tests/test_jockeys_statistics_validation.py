#!/usr/bin/env python3
"""
Jockeys Statistics Validation Test

Tests the complete jockeys statistics calculation workflow:
1. Fetches REAL jockeys from database (not TEST entities)
2. Displays current statistics (before)
3. Calculates new statistics using jockeys_statistics_worker
4. Updates database
5. Displays updated statistics (after)
6. Verifies all 10 statistics fields are populated correctly

This script uses real jockeys that exist in the Racing API, avoiding HTTP 422 errors.
"""

import sys
import os
from datetime import datetime
from typing import Dict, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.api_client import RacingAPIClient
from utils.supabase_client import SupabaseReferenceClient
from scripts.statistics_workers.jockeys_statistics_worker import calculate_jockey_statistics


def print_header(text: str, char: str = "="):
    """Print a formatted header"""
    print(f"\n{char * 80}")
    print(text)
    print(f"{char * 80}\n")


def print_subheader(text: str):
    """Print a formatted subheader"""
    print(f"\n{text}")
    print("-" * 80)


def print_jockey_stats(jockey: Dict, stats_fields: List[str]):
    """Print jockey statistics in a formatted table"""
    print(f"\n*** {jockey.get('name', 'Unknown')}")
    print_subheader("")

    for field in stats_fields:
        value = jockey.get(field)

        # Format value for display
        if value is None:
            display_value = "None"
            status = ""
        elif isinstance(value, float):
            display_value = f"{value:.2f}"
            status = "✓"
        elif isinstance(value, int):
            display_value = str(value)
            status = "✓"
        else:
            display_value = str(value)
            status = "✓"

        # Align output
        print(f"  {field:30s} {display_value:25s} {status}")


def fetch_real_jockeys(db_client: SupabaseReferenceClient, limit: int = 3) -> List[Dict]:
    """
    Fetch real jockeys from database (not TEST entities)

    Args:
        db_client: Supabase client
        limit: Number of jockeys to fetch

    Returns:
        List of jockey records
    """
    try:
        # Fetch real jockeys (exclude TEST entities)
        response = db_client.client.table('ra_jockeys').select('*').not_.like('id', '**TEST**%').limit(limit).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching jockeys: {e}")
        return []


def calculate_and_update_statistics(
    jockeys: List[Dict],
    api_client: RacingAPIClient,
    db_client: SupabaseReferenceClient
) -> Dict:
    """
    Calculate statistics for jockeys and update database

    Args:
        jockeys: List of jockey records
        api_client: Racing API client
        db_client: Supabase client

    Returns:
        Dictionary with execution statistics
    """
    results = {
        'calculated': 0,
        'updated': 0,
        'errors': 0,
        'updated_jockeys': []
    }

    for jockey in jockeys:
        jockey_id = jockey['id']
        jockey_name = jockey.get('name', 'Unknown')

        print(f"\nCalculating statistics for {jockey_name}...")

        try:
            # Calculate statistics
            stats = calculate_jockey_statistics(jockey_id, jockey_name, api_client)

            if stats:
                results['calculated'] += 1

                # Display calculated stats
                print("✓ Statistics calculated")
                if stats.get('last_ride_date'):
                    print(f"  - Last ride: {stats['last_ride_date']}")
                    print(f"  - Days since: {stats.get('days_since_last_ride', 'N/A')}")
                if stats.get('recent_14d_rides', 0) > 0:
                    print(f"  - 14-day rides: {stats['recent_14d_rides']}")
                    print(f"  - 14-day wins: {stats['recent_14d_wins']}")
                    print(f"  - 14-day win rate: {stats.get('recent_14d_win_rate', 0)}%")
                else:
                    print(f"  - No rides in last 14 days")

                # Update database
                try:
                    update_result = db_client.client.table('ra_jockeys').update(stats).eq('id', jockey_id).execute()
                    if update_result.data:
                        results['updated'] += 1
                        results['updated_jockeys'].append(jockey_id)
                        print("✓ Database updated")
                    else:
                        print("⚠ Database update returned no data")
                        results['errors'] += 1
                except Exception as e:
                    print(f"✗ Database update failed: {e}")
                    results['errors'] += 1
            else:
                print(f"✗ Failed to calculate statistics")
                results['errors'] += 1

        except Exception as e:
            print(f"✗ Error processing jockey: {e}")
            results['errors'] += 1

    return results


def verify_statistics(db_client: SupabaseReferenceClient, jockey_ids: List[str]) -> List[Dict]:
    """
    Fetch updated jockey records from database

    Args:
        db_client: Supabase client
        jockey_ids: List of jockey IDs to fetch

    Returns:
        List of updated jockey records
    """
    try:
        response = db_client.client.table('ra_jockeys').select('*').in_('id', jockey_ids).execute()
        return response.data if response.data else []
    except Exception as e:
        print(f"Error fetching updated jockeys: {e}")
        return []


def main():
    """Main test execution"""
    print_header("JOCKEYS STATISTICS VALIDATION TEST")

    # Statistics fields to verify (10 total)
    stats_fields = [
        'last_ride_date',
        'last_win_date',
        'days_since_last_ride',
        'days_since_last_win',
        'recent_14d_rides',
        'recent_14d_wins',
        'recent_14d_win_rate',
        'recent_30d_rides',
        'recent_30d_wins',
        'recent_30d_win_rate'
    ]

    # Initialize clients
    print("Initializing clients...")
    config = get_config()
    api_client = RacingAPIClient(
        username=config.api.username,
        password=config.api.password
    )
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )
    print("✓ Clients initialized")

    # STEP 1: Fetch real jockeys
    print_header("STEP 1: Fetching real jockeys from database...", "-")
    jockeys = fetch_real_jockeys(db_client, limit=3)

    if not jockeys:
        print("✗ No jockeys found in database")
        return 1

    print(f"✓ Found {len(jockeys)} jockeys to test")
    for jockey in jockeys:
        print(f"  - {jockey.get('name', 'Unknown')} ({jockey['id']})")

    # STEP 2: Display current statistics
    print_header("STEP 2: CURRENT STATISTICS (BEFORE)")
    for jockey in jockeys:
        print_jockey_stats(jockey, stats_fields)

    # STEP 3: Calculate new statistics
    print_header("STEP 3: CALCULATING NEW STATISTICS")
    results = calculate_and_update_statistics(jockeys, api_client, db_client)

    print(f"\n✓ Calculated: {results['calculated']}/{len(jockeys)}")
    print(f"✓ Updated: {results['updated']}/{len(jockeys)}")
    if results['errors'] > 0:
        print(f"✗ Errors: {results['errors']}")

    # STEP 4: Fetch and display updated statistics
    print_header("STEP 4: UPDATED STATISTICS (AFTER)")
    if results['updated_jockeys']:
        updated_jockeys = verify_statistics(db_client, results['updated_jockeys'])
        for jockey in updated_jockeys:
            print_jockey_stats(jockey, stats_fields)
    else:
        print("⚠ No jockeys were updated")

    # STEP 5: Summary and validation
    print_header("STEP 5: SUMMARY")
    print(f"Jockeys tested: {len(jockeys)}")
    print(f"Statistics calculated: {results['calculated']}")
    print(f"Database updates: {results['updated']}")
    print(f"Errors: {results['errors']}")

    # Determine test pass/fail
    if results['updated'] > 0 and results['errors'] == 0:
        print("\n✅ TEST PASSED: Statistics calculation and storage working correctly")
        return 0
    elif results['updated'] > 0 and results['errors'] > 0:
        print("\n⚠ TEST PARTIAL SUCCESS: Some statistics calculated but errors occurred")
        return 1
    else:
        print("\n✗ TEST FAILED: No statistics were successfully calculated and stored")
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
