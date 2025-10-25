#!/usr/bin/env python3
"""
Backfill missing metadata fields in dh_weather_history table

This script fixes NULL values in the following columns:
- update_phase
- total_updates
- update_display

The issue started on 2025-10-15 (ID 925922) and affects approximately 5,601 records.

Root cause: Weather fetcher logic was updated but didn't populate these tracking fields.

Solution: Calculate proper values based on existing data (hours_before_race, race_datetime, etc.)
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timezone
import logging
import time

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv('.env.local')
if not os.getenv('SUPABASE_URL'):
    load_dotenv('../.env.local')

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_SERVICE_KEY')

if not url or not key:
    logger.error('Missing SUPABASE_URL or SUPABASE_SERVICE_KEY')
    sys.exit(1)

# Create client
from supabase.lib.client_options import ClientOptions
options = ClientOptions()
client = create_client(url, key, options)


def determine_update_phase(hours_before_race, race_datetime_str, fetch_datetime_str):
    """
    Determine the update phase based on hours before race

    Args:
        hours_before_race: Hours before race start (negative if after)
        race_datetime_str: Race datetime as ISO string
        fetch_datetime_str: Fetch datetime as ISO string

    Returns:
        str: Update phase ('pre_race', 'race_day', or 'post_race')
    """
    if hours_before_race is None:
        # Calculate from datetimes
        try:
            race_dt = datetime.fromisoformat(race_datetime_str.replace('Z', '+00:00'))
            fetch_dt = datetime.fromisoformat(fetch_datetime_str.replace('Z', '+00:00'))
            hours_diff = (race_dt - fetch_dt).total_seconds() / 3600
        except:
            # Default to post_race if we can't calculate
            return 'post_race'
    else:
        hours_diff = hours_before_race

    # Determine phase
    if hours_diff < 0:
        return 'post_race'
    elif hours_diff < 24:
        return 'race_day'
    else:
        return 'pre_race'


def calculate_total_updates(update_number, update_phase):
    """
    Calculate expected total updates based on phase

    Typical pattern:
    - Pre-race: Multiple updates (24-48 updates over multiple days)
    - Race day: Final updates (48 updates leading up to race)
    - Post-race: Archive updates (48 updates for historical data)

    Args:
        update_number: Current update number
        update_phase: Phase of updates

    Returns:
        int: Expected total updates
    """
    if update_phase == 'post_race':
        # Post-race archive typically has 48 updates
        return 48
    elif update_phase == 'race_day':
        # Race day typically has 48 updates
        return max(48, update_number)
    else:
        # Pre-race can vary, use update_number as guide
        return max(48, update_number)


def backfill_records(batch_size=100, dry_run=False):
    """
    Backfill NULL metadata fields in dh_weather_history

    Args:
        batch_size: Number of records to process per batch
        dry_run: If True, don't actually update the database
    """
    logger.info("Starting weather metadata backfill...")

    # Stats
    total_processed = 0
    total_updated = 0
    total_errors = 0

    # Find range of affected records
    logger.info("Finding affected records...")
    result = client.table('dh_weather_history').select('id').is_('update_phase', 'null').order('id', desc=False).limit(1).execute()

    if not result.data:
        logger.info("No records with NULL update_phase found!")
        return

    first_null_id = result.data[0]['id']

    result_max = client.table('dh_weather_history').select('id').order('id', desc=True).limit(1).execute()
    max_id = result_max.data[0]['id']

    estimated_count = max_id - first_null_id + 1
    logger.info(f"Estimated affected records: {estimated_count} (IDs {first_null_id} to {max_id})")

    # Process in batches
    current_id = first_null_id

    while current_id <= max_id:
        # Fetch batch
        logger.info(f"Processing batch starting at ID {current_id}...")

        result = client.table('dh_weather_history').select(
            'id, race_id, race_datetime, fetch_datetime, hours_before_race, update_number, update_phase, total_updates, api_source'
        ).gte('id', current_id).is_('update_phase', 'null').order('id', desc=False).limit(batch_size).execute()

        if not result.data:
            logger.info("No more NULL records found in this range")
            break

        records = result.data
        logger.info(f"  Found {len(records)} records to update")

        # Process each record
        for record in records:
            try:
                record_id = record['id']
                hours_before = record.get('hours_before_race')
                race_datetime = record.get('race_datetime')
                fetch_datetime = record.get('fetch_datetime')
                update_number = record.get('update_number', 1)
                api_source = record.get('api_source', 'archive')

                # Determine update phase
                update_phase = determine_update_phase(hours_before, race_datetime, fetch_datetime)

                # Calculate total updates
                total_updates = calculate_total_updates(update_number, update_phase)

                # Create update display
                update_display = f"{update_number}/{total_updates}"

                # Prepare update
                update_data = {
                    'update_phase': update_phase,
                    'total_updates': total_updates,
                    'update_display': update_display,
                    'updated_at': datetime.now(timezone.utc).isoformat()
                }

                if dry_run:
                    logger.info(f"  [DRY RUN] Would update ID {record_id}: {update_data}")
                else:
                    # Update record
                    client.table('dh_weather_history').update(update_data).eq('id', record_id).execute()
                    total_updated += 1

                total_processed += 1

                if total_processed % 100 == 0:
                    logger.info(f"  Progress: {total_processed} processed, {total_updated} updated")

            except Exception as e:
                logger.error(f"  Error processing record ID {record.get('id')}: {e}")
                total_errors += 1

        # Move to next batch
        if records:
            current_id = records[-1]['id'] + 1
        else:
            break

        # Small delay to avoid overwhelming the database
        time.sleep(0.1)

    # Summary
    logger.info("\n=== BACKFILL COMPLETE ===")
    logger.info(f"Total processed: {total_processed}")
    logger.info(f"Total updated: {total_updated}")
    logger.info(f"Total errors: {total_errors}")

    return {
        'processed': total_processed,
        'updated': total_updated,
        'errors': total_errors
    }


def verify_backfill():
    """
    Verify the backfill by checking for remaining NULL records
    """
    logger.info("\n=== VERIFYING BACKFILL ===")

    # Check for remaining NULLs
    result = client.table('dh_weather_history').select('id', count='exact').is_('update_phase', 'null').limit(1).execute()

    null_count = result.count if hasattr(result, 'count') else 0

    if null_count == 0:
        logger.info("✓ SUCCESS: No NULL update_phase records found!")
    else:
        logger.warning(f"⚠ WARNING: Still {null_count} NULL update_phase records")

    # Sample recent records to verify
    result = client.table('dh_weather_history').select(
        'id, update_phase, total_updates, update_display'
    ).order('id', desc=True).limit(5).execute()

    logger.info("\nSample of most recent records:")
    for record in result.data:
        logger.info(f"  ID {record['id']}: phase={record['update_phase']}, "
                   f"total={record['total_updates']}, display={record['update_display']}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Backfill weather metadata fields')
    parser.add_argument('--dry-run', action='store_true', help='Run without updating database')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing')
    parser.add_argument('--verify-only', action='store_true', help='Only verify, don\'t backfill')

    args = parser.parse_args()

    if args.verify_only:
        verify_backfill()
    else:
        if args.dry_run:
            logger.info("=== DRY RUN MODE - No changes will be made ===\n")

        result = backfill_records(batch_size=args.batch_size, dry_run=args.dry_run)

        if not args.dry_run:
            verify_backfill()
