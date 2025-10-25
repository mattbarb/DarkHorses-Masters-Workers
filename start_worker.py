#!/usr/bin/env python3
"""
Render.com Worker - Scheduled Racing API Data Fetcher
Runs as a long-running worker process with scheduled tasks
"""

import sys
import time
import schedule
from datetime import datetime

from config.config import get_config
from utils.logger import get_logger
from utils.supabase_client import SupabaseReferenceClient
from main import ReferenceDataOrchestrator

logger = get_logger('render_worker')


def update_entity_statistics():
    """Update entity statistics (jockeys, trainers, owners)"""
    logger.info("-" * 80)
    logger.info("UPDATING ENTITY STATISTICS")
    logger.info("-" * 80)

    try:
        config = get_config()
        db_client = SupabaseReferenceClient(
            url=config.supabase.url,
            service_key=config.supabase.service_key
        )

        # Call the database function to update statistics
        logger.info("Calling update_entity_statistics() function...")
        result = db_client.client.rpc('update_entity_statistics').execute()

        if result.data:
            stats = result.data[0] if isinstance(result.data, list) else result.data
            jockeys = stats.get('jockeys_updated', 0)
            trainers = stats.get('trainers_updated', 0)
            owners = stats.get('owners_updated', 0)

            logger.info(f"✓ Jockeys updated:  {jockeys:,}")
            logger.info(f"✓ Trainers updated: {trainers:,}")
            logger.info(f"✓ Owners updated:   {owners:,}")
            logger.info("Entity statistics update completed successfully")
        else:
            logger.warning("Statistics update returned no data")

    except Exception as e:
        # Log error but don't fail the entire daily run
        logger.error(f"Entity statistics update failed: {e}", exc_info=True)
        logger.warning("Continuing despite statistics update failure (will retry on next run)")

    logger.info("-" * 80)


def run_daily_fetch():
    """Run daily fetch: races and results"""
    logger.info("=" * 80)
    logger.info(f"DAILY FETCH TRIGGERED - {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)

    try:
        orchestrator = ReferenceDataOrchestrator()
        results = orchestrator.run_fetch(entities=['races', 'results'])

        success = all(r.get('success', False) for r in results.values())

        # Log summary of downloaded records
        logger.info("\n" + "=" * 80)
        logger.info("DAILY FETCH SUMMARY")
        logger.info("=" * 80)

        for entity, result in results.items():
            if entity == 'races':
                races_fetched = result.get('races_fetched', result.get('fetched', 0))
                runners_fetched = result.get('runners_fetched', 0)
                races_inserted = result.get('races_inserted', result.get('inserted', 0))
                runners_inserted = result.get('runners_inserted', 0)
                logger.info(f"Races:   {races_fetched} fetched, {races_inserted} new/updated")
                logger.info(f"Runners: {runners_fetched} fetched, {runners_inserted} new/updated")
            elif entity == 'results':
                results_fetched = result.get('fetched', 0)
                results_inserted = result.get('inserted', 0)
                days_fetched = result.get('days_fetched', 0)
                days_with_data = result.get('days_with_data', 0)
                logger.info(f"Results: {results_fetched} fetched, {results_inserted} new/updated")
                logger.info(f"         {days_with_data}/{days_fetched} days had data")

        logger.info("=" * 80)

        if success:
            logger.info("Daily fetch completed successfully")

            # Update entity statistics after successful fetch
            logger.info("\nUpdating entity statistics with new data...")
            update_entity_statistics()
        else:
            logger.error("Daily fetch completed with errors")

    except Exception as e:
        logger.error(f"Daily fetch failed: {e}", exc_info=True)


def run_weekly_fetch():
    """Run weekly fetch: horses (jockeys/trainers/owners auto-extracted from daily races)"""
    logger.info("=" * 80)
    logger.info(f"WEEKLY FETCH TRIGGERED - {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)

    try:
        orchestrator = ReferenceDataOrchestrator()
        results = orchestrator.run_fetch(
            entities=['horses']  # jockeys, trainers, owners are auto-extracted during daily race fetching
        )

        success = all(r.get('success', False) for r in results.values())

        # Log summary of downloaded records
        logger.info("\n" + "=" * 80)
        logger.info("WEEKLY FETCH SUMMARY")
        logger.info("=" * 80)

        for entity, result in results.items():
            fetched = result.get('fetched', 0)
            inserted = result.get('inserted', 0)
            logger.info(f"{entity.capitalize()}: {fetched} fetched, {inserted} new/updated")

        logger.info("=" * 80)

        if success:
            logger.info("Weekly fetch completed successfully")

            # Update entity statistics after successful fetch
            logger.info("\nUpdating entity statistics with new data...")
            update_entity_statistics()
        else:
            logger.error("Weekly fetch completed with errors")

    except Exception as e:
        logger.error(f"Weekly fetch failed: {e}", exc_info=True)


def run_monthly_fetch():
    """Run monthly fetch: courses and bookmakers"""
    logger.info("=" * 80)
    logger.info(f"MONTHLY FETCH TRIGGERED - {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)

    try:
        orchestrator = ReferenceDataOrchestrator()
        results = orchestrator.run_fetch(
            entities=['courses', 'bookmakers']
        )

        success = all(r.get('success', False) for r in results.values())

        # Log summary of downloaded records
        logger.info("\n" + "=" * 80)
        logger.info("MONTHLY FETCH SUMMARY")
        logger.info("=" * 80)

        for entity, result in results.items():
            fetched = result.get('fetched', 0)
            inserted = result.get('inserted', 0)
            logger.info(f"{entity.capitalize()}: {fetched} fetched, {inserted} new/updated")

        logger.info("=" * 80)

        if success:
            logger.info("Monthly fetch completed successfully")
        else:
            logger.error("Monthly fetch completed with errors")

    except Exception as e:
        logger.error(f"Monthly fetch failed: {e}", exc_info=True)


def run_initial_sync():
    """Run initial full sync on first startup"""
    logger.info("=" * 80)
    logger.info("INITIAL SYNC - Fetching all entities")
    logger.info("=" * 80)

    try:
        orchestrator = ReferenceDataOrchestrator()
        results = orchestrator.run_fetch(entities=None)  # Fetch all

        success = all(r.get('success', False) for r in results.values())
        if success:
            logger.info("Initial sync completed successfully")
        else:
            logger.error("Initial sync completed with errors")

    except Exception as e:
        logger.error(f"Initial sync failed: {e}", exc_info=True)


def main():
    """Main worker process"""
    logger.info("=" * 80)
    logger.info("RACING API MASTERS - RENDER WORKER")
    logger.info(f"Started at: {datetime.utcnow().isoformat()}")
    logger.info("=" * 80)

    # Run initial sync on startup (optional - comment out if not needed)
    # logger.info("\nRunning initial sync...")
    # run_initial_sync()

    # Schedule jobs
    logger.info("\nScheduling jobs...")

    # Daily: 1:00 AM UTC
    schedule.every().day.at("01:00").do(run_daily_fetch)
    logger.info("  ✓ Daily fetch: 01:00 UTC (races, results + statistics update)")

    # Weekly: Sunday 2:00 AM UTC
    schedule.every().sunday.at("02:00").do(run_weekly_fetch)
    logger.info("  ✓ Weekly fetch: Sunday 02:00 UTC (horses only - jockeys/trainers/owners auto-extracted daily)")

    # Monthly: 1st day at 3:00 AM UTC (approximated with weekly check)
    schedule.every().monday.at("03:00").do(
        lambda: run_monthly_fetch() if datetime.utcnow().day <= 7 else None
    )
    logger.info("  ✓ Monthly fetch: First Monday 03:00 UTC (courses, bookmakers)")

    logger.info("\nWorker running. Press Ctrl+C to stop.")
    logger.info("=" * 80)

    # Keep worker running
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute

    except KeyboardInterrupt:
        logger.info("\nWorker stopped by user")
    except Exception as e:
        logger.error(f"Worker crashed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
