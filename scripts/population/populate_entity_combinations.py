#!/usr/bin/env python3
"""
Populate ra_entity_combinations Table

Analyzes ra_mst_runners to identify frequent jockey/trainer/owner/horse combinations
and calculates their performance statistics.

Phase 1 - Quick Win (Database analysis only, no external API calls)

Usage:
    python3 scripts/populate_entity_combinations.py [--min-races N]

Options:
    --min-races N    Minimum number of races for a combination (default: 2)
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_entity_combinations')


def analyze_combinations(db_client: SupabaseReferenceClient, min_races: int = 2) -> Dict:
    """
    Analyze runner data to find entity combinations

    Args:
        db_client: Database client
        min_races: Minimum number of races for a combination to be included

    Returns:
        Dict with combination statistics
    """
    logger.info("Fetching runners data for combination analysis...")

    # Fetch all runners with position data
    response = db_client.client.table('ra_mst_runners')\
        .select('jockey_id, trainer_id, owner_id, horse_id, position, race_id')\
        .not_.is_('jockey_id', 'null')\
        .not_.is_('trainer_id', 'null')\
        .not_.is_('owner_id', 'null')\
        .not_.is_('horse_id', 'null')\
        .execute()

    if not response.data:
        logger.error("No runner data found")
        return {}

    logger.info(f"Analyzing {len(response.data)} runner records...")

    # Track combinations
    combinations = defaultdict(lambda: {
        'races': [],
        'wins': 0,
        'places': 0,  # Top 3 finishes
        'last_seen': None
    })

    for runner in response.data:
        jockey_id = runner['jockey_id']
        trainer_id = runner['trainer_id']
        owner_id = runner['owner_id']
        horse_id = runner['horse_id']
        position = runner.get('position')
        race_id = runner['race_id']

        # Create combination key
        combo_key = f"{jockey_id}|{trainer_id}|{owner_id}|{horse_id}"

        # Track race
        combinations[combo_key]['races'].append(race_id)

        # Track performance
        if position:
            try:
                pos_int = int(position)
                if pos_int == 1:
                    combinations[combo_key]['wins'] += 1
                if pos_int <= 3:
                    combinations[combo_key]['places'] += 1
            except ValueError:
                pass  # Skip non-numeric positions

        # Update last seen
        combinations[combo_key]['jockey_id'] = jockey_id
        combinations[combo_key]['trainer_id'] = trainer_id
        combinations[combo_key]['owner_id'] = owner_id
        combinations[combo_key]['horse_id'] = horse_id

    # Filter combinations by minimum races
    filtered_combinations = {
        key: data for key, data in combinations.items()
        if len(data['races']) >= min_races
    }

    logger.info(f"Found {len(combinations)} total combinations")
    logger.info(f"Filtered to {len(filtered_combinations)} combinations with {min_races}+ races")

    return filtered_combinations


def create_combination_records(combinations: Dict) -> List[Dict]:
    """
    Convert combination analysis to database records

    Args:
        combinations: Dictionary of combinations with statistics

    Returns:
        List of records ready for database insertion
    """
    records = []

    for combo_key, data in combinations.items():
        race_count = len(data['races'])
        win_count = data['wins']
        place_count = data['places']

        # Calculate rates
        win_rate = (win_count / race_count * 100) if race_count > 0 else 0.0
        place_rate = (place_count / race_count * 100) if race_count > 0 else 0.0

        record = {
            'id': combo_key,  # Use composite key as ID
            'jockey_id': data['jockey_id'],
            'trainer_id': data['trainer_id'],
            'owner_id': data['owner_id'],
            'horse_id': data['horse_id'],
            'combination_count': race_count,
            'wins': win_count,
            'places': place_count,
            'win_rate': round(win_rate, 2),
            'place_rate': round(place_rate, 2),
            'first_seen': None,  # Would need date analysis
            'last_seen': None,   # Would need date analysis
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }

        records.append(record)

    # Sort by combination count (most frequent first)
    records.sort(key=lambda x: x['combination_count'], reverse=True)

    return records


def populate_entity_combinations(min_races: int = 2) -> Dict:
    """
    Populate entity combinations table

    Args:
        min_races: Minimum number of races for inclusion

    Returns:
        Dict with operation statistics
    """
    config = get_config()

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    logger.info("=" * 80)
    logger.info("POPULATING ra_entity_combinations TABLE")
    logger.info("=" * 80)
    logger.info(f"Minimum races per combination: {min_races}")

    try:
        # Step 1: Analyze combinations
        logger.info("\nStep 1: Analyzing entity combinations...")
        combinations = analyze_combinations(db_client, min_races)

        if not combinations:
            logger.error("No combinations found")
            return {'success': False, 'error': 'No combinations found'}

        # Step 2: Create records
        logger.info("\nStep 2: Creating combination records...")
        records = create_combination_records(combinations)

        logger.info(f"Created {len(records)} combination records")

        # Show top 10
        logger.info("\nTop 10 combinations by frequency:")
        for i, record in enumerate(records[:10], 1):
            logger.info(
                f"  {i}. Jockey {record['jockey_id']}, "
                f"Trainer {record['trainer_id']}, "
                f"Horse {record['horse_id']}: "
                f"{record['combination_count']} races, "
                f"{record['win_rate']:.1f}% win rate"
            )

        # Step 3: Upsert to database
        logger.info("\nStep 3: Upserting combinations to database...")

        stats = db_client.upsert_batch(
            table='ra_entity_combinations',
            records=records,
            unique_key='id'
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Updated: {stats.get('updated', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Step 4: Verify results
        logger.info("\nStep 4: Verifying results...")

        verify_response = db_client.client.table('ra_entity_combinations')\
            .select('*', count='exact')\
            .execute()

        logger.info(f"Total combinations in database: {verify_response.count}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ ENTITY COMBINATIONS TABLE POPULATION COMPLETE")
        logger.info("=" * 80)

        return {
            'success': True,
            'combinations_analyzed': len(combinations),
            'records_created': len(records),
            'database_stats': stats,
            'total_in_db': verify_response.count
        }

    except Exception as e:
        logger.error(f"Failed to populate entity combinations: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate entity combinations table'
    )
    parser.add_argument(
        '--min-races',
        type=int,
        default=2,
        help='Minimum number of races for a combination (default: 2)'
    )

    args = parser.parse_args()

    logger.info("Starting entity combinations analysis...")

    result = populate_entity_combinations(min_races=args.min_races)

    if result['success']:
        logger.info("\n✅ SUCCESS")
        logger.info(f"Combinations analyzed: {result['combinations_analyzed']}")
        logger.info(f"Records created: {result['records_created']}")
        logger.info(f"Total in database: {result['total_in_db']}")
    else:
        logger.error(f"\n❌ FAILED: {result.get('error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
