#!/usr/bin/env python3
"""Apply migration 027 to make horse_name nullable in ra_mst_runners"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('apply_migration_027')

def main():
    """Apply the migration"""
    config = get_config()

    # Create database client
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Read migration SQL
    migration_file = Path(__file__).parent.parent / 'migrations' / '027_make_horse_name_nullable_in_runners.sql'

    with open(migration_file, 'r') as f:
        sql = f.read()

    logger.info("=" * 80)
    logger.info("APPLYING MIGRATION 027")
    logger.info("=" * 80)
    logger.info(f"Migration file: {migration_file}")
    logger.info("\nSQL to execute:")
    logger.info(sql)
    logger.info("=" * 80)

    try:
        # Execute the ALTER TABLE statement
        result = db_client.client.rpc('exec_sql', {'sql': sql}).execute()
        logger.info("✅ Migration applied successfully!")
        return True
    except Exception as e:
        logger.error(f"❌ Error applying migration via RPC: {e}")
        logger.info("\nNote: This may require manual application via Supabase SQL Editor")
        logger.info("Or use psql command:")
        logger.info(f"\npsql $SUPABASE_URL -f {migration_file}")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
