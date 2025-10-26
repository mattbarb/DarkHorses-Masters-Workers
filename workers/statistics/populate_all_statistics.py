#!/usr/bin/env python3
"""
Populate ALL Statistics - Master Orchestrator
==============================================

Runs all 6 statistics calculation workers in sequence to populate complete
statistics for all entity types from historical database data.

Workers Executed:
-----------------
1. calculate_sire_statistics.py - Populates ra_sire_stats
2. calculate_dam_statistics.py - Populates ra_dam_stats
3. calculate_damsire_statistics.py - Populates ra_damsire_stats
4. calculate_jockey_statistics.py - Updates ra_mst_jockeys
5. calculate_trainer_statistics.py - Updates ra_mst_trainers
6. calculate_owner_statistics.py - Updates ra_mst_owners

Features:
---------
- Sequential execution with progress tracking
- Overall timing and performance metrics
- Automatic error detection and reporting
- Resume capability (each worker supports --resume)
- Summary report with entity counts

Performance Expectations:
-------------------------
Based on database size:
- Sires: ~10-15 minutes (depends on progeny count)
- Dams: ~10-15 minutes (depends on progeny count)
- Damsires: ~10-15 minutes (depends on grandoffspring count)
- Jockeys: ~30-60 seconds (3,500 jockeys)
- Trainers: ~30-60 seconds (2,800 trainers)
- Owners: ~5-10 minutes (48,000 owners)

TOTAL ESTIMATED TIME: 30-60 minutes for full database

Data Requirements:
------------------
- Position data must be populated in ra_mst_runners (from results fetcher)
- Pedigree data must be populated in ra_rel_pedigree
- Race dates must be in ra_races
- All master tables (ra_mst_*) must exist

Usage:
------
    # Run all workers
    python3 scripts/statistics_workers/populate_all_statistics.py

    # Run specific workers
    python3 scripts/statistics_workers/populate_all_statistics.py --workers sires dams jockeys

    # Test mode (limit 10 entities per worker)
    python3 scripts/statistics_workers/populate_all_statistics.py --test

    # Resume all workers from checkpoints
    python3 scripts/statistics_workers/populate_all_statistics.py --resume

Author: Claude Code
Date: 2025-10-20
"""

import sys
import os
import argparse
import subprocess
from datetime import datetime
from typing import Dict, List
from pathlib import Path

# Setup logging
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Worker definitions
WORKERS = {
    'sires': {
        'script': 'calculate_sire_statistics.py',
        'description': 'Sire statistics (own career + progeny)',
        'table': 'ra_sire_stats'
    },
    'dams': {
        'script': 'calculate_dam_statistics.py',
        'description': 'Dam statistics (own career + progeny)',
        'table': 'ra_dam_stats'
    },
    'damsires': {
        'script': 'calculate_damsire_statistics.py',
        'description': 'Damsire statistics (own career + grandoffspring)',
        'table': 'ra_damsire_stats'
    },
    'jockeys': {
        'script': 'calculate_jockey_statistics.py',
        'description': 'Jockey statistics (rides, wins, recent form)',
        'table': 'ra_mst_jockeys'
    },
    'trainers': {
        'script': 'calculate_trainer_statistics.py',
        'description': 'Trainer statistics (runners, wins, recent form)',
        'table': 'ra_mst_trainers'
    },
    'owners': {
        'script': 'calculate_owner_statistics.py',
        'description': 'Owner statistics (runners, wins, horses, recent form)',
        'table': 'ra_mst_owners'
    }
}


def run_worker(worker_name: str, script_path: str, test: bool = False, resume: bool = False) -> Dict:
    """
    Run a single statistics worker

    Args:
        worker_name: Name of the worker (for logging)
        script_path: Path to the worker script
        test: If True, run with --limit 10
        resume: If True, pass --resume flag

    Returns:
        Dict with success, duration, and error info
    """
    logger.info(f"\n{'=' * 80}")
    logger.info(f"STARTING: {worker_name.upper()}")
    logger.info(f"Script: {script_path}")
    logger.info(f"{'=' * 80}\n")

    start_time = datetime.utcnow()

    # Build command
    cmd = ['python3', script_path]
    if test:
        cmd.extend(['--limit', '10'])
    if resume:
        cmd.append('--resume')

    try:
        # Run worker
        result = subprocess.run(
            cmd,
            cwd=str(Path(__file__).parent.parent.parent),
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout
        )

        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()

        # Log output
        if result.stdout:
            logger.info(result.stdout)
        if result.stderr:
            logger.error(result.stderr)

        success = result.returncode == 0

        if success:
            logger.info(f"\n✓ {worker_name.upper()} COMPLETED SUCCESSFULLY")
            logger.info(f"Duration: {duration:.2f}s ({duration/60:.2f}m)")
        else:
            logger.error(f"\n✗ {worker_name.upper()} FAILED")
            logger.error(f"Exit code: {result.returncode}")

        return {
            'success': success,
            'duration': duration,
            'exit_code': result.returncode,
            'error': result.stderr if not success else None
        }

    except subprocess.TimeoutExpired:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"\n✗ {worker_name.upper()} TIMED OUT")
        return {
            'success': False,
            'duration': duration,
            'exit_code': -1,
            'error': 'Worker timed out after 1 hour'
        }

    except Exception as e:
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        logger.error(f"\n✗ {worker_name.upper()} ERROR: {e}")
        return {
            'success': False,
            'duration': duration,
            'exit_code': -1,
            'error': str(e)
        }


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Run all statistics calculation workers',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all workers
  python3 scripts/statistics_workers/populate_all_statistics.py

  # Test mode (10 entities per worker)
  python3 scripts/statistics_workers/populate_all_statistics.py --test

  # Run specific workers
  python3 scripts/statistics_workers/populate_all_statistics.py --workers sires dams jockeys

  # Resume all from checkpoints
  python3 scripts/statistics_workers/populate_all_statistics.py --resume
        """
    )
    parser.add_argument(
        '--workers',
        nargs='+',
        choices=list(WORKERS.keys()),
        help='Specific workers to run (default: all)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test mode: process only 10 entities per worker'
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume all workers from checkpoints'
    )
    args = parser.parse_args()

    # Determine which workers to run
    workers_to_run = args.workers if args.workers else list(WORKERS.keys())

    logger.info("=" * 80)
    logger.info("POPULATE ALL STATISTICS - MASTER ORCHESTRATOR")
    logger.info("=" * 80)
    logger.info(f"Mode: {'TEST (10 entities)' if args.test else 'FULL'}")
    logger.info(f"Resume: {'Yes' if args.resume else 'No'}")
    logger.info(f"Workers: {', '.join(workers_to_run)}")
    logger.info(f"Start time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}")
    logger.info("=" * 80)

    # Run workers
    overall_start = datetime.utcnow()
    results = {}

    for i, worker_name in enumerate(workers_to_run, 1):
        worker_info = WORKERS[worker_name]
        script_name = worker_info['script']
        script_path = Path(__file__).parent / script_name

        if not script_path.exists():
            logger.error(f"\n✗ Script not found: {script_path}")
            results[worker_name] = {
                'success': False,
                'duration': 0,
                'exit_code': -1,
                'error': f'Script not found: {script_path}'
            }
            continue

        logger.info(f"\n[{i}/{len(workers_to_run)}] {worker_info['description']}")
        logger.info(f"Table: {worker_info['table']}")

        # Run worker
        result = run_worker(
            worker_name=worker_name,
            script_path=str(script_path),
            test=args.test,
            resume=args.resume
        )
        results[worker_name] = result

        # Stop if worker failed (unless we're in test mode)
        if not result['success'] and not args.test:
            logger.error(f"\nStopping due to failure in {worker_name}")
            break

    # Calculate overall statistics
    overall_end = datetime.utcnow()
    overall_duration = (overall_end - overall_start).total_seconds()

    # Print summary
    logger.info("\n" + "=" * 80)
    logger.info("SUMMARY")
    logger.info("=" * 80)

    successful = [w for w, r in results.items() if r['success']]
    failed = [w for w, r in results.items() if not r['success']]

    logger.info(f"\nOverall Duration: {overall_duration:.2f}s ({overall_duration/60:.2f}m)")
    logger.info(f"\nWorkers Run: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")

    # Individual worker details
    logger.info("\nDetailed Results:")
    logger.info("-" * 80)
    for worker_name, result in results.items():
        status = "✓ SUCCESS" if result['success'] else "✗ FAILED"
        logger.info(f"{worker_name:15} | {status:12} | {result['duration']:8.2f}s")
        if result['error']:
            logger.info(f"                | Error: {result['error']}")
    logger.info("-" * 80)

    # Failed workers
    if failed:
        logger.warning("\nFailed Workers:")
        for worker_name in failed:
            result = results[worker_name]
            logger.warning(f"  - {worker_name}: {result['error']}")

    logger.info("\n" + "=" * 80)
    if len(failed) == 0:
        logger.info("ALL WORKERS COMPLETED SUCCESSFULLY")
    else:
        logger.warning(f"{len(failed)} WORKER(S) FAILED")
    logger.info("=" * 80)

    # Exit with appropriate code
    sys.exit(0 if len(failed) == 0 else 1)


if __name__ == '__main__':
    main()
