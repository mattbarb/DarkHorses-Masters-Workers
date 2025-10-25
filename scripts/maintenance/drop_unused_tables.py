#!/usr/bin/env python3
"""
Drop Unused Tables Script
Drops ra_results and om_weather_hourly_forecast tables via Supabase

Usage:
    python3 scripts/drop_unused_tables.py

Environment Variables:
    SUPABASE_URL - Supabase project URL
    SUPABASE_SERVICE_KEY - Supabase service role key
"""

import os
import sys
from supabase import create_client

def drop_unused_tables():
    """Drop unused tables from the database"""

    # Get credentials from environment
    supabase_url = os.environ.get('SUPABASE_URL')
    supabase_key = os.environ.get('SUPABASE_SERVICE_KEY')

    if not supabase_url or not supabase_key:
        print('❌ Error: SUPABASE_URL and SUPABASE_SERVICE_KEY environment variables required')
        print('Example:')
        print('  export SUPABASE_URL="https://xxx.supabase.co"')
        print('  export SUPABASE_SERVICE_KEY="your_key"')
        sys.exit(1)

    # Create Supabase client
    supabase = create_client(supabase_url, supabase_key)

    tables_to_drop = [
        ('ra_results', '0 records - results data stored in ra_runners instead'),
        ('om_weather_hourly_forecast', '528 stale records - replaced by dh_weather_* tables')
    ]

    print('=' * 80)
    print('DROP UNUSED TABLES')
    print('=' * 80)
    print()

    # Check current state
    print('Checking current table state...')
    print()

    existing_tables = []
    for table_name, reason in tables_to_drop:
        try:
            result = supabase.table(table_name).select('*', count='exact').limit(1).execute()
            print(f'✅ {table_name} exists ({result.count:,} records)')
            print(f'   Reason for removal: {reason}')
            existing_tables.append(table_name)
        except Exception as e:
            print(f'⚠️  {table_name} does not exist (already dropped?)')
        print()

    if not existing_tables:
        print('✅ All tables already dropped. Nothing to do.')
        return

    # Confirm before dropping
    print('=' * 80)
    print(f'About to drop {len(existing_tables)} table(s):')
    for table in existing_tables:
        print(f'  - {table}')
    print()

    response = input('Are you sure you want to drop these tables? (yes/no): ').strip().lower()

    if response != 'yes':
        print('❌ Operation cancelled.')
        sys.exit(0)

    print()
    print('Dropping tables...')
    print()

    # Drop tables using raw SQL via RPC
    # Note: Supabase requires an RPC function for raw SQL execution
    # If this fails, instructions for manual execution will be provided

    dropped_tables = []
    failed_tables = []

    for table_name in existing_tables:
        try:
            # Attempt to drop via raw SQL
            # This requires the database to have an exec_sql function
            sql = f"DROP TABLE IF EXISTS {table_name};"

            # Try using PostgREST's exec_sql if available
            try:
                supabase.rpc('exec_sql', {'sql': sql}).execute()
                dropped_tables.append(table_name)
                print(f'✅ Dropped {table_name}')
            except Exception as rpc_error:
                # RPC method not available - provide manual instructions
                print(f'⚠️  Cannot drop {table_name} via RPC')
                print(f'   Error: {str(rpc_error)[:100]}')
                failed_tables.append((table_name, sql))

        except Exception as e:
            print(f'❌ Failed to drop {table_name}: {e}')
            failed_tables.append((table_name, f"DROP TABLE IF EXISTS {table_name};"))

    print()
    print('=' * 80)
    print('SUMMARY')
    print('=' * 80)
    print()

    if dropped_tables:
        print(f'✅ Successfully dropped {len(dropped_tables)} table(s):')
        for table in dropped_tables:
            print(f'   - {table}')
        print()

    if failed_tables:
        print(f'⚠️  {len(failed_tables)} table(s) require manual execution:')
        print()
        print('Execute the following SQL in Supabase Dashboard SQL Editor:')
        print('(https://supabase.com/dashboard/project/amsjvmlaknnvppxsgpfk)')
        print()
        print('-' * 80)
        for table, sql in failed_tables:
            print(f'-- Drop {table}')
            print(sql)
            print()
        print('-' * 80)
        print()

    # Verify tables are dropped
    print('Verifying...')
    print()

    for table_name in existing_tables:
        try:
            supabase.table(table_name).select('*').limit(1).execute()
            print(f'⚠️  {table_name} still exists (may need manual drop)')
        except Exception:
            print(f'✅ {table_name} confirmed dropped')

    print()
    print('Done!')
    print()


if __name__ == '__main__':
    try:
        drop_unused_tables()
    except KeyboardInterrupt:
        print('\n❌ Operation cancelled by user.')
        sys.exit(1)
    except Exception as e:
        print(f'\n❌ Error: {e}')
        import traceback
        traceback.print_exc()
        sys.exit(1)
