#!/usr/bin/env python3
"""
Run Migration 029: Rename Tables to ra_mst_* Convention
========================================================

This script executes the migration to rename:
- ra_races → ra_mst_races
- ra_runners → ra_mst_runners
- ra_race_results → ra_mst_race_results

Usage:
    python3 migrations/run_migration_029.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger

logger = get_logger('migration_029')

def run_migration():
    """Execute Migration 029"""

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

    # Read migration SQL
    migration_file = Path(__file__).parent / 'sql' / '029_rename_three_tables_to_mst.sql'

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    try:
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        logger.info(f"Loaded migration SQL ({len(migration_sql)} characters)")
    except Exception as e:
        logger.error(f"Failed to read migration file: {e}")
        return False

    # Connect to database using psycopg2
    print("\n📊 Connecting to Supabase database...")

    try:
        import psycopg2
        from urllib.parse import urlparse

        # Parse Supabase URL to get connection details
        supabase_url = config.supabase.url
        # Extract project ID from URL (e.g., amsjvmlaknnvppxsgpfk from https://amsjvmlaknnvppxsgpfk.supabase.co)
        hostname = supabase_url.replace('https://', '').replace('http://', '')
        project_id = hostname.split('.')[0]

        # Supabase direct database connection format
        # db.<project-ref>.supabase.co:5432
        db_host = f"db.{project_id}.supabase.co"

        print(f"   Project ID: {project_id}")
        print(f"   Database Host: {db_host}")
        print(f"   Connecting (this may take a moment)...")

        conn = psycopg2.connect(
            host=db_host,
            port=5432,  # Direct connection port
            database="postgres",
            user="postgres",
            password=config.supabase.db_password,
            connect_timeout=30
        )

        conn.autocommit = False
        cursor = conn.cursor()

        logger.info("✅ Connected to database")
        print("   ✅ Connected successfully!\n")

    except ImportError:
        print("\n❌ ERROR: psycopg2 is not installed")
        print("\nPlease install it with:")
        print("   pip install psycopg2-binary")
        print("\nOr use one of these alternative methods:")
        print("   1. Supabase CLI: supabase db execute < migrations/sql/029_rename_three_tables_to_mst.sql")
        print("   2. SQL Editor in Supabase Dashboard")
        print("   3. Direct psql connection")
        print("\nSee migrations/RUN_MIGRATION_029.md for details")
        return False
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        print(f"\n❌ Connection failed: {e}")
        print("\nPlease check:")
        print("   1. Your .env.local file has correct credentials")
        print("   2. Your database password is set (DB_PASSWORD in .env.local)")
        print("   3. Your network allows connection to Supabase")
        print("\nAlternatively, use Supabase CLI or SQL Editor")
        print("See migrations/RUN_MIGRATION_029.md for details")
        return False

    # Pre-migration verification
    print("🔍 Pre-migration verification...")

    try:
        cursor.execute("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_name IN ('ra_races', 'ra_runners', 'ra_race_results')
            ORDER BY table_name;
        """)

        old_tables = cursor.fetchall()

        if len(old_tables) != 3:
            print(f"\n⚠️  WARNING: Expected 3 tables, found {len(old_tables)}")
            print("   Tables found:", [t[0] for t in old_tables])

            response = input("\n   Continue anyway? (yes/no): ")
            if response.lower() not in ['yes', 'y']:
                print("   Migration cancelled")
                cursor.close()
                conn.close()
                return False
        else:
            print("   ✅ Found all 3 tables to rename:")
            for table_name, col_count in old_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print(f"      - {table_name}: {row_count:,} rows, {col_count} columns")

    except Exception as e:
        logger.error(f"Pre-migration check failed: {e}")
        print(f"   ⚠️  Could not verify existing tables: {e}")
        cursor.close()
        conn.close()
        return False

    # Confirm execution
    print("\n⚠️  READY TO EXECUTE MIGRATION")
    print("   This will rename:")
    print("      ra_races → ra_mst_races")
    print("      ra_runners → ra_mst_runners")
    print("      ra_race_results → ra_mst_race_results")
    print()

    response = input("   Proceed with migration? (yes/no): ")

    if response.lower() not in ['yes', 'y']:
        print("\n   Migration cancelled by user")
        cursor.close()
        conn.close()
        return False

    # Execute migration
    print("\n🚀 Executing migration...")

    try:
        cursor.execute(migration_sql)
        conn.commit()

        logger.info("✅ Migration executed successfully")
        print("   ✅ Migration completed successfully!\n")

    except Exception as e:
        logger.error(f"Migration failed: {e}")
        print(f"\n   ❌ Migration failed: {e}")
        print("\n   Rolling back...")

        try:
            conn.rollback()
            print("   ✅ Rollback successful")
        except Exception as rollback_error:
            print(f"   ❌ Rollback failed: {rollback_error}")

        cursor.close()
        conn.close()
        return False

    # Post-migration verification
    print("🔍 Post-migration verification...")

    try:
        # Check new tables exist
        cursor.execute("""
            SELECT table_name,
                   (SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            AND table_name IN ('ra_mst_races', 'ra_mst_runners', 'ra_mst_race_results')
            ORDER BY table_name;
        """)

        new_tables = cursor.fetchall()

        if len(new_tables) == 3:
            print("   ✅ New tables created:")
            for table_name, col_count in new_tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                row_count = cursor.fetchone()[0]
                print(f"      - {table_name}: {row_count:,} rows, {col_count} columns")
        else:
            print(f"   ⚠️  Expected 3 new tables, found {len(new_tables)}")

        # Check old tables are gone
        cursor.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name IN ('ra_races', 'ra_runners', 'ra_race_results');
        """)

        old_tables_remaining = cursor.fetchall()

        if len(old_tables_remaining) == 0:
            print("   ✅ Old table names removed")
        else:
            print(f"   ⚠️  Old tables still exist: {[t[0] for t in old_tables_remaining]}")

        # Check metadata tracking
        cursor.execute("""
            SELECT table_name, COUNT(*) as update_count
            FROM ra_metadata_tracking
            WHERE table_name IN ('ra_mst_races', 'ra_mst_runners', 'ra_mst_race_results')
            GROUP BY table_name
            ORDER BY table_name;
        """)

        metadata_updates = cursor.fetchall()

        if metadata_updates:
            print("   ✅ Metadata tracking updated:")
            for table_name, count in metadata_updates:
                print(f"      - {table_name}: {count} tracking records")

    except Exception as e:
        logger.error(f"Post-migration verification failed: {e}")
        print(f"   ⚠️  Verification failed: {e}")

    # Close connection
    cursor.close()
    conn.close()

    print("\n" + "=" * 80)
    print("✅ MIGRATION 029 COMPLETE")
    print("=" * 80)
    print()
    print("Next steps:")
    print("   1. Test application: python3 main.py --entities races --test")
    print("   2. Test results: python3 main.py --entities results --test")
    print("   3. Commit changes: git add -A && git commit -m 'Migration 029: Rename to ra_mst_* convention'")
    print()

    return True


if __name__ == '__main__':
    success = run_migration()
    sys.exit(0 if success else 1)
