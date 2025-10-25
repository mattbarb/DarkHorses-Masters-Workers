#!/usr/bin/env python3
"""
Apply Migration 030: Add region columns to pedigree tables
Uses Supabase client to execute SQL statements individually
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from supabase import create_client
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

client = create_client(url, key)

print('=' * 80)
print('MIGRATION 030: Adding region columns to pedigree tables')
print('=' * 80)

# Execute each ALTER TABLE statement separately
statements = [
    {
        'name': 'Add region to ra_mst_sires',
        'sql': 'ALTER TABLE ra_mst_sires ADD COLUMN IF NOT EXISTS region VARCHAR(10);'
    },
    {
        'name': 'Add region to ra_mst_dams',
        'sql': 'ALTER TABLE ra_mst_dams ADD COLUMN IF NOT EXISTS region VARCHAR(10);'
    },
    {
        'name': 'Add region to ra_mst_damsires',
        'sql': 'ALTER TABLE ra_mst_damsires ADD COLUMN IF NOT EXISTS region VARCHAR(10);'
    },
]

for stmt in statements:
    print(f"\n{stmt['name']}...")
    try:
        # Use raw SQL execution via PostgREST
        result = client.table('ra_mst_sires').select('*').limit(0).execute()

        # Since direct SQL isn't supported, we'll use the REST API directly
        import requests

        # Construct the request
        headers = {
            'apikey': key,
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }

        # Use Supabase REST API to execute SQL
        # This is a workaround - ideally use Supabase SQL editor
        print(f"  ⚠️  Cannot execute via Python client")
        print(f"  📝 SQL: {stmt['sql']}")

    except Exception as e:
        print(f"  ❌ Error: {e}")

print('\n' + '=' * 80)
print('MIGRATION NEEDS MANUAL EXECUTION')
print('=' * 80)
print('\nPlease run the following SQL in Supabase SQL Editor:')
print('\n```sql')
with open('migrations/030_add_region_to_pedigree_tables.sql', 'r') as f:
    print(f.read())
print('```')
