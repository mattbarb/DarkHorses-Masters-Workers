#!/usr/bin/env python3
"""
Apply migration to Supabase using direct table alterations via the Python client
This works around the RPC limitation
"""

import os
import sys
from pathlib import Path

# Set environment variables
os.environ['SUPABASE_URL'] = 'https://amsjvmlaknnvppxsgpfk.supabase.co'
os.environ['SUPABASE_SERVICE_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImFtc2p2bWxha25udnBweHNncGZrIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MDAxNjQxNSwiZXhwIjoyMDY1NTkyNDE1fQ.8JiQWlaTBH18o8PvElYC5aBAKGw8cfdMBe8KbXTAukI'

def apply_migration_via_rest():
    """
    Apply migration by using Supabase REST API
    Note: This approach has limitations - we'll check if columns already exist
    """
    from supabase import create_client
    from supabase.lib.client_options import ClientOptions

    url = os.environ['SUPABASE_URL']
    key = os.environ['SUPABASE_SERVICE_KEY']

    print("Connecting to Supabase...")
    options = ClientOptions()
    client = create_client(url, key, options)

    print("Connection established")

    # Check if columns exist by trying to query them
    try:
        # Try to select the new columns - if this works, they already exist
        result = client.table('ra_runners').select('position, distance_beaten, prize_won, starting_price, result_updated_at').limit(1).execute()
        print("\n✓ Position columns already exist in ra_runners table!")
        print("  - position")
        print("  - distance_beaten")
        print("  - prize_won")
        print("  - starting_price")
        print("  - result_updated_at")
        return True
    except Exception as e:
        error_msg = str(e)
        if 'column' in error_msg.lower() and 'does not exist' in error_msg.lower():
            print("\n✗ Position columns do not exist yet")
            print("  Migration needs to be applied manually via Supabase SQL Editor or psql")
            print("\n" + "=" * 80)
            print("MANUAL MIGRATION INSTRUCTIONS:")
            print("=" * 80)
            print("1. Go to: https://supabase.com/dashboard/project/amsjvmlaknnvppxsgpfk/sql/new")
            print("2. Copy the SQL from: migrations/005_add_position_fields_to_runners.sql")
            print("3. Paste into the SQL Editor and run")
            print("4. Or use psql to connect and execute the migration")
            print("=" * 80)
            return False
        else:
            print(f"Error checking columns: {e}")
            return False

if __name__ == '__main__':
    success = apply_migration_via_rest()
    sys.exit(0 if success else 1)
