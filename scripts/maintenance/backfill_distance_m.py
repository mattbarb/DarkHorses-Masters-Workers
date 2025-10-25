#!/usr/bin/env python3
"""
Backfill distance_m field for races that are missing it.
Uses the parse_distance_meters() function to calculate from distance_f field.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('backfill_distance_m')


def parse_distance_meters(dist_str):
    """Convert distance string like '1m', '6f', '2m4f', '7.5f' to meters (approximate)"""
    if not dist_str or not isinstance(dist_str, str):
        return None
    try:
        # Try direct numeric conversion first (handles integers and floats)
        return int(float(dist_str))
    except (ValueError, TypeError):
        # Parse string like "1m", "6f", "2m4f", "7.5f" etc.
        # Note: This is approximate. 1 furlong ≈ 201 meters, 1 mile ≈ 1609 meters
        dist_str = dist_str.lower().strip()
        meters = 0.0

        # Extract miles (handles decimals like "1.5m")
        if 'm' in dist_str:
            parts = dist_str.split('m')
            if parts[0]:
                try:
                    miles = float(parts[0])
                    meters += miles * 1609  # 1 mile ≈ 1609 meters
                    dist_str = parts[1] if len(parts) > 1 else ''
                except ValueError:
                    pass

        # Extract furlongs (handles decimals like "7.5f")
        if 'f' in dist_str:
            parts = dist_str.split('f')
            if parts[0]:
                try:
                    furlongs = float(parts[0])
                    meters += furlongs * 201  # 1 furlong ≈ 201 meters
                except ValueError:
                    pass

        return int(meters) if meters > 0 else None


def backfill_distance_m():
    """Backfill missing distance_m values for all races"""
    logger.info("Starting distance_m backfill")

    config = get_config()
    db = SupabaseReferenceClient(config.supabase.url, config.supabase.service_key)

    # Get all races missing distance_m (query in batches to avoid memory issues)
    logger.info("Counting races with missing distance_m...")
    count_result = db.client.from_('ra_races').select('id', count='exact').is_('distance_m', 'null').execute()
    total = count_result.count

    logger.info(f"Total races needing backfill: {total:,}")

    # Process in chunks from database
    fetch_size = 5000  # Fetch 5000 at a time from DB
    races_to_update = []

    logger.info(f"Fetching races to update ({fetch_size} at a time)...")
    for offset in range(0, total, fetch_size):
        result = db.client.from_('ra_races').select('id, distance_f').is_('distance_m', 'null').limit(fetch_size).offset(offset).execute()
        races_to_update.extend(result.data)
        logger.info(f"  Fetched {len(races_to_update):,}/{total:,} races")

    total = len(races_to_update)

    if total == 0:
        logger.info("No races need distance_m backfill")
        return

    logger.info(f"Found {total:,} races missing distance_m")

    # Process in batches
    batch_size = 500
    updated = 0
    failed = 0

    for i in range(0, total, batch_size):
        batch = races_to_update[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        total_batches = (total + batch_size - 1) // batch_size

        logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} races)")

        # Calculate distance_m for each race in batch
        updates = []
        for race in batch:
            distance_m = parse_distance_meters(race['distance_f'])
            if distance_m:
                updates.append({
                    'id': race['id'],
                    'distance_m': distance_m
                })

        # Update database - update each race individually
        if updates:
            try:
                for update in updates:
                    db.client.from_('ra_races').update({'distance_m': update['distance_m']}).eq('id', update['id']).execute()
                updated += len(updates)
                logger.info(f"  ✓ Updated {len(updates)} races")
            except Exception as e:
                logger.error(f"  ✗ Failed to update batch: {e}")
                failed += len(batch)
        else:
            logger.warning(f"  ⚠ No valid distance_m values calculated for batch")
            failed += len(batch)

    logger.info("=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info(f"Total races processed: {total:,}")
    logger.info(f"Successfully updated: {updated:,}")
    logger.info(f"Failed: {failed:,}")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        backfill_distance_m()
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        sys.exit(1)
