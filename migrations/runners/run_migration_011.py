#!/usr/bin/env python3
"""
Run Migration 011: Add Missing Runner Fields
Executes the database migration to add 6 new fields to ra_mst_runners
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('run_migration_011')

def run_migration():
    """Execute migration 011"""

    logger.info("=" * 80)
    logger.info("Running Migration 011: Add Missing Runner Fields")
    logger.info("=" * 80)

    # Load config
    config = get_config()

    # Initialize Supabase client
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Read migration SQL
    migration_file = Path(__file__).parent.parent / 'migrations' / '011_add_missing_runner_fields.sql'

    if not migration_file.exists():
        logger.error(f"Migration file not found: {migration_file}")
        return False

    logger.info(f"Reading migration from: {migration_file}")

    with open(migration_file, 'r') as f:
        migration_sql = f.read()

    logger.info(f"Migration SQL length: {len(migration_sql)} characters")

    # Execute migration using raw SQL
    try:
        logger.info("Executing migration...")

        # Use the Supabase client's underlying connection
        result = db_client.client.postgrest.session.post(
            f"{config.supabase.url}/rest/v1/rpc/exec_sql",
            json={"query": migration_sql},
            headers={
                "apikey": config.supabase.service_key,
                "Authorization": f"Bearer {config.supabase.service_key}"
            }
        )

        if result.status_code == 200:
            logger.info("✓ Migration executed successfully!")
            logger.info("=" * 80)
            logger.info("Migration 011 Complete - 6 new fields added to ra_mst_runners:")
            logger.info("  1. starting_price_decimal (DECIMAL)")
            logger.info("  2. race_comment (TEXT)")
            logger.info("  3. jockey_silk_url (TEXT)")
            logger.info("  4. overall_beaten_distance (DECIMAL)")
            logger.info("  5. jockey_claim_lbs (INTEGER)")
            logger.info("  6. weight_stones_lbs (VARCHAR)")
            logger.info("=" * 80)
            return True
        else:
            logger.error(f"Migration failed with status {result.status_code}")
            logger.error(f"Response: {result.text}")
            return False

    except Exception as e:
        logger.error(f"Error executing migration: {e}", exc_info=True)
        logger.info("\n" + "=" * 80)
        logger.info("ALTERNATIVE: Run migration manually using psql")
        logger.info("=" * 80)
        logger.info("Connect to Supabase and run:")
        logger.info(f"  psql <connection_string> -f {migration_file}")
        logger.info("\nOr use the Supabase SQL Editor in the dashboard")
        logger.info("=" * 80)
        return False

def main():
    success = run_migration()

    if success:
        logger.info("\n✓ Next steps:")
        logger.info("  1. Test enhanced data capture: python3 scripts/test_enhanced_data_capture.py")
        logger.info("  2. Fetch fresh results: python3 main.py --entities results")
        logger.info("  3. Verify field population in database")
        sys.exit(0)
    else:
        logger.error("\n✗ Migration failed - see logs above")
        sys.exit(1)

if __name__ == '__main__':
    main()
