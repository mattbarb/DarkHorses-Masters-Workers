"""
Monitor Backfill Progress
Displays real-time progress of the horse pedigree backfill operation
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import time
from datetime import datetime
from utils.supabase_client import SupabaseReferenceClient
from config.config import get_config


def format_duration(seconds):
    """Format duration in human readable format"""
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    secs = int(seconds % 60)
    return f"{hours}h {minutes}m {secs}s"


def monitor_backfill(checkpoint_file: str = None, refresh_interval: int = 60):
    """
    Monitor backfill progress

    Args:
        checkpoint_file: Path to checkpoint file
        refresh_interval: Seconds between updates (default: 60)
    """
    # Setup paths
    if checkpoint_file:
        checkpoint_path = Path(checkpoint_file)
    else:
        checkpoint_path = Path(__file__).parent.parent / 'logs' / 'backfill_checkpoint.json'

    error_log_path = Path(__file__).parent.parent / 'logs' / 'backfill_errors.json'

    # Setup database client
    config = get_config()
    db_client = SupabaseReferenceClient(
        url=config.supabase.url,
        service_key=config.supabase.service_key,
        batch_size=100
    )

    print("=" * 80)
    print("HORSE PEDIGREE BACKFILL MONITOR")
    print("=" * 80)
    print(f"Checkpoint file: {checkpoint_path}")
    print(f"Error log file: {error_log_path}")
    print(f"Refresh interval: {refresh_interval} seconds")
    print(f"Press Ctrl+C to exit")
    print("=" * 80)
    print()

    try:
        while True:
            # Clear screen (works on Unix/Linux/Mac)
            print("\033[2J\033[H", end="")

            print("=" * 80)
            print(f"BACKFILL PROGRESS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            print("=" * 80)

            # Check if checkpoint exists
            if not checkpoint_path.exists():
                print("\nNo checkpoint file found. Backfill may not have started yet.")
                print(f"Waiting for: {checkpoint_path}")
            else:
                # Load checkpoint
                try:
                    with open(checkpoint_path, 'r') as f:
                        checkpoint = json.load(f)

                    stats = checkpoint.get('stats', {})
                    processed_count = checkpoint.get('processed', 0)
                    last_update = checkpoint.get('timestamp', 'Unknown')

                    # Calculate progress metrics
                    total = stats.get('total', 0)
                    processed = stats.get('processed', 0)
                    with_pedigree = stats.get('with_pedigree', 0)
                    without_pedigree = stats.get('without_pedigree', 0)
                    errors = stats.get('errors', 0)

                    # Calculate progress percentage
                    progress_pct = (processed / total * 100) if total > 0 else 0

                    # Calculate time metrics
                    session_start = stats.get('session_start')
                    if session_start:
                        start_time = datetime.fromisoformat(session_start.replace('Z', '+00:00'))
                        elapsed = (datetime.utcnow() - start_time).total_seconds()
                        rate = processed / elapsed if elapsed > 0 else 0
                        remaining = (total - processed) / rate if rate > 0 else 0

                        # Calculate ETA
                        eta_timestamp = datetime.utcnow().timestamp() + remaining
                        eta_str = datetime.fromtimestamp(eta_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                    else:
                        elapsed = 0
                        rate = 0
                        remaining = 0
                        eta_str = "Unknown"

                    print(f"\nLast Update: {last_update}")
                    print(f"\nOVERALL PROGRESS:")
                    print(f"  Total horses: {total:,}")
                    print(f"  Processed: {processed:,} ({progress_pct:.1f}%)")
                    print(f"  Remaining: {total - processed:,}")
                    print()
                    print(f"RESULTS:")
                    print(f"  With pedigree: {with_pedigree:,} ({with_pedigree/processed*100 if processed > 0 else 0:.1f}%)")
                    print(f"  Without pedigree: {without_pedigree:,} ({without_pedigree/processed*100 if processed > 0 else 0:.1f}%)")
                    print(f"  Errors: {errors:,} ({errors/processed*100 if processed > 0 else 0:.1f}%)")
                    print()
                    print(f"TIMING:")
                    print(f"  Elapsed: {format_duration(elapsed)}")
                    print(f"  Rate: {rate:.2f} horses/sec ({rate * 60:.1f} horses/min)")
                    print(f"  Estimated remaining: {format_duration(remaining)}")
                    print(f"  ETA: {eta_str}")

                    # Progress bar
                    bar_width = 50
                    filled = int(bar_width * progress_pct / 100)
                    bar = '█' * filled + '░' * (bar_width - filled)
                    print(f"\n  [{bar}] {progress_pct:.1f}%")

                except Exception as e:
                    print(f"\nError reading checkpoint: {e}")

            # Check database state
            print("\n" + "=" * 80)
            print("DATABASE STATE")
            print("=" * 80)

            try:
                # Count enriched horses
                total_horses = db_client.client.table('ra_horses').select('horse_id', count='exact').execute().count
                enriched = db_client.client.table('ra_horses').select('horse_id', count='exact').not_.is_('dob', 'null').execute().count
                pedigree_count = db_client.client.table('ra_horse_pedigree').select('horse_id', count='exact').execute().count

                print(f"\nTotal horses in database: {total_horses:,}")
                print(f"Enriched (with dob): {enriched:,} ({enriched/total_horses*100:.1f}%)")
                print(f"Need enrichment: {total_horses - enriched:,}")
                print(f"Pedigree records: {pedigree_count:,}")

            except Exception as e:
                print(f"\nError querying database: {e}")

            # Check for errors
            if error_log_path.exists():
                try:
                    with open(error_log_path, 'r') as f:
                        errors = json.load(f)
                    print(f"\nTotal errors logged: {len(errors)}")
                    if len(errors) > 0:
                        print(f"Most recent error: {errors[-1].get('error', 'Unknown')[:80]}")
                except Exception as e:
                    print(f"\nError reading error log: {e}")

            print("\n" + "=" * 80)
            print(f"Next update in {refresh_interval} seconds... (Ctrl+C to exit)")
            print("=" * 80)

            # Wait for next update
            time.sleep(refresh_interval)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Monitor horse pedigree backfill progress')
    parser.add_argument('--checkpoint-file', type=str, help='Custom checkpoint file path')
    parser.add_argument('--interval', type=int, default=60, help='Refresh interval in seconds (default: 60)')

    args = parser.parse_args()

    monitor_backfill(checkpoint_file=args.checkpoint_file, refresh_interval=args.interval)


if __name__ == '__main__':
    main()
