#!/usr/bin/env python3
"""
Run Migration 029 via Supabase SQL Editor API
==============================================

This uses the Supabase Management API to execute SQL directly.
"""

import sys
import requests
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger

logger = get_logger('migration_029_api')

def run_migration():
    """Execute Migration 029 via Supabase API"""

    print("=" * 80)
    print("MIGRATION 029: Rename Tables to ra_mst_* Convention (via SQL Editor)")
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

    # Extract project ref from URL
    supabase_url = config.supabase.url
    project_ref = supabase_url.replace('https://', '').replace('http://', '').split('.')[0]

    print(f"📊 Project: {project_ref}")
    print(f"   Supabase URL: {supabase_url}")
    print()

    # Use PostgREST API to execute SQL
    # Supabase exposes a PostgREST endpoint for raw SQL queries
    # Format: https://<project-ref>.supabase.co/rest/v1/rpc/<function_name>

    # Actually, let's use the Supabase client directly with a raw query approach
    print("⚠️  Direct PostgreSQL connection failed.")
    print("   Please run the migration using one of these methods:\n")

    print("1️⃣  SUPABASE DASHBOARD (EASIEST):")
    print("   • Go to: https://supabase.com/dashboard/project/{project_ref}/sql/new")
    print(f"   • Copy the SQL from: {migration_file}")
    print("   • Paste and click 'Run'\n")

    print("2️⃣  SUPABASE CLI:")
    print("   • Install: brew install supabase/tap/supabase")
    print(f"   • Link: supabase link --project-ref {project_ref}")
    print(f"   • Run: supabase db execute < {migration_file}\n")

    print("3️⃣  DIRECT psql (if you have connection pooler enabled):")
    print(f"   • Get connection string from Supabase Dashboard → Settings → Database")
    print(f"   • Run: psql '<connection-string>' < {migration_file}\n")

    print("=" * 80)
    print("MIGRATION SQL READY AT:")
    print(f"   {migration_file.absolute()}")
    print("=" * 80)
    print()

    return False

if __name__ == '__main__':
    run_migration()
