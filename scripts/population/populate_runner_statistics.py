#!/usr/bin/env python3
"""
Populate ra_runner_statistics Table

Calculates individual runner-level statistics from ra_runners table.
This includes performance metrics for each race entry (runner) rather than
aggregated horse statistics.

Statistics calculated for each runner:
- Career stats: prize money, win/place percentages
- Course performance: runs/wins at this course
- Distance performance: runs/wins at this distance
- Going performance: firm/good/soft/heavy ground performance
- Recent form: last 10 runs, last 12 months
- Partnership stats: with this jockey

Uses efficient SQL aggregation via database joins.

Usage:
    python3 scripts/populate_runner_statistics.py [--min-runs N]

Options:
    --min-runs N    Minimum career runs for inclusion (default: 3)
    --batch-size N  Batch size for processing (default: 1000)
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient

logger = get_logger('populate_runner_statistics')


def calculate_runner_statistics(
    db_client: SupabaseReferenceClient,
    min_runs: int = 3
) -> List[Dict]:
    """
    Calculate runner statistics using SQL aggregation

    For each runner (individual race entry), calculate:
    - Career performance of the horse
    - Course-specific performance
    - Distance-specific performance
    - Going-specific performance
    - Recent form
    """
    logger.info("Fetching runner and race data...")

    # Fetch all runners with their race details
    # Join with races to get course, distance, going, surface
    try:
        # Get all runners with race context
        runners_response = db_client.client.table('ra_runners')\
            .select('id, race_id, horse_id, horse_name, jockey_id, position, prize_won, created_at')\
            .not_.is_('position', 'null')\
            .execute()

        if not runners_response.data:
            logger.warning("No runner data found")
            return []

        logger.info(f"Processing {len(runners_response.data)} completed runners...")

        # Get race details for all races
        race_ids = list(set(r['race_id'] for r in runners_response.data))
        logger.info(f"Fetching details for {len(race_ids)} races...")

        # Fetch races in batches (1000 at a time)
        races = []
        batch_size = 1000
        for i in range(0, len(race_ids), batch_size):
            batch_ids = race_ids[i:i + batch_size]
            race_batch = db_client.client.table('ra_races')\
                .select('id, course_id, distance_f, going, surface, off_time')\
                .in_('id', batch_ids)\
                .execute()
            races.extend(race_batch.data)
            logger.info(f"  Fetched {len(races)}/{len(race_ids)} races...")

        # Build race lookup
        race_lookup = {race['id']: race for race in races}

        # Now calculate stats per runner
        logger.info("Calculating statistics per runner...")
        from collections import defaultdict

        # Group runners by horse for career stats
        horse_stats = defaultdict(lambda: {
            'runs': [],
            'total_prize': 0,
            'wins': 0,
            'places': 0,
            'last_raced': None,
            'last_won': None
        })

        # First pass: aggregate by horse
        for runner in runners_response.data:
            horse_id = runner['horse_id']
            position = runner['position']
            prize = runner.get('prize_won', 0) or 0
            created_at = runner.get('created_at')

            horse_stats[horse_id]['runs'].append(runner)
            horse_stats[horse_id]['total_prize'] += float(prize)

            if position == 1:
                horse_stats[horse_id]['wins'] += 1
                if created_at:
                    current_won = horse_stats[horse_id]['last_won']
                    if not current_won or created_at > current_won:
                        horse_stats[horse_id]['last_won'] = created_at

            if position in [1, 2, 3]:
                horse_stats[horse_id]['places'] += 1

            if created_at:
                current_raced = horse_stats[horse_id]['last_raced']
                if not current_raced or created_at > current_raced:
                    horse_stats[horse_id]['last_raced'] = created_at

        # Second pass: calculate per-runner statistics
        records = []
        now = datetime.utcnow()
        twelve_months_ago = now - timedelta(days=365)

        for runner in runners_response.data:
            runner_id = runner['id']
            horse_id = runner['horse_id']
            race_id = runner['race_id']
            jockey_id = runner['jockey_id']

            # Get race context
            race = race_lookup.get(race_id)
            if not race:
                continue

            course_id = race['course_id']
            distance_f = race['distance_f']
            going = race.get('going', '').lower()
            surface = race.get('surface', '').lower()

            # Get horse career stats
            horse_data = horse_stats[horse_id]
            career_runs = len(horse_data['runs'])

            # Skip horses with too few runs
            if career_runs < min_runs:
                continue

            career_wins = horse_data['wins']
            career_places = horse_data['places']
            career_prize = horse_data['total_prize']

            career_win_pct = (career_wins / career_runs * 100) if career_runs > 0 else 0
            career_place_pct = (career_places / career_runs * 100) if career_runs > 0 else 0

            # Course stats (all races at this course)
            course_runs = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('course_id') == course_id)
            course_wins = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('course_id') == course_id and r['position'] == 1)
            course_2nds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('course_id') == course_id and r['position'] == 2)
            course_3rds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('course_id') == course_id and r['position'] == 3)

            # Course + distance stats
            course_dist_runs = sum(1 for r in horse_data['runs']
                                   if race_lookup.get(r['race_id'], {}).get('course_id') == course_id
                                   and race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f)
            course_dist_wins = sum(1 for r in horse_data['runs']
                                    if race_lookup.get(r['race_id'], {}).get('course_id') == course_id
                                    and race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f
                                    and r['position'] == 1)
            course_dist_2nds = sum(1 for r in horse_data['runs']
                                    if race_lookup.get(r['race_id'], {}).get('course_id') == course_id
                                    and race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f
                                    and r['position'] == 2)
            course_dist_3rds = sum(1 for r in horse_data['runs']
                                    if race_lookup.get(r['race_id'], {}).get('course_id') == course_id
                                    and race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f
                                    and r['position'] == 3)

            # Distance stats (all races at this distance)
            distance_runs = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f)
            distance_wins = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f and r['position'] == 1)
            distance_2nds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f and r['position'] == 2)
            distance_3rds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('distance_f') == distance_f and r['position'] == 3)

            # Going stats
            firm_runs = sum(1 for r in horse_data['runs'] if 'firm' in race_lookup.get(r['race_id'], {}).get('going', '').lower())
            firm_wins = sum(1 for r in horse_data['runs'] if 'firm' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 1)
            firm_2nds = sum(1 for r in horse_data['runs'] if 'firm' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 2)
            firm_3rds = sum(1 for r in horse_data['runs'] if 'firm' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 3)

            good_runs = sum(1 for r in horse_data['runs'] if 'good' in race_lookup.get(r['race_id'], {}).get('going', '').lower())
            good_wins = sum(1 for r in horse_data['runs'] if 'good' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 1)
            good_2nds = sum(1 for r in horse_data['runs'] if 'good' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 2)
            good_3rds = sum(1 for r in horse_data['runs'] if 'good' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 3)

            soft_runs = sum(1 for r in horse_data['runs'] if 'soft' in race_lookup.get(r['race_id'], {}).get('going', '').lower())
            soft_wins = sum(1 for r in horse_data['runs'] if 'soft' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 1)
            soft_2nds = sum(1 for r in horse_data['runs'] if 'soft' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 2)
            soft_3rds = sum(1 for r in horse_data['runs'] if 'soft' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 3)

            heavy_runs = sum(1 for r in horse_data['runs'] if 'heavy' in race_lookup.get(r['race_id'], {}).get('going', '').lower())
            heavy_wins = sum(1 for r in horse_data['runs'] if 'heavy' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 1)
            heavy_2nds = sum(1 for r in horse_data['runs'] if 'heavy' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 2)
            heavy_3rds = sum(1 for r in horse_data['runs'] if 'heavy' in race_lookup.get(r['race_id'], {}).get('going', '').lower() and r['position'] == 3)

            # Surface stats
            aw_runs = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['aw', 'all weather', 'tapeta', 'polytrack'])
            aw_wins = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['aw', 'all weather', 'tapeta', 'polytrack'] and r['position'] == 1)
            aw_2nds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['aw', 'all weather', 'tapeta', 'polytrack'] and r['position'] == 2)
            aw_3rds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['aw', 'all weather', 'tapeta', 'polytrack'] and r['position'] == 3)

            jumps_runs = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['hurdle', 'chase', 'nh flat'])
            jumps_wins = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['hurdle', 'chase', 'nh flat'] and r['position'] == 1)
            jumps_2nds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['hurdle', 'chase', 'nh flat'] and r['position'] == 2)
            jumps_3rds = sum(1 for r in horse_data['runs'] if race_lookup.get(r['race_id'], {}).get('surface', '').lower() in ['hurdle', 'chase', 'nh flat'] and r['position'] == 3)

            # Jockey partnership stats
            jockey_runs = sum(1 for r in horse_data['runs'] if r['jockey_id'] == jockey_id) if jockey_id else 0
            jockey_wins = sum(1 for r in horse_data['runs'] if r['jockey_id'] == jockey_id and r['position'] == 1) if jockey_id else 0
            jockey_2nds = sum(1 for r in horse_data['runs'] if r['jockey_id'] == jockey_id and r['position'] == 2) if jockey_id else 0
            jockey_3rds = sum(1 for r in horse_data['runs'] if r['jockey_id'] == jockey_id and r['position'] == 3) if jockey_id else 0

            # Recent form (last 10 runs)
            sorted_runs = sorted(horse_data['runs'],
                               key=lambda x: x.get('created_at') or '1970-01-01',
                               reverse=True)
            last_10 = sorted_runs[:10]
            last_10_wins = sum(1 for r in last_10 if r['position'] == 1)
            last_10_2nds = sum(1 for r in last_10 if r['position'] == 2)
            last_10_3rds = sum(1 for r in last_10 if r['position'] == 3)

            # Last 12 months
            last_12m = [r for r in horse_data['runs']
                       if r.get('created_at') and r['created_at'] >= twelve_months_ago.isoformat()]
            last_12m_runs = len(last_12m)
            last_12m_wins = sum(1 for r in last_12m if r['position'] == 1)
            last_12m_2nds = sum(1 for r in last_12m if r['position'] == 2)
            last_12m_3rds = sum(1 for r in last_12m if r['position'] == 3)

            # Winning distance range (not implemented - would need detailed distance parsing)

            records.append({
                'runner_id': runner_id,
                'horse_id': horse_id,
                'career_prize': round(career_prize, 2),
                'career_win_percent': round(career_win_pct, 2),
                'career_place_percent': round(career_place_pct, 2),
                'course_runs': course_runs,
                'course_wins': course_wins,
                'course_2nds': course_2nds,
                'course_3rds': course_3rds,
                'course_distance_runs': course_dist_runs,
                'course_distance_wins': course_dist_wins,
                'course_distance_2nds': course_dist_2nds,
                'course_distance_3rds': course_dist_3rds,
                'distance_runs': distance_runs,
                'distance_wins': distance_wins,
                'distance_2nds': distance_2nds,
                'distance_3rds': distance_3rds,
                'firm_runs': firm_runs,
                'firm_wins': firm_wins,
                'firm_2nds': firm_2nds,
                'firm_3rds': firm_3rds,
                'good_runs': good_runs,
                'good_wins': good_wins,
                'good_2nds': good_2nds,
                'good_3rds': good_3rds,
                'soft_runs': soft_runs,
                'soft_wins': soft_wins,
                'soft_2nds': soft_2nds,
                'soft_3rds': soft_3rds,
                'heavy_runs': heavy_runs,
                'heavy_wins': heavy_wins,
                'heavy_2nds': heavy_2nds,
                'heavy_3rds': heavy_3rds,
                'aw_runs': aw_runs,
                'aw_wins': aw_wins,
                'aw_2nds': aw_2nds,
                'aw_3rds': aw_3rds,
                'jockey_runs': jockey_runs,
                'jockey_wins': jockey_wins,
                'jockey_2nds': jockey_2nds,
                'jockey_3rds': jockey_3rds,
                'jumps_runs': jumps_runs,
                'jumps_wins': jumps_wins,
                'jumps_2nds': jumps_2nds,
                'jumps_3rds': jumps_3rds,
                'last_10_runs': len(last_10),
                'last_10_wins': last_10_wins,
                'last_10_2nds': last_10_2nds,
                'last_10_3rds': last_10_3rds,
                'last_12m_runs': last_12m_runs,
                'last_12m_wins': last_12m_wins,
                'last_12m_2nds': last_12m_2nds,
                'last_12m_3rds': last_12m_3rds,
                'last_raced': horse_data['last_raced'].split('T')[0] if horse_data['last_raced'] else None,
                'last_won': horse_data['last_won'].split('T')[0] if horse_data['last_won'] else None,
                'min_winning_distance_yards': None,
                'max_winning_distance_yards': None,
                'created_at': datetime.utcnow().isoformat(),
                'updated_at': datetime.utcnow().isoformat()
            })

        logger.info(f"Calculated statistics for {len(records)} runners")
        return records

    except Exception as e:
        logger.error(f"Failed to calculate runner statistics: {e}", exc_info=True)
        return []


def populate_runner_statistics(min_runs: int = 3):
    """
    Populate ra_runner_statistics table
    """
    config = get_config()

    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=config.supabase.batch_size
    )

    logger.info("=" * 80)
    logger.info("POPULATING ra_runner_statistics TABLE")
    logger.info("=" * 80)
    logger.info(f"Minimum career runs: {min_runs}")

    try:
        # Calculate statistics
        records = calculate_runner_statistics(db_client, min_runs)

        if not records:
            logger.warning("No runner statistics calculated")
            return {
                'success': True,
                'records_created': 0,
                'total_in_db': 0
            }

        # Clear existing data
        logger.info(f"\nClearing existing runner statistics...")
        db_client.client.table('ra_runner_statistics').delete().neq('id', 0).execute()

        # Insert new data
        logger.info(f"\nInserting {len(records)} runner statistics...")

        stats = db_client.upsert_batch(
            table='ra_runner_statistics',
            records=records,
            unique_key='runner_id'
        )

        logger.info(f"Database operation completed:")
        logger.info(f"  Inserted: {stats.get('inserted', 0)}")
        logger.info(f"  Errors: {stats.get('errors', 0)}")

        # Verify
        verify_response = db_client.client.table('ra_runner_statistics')\
            .select('*', count='exact')\
            .execute()

        logger.info(f"\nTotal runner statistics in database: {verify_response.count}")

        # Show sample top performers
        logger.info("\nSample top performers (by career win %):")
        top_performers = db_client.client.table('ra_runner_statistics')\
            .select('horse_id, career_win_percent, course_wins, distance_wins')\
            .gte('career_win_percent', 20)\
            .order('career_win_percent', desc=True)\
            .limit(10)\
            .execute()

        for i, perf in enumerate(top_performers.data, 1):
            logger.info(
                f"  {i}. Horse {perf['horse_id'][:15]}: "
                f"{perf['career_win_percent']}% wins, "
                f"{perf['course_wins']} course wins, "
                f"{perf['distance_wins']} distance wins"
            )

        logger.info("\n" + "=" * 80)
        logger.info("✅ RUNNER STATISTICS TABLE POPULATION COMPLETE")
        logger.info("=" * 80)

        return {
            'success': True,
            'records_created': len(records),
            'database_stats': stats,
            'total_in_db': verify_response.count
        }

    except Exception as e:
        logger.error(f"Failed to populate runner statistics: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate runner statistics from race results'
    )
    parser.add_argument(
        '--min-runs',
        type=int,
        default=3,
        help='Minimum career runs for inclusion (default: 3)'
    )

    args = parser.parse_args()

    logger.info("Starting runner statistics calculation...")
    start_time = datetime.now()

    result = populate_runner_statistics(min_runs=args.min_runs)

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
