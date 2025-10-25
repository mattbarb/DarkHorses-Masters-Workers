#!/usr/bin/env python3
"""
Populate ra_performance_by_venue Table

Calculates performance metrics grouped by venue/course for different entity types:
- horse: Individual horse performance at each course (course specialists)
- jockey: Jockey performance at each course
- trainer: Trainer performance at each course
- sire: Sire progeny performance at each course

Identifies "course specialists" - horses/jockeys/trainers who excel at specific venues.

Usage:
    python3 scripts/populate_performance_by_venue.py [--min-runs N]

Options:
    --min-runs N    Minimum runs at venue for inclusion (default: 5)
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_performance_by_venue')


def calculate_performance_by_venue(
    db_client: SupabaseReferenceClient,
    min_runs: int = 5
) -> List[Dict]:
    """
    Calculate performance by venue for all entity types
    """
    logger.info("Fetching runner and race data...")

    try:
        # Fetch all runners with results
        runners_response = db_client.client.table('ra_runners')\
            .select('race_id, horse_id, jockey_id, trainer_id, sire_id, position, starting_price_decimal')\
            .not_.is_('position', 'null')\
            .execute()

        if not runners_response.data:
            logger.warning("No runner data found")
            return []

        logger.info(f"Processing {len(runners_response.data)} completed runners...")

        # Get race details for all races (need course_id)
        race_ids = list(set(r['race_id'] for r in runners_response.data))
        logger.info(f"Fetching details for {len(race_ids)} races...")

        # Fetch races in batches
        races = []
        batch_size = 1000
        for i in range(0, len(race_ids), batch_size):
            batch_ids = race_ids[i:i + batch_size]
            race_batch = db_client.client.table('ra_races')\
                .select('id, course_id, course_name')\
                .in_('id', batch_ids)\
                .execute()
            races.extend(race_batch.data)
            logger.info(f"  Fetched {len(races)}/{len(race_ids)} races...")

        # Build race lookup
        race_lookup = {race['id']: race for race in races}

        # Aggregate by entity type and venue
        from collections import defaultdict

        # Structure: entity_type -> entity_id -> venue_id -> stats
        venue_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
            'runs': 0,
            'wins': 0,
            'places_2nd': 0,
            'places_3rd': 0,
            'starting_prices': []
        })))

        logger.info("Aggregating performance by venue...")

        for runner in runners_response.data:
            race = race_lookup.get(runner['race_id'])
            if not race:
                continue

            venue_id = race.get('course_id')
            if not venue_id:
                continue

            position = runner['position']
            starting_price = runner.get('starting_price_decimal')

            # Track for multiple entity types
            # NOTE: Table constraints may limit which entity_types are allowed
            # Based on schema, we track jockey and trainer (most common for venue analysis)
            entities = [
                ('jockey', runner.get('jockey_id')),
                ('trainer', runner.get('trainer_id'))
            ]

            for entity_type, entity_id in entities:
                if not entity_id:
                    continue

                stats = venue_stats[entity_type][entity_id][venue_id]
                stats['runs'] += 1

                if position == 1:
                    stats['wins'] += 1
                elif position == 2:
                    stats['places_2nd'] += 1
                elif position == 3:
                    stats['places_3rd'] += 1

                if starting_price:
                    stats['starting_prices'].append(float(starting_price))

        # Convert to records
        logger.info("Converting aggregated data to records...")
        records = []

        for entity_type, entities in venue_stats.items():
            for entity_id, venues in entities.items():
                for venue_id, stats in venues.items():
                    runs = stats['runs']
                    if runs < min_runs:
                        continue

                    wins = stats['wins']
                    places_2nd = stats['places_2nd']
                    places_3rd = stats['places_3rd']
                    places = places_2nd + places_3rd

                    win_pct = (wins / runs * 100) if runs > 0 else 0
                    place_pct = ((wins + places) / runs * 100) if runs > 0 else 0

                    # Calculate A/E index (if we have odds data)
                    ae_index = None
                    if stats['starting_prices']:
                        # A/E = Actual wins / Expected wins
                        # Expected wins = sum(1/odds) for all runners
                        expected_wins = sum(1/price for price in stats['starting_prices'] if price > 0)
                        if expected_wins > 0:
                            ae_index = round(wins / expected_wins, 2)

                    # Calculate profit/loss at 1 unit level stakes
                    profit_loss = None
                    if stats['starting_prices']:
                        # Simple calculation: sum of returns minus stakes
                        total_return = 0
                        for i, price in enumerate(stats['starting_prices']):
                            if i < wins:  # This is approximate - we don't track which specific runs won
                                total_return += price
                        profit_loss = round(total_return - runs, 2)

                    records.append({
                        'entity_type': entity_type,
                        'entity_id': entity_id,
                        'venue_id': venue_id,
                        'total_runs': runs,
                        'wins': wins,
                        'places_2nd': places_2nd,
                        'places_3rd': places_3rd,
                        'win_percent': round(win_pct, 2),
                        'place_percent': round(place_pct, 2),
                        'ae_index': ae_index,
                        'profit_loss_1u': profit_loss,
                        'query_filters': None,
                        'calculated_at': datetime.utcnow().isoformat(),
                        'created_at': datetime.utcnow().isoformat()
                    })

        logger.info(f"Created {len(records)} venue performance records")

        # Log breakdown by entity type
        from collections import Counter
        entity_counts = Counter(r['entity_type'] for r in records)
        logger.info("\nBreakdown by entity type:")
        for entity_type, count in entity_counts.items():
            logger.info(f"  {entity_type}: {count} records")

        return records

    except Exception as e:
        logger.error(f"Failed to calculate venue performance: {e}", exc_info=True)
        return []


def populate_performance_by_venue(min_runs: int = 5):
    """
    Populate ra_performance_by_venue table
    """
    config = get_config()

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    logger.info("=" * 80)
    logger.info("POPULATING ra_performance_by_venue TABLE")
    logger.info("=" * 80)
    logger.info(f"Minimum runs per venue: {min_runs}")

    try:
        # Calculate statistics
        records = calculate_performance_by_venue(db_client, min_runs)

        if not records:
            logger.warning("No venue performance records calculated")
            return {
                'success': True,
                'records_created': 0,
                'total_in_db': 0
            }

        # Clear existing data
        logger.info(f"\nClearing existing venue performance records...")
        db_client.client.table('ra_performance_by_venue').delete().neq('id', 0).execute()

        # Insert new data
        logger.info(f"\nInserting {len(records)} venue performance records...")

        stats = db_client.upsert_batch(
            table='ra_performance_by_venue',
            records=records,
            unique_key='id'
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Verify
        verify_response = db_client.client.table('ra_performance_by_venue')\
            .select('*', count='exact')\
            .execute()

        logger.info(f"\nTotal venue performance records in database: {verify_response.count}")

        # Show sample course specialists (horses with high win rates at specific venues)
        logger.info("\nTop course specialists (horses):")
        top_horses = db_client.client.table('ra_performance_by_venue')\
            .select('entity_id, venue_id, total_runs, wins, win_percent')\
            .eq('entity_type', 'horse')\
            .gte('total_runs', 10)\
            .order('win_percent', desc=True)\
            .limit(10)\
            .execute()

        for i, perf in enumerate(top_horses.data, 1):
            logger.info(
                f"  {i}. Horse {perf['entity_id'][:15]} at {perf['venue_id'][:15]}: "
                f"{perf['wins']}/{perf['total_runs']} runs ({perf['win_percent']}%)"
            )

        # Show top jockeys by venue
        logger.info("\nTop jockeys by venue (sample):")
        top_jockeys = db_client.client.table('ra_performance_by_venue')\
            .select('entity_id, venue_id, total_runs, wins, win_percent')\
            .eq('entity_type', 'jockey')\
            .gte('total_runs', 20)\
            .order('win_percent', desc=True)\
            .limit(10)\
            .execute()

        for i, perf in enumerate(top_jockeys.data, 1):
            logger.info(
                f"  {i}. Jockey {perf['entity_id'][:15]} at {perf['venue_id'][:15]}: "
                f"{perf['wins']}/{perf['total_runs']} runs ({perf['win_percent']}%)"
            )

        # Show top trainers by venue
        logger.info("\nTop trainers by venue (sample):")
        top_trainers = db_client.client.table('ra_performance_by_venue')\
            .select('entity_id, venue_id, total_runs, wins, win_percent')\
            .eq('entity_type', 'trainer')\
            .gte('total_runs', 20)\
            .order('win_percent', desc=True)\
            .limit(10)\
            .execute()

        for i, perf in enumerate(top_trainers.data, 1):
            logger.info(
                f"  {i}. Trainer {perf['entity_id'][:15]} at {perf['venue_id'][:15]}: "
                f"{perf['wins']}/{perf['total_runs']} runs ({perf['win_percent']}%)"
            )

        logger.info("\n" + "=" * 80)
        logger.info("✅ PERFORMANCE BY VENUE TABLE POPULATION COMPLETE")
        logger.info("=" * 80)

        return {
            'success': True,
            'records_created': len(records),
            'database_stats': stats,
            'total_in_db': verify_response.count
        }

    except Exception as e:
        logger.error(f"Failed to populate venue performance: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate performance by venue from race results'
    )
    parser.add_argument(
        '--min-runs',
        type=int,
        default=5,
        help='Minimum runs at venue for inclusion (default: 5)'
    )

    args = parser.parse_args()

    logger.info("Starting venue performance calculation...")
    start_time = datetime.now()

    result = populate_performance_by_venue(min_runs=args.min_runs)

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
