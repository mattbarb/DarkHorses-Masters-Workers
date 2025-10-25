#!/usr/bin/env python3
"""
Run Migration 011: Add Missing Runner Fields (Direct SQL Execution)
Executes the database migration by running SQL statements directly
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from supabase import create_client
from config.config import get_config
from utils.logger import get_logger

logger = get_logger('run_migration_011_direct')

def execute_sql(client, sql_statement, description=""):
    """Execute a single SQL statement"""
    try:
        if description:
            logger.info(f"  {description}...")

        # Use raw SQL execution via RPC
        result = client.rpc('exec', {'sql': sql_statement}).execute()
        return True

    except Exception as e:
        error_msg = str(e)
        if 'does not exist' in error_msg and 'exec' in error_msg:
            # exec function doesn't exist, we need to use direct psycopg2
            return None  # Signal that we need alternative approach
        logger.error(f"Error: {e}")
        return False

def run_migration_statements():
    """Execute migration as individual statements"""

    logger.info("=" * 80)
    logger.info("Running Migration 011: Add Missing Runner Fields")
    logger.info("=" * 80)

    # Load config
    config = get_config()

    # Initialize Supabase client
    client = create_client(config.supabase.url, config.supabase.service_key)

    logger.info("\nAdding columns to ra_runners table...")

    # Execute each ALTER TABLE statement individually
    statements = [
        ("ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS starting_price_decimal DECIMAL(10,2);",
         "Add starting_price_decimal"),
        ("ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS race_comment TEXT;",
         "Add race_comment"),
        ("ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS jockey_silk_url TEXT;",
         "Add jockey_silk_url"),
        ("ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS overall_beaten_distance DECIMAL(10,2);",
         "Add overall_beaten_distance"),
        ("ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS jockey_claim_lbs INTEGER;",
         "Add jockey_claim_lbs"),
        ("ALTER TABLE ra_runners ADD COLUMN IF NOT EXISTS weight_stones_lbs VARCHAR(10);",
         "Add weight_stones_lbs"),
    ]

    logger.info("\n" + "-" * 80)
    logger.info("MANUAL MIGRATION REQUIRED")
    logger.info("-" * 80)
    logger.info("\nSupabase requires SQL execution via the dashboard or psql.")
    logger.info("\nOption 1: Use Supabase SQL Editor (Recommended)")
    logger.info("-" * 80)
    logger.info("1. Go to: https://supabase.com/dashboard/project/<your-project>/sql")
    logger.info("2. Copy and paste the migration SQL from:")
    logger.info("   migrations/011_add_missing_runner_fields.sql")
    logger.info("3. Click 'Run' to execute")
    logger.info("")
    logger.info("Option 2: Use psql command line")
    logger.info("-" * 80)
    logger.info("Run these commands one by one:\n")

    for sql, desc in statements:
        print(f"-- {desc}")
        print(sql)
        print()

    logger.info("\nOption 3: Quick ALTER TABLE commands")
    logger.info("-" * 80)

    quick_sql = """
-- Add all columns in one statement
ALTER TABLE ra_runners
  ADD COLUMN IF NOT EXISTS starting_price_decimal DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS race_comment TEXT,
  ADD COLUMN IF NOT EXISTS jockey_silk_url TEXT,
  ADD COLUMN IF NOT EXISTS overall_beaten_distance DECIMAL(10,2),
  ADD COLUMN IF NOT EXISTS jockey_claim_lbs INTEGER,
  ADD COLUMN IF NOT EXISTS weight_stones_lbs VARCHAR(10);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_runners_sp_decimal
  ON ra_runners(starting_price_decimal)
  WHERE starting_price_decimal IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_runners_ovr_btn
  ON ra_runners(overall_beaten_distance)
  WHERE overall_beaten_distance IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_runners_jockey_claim
  ON ra_runners(jockey_claim_lbs)
  WHERE jockey_claim_lbs > 0;
"""

    print(quick_sql)

    logger.info("\n" + "=" * 80)
    logger.info("After running the migration, verify with:")
    logger.info("  python3 scripts/test_enhanced_data_capture.py")
    logger.info("=" * 80)

    return False  # Indicate manual action required

def main():
    run_migration_statements()
    logger.info("\nPlease run the migration SQL manually using one of the options above.")
    sys.exit(1)  # Exit with error code to indicate manual intervention needed

if __name__ == '__main__':
    main()
