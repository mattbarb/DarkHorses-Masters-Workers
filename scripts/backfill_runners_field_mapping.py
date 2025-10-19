"""
Backfill Script: Fix NULL Fields in ra_runners
Extracts correct data from api_data JSONB column to populate NULL fields
"""

import os
import sys
from datetime import datetime
from typing import Dict, List
import json

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.logger import get_logger
from utils.position_parser import parse_int_field, parse_decimal_field, parse_text_field, parse_rating
from config.config import get_config

logger = get_logger('backfill_runners_field_mapping')

# Import Supabase client directly
from supabase import create_client

def backfill_runners_from_api_data(batch_size: int = 1000, limit: int = None, dry_run: bool = False):
    """
    Backfill NULL fields in ra_runners by extracting data from api_data JSONB column

    Args:
        batch_size: Number of records to process per batch
        limit: Maximum number of records to process (None = all)
        dry_run: If True, show what would be updated without actually updating
    """
    logger.info("=" * 80)
    logger.info("BACKFILL RUNNERS FIELD MAPPING")
    logger.info("=" * 80)
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Limit: {limit if limit else 'None (all records)'}")
    logger.info(f"Dry run: {dry_run}")

    config = get_config()
    supabase = create_client(config.supabase.url, config.supabase.service_key)

    # Set processing limit (avoid expensive count query)
    if limit:
        total_count = limit
        logger.info(f"Processing limit: {total_count:,} records")
    else:
        total_count = 2000000  # Upper bound estimate (more than current 1.3M)
        logger.info(f"Processing all records (estimated max: {total_count:,})")

    # Statistics
    stats = {
        'total_processed': 0,
        'total_updated': 0,
        'total_skipped': 0,
        'fields_updated': {
            'weight': 0,
            'form': 0,
            'form_string': 0,
            'prize_money_won': 0,
            'comment': 0,
            'silk_url': 0,
            'finishing_time': 0,
            'starting_price_decimal': 0,
            'overall_beaten_distance': 0,
            'jockey_claim_lbs': 0,
            'weight_stones_lbs': 0,
            'race_comment': 0,
            'jockey_silk_url': 0,
        },
        'errors': []
    }

    # Process in batches
    offset = 0
    while offset < total_count:
        current_batch_size = min(batch_size, total_count - offset)
        logger.info(f"\nProcessing batch {offset//batch_size + 1}: records {offset:,} to {offset + current_batch_size:,}")

        # Fetch batch
        result = supabase.table('ra_runners').select('runner_id,api_data').not_.is_('api_data', 'null').range(offset, offset + current_batch_size - 1).execute()

        runners = result.data
        logger.info(f"Fetched {len(runners)} runners")

        if not runners or len(runners) == 0:
            logger.info("No more records to process")
            break

        # Process each runner
        updates = []
        for runner in runners:
            runner_id = runner['runner_id']
            api_data = runner.get('api_data', {})

            if not api_data:
                stats['total_skipped'] += 1
                continue

            # Extract fields from api_data
            update_fields = {}

            # Weight (API: weight_lbs)
            if api_data.get('weight_lbs'):
                update_fields['weight'] = parse_int_field(api_data.get('weight_lbs'))
                update_fields['weight_lbs'] = parse_int_field(api_data.get('weight_lbs'))
                stats['fields_updated']['weight'] += 1

            # Form (API: form_string)
            if api_data.get('form_string'):
                update_fields['form'] = api_data.get('form_string')
                update_fields['form_string'] = api_data.get('form_string')
                stats['fields_updated']['form'] += 1
                stats['fields_updated']['form_string'] += 1

            # Prize money (API: prize) - clean currency symbols
            if api_data.get('prize'):
                prize_str = str(api_data.get('prize'))
                # Remove currency symbols (£, €, $) and commas
                cleaned_prize = prize_str.replace('£', '').replace('€', '').replace('$', '').replace(',', '').strip()
                if cleaned_prize:
                    try:
                        update_fields['prize_money_won'] = float(cleaned_prize)
                        stats['fields_updated']['prize_money_won'] += 1
                    except ValueError:
                        pass  # Skip if can't parse

            # Comment (API: comment)
            if api_data.get('comment'):
                update_fields['comment'] = api_data.get('comment')
                stats['fields_updated']['comment'] += 1

            # Silk URL (API: silk_url)
            if api_data.get('silk_url'):
                update_fields['silk_url'] = api_data.get('silk_url')
                stats['fields_updated']['silk_url'] += 1

            # Migration 011 fields

            # Finishing time (API: time)
            if api_data.get('time'):
                update_fields['finishing_time'] = parse_text_field(api_data.get('time'))
                stats['fields_updated']['finishing_time'] += 1

            # Starting price decimal (API: sp_dec)
            if api_data.get('sp_dec'):
                update_fields['starting_price_decimal'] = parse_decimal_field(api_data.get('sp_dec'))
                stats['fields_updated']['starting_price_decimal'] += 1

            # Overall beaten distance (API: ovr_btn)
            if api_data.get('ovr_btn') is not None:  # Can be 0
                update_fields['overall_beaten_distance'] = parse_decimal_field(api_data.get('ovr_btn'))
                stats['fields_updated']['overall_beaten_distance'] += 1

            # Jockey claim lbs (API: jockey_claim_lbs)
            if api_data.get('jockey_claim_lbs') is not None:  # Can be 0
                update_fields['jockey_claim_lbs'] = parse_int_field(api_data.get('jockey_claim_lbs'))
                stats['fields_updated']['jockey_claim_lbs'] += 1

            # Weight stones-lbs (API: weight)
            if api_data.get('weight'):
                update_fields['weight_stones_lbs'] = parse_text_field(api_data.get('weight'))
                stats['fields_updated']['weight_stones_lbs'] += 1

            # Race comment (API: comment - same as comment field)
            if api_data.get('comment'):
                update_fields['race_comment'] = parse_text_field(api_data.get('comment'))
                stats['fields_updated']['race_comment'] += 1

            # Jockey silk URL (API: silk_url - same as silk_url field)
            if api_data.get('silk_url'):
                update_fields['jockey_silk_url'] = parse_text_field(api_data.get('silk_url'))
                stats['fields_updated']['jockey_silk_url'] += 1

            # Add updated_at timestamp
            update_fields['updated_at'] = datetime.utcnow().isoformat()

            if update_fields:
                updates.append({
                    'runner_id': runner_id,
                    'updates': update_fields
                })
                stats['total_updated'] += 1
            else:
                stats['total_skipped'] += 1

            stats['total_processed'] += 1

        # Perform batch update
        if updates and not dry_run:
            logger.info(f"Updating {len(updates)} runners...")
            for update in updates:
                try:
                    supabase.table('ra_runners').update(update['updates']).eq('runner_id', update['runner_id']).execute()
                except Exception as e:
                    logger.error(f"Error updating runner {update['runner_id']}: {e}")
                    stats['errors'].append({'runner_id': update['runner_id'], 'error': str(e)})
        elif dry_run:
            logger.info(f"DRY RUN: Would update {len(updates)} runners")
            if updates:
                logger.info(f"Sample update: {updates[0]}")

        # Progress report
        logger.info(f"Batch complete. Processed: {stats['total_processed']:,}, Updated: {stats['total_updated']:,}, Skipped: {stats['total_skipped']:,}")

        offset += current_batch_size

    # Final report
    logger.info("\n" + "=" * 80)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total processed: {stats['total_processed']:,}")
    logger.info(f"Total updated: {stats['total_updated']:,}")
    logger.info(f"Total skipped: {stats['total_skipped']:,}")
    logger.info(f"Total errors: {len(stats['errors'])}")
    logger.info("\nFields updated:")
    for field, count in sorted(stats['fields_updated'].items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {field:30s}: {count:,}")

    if stats['errors']:
        logger.warning(f"\nEncountered {len(stats['errors'])} errors. See log for details.")
        logger.warning(f"Sample errors: {stats['errors'][:5]}")

    # Save stats to file
    stats_file = f"logs/backfill_runners_field_mapping_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
    os.makedirs('logs', exist_ok=True)
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"\nStatistics saved to: {stats_file}")

    return stats


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Backfill NULL fields in ra_runners from api_data')
    parser.add_argument('--batch-size', type=int, default=1000, help='Batch size (default: 1000)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of records to process (default: None/all)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no actual updates)')
    parser.add_argument('--test', action='store_true', help='Test mode (limit to 100 records)')

    args = parser.parse_args()

    if args.test:
        logger.info("TEST MODE: Processing only 100 records")
        args.limit = 100

    try:
        stats = backfill_runners_from_api_data(
            batch_size=args.batch_size,
            limit=args.limit,
            dry_run=args.dry_run
        )

        logger.info("\n✅ Backfill completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  Backfill interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"\n\n❌ Backfill failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit(main())
