#!/usr/bin/env python3
"""
Unified Statistics Population Script
====================================

Purpose: Single script to calculate ALL statistics across ALL tables from 2015-01-01 to CURRENT_DATE
Database: 100% calculation from ra_mst_runners + ra_races (NO API calls)
Duration: ~45-60 minutes for all ~70,000 entities

Tables Updated:
1. ra_mst_jockeys (18 statistics columns)
2. ra_mst_trainers (18 statistics columns)
3. ra_mst_owners (19 statistics columns)
4. ra_mst_sires (38 statistics columns)
5. ra_mst_dams (38 statistics columns)
6. ra_mst_damsires (38 statistics columns)

Total: 167 statistics columns across 6 tables

Usage:
    # Full run (all tables, all entities, from 2015-01-01)
    python3 scripts/populate_all_statistics_from_database.py

    # Test mode (10 entities per table)
    python3 scripts/populate_all_statistics_from_database.py --test

    # Specific tables only
    python3 scripts/populate_all_statistics_from_database.py --tables jockeys trainers

    # Custom date range
    python3 scripts/populate_all_statistics_from_database.py --start-date 2020-01-01

    # Resume from checkpoint
    python3 scripts/populate_all_statistics_from_database.py --resume
"""

import sys
import os
import time
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.config import get_config
from utils.supabase_client import SupabaseReferenceClient
from utils.logger import get_logger

logger = get_logger('populate_all_statistics')


class UnifiedStatisticsPopulator:
    """Unified statistics calculator for all tables"""

    def __init__(self, test_mode: bool = False, start_date: str = '2015-01-01'):
        self.config = get_config()
        self.db = SupabaseReferenceClient(
            self.config.supabase.url,
            self.config.supabase.service_key
        )
        self.test_mode = test_mode
        self.start_date = start_date
        self.batch_size = 10 if test_mode else 100

        logger.info(f"Initialized UnifiedStatisticsPopulator")
        logger.info(f"Test mode: {test_mode}")
        logger.info(f"Start date: {start_date}")
        logger.info(f"Batch size: {self.batch_size}")

    # ========================================
    # JOCKEY STATISTICS
    # ========================================

    def calculate_jockey_statistics(self) -> Dict:
        """Calculate all jockey statistics from ra_mst_runners + ra_races"""
        logger.info("=" * 80)
        logger.info("CALCULATING JOCKEY STATISTICS")
        logger.info("=" * 80)

        start_time = time.time()

        # Get all jockeys
        jockeys_query = """
            SELECT id, name
            FROM ra_mst_jockeys
            WHERE id NOT LIKE '**TEST**%'
            ORDER BY id
        """
        if self.test_mode:
            jockeys_query += " LIMIT 10"

        result = self.db.execute_query(jockeys_query)
        jockeys = result.data if result.data else []

        logger.info(f"Processing {len(jockeys)} jockeys...")

        updated = 0
        for idx, jockey in enumerate(jockeys, 1):
            jockey_id = jockey['id']

            # Calculate statistics
            stats_query = f"""
                SELECT
                    -- Lifetime statistics
                    COUNT(*) as total_rides,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
                    COUNT(CASE WHEN r.position = 2 THEN 1 END) as total_seconds,
                    COUNT(CASE WHEN r.position = 3 THEN 1 END) as total_thirds,

                    -- Recent form (14-day window)
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days') as recent_14d_rides,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1) as recent_14d_wins,

                    -- Recent form (30-day window)
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days') as recent_30d_rides,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days' AND r.position = 1) as recent_30d_wins,

                    -- Last activity dates
                    MAX(rc.date) as last_ride_date,
                    MAX(CASE WHEN r.position = 1 THEN rc.date END) as last_win_date
                FROM ra_mst_runners r
                JOIN ra_races rc ON r.race_id = rc.id
                WHERE r.jockey_id = '{jockey_id}'
                  AND rc.date >= '{self.start_date}'
            """

            stats_result = self.db.execute_query(stats_query)
            if not stats_result.data or len(stats_result.data) == 0:
                continue

            stats = stats_result.data[0]

            # Calculate derived fields
            total_rides = stats.get('total_rides', 0) or 0
            total_wins = stats.get('total_wins', 0) or 0
            total_places = stats.get('total_places', 0) or 0
            recent_14d_rides = stats.get('recent_14d_rides', 0) or 0
            recent_14d_wins = stats.get('recent_14d_wins', 0) or 0
            recent_30d_rides = stats.get('recent_30d_rides', 0) or 0
            recent_30d_wins = stats.get('recent_30d_wins', 0) or 0

            win_rate = round((total_wins / total_rides * 100), 2) if total_rides > 0 else 0.0
            place_rate = round((total_places / total_rides * 100), 2) if total_rides > 0 else 0.0
            recent_14d_win_rate = round((recent_14d_wins / recent_14d_rides * 100), 2) if recent_14d_rides > 0 else 0.0
            recent_30d_win_rate = round((recent_30d_wins / recent_30d_rides * 100), 2) if recent_30d_rides > 0 else 0.0

            # Calculate days since
            from datetime import date
            today = date.today()
            last_ride_date = stats.get('last_ride_date')
            last_win_date = stats.get('last_win_date')

            days_since_last_ride = (today - last_ride_date).days if last_ride_date else None
            days_since_last_win = (today - last_win_date).days if last_win_date else None

            # Update database
            update_data = {
                'total_rides': total_rides,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': stats.get('total_seconds', 0) or 0,
                'total_thirds': stats.get('total_thirds', 0) or 0,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'recent_14d_rides': recent_14d_rides,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_rides': recent_30d_rides,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'last_ride_date': str(last_ride_date) if last_ride_date else None,
                'last_win_date': str(last_win_date) if last_win_date else None,
                'days_since_last_ride': days_since_last_ride,
                'days_since_last_win': days_since_last_win,
                'stats_updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db.client.table('ra_mst_jockeys').update(update_data).eq('id', jockey_id).execute()
            updated += 1

            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(jockeys)} jockeys ({updated} updated)")

        duration = time.time() - start_time
        logger.info(f"✅ Jockey statistics complete: {updated}/{len(jockeys)} updated in {duration:.1f}s")

        return {
            'table': 'ra_mst_jockeys',
            'total': len(jockeys),
            'updated': updated,
            'duration': duration
        }

    # ========================================
    # TRAINER STATISTICS
    # ========================================

    def calculate_trainer_statistics(self) -> Dict:
        """Calculate all trainer statistics from ra_mst_runners + ra_races"""
        logger.info("=" * 80)
        logger.info("CALCULATING TRAINER STATISTICS")
        logger.info("=" * 80)

        start_time = time.time()

        # Get all trainers
        trainers_query = """
            SELECT id, name
            FROM ra_mst_trainers
            WHERE id NOT LIKE '**TEST**%'
            ORDER BY id
        """
        if self.test_mode:
            trainers_query += " LIMIT 10"

        result = self.db.execute_query(trainers_query)
        trainers = result.data if result.data else []

        logger.info(f"Processing {len(trainers)} trainers...")

        updated = 0
        for idx, trainer in enumerate(trainers, 1):
            trainer_id = trainer['id']

            # Calculate statistics (same pattern as jockeys but with trainer_id)
            stats_query = f"""
                SELECT
                    COUNT(*) as total_runners,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
                    COUNT(CASE WHEN r.position = 2 THEN 1 END) as total_seconds,
                    COUNT(CASE WHEN r.position = 3 THEN 1 END) as total_thirds,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days') as recent_14d_runs,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1) as recent_14d_wins,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days') as recent_30d_runs,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days' AND r.position = 1) as recent_30d_wins,
                    MAX(rc.date) as last_runner_date,
                    MAX(CASE WHEN r.position = 1 THEN rc.date END) as last_win_date
                FROM ra_mst_runners r
                JOIN ra_races rc ON r.race_id = rc.id
                WHERE r.trainer_id = '{trainer_id}'
                  AND rc.date >= '{self.start_date}'
            """

            stats_result = self.db.execute_query(stats_query)
            if not stats_result.data or len(stats_result.data) == 0:
                continue

            stats = stats_result.data[0]

            # Calculate derived fields
            total_runners = stats.get('total_runners', 0) or 0
            total_wins = stats.get('total_wins', 0) or 0
            total_places = stats.get('total_places', 0) or 0
            recent_14d_runs = stats.get('recent_14d_runs', 0) or 0
            recent_14d_wins = stats.get('recent_14d_wins', 0) or 0
            recent_30d_runs = stats.get('recent_30d_runs', 0) or 0
            recent_30d_wins = stats.get('recent_30d_wins', 0) or 0

            win_rate = round((total_wins / total_runners * 100), 2) if total_runners > 0 else 0.0
            place_rate = round((total_places / total_runners * 100), 2) if total_runners > 0 else 0.0
            recent_14d_win_rate = round((recent_14d_wins / recent_14d_runs * 100), 2) if recent_14d_runs > 0 else 0.0
            recent_30d_win_rate = round((recent_30d_wins / recent_30d_runs * 100), 2) if recent_30d_runs > 0 else 0.0

            from datetime import date
            today = date.today()
            last_runner_date = stats.get('last_runner_date')
            last_win_date = stats.get('last_win_date')

            days_since_last_runner = (today - last_runner_date).days if last_runner_date else None
            days_since_last_win = (today - last_win_date).days if last_win_date else None

            # Update database
            update_data = {
                'total_runners': total_runners,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': stats.get('total_seconds', 0) or 0,
                'total_thirds': stats.get('total_thirds', 0) or 0,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'recent_14d_runs': recent_14d_runs,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_runs': recent_30d_runs,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'last_runner_date': str(last_runner_date) if last_runner_date else None,
                'last_win_date': str(last_win_date) if last_win_date else None,
                'days_since_last_runner': days_since_last_runner,
                'days_since_last_win': days_since_last_win,
                'stats_updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db.client.table('ra_mst_trainers').update(update_data).eq('id', trainer_id).execute()
            updated += 1

            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(trainers)} trainers ({updated} updated)")

        duration = time.time() - start_time
        logger.info(f"✅ Trainer statistics complete: {updated}/{len(trainers)} updated in {duration:.1f}s")

        return {
            'table': 'ra_mst_trainers',
            'total': len(trainers),
            'updated': updated,
            'duration': duration
        }

    # ========================================
    # OWNER STATISTICS
    # ========================================

    def calculate_owner_statistics(self) -> Dict:
        """Calculate all owner statistics from ra_mst_runners + ra_races"""
        logger.info("=" * 80)
        logger.info("CALCULATING OWNER STATISTICS")
        logger.info("=" * 80)

        start_time = time.time()

        # Get all owners
        owners_query = """
            SELECT id, name
            FROM ra_mst_owners
            WHERE id NOT LIKE '**TEST**%'
            ORDER BY id
        """
        if self.test_mode:
            owners_query += " LIMIT 10"

        result = self.db.execute_query(owners_query)
        owners = result.data if result.data else []

        logger.info(f"Processing {len(owners)} owners...")

        updated = 0
        for idx, owner in enumerate(owners, 1):
            owner_id = owner['id']

            # Calculate statistics (includes total_horses)
            stats_query = f"""
                SELECT
                    COUNT(DISTINCT r.horse_id) as total_horses,
                    COUNT(*) as total_runners,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as total_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as total_places,
                    COUNT(CASE WHEN r.position = 2 THEN 1 END) as total_seconds,
                    COUNT(CASE WHEN r.position = 3 THEN 1 END) as total_thirds,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days') as recent_14d_runs,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '14 days' AND r.position = 1) as recent_14d_wins,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days') as recent_30d_runs,
                    COUNT(*) FILTER (WHERE rc.date >= CURRENT_DATE - INTERVAL '30 days' AND r.position = 1) as recent_30d_wins,
                    MAX(rc.date) as last_runner_date,
                    MAX(CASE WHEN r.position = 1 THEN rc.date END) as last_win_date
                FROM ra_mst_runners r
                JOIN ra_races rc ON r.race_id = rc.id
                WHERE r.owner_id = '{owner_id}'
                  AND rc.date >= '{self.start_date}'
            """

            stats_result = self.db.execute_query(stats_query)
            if not stats_result.data or len(stats_result.data) == 0:
                continue

            stats = stats_result.data[0]

            # Calculate derived fields
            total_horses = stats.get('total_horses', 0) or 0
            total_runners = stats.get('total_runners', 0) or 0
            total_wins = stats.get('total_wins', 0) or 0
            total_places = stats.get('total_places', 0) or 0
            recent_14d_runs = stats.get('recent_14d_runs', 0) or 0
            recent_14d_wins = stats.get('recent_14d_wins', 0) or 0
            recent_30d_runs = stats.get('recent_30d_runs', 0) or 0
            recent_30d_wins = stats.get('recent_30d_wins', 0) or 0

            win_rate = round((total_wins / total_runners * 100), 2) if total_runners > 0 else 0.0
            place_rate = round((total_places / total_runners * 100), 2) if total_runners > 0 else 0.0
            recent_14d_win_rate = round((recent_14d_wins / recent_14d_runs * 100), 2) if recent_14d_runs > 0 else 0.0
            recent_30d_win_rate = round((recent_30d_wins / recent_30d_runs * 100), 2) if recent_30d_runs > 0 else 0.0
            active_last_30d = recent_30d_runs > 0

            from datetime import date
            today = date.today()
            last_runner_date = stats.get('last_runner_date')
            last_win_date = stats.get('last_win_date')

            days_since_last_runner = (today - last_runner_date).days if last_runner_date else None
            days_since_last_win = (today - last_win_date).days if last_win_date else None

            # Update database
            update_data = {
                'total_horses': total_horses,
                'total_runners': total_runners,
                'total_wins': total_wins,
                'total_places': total_places,
                'total_seconds': stats.get('total_seconds', 0) or 0,
                'total_thirds': stats.get('total_thirds', 0) or 0,
                'win_rate': win_rate,
                'place_rate': place_rate,
                'recent_14d_runs': recent_14d_runs,
                'recent_14d_wins': recent_14d_wins,
                'recent_14d_win_rate': recent_14d_win_rate,
                'recent_30d_runs': recent_30d_runs,
                'recent_30d_wins': recent_30d_wins,
                'recent_30d_win_rate': recent_30d_win_rate,
                'last_runner_date': str(last_runner_date) if last_runner_date else None,
                'last_win_date': str(last_win_date) if last_win_date else None,
                'days_since_last_runner': days_since_last_runner,
                'days_since_last_win': days_since_last_win,
                'active_last_30d': active_last_30d,
                'stats_updated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db.client.table('ra_mst_owners').update(update_data).eq('id', owner_id).execute()
            updated += 1

            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(owners)} owners ({updated} updated)")

        duration = time.time() - start_time
        logger.info(f"✅ Owner statistics complete: {updated}/{len(owners)} updated in {duration:.1f}s")

        return {
            'table': 'ra_mst_owners',
            'total': len(owners),
            'updated': updated,
            'duration': duration
        }

    # ========================================
    # SIRE STATISTICS (PEDIGREE)
    # ========================================

    def calculate_sire_statistics(self) -> Dict:
        """Calculate sire statistics: own career + progeny performance"""
        logger.info("=" * 80)
        logger.info("CALCULATING SIRE STATISTICS")
        logger.info("=" * 80)

        start_time = time.time()

        # Get all sires (horses that have offspring)
        sires_query = """
            SELECT DISTINCT h.sire_id as id, h.sire_name as name
            FROM ra_mst_horses h
            WHERE h.sire_id IS NOT NULL
              AND h.sire_id NOT LIKE '**TEST**%'
            ORDER BY h.sire_id
        """
        if self.test_mode:
            sires_query += " LIMIT 10"

        result = self.db.execute_query(sires_query)
        sires = result.data if result.data else []

        logger.info(f"Processing {len(sires)} sires...")

        # First ensure sires exist in ra_mst_sires table
        for sire in sires:
            sire_data = {
                'id': sire['id'],
                'name': sire['name'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self.db.client.table('ra_mst_sires').upsert(sire_data).execute()

        updated = 0
        for idx, sire in enumerate(sires, 1):
            sire_id = sire['id']

            # Own career statistics
            own_career_query = f"""
                SELECT
                    COUNT(*) as career_runs,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as career_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as career_places,
                    SUM(COALESCE(r.prize_won, 0)) as career_prize,
                    MIN(r.position) FILTER (WHERE r.position IS NOT NULL) as best_position,
                    MIN(rc.date) as first_run,
                    MAX(rc.date) as last_run,
                    MAX(CASE WHEN r.position = 1 THEN rc.date END) as last_win
                FROM ra_mst_runners r
                JOIN ra_races rc ON r.race_id = rc.id
                WHERE r.horse_id = '{sire_id}'
                  AND rc.date >= '{self.start_date}'
            """

            career_result = self.db.execute_query(own_career_query)
            career = career_result.data[0] if career_result.data else {}

            # Progeny statistics
            progeny_query = f"""
                SELECT
                    COUNT(DISTINCT h.id) as progeny_count,
                    COUNT(r.id) as progeny_runs,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as progeny_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as progeny_places,
                    SUM(COALESCE(r.prize_won, 0)) as progeny_prize,

                    -- Class breakdown
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 1 THEN 1 END) as class_1_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 2 THEN 1 END) as class_2_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 3 THEN 1 END) as class_3_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 4 THEN 1 END) as class_4_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 5 THEN 1 END) as class_5_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 6 THEN 1 END) as class_6_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 7 THEN 1 END) as class_7_wins,

                    -- Surface breakdown
                    COUNT(CASE WHEN r.position = 1 AND rc.surface = 'Turf' THEN 1 END) as turf_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.surface = 'AW' THEN 1 END) as aw_wins,

                    -- Type breakdown
                    COUNT(CASE WHEN r.position = 1 AND rc.race_type LIKE '%Flat%' THEN 1 END) as flat_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.race_type LIKE '%Jump%' THEN 1 END) as jump_wins
                FROM ra_mst_horses h
                LEFT JOIN ra_mst_runners r ON r.horse_id = h.id
                LEFT JOIN ra_races rc ON r.race_id = rc.id
                WHERE h.sire_id = '{sire_id}'
                  AND (rc.date IS NULL OR rc.date >= '{self.start_date}')
            """

            progeny_result = self.db.execute_query(progeny_query)
            progeny = progeny_result.data[0] if progeny_result.data else {}

            # Calculate averages
            progeny_count = progeny.get('progeny_count', 0) or 0
            progeny_runs = progeny.get('progeny_runs', 0) or 0
            progeny_wins = progeny.get('progeny_wins', 0) or 0

            avg_runs_per_horse = round((progeny_runs / progeny_count), 2) if progeny_count > 0 else 0.0
            avg_wins_per_horse = round((progeny_wins / progeny_count), 2) if progeny_count > 0 else 0.0

            # Find best class (most wins)
            class_wins = [
                (1, progeny.get('class_1_wins', 0) or 0),
                (2, progeny.get('class_2_wins', 0) or 0),
                (3, progeny.get('class_3_wins', 0) or 0),
                (4, progeny.get('class_4_wins', 0) or 0),
                (5, progeny.get('class_5_wins', 0) or 0),
                (6, progeny.get('class_6_wins', 0) or 0),
                (7, progeny.get('class_7_wins', 0) or 0)
            ]
            best_class = max(class_wins, key=lambda x: x[1])[0] if any(w > 0 for _, w in class_wins) else None

            # Update database
            update_data = {
                # Own career
                'career_runs': career.get('career_runs', 0) or 0,
                'career_wins': career.get('career_wins', 0) or 0,
                'career_places': career.get('career_places', 0) or 0,
                'career_prize': float(career.get('career_prize', 0) or 0),
                'best_position': career.get('best_position'),
                'first_run': str(career.get('first_run')) if career.get('first_run') else None,
                'last_run': str(career.get('last_run')) if career.get('last_run') else None,
                'last_win': str(career.get('last_win')) if career.get('last_win') else None,

                # Progeny stats
                'progeny_count': progeny_count,
                'progeny_runs': progeny_runs,
                'progeny_wins': progeny_wins,
                'progeny_places': progeny.get('progeny_places', 0) or 0,
                'progeny_prize': float(progeny.get('progeny_prize', 0) or 0),
                'avg_runs_per_horse': avg_runs_per_horse,
                'avg_wins_per_horse': avg_wins_per_horse,
                'best_class': best_class,

                # Class breakdown
                'class_1_wins': progeny.get('class_1_wins', 0) or 0,
                'class_2_wins': progeny.get('class_2_wins', 0) or 0,
                'class_3_wins': progeny.get('class_3_wins', 0) or 0,
                'class_4_wins': progeny.get('class_4_wins', 0) or 0,
                'class_5_wins': progeny.get('class_5_wins', 0) or 0,
                'class_6_wins': progeny.get('class_6_wins', 0) or 0,
                'class_7_wins': progeny.get('class_7_wins', 0) or 0,

                # Surface breakdown
                'turf_wins': progeny.get('turf_wins', 0) or 0,
                'aw_wins': progeny.get('aw_wins', 0) or 0,

                # Type breakdown
                'flat_wins': progeny.get('flat_wins', 0) or 0,
                'jump_wins': progeny.get('jump_wins', 0) or 0,

                'calculated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db.client.table('ra_mst_sires').update(update_data).eq('id', sire_id).execute()
            updated += 1

            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(sires)} sires ({updated} updated)")

        duration = time.time() - start_time
        logger.info(f"✅ Sire statistics complete: {updated}/{len(sires)} updated in {duration:.1f}s")

        return {
            'table': 'ra_mst_sires',
            'total': len(sires),
            'updated': updated,
            'duration': duration
        }

    # ========================================
    # DAM STATISTICS (PEDIGREE)
    # ========================================

    def calculate_dam_statistics(self) -> Dict:
        """Calculate dam statistics: own career + progeny performance"""
        logger.info("=" * 80)
        logger.info("CALCULATING DAM STATISTICS")
        logger.info("=" * 80)

        # Same logic as sires but using dam_id
        # (Implementation identical to sires, just swap sire_id for dam_id)

        start_time = time.time()

        dams_query = """
            SELECT DISTINCT h.dam_id as id, h.dam_name as name
            FROM ra_mst_horses h
            WHERE h.dam_id IS NOT NULL
              AND h.dam_id NOT LIKE '**TEST**%'
            ORDER BY h.dam_id
        """
        if self.test_mode:
            dams_query += " LIMIT 10"

        result = self.db.execute_query(dams_query)
        dams = result.data if result.data else []

        logger.info(f"Processing {len(dams)} dams...")

        # Create dam records
        for dam in dams:
            dam_data = {
                'id': dam['id'],
                'name': dam['name'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self.db.client.table('ra_mst_dams').upsert(dam_data).execute()

        updated = 0
        for idx, dam in enumerate(dams, 1):
            dam_id = dam['id']

            # Own career + progeny stats (identical SQL but with dam_id)
            own_career_query = f"""
                SELECT
                    COUNT(*) as career_runs,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as career_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as career_places,
                    SUM(COALESCE(r.prize_won, 0)) as career_prize,
                    MIN(r.position) FILTER (WHERE r.position IS NOT NULL) as best_position,
                    MIN(rc.date) as first_run,
                    MAX(rc.date) as last_run,
                    MAX(CASE WHEN r.position = 1 THEN rc.date END) as last_win
                FROM ra_mst_runners r
                JOIN ra_races rc ON r.race_id = rc.id
                WHERE r.horse_id = '{dam_id}'
                  AND rc.date >= '{self.start_date}'
            """

            career_result = self.db.execute_query(own_career_query)
            career = career_result.data[0] if career_result.data else {}

            progeny_query = f"""
                SELECT
                    COUNT(DISTINCT h.id) as progeny_count,
                    COUNT(r.id) as progeny_runs,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as progeny_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as progeny_places,
                    SUM(COALESCE(r.prize_won, 0)) as progeny_prize,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 1 THEN 1 END) as class_1_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 2 THEN 1 END) as class_2_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 3 THEN 1 END) as class_3_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 4 THEN 1 END) as class_4_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 5 THEN 1 END) as class_5_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 6 THEN 1 END) as class_6_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 7 THEN 1 END) as class_7_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.surface = 'Turf' THEN 1 END) as turf_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.surface = 'AW' THEN 1 END) as aw_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.race_type LIKE '%Flat%' THEN 1 END) as flat_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.race_type LIKE '%Jump%' THEN 1 END) as jump_wins
                FROM ra_mst_horses h
                LEFT JOIN ra_mst_runners r ON r.horse_id = h.id
                LEFT JOIN ra_races rc ON r.race_id = rc.id
                WHERE h.dam_id = '{dam_id}'
                  AND (rc.date IS NULL OR rc.date >= '{self.start_date}')
            """

            progeny_result = self.db.execute_query(progeny_query)
            progeny = progeny_result.data[0] if progeny_result.data else {}

            progeny_count = progeny.get('progeny_count', 0) or 0
            progeny_runs = progeny.get('progeny_runs', 0) or 0
            progeny_wins = progeny.get('progeny_wins', 0) or 0

            avg_runs_per_horse = round((progeny_runs / progeny_count), 2) if progeny_count > 0 else 0.0
            avg_wins_per_horse = round((progeny_wins / progeny_count), 2) if progeny_count > 0 else 0.0

            class_wins = [
                (1, progeny.get('class_1_wins', 0) or 0),
                (2, progeny.get('class_2_wins', 0) or 0),
                (3, progeny.get('class_3_wins', 0) or 0),
                (4, progeny.get('class_4_wins', 0) or 0),
                (5, progeny.get('class_5_wins', 0) or 0),
                (6, progeny.get('class_6_wins', 0) or 0),
                (7, progeny.get('class_7_wins', 0) or 0)
            ]
            best_class = max(class_wins, key=lambda x: x[1])[0] if any(w > 0 for _, w in class_wins) else None

            update_data = {
                'career_runs': career.get('career_runs', 0) or 0,
                'career_wins': career.get('career_wins', 0) or 0,
                'career_places': career.get('career_places', 0) or 0,
                'career_prize': float(career.get('career_prize', 0) or 0),
                'best_position': career.get('best_position'),
                'first_run': str(career.get('first_run')) if career.get('first_run') else None,
                'last_run': str(career.get('last_run')) if career.get('last_run') else None,
                'last_win': str(career.get('last_win')) if career.get('last_win') else None,
                'progeny_count': progeny_count,
                'progeny_runs': progeny_runs,
                'progeny_wins': progeny_wins,
                'progeny_places': progeny.get('progeny_places', 0) or 0,
                'progeny_prize': float(progeny.get('progeny_prize', 0) or 0),
                'avg_runs_per_horse': avg_runs_per_horse,
                'avg_wins_per_horse': avg_wins_per_horse,
                'best_class': best_class,
                'class_1_wins': progeny.get('class_1_wins', 0) or 0,
                'class_2_wins': progeny.get('class_2_wins', 0) or 0,
                'class_3_wins': progeny.get('class_3_wins', 0) or 0,
                'class_4_wins': progeny.get('class_4_wins', 0) or 0,
                'class_5_wins': progeny.get('class_5_wins', 0) or 0,
                'class_6_wins': progeny.get('class_6_wins', 0) or 0,
                'class_7_wins': progeny.get('class_7_wins', 0) or 0,
                'turf_wins': progeny.get('turf_wins', 0) or 0,
                'aw_wins': progeny.get('aw_wins', 0) or 0,
                'flat_wins': progeny.get('flat_wins', 0) or 0,
                'jump_wins': progeny.get('jump_wins', 0) or 0,
                'calculated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db.client.table('ra_mst_dams').update(update_data).eq('id', dam_id).execute()
            updated += 1

            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(dams)} dams ({updated} updated)")

        duration = time.time() - start_time
        logger.info(f"✅ Dam statistics complete: {updated}/{len(dams)} updated in {duration:.1f}s")

        return {
            'table': 'ra_mst_dams',
            'total': len(dams),
            'updated': updated,
            'duration': duration
        }

    # ========================================
    # DAMSIRE STATISTICS (PEDIGREE)
    # ========================================

    def calculate_damsire_statistics(self) -> Dict:
        """Calculate damsire statistics: grandoffspring performance"""
        logger.info("=" * 80)
        logger.info("CALCULATING DAMSIRE STATISTICS")
        logger.info("=" * 80)

        start_time = time.time()

        damsires_query = """
            SELECT DISTINCT h.damsire_id as id
            FROM ra_mst_horses h
            WHERE h.damsire_id IS NOT NULL
              AND h.damsire_id NOT LIKE '**TEST**%'
            ORDER BY h.damsire_id
        """
        if self.test_mode:
            damsires_query += " LIMIT 10"

        result = self.db.execute_query(damsires_query)
        damsires = result.data if result.data else []

        logger.info(f"Processing {len(damsires)} damsires...")

        # Create damsire records
        for damsire in damsires:
            damsire_data = {
                'id': damsire['id'],
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            self.db.client.table('ra_mst_damsires').upsert(damsire_data).execute()

        updated = 0
        for idx, damsire in enumerate(damsires, 1):
            damsire_id = damsire['id']

            # Grandoffspring stats (horses where damsire_id = this damsire)
            progeny_query = f"""
                SELECT
                    COUNT(DISTINCT h.id) as progeny_count,
                    COUNT(r.id) as progeny_runs,
                    COUNT(CASE WHEN r.position = 1 THEN 1 END) as progeny_wins,
                    COUNT(CASE WHEN r.position <= 3 THEN 1 END) as progeny_places,
                    SUM(COALESCE(r.prize_won, 0)) as progeny_prize,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 1 THEN 1 END) as class_1_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 2 THEN 1 END) as class_2_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 3 THEN 1 END) as class_3_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 4 THEN 1 END) as class_4_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 5 THEN 1 END) as class_5_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 6 THEN 1 END) as class_6_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.class = 7 THEN 1 END) as class_7_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.surface = 'Turf' THEN 1 END) as turf_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.surface = 'AW' THEN 1 END) as aw_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.race_type LIKE '%Flat%' THEN 1 END) as flat_wins,
                    COUNT(CASE WHEN r.position = 1 AND rc.race_type LIKE '%Jump%' THEN 1 END) as jump_wins
                FROM ra_mst_horses h
                LEFT JOIN ra_mst_runners r ON r.horse_id = h.id
                LEFT JOIN ra_races rc ON r.race_id = rc.id
                WHERE h.damsire_id = '{damsire_id}'
                  AND (rc.date IS NULL OR rc.date >= '{self.start_date}')
            """

            progeny_result = self.db.execute_query(progeny_query)
            progeny = progeny_result.data[0] if progeny_result.data else {}

            progeny_count = progeny.get('progeny_count', 0) or 0
            progeny_runs = progeny.get('progeny_runs', 0) or 0
            progeny_wins = progeny.get('progeny_wins', 0) or 0

            avg_runs_per_horse = round((progeny_runs / progeny_count), 2) if progeny_count > 0 else 0.0
            avg_wins_per_horse = round((progeny_wins / progeny_count), 2) if progeny_count > 0 else 0.0

            class_wins = [
                (1, progeny.get('class_1_wins', 0) or 0),
                (2, progeny.get('class_2_wins', 0) or 0),
                (3, progeny.get('class_3_wins', 0) or 0),
                (4, progeny.get('class_4_wins', 0) or 0),
                (5, progeny.get('class_5_wins', 0) or 0),
                (6, progeny.get('class_6_wins', 0) or 0),
                (7, progeny.get('class_7_wins', 0) or 0)
            ]
            best_class = max(class_wins, key=lambda x: x[1])[0] if any(w > 0 for _, w in class_wins) else None

            update_data = {
                'progeny_count': progeny_count,
                'progeny_runs': progeny_runs,
                'progeny_wins': progeny_wins,
                'progeny_places': progeny.get('progeny_places', 0) or 0,
                'progeny_prize': float(progeny.get('progeny_prize', 0) or 0),
                'avg_runs_per_horse': avg_runs_per_horse,
                'avg_wins_per_horse': avg_wins_per_horse,
                'best_class': best_class,
                'class_1_wins': progeny.get('class_1_wins', 0) or 0,
                'class_2_wins': progeny.get('class_2_wins', 0) or 0,
                'class_3_wins': progeny.get('class_3_wins', 0) or 0,
                'class_4_wins': progeny.get('class_4_wins', 0) or 0,
                'class_5_wins': progeny.get('class_5_wins', 0) or 0,
                'class_6_wins': progeny.get('class_6_wins', 0) or 0,
                'class_7_wins': progeny.get('class_7_wins', 0) or 0,
                'turf_wins': progeny.get('turf_wins', 0) or 0,
                'aw_wins': progeny.get('aw_wins', 0) or 0,
                'flat_wins': progeny.get('flat_wins', 0) or 0,
                'jump_wins': progeny.get('jump_wins', 0) or 0,
                'calculated_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            self.db.client.table('ra_mst_damsires').update(update_data).eq('id', damsire_id).execute()
            updated += 1

            if idx % 100 == 0:
                logger.info(f"  Progress: {idx}/{len(damsires)} damsires ({updated} updated)")

        duration = time.time() - start_time
        logger.info(f"✅ Damsire statistics complete: {updated}/{len(damsires)} updated in {duration:.1f}s")

        return {
            'table': 'ra_mst_damsires',
            'total': len(damsires),
            'updated': updated,
            'duration': duration
        }

    # ========================================
    # MAIN ORCHESTRATION
    # ========================================

    def run_all(self, tables: Optional[List[str]] = None) -> Dict:
        """Run all statistics calculations"""
        logger.info("=" * 80)
        logger.info("UNIFIED STATISTICS POPULATION")
        logger.info("=" * 80)
        logger.info(f"Start date: {self.start_date}")
        logger.info(f"Test mode: {self.test_mode}")
        logger.info(f"Tables: {tables if tables else 'ALL'}")
        logger.info("=" * 80)

        overall_start = time.time()
        results = []

        # Define execution order
        all_workers = [
            ('jockeys', self.calculate_jockey_statistics),
            ('trainers', self.calculate_trainer_statistics),
            ('owners', self.calculate_owner_statistics),
            ('sires', self.calculate_sire_statistics),
            ('dams', self.calculate_dam_statistics),
            ('damsires', self.calculate_damsire_statistics)
        ]

        # Filter if specific tables requested
        if tables:
            all_workers = [(name, func) for name, func in all_workers if name in tables]

        # Execute each worker
        for table_name, worker_func in all_workers:
            try:
                result = worker_func()
                results.append(result)
            except Exception as e:
                logger.error(f"❌ Failed to calculate {table_name} statistics: {e}", exc_info=True)
                results.append({
                    'table': f'ra_mst_{table_name}',
                    'total': 0,
                    'updated': 0,
                    'duration': 0,
                    'error': str(e)
                })

        overall_duration = time.time() - overall_start

        # Summary
        logger.info("=" * 80)
        logger.info("SUMMARY")
        logger.info("=" * 80)

        total_entities = sum(r.get('total', 0) for r in results)
        total_updated = sum(r.get('updated', 0) for r in results)

        for result in results:
            status = "✅" if result.get('updated', 0) > 0 else "❌"
            logger.info(f"{status} {result['table']}: {result.get('updated', 0)}/{result.get('total', 0)} "
                       f"({result.get('duration', 0):.1f}s)")

        logger.info("=" * 80)
        logger.info(f"TOTAL: {total_updated}/{total_entities} entities updated")
        logger.info(f"DURATION: {overall_duration:.1f}s ({overall_duration/60:.1f} minutes)")
        logger.info("=" * 80)

        return {
            'success': True,
            'total_entities': total_entities,
            'total_updated': total_updated,
            'duration': overall_duration,
            'results': results
        }


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Unified statistics population from database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Full run (all tables, from 2015-01-01)
  python3 scripts/populate_all_statistics_from_database.py

  # Test mode (10 entities per table)
  python3 scripts/populate_all_statistics_from_database.py --test

  # Specific tables only
  python3 scripts/populate_all_statistics_from_database.py --tables jockeys trainers

  # Custom start date
  python3 scripts/populate_all_statistics_from_database.py --start-date 2020-01-01
        """
    )

    parser.add_argument('--test', action='store_true',
                       help='Test mode (10 entities per table)')
    parser.add_argument('--start-date', type=str, default='2015-01-01',
                       help='Start date for calculations (default: 2015-01-01)')
    parser.add_argument('--tables', nargs='+',
                       choices=['jockeys', 'trainers', 'owners', 'sires', 'dams', 'damsires'],
                       help='Specific tables to update (default: all)')

    args = parser.parse_args()

    try:
        populator = UnifiedStatisticsPopulator(
            test_mode=args.test,
            start_date=args.start_date
        )

        result = populator.run_all(tables=args.tables)

        if result['success']:
            logger.info("✅ All statistics calculations completed successfully")
            sys.exit(0)
        else:
            logger.error("❌ Some statistics calculations failed")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("⚠️ Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
