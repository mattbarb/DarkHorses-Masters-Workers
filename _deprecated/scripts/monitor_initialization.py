#!/usr/bin/env python3
"""
Real-time Initialization Monitor
Displays progress of historical data backfill across all tables
"""

import time
import re
import os
import sys
from datetime import datetime
from pathlib import Path

# ANSI color codes
GREEN = '\033[92m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
CYAN = '\033[96m'
RED = '\033[91m'
BOLD = '\033[1m'
RESET = '\033[0m'

def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def format_number(num):
    """Format number with thousands separator"""
    return f"{num:,}"

def parse_log_file(log_path):
    """Parse log file and extract statistics"""
    stats = {
        'phase': 'Starting',
        'current_chunk': 0,
        'total_chunks': 44,
        'current_date': None,
        'tables': {
            'ra_courses': {'inserted': 0, 'status': 'pending'},
            'ra_bookmakers': {'inserted': 0, 'status': 'pending'},
            'ra_jockeys': {'inserted': 0, 'status': 'pending'},
            'ra_trainers': {'inserted': 0, 'status': 'pending'},
            'ra_owners': {'inserted': 0, 'status': 'pending'},
            'ra_horses': {'inserted': 0, 'status': 'pending'},
            'ra_races': {'inserted': 0, 'status': 'pending'},
            'ra_results': {'inserted': 0, 'status': 'pending'},
        },
        'start_time': None,
        'last_update': None,
        'total_api_calls': 0,
        'rate_limits': 0
    }

    if not Path(log_path).exists():
        return stats

    with open(log_path, 'r') as f:
        lines = f.readlines()

    for line in lines:
        # Phase detection
        if 'PHASE 1: REFERENCE DATA' in line:
            stats['phase'] = 'Phase 1: Reference Data'
        elif 'PHASE 2: HISTORICAL' in line:
            stats['phase'] = 'Phase 2: Historical Backfill'
        elif 'INITIALIZATION COMPLETE' in line:
            stats['phase'] = 'Complete'

        # Start time
        if 'Started at:' in line and not stats['start_time']:
            match = re.search(r'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})', line)
            if match:
                stats['start_time'] = match.group(1)

        # Chunk progress
        if 'CHUNK' in line and '/' in line:
            match = re.search(r'CHUNK (\d+)/(\d+)', line)
            if match:
                stats['current_chunk'] = int(match.group(1))
                stats['total_chunks'] = int(match.group(2))

        # Current date being processed
        if 'Fetching racecards for' in line:
            match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if match:
                stats['current_date'] = match.group(1)
                stats['last_update'] = datetime.now().strftime('%H:%M:%S')

        if 'Fetching results for' in line:
            match = re.search(r'(\d{4}-\d{2}-\d{2})', line)
            if match:
                stats['current_date'] = match.group(1)
                stats['last_update'] = datetime.now().strftime('%H:%M:%S')

        # Table insertions
        if '[SUCCESS] courses' in line and 'Inserted:' in line:
            match = re.search(r'Inserted:\s+(\d+)', line)
            if match:
                stats['tables']['ra_courses']['inserted'] = int(match.group(1))
                stats['tables']['ra_courses']['status'] = 'complete'

        if '[SUCCESS] bookmakers' in line and 'Inserted:' in line:
            match = re.search(r'Inserted:\s+(\d+)', line)
            if match:
                stats['tables']['ra_bookmakers']['inserted'] = int(match.group(1))
                stats['tables']['ra_bookmakers']['status'] = 'complete'

        # Races and results (accumulate across chunks)
        if 'Total races fetched:' in line:
            match = re.search(r'Total races fetched:\s+(\d+)', line)
            if match:
                races = int(match.group(1))
                if races > 0:
                    stats['tables']['ra_races']['inserted'] += races
                    stats['tables']['ra_races']['status'] = 'processing'

        if 'Total results fetched:' in line:
            match = re.search(r'Total results fetched:\s+(\d+)', line)
            if match:
                results = int(match.group(1))
                if results > 0:
                    stats['tables']['ra_results']['inserted'] += results
                    stats['tables']['ra_results']['status'] = 'processing'

        # Rate limiting
        if 'Rate limited' in line:
            stats['rate_limits'] += 1

    return stats

def draw_progress_bar(current, total, width=40):
    """Draw a progress bar"""
    if total == 0:
        return "[" + " " * width + "] 0%"

    progress = current / total
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    percentage = progress * 100
    return f"[{bar}] {percentage:.1f}%"

def display_dashboard(stats):
    """Display monitoring dashboard"""
    clear_screen()

    # Header
    print(f"{BOLD}{CYAN}{'=' * 80}{RESET}")
    print(f"{BOLD}{CYAN}DARKHORSES MASTERS WORKER - INITIALIZATION MONITOR{RESET}")
    print(f"{BOLD}{CYAN}{'=' * 80}{RESET}\n")

    # Current status
    print(f"{BOLD}Current Phase:{RESET} {YELLOW}{stats['phase']}{RESET}")
    if stats['start_time']:
        print(f"{BOLD}Started:{RESET} {stats['start_time']}")
    if stats['last_update']:
        print(f"{BOLD}Last Update:{RESET} {stats['last_update']}")
    print()

    # Chunk progress
    if stats['current_chunk'] > 0:
        print(f"{BOLD}Chunk Progress:{RESET}")
        progress_bar = draw_progress_bar(stats['current_chunk'], stats['total_chunks'])
        print(f"  {progress_bar} ({stats['current_chunk']}/{stats['total_chunks']} chunks)")
        if stats['current_date']:
            print(f"  {BOLD}Processing:{RESET} {stats['current_date']}")
        print()

    # Table statistics
    print(f"{BOLD}{GREEN}{'─' * 80}{RESET}")
    print(f"{BOLD}TABLE STATISTICS{RESET}")
    print(f"{BOLD}{GREEN}{'─' * 80}{RESET}\n")

    # Reference tables
    print(f"{BOLD}{BLUE}Reference Data (Phase 1):{RESET}")
    for table in ['ra_courses', 'ra_bookmakers', 'ra_jockeys', 'ra_trainers', 'ra_owners', 'ra_horses']:
        data = stats['tables'][table]
        status_icon = {
            'complete': f'{GREEN}✓{RESET}',
            'processing': f'{YELLOW}●{RESET}',
            'pending': f'{RED}○{RESET}'
        }.get(data['status'], f'{RED}○{RESET}')

        print(f"  {status_icon} {table:<20} {format_number(data['inserted']):>10} records")

    print()

    # Historical tables
    print(f"{BOLD}{BLUE}Historical Data (Phase 2):{RESET}")
    for table in ['ra_races', 'ra_results']:
        data = stats['tables'][table]
        status_icon = {
            'complete': f'{GREEN}✓{RESET}',
            'processing': f'{YELLOW}●{RESET}',
            'pending': f'{RED}○{RESET}'
        }.get(data['status'], f'{RED}○{RESET}')

        print(f"  {status_icon} {table:<20} {format_number(data['inserted']):>10} records")

    print()

    # Performance metrics
    if stats['rate_limits'] > 0:
        print(f"{BOLD}Performance Metrics:{RESET}")
        print(f"  Rate limit pauses: {stats['rate_limits']}")
        print()

    # Footer
    print(f"{BOLD}{CYAN}{'─' * 80}{RESET}")
    print(f"{CYAN}Press Ctrl+C to exit monitor (initialization will continue){RESET}")
    print(f"{BOLD}{CYAN}{'─' * 80}{RESET}")

def main():
    """Main monitoring loop"""
    log_path = '/Users/matthewbarber/Documents/GitHub/DarkHorses-Masters-Workers/logs/initialization_fixed.log'

    print(f"{BOLD}Starting initialization monitor...{RESET}")
    print(f"Watching: {log_path}")
    time.sleep(2)

    try:
        while True:
            stats = parse_log_file(log_path)
            display_dashboard(stats)

            # Exit if complete
            if stats['phase'] == 'Complete':
                print(f"\n{GREEN}{BOLD}✓ Initialization complete!{RESET}\n")
                break

            time.sleep(2)  # Update every 2 seconds

    except KeyboardInterrupt:
        print(f"\n\n{YELLOW}Monitor stopped. Initialization continues in background.{RESET}")
        print(f"To resume monitoring, run: {BOLD}python3 monitor_initialization.py{RESET}\n")
        sys.exit(0)

if __name__ == '__main__':
    main()
