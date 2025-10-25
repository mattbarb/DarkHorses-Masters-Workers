#!/usr/bin/env python3
"""
Test Pro lineage endpoints:
- /v1/dams/{dam_id}/progeny/results
- /v1/damsires/{damsire_id}/grandoffspring/results
"""

import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.api_client import RacingAPIClient
from config.config import get_config

print("=" * 100)
print("TESTING PRO LINEAGE ENDPOINTS")
print("=" * 100)
print()

# Initialize API client
config = get_config()
api_client = RacingAPIClient(
    username=config.api.username,
    password=config.api.password
)

# =========================================================================
# Test 1: Get a popular dam_id from our database
# =========================================================================
print("STEP 1: Finding a popular dam for testing")
print("-" * 100)

import psycopg2

conn_string = "postgresql://postgres.amsjvmlaknnvppxsgpfk:ujCx2aXH!RYnU6x@aws-0-eu-west-2.pooler.supabase.com:6543/postgres"

try:
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor()

    # Get a popular dam (one with many offspring)
    cur.execute("""
        SELECT
            ancestor_horse_id as dam_id,
            ancestor_name as dam_name,
            COUNT(DISTINCT horse_id) as offspring_count
        FROM ra_lineage
        WHERE relation_type = 'dam'
        AND ancestor_horse_id IS NOT NULL
        GROUP BY ancestor_horse_id, ancestor_name
        ORDER BY offspring_count DESC
        LIMIT 5;
    """)

    print("Top dams by offspring count in our database:")
    popular_dams = []
    for dam_id, dam_name, count in cur.fetchall():
        print(f"  {dam_name:<40} ({dam_id}) - {count} offspring")
        popular_dams.append((dam_id, dam_name, count))

    test_dam_id, test_dam_name, test_dam_count = popular_dams[0]
    print()
    print(f"Testing with: {test_dam_name} ({test_dam_id})")
    print()

    # Get a popular damsire
    cur.execute("""
        SELECT
            ancestor_horse_id as damsire_id,
            ancestor_name as damsire_name,
            COUNT(DISTINCT horse_id) as grandoffspring_count
        FROM ra_lineage
        WHERE relation_type = 'grandsire_maternal'
        AND ancestor_horse_id IS NOT NULL
        GROUP BY ancestor_horse_id, ancestor_name
        ORDER BY grandoffspring_count DESC
        LIMIT 5;
    """)

    print("Top damsires by grandoffspring count in our database:")
    popular_damsires = []
    for damsire_id, damsire_name, count in cur.fetchall():
        print(f"  {damsire_name:<40} ({damsire_id}) - {count} grandoffspring")
        popular_damsires.append((damsire_id, damsire_name, count))

    test_damsire_id, test_damsire_name, test_damsire_count = popular_damsires[0]
    print()
    print(f"Testing with: {test_damsire_name} ({test_damsire_id})")
    print()

    cur.close()
    conn.close()

except Exception as e:
    print(f"❌ Database error: {e}")
    sys.exit(1)

# =========================================================================
# Test 2: Test /v1/dams/{dam_id}/progeny/results
# =========================================================================
print("=" * 100)
print("TEST 2: /v1/dams/{dam_id}/results")
print("=" * 100)
print()

endpoint = f"/dams/{test_dam_id}/results"
print(f"Endpoint: {endpoint}")
print(f"Dam: {test_dam_name} ({test_dam_id})")
print()

try:
    # Try fetching dam progeny results
    params = {
        'limit': 10  # Start with small limit for testing
    }

    response = api_client._make_request(endpoint, params)

    if response and isinstance(response, dict):
        print("✅ Endpoint exists and returned data!")
        print()

        # Save full response
        output_file = Path(__file__).parent.parent / "test_dam_progeny_response.json"
        with open(output_file, 'w') as f:
            json.dump(response, f, indent=2)
        print(f"📄 Full response saved to: {output_file}")
        print()

        # Analyze structure
        print("Response structure:")
        for key, value in response.items():
            if isinstance(value, list):
                print(f"  {key}: [{len(value)} items]")
                if len(value) > 0:
                    print(f"    Sample item keys: {list(value[0].keys())[:10]}")
            else:
                print(f"  {key}: {type(value).__name__}")
        print()

        # Show sample data
        if 'results' in response or 'progeny' in response or isinstance(response, list):
            data_key = 'results' if 'results' in response else ('progeny' if 'progeny' in response else None)
            data = response[data_key] if data_key else response

            if data and len(data) > 0:
                print(f"Sample record (first of {len(data)}):")
                print(json.dumps(data[0], indent=2))

    else:
        print("⚠️  Unexpected response format")
        print(f"Response: {response}")

except Exception as e:
    print(f"❌ Error testing dam progeny endpoint: {e}")
    import traceback
    traceback.print_exc()

print()

# =========================================================================
# Test 3: Test /v1/damsires/{damsire_id}/grandoffspring/results
# =========================================================================
print("=" * 100)
print("TEST 3: /v1/damsires/{damsire_id}/results")
print("=" * 100)
print()

endpoint = f"/damsires/{test_damsire_id}/results"
print(f"Endpoint: {endpoint}")
print(f"Damsire: {test_damsire_name} ({test_damsire_id})")
print()

try:
    # Try fetching damsire grandoffspring results
    params = {
        'limit': 10  # Start with small limit for testing
    }

    response = api_client._make_request(endpoint, params)

    if response and isinstance(response, dict):
        print("✅ Endpoint exists and returned data!")
        print()

        # Save full response
        output_file = Path(__file__).parent.parent / "test_damsire_grandoffspring_response.json"
        with open(output_file, 'w') as f:
            json.dump(response, f, indent=2)
        print(f"📄 Full response saved to: {output_file}")
        print()

        # Analyze structure
        print("Response structure:")
        for key, value in response.items():
            if isinstance(value, list):
                print(f"  {key}: [{len(value)} items]")
                if len(value) > 0:
                    print(f"    Sample item keys: {list(value[0].keys())[:10]}")
            else:
                print(f"  {key}: {type(value).__name__}")
        print()

        # Show sample data
        if 'results' in response or 'grandoffspring' in response or isinstance(response, list):
            data_key = 'results' if 'results' in response else ('grandoffspring' if 'grandoffspring' in response else None)
            data = response[data_key] if data_key else response

            if data and len(data) > 0:
                print(f"Sample record (first of {len(data)}):")
                print(json.dumps(data[0], indent=2))

    else:
        print("⚠️  Unexpected response format")
        print(f"Response: {response}")

except Exception as e:
    print(f"❌ Error testing damsire grandoffspring endpoint: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 100)
print("TESTING COMPLETE")
print("=" * 100)
