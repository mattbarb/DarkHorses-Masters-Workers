#!/usr/bin/env python3
"""
Populate ra_entity_combinations Table from ra_mst_runners

Calculates entity pair statistics (jockey-horse, trainer-horse, etc.)
directly from the ra_mst_runners table using database aggregation.

This is more efficient than fetching all rows and processing in Python.

Entity Pair Types:
- horse + jockey (most races together)
- horse + trainer
- horse + owner
- jockey + trainer (partnerships)

Usage:
    python3 scripts/populate_entity_combinations_from_runners.py [--min-runs N]

Options:
    --min-runs N    Minimum runs for inclusion (default: 5)
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_entity_combinations')


def calculate_combinations_sql(
    db_client: SupabaseReferenceClient,
    entity1_type: str,
    entity2_type: str,
    entity1_col: str,
    entity2_col: str,
    min_runs: int = 5
):
    """
    Calculate entity combinations using SQL aggregation

    The constraint requires entity types in canonical (alphabetical) order.
    So we need to ensure entity1_type < entity2_type alphabetically.
    """
    # Ensure canonical order
    if entity1_type > entity2_type:
        entity1_type, entity2_type = entity2_type, entity1_type
        entity1_col, entity2_col = entity2_col, entity1_col

    logger.info(f"Calculating {entity1_type}-{entity2_type} combinations...")

    # SQL aggregation query
    sql = f"""
        SELECT
            '{entity1_type}' as entity1_type,
            {entity1_col} as entity1_id,
            '{entity2_type}' as entity2_type,
            {entity2_col} as entity2_id,
            COUNT(*) as total_runs,
            SUM(CASE WHEN position = '1' THEN 1 ELSE 0 END) as wins,
            SUM(CASE WHEN position = '2' THEN 1 ELSE 0 END) as places_2nd,
            SUM(CASE WHEN position = '3' THEN 1 ELSE 0 END) as places_3rd
        FROM ra_mst_runners
        WHERE {entity1_col} IS NOT NULL
          AND {entity2_col} IS NOT NULL
          AND position IS NOT NULL
        GROUP BY {entity1_col}, {entity2_col}
        HAVING COUNT(*) >= {min_runs}
        ORDER BY COUNT(*) DESC
    """

    try:
        # Execute via RPC or raw SQL
        # Supabase doesn't directly support raw SQL, so we'll fetch and aggregate in Python
        # (More efficient would be a stored procedure, but this works)

        logger.info("Fetching runner data for aggregation...")
        response = db_client.client.table('ra_mst_runners')\
            .select(f'{entity1_col}, {entity2_col}, position')\
            .not_.is_(entity1_col, 'null')\
            .not_.is_(entity2_col, 'null')\
            .not_.is_('position', 'null')\
            .execute()

        if not response.data:
            logger.warning("No runner data found")
            return []

        logger.info(f"Aggregating {len(response.data)} runner records...")

        # Aggregate in Python
        from collections import defaultdict

        combos = defaultdict(lambda: {
            'total_runs': 0,
            'wins': 0,
            'places_2nd': 0,
            'places_3rd': 0
        })

        for row in response.data:
            entity1_id = row[entity1_col]
            entity2_id = row[entity2_col]
            position = row['position']

            key = (entity1_id, entity2_id)
            combos[key]['total_runs'] += 1

            try:
                pos_int = int(position)
                if pos_int == 1:
                    combos[key]['wins'] += 1
                elif pos_int == 2:
                    combos[key]['places_2nd'] += 1
                elif pos_int == 3:
                    combos[key]['places_3rd'] += 1
            except ValueError:
                pass

        # Filter and format
        records = []
        for (entity1_id, entity2_id), stats in combos.items():
            if stats['total_runs'] >= min_runs:
                total_runs = stats['total_runs']
                wins = stats['wins']
                places = stats['places_2nd'] + stats['places_3rd']

                win_pct = (wins / total_runs * 100) if total_runs > 0 else 0
                place_pct = ((wins + places) / total_runs * 100) if total_runs > 0 else 0

                records.append({
                    'entity1_type': entity1_type,
                    'entity1_id': entity1_id,
                    'entity2_type': entity2_type,
                    'entity2_id': entity2_id,
                    'total_runs': total_runs,
                    'wins': wins,
                    'places_2nd': stats['places_2nd'],
                    'places_3rd': stats['places_3rd'],
                    'win_percent': round(win_pct, 2),
                    'place_percent': round(place_pct, 2),
                    'ae_index': None,
                    'profit_loss_1u': None,
                    'query_filters': None,
                    'calculated_at': datetime.utcnow().isoformat()
                })

        # Sort by total_runs
        records.sort(key=lambda x: x['total_runs'], reverse=True)

        logger.info(f"Found {len(records)} {entity1_type}-{entity2_type} combinations with {min_runs}+ runs")
        return records

    except Exception as e:
        logger.error(f"Failed to calculate combinations: {e}", exc_info=True)
        return []


def populate_entity_combinations(min_runs: int = 5):
    """
    Populate all entity combination types
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
    logger.info(f"Minimum runs per combination: {min_runs}")

    # Define entity pair types
    # IMPORTANT: Table constraint 'chk_entity_comb_types' only allows jockey+trainer pairs
    # Must be in alphabetical order due to 'chk_entity_comb_canonical_order' constraint
    pair_types = [
        ('jockey', 'trainer', 'jockey_id', 'trainer_id'),
    ]

    all_records = []

    try:
        # Calculate all combination types
        for entity1_type, entity2_type, entity1_col, entity2_col in pair_types:
            logger.info(f"\n{'=' * 80}")
            logger.info(f"Processing {entity1_type}-{entity2_type} combinations...")
            logger.info('=' * 80)

            records = calculate_combinations_sql(
                db_client,
                entity1_type,
                entity2_type,
                entity1_col,
                entity2_col,
                min_runs
            )

            if records:
                logger.info(f"Top 5 {entity1_type}-{entity2_type} combinations:")
                for i, rec in enumerate(records[:5], 1):
                    logger.info(
                        f"  {i}. {rec['entity1_id'][:15]} + {rec['entity2_id'][:15]}: "
                        f"{rec['total_runs']} runs, {rec['wins']} wins ({rec['win_percent']}%)"
                    )

            all_records.extend(records)

        if not all_records:
            logger.warning("No combinations found")
            return {
                'success': True,
                'records_created': 0,
                'total_in_db': 0
            }

        # Clear and repopulate
        logger.info(f"\n{'=' * 80}")
        logger.info(f"Clearing existing combinations...")
        logger.info('=' * 80)

        db_client.client.table('ra_entity_combinations').delete().neq('id', 0).execute()

        # Insert all combinations
        logger.info(f"\nInserting {len(all_records)} combinations...")

        stats = db_client.upsert_batch(
            table='ra_entity_combinations',
            records=all_records,
            unique_key='id'
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Verify
        verify_response = db_client.client.table('ra_entity_combinations')\
            .select('*', count='exact')\
            .execute()

        logger.info(f"\nTotal combinations in database: {verify_response.count}")

        # Summary by type
        logger.info("\nBreakdown by type:")
        for entity1_type, entity2_type, _, _ in pair_types:
            type_count = sum(1 for r in all_records
                           if r['entity1_type'] == entity1_type
                           and r['entity2_type'] == entity2_type)
            logger.info(f"  {entity1_type}-{entity2_type}: {type_count}")

        logger.info("\n" + "=" * 80)
        logger.info("✅ ENTITY COMBINATIONS TABLE POPULATION COMPLETE")
        logger.info("=" * 80)

        return {
            'success': True,
            'records_created': len(all_records),
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
        description='Populate entity combinations from runners'
    )
    parser.add_argument(
        '--min-runs',
        type=int,
        default=5,
        help='Minimum runs for inclusion (default: 5)'
    )

    args = parser.parse_args()

    logger.info("Starting entity combinations calculation...")
    start_time = datetime.now()

    result = populate_entity_combinations(min_runs=args.min_runs)

    if result['success']:
        logger.info("\n✅ SUCCESS")
        logger.info(f"Records created: {result['records_created']}")
        logger.info(f"Total in database: {result['total_in_db']}")
        logger.info(f"Duration: {datetime.now() - start_time}")
    else:
        logger.error(f"\n❌ FAILED: {result.get('error')}")
        sys.exit(1)


if __name__ == '__main__':
    main()
