#!/usr/bin/env python3
"""
Backfill ra_races from 2015 to present using RacesFetcher

Fetches racecards from Racing API and populates:
- ra_races (race metadata with distance_m calculated)
- ra_runners (race entries)
- ra_mst_* tables (via automatic entity extraction)

Usage:
    # Full backfill from 2015
    python3 scripts/backfill/backfill_races_2015.py

    # Specific date range
    python3 scripts/backfill/backfill_races_2015.py --start-date 2020-01-01 --end-date 2020-12-31

    # Resume from checkpoint
    python3 scripts/backfill/backfill_races_2015.py --resume
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import argparse
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from utils.logger import get_logger
from fetchers.races_fetcher import RacesFetcher

logger = get_logger('backfill_races_2015')


class RacesBackfillManager:
    """Manager for races backfill with checkpoint/resume capability"""

    def __init__(self):
        """Initialize backfill manager"""
        self.fetcher = RacesFetcher()
        self.checkpoint_file = Path(__file__).parent.parent.parent / 'logs' / 'backfill_races_checkpoint.json'
        self.error_log_file = Path(__file__).parent.parent.parent / 'logs' / 'backfill_races_errors.json'

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint data if exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: processed up to {checkpoint.get('last_date')}")
                return checkpoint
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return None

    def save_checkpoint(self, last_date: str, stats: Dict):
        """Save checkpoint for resume capability"""
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'last_date': last_date,
            'stats': stats
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {last_date}")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def log_error(self, date: str, error: str):
        """Log errors to separate file"""
        errors = []
        if self.error_log_file.exists():
            try:
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)
            except:
                pass

        errors.append({
            'date': date,
            'timestamp': datetime.utcnow().isoformat(),
            'error': str(error)
        })

        try:
            with open(self.error_log_file, 'w') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving error log: {e}")

    def backfill(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        resume: bool = False,
        chunk_days: int = 30
    ):
        """
        Backfill races from start_date to end_date in chunks

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), defaults to today
            resume: Resume from checkpoint if exists
            chunk_days: Days to process per chunk (default: 30)
        """
        # Handle resume
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint:
                start_date = checkpoint.get('last_date')
                logger.info(f"Resuming from {start_date}")

        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if end_date:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        else:
            end_dt = datetime.utcnow()

        logger.info("=" * 80)
        logger.info("RACES BACKFILL FROM 2015")
        logger.info(f"Date range: {start_dt.date()} to {end_dt.date()}")
        logger.info(f"Chunk size: {chunk_days} days")
        logger.info("=" * 80)

        # Calculate total chunks
        total_days = (end_dt - start_dt).days
        total_chunks = (total_days + chunk_days - 1) // chunk_days

        logger.info(f"Total days: {total_days:,}")
        logger.info(f"Total chunks: {total_chunks:,}")
        logger.info("")

        # Track overall stats
        overall_stats = {
            'chunks_processed': 0,
            'total_races': 0,
            'total_runners': 0,
            'total_horses': 0,
            'errors': 0,
            'start_time': datetime.utcnow().isoformat()
        }

        # Process in chunks
        current_dt = start_dt
        chunk_num = 0

        while current_dt < end_dt:
            chunk_num += 1
            chunk_start = current_dt
            chunk_end = min(current_dt + timedelta(days=chunk_days), end_dt)

            logger.info("-" * 80)
            logger.info(f"CHUNK {chunk_num}/{total_chunks}")
            logger.info(f"Date range: {chunk_start.date()} to {chunk_end.date()}")
            logger.info("-" * 80)

            try:
                # Fetch races for this chunk
                result = self.fetcher.fetch_and_store(
                    start_date=chunk_start.strftime('%Y-%m-%d'),
                    end_date=chunk_end.strftime('%Y-%m-%d'),
                    region_codes=['gb', 'ire']
                )

                # Extract stats
                races_fetched = result.get('races_fetched', 0)
                runners_fetched = result.get('runners_fetched', 0)
                horses_enriched = result.get('db_stats', {}).get('entities', {}).get('horses', {}).get('inserted', 0)

                logger.info(f"✓ Races fetched: {races_fetched:,}")
                logger.info(f"✓ Runners fetched: {runners_fetched:,}")
                logger.info(f"✓ Horses enriched: {horses_enriched:,}")

                # Update overall stats
                overall_stats['chunks_processed'] += 1
                overall_stats['total_races'] += races_fetched
                overall_stats['total_runners'] += runners_fetched
                overall_stats['total_horses'] += horses_enriched

                # Save checkpoint
                self.save_checkpoint(chunk_end.strftime('%Y-%m-%d'), overall_stats)

                # Rate limiting pause between chunks
                time.sleep(2)

            except Exception as e:
                logger.error(f"✗ Chunk failed: {e}")
                self.log_error(chunk_start.strftime('%Y-%m-%d'), str(e))
                overall_stats['errors'] += 1
                # Continue to next chunk despite error
                time.sleep(5)

            # Move to next chunk
            current_dt = chunk_end

        # Final summary
        overall_stats['end_time'] = datetime.utcnow().isoformat()
        duration = datetime.fromisoformat(overall_stats['end_time']) - datetime.fromisoformat(overall_stats['start_time'])

        logger.info("")
        logger.info("=" * 80)
        logger.info("BACKFILL COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Chunks processed: {overall_stats['chunks_processed']:,}/{total_chunks}")
        logger.info(f"Total races: {overall_stats['total_races']:,}")
        logger.info(f"Total runners: {overall_stats['total_runners']:,}")
        logger.info(f"Total horses enriched: {overall_stats['total_horses']:,}")
        logger.info(f"Errors: {overall_stats['errors']:,}")
        logger.info(f"Duration: {duration}")
        logger.info("=" * 80)


def main():
    parser = argparse.ArgumentParser(description='Backfill ra_races from 2015 to present')
    parser.add_argument('--start-date', default='2015-01-01', help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', help='End date (YYYY-MM-DD), defaults to today')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    parser.add_argument('--chunk-days', type=int, default=30, help='Days per chunk (default: 30)')

    args = parser.parse_args()

    manager = RacesBackfillManager()
    manager.backfill(
        start_date=args.start_date,
        end_date=args.end_date,
        resume=args.resume,
        chunk_days=args.chunk_days
    )


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\nBackfill interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        sys.exit(1)
