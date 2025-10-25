#!/usr/bin/env python3
"""
Populate ALL Calculated Tables (Phase 1 + Phase 2)

Master script that runs all database calculation tasks in the correct order:

Phase 1 - Database Calculations:
- ra_entity_combinations (jockey-trainer partnerships)

Phase 2 - Analytics:
- ra_runner_statistics (runner performance metrics)
- ra_performance_by_distance (distance-based performance)
- ra_performance_by_venue (venue-based performance)

This is the main production script for scheduled runs.

Usage:
    python3 scripts/populate_all_calculated_tables.py [options]

Typical Production Run:
    python3 scripts/populate_all_calculated_tables.py

Custom Thresholds:
    python3 scripts/populate_all_calculated_tables.py \\
      --min-runs 10 --days-back 14 \\
      --min-runs-runner 5 --min-runs-distance 10 --min-runs-venue 10

Options:
    --skip-phase1              Skip all Phase 1 calculations
    --skip-phase2              Skip all Phase 2 calculations
    --skip-entity-combinations Skip jockey-trainer partnerships
    --skip-runner-stats        Skip runner statistics
    --skip-distance            Skip distance performance
    --skip-venue               Skip venue performance
    --min-runs N               Phase 1: Entity combinations threshold (default: 5)
    --min-runs-runner N        Phase 2: Runner stats threshold (default: 3)
    --min-runs-distance N      Phase 2: Distance stats threshold (default: 5)
    --min-runs-venue N         Phase 2: Venue stats threshold (default: 5)
"""

import sys
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger

# Import individual populate functions
try:
    from populate_entity_combinations_from_runners import populate_entity_combinations
    from populate_runner_statistics import populate_runner_statistics
    from populate_performance_by_distance import populate_performance_by_distance
    from populate_performance_by_venue import populate_performance_by_venue
except ImportError as e:
    print(f"Error importing populate functions: {e}")
    print("Make sure all calculation scripts are in scripts/ directory")
    sys.exit(1)

logger = get_logger('populate_all_calculated')


def run_phase1(args):
    """Run Phase 1 calculations"""
    logger.info("=" * 80)
    logger.info("PHASE 1 - DATABASE CALCULATIONS")
    logger.info("=" * 80)

    results = {}

    # 1. Entity Combinations (only table in Phase 1)
    if not args.skip_entity_combinations:
        logger.info("\n[1/1] Populating ra_entity_combinations...")
        result = populate_entity_combinations(min_runs=args.min_runs)
        results['entity_combinations'] = result

        if result['success']:
            logger.info(f"✅ {result['total_in_db']} jockey-trainer partnerships")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")
    else:
        logger.info("\n⏭️  Skipping entity combinations")

    return results


def run_phase2(args):
    """Run Phase 2 analytics calculations"""
    logger.info("\n" + "=" * 80)
    logger.info("PHASE 2 - ANALYTICS")
    logger.info("=" * 80)

    results = {}

    # 1. Runner Statistics
    if not args.skip_runner_stats:
        logger.info("\n[1/3] Populating ra_runner_statistics...")
        result = populate_runner_statistics(min_runs=args.min_runs_runner)
        results['runner_statistics'] = result

        if result['success']:
            logger.info(f"✅ {result['total_in_db']} runner stat records")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")
    else:
        logger.info("\n⏭️  Skipping runner statistics")

    # 2. Performance by Distance
    if not args.skip_distance:
        logger.info("\n[2/3] Populating ra_performance_by_distance...")
        result = populate_performance_by_distance(min_runs=args.min_runs_distance)
        results['performance_by_distance'] = result

        if result['success']:
            logger.info(f"✅ {result['total_in_db']} distance performance records")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")
    else:
        logger.info("\n⏭️  Skipping distance performance")

    # 3. Performance by Venue
    if not args.skip_venue:
        logger.info("\n[3/3] Populating ra_performance_by_venue...")
        result = populate_performance_by_venue(min_runs=args.min_runs_venue)
        results['performance_by_venue'] = result

        if result['success']:
            logger.info(f"✅ {result['total_in_db']} venue performance records")
        else:
            logger.error(f"❌ Failed: {result.get('error')}")
    else:
        logger.info("\n⏭️  Skipping venue performance")

    return results


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate all calculated tables (Phase 1 + Phase 2)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Phase control
    parser.add_argument('--skip-phase1', action='store_true',
                       help='Skip all Phase 1 calculations')
    parser.add_argument('--skip-phase2', action='store_true',
                       help='Skip all Phase 2 calculations')

    # Phase 1 individual skips
    parser.add_argument('--skip-entity-combinations', action='store_true',
                       help='Skip entity combinations')

    # Phase 2 individual skips
    parser.add_argument('--skip-runner-stats', action='store_true',
                       help='Skip runner statistics')
    parser.add_argument('--skip-distance', action='store_true',
                       help='Skip distance performance')
    parser.add_argument('--skip-venue', action='store_true',
                       help='Skip venue performance')

    # Phase 1 parameters
    parser.add_argument('--min-runs', type=int, default=5,
                       help='Phase 1: Minimum runs for entity combinations (default: 5)')

    # Phase 2 parameters
    parser.add_argument('--min-runs-runner', type=int, default=3,
                       help='Phase 2: Minimum career runs for runner stats (default: 3)')
    parser.add_argument('--min-runs-distance', type=int, default=5,
                       help='Phase 2: Minimum runs per distance (default: 5)')
    parser.add_argument('--min-runs-venue', type=int, default=5,
                       help='Phase 2: Minimum runs per venue (default: 5)')

    args = parser.parse_args()

    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("POPULATE ALL CALCULATED TABLES")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"\nConfiguration:")
    logger.info(f"  Phase 1: {'SKIP' if args.skip_phase1 else 'RUN'}")
    logger.info(f"    Entity combinations: min_runs={args.min_runs}")
    logger.info(f"  Phase 2: {'SKIP' if args.skip_phase2 else 'RUN'}")
    logger.info(f"    Runner stats: min_runs={args.min_runs_runner}")
    logger.info(f"    Distance: min_runs={args.min_runs_distance}")
    logger.info(f"    Venue: min_runs={args.min_runs_venue}")

    all_results = {}

    # Run Phase 1
    if not args.skip_phase1:
        phase1_results = run_phase1(args)
        all_results.update(phase1_results)
    else:
        logger.info("\n⏭️  SKIPPING PHASE 1")

    # Run Phase 2
    if not args.skip_phase2:
        phase2_results = run_phase2(args)
        all_results.update(phase2_results)
    else:
        logger.info("\n⏭️  SKIPPING PHASE 2")

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "=" * 80)
    logger.info("ALL CALCULATED TABLES POPULATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Duration: {duration}")
    logger.info(f"\nResults Summary:")

    phase1_tables = ['entity_combinations']
    phase2_tables = ['runner_statistics', 'performance_by_distance', 'performance_by_venue']

    if not args.skip_phase1:
        logger.info("\n  Phase 1:")
        for table in phase1_tables:
            if table in all_results:
                result = all_results[table]
                status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                logger.info(f"    {table}: {status}")
                if result['success']:
                    logger.info(f"      Records: {result['total_in_db']}")

    if not args.skip_phase2:
        logger.info("\n  Phase 2:")
        for table in phase2_tables:
            if table in all_results:
                result = all_results[table]
                status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
                logger.info(f"    {table}: {status}")
                if result['success']:
                    logger.info(f"      Records: {result['total_in_db']}")

    # Exit code
    if all_results:
        all_success = all(r['success'] for r in all_results.values())
        if all_success:
            logger.info("\n✅ All calculated tables populated successfully")
            sys.exit(0)
        else:
            logger.error("\n❌ Some calculated tables failed to populate")
            sys.exit(1)
    else:
        logger.info("\n⏭️  No tables processed (all skipped)")
        sys.exit(0)


if __name__ == '__main__':
    main()
