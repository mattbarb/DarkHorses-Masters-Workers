"""
Complete Backfill Orchestrator

This script runs a complete backfill of ALL data in the correct order:
1. Master reference data (bookmakers, courses, regions)
2. Event data (racecards and results from 2015 to present)
3. Entity extraction happens automatically during event backfill

Usage:
    # Full backfill from 2015
    python3 scripts/backfill_all.py --start-date 2015-01-01

    # Resume from checkpoint (events only, masters is fast)
    python3 scripts/backfill_all.py --start-date 2015-01-01 --resume

    # Skip masters (if already complete)
    python3 scripts/backfill_all.py --start-date 2015-01-01 --skip-masters

    # Check what would be done
    python3 scripts/backfill_all.py --start-date 2015-01-01 --dry-run
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import argparse
import subprocess
from datetime import datetime
from utils.logger import get_logger

logger = get_logger('backfill_all')


def run_script(script_name: str, args: list) -> int:
    """
    Run a Python script and return exit code

    Args:
        script_name: Name of script to run
        args: List of arguments

    Returns:
        Exit code
    """
    script_path = Path(__file__).parent / script_name
    cmd = ['python3', str(script_path)] + args

    logger.info(f"Running: {' '.join(cmd)}")

    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return 1


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Complete backfill orchestrator (masters + events)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--start-date',
        required=True,
        help='Start date for events backfill (YYYY-MM-DD)'
    )
    parser.add_argument(
        '--end-date',
        help='End date for events backfill (YYYY-MM-DD). Defaults to today'
    )
    parser.add_argument(
        '--region-codes',
        nargs='+',
        default=['gb', 'ire'],
        help='Region codes to fetch (default: gb ire)'
    )
    parser.add_argument(
        '--skip-masters',
        action='store_true',
        help='Skip master data backfill (if already complete)'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume events backfill from checkpoint'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )

    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("COMPLETE BACKFILL ORCHESTRATOR")
    logger.info("=" * 80)
    logger.info(f"Started at: {datetime.utcnow().isoformat()}")
    logger.info(f"Start date: {args.start_date}")
    logger.info(f"End date: {args.end_date or 'today'}")
    logger.info(f"Region codes: {args.region_codes}")
    logger.info(f"Skip masters: {args.skip_masters}")
    logger.info(f"Resume: {args.resume}")
    logger.info(f"Dry run: {args.dry_run}")

    if args.dry_run:
        logger.info("\n" + "=" * 80)
        logger.info("DRY RUN MODE - SHOWING WHAT WOULD BE EXECUTED")
        logger.info("=" * 80)

        if not args.skip_masters:
            logger.info("\n1. Master Data Backfill:")
            logger.info("   python3 scripts/backfill_masters.py")

        logger.info("\n2. Events Data Backfill:")
        events_cmd = f"   python3 scripts/backfill_events.py --start-date {args.start_date}"
        if args.end_date:
            events_cmd += f" --end-date {args.end_date}"
        if args.resume:
            events_cmd += " --resume"
        logger.info(events_cmd)

        logger.info("\n" + "=" * 80)
        logger.info("Add --check-status to events command to see estimates")
        logger.info("=" * 80)
        return 0

    # Track overall status
    overall_success = True
    start_time = datetime.utcnow()

    # Step 1: Master data backfill
    if not args.skip_masters:
        logger.info("\n" + "=" * 80)
        logger.info("STEP 1: MASTER DATA BACKFILL")
        logger.info("=" * 80)

        masters_args = ['--region-codes'] + args.region_codes
        exit_code = run_script('backfill_masters.py', masters_args)

        if exit_code != 0:
            logger.error("Master data backfill failed!")
            overall_success = False
            # Continue anyway, as it's non-critical
        else:
            logger.info("Master data backfill completed successfully")
    else:
        logger.info("Skipping master data backfill (--skip-masters)")

    # Step 2: Events data backfill
    logger.info("\n" + "=" * 80)
    logger.info("STEP 2: EVENTS DATA BACKFILL")
    logger.info("=" * 80)

    events_args = ['--start-date', args.start_date]
    if args.end_date:
        events_args.extend(['--end-date', args.end_date])
    if args.resume:
        events_args.append('--resume')
    events_args.extend(['--region-codes'] + args.region_codes)

    exit_code = run_script('backfill_events.py', events_args)

    if exit_code != 0:
        logger.error("Events data backfill failed!")
        overall_success = False
    else:
        logger.info("Events data backfill completed successfully")

    # Final summary
    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    logger.info("\n" + "=" * 80)
    logger.info("COMPLETE BACKFILL - FINISHED")
    logger.info("=" * 80)
    logger.info(f"Overall success: {overall_success}")
    logger.info(f"Total duration: {duration / 3600:.2f} hours ({duration / 60:.1f} minutes)")
    logger.info(f"Completed at: {end_time.isoformat()}")
    logger.info("=" * 80)

    logger.info("\nNext steps:")
    logger.info("1. Verify data in Supabase database")
    logger.info("2. Check logs/backfill_events_checkpoint.json for progress")
    logger.info("3. Review logs/backfill_events_errors.json for any errors")
    logger.info("4. If interrupted, use --resume to continue")

    return 0 if overall_success else 1


if __name__ == '__main__':
    sys.exit(main())
