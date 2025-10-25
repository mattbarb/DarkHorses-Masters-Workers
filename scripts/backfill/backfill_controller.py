"""
Backfill Controller - Master Orchestrator

This script manages both the fast backfill and enrichment processes,
providing a unified progress dashboard with real-time statistics.

USAGE:
    # Run both backfill and enrichment in parallel
    python3 scripts/backfill_controller.py --start-date 2015-01-01

    # Resume both processes from checkpoints
    python3 scripts/backfill_controller.py --resume

    # Monitor only (don't start processes)
    python3 scripts/backfill_controller.py --monitor-only
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import os
import subprocess
import time
import json
import signal
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from utils.logger import get_logger

logger = get_logger('backfill_controller')


class BackfillController:
    """Master controller for backfill and enrichment processes"""

    def __init__(self):
        self.base_dir = Path(__file__).parent.parent
        self.logs_dir = self.base_dir / 'logs'

        # Process tracking
        self.backfill_pid = None
        self.enrichment_pid = None

        # Checkpoint files
        self.backfill_checkpoint = self.logs_dir / 'backfill_all_tables_checkpoint.json'
        self.enrichment_checkpoint = self.logs_dir / 'enrichment_checkpoint.json'

        # PID files
        self.backfill_pid_file = self.logs_dir / 'backfill_pid.txt'
        self.enrichment_pid_file = self.logs_dir / 'enrichment_pid.txt'

        # Log files
        self.backfill_log = self.logs_dir / 'backfill_fast_2015_full.log'
        self.enrichment_log = self.logs_dir / 'enrichment_full.log'

    def check_process(self, pid: int) -> bool:
        """Check if process is running"""
        try:
            os.kill(pid, 0)
            return True
        except OSError:
            return False

    def load_backfill_progress(self) -> Optional[Dict]:
        """Load backfill checkpoint"""
        if self.backfill_checkpoint.exists():
            try:
                with open(self.backfill_checkpoint, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading backfill checkpoint: {e}")
        return None

    def load_enrichment_progress(self) -> Optional[Dict]:
        """Load enrichment checkpoint"""
        if self.enrichment_checkpoint.exists():
            try:
                with open(self.enrichment_checkpoint, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading enrichment checkpoint: {e}")
        return None

    def get_process_status(self) -> Tuple[bool, bool]:
        """
        Get status of both processes

        Returns:
            Tuple of (backfill_running, enrichment_running)
        """
        backfill_running = False
        enrichment_running = False

        # Check backfill
        if self.backfill_pid_file.exists():
            try:
                with open(self.backfill_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    backfill_running = self.check_process(pid)
                    if backfill_running:
                        self.backfill_pid = pid
            except:
                pass

        # Check enrichment
        if self.enrichment_pid_file.exists():
            try:
                with open(self.enrichment_pid_file, 'r') as f:
                    pid = int(f.read().strip())
                    enrichment_running = self.check_process(pid)
                    if enrichment_running:
                        self.enrichment_pid = pid
            except:
                pass

        return backfill_running, enrichment_running

    def start_backfill(self, start_date: str, resume: bool = False):
        """Start fast backfill process"""
        logger.info("Starting fast backfill process...")

        cmd = [
            'python3',
            'scripts/backfill_all_ra_tables_2015_2025.py',
            '--start-date', start_date,
            '--fast',
            '--non-interactive'
        ]

        if resume:
            cmd.append('--resume')

        # Start process in background
        process = subprocess.Popen(
            cmd,
            stdout=open(self.backfill_log, 'w'),
            stderr=subprocess.STDOUT,
            cwd=self.base_dir
        )

        self.backfill_pid = process.pid

        # Save PID
        with open(self.backfill_pid_file, 'w') as f:
            f.write(str(self.backfill_pid))

        logger.info(f"Backfill started with PID {self.backfill_pid}")
        return self.backfill_pid

    def start_enrichment(self, resume: bool = False):
        """Start enrichment process"""
        logger.info("Starting enrichment process...")

        cmd = [
            'python3',
            'scripts/enrich_entities_local_batch.py'
        ]

        if resume:
            cmd.append('--resume')

        # Start process in background
        process = subprocess.Popen(
            cmd,
            stdout=open(self.enrichment_log, 'w'),
            stderr=subprocess.STDOUT,
            cwd=self.base_dir
        )

        self.enrichment_pid = process.pid

        # Save PID
        with open(self.enrichment_pid_file, 'w') as f:
            f.write(str(self.enrichment_pid))

        logger.info(f"Enrichment started with PID {self.enrichment_pid}")
        return self.enrichment_pid

    def stop_processes(self):
        """Stop both processes gracefully"""
        logger.info("Stopping processes...")

        if self.backfill_pid and self.check_process(self.backfill_pid):
            logger.info(f"Stopping backfill (PID {self.backfill_pid})")
            os.kill(self.backfill_pid, signal.SIGTERM)

        if self.enrichment_pid and self.check_process(self.enrichment_pid):
            logger.info(f"Stopping enrichment (PID {self.enrichment_pid})")
            os.kill(self.enrichment_pid, signal.SIGTERM)

    def calculate_eta(self, processed: int, total: int, start_time: str) -> Tuple[str, float]:
        """
        Calculate ETA

        Returns:
            Tuple of (eta_string, hours_remaining)
        """
        if processed == 0:
            return "Calculating...", 0.0

        try:
            start = datetime.fromisoformat(start_time)
            elapsed = (datetime.utcnow() - start).total_seconds()
            rate = processed / elapsed if elapsed > 0 else 0
            remaining = total - processed
            remaining_seconds = remaining / rate if rate > 0 else 0

            eta = datetime.utcnow() + timedelta(seconds=remaining_seconds)
            eta_str = eta.strftime('%Y-%m-%d %H:%M')
            hours_remaining = remaining_seconds / 3600

            return eta_str, hours_remaining
        except:
            return "Unknown", 0.0

    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable form"""
        if seconds < 60:
            return f"{seconds:.0f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}m"
        elif seconds < 86400:
            return f"{seconds/3600:.1f}h"
        else:
            return f"{seconds/86400:.1f}d"

    def display_progress(self):
        """Display unified progress dashboard"""
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')

        # Get process status
        backfill_running, enrichment_running = self.get_process_status()

        # Load progress
        backfill_progress = self.load_backfill_progress()
        enrichment_progress = self.load_enrichment_progress()

        # Print header
        print("=" * 80)
        print("BACKFILL CONTROLLER - LIVE DASHBOARD".center(80))
        print("=" * 80)
        print()

        # Backfill section
        print("┌─ FAST BACKFILL (Data Collection) " + "─" * 44 + "┐")

        if backfill_running:
            status_icon = "🟢 RUNNING"
            if backfill_progress:
                stats = backfill_progress.get('stats', {})
                total_dates = stats.get('total_dates', 3943)
                processed_dates = stats.get('dates_processed', 0)
                races = stats.get('races_processed', 0)
                runners = stats.get('runners_processed', 0)
                start_time = stats.get('start_time', '')

                percent = (processed_dates / total_dates * 100) if total_dates > 0 else 0
                eta, hours_left = self.calculate_eta(processed_dates, total_dates, start_time)

                # Progress bar
                bar_width = 50
                filled = int(bar_width * processed_dates / total_dates)
                bar = "█" * filled + "░" * (bar_width - filled)

                print(f"│ Status: {status_icon}  PID: {self.backfill_pid}")
                print(f"│ Progress: [{bar}] {percent:.1f}%")
                print(f"│")
                print(f"│ Dates:   {processed_dates:,} / {total_dates:,}")
                print(f"│ Races:   {races:,}")
                print(f"│ Runners: {runners:,}")
                print(f"│")
                print(f"│ Time Remaining: {hours_left:.1f}h")
                print(f"│ ETA: {eta}")
            else:
                print(f"│ Status: {status_icon}  PID: {self.backfill_pid}")
                print(f"│ Progress: Starting...")
        else:
            status_icon = "⚪ NOT RUNNING"
            print(f"│ Status: {status_icon}")
            if backfill_progress:
                stats = backfill_progress.get('stats', {})
                processed = stats.get('dates_processed', 0)
                total = stats.get('total_dates', 3943)
                percent = (processed / total * 100) if total > 0 else 0
                print(f"│ Last checkpoint: {processed:,} / {total:,} dates ({percent:.1f}%)")

        print("└" + "─" * 78 + "┘")
        print()

        # Enrichment section
        print("┌─ ENTITY ENRICHMENT (Pedigree Data) " + "─" * 41 + "┐")

        if enrichment_running:
            status_icon = "🟢 RUNNING"
            if enrichment_progress:
                stats = enrichment_progress.get('stats', {})
                runners_processed = stats.get('runners_processed', 0)
                horses_enriched = stats.get('horses_enriched', 0)
                pedigrees = stats.get('pedigrees_captured', 0)
                start_time = stats.get('start_time', '')

                # Estimate total based on backfill progress
                total_runners = backfill_progress.get('stats', {}).get('runners_processed', 0) if backfill_progress else 0
                percent = (runners_processed / total_runners * 100) if total_runners > 0 else 0

                # Progress bar
                bar_width = 50
                filled = int(bar_width * min(runners_processed, total_runners) / max(total_runners, 1))
                bar = "█" * filled + "░" * (bar_width - filled)

                print(f"│ Status: {status_icon}  PID: {self.enrichment_pid}")
                print(f"│ Progress: [{bar}] {percent:.1f}%")
                print(f"│")
                print(f"│ Runners Processed: {runners_processed:,}")
                print(f"│ Horses Enriched:   {horses_enriched:,}")
                print(f"│ Pedigrees:         {pedigrees:,}")

                if total_runners > 0 and runners_processed > 0:
                    eta, hours_left = self.calculate_eta(runners_processed, total_runners, start_time)
                    print(f"│")
                    print(f"│ Time Remaining: {hours_left:.1f}h")
                    print(f"│ ETA: {eta}")
            else:
                print(f"│ Status: {status_icon}  PID: {self.enrichment_pid}")
                print(f"│ Progress: Starting...")
        else:
            status_icon = "⚪ NOT RUNNING"
            print(f"│ Status: {status_icon}")
            if enrichment_progress:
                stats = enrichment_progress.get('stats', {})
                runners = stats.get('runners_processed', 0)
                horses = stats.get('horses_enriched', 0)
                print(f"│ Last checkpoint: {runners:,} runners, {horses:,} horses enriched")

        print("└" + "─" * 78 + "┘")
        print()

        # Overall status
        print("┌─ OVERALL STATUS " + "─" * 61 + "┐")

        if backfill_running and enrichment_running:
            print("│ 🚀 Both processes running in parallel")
        elif backfill_running:
            print("│ ⏳ Backfill running, enrichment not started")
        elif enrichment_running:
            print("│ ⏳ Enrichment running, backfill complete")
        else:
            print("│ ⏸️  No processes running")

        print("│")
        print("│ Commands:")
        print("│   Ctrl+C : Stop monitoring (processes continue in background)")
        print("│   Ctrl+\\ : Stop all processes and exit")
        print("└" + "─" * 78 + "┘")

        print()
        print(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

    def monitor_loop(self, refresh_interval: int = 10):
        """
        Main monitoring loop

        Args:
            refresh_interval: Seconds between updates
        """
        logger.info(f"Starting monitor loop (refresh every {refresh_interval}s)")

        try:
            while True:
                self.display_progress()

                # Check if both are complete
                backfill_running, enrichment_running = self.get_process_status()

                if not backfill_running and not enrichment_running:
                    backfill_progress = self.load_backfill_progress()
                    if backfill_progress:
                        stats = backfill_progress.get('stats', {})
                        if stats.get('dates_processed', 0) >= stats.get('total_dates', 3943):
                            print("✅ All processes complete!")
                            break

                time.sleep(refresh_interval)

        except KeyboardInterrupt:
            print("\n\n⏸️  Monitoring stopped (processes continue in background)")
            print(f"   Backfill PID: {self.backfill_pid}")
            print(f"   Enrichment PID: {self.enrichment_pid}")
            print(f"\nTo resume monitoring: python3 scripts/backfill_controller.py --monitor-only")

        except Exception as e:
            logger.error(f"Error in monitor loop: {e}")
            raise

    def run(self, start_date: str, resume: bool = False, monitor_only: bool = False):
        """
        Main execution

        Args:
            start_date: Start date for backfill
            resume: Resume from checkpoints
            monitor_only: Only monitor, don't start processes
        """
        logger.info("=" * 80)
        logger.info("BACKFILL CONTROLLER STARTING")
        logger.info("=" * 80)

        if not monitor_only:
            # Check if processes are already running
            backfill_running, enrichment_running = self.get_process_status()

            # Start backfill if not running
            if not backfill_running:
                self.start_backfill(start_date, resume=resume)
                time.sleep(2)  # Give it time to start
            else:
                logger.info(f"Backfill already running (PID {self.backfill_pid})")

            # Start enrichment if not running
            if not enrichment_running:
                self.start_enrichment(resume=resume)
                time.sleep(2)  # Give it time to start
            else:
                logger.info(f"Enrichment already running (PID {self.enrichment_pid})")

        # Start monitoring
        self.monitor_loop()


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Master controller for backfill and enrichment processes',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start both processes from beginning
  python3 scripts/backfill_controller.py --start-date 2015-01-01

  # Resume both processes from checkpoints
  python3 scripts/backfill_controller.py --resume

  # Monitor existing processes
  python3 scripts/backfill_controller.py --monitor-only

  # Custom refresh interval (default 10s)
  python3 scripts/backfill_controller.py --monitor-only --refresh 5
        """
    )

    parser.add_argument('--start-date', type=str, default='2015-01-01',
                       help='Start date for backfill (YYYY-MM-DD)')
    parser.add_argument('--resume', action='store_true',
                       help='Resume from checkpoints')
    parser.add_argument('--monitor-only', action='store_true',
                       help='Only monitor existing processes')
    parser.add_argument('--refresh', type=int, default=10,
                       help='Dashboard refresh interval in seconds (default: 10)')

    args = parser.parse_args()

    controller = BackfillController()

    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n\n⚠️  Received shutdown signal")
        response = input("Stop all processes? (yes/no): ")
        if response.lower() == 'yes':
            controller.stop_processes()
            print("✅ Processes stopped")
            sys.exit(0)
        else:
            print("Processes continue in background")
            sys.exit(0)

    signal.signal(signal.SIGQUIT, signal_handler)

    # Run controller
    try:
        controller.run(
            start_date=args.start_date,
            resume=args.resume,
            monitor_only=args.monitor_only
        )
    except Exception as e:
        logger.error(f"Controller error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
