#!/usr/bin/env python3
"""
Calculate Dam Statistics from Database
========================================

Populates ra_dam_stats table with comprehensive statistics calculated from
historical race data in ra_runners + ra_races + ra_rel_pedigree tables.

Statistics Calculated:
----------------------
1. OWN RACING CAREER (dam's performance as a racehorse):
   - own_race_runs, own_race_wins, own_race_places
   - own_total_prize, own_best_position, own_avg_position
   - own_career_start, own_career_end

2. PROGENY STATISTICS (offspring performance):
   - total_progeny (unique offspring count)
   - progeny_total_runs, progeny_wins, progeny_places
   - progeny_total_prize, progeny_win_rate, progeny_place_rate
   - progeny_avg_position

Data Sources:
-------------
- ra_mst_dams: List of all dams
- ra_rel_pedigree: Horse-to-dam relationships
- ra_runners: Race performance data
- ra_races: Race dates and metadata

Usage:
------
    # Process all dams
    python3 scripts/statistics_workers/calculate_dam_statistics.py

    # Process with limit (testing)
    python3 scripts/statistics_workers/calculate_dam_statistics.py --limit 100

    # Resume from checkpoint
    python3 scripts/statistics_workers/calculate_dam_statistics.py --resume

Author: Claude Code
Date: 2025-10-20
"""

import sys
import os
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('calculate_dam_statistics')

CHECKPOINT_FILE = 'logs/dam_statistics_checkpoint.json'
BATCH_SIZE = 100


class DamStatisticsCalculator:
    """Calculate dam statistics from database"""

    def __init__(self, db_client: SupabaseReferenceClient):
        self.db_client = db_client
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

    def get_dam_own_career_stats(self, dam_id: str) -> Dict:
        """
        Calculate dam's own racing career statistics

        Query ra_runners where horse_id = dam_id (the dam raced as a horse)
        """
        try:
            # Get all races where this dam raced
            runners = self.db_client.client.table('ra_runners')\
                .select('position, prize_won, race_id')\
                .eq('horse_id', dam_id)\
                .execute()

            if not runners.data:
                return {
                    'own_race_runs': 0,
                    'own_race_wins': 0,
                    'own_race_places': 0,
                    'own_total_prize': 0.0,
                    'own_best_position': None,
                    'own_avg_position': None,
                    'own_career_start': None,
                    'own_career_end': None
                }

            # Get race dates
            race_ids = [r['race_id'] for r in runners.data if r.get('race_id')]
            if race_ids:
                races = self.db_client.client.table('ra_races')\
                    .select('id, date')\
                    .in_('id', race_ids)\
                    .execute()
                race_dates = {r['id']: r['date'] for r in races.data}
            else:
                race_dates = {}

            # Calculate statistics
            total_runs = len(runners.data)
            wins = 0
            places = 0
            total_prize = 0.0
            positions = []
            dates = []

            for runner in runners.data:
                pos = runner.get('position')
                if pos:
                    try:
                        pos_int = int(pos)
                        positions.append(pos_int)
                        if pos_int == 1:
                            wins += 1
                        if pos_int <= 3:
                            places += 1
                    except (ValueError, TypeError):
                        pass

                prize = runner.get('prize_won')
                if prize:
                    total_prize += float(prize)

                race_id = runner.get('race_id')
                if race_id and race_id in race_dates:
                    dates.append(race_dates[race_id])

            best_position = min(positions) if positions else None
            avg_position = round(sum(positions) / len(positions), 2) if positions else None
            career_start = min(dates) if dates else None
            career_end = max(dates) if dates else None

            return {
                'own_race_runs': total_runs,
                'own_race_wins': wins,
                'own_race_places': places,
                'own_total_prize': round(total_prize, 2),
                'own_best_position': best_position,
                'own_avg_position': avg_position,
                'own_career_start': career_start,
                'own_career_end': career_end
            }

        except Exception as e:
            logger.error(f"Error calculating own career stats for dam {dam_id}: {e}")
            return {}

    def get_progeny_stats(self, dam_id: str) -> Dict:
        """
        Calculate progeny (offspring) performance statistics

        Query ra_rel_pedigree to find all horses from this dam,
        then aggregate their race performance from ra_runners
        """
        try:
            # Find all progeny (offspring)
            progeny = self.db_client.client.table('ra_rel_pedigree')\
                .select('horse_id')\
                .eq('dam_id', dam_id)\
                .execute()

            if not progeny.data:
                return {
                    'total_progeny': 0,
                    'progeny_total_runs': 0,
                    'progeny_wins': 0,
                    'progeny_places': 0,
                    'progeny_total_prize': 0.0,
                    'progeny_win_rate': None,
                    'progeny_place_rate': None,
                    'progeny_avg_position': None
                }

            progeny_ids = [p['horse_id'] for p in progeny.data]
            total_progeny = len(progeny_ids)

            # Get all races for these progeny
            runners = self.db_client.client.table('ra_runners')\
                .select('position, prize_won')\
                .in_('horse_id', progeny_ids)\
                .execute()

            if not runners.data:
                return {
                    'total_progeny': total_progeny,
                    'progeny_total_runs': 0,
                    'progeny_wins': 0,
                    'progeny_places': 0,
                    'progeny_total_prize': 0.0,
                    'progeny_win_rate': None,
                    'progeny_place_rate': None,
                    'progeny_avg_position': None
                }

            # Calculate progeny statistics
            total_runs = len(runners.data)
            wins = 0
            places = 0
            total_prize = 0.0
            positions = []

            for runner in runners.data:
                pos = runner.get('position')
                if pos:
                    try:
                        pos_int = int(pos)
                        positions.append(pos_int)
                        if pos_int == 1:
                            wins += 1
                        if pos_int <= 3:
                            places += 1
                    except (ValueError, TypeError):
                        pass

                prize = runner.get('prize_won')
                if prize:
                    total_prize += float(prize)

            win_rate = round((wins / total_runs) * 100, 2) if total_runs > 0 else None
            place_rate = round((places / total_runs) * 100, 2) if total_runs > 0 else None
            avg_position = round(sum(positions) / len(positions), 2) if positions else None

            return {
                'total_progeny': total_progeny,
                'progeny_total_runs': total_runs,
                'progeny_wins': wins,
                'progeny_places': places,
                'progeny_total_prize': round(total_prize, 2),
                'progeny_win_rate': win_rate,
                'progeny_place_rate': place_rate,
                'progeny_avg_position': avg_position
            }

        except Exception as e:
            logger.error(f"Error calculating progeny stats for dam {dam_id}: {e}")
            return {}

    def calculate_dam_statistics(self, dam_id: str, dam_name: str, ) -> Optional[Dict]:
        """Calculate all statistics for a single dam"""
        try:
            # Get own career stats
            own_stats = self.get_dam_own_career_stats(dam_id)

            # Get progeny stats
            progeny_stats = self.get_progeny_stats(dam_id)

            # Combine all stats
            stats = {
                'dam_id': dam_id,
                'dam_name': dam_name,
                
                **own_stats,
                **progeny_stats,
                'updated_at': datetime.utcnow().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics for {dam_name} ({dam_id}): {e}")
            return None

    def upsert_dam_stats(self, stats: Dict) -> bool:
        """Upsert statistics into ra_dam_stats table"""
        try:
            result = self.db_client.client.table('ra_dam_stats')\
                .upsert(stats, on_conflict='dam_id')\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting stats for dam {stats.get('dam_id')}: {e}")
            return False


def load_checkpoint() -> Dict:
    """Load checkpoint from file"""
    if os.path.exists(CHECKPOINT_FILE):
        try:
            with open(CHECKPOINT_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading checkpoint: {e}")
    return {'last_processed_index': 0, 'stats': {}}


def save_checkpoint(index: int, stats: Dict):
    """Save checkpoint to file"""
    try:
        os.makedirs(os.path.dirname(CHECKPOINT_FILE), exist_ok=True)
        with open(CHECKPOINT_FILE, 'w') as f:
            json.dump({
                'last_processed_index': index,
                'stats': stats,
                'timestamp': datetime.utcnow().isoformat()
            }, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving checkpoint: {e}")


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Calculate and populate dam statistics')
    parser.add_argument('--limit', type=int, help='Limit number of dams to process (for testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("DAM STATISTICS CALCULATOR")
    logger.info("=" * 80)

    # Initialize database client
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Initialize calculator
    calculator = DamStatisticsCalculator(db_client)

    # Load checkpoint if resuming
    checkpoint = {'last_processed_index': 0, 'stats': {}}
    if args.resume:
        checkpoint = load_checkpoint()
        logger.info(f"Resuming from index {checkpoint['last_processed_index']}")
        calculator.stats = checkpoint.get('stats', calculator.stats)

    # Fetch all dams
    logger.info("Fetching dams from database...")
    try:
        query = db_client.client.table('ra_mst_dams').select('id, name')

        if args.limit:
            query = query.limit(args.limit)
            logger.info(f"Limiting to {args.limit} dams for testing")

        response = query.execute()
        dams = response.data

        if not dams:
            logger.warning("No dams found in database")
            return

        logger.info(f"Found {len(dams)} dams to process")

    except Exception as e:
        logger.error(f"Error fetching dams: {e}")
        return

    # Process dams in batches
    start_time = datetime.utcnow()
    start_index = checkpoint['last_processed_index']

    for i in range(start_index, len(dams)):
        dam = dams[i]
        dam_id = dam['id']
        dam_name = dam.get('name', 'Unknown')
        

        logger.info(f"[{i+1}/{len(dams)}] Processing {dam_name} ({dam_id})...")

        # Calculate statistics
        stats = calculator.calculate_dam_statistics(dam_id, dam_name)

        if stats:
            # Upsert to database
            if calculator.upsert_dam_stats(stats):
                calculator.stats['updated'] += 1
            else:
                calculator.stats['errors'] += 1
            calculator.stats['processed'] += 1
        else:
            calculator.stats['errors'] += 1

        # Save checkpoint every batch
        if (i + 1) % BATCH_SIZE == 0:
            save_checkpoint(i + 1, calculator.stats)
            logger.info(f"Checkpoint saved at index {i + 1}")
            logger.info(f"Progress: {calculator.stats['updated']} updated, {calculator.stats['errors']} errors")

    # Final summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("DAM STATISTICS CALCULATOR COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total dams: {len(dams)}")
    logger.info(f"Processed: {calculator.stats['processed']}")
    logger.info(f"Updated: {calculator.stats['updated']}")
    logger.info(f"Errors: {calculator.stats['errors']}")
    logger.info(f"Duration: {duration:.2f}s ({duration/60:.2f}m)")
    logger.info("=" * 80)

    # Clean up checkpoint on successful completion
    if calculator.stats['errors'] == 0 and os.path.exists(CHECKPOINT_FILE):
        os.remove(CHECKPOINT_FILE)
        logger.info("Checkpoint file removed (processing complete)")


if __name__ == '__main__':
    main()
