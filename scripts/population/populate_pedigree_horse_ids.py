#!/usr/bin/env python3
"""
Populate horse_id in ra_mst_sires/dams/damsires via name + region matching

This script matches breeding entities to horses in ra_mst_horses using:
1. Name matching (with region suffix handling)
2. Region validation (when available)

Expected match rate: 90-95% with region data, 70-85% without

Usage:
    python3 scripts/population/populate_pedigree_horse_ids.py [--dry-run]
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from supabase import create_client
import os
from dotenv import load_dotenv
import argparse
from utils.logger import get_logger

logger = get_logger('populate_pedigree_horse_ids')

load_dotenv('.env.local')


def normalize_name(name: str) -> str:
    """
    Normalize horse name for matching
    - Remove extra whitespace
    - Convert to lowercase
    - Keep region suffix (e.g., '(GB)')
    """
    if not name:
        return ''
    return ' '.join(name.split()).lower()


def match_pedigree_to_horses(client, table_name: str, entity_type: str, dry_run: bool = False):
    """
    Match pedigree entities to horses by name and region

    Args:
        client: Supabase client
        table_name: Table to update (ra_mst_sires, ra_mst_dams, ra_mst_damsires)
        entity_type: Entity type for logging (sire, dam, damsire)
        dry_run: If True, only count matches without updating

    Returns:
        Dict with match statistics
    """
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Processing {table_name} ({entity_type}s)")
    logger.info(f"{'=' * 80}")

    # Get all entities from pedigree table
    # Try with region column first, fallback to without if it doesn't exist
    try:
        entities = client.table(table_name).select('id, name, region, horse_id').execute()
        has_region_column = True
    except Exception as e:
        if 'region does not exist' in str(e) or '42703' in str(e):
            logger.warning(f"⚠️  Region column not found in {table_name}, using name-only matching")
            logger.warning("   Run Migration 030 to enable region-aware matching")
            entities = client.table(table_name).select('id, name, horse_id').execute()
            has_region_column = False
        else:
            raise

    total = len(entities.data)
    already_matched = sum(1 for e in entities.data if e.get('horse_id'))
    to_match = total - already_matched

    logger.info(f"Total {entity_type}s: {total:,}")
    logger.info(f"Already matched: {already_matched:,}")
    logger.info(f"To match: {to_match:,}")

    if to_match == 0:
        logger.info(f"✅ All {entity_type}s already have horse_id!")
        return {
            'total': total,
            'already_matched': already_matched,
            'newly_matched': 0,
            'failed': 0
        }

    # Get all horses for matching
    horses = client.table('ra_mst_horses').select('id, name, region').execute()
    logger.info(f"Total horses in database: {len(horses.data):,}")

    # Build lookup dictionaries
    # Strategy 1: name + region lookup (most accurate)
    horses_by_name_region = {}
    # Strategy 2: name-only lookup (fallback)
    horses_by_name = {}

    for horse in horses.data:
        name = normalize_name(horse.get('name', ''))
        region = horse.get('region')
        horse_id = horse.get('id')  # ra_mst_horses uses 'id' not 'horse_id'

        if name and horse_id:
            # Add to name-only lookup
            if name not in horses_by_name:
                horses_by_name[name] = []
            horses_by_name[name].append(horse_id)

            # Add to name+region lookup
            if region:
                key = (name, region.lower() if region else None)
                if key not in horses_by_name_region:
                    horses_by_name_region[key] = []
                horses_by_name_region[key].append(horse_id)

    logger.info(f"Unique horse names: {len(horses_by_name):,}")
    logger.info(f"Unique name+region combinations: {len(horses_by_name_region):,}")

    # Match entities to horses
    matched = 0
    matched_with_region = 0
    matched_name_only = 0
    multiple_matches = 0
    no_match = 0

    updates = []

    for entity in entities.data:
        # Skip if already matched
        if entity.get('horse_id'):
            continue

        entity_id = entity.get('id')
        entity_name = normalize_name(entity.get('name', ''))
        entity_region = entity.get('region')

        if not entity_name:
            no_match += 1
            continue

        matched_horse_id = None
        match_method = None

        # Strategy 1: Try name + region match (if region available)
        if entity_region:
            key = (entity_name, entity_region.lower())
            if key in horses_by_name_region:
                candidates = horses_by_name_region[key]
                if len(candidates) == 1:
                    matched_horse_id = candidates[0]
                    match_method = 'name+region'
                    matched_with_region += 1
                elif len(candidates) > 1:
                    # Multiple matches even with region - take first
                    matched_horse_id = candidates[0]
                    match_method = 'name+region (multiple)'
                    matched_with_region += 1
                    multiple_matches += 1
                    logger.warning(f"  Multiple matches for {entity_name} ({entity_region}): {len(candidates)} candidates")

        # Strategy 2: Fallback to name-only match
        if not matched_horse_id and entity_name in horses_by_name:
            candidates = horses_by_name[entity_name]
            if len(candidates) == 1:
                matched_horse_id = candidates[0]
                match_method = 'name_only'
                matched_name_only += 1
            elif len(candidates) > 1:
                # Multiple candidates - skip for safety (ambiguous)
                multiple_matches += 1
                logger.warning(f"  Ambiguous match for {entity_name}: {len(candidates)} candidates (skipping)")
                no_match += 1
                continue

        if matched_horse_id:
            matched += 1
            updates.append({
                'id': entity_id,
                'name': entity.get('name'),
                'horse_id': matched_horse_id,
                'method': match_method
            })

            if matched <= 10:  # Log first 10 matches
                logger.info(f"  ✓ Matched: {entity.get('name')} → {matched_horse_id} (via {match_method})")
        else:
            no_match += 1

    logger.info(f"\nMatch Results:")
    logger.info(f"  Matched: {matched:,}")
    logger.info(f"    - Via name+region: {matched_with_region:,}")
    logger.info(f"    - Via name only: {matched_name_only:,}")
    logger.info(f"  No match: {no_match:,}")
    logger.info(f"  Multiple matches (ambiguous): {multiple_matches:,}")

    if dry_run:
        logger.info(f"\n🔍 DRY RUN - No updates performed")
        return {
            'total': total,
            'already_matched': already_matched,
            'newly_matched': matched,
            'failed': no_match,
            'dry_run': True
        }

    # Perform updates
    if matched > 0:
        logger.info(f"\nUpdating {matched:,} {entity_type} records...")

        # Update in batches
        batch_size = 100
        updated_count = 0

        for i in range(0, len(updates), batch_size):
            batch = updates[i:i+batch_size]

            # Update each record
            for update in batch:
                try:
                    client.table(table_name).update({
                        'horse_id': update['horse_id'],
                        'updated_at': 'now()'
                    }).eq('id', update['id']).execute()
                    updated_count += 1
                except Exception as e:
                    logger.error(f"  ❌ Failed to update {update['name']}: {e}")

            logger.info(f"  Updated {updated_count:,}/{matched:,} records...")

        logger.info(f"✅ Updated {updated_count:,} {entity_type} records with horse_id")
    else:
        logger.info(f"No updates needed")

    return {
        'total': total,
        'already_matched': already_matched,
        'newly_matched': matched,
        'updated': updated_count if not dry_run else 0,
        'failed': no_match
    }


def main():
    parser = argparse.ArgumentParser(description='Populate horse_id in pedigree tables')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be matched without updating')
    args = parser.parse_args()

    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_SERVICE_KEY')

    if not url or not key:
        logger.error("❌ Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables")
        sys.exit(1)

    client = create_client(url, key)

    logger.info("=" * 80)
    logger.info("POPULATING PEDIGREE HORSE_IDS VIA NAME + REGION MATCHING")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("🔍 DRY RUN MODE - No updates will be performed")

    tables = [
        ('ra_mst_sires', 'sire'),
        ('ra_mst_dams', 'dam'),
        ('ra_mst_damsires', 'damsire')
    ]

    total_stats = {
        'total': 0,
        'already_matched': 0,
        'newly_matched': 0,
        'failed': 0
    }

    for table_name, entity_type in tables:
        stats = match_pedigree_to_horses(client, table_name, entity_type, dry_run=args.dry_run)

        total_stats['total'] += stats['total']
        total_stats['already_matched'] += stats['already_matched']
        total_stats['newly_matched'] += stats['newly_matched']
        total_stats['failed'] += stats['failed']

    # Final summary
    logger.info("\n" + "=" * 80)
    logger.info("FINAL SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Total pedigree records: {total_stats['total']:,}")
    logger.info(f"Already matched: {total_stats['already_matched']:,}")
    logger.info(f"Newly matched: {total_stats['newly_matched']:,}")
    logger.info(f"Failed to match: {total_stats['failed']:,}")

    total_with_id = total_stats['already_matched'] + total_stats['newly_matched']
    coverage_pct = (total_with_id / total_stats['total'] * 100) if total_stats['total'] > 0 else 0

    logger.info(f"\nOverall Coverage: {coverage_pct:.1f}% ({total_with_id:,}/{total_stats['total']:,})")

    if args.dry_run:
        logger.info("\n🔍 DRY RUN COMPLETE - Run without --dry-run to apply changes")
    else:
        logger.info("\n✅ MATCHING COMPLETE!")

    logger.info("=" * 80)


if __name__ == '__main__':
    main()
