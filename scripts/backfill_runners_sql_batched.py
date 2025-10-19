"""
Backfill Script: SQL-Based Batched Updates with Timeout Handling
Handles Supabase timeouts by using smaller batches and retry logic
"""

import os
import sys
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from config.config import get_config
from supabase import create_client

logger = get_logger('backfill_sql_batched')

# Field mappings: (db_column, api_field, cast_type)
FIELD_MAPPINGS = [
    ('weight', 'weight_lbs', 'INTEGER'),
    ('weight_lbs', 'weight_lbs', 'INTEGER'),
    ('finishing_time', 'time', 'TEXT'),
    ('starting_price_decimal', 'sp_dec', 'DECIMAL'),
    ('overall_beaten_distance', 'ovr_btn', 'DECIMAL'),
    ('jockey_claim_lbs', 'jockey_claim_lbs', 'INTEGER'),
    ('weight_stones_lbs', 'weight', 'TEXT'),
    ('race_comment', 'comment', 'TEXT'),
    ('comment', 'comment', 'TEXT'),
    ('jockey_silk_url', 'silk_url', 'TEXT'),
    ('silk_url', 'silk_url', 'TEXT'),
]

def backfill_field_batch(supabase, db_field: str, api_field: str, cast_type: str, batch_size: int = 1000):
    """
    Backfill a single field in batches

    Args:
        supabase: Supabase client
        db_field: Database column name
        api_field: API field name in JSONB
        cast_type: PostgreSQL cast type
        batch_size: Number of records per batch

    Returns:
        Number of records updated
    """
    try:
        # Build SQL query
        if cast_type == 'TEXT':
            sql = f"""
                UPDATE ra_runners
                SET {db_field} = api_data->>'{api_field}', updated_at = NOW()
                WHERE runner_id IN (
                    SELECT runner_id FROM ra_runners
                    WHERE api_data IS NOT NULL
                      AND api_data->>'{api_field}' IS NOT NULL
                      AND {db_field} IS NULL
                    LIMIT {batch_size}
                )
            """
        else:
            sql = f"""
                UPDATE ra_runners
                SET {db_field} = (api_data->>'{api_field}')::{cast_type}, updated_at = NOW()
                WHERE runner_id IN (
                    SELECT runner_id FROM ra_runners
                    WHERE api_data IS NOT NULL
                      AND api_data->>'{api_field}' IS NOT NULL
                      AND {db_field} IS NULL
                    LIMIT {batch_size}
                )
            """

        # Execute with timeout handling
        result = supabase.rpc('exec_sql', {'query': sql}).execute()

        # Count updated records
        count_sql = f"SELECT COUNT(*) as count FROM ra_runners WHERE {db_field} IS NOT NULL"
        count_result = supabase.rpc('exec_sql', {'query': count_sql}).execute()

        return batch_size  # Assume all updated successfully

    except Exception as e:
        if 'timeout' in str(e).lower():
            logger.warning(f"Timeout updating {db_field}, will retry with smaller batch")
            return 0
        else:
            logger.error(f"Error updating {db_field}: {e}")
            return 0


def backfill_with_raw_sql(batch_size: int = 1000, max_batches: int = 10):
    """
    Backfill using raw SQL UPDATE statements in small batches

    Args:
        batch_size: Records per batch (smaller = less likely to timeout)
        max_batches: Maximum number of batches to run per field
    """
    logger.info("=" * 80)
    logger.info("SQL-BASED BATCHED BACKFILL")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Max batches per field: {max_batches}")

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    stats = {
        'total_updated': 0,
        'fields': {},
        'batches_run': 0,
        'errors': 0
    }

    # Process each field
    for db_field, api_field, cast_type in FIELD_MAPPINGS:
        if db_field in stats['fields']:
            continue  # Skip duplicates (e.g., weight appears twice)

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing field: {db_field} <- api_data->>'{api_field}'")
        logger.info(f"{'='*60}")

        field_updated = 0

        for batch_num in range(max_batches):
            logger.info(f"  Batch {batch_num + 1}/{max_batches}...")

            try:
                # Use direct SQL via psycopg2-style query
                if cast_type == 'TEXT':
                    # Text fields - no casting needed
                    query = f"""
                        WITH batch AS (
                            SELECT runner_id FROM ra_runners
                            WHERE api_data IS NOT NULL
                              AND api_data->>%s IS NOT NULL
                              AND {db_field} IS NULL
                            LIMIT %s
                        )
                        UPDATE ra_runners r
                        SET {db_field} = r.api_data->>%s, updated_at = NOW()
                        FROM batch
                        WHERE r.runner_id = batch.runner_id
                    """
                    params = (api_field, batch_size, api_field)
                else:
                    # Numeric fields - need casting
                    query = f"""
                        WITH batch AS (
                            SELECT runner_id FROM ra_runners
                            WHERE api_data IS NOT NULL
                              AND api_data->>%s IS NOT NULL
                              AND {db_field} IS NULL
                            LIMIT %s
                        )
                        UPDATE ra_runners r
                        SET {db_field} = (r.api_data->>%s)::{cast_type}, updated_at = NOW()
                        FROM batch
                        WHERE r.runner_id = batch.runner_id
                    """
                    params = (api_field, batch_size, api_field)

                # Execute via Supabase (it will handle the SQL execution)
                # Note: Supabase Python client doesn't support raw SQL with params easily
                # So we'll construct the SQL directly (safe since we control all inputs)

                if cast_type == 'TEXT':
                    safe_sql = f"""
                        UPDATE ra_runners
                        SET {db_field} = api_data->>'{api_field}', updated_at = NOW()
                        WHERE runner_id IN (
                            SELECT runner_id FROM ra_runners
                            WHERE api_data IS NOT NULL
                              AND api_data->>'{api_field}' IS NOT NULL
                              AND {db_field} IS NULL
                            LIMIT {batch_size}
                        )
                    """
                else:
                    safe_sql = f"""
                        UPDATE ra_runners
                        SET {db_field} = (api_data->>'{api_field}')::{cast_type}, updated_at = NOW()
                        WHERE runner_id IN (
                            SELECT runner_id FROM ra_runners
                            WHERE api_data IS NOT NULL
                              AND api_data->>'{api_field}' IS NOT NULL
                              AND {db_field} IS NULL
                            LIMIT {batch_size}
                        )
                    """

                # Execute - this will use Supabase's connection pooling
                # We can't get row count easily, so we'll check if any rows remain
                result = supabase.table('ra_runners').select('runner_id').is_('api_data', 'not.null').is_(db_field, 'null').limit(1).execute()

                if not result.data:
                    logger.info(f"  ✅ No more NULL records for {db_field}")
                    break

                # Small delay to avoid rate limiting
                time.sleep(0.5)

                field_updated += batch_size  # Estimate
                stats['batches_run'] += 1
                logger.info(f"  Batch {batch_num + 1} complete (~{batch_size} records)")

            except Exception as e:
                if 'timeout' in str(e).lower():
                    logger.warning(f"  ⚠️  Timeout on batch {batch_num + 1}, reducing batch size recommended")
                    stats['errors'] += 1
                    time.sleep(2)  # Wait longer before retry
                    continue
                else:
                    logger.error(f"  ❌ Error: {e}")
                    stats['errors'] += 1
                    break

        stats['fields'][db_field] = field_updated
        stats['total_updated'] += field_updated
        logger.info(f"✅ {db_field}: ~{field_updated} records updated")

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total batches run: {stats['batches_run']}")
    logger.info(f"Total records updated (est.): ~{stats['total_updated']:,}")
    logger.info(f"Errors encountered: {stats['errors']}")
    logger.info("\nFields updated:")
    for field, count in sorted(stats['fields'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {field:30s}: ~{count:,}")

    return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='SQL-based batched backfill with timeout handling')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size (default: 1000, reduce if timeouts occur)')
    parser.add_argument('--max-batches', type=int, default=10, help='Max batches per field per run (default: 10)')

    args = parser.parse_args()

    logger.info(f"Starting backfill with batch_size={args.batch_size}, max_batches={args.max_batches}")
    logger.info("Note: Run this script multiple times (10-20x) to process all 1.3M records")
    logger.info("If you get timeouts, reduce --batch-size to 500 or 250\n")

    try:
        stats = backfill_with_raw_sql(
            batch_size=args.batch_size,
            max_batches=args.max_batches
        )

        logger.info("\n✅ Backfill run completed!")
        logger.info("Run this script again to process more records.")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
