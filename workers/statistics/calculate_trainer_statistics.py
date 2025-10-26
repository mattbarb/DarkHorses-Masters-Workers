#!/usr/bin/env python3
"""
Calculate Trainer Statistics from Database
===========================================

Populates ra_mst_trainers table with comprehensive statistics calculated from
historical race data in ra_mst_runners + ra_races tables.

Statistics Calculated:
----------------------
1. LIFETIME STATISTICS:
   - total_runners, total_wins, total_places (top 3), total_seconds, total_thirds
   - win_rate, place_rate

2. RECENT FORM (14-day and 30-day windows):
   - recent_14d_runs, recent_14d_wins, recent_14d_win_rate
   - recent_30d_runs, recent_30d_wins, recent_30d_win_rate

3. LAST ACTIVITY DATES:
   - last_runner_date, last_win_date
   - days_since_last_runner, days_since_last_win

4. METADATA:
   - stats_updated_at

Data Sources:
-------------
- ra_mst_trainers: List of all trainers
- ra_mst_runners: Race performance data (JOIN on trainer_id)
- ra_races: Race dates

Usage:
------
    # Process all trainers
    python3 scripts/statistics_workers/calculate_trainer_statistics.py

    # Process with limit (testing)
    python3 scripts/statistics_workers/calculate_trainer_statistics.py --limit 100

    # Resume from checkpoint
    python3 scripts/statistics_workers/calculate_trainer_statistics.py --resume

Author: Claude Code
Date: 2025-10-20
"""

import sys
import os
import argparse
import json
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('calculate_trainer_statistics')

CHECKPOINT_FILE = 'logs/trainer_statistics_checkpoint.json'
BATCH_SIZE = 100


class TrainerStatisticsCalculator:
    """Calculate trainer statistics from database"""

    def __init__(self, db_client: SupabaseReferenceClient):
        self.db_client = db_client
        self.stats = {
            'processed': 0,
            'updated': 0,
            'errors': 0,
            'skipped': 0
        }
        self.today = date.today()
        self.cutoff_14d = self.today - timedelta(days=14)
        self.cutoff_30d = self.today - timedelta(days=30)

    def calculate_trainer_statistics(self, trainer_id: str) -> Optional[Dict]:
        """Calculate all statistics for a single trainer"""
        try:
            # Get all runners for this trainer
            runners = self.db_client.client.table('ra_mst_runners')\
                .select('position, race_id')\
                .eq('trainer_id', trainer_id)\
                .execute()

            if not runners.data:
                return {
                    'id': trainer_id,
                    'total_runners': 0,
                    'total_wins': 0,
                    'total_places': 0,
                    'total_seconds': 0,
                    'total_thirds': 0,
                    'win_rate': None,
                    'place_rate': None,
                    'last_runner_date': None,
                    'last_win_date': None,
                    'days_since_last_runner': None,
                    'days_since_last_win': None,
                    'recent_14d_runs': 0,
                    'recent_14d_wins': 0,
                    'recent_14d_win_rate': None,
                    'recent_30d_runs': 0,
                    'recent_30d_wins': 0,
                    'recent_30d_win_rate': None,
                    'stats_updated_at': datetime.utcnow().isoformat()
                }

            # Get race dates
            race_ids = list(set([r['race_id'] for r in runners.data if r.get('race_id')]))
            if race_ids:
                races = self.db_client.client.table('ra_mst_races')\
                    .select('id, date')\
                    .in_('id', race_ids)\
                    .execute()
                race_dates = {r['id']: r['date'] for r in races.data}
            else:
                race_dates = {}

            # Initialize counters
            total_runners = len(runners.data)
            total_wins = 0
            total_places = 0
            total_seconds = 0
            total_thirds = 0
            last_runner_date = None
            last_win_date = None
            recent_14d_runs = 0
            recent_14d_wins = 0
            recent_30d_runs = 0
            recent_30d_wins = 0

            # Process each runner
            for runner in runners.data:
                pos = runner.get('position')
                race_id = runner.get('race_id')
                race_date_str = race_dates.get(race_id)

                # Convert race date
                if race_date_str:
                    try:
                        if isinstance(race_date_str, str):
                            race_date = datetime.strptime(race_date_str, '%Y-%m-%d').date()
                        else:
                            race_date = race_date_str

                        # Track last runner date
                        if not last_runner_date or race_date > last_runner_date:
                            last_runner_date = race_date

                        # Count recent form
                        if race_date >= self.cutoff_14d:
                            recent_14d_runs += 1
                        if race_date >= self.cutoff_30d:
                            recent_30d_runs += 1
                    except (ValueError, TypeError):
                        race_date = None
                else:
                    race_date = None

                # Process position
                if pos:
                    try:
                        pos_int = int(pos)

                        if pos_int == 1:
                            total_wins += 1
                            if race_date:
                                if not last_win_date or race_date > last_win_date:
                                    last_win_date = race_date
                                if race_date >= self.cutoff_14d:
                                    recent_14d_wins += 1
                                if race_date >= self.cutoff_30d:
                                    recent_30d_wins += 1

                        if pos_int <= 3:
                            total_places += 1

                        if pos_int == 2:
                            total_seconds += 1

                        if pos_int == 3:
                            total_thirds += 1

                    except (ValueError, TypeError):
                        pass

            # Calculate rates
            win_rate = round((total_wins / total_runners) * 100, 2) if total_runners > 0 else None
            place_rate = round((total_places / total_runners) * 100, 2) if total_runners > 0 else None
            recent_14d_win_rate = round((recent_14d_wins / recent_14d_runs) * 100, 2) if recent_14d_runs > 0 else None
            recent_30d_win_rate = round((recent_30d_wins / recent_30d_runs) * 100, 2) if recent_30d_runs > 0 else None

            # Calculate days since
            days_since_last_runner = (self.today - last_runner_date).days if last_runner_date else None
            days_since_last_win = (self.today - last_win_date).days if last_win_date else None

            return {
                'id': trainer_id,
                'total_runners': total_runners,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': total_seconds,
                'total_thirds': total_thirds,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'last_runner_date': last_runner_date.isoformat() if last_runner_date else None,
                'last_win_date': last_win_date.isoformat() if last_win_date else None,
                'days_since_last_runner': days_since_last_runner,
                'days_since_last_win': days_since_last_win,
                'recent_14d_runs': recent_14d_runs,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_runs': recent_30d_runs,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'stats_updated_at': datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Error calculating statistics for trainer {trainer_id}: {e}")
            return None

    def update_trainer_stats(self, stats: Dict) -> bool:
        """Update statistics in ra_mst_trainers table"""
        try:
            trainer_id = stats.pop('id')
            result = self.db_client.client.table('ra_mst_trainers')\
                .update(stats)\
                .eq('id', trainer_id)\
                .execute()
            return True
        except Exception as e:
            logger.error(f"Error updating stats for trainer {stats.get('id', 'unknown')}: {e}")
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
    parser = argparse.ArgumentParser(description='Calculate and populate trainer statistics')
    parser.add_argument('--limit', type=int, help='Limit number of trainers to process (for testing)')
    parser.add_argument('--resume', action='store_true', help='Resume from last checkpoint')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("TRAINER STATISTICS CALCULATOR")
    logger.info("=" * 80)

    # Initialize database client
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key
    )

    # Initialize calculator
    calculator = TrainerStatisticsCalculator(db_client)

    # Load checkpoint if resuming
    checkpoint = {'last_processed_index': 0, 'stats': {}}
    if args.resume:
        checkpoint = load_checkpoint()
        logger.info(f"Resuming from index {checkpoint['last_processed_index']}")
        calculator.stats = checkpoint.get('stats', calculator.stats)

    # Fetch all trainers
    logger.info("Fetching trainers from database...")
    try:
        query = db_client.client.table('ra_mst_trainers').select('id')

        if args.limit:
            query = query.limit(args.limit)
            logger.info(f"Limiting to {args.limit} trainers for testing")

        response = query.execute()
        trainers = response.data

        if not trainers:
            logger.warning("No trainers found in database")
            return

        logger.info(f"Found {len(trainers)} trainers to process")

    except Exception as e:
        logger.error(f"Error fetching trainers: {e}")
        return

    # Process trainers in batches
    start_time = datetime.utcnow()
    start_index = checkpoint['last_processed_index']

    for i in range(start_index, len(trainers)):
        trainer = trainers[i]
        trainer_id = trainer['id']

        logger.info(f"[{i+1}/{len(trainers)}] Processing trainer {trainer_id}...")

        # Calculate statistics
        stats = calculator.calculate_trainer_statistics(trainer_id)

        if stats:
            # Update database
            if calculator.update_trainer_stats(stats):
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
    logger.info("TRAINER STATISTICS CALCULATOR COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total trainers: {len(trainers)}")
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
