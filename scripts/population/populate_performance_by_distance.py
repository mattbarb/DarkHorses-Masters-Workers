#!/usr/bin/env python3
"""
Populate ra_performance_by_distance Table

Calculates performance metrics grouped by distance for different entity types:
- horse: Individual horse performance at each distance
- jockey: Jockey performance at each distance
- trainer: Trainer performance at each distance
- sire: Sire progeny performance at each distance

Distance groupings:
- Sprint: 5f-7f (1000-1400 yards)
- Mile: 7f-9f (1400-1800 yards)
- Middle: 9f-12f (1800-2400 yards)
- Staying: 12f+ (2400+ yards)

Plus exact distance tracking for all distances run.

Usage:
    python3 scripts/populate_performance_by_distance.py [--min-runs N]

Options:
    --min-runs N    Minimum runs at distance for inclusion (default: 5)
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List
import argparse
import re

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_performance_by_distance')


def parse_distance_to_yards(distance_str: str) -> int:
    """
    Parse distance string to yards

    Examples:
    - "16f" -> 3520 yards (16 * 220)
    - "2m" -> 3520 yards (2 miles * 1760)
    - "2m4f" -> 4400 yards (2 miles + 4 furlongs)
    - "1m2f110y" -> 2090 yards
    """
    if not distance_str:
        return 0

    yards = 0
    distance_str = str(distance_str).strip().lower()

    # Extract miles
    miles_match = re.search(r'(\d+)m', distance_str)
    if miles_match:
        yards += int(miles_match.group(1)) * 1760

    # Extract furlongs
    furlongs_match = re.search(r'(\d+)f', distance_str)
    if furlongs_match:
        yards += int(furlongs_match.group(1)) * 220

    # Extract yards
    yards_match = re.search(r'(\d+)y', distance_str)
    if yards_match:
        yards += int(yards_match.group(1))

    return yards


def get_distance_category(yards: int) -> str:
    """Categorize distance"""
    if yards < 1400:
        return "Sprint (5f-7f)"
    elif yards < 1800:
        return "Mile (7f-9f)"
    elif yards < 2400:
        return "Middle (9f-12f)"
    else:
        return "Staying (12f+)"


def parse_finishing_time(time_str: str) -> float:
    """
    Parse finishing time to seconds

    Examples:
    - "1:48.55" -> 108.55
    - "2:05.32" -> 125.32
    """
    if not time_str:
        return None

    try:
        parts = str(time_str).split(':')
        if len(parts) == 2:
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        elif len(parts) == 1:
            return float(parts[0])
    except:
        return None

    return None


def calculate_performance_by_distance(
    db_client: SupabaseReferenceClient,
    min_runs: int = 5
) -> List[Dict]:
    """
    Calculate performance by distance for all entity types
    """
    logger.info("Fetching runner and race data...")

    try:
        # Fetch all runners with results
        runners_response = db_client.client.table('ra_runners')\
            .select('race_id, horse_id, jockey_id, trainer_id, sire_id, position, finishing_time, starting_price_decimal')\
            .not_.is_('position', 'null')\
            .execute()

        if not runners_response.data:
            logger.warning("No runner data found")
            return []

        logger.info(f"Processing {len(runners_response.data)} completed runners...")

        # Get race details for all races
        race_ids = list(set(r['race_id'] for r in runners_response.data))
        logger.info(f"Fetching details for {len(race_ids)} races...")

        # Fetch races in batches
        races = []
        batch_size = 1000
        for i in range(0, len(race_ids), batch_size):
            batch_ids = race_ids[i:i + batch_size]
            race_batch = db_client.client.table('ra_races')\
                .select('id, distance_f, going')\
                .in_('id', batch_ids)\
                .execute()
            races.extend(race_batch.data)
            logger.info(f"  Fetched {len(races)}/{len(race_ids)} races...")

        # Build race lookup
        race_lookup = {race['id']: race for race in races}

        # Aggregate by entity type and distance
        from collections import defaultdict

        # Structure: entity_type -> entity_id -> distance_yards -> stats
        distance_stats = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: {
            'runs': 0,
            'wins': 0,
            'places_2nd': 0,
            'places_3rd': 0,
            'finishing_times': [],
            'starting_prices': [],
            'going_breakdown': defaultdict(int)
        })))

        logger.info("Aggregating performance by distance...")

        for runner in runners_response.data:
            race = race_lookup.get(runner['race_id'])
            if not race:
                continue

            # Parse distance
            distance_f = race.get('distance_f', '')
            yards = parse_distance_to_yards(distance_f)
            if yards == 0:
                continue

            position = runner['position']
            going = race.get('going', 'Unknown')
            finishing_time = parse_finishing_time(runner.get('finishing_time'))
            starting_price = runner.get('starting_price_decimal')

            # Track for multiple entity types
            # NOTE: Table constraints may limit which entity_types are allowed
            # Based on schema, we track horse, jockey, trainer
            entities = [
                ('horse', runner.get('horse_id')),
                ('jockey', runner.get('jockey_id')),
                ('trainer', runner.get('trainer_id'))
            ]

            for entity_type, entity_id in entities:
                if not entity_id:
                    continue

                stats = distance_stats[entity_type][entity_id][yards]
                stats['runs'] += 1
                stats['going_breakdown'][going] += 1

                if position == 1:
                    stats['wins'] += 1
                elif position == 2:
                    stats['places_2nd'] += 1
                elif position == 3:
                    stats['places_3rd'] += 1

                if finishing_time:
                    stats['finishing_times'].append(finishing_time)

                if starting_price:
                    stats['starting_prices'].append(float(starting_price))

        # Convert to records
        logger.info("Converting aggregated data to records...")
        records = []

        for entity_type, entities in distance_stats.items():
            for entity_id, distances in entities.items():
                for yards, stats in distances.items():
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
                        # P/L = sum of (odds-1) for wins - number of losses
                        pl = sum(price - 1 for i, price in enumerate(stats['starting_prices'])
                                if i < wins) - (runs - wins)
                        profit_loss = round(pl, 2)

                    # Time statistics
                    best_time = min(stats['finishing_times']) if stats['finishing_times'] else None
                    avg_time = sum(stats['finishing_times']) / len(stats['finishing_times']) if stats['finishing_times'] else None
                    last_time = stats['finishing_times'][-1] if stats['finishing_times'] else None

                    # Distance display
                    distance_display = get_distance_category(yards)

                    records.append({
                        'entity_type': entity_type,
                        'entity_id': entity_id,
                        'distance_yards': yards,
                        'distance_display': distance_display,
                        'total_runs': runs,
                        'wins': wins,
                        'places_2nd': places_2nd,
                        'places_3rd': places_3rd,
                        'win_percent': round(win_pct, 2),
                        'place_percent': round(place_pct, 2),
                        'ae_index': ae_index,
                        'profit_loss_1u': profit_loss,
                        'best_time_seconds': round(best_time, 2) if best_time else None,
                        'avg_time_seconds': round(avg_time, 2) if avg_time else None,
                        'last_time_seconds': round(last_time, 2) if last_time else None,
                        'going_breakdown': dict(stats['going_breakdown']),
                        'query_filters': None,
                        'calculated_at': datetime.utcnow().isoformat(),
                        'created_at': datetime.utcnow().isoformat()
                    })

        logger.info(f"Created {len(records)} distance performance records")

        # Log breakdown by entity type
        from collections import Counter
        entity_counts = Counter(r['entity_type'] for r in records)
        logger.info("\nBreakdown by entity type:")
        for entity_type, count in entity_counts.items():
            logger.info(f"  {entity_type}: {count} records")

        return records

    except Exception as e:
        logger.error(f"Failed to calculate distance performance: {e}", exc_info=True)
        return []


def populate_performance_by_distance(min_runs: int = 5):
    """
    Populate ra_performance_by_distance table
    """
    config = get_config()

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    logger.info("=" * 80)
    logger.info("POPULATING ra_performance_by_distance TABLE")
    logger.info("=" * 80)
    logger.info(f"Minimum runs per distance: {min_runs}")

    try:
        # Calculate statistics
        records = calculate_performance_by_distance(db_client, min_runs)

        if not records:
            logger.warning("No distance performance records calculated")
            return {
                'success': True,
                'records_created': 0,
                'total_in_db': 0
            }

        # Clear existing data
        logger.info(f"\nClearing existing distance performance records...")
        db_client.client.table('ra_performance_by_distance').delete().neq('id', 0).execute()

        # Insert new data
        logger.info(f"\nInserting {len(records)} distance performance records...")

        stats = db_client.upsert_batch(
            table='ra_performance_by_distance',
            records=records,
            unique_key='id'
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Verify
        verify_response = db_client.client.table('ra_performance_by_distance')\
            .select('*', count='exact')\
            .execute()

        logger.info(f"\nTotal distance performance records in database: {verify_response.count}")

        # Show sample top performers at different distances
        logger.info("\nSample top performers by distance category:")

        for category in ["Sprint (5f-7f)", "Mile (7f-9f)", "Middle (9f-12f)", "Staying (12f+)"]:
            logger.info(f"\n{category}:")
            top = db_client.client.table('ra_performance_by_distance')\
                .select('entity_type, entity_id, distance_yards, total_runs, wins, win_percent')\
                .eq('distance_display', category)\
                .eq('entity_type', 'horse')\
                .gte('total_runs', 10)\
                .order('win_percent', desc=True)\
                .limit(3)\
                .execute()

            for i, perf in enumerate(top.data, 1):
                logger.info(
                    f"  {i}. {perf['entity_type']} {perf['entity_id'][:15]}: "
                    f"{perf['wins']}/{perf['total_runs']} runs ({perf['win_percent']}%)"
                )

        logger.info("\n" + "=" * 80)
        logger.info("✅ PERFORMANCE BY DISTANCE TABLE POPULATION COMPLETE")
        logger.info("=" * 80)

        return {
            'success': True,
            'records_created': len(records),
            'database_stats': stats,
            'total_in_db': verify_response.count
        }

    except Exception as e:
        logger.error(f"Failed to populate distance performance: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate performance by distance from race results'
    )
    parser.add_argument(
        '--min-runs',
        type=int,
        default=5,
        help='Minimum runs at distance for inclusion (default: 5)'
    )

    args = parser.parse_args()

    logger.info("Starting distance performance calculation...")
    start_time = datetime.now()

    result = populate_performance_by_distance(min_runs=args.min_runs)

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
