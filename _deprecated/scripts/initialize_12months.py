#!/usr/bin/env python3
"""
12-Month Initialization Script
Backfills data from last 12 months (API limit) + reference data

Run this on Render.com or locally to populate database with recent data.

Usage:
    python3 initialize_12months.py
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

# Add current directory to path
sys.path.append(str(Path(__file__).parent))

from config.config import get_config
from utils.logger import get_logger
from main import ReferenceDataOrchestrator

logger = get_logger('initialize_12months')


def main():
    """Run 12-month initialization"""
    logger.info("=" * 80)
    logger.info("DARKHORSES MASTERS WORKER - 12 MONTH INITIALIZATION")
    logger.info("=" * 80)
    logger.info("This script initializes the database with:")
    logger.info("  1. Reference data (courses, bookmakers)")
    logger.info("  2. Last 12 months of races & results")
    logger.info("=" * 80)

    orchestrator = ReferenceDataOrchestrator()
    overall_start = time.time()

    # Calculate 12 month date range
    end_date = datetime.utcnow().date()
    start_date = end_date - timedelta(days=365)

    logger.info(f"\nDate range: {start_date} to {end_date}")
    logger.info(f"Total days: {(end_date - start_date).days}")

    # PHASE 1: Reference Data
    logger.info("\n" + "▶" * 80)
    logger.info("PHASE 1: REFERENCE DATA (Courses & Bookmakers)")
    logger.info("▶" * 80 + "\n")

    try:
        result = orchestrator.run_fetch(entities=['courses', 'bookmakers'])
        logger.info(f"\n✅ Reference data complete")
        logger.info(f"   Courses: {result['courses']['inserted']} records")
        logger.info(f"   Bookmakers: {result['bookmakers']['inserted']} records")
    except Exception as e:
        logger.error(f"❌ Reference data failed: {e}")

    # PHASE 2: Historical Races & Results (12 months in 30-day chunks)
    logger.info("\n" + "▶" * 80)
    logger.info("PHASE 2: HISTORICAL RACES & RESULTS (Last 12 Months)")
    logger.info("▶" * 80 + "\n")

    # Process in 30-day chunks
    CHUNK_DAYS = 30
    chunks = []
    current = start_date

    while current <= end_date:
        chunk_end = min(current + timedelta(days=CHUNK_DAYS - 1), end_date)
        chunks.append((current, chunk_end))
        current = chunk_end + timedelta(days=1)

    logger.info(f"Processing {len(chunks)} chunks of ~{CHUNK_DAYS} days each\n")

    total_races = 0
    total_results = 0

    for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
        logger.info(f"\n{'=' * 80}")
        logger.info(f"CHUNK {i}/{len(chunks)}: {chunk_start} to {chunk_end}")
        logger.info(f"{'=' * 80}")

        custom_configs = {
            'races': {
                'start_date': chunk_start.strftime('%Y-%m-%d'),
                'end_date': chunk_end.strftime('%Y-%m-%d'),
                'region_codes': ['gb', 'ire']
            },
            'results': {
                'start_date': chunk_start.strftime('%Y-%m-%d'),
                'end_date': chunk_end.strftime('%Y-%m-%d'),
                'region_codes': ['gb', 'ire']
            }
        }

        try:
            result = orchestrator.run_fetch(
                entities=['races', 'results'],
                custom_configs=custom_configs
            )

            races_inserted = result.get('races', {}).get('inserted', 0)
            results_inserted = result.get('results', {}).get('inserted', 0)

            total_races += races_inserted
            total_results += results_inserted

            logger.info(f"\n✅ Chunk {i} complete:")
            logger.info(f"   Races: {races_inserted} records")
            logger.info(f"   Results: {results_inserted} records")

            # Progress
            days_done = (chunk_end - start_date).days + 1
            total_days = (end_date - start_date).days + 1
            progress = (days_done / total_days) * 100

            logger.info(f"\n📊 Overall Progress: {days_done}/{total_days} days ({progress:.1f}%)")
            logger.info(f"   Total races so far: {total_races:,}")
            logger.info(f"   Total results so far: {total_results:,}")

        except Exception as e:
            logger.error(f"❌ Chunk {i} failed: {e}")

        # Brief pause between chunks
        if i < len(chunks):
            logger.info("⏸️  Pausing 3 seconds...")
            time.sleep(3)

    # SUMMARY
    duration = time.time() - overall_start

    logger.info("\n" + "=" * 80)
    logger.info("INITIALIZATION COMPLETE")
    logger.info("=" * 80)
    logger.info(f"Total duration: {duration:.2f} seconds ({duration/60:.2f} minutes)")
    logger.info(f"\n📊 Final Results:")
    logger.info(f"   Date range: {start_date} to {end_date}")
    logger.info(f"   Races: {total_races:,} records")
    logger.info(f"   Results: {total_results:,} records")
    logger.info("\n🎉 Database initialization complete!")
    logger.info("=" * 80)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("\n⏹️  Initialization cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)
