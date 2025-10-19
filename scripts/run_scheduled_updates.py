#!/usr/bin/env python3
"""
Scheduled Updates Orchestrator
Main orchestrator that manages all scheduled data updates.

This script:
- Reads configuration from scheduler_config.yaml
- Determines which updates to run based on schedule
- Manages concurrent execution (prevents overlaps)
- Provides centralized logging and monitoring
- Can be run via cron or as a continuous daemon

Usage:
    python run_scheduled_updates.py               # Check schedule and run appropriate updates
    python run_scheduled_updates.py --force-all   # Force run all update types
    python run_scheduled_updates.py --test        # Dry-run mode (no database writes)
"""

import sys
import os
import argparse
import yaml
import fcntl
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import signal

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.config import get_config
from utils.logger import get_logger

logger = get_logger('scheduler')


class UpdateLock:
    """Context manager for update locks to prevent concurrent execution"""

    def __init__(self, lock_name: str, lock_dir: str = "/tmp", stale_timeout: int = 3600):
        """
        Initialize update lock

        Args:
            lock_name: Name of the lock (e.g., 'update_daily_data')
            lock_dir: Directory for lock files
            stale_timeout: Remove locks older than this (seconds)
        """
        self.lock_file = Path(lock_dir) / f"darkhorses_update_{lock_name}.lock"
        self.lock_fd = None
        self.stale_timeout = stale_timeout

    def __enter__(self):
        """Acquire lock"""
        # Check for stale lock
        if self.lock_file.exists():
            lock_age = time.time() - self.lock_file.stat().st_mtime
            if lock_age > self.stale_timeout:
                logger.warning(f"Removing stale lock (age: {lock_age:.0f}s): {self.lock_file}")
                try:
                    self.lock_file.unlink()
                except Exception as e:
                    logger.warning(f"Failed to remove stale lock: {e}")

        # Try to acquire lock
        try:
            self.lock_fd = open(self.lock_file, 'w')
            fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_fd.write(f"{os.getpid()}\n{datetime.utcnow().isoformat()}")
            self.lock_fd.flush()
            return self
        except IOError:
            # Lock already held
            if self.lock_fd:
                self.lock_fd.close()
            raise RuntimeError(f"Another instance is already running (lock: {self.lock_file})")

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Release lock"""
        if self.lock_fd:
            try:
                fcntl.flock(self.lock_fd, fcntl.LOCK_UN)
                self.lock_fd.close()
            except Exception as e:
                logger.warning(f"Failed to release lock: {e}")
            try:
                self.lock_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to remove lock file: {e}")


class ScheduledUpdatesOrchestrator:
    """Orchestrator for scheduled data updates"""

    def __init__(self, config_path: Optional[str] = None, dry_run: bool = False):
        """
        Initialize orchestrator

        Args:
            config_path: Path to scheduler config YAML file
            dry_run: If True, don't actually run updates (testing only)
        """
        self.config = get_config()
        self.dry_run = dry_run

        # Load scheduler configuration
        if config_path is None:
            config_path = self.config.paths.root_dir / 'config' / 'scheduler_config.yaml'

        self.scheduler_config = self._load_scheduler_config(config_path)

        # Statistics
        self.stats = {
            'start_time': datetime.utcnow(),
            'updates_run': [],
            'errors': 0,
            'total_duration': 0
        }

        if dry_run:
            logger.warning("DRY RUN MODE - No updates will be executed")

    def _load_scheduler_config(self, config_path: Path) -> Dict:
        """Load scheduler configuration from YAML file"""
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded scheduler config from: {config_path}")
            return config
        except Exception as e:
            logger.error(f"Failed to load scheduler config: {e}")
            # Return minimal default config
            return {
                'intervals': {},
                'retry': {'max_attempts': 3, 'initial_delay': 5},
                'concurrency': {'enabled': True}
            }

    def run(self, force_all: bool = False, specific_update: Optional[str] = None):
        """
        Run scheduled updates

        Args:
            force_all: Force run all update types regardless of schedule
            specific_update: Run a specific update type only (e.g., 'daily_data')
        """
        logger.info("=" * 80)
        logger.info("SCHEDULED UPDATES ORCHESTRATOR - Starting")
        logger.info(f"Time: {self.stats['start_time'].isoformat()}")
        logger.info(f"Force all: {force_all}")
        logger.info(f"Dry run: {self.dry_run}")
        logger.info("=" * 80)

        try:
            # Determine which updates to run
            if specific_update:
                updates_to_run = [specific_update]
                logger.info(f"Running specific update: {specific_update}")
            elif force_all:
                updates_to_run = list(self.scheduler_config.get('intervals', {}).keys())
                logger.info(f"Force running all updates: {updates_to_run}")
            else:
                updates_to_run = self._determine_due_updates()
                logger.info(f"Updates due: {updates_to_run if updates_to_run else 'None'}")

            # Run each update
            for update_name in updates_to_run:
                self._run_update(update_name)

            # Print summary
            self._print_summary()

            return self.stats

        except Exception as e:
            logger.error(f"Orchestrator failed: {e}", exc_info=True)
            self.stats['errors'] += 1
            return self.stats

    def _determine_due_updates(self) -> List[str]:
        """
        Determine which updates are due to run based on current time

        Returns:
            List of update names that should run
        """
        due_updates = []
        now = datetime.utcnow()
        current_hour = now.hour
        current_minute = now.minute
        current_day = now.day
        current_weekday = now.weekday()  # 0=Monday, 6=Sunday

        for update_name, update_config in self.scheduler_config.get('intervals', {}).items():
            if not update_config.get('enabled', True):
                continue

            # Check if update is due based on frequency (cron expression)
            # This is a simplified check - for production, use croniter library
            frequency = update_config.get('frequency', '')

            # Parse simple cron expressions
            # Format: minute hour day month weekday
            # Example: "*/15 9-20 * * *" = every 15 min between 9-20 hours

            if self._is_update_due(frequency, now):
                due_updates.append(update_name)

        return due_updates

    def _is_update_due(self, cron_expr: str, now: datetime) -> bool:
        """
        Simple cron expression parser (basic implementation)

        For production, use croniter library for full cron support.
        This is a simplified version for common cases.

        Args:
            cron_expr: Cron expression (e.g., "0 6 * * *")
            now: Current datetime

        Returns:
            True if update is due
        """
        try:
            parts = cron_expr.strip().split()
            if len(parts) != 5:
                return False

            minute, hour, day, month, weekday = parts

            # Check minute
            if not self._matches_cron_field(minute, now.minute, 0, 59):
                return False

            # Check hour
            if not self._matches_cron_field(hour, now.hour, 0, 23):
                return False

            # Check day of month
            if not self._matches_cron_field(day, now.day, 1, 31):
                return False

            # Check month
            if not self._matches_cron_field(month, now.month, 1, 12):
                return False

            # Check weekday (0=Sunday in some systems, 0=Monday in others)
            # We use 0=Monday (Python's weekday())
            weekday_val = (now.weekday() + 1) % 7  # Convert to 0=Sunday
            if not self._matches_cron_field(weekday, weekday_val, 0, 6):
                return False

            return True

        except Exception as e:
            logger.warning(f"Failed to parse cron expression '{cron_expr}': {e}")
            return False

    def _matches_cron_field(self, field: str, value: int, min_val: int, max_val: int) -> bool:
        """
        Check if a cron field matches the current value

        Args:
            field: Cron field (e.g., "*/15", "9-20", "0", "*")
            value: Current value (e.g., current hour)
            min_val: Minimum valid value
            max_val: Maximum valid value

        Returns:
            True if matches
        """
        # Wildcard
        if field == '*':
            return True

        # Specific value
        if field.isdigit():
            return int(field) == value

        # Range (e.g., "9-20")
        if '-' in field:
            start, end = field.split('-')
            return int(start) <= value <= int(end)

        # Step (e.g., "*/15")
        if field.startswith('*/'):
            step = int(field[2:])
            return value % step == 0

        # List (e.g., "1,15,30")
        if ',' in field:
            values = [int(v) for v in field.split(',')]
            return value in values

        return False

    def _run_update(self, update_name: str):
        """
        Run a specific update

        Args:
            update_name: Name of the update (from config)
        """
        logger.info("\n" + "=" * 80)
        logger.info(f"RUNNING UPDATE: {update_name}")
        logger.info("=" * 80)

        update_config = self.scheduler_config['intervals'].get(update_name, {})
        script = update_config.get('script', '')
        args = update_config.get('args', '')
        timeout = update_config.get('timeout', 900)  # Default 15 minutes

        if not script:
            logger.error(f"No script defined for update: {update_name}")
            self.stats['errors'] += 1
            return

        # Build command
        script_path = self.config.paths.root_dir / script
        cmd = [sys.executable, str(script_path)]

        if args:
            cmd.extend(args.split())

        if self.dry_run:
            cmd.append('--dry-run')

        logger.info(f"Command: {' '.join(cmd)}")
        logger.info(f"Timeout: {timeout}s")

        # Use lock to prevent concurrent execution
        lock_name = update_name
        if not self.scheduler_config.get('concurrency', {}).get('enabled', True):
            logger.info("Concurrency control disabled, running without lock")
            lock_name = None

        update_start = time.time()

        try:
            if lock_name:
                lock_dir = self.scheduler_config.get('concurrency', {}).get('lock_dir', '/tmp')
                stale_timeout = self.scheduler_config.get('concurrency', {}).get('stale_timeout', 3600)

                with UpdateLock(lock_name, lock_dir=lock_dir, stale_timeout=stale_timeout):
                    result = self._execute_update(cmd, timeout)
            else:
                result = self._execute_update(cmd, timeout)

            # Record results
            update_duration = time.time() - update_start
            self.stats['updates_run'].append({
                'name': update_name,
                'success': result['success'],
                'duration': update_duration,
                'exit_code': result.get('exit_code'),
                'error': result.get('error')
            })

            if result['success']:
                logger.info(f"Update completed successfully in {update_duration:.2f}s")
            else:
                logger.error(f"Update failed: {result.get('error')}")
                self.stats['errors'] += 1

        except RuntimeError as e:
            logger.warning(f"Update skipped: {e}")
            # Not counted as error - just already running
        except Exception as e:
            logger.error(f"Update execution failed: {e}", exc_info=True)
            self.stats['errors'] += 1

    def _execute_update(self, cmd: List[str], timeout: int) -> Dict:
        """
        Execute update script

        Args:
            cmd: Command to execute
            timeout: Timeout in seconds

        Returns:
            Result dictionary
        """
        if self.dry_run:
            logger.info("[DRY RUN] Would execute: " + ' '.join(cmd))
            return {'success': True, 'exit_code': 0}

        try:
            result = subprocess.run(
                cmd,
                timeout=timeout,
                capture_output=True,
                text=True
            )

            # Log output
            if result.stdout:
                logger.info(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.warning(f"STDERR:\n{result.stderr}")

            return {
                'success': result.returncode == 0,
                'exit_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except subprocess.TimeoutExpired:
            logger.error(f"Update timed out after {timeout}s")
            return {
                'success': False,
                'error': f'Timeout after {timeout}s'
            }
        except Exception as e:
            logger.error(f"Execution failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e)
            }

    def _print_summary(self):
        """Print execution summary"""
        end_time = datetime.utcnow()
        duration = (end_time - self.stats['start_time']).total_seconds()

        logger.info("\n" + "=" * 80)
        logger.info("ORCHESTRATOR SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Start time: {self.stats['start_time'].isoformat()}")
        logger.info(f"End time: {end_time.isoformat()}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info("")
        logger.info(f"Updates executed: {len(self.stats['updates_run'])}")
        logger.info(f"Errors: {self.stats['errors']}")

        if self.stats['updates_run']:
            logger.info("\nUpdate Details:")
            for update in self.stats['updates_run']:
                status = "SUCCESS" if update['success'] else "FAILED"
                logger.info(f"  [{status}] {update['name']}: {update['duration']:.2f}s")
                if update.get('error'):
                    logger.info(f"          Error: {update['error']}")

        if self.dry_run:
            logger.info("\n[DRY RUN] No updates were actually executed")

        logger.info("=" * 80)


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Scheduled updates orchestrator for DarkHorses Masters Workers'
    )
    parser.add_argument(
        '--force-all',
        action='store_true',
        help='Force run all update types regardless of schedule'
    )
    parser.add_argument(
        '--update',
        type=str,
        help='Run a specific update only (e.g., daily_data, live_data)'
    )
    parser.add_argument(
        '--config',
        type=str,
        help='Path to scheduler config YAML file'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Dry-run mode (no actual updates executed)'
    )

    args = parser.parse_args()

    try:
        orchestrator = ScheduledUpdatesOrchestrator(
            config_path=args.config,
            dry_run=args.test
        )

        stats = orchestrator.run(
            force_all=args.force_all,
            specific_update=args.update
        )

        # Exit with appropriate code
        if stats.get('errors', 0) > 0:
            logger.warning("Orchestrator completed with errors")
            sys.exit(1)
        else:
            logger.info("Orchestrator completed successfully")
            sys.exit(0)

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
