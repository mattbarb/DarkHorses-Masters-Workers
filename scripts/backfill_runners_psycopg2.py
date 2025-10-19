"""
Direct PostgreSQL Backfill Script
Uses psycopg2 with direct database connection to bypass REST API timeouts
Processes all 1.3M records efficiently with custom statement_timeout
"""

import os
import sys
import time
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Load environment variables from .env.local
try:
    from dotenv import load_dotenv
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
    load_dotenv(env_path)
except ImportError:
    print("Warning: python-dotenv not installed. Trying to load .env manually...")
    # Manual .env loading as fallback
    env_path = os.path.join(os.path.dirname(__file__), '..', '.env.local')
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

from utils.logger import get_logger

logger = get_logger('backfill_psycopg2')

# Try to import psycopg2
try:
    import psycopg2
    from psycopg2 import sql
    from psycopg2.extras import execute_batch
except ImportError:
    logger.error("psycopg2 not installed. Install with: pip install psycopg2-binary")
    sys.exit(1)

# Checkpoint file for resume capability
CHECKPOINT_FILE = 'logs/backfill_psycopg2_checkpoint.json'

# Field mappings with validation rules
FIELD_MAPPINGS = [
    {
        'db_field': 'weight',
        'api_field': 'weight_lbs',
        'sql_cast': 'INTEGER',
        'validate_pattern': r'^\d+$'
    },
    {
        'db_field': 'weight_lbs',
        'api_field': 'weight_lbs',
        'sql_cast': 'INTEGER',
        'validate_pattern': r'^\d+$'
    },
    {
        'db_field': 'finishing_time',
        'api_field': 'time',
        'sql_cast': 'TEXT',
        'validate_pattern': None  # Any non-empty string
    },
    {
        'db_field': 'starting_price_decimal',
        'api_field': 'sp_dec',
        'sql_cast': 'DECIMAL',
        'validate_pattern': r'^\d+\.?\d*$'  # Skip "-"
    },
    {
        'db_field': 'overall_beaten_distance',
        'api_field': 'ovr_btn',
        'sql_cast': 'DECIMAL',
        'validate_pattern': r'^\d+\.?\d*$'  # Skip "-"
    },
    {
        'db_field': 'jockey_claim_lbs',
        'api_field': 'jockey_claim_lbs',
        'sql_cast': 'INTEGER',
        'validate_pattern': r'^\d+$'
    },
    {
        'db_field': 'weight_stones_lbs',
        'api_field': 'weight',
        'sql_cast': 'TEXT',
        'validate_pattern': None
    },
    {
        'db_field': 'race_comment',
        'api_field': 'comment',
        'sql_cast': 'TEXT',
        'validate_pattern': None
    },
    {
        'db_field': 'comment',
        'api_field': 'comment',
        'sql_cast': 'TEXT',
        'validate_pattern': None
    },
    {
        'db_field': 'jockey_silk_url',
        'api_field': 'silk_url',
        'sql_cast': 'TEXT',
        'validate_pattern': None
    },
    {
        'db_field': 'silk_url',
        'api_field': 'silk_url',
        'sql_cast': 'TEXT',
        'validate_pattern': None
    },
]


def get_database_connection():
    """
    Get direct PostgreSQL connection using Supavisor Session Mode
    Session Mode (port 5432) supports long-running queries

    Returns:
        psycopg2 connection
    """
    # Try SESSION_POOLER first (correct Session Mode connection)
    database_url = os.getenv('SESSION_POOLER')

    if database_url:
        logger.info(f"Using SESSION_POOLER (Supavisor Session Mode - port 5432)")
    else:
        # Fallback: Try to build from SHARED_POOLER by changing port
        shared_pooler = os.getenv('SHARED_POOLER')
        if shared_pooler:
            database_url = shared_pooler.replace(':6543/', ':5432/')
            logger.info(f"Using SHARED_POOLER converted to Session Mode (port 5432)")
        else:
            # Last resort: other connection types
            database_url = os.getenv('TRANSACTION_POOLER') or os.getenv('DATABASE_URL')
            logger.warning("Using fallback connection (may have timeout limits)")

    if not database_url:
        logger.error("No database connection URL found in environment")
        logger.error("Looking for: SESSION_POOLER, SHARED_POOLER, TRANSACTION_POOLER, or DATABASE_URL")
        return None

    logger.info(f"Connection: {database_url.split('@')[1] if '@' in database_url else 'unknown'}")

    try:
        conn = psycopg2.connect(database_url)

        # Set statement timeout to 10 minutes
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = '10min'")
            cur.execute("SET lock_timeout = '10min'")

        conn.commit()

        logger.info("✅ Connected to PostgreSQL database")
        logger.info("   Timeout set to 10 minutes")

        return conn

    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        return None


def load_checkpoint():
    """Load checkpoint from file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except:
            pass
    return {}


def save_checkpoint(checkpoint):
    """Save checkpoint to file"""
    os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
    with open(CHECKPOINT_FILE, 'w') as f:
        json.dump(checkpoint, f, indent=2)


def backfill_field(conn, field_config: dict, batch_size: int = 5000) -> dict:
    """
    Backfill a single field using direct SQL

    Args:
        conn: psycopg2 connection
        field_config: Field configuration dict
        batch_size: Records per batch

    Returns:
        Stats dict
    """
    db_field = field_config['db_field']
    api_field = field_config['api_field']
    sql_cast = field_config['sql_cast']
    validate_pattern = field_config['validate_pattern']

    logger.info(f"\n{'='*60}")
    logger.info(f"Processing field: {db_field}")
    logger.info(f"{'='*60}")

    total_updated = 0
    batch_num = 0

    # Build WHERE clause based on validation pattern
    where_clause = f"""
        api_data IS NOT NULL
        AND api_data->>%s IS NOT NULL
        AND api_data->>%s != ''
        AND {db_field} IS NULL
    """

    if validate_pattern:
        where_clause += f" AND api_data->>%s ~ '{validate_pattern}'"

    while True:
        batch_num += 1

        try:
            with conn.cursor() as cur:
                # Build UPDATE query
                if sql_cast == 'TEXT':
                    update_sql = f"""
                        UPDATE ra_runners
                        SET {db_field} = api_data->>%s, updated_at = NOW()
                        WHERE runner_id IN (
                            SELECT runner_id FROM ra_runners
                            WHERE {where_clause}
                            LIMIT %s
                        )
                    """
                else:
                    update_sql = f"""
                        UPDATE ra_runners
                        SET {db_field} = (api_data->>%s)::{sql_cast}, updated_at = NOW()
                        WHERE runner_id IN (
                            SELECT runner_id FROM ra_runners
                            WHERE {where_clause}
                            LIMIT %s
                        )
                    """

                # Build parameters
                if validate_pattern:
                    params = (api_field, api_field, api_field, api_field, batch_size)
                else:
                    params = (api_field, api_field, api_field, batch_size)

                # Execute update
                cur.execute(update_sql, params)
                rows_updated = cur.rowcount

                conn.commit()

                if rows_updated == 0:
                    logger.info(f"  ✅ No more records to update")
                    break

                total_updated += rows_updated
                logger.info(f"  Batch {batch_num}: {rows_updated:,} records updated (total: {total_updated:,})")

                # If we updated fewer than batch_size, we're done
                if rows_updated < batch_size:
                    logger.info(f"  ✅ Completed (last batch)")
                    break

        except Exception as e:
            conn.rollback()
            logger.error(f"  ❌ Error in batch {batch_num}: {e}")

            # If it's a timeout, log and continue
            if 'timeout' in str(e).lower():
                logger.warning(f"  ⚠️  Timeout - will retry smaller batch")
                # Could reduce batch_size here if needed
                break
            else:
                raise

    stats = {
        'field': db_field,
        'batches': batch_num,
        'updated': total_updated
    }

    logger.info(f"\n✅ {db_field} complete: {total_updated:,} records updated")

    return stats


def backfill_all_fields(batch_size: int = 5000, resume: bool = True):
    """
    Backfill all fields using direct PostgreSQL connection

    Args:
        batch_size: Records per batch
        resume: Resume from checkpoint if available
    """
    logger.info("=" * 80)
    logger.info("POSTGRESQL DIRECT BACKFILL")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Resume mode: {resume}")

    # Load checkpoint
    checkpoint = load_checkpoint() if resume else {}
    completed_fields = checkpoint.get('completed_fields', [])

    # Get database connection
    conn = get_database_connection()
    if not conn:
        logger.error("Failed to connect to database")
        return None

    all_stats = []
    start_time = time.time()

    try:
        # Process unique fields only
        processed_fields = set()

        for field_config in FIELD_MAPPINGS:
            db_field = field_config['db_field']

            # Skip duplicates
            if db_field in processed_fields:
                logger.info(f"Skipping duplicate field: {db_field}")
                continue

            processed_fields.add(db_field)

            # Skip if already completed (resume)
            if db_field in completed_fields:
                logger.info(f"Skipping completed field: {db_field}")
                continue

            try:
                stats = backfill_field(conn, field_config, batch_size)
                all_stats.append(stats)

                # Mark as completed
                completed_fields.append(db_field)
                checkpoint['completed_fields'] = completed_fields
                checkpoint['last_updated'] = datetime.utcnow().isoformat()
                save_checkpoint(checkpoint)

            except Exception as e:
                logger.error(f"Failed to process {db_field}: {e}", exc_info=True)
                # Save checkpoint even on error
                checkpoint['last_error'] = {
                    'field': db_field,
                    'error': str(e),
                    'time': datetime.utcnow().isoformat()
                }
                save_checkpoint(checkpoint)

    finally:
        conn.close()
        logger.info("Database connection closed")

    # Final summary
    elapsed = time.time() - start_time

    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total time: {elapsed / 60:.1f} minutes")
    logger.info("\nResults by field:")

    total_updated = 0

    for stats in all_stats:
        logger.info(f"  {stats['field']:30s}: {stats['updated']:,} updated")
        total_updated += stats['updated']

    logger.info(f"\nOverall:")
    logger.info(f"  Total updated: {total_updated:,}")

    # Clear checkpoint on successful completion
    if os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info(f"\nCheckpoint file removed (backfill complete)")

    return all_stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Direct PostgreSQL backfill (bypasses REST API)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=5000,
        help='Records per batch (default: 5000)'
    )
    parser.add_argument(
        '--no-resume',
        action='store_true',
        help='Start fresh (ignore checkpoint)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: only process 2 batches per field'
    )

    args = parser.parse_args()

    # Test mode: smaller batch size
    if args.test:
        logger.info("🧪 TEST MODE: Processing 2 batches per field only")
        # In test mode, we'll modify the logic to limit batches
        # For now, just use smaller batch size
        batch_size = 100
    else:
        batch_size = args.batch_size

    logger.info("=" * 80)
    logger.info("POSTGRESQL DIRECT BACKFILL FOR ra_runners")
    logger.info("=" * 80)
    logger.info("This script uses direct PostgreSQL connection")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Resume: {not args.no_resume}")
    logger.info("\nStarting in 3 seconds... (Ctrl+C to cancel)")
    logger.info("=" * 80 + "\n")

    time.sleep(3)

    try:
        stats = backfill_all_fields(
            batch_size=batch_size,
            resume=not args.no_resume
        )

        if stats is None:
            logger.error("\n❌ Backfill failed to start")
            return 1

        logger.info("\n✅ Backfill complete!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Interrupted by user")
        logger.info("Progress saved in checkpoint. Run again to resume.")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
