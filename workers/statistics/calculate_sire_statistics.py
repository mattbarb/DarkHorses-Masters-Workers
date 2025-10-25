#!/usr/bin/env python3
"""
Calculate Sire Statistics from Database
=========================================

Populates ra_sire_stats table with comprehensive statistics calculated from
historical race data in ra_runners + ra_races + ra_rel_pedigree tables.

Statistics Calculated:
----------------------
1. OWN RACING CAREER (sire's performance as a racehorse):
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
- ra_mst_sires: List of all sires
- ra_rel_pedigree: Horse-to-sire relationships
- ra_runners: Race performance data
- ra_races: Race dates and metadata

Usage:
------
    # Process all sires
    python3 scripts/statistics_workers/calculate_sire_statistics.py

    # Process with limit (testing)
    python3 scripts/statistics_workers/calculate_sire_statistics.py --limit 100

    # Resume from checkpoint
    python3 scripts/statistics_workers/calculate_sire_statistics.py --resume

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

logger = get_logger('calculate_sire_statistics')

CHECKPOINT_FILE = 'logs/sire_statistics_checkpoint.json'
BATCH_SIZE = 100


class SireStatisticsCalculator:
    """Calculate sire statistics from database"""

    def __init__(self, db_client: SupabaseReferenceClient):
        self.db_client = db_client
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }

    def get_sire_own_career_stats(self, sire_id: str) -> Dict:
        """
        Calculate sire's own racing career statistics

        Query ra_runners where horse_id = sire_id (the sire raced as a horse)
        """
        try:
            # Get all races where this sire raced
            runners = self.db_client.client.table('ra_runners')\
                .select('position, prize_won, race_id')\
                .eq('horse_id', sire_id)\
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
            logger.error(f"Error calculating own career stats for sire {sire_id}: {e}")
            return {}

    def get_progeny_stats(self, sire_id: str) -> Dict:
        """
        Calculate progeny (offspring) performance statistics

        Query ra_rel_pedigree to find all horses sired by this sire,
        then aggregate their race performance from ra_runners
        """
        try:
            # Find all progeny (offspring)
            progeny = self.db_client.client.table('ra_rel_pedigree')\
                .select('horse_id')\
                .eq('sire_id', sire_id)\
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
            logger.error(f"Error calculating progeny stats for sire {sire_id}: {e}")
            return {}

    def calculate_sire_statistics(self, sire_id: str, sire_name: str, ) -> Optional[Dict]:
        """Calculate all statistics for a single sire"""
        try:
            # Get own career stats
            own_stats = self.get_sire_own_career_stats(sire_id)

            # Get progeny stats
            progeny_stats = self.get_progeny_stats(sire_id)

            # Combine all stats
            stats = {
                'sire_id': sire_id,
                'sire_name': sire_name,
                
                **own_stats,
                **progeny_stats,
                'updated_at': datetime.utcnow().isoformat()
            }

            return stats

        except Exception as e:
            logger.error(f"Error calculating statistics for {sire_name} ({sire_id}): {e}")
            return None

    def upsert_sire_stats(self, stats: Dict) -> bool:
        """Upsert statistics into ra_sire_stats table"""
        try:
            result = self.db_client.client.table('ra_sire_stats')\
                .upsert(stats, on_conflict='sire_id')\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error upserting stats for sire {stats.get('sire_id')}: {e}")
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
    parser = argparse.ArgumentParser(description='Calculate and populate sire statistics')
    parser.add_argument('--limit', type=int, help='Limit number of sires to process (for testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("SIRE STATISTICS CALCULATOR")
    logger.info("=" * 80)

    # Initialize database client
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Initialize calculator
    calculator = SireStatisticsCalculator(db_client)

    # Load checkpoint if resuming
    checkpoint = {'last_processed_index': 0, 'stats': {}}
    if args.resume:
        checkpoint = load_checkpoint()
        logger.info(f"Resuming from index {checkpoint['last_processed_index']}")
        calculator.stats = checkpoint.get('stats', calculator.stats)

    # Fetch all sires
    logger.info("Fetching sires from database...")
    try:
        query = db_client.client.table('ra_mst_sires').select('id, name')

        if args.limit:
            query = query.limit(args.limit)
            logger.info(f"Limiting to {args.limit} sires for testing")

        response = query.execute()
        sires = response.data

        if not sires:
            logger.warning("No sires found in database")
            return

        logger.info(f"Found {len(sires)} sires to process")

    except Exception as e:
        logger.error(f"Error fetching sires: {e}")
        return

    # Process sires in batches
    start_time = datetime.utcnow()
    start_index = checkpoint['last_processed_index']

    for i in range(start_index, len(sires)):
        sire = sires[i]
        sire_id = sire['id']
        sire_name = sire.get('name', 'Unknown')
        

        logger.info(f"[{i+1}/{len(sires)}] Processing {sire_name} ({sire_id})...")

        # Calculate statistics
        stats = calculator.calculate_sire_statistics(sire_id, sire_name)

        if stats:
            # Upsert to database
            if calculator.upsert_sire_stats(stats):
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
    logger.info("SIRE STATISTICS CALCULATOR COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total sires: {len(sires)}")
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
