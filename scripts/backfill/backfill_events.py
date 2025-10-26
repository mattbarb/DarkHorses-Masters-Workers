"""
Backfill Historical Event Data (Races & Results) from 2015 to Present

This script performs a comprehensive backfill of all racing event data:
- Racecards (pre-race data: races, runners)
- Results (post-race data: positions, times, prizes)
- Entity extraction (automatic population of horses, jockeys, trainers, owners)
- Pedigree data (automatic capture for new horses)

Features:
- Resume capability (checkpoint/restart if interrupted)
- Progress tracking (monthly chunks with estimates)
- Rate limit handling (2 requests/second)
- Error logging and retry logic
- Smart date range processing

Database Tables Populated:
- ra_races (race metadata)
- ra_mst_runners (runner records with positions)
- ra_mst_horses (via entity extraction)
- ra_mst_jockeys (via entity extraction)
- ra_mst_trainers (via entity extraction)
- ra_mst_owners (via entity extraction)
- ra_mst_sires, ra_mst_dams, ra_mst_damsires (via pedigree extraction)
- ra_horse_pedigree (complete lineage)

Usage:
    # Full backfill from 2015
    python3 scripts/backfill_events.py --start-date 2015-01-01

    # Specific date range
    python3 scripts/backfill_events.py --start-date 2020-01-01 --end-date 2020-12-31

    # Resume from checkpoint
    python3 scripts/backfill_events.py --resume

    # Check status (dry run)
    python3 scripts/backfill_events.py --check-status --start-date 2015-01-01

    # Racecards only (no results)
    python3 scripts/backfill_events.py --start-date 2015-01-01 --no-results

    # Results only (no racecards)
    python3 scripts/backfill_events.py --start-date 2015-01-01 --no-racecards
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional
from utils.logger import get_logger
from fetchers.events_fetcher import EventsFetcher

logger = get_logger('backfill_events')


class EventsBackfillManager:
    """Manager for events backfill with checkpoint/resume capability"""

    def __init__(self, checkpoint_file: str = None):
        """Initialize backfill manager"""
        self.fetcher = EventsFetcher()

        # Checkpoint file
        if checkpoint_file:
            self.checkpoint_file = Path(checkpoint_file)
        else:
            self.checkpoint_file = Path(__file__).parent.parent / 'logs' / 'backfill_events_checkpoint.json'

        # Error log file
        self.error_log_file = Path(__file__).parent.parent / 'logs' / 'backfill_events_errors.json'

    def load_checkpoint(self) -> Optional[Dict]:
        """Load checkpoint data if exists"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    checkpoint = json.load(f)
                logger.info(f"Loaded checkpoint: {checkpoint.get('chunks_processed', 0)} chunks processed")
                return checkpoint
            except Exception as e:
                logger.error(f"Error loading checkpoint: {e}")
        return None

    def save_checkpoint(self, stats: Dict):
        """Save checkpoint for resume capability"""
        checkpoint = {
            'timestamp': datetime.utcnow().isoformat(),
            'stats': stats
        }
        try:
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint, f, indent=2)
            logger.debug(f"Checkpoint saved: {stats.get('chunks_processed', 0)} chunks processed")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")

    def log_error(self, chunk_info: str, error: str):
        """Log error to error file"""
        error_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'chunk': chunk_info,
            'error': str(error)
        }

        try:
            errors = []
            if self.error_log_file.exists():
                with open(self.error_log_file, 'r') as f:
                    errors = json.load(f)

            errors.append(error_entry)

            with open(self.error_log_file, 'w') as f:
                json.dump(errors, f, indent=2)
        except Exception as e:
            logger.error(f"Error logging to error file: {e}")

    def check_status(self, start_date: str, end_date: str) -> Dict:
        """
        Check backfill status without fetching data

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            Status dictionary
        """
        logger.info("=" * 80)
        logger.info("CHECKING BACKFILL STATUS")
        logger.info("=" * 80)

        # Parse dates
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        total_days = (end_dt - start_dt).days + 1

        # Calculate chunks
        chunks = self.fetcher._generate_monthly_chunks(start_dt, end_dt)

        # Estimate API calls and time
        # Assumption: ~50 races/day average, 2 API calls (racecards + results)
        estimated_api_calls = total_days * 2  # 1 for racecards, 1 for results per day
        estimated_time_hours = (estimated_api_calls * 0.5) / 3600  # 0.5s per call at 2 req/sec

        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Total days: {total_days}")
        logger.info(f"Monthly chunks: {len(chunks)}")
        logger.info(f"Estimated API calls: {estimated_api_calls:,}")
        logger.info(f"Estimated time (at 2 req/sec): {estimated_time_hours:.1f} hours")
        logger.info("")

        # Check for existing checkpoint
        checkpoint = self.load_checkpoint()
        if checkpoint:
            logger.info("Checkpoint found:")
            logger.info(f"  Chunks processed: {checkpoint['stats'].get('chunks_processed', 0)}")
            logger.info(f"  Total races: {checkpoint['stats'].get('total_races', 0)}")
            logger.info(f"  Total runners: {checkpoint['stats'].get('total_runners', 0)}")
            logger.info(f"  Last updated: {checkpoint.get('timestamp')}")
        else:
            logger.info("No checkpoint found (fresh start)")

        logger.info("=" * 80)

        return {
            'total_days': total_days,
            'total_chunks': len(chunks),
            'estimated_api_calls': estimated_api_calls,
            'estimated_time_hours': estimated_time_hours,
            'checkpoint': checkpoint
        }

    def run_backfill(
        self,
        start_date: str,
        end_date: Optional[str] = None,
        region_codes: list = None,
        fetch_racecards: bool = True,
        fetch_results: bool = True,
        resume: bool = False
    ) -> Dict:
        """
        Run the backfill operation

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD). If None, defaults to today
            region_codes: Region filter (default: ['gb', 'ire'])
            fetch_racecards: Whether to fetch racecards
            fetch_results: Whether to fetch results
            resume: Resume from checkpoint if available

        Returns:
            Statistics dictionary
        """
        if region_codes is None:
            region_codes = ['gb', 'ire']

        if end_date is None:
            end_date = datetime.utcnow().strftime('%Y-%m-%d')

        logger.info("=" * 80)
        logger.info("EVENTS BACKFILL - STARTING")
        logger.info("=" * 80)
        logger.info(f"Date range: {start_date} to {end_date}")
        logger.info(f"Regions: {region_codes}")
        logger.info(f"Fetch racecards: {fetch_racecards}")
        logger.info(f"Fetch results: {fetch_results}")
        logger.info(f"Resume mode: {resume}")

        start_time = datetime.utcnow()

        # Check for checkpoint if resume mode
        resume_from_date = None
        if resume:
            checkpoint = self.load_checkpoint()
            if checkpoint and checkpoint.get('stats', {}).get('chunks'):
                # Get last processed chunk
                chunks = checkpoint['stats']['chunks']
                if chunks:
                    last_chunk = chunks[-1]
                    resume_from_date = last_chunk.get('end_date')
                    logger.info(f"Resuming from: {resume_from_date}")

                    # Adjust start date
                    if resume_from_date:
                        resume_dt = datetime.strptime(resume_from_date, '%Y-%m-%d').date() + timedelta(days=1)
                        start_date = resume_dt.strftime('%Y-%m-%d')
                        logger.info(f"Adjusted start date: {start_date}")

        # Run backfill
        result = self.fetcher.backfill(
            start_date=start_date,
            end_date=end_date,
            region_codes=region_codes,
            fetch_racecards=fetch_racecards,
            fetch_results=fetch_results
        )

        # Save checkpoint after each chunk (already done in fetcher, but save final state)
        self.save_checkpoint(result)

        # Calculate duration
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("EVENTS BACKFILL - COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Success: {result.get('success')}")
        logger.info(f"Duration: {duration / 3600:.2f} hours ({duration / 60:.1f} minutes)")
        logger.info(f"Chunks processed: {result.get('chunks_processed')}/{result.get('total_chunks')}")
        logger.info(f"Total races: {result.get('total_races', 0):,}")
        logger.info(f"Total runners: {result.get('total_runners', 0):,}")
        logger.info("=" * 80)

        return result


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Backfill historical event data (races & results)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--start-date',
        required=False,
        help='Start date (YYYY-MM-DD). Required unless --resume is used'
    )
    parser.add_argument(
        '--end-date',
        help='End date (YYYY-MM-DD). Defaults to today'
    )
    parser.add_argument(
        '--region-codes',
        nargs='+',
        default=['gb', 'ire'],
        help='Region codes to fetch (default: gb ire)'
    )
    parser.add_argument(
        '--no-racecards',
        action='store_true',
        help='Skip fetching racecards (results only)'
    )
    parser.add_argument(
        '--no-results',
        action='store_true',
        help='Skip fetching results (racecards only)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--check-status',
        action='store_true',
        help='Check backfill status without running (dry run)'
    )
    parser.add_argument(
        '--checkpoint-file',
        help='Custom checkpoint file path'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.resume and not args.start_date and not args.check_status:
        parser.error('--start-date is required unless --resume or --check-status is used')

    # Initialize manager
    manager = EventsBackfillManager(checkpoint_file=args.checkpoint_file)

    # Check status mode
    if args.check_status:
        if not args.start_date:
            parser.error('--start-date is required for --check-status')
        end_date = args.end_date or datetime.utcnow().strftime('%Y-%m-%d')
        manager.check_status(args.start_date, end_date)
        return 0

    # Run backfill
    try:
        result = manager.run_backfill(
            start_date=args.start_date or '2015-01-01',
            end_date=args.end_date,
            region_codes=args.region_codes,
            fetch_racecards=not args.no_racecards,
            fetch_results=not args.no_results,
            resume=args.resume
        )
        return 0 if result.get('success') else 1
    except KeyboardInterrupt:
        logger.warning("\n\nBackfill interrupted by user (Ctrl+C)")
        logger.info("Progress has been saved to checkpoint. Use --resume to continue.")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.error(f"Backfill failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
