#!/usr/bin/env python3
"""
Run Migration 029 Directly via Supabase Client
===============================================

This executes the migration using Supabase's service role key
to run raw SQL commands.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('migration_direct')

def run_migration(auto_confirm=False):
    """Execute Migration 029 directly via Supabase client"""

    print("=" * 80)
    print("MIGRATION 029: Rename Tables to ra_mst_* Convention")
    print("=" * 80)
    print()

    # Load config
    try:
        config = get_config()
        logger.info("Configuration loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return False

    # Connect to Supabase
    try:
        db_client = SupabaseReferenceClient(
            url=config.supabase.url,
            service_key=config.supabase.service_key
        )
        logger.info("✅ Connected to Supabase")
        print("✅ Connected to Supabase\n")
    except Exception as e:
        logger.error(f"Failed to connect: {e}")
        return False

    # Read migration SQL
    migration_file = Path(__file__).parent / 'sql' / '029_rename_three_tables_to_mst.sql'

    try:
        with open(migration_file, 'r') as f:
            full_sql = f.read()
        logger.info(f"Loaded migration SQL ({len(full_sql)} characters)")
    except Exception as e:
        logger.error(f"Failed to read migration file: {e}")
        return False

    # Split into individual statements (exclude comments and verification queries)
    sql_statements = []
    current_statement = []
    in_comment_block = False

    for line in full_sql.split('\n'):
        stripped = line.strip()

        # Skip comment blocks
        if '-- ============' in line or '-- PART' in line or '-- Step' in line:
            continue

        # Skip single-line comments that are just comments (keep inline comments)
        if stripped.startswith('--') and not any(keyword in current_statement for keyword in ['ALTER', 'UPDATE', 'COMMENT']):
            continue

        # Skip verification queries (commented out)
        if '-- SELECT' in line or '-- Verify' in line:
            continue

        # Add line to current statement
        if stripped:
            current_statement.append(line)

        # If we hit a semicolon, that's the end of a statement
        if stripped.endswith(';') and current_statement:
            statement = '\n'.join(current_statement)
            # Only add if it's a real SQL statement
            if any(keyword in statement.upper() for keyword in ['ALTER', 'UPDATE', 'COMMENT', 'DO']):
                sql_statements.append(statement)
            current_statement = []

    print(f"📋 Parsed {len(sql_statements)} SQL statements\n")

    # Pre-migration check
    print("🔍 Pre-migration verification...")
    try:
        # Check old tables exist
        races_check = db_client.client.table('ra_races').select('*', count='exact').limit(1).execute()
        runners_check = db_client.client.table('ra_runners').select('*', count='exact').limit(1).execute()
        results_check = db_client.client.table('ra_race_results').select('*', count='exact').limit(1).execute()

        print(f"   ✅ ra_races: {races_check.count:,} rows")
        print(f"   ✅ ra_runners: {runners_check.count:,} rows")
        print(f"   ✅ ra_race_results: {results_check.count:,} rows")
        print()
    except Exception as e:
        print(f"   ⚠️  Could not verify existing tables: {e}\n")

    # Confirm execution
    print("⚠️  READY TO EXECUTE MIGRATION")
    print("   This will rename:")
    print("      ra_races → ra_mst_races")
    print("      ra_runners → ra_mst_runners")
    print("      ra_race_results → ra_mst_race_results")
    print()

    if not auto_confirm:
        try:
            response = input("   Proceed with migration? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("\n   Migration cancelled by user")
                return False
        except EOFError:
            print("   Non-interactive mode detected - use --confirm flag")
            return False
    else:
        print("   ✅ Auto-confirmed - proceeding with migration...")

    # Execute each statement
    print("\n🚀 Executing migration...")
    print(f"   Total statements: {len(sql_statements)}\n")

    success_count = 0
    failed_statements = []

    for i, statement in enumerate(sql_statements, 1):
        try:
            # Extract statement type for display
            statement_type = statement.split()[0].upper()

            # Use Supabase's rpc function to execute raw SQL
            # Note: This requires a custom function in Supabase or we use postgrest directly
            result = db_client.client.rpc('exec_sql', {'query': statement}).execute()

            print(f"   ✅ [{i}/{len(sql_statements)}] {statement_type} executed")
            success_count += 1

        except Exception as e:
            error_msg = str(e)

            # Check if it's just because rpc function doesn't exist
            if 'exec_sql' in error_msg or 'function' in error_msg.lower():
                print(f"\n   ℹ️  RPC method not available. Trying alternative approach...\n")

                # Alternative: Use the PostgREST API directly
                # This requires executing via the REST API endpoint
                print("   ⚠️  Cannot execute SQL directly via Supabase Python client.")
                print("   The Supabase client doesn't support raw SQL execution.\n")
                print("   Please use one of these methods:")
                print("   1. Supabase SQL Editor (Dashboard)")
                print("   2. Supabase CLI: supabase db execute < migrations/sql/029_rename_three_tables_to_mst.sql")
                print("   3. Direct psql connection\n")
                print(f"   Migration SQL is ready at:")
                print(f"   {migration_file.absolute()}\n")
                return False
            else:
                print(f"   ❌ [{i}/{len(sql_statements)}] Failed: {error_msg}")
                failed_statements.append((i, statement_type, error_msg))

    # Summary
    print(f"\n   Executed: {success_count}/{len(sql_statements)} statements")

    if failed_statements:
        print(f"   Failed: {len(failed_statements)} statements")
        for stmt_num, stmt_type, error in failed_statements:
            print(f"      - Statement {stmt_num} ({stmt_type}): {error}")
        return False

    # Post-migration verification
    print("\n🔍 Post-migration verification...")
    try:
        # Check new tables exist
        new_races = db_client.client.table('ra_mst_races').select('*', count='exact').limit(1).execute()
        new_runners = db_client.client.table('ra_mst_runners').select('*', count='exact').limit(1).execute()
        new_results = db_client.client.table('ra_mst_race_results').select('*', count='exact').limit(1).execute()

        print(f"   ✅ ra_mst_races: {new_races.count:,} rows")
        print(f"   ✅ ra_mst_runners: {new_runners.count:,} rows")
        print(f"   ✅ ra_mst_race_results: {new_results.count:,} rows")

        # Try to query old tables (should fail)
        try:
            db_client.client.table('ra_races').select('*').limit(1).execute()
            print("   ⚠️  Old table 'ra_races' still exists!")
        except:
            print("   ✅ Old table 'ra_races' removed")

    except Exception as e:
        print(f"   ⚠️  Verification issue: {e}")

    print("\n" + "=" * 80)
    print("✅ MIGRATION 029 COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("   1. Test: python3 main.py --entities races --test")
    print("   2. Test: python3 main.py --entities results --test")
    print("   3. Commit: git add -A && git commit -m 'Migration 029 complete'")
    print()

    return True


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Run Migration 029')
    parser.add_argument('--confirm', action='store_true', help='Auto-confirm execution (non-interactive)')
    args = parser.parse_args()

    success = run_migration(auto_confirm=args.confirm)
    sys.exit(0 if success else 1)
