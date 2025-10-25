#!/usr/bin/env python3
"""
Populate Phase 1 Planned Tables

Runs all Phase 1 "Quick Win" table population scripts:
1. ra_mst_regions - Extract regions from courses
2. ra_entity_combinations - Analyze jockey/trainer/owner/horse patterns

These tables require NO external API calls - only database analysis.

Usage:
    python3 scripts/populate_phase1_tables.py [--skip-regions] [--skip-combinations]

Options:
    --skip-regions         Skip regions table population
    --skip-combinations    Skip entity combinations population
    --min-combo-races N    Minimum races for combinations (default: 2)
"""

import sys
from pathlib import Path
import argparse
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import get_logger
from populate_regions import populate_regions
from populate_entity_combinations import populate_entity_combinations

logger = get_logger('populate_phase1')


def main():
    """Main execution"""
    parser = argparse.ArgumentParser(
        description='Populate Phase 1 planned tables'
    )
    parser.add_argument(
        '--skip-regions',
        action='store_true',
        help='Skip regions table population'
    )
    parser.add_argument(
        '--skip-combinations',
        action='store_true',
        help='Skip entity combinations population'
    )
    parser.add_argument(
        '--min-combo-races',
        type=int,
        default=2,
        help='Minimum races for combinations (default: 2)'
    )

    args = parser.parse_args()

    start_time = datetime.now()

    logger.info("=" * 80)
    logger.info("PHASE 1 TABLE POPULATION")
    logger.info("=" * 80)
    logger.info(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n")

    results = {}

    # 1. Populate regions
    if not args.skip_regions:
        logger.info("\n" + "=" * 80)
        logger.info("1. POPULATING ra_mst_regions")
        logger.info("=" * 80)

        result = populate_regions()
        results['regions'] = result

        if not result['success']:
            logger.error(f"❌ Regions population failed: {result.get('error')}")
        else:
            logger.info(f"✅ Regions populated: {result['total_in_db']} regions")
    else:
        logger.info("\n⏭️  Skipping regions table")

    # 2. Populate entity combinations
    if not args.skip_combinations:
        logger.info("\n" + "=" * 80)
        logger.info("2. POPULATING ra_entity_combinations")
        logger.info("=" * 80)

        result = populate_entity_combinations(min_races=args.min_combo_races)
        results['combinations'] = result

        if not result['success']:
            logger.error(f"❌ Entity combinations failed: {result.get('error')}")
        else:
            logger.info(f"✅ Combinations populated: {result['total_in_db']} combinations")
    else:
        logger.info("\n⏭️  Skipping entity combinations table")

    # Final summary
    end_time = datetime.now()
    duration = end_time - start_time

    logger.info("\n" + "=" * 80)
    logger.info("PHASE 1 POPULATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Duration: {duration}")
    logger.info(f"\nResults Summary:")

    for table_name, result in results.items():
        status = "✅ SUCCESS" if result['success'] else "❌ FAILED"
        logger.info(f"  {table_name}: {status}")

        if result['success']:
            if table_name == 'regions':
                logger.info(f"    - Regions in database: {result['total_in_db']}")
            elif table_name == 'combinations':
                logger.info(f"    - Combinations in database: {result['total_in_db']}")

    # Exit code
    all_success = all(r['success'] for r in results.values())

    if all_success:
        logger.info("\n✅ All Phase 1 tables populated successfully")
        sys.exit(0)
    else:
        logger.error("\n❌ Some Phase 1 tables failed to populate")
        sys.exit(1)


if __name__ == '__main__':
    main()
