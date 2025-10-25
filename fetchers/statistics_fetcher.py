#!/usr/bin/env python3
"""
Statistics Fetcher
==================

Wrapper for statistics update operations to integrate with main.py orchestrator.

This fetcher coordinates the daily statistics update for jockeys, trainers, and owners.
It uses the DailyStatisticsUpdater which implements smart incremental updates.

Usage from main.py:
    python3 main.py --entities statistics

Direct usage:
    python3 scripts/statistics_workers/daily_statistics_update.py --all

Author: Claude Code
Date: 2025-10-19
"""

import sys
import os
from datetime import datetime
from typing import Dict

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('statistics_fetcher')


class StatisticsFetcher:
    """
    Statistics fetcher that wraps daily_statistics_update.py for main.py integration
    """

    def __init__(self):
        """Initialize fetcher"""
        self.config = get_config()
        self.db_client = SupabaseReferenceClient(
            url=self.config.supabase.url,
            service_key=self.config.supabase.service_key
        )

    def fetch_and_store(self, recent_only: bool = True, entities: list = None) -> Dict:
        """
        Update statistics for entities

        Args:
            recent_only: If True, only update entities with recent activity (default: True, faster)
            entities: List of entity types to update (default: ['jockeys', 'trainers', 'owners'])

        Returns:
            Dictionary with success status and statistics
        """
        logger.info("Starting statistics update...")

        if entities is None:
            entities = ['jockeys', 'trainers', 'owners']

        try:
            # Import DailyStatisticsUpdater
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'scripts', 'statistics_workers'))
            from daily_statistics_update import DailyStatisticsUpdater

            # Initialize updater
            updater = DailyStatisticsUpdater(self.db_client, dry_run=False)

            # Check if position data is available
            if not updater.use_database:
                logger.error("Position data not available - cannot update statistics")
                logger.error("Run results fetcher first: python3 main.py --entities results")
                return {
                    'success': False,
                    'error': 'Position data not available - run results fetcher first',
                    'fetched': 0,
                    'inserted': 0
                }

            # Update each entity type
            start_time = datetime.utcnow()
            total_updated = 0

            for entity_type in entities:
                logger.info(f"\nUpdating {entity_type}...")
                updater.update_entity_type(entity_type, recent_only=recent_only)

                # Count updates
                stats = updater.stats[entity_type]
                entity_total = stats['recent_form'] + stats['last_dates'] + stats['lifetime']
                total_updated += entity_total

                logger.info(f"  {entity_type}: {entity_total} total updates ({stats['errors']} errors)")

            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            # Build summary
            summary = {
                'success': True,
                'fetched': total_updated,  # Number of entities processed
                'inserted': total_updated,  # Number of entities updated
                'duration_seconds': duration,
                'entities_updated': {}
            }

            for entity_type in entities:
                stats = updater.stats[entity_type]
                summary['entities_updated'][entity_type] = {
                    'recent_form': stats['recent_form'],
                    'last_dates': stats['last_dates'],
                    'lifetime': stats['lifetime'],
                    'errors': stats['errors']
                }

            logger.info(f"\nStatistics update complete: {total_updated} entities updated in {duration:.1f}s")
            return summary

        except Exception as e:
            logger.error(f"Statistics update failed: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'fetched': 0,
                'inserted': 0
            }


def main():
    """Main entry point for testing"""
    logger.info("=" * 80)
    logger.info("STATISTICS FETCHER TEST")
    logger.info("=" * 80)

    fetcher = StatisticsFetcher()
    result = fetcher.fetch_and_store(recent_only=True)

    logger.info("\n" + "=" * 80)
    logger.info("RESULT")
    logger.info("=" * 80)
    logger.info(f"Success: {result['success']}")
    logger.info(f"Updated: {result['inserted']}")
    if not result['success']:
        logger.info(f"Error: {result.get('error')}")
    logger.info("=" * 80)


if __name__ == '__main__':
    main()
