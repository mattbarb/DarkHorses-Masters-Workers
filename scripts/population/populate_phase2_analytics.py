#!/usr/bin/env python3
"""
Populate Phase 2 Analytics Tables

Runs all Phase 2 calculation scripts to populate derived analytics tables:
- ra_runner_statistics (individual runner performance metrics)
- ra_performance_by_distance (entity performance grouped by distance)
- ra_performance_by_venue (entity performance grouped by venue/course)

These tables are calculated FROM existing ra_mst_runners and ra_races data and
should be run regularly to keep statistics up to date.

Phase 2 tables provide advanced analytics for:
- ML feature engineering
- Race prediction modeling
- Course specialist identification
- Distance preference analysis
- Recent form tracking

Usage:
    python3 scripts/populate_phase2_analytics.py [options]

Schedule:
    Daily after results are updated (around 2 AM)
    OR
    Weekly for full recalculation

Options:
    --skip-runner-stats      Skip runner statistics calculation
    --skip-distance          Skip distance performance calculation
    --skip-venue             Skip venue performance calculation
    --min-runs N             Minimum runs for inclusion (default: varies by table)
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from populate_runner_statistics import populate_runner_statistics
from populate_performance_by_distance import populate_performance_by_distance
from populate_performance_by_venue import populate_performance_by_venue

logger = get_logger('populate_phase2_analytics')


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate all Phase 2 analytics tables'
    )
    parser.add_argument(
        '--skip-runner-stats',
        action='store_true',
        help='Skip runner statistics calculation'
    )
    parser.add_argument(
        '--skip-distance',
        action='store_true',
        help='Skip distance performance calculation'
    )
    parser.add_argument(
        '--skip-venue',
        action='store_true',
        help='Skip venue performance calculation'
    )
    parser.add_argument(
        '--min-runs-runner',
        type=int,
        default=3,
        help='Minimum career runs for runner stats (default: 3)'
    )
    parser.add_argument(
        '--min-runs-distance',
        type=int,
        default=5,
        help='Minimum runs per distance for distance stats (default: 5)'
    )
    parser.add_argument(
        '--min-runs-venue',
        type=int,
        default=5,
        help='Minimum runs per venue for venue stats (default: 5)'
    )

    args = parser.parse_args()

    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("POPULATE PHASE 2 ANALYTICS TABLES")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # 1. Runner Statistics
    if not args.skip_runner_stats:
        logger.info("\n" + "=" * 80)
        logger.info("1. POPULATING ra_runner_statistics")
        logger.info("=" * 80)

        table_start = datetime.now()
        result = populate_runner_statistics(min_runs=args.min_runs_runner)
        results['runner_statistics'] = result
        table_duration = datetime.now() - table_start

        if not result['success']:
            logger.error(f"❌ Runner statistics failed: {result.get('error')}")
        else:
            logger.info(f"✅ Runner statistics: {result['total_in_db']} records")
            logger.info(f"   Duration: {table_duration}")
    else:
        logger.info("\n⏭️  Skipping runner statistics")

    # 2. Performance by Distance
    if not args.skip_distance:
        logger.info("\n" + "=" * 80)
        logger.info("2. POPULATING ra_performance_by_distance")
        logger.info("=" * 80)

        table_start = datetime.now()
        result = populate_performance_by_distance(min_runs=args.min_runs_distance)
        results['performance_by_distance'] = result
        table_duration = datetime.now() - table_start

        if not result['success']:
            logger.error(f"❌ Distance performance failed: {result.get('error')}")
        else:
            logger.info(f"✅ Distance performance: {result['total_in_db']} records")
            logger.info(f"   Duration: {table_duration}")
    else:
        logger.info("\n⏭️  Skipping distance performance")

    # 3. Performance by Venue
    if not args.skip_venue:
        logger.info("\n" + "=" * 80)
        logger.info("3. POPULATING ra_performance_by_venue")
        logger.info("=" * 80)

        table_start = datetime.now()
        result = populate_performance_by_venue(min_runs=args.min_runs_venue)
        results['performance_by_venue'] = result
        table_duration = datetime.now() - table_start

        if not result['success']:
            logger.error(f"❌ Venue performance failed: {result.get('error')}")
        else:
            logger.info(f"✅ Venue performance: {result['total_in_db']} records")
            logger.info(f"   Duration: {table_duration}")
    else:
        logger.info("\n⏭️  Skipping venue performance")

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2 ANALYTICS POPULATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total duration: {duration}")
    logger.info(f"\nResults Summary:")

    table_names = {
        'runner_statistics': 'ra_runner_statistics',
        'performance_by_distance': 'ra_performance_by_distance',
        'performance_by_venue': 'ra_performance_by_venue'
    }

    for key, result in results.items():
        table_name = table_names.get(key, key)
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        logger.info(f"  {table_name}: {status}")

        if result['success']:
            logger.info(f"    - Records in database: {result['total_in_db']}")

    # Exit code
    all_success = all(r['success'] for r in results.values())

    if all_success:
        logger.info("\n✅ All Phase 2 analytics tables populated successfully")
        logger.info("\nThese tables provide:")
        logger.info("  - Individual runner performance metrics (runner_statistics)")
        logger.info("  - Entity performance by distance (performance_by_distance)")
        logger.info("  - Entity performance by venue (performance_by_venue)")
        logger.info("\nUse cases:")
        logger.info("  - ML feature engineering")
        logger.info("  - Race prediction modeling")
        logger.info("  - Course specialist identification")
        logger.info("  - Distance preference analysis")
        sys.exit(0)
    else:
        logger.error("\n❌ Some Phase 2 analytics tables failed to populate")
        sys.exit(1)


if __name__ == '__main__':
    main()
