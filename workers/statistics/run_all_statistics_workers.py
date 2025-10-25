"""
Run All Statistics Workers

Executes all three statistics workers (jockeys, trainers, owners) in sequence.
This is the recommended way to update all entity statistics.

Usage:
    python3 scripts/statistics_workers/run_all_statistics_workers.py
    python3 scripts/statistics_workers/run_all_statistics_workers.py --limit 10
"""

import sys
import os
import argparse
from datetime import datetime
import logging

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import workers
from scripts.statistics_workers import jockeys_statistics_worker
from scripts.statistics_workers import trainers_statistics_worker
from scripts.statistics_workers import owners_statistics_worker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(description='Run all statistics workers')
    parser.add_argument('--limit', type=int, help='Limit number of entities per worker (for testing)')
    args = parser.parse_args()

    logger.info("=" * 80)
    logger.info("STATISTICS WORKERS - RUNNING ALL")
    logger.info("=" * 80)

    if args.limit:
        logger.info(f"Running in TEST MODE with limit={args.limit} entities per worker")
    else:
        logger.info("Running in PRODUCTION MODE (processing all entities)")

    logger.info("")

    overall_start = datetime.utcnow()

    # Run jockeys worker
    logger.info("=" * 80)
    logger.info("STEP 1/3: JOCKEYS STATISTICS")
    logger.info("=" * 80)
    try:
        # Temporarily override sys.argv to pass limit argument
        original_argv = sys.argv
        sys.argv = ['jockeys_statistics_worker.py']
        if args.limit:
            sys.argv.extend(['--limit', str(args.limit)])

        jockeys_statistics_worker.main()
        logger.info("Jockeys worker completed successfully")
    except Exception as e:
        logger.error(f"Jockeys worker failed: {e}", exc_info=True)
    finally:
        sys.argv = original_argv

    logger.info("")

    # Run trainers worker
    logger.info("=" * 80)
    logger.info("STEP 2/3: TRAINERS STATISTICS")
    logger.info("=" * 80)
    try:
        # Temporarily override sys.argv to pass limit argument
        original_argv = sys.argv
        sys.argv = ['trainers_statistics_worker.py']
        if args.limit:
            sys.argv.extend(['--limit', str(args.limit)])

        trainers_statistics_worker.main()
        logger.info("Trainers worker completed successfully")
    except Exception as e:
        logger.error(f"Trainers worker failed: {e}", exc_info=True)
    finally:
        sys.argv = original_argv

    logger.info("")

    # Run owners worker
    logger.info("=" * 80)
    logger.info("STEP 3/3: OWNERS STATISTICS")
    logger.info("=" * 80)
    try:
        # Temporarily override sys.argv to pass limit argument
        original_argv = sys.argv
        sys.argv = ['owners_statistics_worker.py']
        if args.limit:
            sys.argv.extend(['--limit', str(args.limit)])

        owners_statistics_worker.main()
        logger.info("Owners worker completed successfully")
    except Exception as e:
        logger.error(f"Owners worker failed: {e}", exc_info=True)
    finally:
        sys.argv = original_argv

    # Final summary
    overall_end = datetime.utcnow()
    overall_duration = (overall_end - overall_start).total_seconds()

    logger.info("")
    logger.info("=" * 80)
    logger.info("ALL STATISTICS WORKERS COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total duration: {overall_duration:.2f}s ({overall_duration/60:.2f} minutes)")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
