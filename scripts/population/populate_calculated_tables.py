#!/usr/bin/env python3
"""
Populate All Calculated Tables

Runs all database calculation scripts to populate derived/aggregated tables:
- ra_entity_combinations (jockey-trainer partnerships)
- ra_runner_odds (aggregated odds from live/historical)

These tables are calculated FROM existing data and should be run regularly
to keep statistics up to date.

Usage:
    python3 scripts/populate_calculated_tables.py [--skip-entity-combinations] [--skip-runner-odds]

Schedule:
    Daily after results are updated (around 2 AM)
    OR
    Weekly for full recalculation

Options:
    --skip-entity-combinations    Skip entity combinations calculation
    --skip-runner-odds            Skip runner odds aggregation
    --min-runs N                  Minimum runs for entity combinations (default: 5)
    --days-back N                 Days of odds data to process (default: 7)
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from populate_entity_combinations_from_runners import populate_entity_combinations
from populate_runner_odds import populate_runner_odds

logger = get_logger('populate_calculated_tables')


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate all calculated tables'
    )
    parser.add_argument(
        '--skip-entity-combinations',
        action='store_true',
        help='Skip entity combinations calculation'
    )
    parser.add_argument(
        '--skip-runner-odds',
        action='store_true',
        help='Skip runner odds aggregation'
    )
    parser.add_argument(
        '--min-runs',
        type=int,
        default=5,
        help='Minimum runs for entity combinations (default: 5)'
    )
    parser.add_argument(
        '--days-back',
        type=int,
        default=7,
        help='Days of odds data to process (default: 7)'
    )

    args = parser.parse_args()

    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("POPULATE CALCULATED TABLES")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # 1. Entity Combinations
    if not args.skip_entity_combinations:
        logger.info("\n" + "=" * 80)
        logger.info("1. POPULATING ra_entity_combinations")
        logger.info("=" * 80)

        result = populate_entity_combinations(min_runs=args.min_runs)
        results['entity_combinations'] = result

        if not result['success']:
            logger.error(f"❌ Entity combinations failed: {result.get('error')}")
        else:
            logger.info(f"✅ Entity combinations: {result['total_in_db']} jockey-trainer partnerships")
    else:
        logger.info("\n⏭️  Skipping entity combinations")

    # 2. Runner Odds
    if not args.skip_runner_odds:
        logger.info("\n" + "=" * 80)
        logger.info("2. POPULATING ra_runner_odds")
        logger.info("=" * 80)

        result = populate_runner_odds(days_back=args.days_back)
        results['runner_odds'] = result

        if not result['success']:
            logger.error(f"❌ Runner odds failed: {result.get('error')}")
        else:
            logger.info(f"✅ Runner odds: {result['total_in_db']} odds records")
    else:
        logger.info("\n⏭️  Skipping runner odds")

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "=" * 80)
    logger.info("CALCULATED TABLES POPULATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Duration: {duration}")
    logger.info(f"\nResults Summary:")

    for table_name, result in results.items():
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        logger.info(f"  {table_name}: {status}")

        if result['success']:
            logger.info(f"    - Records in database: {result['total_in_db']}")

    # Exit code
    all_success = all(r['success'] for r in results.values())

    if all_success:
        logger.info("\n✅ All calculated tables populated successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Some calculated tables failed to populate")
        sys.exit(1)


if __name__ == '__main__':
    main()
