#!/usr/bin/env python3
"""
Populate ra_entity_combinations Table (Version 2)

Analyzes ra_mst_runners to identify frequent entity pair combinations
(jockey-horse, trainer-horse, owner-horse, jockey-trainer, etc.)
and calculates their performance statistics.

Matches actual database schema with entity1/entity2 pairs.

Phase 1 - Quick Win (Database analysis only, no external API calls)

Usage:
    python3 scripts/populate_entity_combinations_v2.py [--min-runs N] [--pair-type TYPE]

Options:
    --min-runs N       Minimum number of runs for a combination (default: 5)
    --pair-type TYPE   Combination type: jockey_horse, trainer_horse, owner_horse,
                       jockey_trainer, or all (default: all)
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from collections import defaultdict
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_entity_combinations_v2')


def analyze_entity_pairs(
    db_client: SupabaseReferenceClient,
    pair_type: str,
    min_runs: int = 5
) -> Dict:
    """
    Analyze runner data to find entity pair combinations

    Args:
        db_client: Database client
        pair_type: Type of pair (jockey_horse, trainer_horse, etc.)
        min_runs: Minimum number of runs for a combination to be included

    Returns:
        Dict with combination statistics
    """
    logger.info(f"Analyzing {pair_type} combinations...")
    logger.info("Fetching runners data...")

    # Fetch all runners with position data
    response = db_client.client.table('ra_mst_runners')\
        .select('jockey_id, trainer_id, owner_id, horse_id, position, race_id')\
        .not_.is_('position', 'null')\
        .execute()

    if not response.data:
        logger.error("No runner data found")
        return {}

    logger.info(f"Analyzing {len(response.data)} runner records...")

    # Determine entity types based on pair_type
    if pair_type == 'jockey_horse':
        entity1_key, entity2_key = 'jockey_id', 'horse_id'
        entity1_type, entity2_type = 'jockey', 'horse'
    elif pair_type == 'trainer_horse':
        entity1_key, entity2_key = 'trainer_id', 'horse_id'
        entity1_type, entity2_type = 'trainer', 'horse'
    elif pair_type == 'owner_horse':
        entity1_key, entity2_key = 'owner_id', 'horse_id'
        entity1_type, entity2_type = 'owner', 'horse'
    elif pair_type == 'jockey_trainer':
        entity1_key, entity2_key = 'jockey_id', 'trainer_id'
        entity1_type, entity2_type = 'jockey', 'trainer'
    else:
        raise ValueError(f"Unknown pair type: {pair_type}")

    # Track combinations
    combinations = defaultdict(lambda: {
        'total_runs': 0,
        'wins': 0,
        'places_2nd': 0,
        'places_3rd': 0
    })

    for runner in response.data:
        entity1_id = runner.get(entity1_key)
        entity2_id = runner.get(entity2_key)
        position = runner.get('position')

        if not entity1_id or not entity2_id:
            continue

        # Create combination key
        combo_key = f"{entity1_id}|{entity2_id}"

        # Track run
        combinations[combo_key]['total_runs'] += 1
        combinations[combo_key]['entity1_id'] = entity1_id
        combinations[combo_key]['entity2_id'] = entity2_id
        combinations[combo_key]['entity1_type'] = entity1_type
        combinations[combo_key]['entity2_type'] = entity2_type

        # Track performance
        if position:
            try:
                pos_int = int(position)
                if pos_int == 1:
                    combinations[combo_key]['wins'] += 1
                elif pos_int == 2:
                    combinations[combo_key]['places_2nd'] += 1
                elif pos_int == 3:
                    combinations[combo_key]['places_3rd'] += 1
            except ValueError:
                pass  # Skip non-numeric positions

    # Filter combinations by minimum runs
    filtered_combinations = {
        key: data for key, data in combinations.items()
        if data['total_runs'] >= min_runs
    }

    logger.info(f"Found {len(combinations)} total {pair_type} combinations")
    logger.info(f"Filtered to {len(filtered_combinations)} combinations with {min_runs}+ runs")

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
        total_runs = data['total_runs']
        wins = data['wins']
        places_2nd = data['places_2nd']
        places_3rd = data['places_3rd']
        places_total = places_2nd + places_3rd

        # Calculate percentages
        win_percent = (wins / total_runs * 100) if total_runs > 0 else 0.0
        place_percent = ((wins + places_total) / total_runs * 100) if total_runs > 0 else 0.0

        record = {
            # Schema doesn't have explicit 'id' field - it's auto-generated bigint
            'entity1_type': data['entity1_type'],
            'entity1_id': data['entity1_id'],
            'entity2_type': data['entity2_type'],
            'entity2_id': data['entity2_id'],
            'total_runs': total_runs,
            'wins': wins,
            'places_2nd': places_2nd,
            'places_3rd': places_3rd,
            'win_percent': round(win_percent, 2),
            'place_percent': round(place_percent, 2),
            'ae_index': None,  # Would need odds data to calculate
            'profit_loss_1u': None,  # Would need odds data to calculate
            'query_filters': None,  # Optional JSON filters
            'calculated_at': datetime.utcnow().isoformat()
        }

        records.append(record)

    # Sort by total runs (most frequent first)
    records.sort(key=lambda x: x['total_runs'], reverse=True)

    return records


def populate_entity_combinations(
    pair_type: str = 'jockey_horse',
    min_runs: int = 5
) -> Dict:
    """
    Populate entity combinations table

    Args:
        pair_type: Type of entity pair to analyze
        min_runs: Minimum number of runs for inclusion

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
    logger.info(f"POPULATING ra_entity_combinations TABLE - {pair_type}")
    logger.info("=" * 80)
    logger.info(f"Minimum runs per combination: {min_runs}")

    try:
        # Step 1: Analyze combinations
        logger.info("\nStep 1: Analyzing entity pair combinations...")
        combinations = analyze_entity_pairs(db_client, pair_type, min_runs)

        if not combinations:
            logger.warning(f"No {pair_type} combinations found with min_runs={min_runs}")
            return {
                'success': True,
                'pair_type': pair_type,
                'combinations_analyzed': 0,
                'records_created': 0,
                'total_in_db': 0
            }

        # Step 2: Create records
        logger.info("\nStep 2: Creating combination records...")
        records = create_combination_records(combinations)

        logger.info(f"Created {len(records)} combination records")

        # Show top 10
        logger.info(f"\nTop 10 {pair_type} combinations by frequency:")
        for i, record in enumerate(records[:10], 1):
            logger.info(
                f"  {i}. {record['entity1_type']} {record['entity1_id'][:12]}... + "
                f"{record['entity2_type']} {record['entity2_id'][:12]}...: "
                f"{record['total_runs']} runs, {record['wins']} wins "
                f"({record['win_percent']:.1f}%)"
            )

        # Step 3: Insert to database (no upsert - just insert new records)
        logger.info("\nStep 3: Inserting combinations to database...")

        # For this table, we need to check if combinations already exist
        # and only insert new ones, or clear and repopulate
        logger.info("Checking for existing records...")
        existing_count_response = db_client.client.table('ra_entity_combinations')\
            .select('*', count='exact')\
            .eq('entity1_type', records[0]['entity1_type'])\
            .eq('entity2_type', records[0]['entity2_type'])\
            .execute()

        existing_count = existing_count_response.count
        logger.info(f"Found {existing_count} existing {pair_type} combinations")

        if existing_count > 0:
            logger.info(f"Deleting existing {pair_type} combinations...")
            db_client.client.table('ra_entity_combinations')\
                .delete()\
                .eq('entity1_type', records[0]['entity1_type'])\
                .eq('entity2_type', records[0]['entity2_type'])\
                .execute()

        # Insert new records
        stats = db_client.upsert_batch(
            table='ra_entity_combinations',
            records=records,
            unique_key='id'  # Auto-generated, but we're inserting fresh
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Step 4: Verify results
        logger.info("\nStep 4: Verifying results...")

        verify_response = db_client.client.table('ra_entity_combinations')\
            .select('*', count='exact')\
            .eq('entity1_type', records[0]['entity1_type'])\
            .eq('entity2_type', records[0]['entity2_type'])\
            .execute()

        logger.info(f"Total {pair_type} combinations in database: {verify_response.count}")

        logger.info("\n" + "=" * 80)
        logger.info(f"✅ ENTITY COMBINATIONS TABLE POPULATION COMPLETE - {pair_type}")
        logger.info("=" * 80)

        return {
            'success': True,
            'pair_type': pair_type,
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


def populate_all_pair_types(min_runs: int = 5) -> Dict:
    """
    Populate all entity pair types

    Args:
        min_runs: Minimum runs per combination

    Returns:
        Dict with results for all pair types
    """
    pair_types = ['jockey_horse', 'trainer_horse', 'owner_horse', 'jockey_trainer']

    results = {}
    for pair_type in pair_types:
        logger.info(f"\n\n{'=' * 80}")
        logger.info(f"Processing {pair_type} combinations...")
        logger.info('=' * 80)

        result = populate_entity_combinations(pair_type, min_runs)
        results[pair_type] = result

    return results


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate entity combinations table'
    )
    parser.add_argument(
        '--min-runs',
        type=int,
        default=5,
        help='Minimum number of runs for a combination (default: 5)'
    )
    parser.add_argument(
        '--pair-type',
        type=str,
        default='all',
        choices=['all', 'jockey_horse', 'trainer_horse', 'owner_horse', 'jockey_trainer'],
        help='Type of entity pair (default: all)'
    )

    args = parser.parse_args()

    logger.info("Starting entity combinations analysis...")
    start_time = datetime.now()

    if args.pair_type == 'all':
        results = populate_all_pair_types(min_runs=args.min_runs)

        # Summary
        logger.info("\n\n" + "=" * 80)
        logger.info("SUMMARY - ALL PAIR TYPES")
        logger.info("=" * 80)

        total_combinations = 0
        for pair_type, result in results.items():
            if result['success']:
                logger.info(f"✅ {pair_type}: {result['total_in_db']} combinations")
                total_combinations += result['total_in_db']
            else:
                logger.error(f"❌ {pair_type}: FAILED - {result.get('error')}")

        logger.info(f"\nTotal combinations across all types: {total_combinations}")
        logger.info(f"Duration: {datetime.now() - start_time}")

        sys.exit(0 if all(r['success'] for r in results.values()) else 1)

    else:
        result = populate_entity_combinations(args.pair_type, args.min_runs)

        if result['success']:
            logger.info("\n✅ SUCCESS")
            logger.info(f"Combinations analyzed: {result['combinations_analyzed']}")
            logger.info(f"Records created: {result['records_created']}")
            logger.info(f"Total in database: {result['total_in_db']}")
            logger.info(f"Duration: {datetime.now() - start_time}")
        else:
            logger.error(f"\n❌ FAILED: {result.get('error')}")
            sys.exit(1)


if __name__ == '__main__':
    main()
